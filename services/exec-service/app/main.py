import os
import sqlite3
import subprocess
from datetime import datetime

from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(title="Exec Service", version="0.1.0")

SANDBOX_ROOT = os.environ.get("SANDBOX_ROOT", "/sandbox/workspace")
ALLOWED_LANGS = {"python", "node", "bash"}
DEFAULT_TIMEOUT = int(os.environ.get("EXEC_TIMEOUT_SECONDS", "15"))
CPU_LIMIT = os.environ.get("EXEC_CPU", "0.5")
MEM_LIMIT = os.environ.get("EXEC_MEM", "256m")
NET_MODE = os.environ.get("EXEC_NETWORK", "none")  # default: no network
IMAGE_MAP = {
    "python": os.environ.get("EXEC_IMAGE_PY", "python:3.11-alpine"),
    "node": os.environ.get("EXEC_IMAGE_NODE", "node:18-alpine"),
    "bash": os.environ.get("EXEC_IMAGE_BASH", "bash:5.2"),
}
API_KEY = os.environ.get("API_KEY", "")
AUDIT_DB_PATH = os.environ.get("AUDIT_DB_PATH", "/app/data/audit.db")

class ExecRequest(BaseModel):
    language: str = Field(description="python|node|bash")
    code: str
    workdir: str = Field(description="Relative path under SANDBOX_ROOT")
    allow_network: bool = False
    confirm_sensitive: bool = False

class ExecResponse(BaseModel):
    stdout: str
    stderr: str
    exit_code: int

def require_api_key(x_api_key: str = Header(default="")):
    if not API_KEY or x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")

@app.on_event("startup")
def startup():
    os.makedirs(os.path.dirname(AUDIT_DB_PATH), exist_ok=True)
    conn = sqlite3.connect(AUDIT_DB_PATH)
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS exec_audit (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              ts TEXT NOT NULL,
              language TEXT,
              workdir TEXT,
              allow_network INTEGER,
              code_len INTEGER,
              exit_code INTEGER,
              status TEXT,
              stdout_preview TEXT,
              stderr_preview TEXT,
              error TEXT
            )
            """
        )
        conn.commit()
    finally:
        conn.close()

@app.post("/execute-local-code", response_model=ExecResponse, dependencies=[Depends(require_api_key)])
async def execute_local_code(req: ExecRequest):
    lang = req.language.lower()
    if lang not in ALLOWED_LANGS:
        raise HTTPException(400, f"Unsupported language: {req.language}")

    # Resolve and validate working directory
    abs_workdir = os.path.realpath(os.path.join(SANDBOX_ROOT, req.workdir))
    if not abs_workdir.startswith(os.path.realpath(SANDBOX_ROOT)):
        raise HTTPException(400, "workdir must be under SANDBOX_ROOT")
    os.makedirs(abs_workdir, exist_ok=True)

    # Confirm sensitive: network or long-running code
    if (req.allow_network or len(req.code) > 5000) and not req.confirm_sensitive:
        raise HTTPException(412, "Confirmation required for sensitive operation")

    image = IMAGE_MAP[lang]
    net = "bridge" if req.allow_network else NET_MODE

    if lang == "python":
        cmd = ["python", "-c", req.code]
    elif lang == "node":
        cmd = ["node", "-e", req.code]
    else:
        cmd = ["bash", "-lc", req.code]

    docker_cmd = [
        "docker", "run", "--rm",
        "--network", net,
        "--cpus", CPU_LIMIT,
        "--memory", MEM_LIMIT,
        "--pids-limit", "128",
        "-v", f"{abs_workdir}:/workspace:rw,noexec,nodev,nosuid",
        "-w", "/workspace",
        image,
    ] + cmd

    stdout_text = ""
    stderr_text = ""
    exit_code = -1
    error_msg = None
    try:
        proc = subprocess.run(
            docker_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=DEFAULT_TIMEOUT,
            check=False,
            text=True,
        )
        stdout_text = proc.stdout
        stderr_text = proc.stderr
        exit_code = proc.returncode
        return ExecResponse(stdout=stdout_text, stderr=stderr_text, exit_code=exit_code)
    except subprocess.TimeoutExpired:
        error_msg = f"Execution timed out after {DEFAULT_TIMEOUT}s"
        raise HTTPException(408, error_msg)
    finally:
        try:
            conn = sqlite3.connect(AUDIT_DB_PATH)
            conn.execute(
                """
                INSERT INTO exec_audit (ts, language, workdir, allow_network, code_len, exit_code, status, stdout_preview, stderr_preview, error)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    datetime.utcnow().isoformat() + "Z",
                    lang,
                    req.workdir,
                    1 if req.allow_network else 0,
                    len(req.code or ""),
                    exit_code,
                    "ok" if error_msg is None else "error",
                    (stdout_text or "")[:512],
                    (stderr_text or "")[:512],
                    error_msg,
                ),
            )
            conn.commit()
        except Exception:
            pass
        finally:
            try:
                conn.close()
            except Exception:
                pass
