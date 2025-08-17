import asyncio
import importlib
import os
import runpy
import signal
import sys
import threading
import time
from pathlib import Path
from typing import Optional

import psutil
import requests
from dotenv import load_dotenv


class BackendManager:
    """
    Boots FastAPI (olympus_api.main:app) and the worker (olympus_worker.main) in separate processes,
    manages lifecycle, and exposes simple health checks. Reads .env from repo root.
    """

    def __init__(self) -> None:
        self.repo_root = self._detect_repo_root()
        self._load_env()
        self._prepare_sys_path()

        self.host = os.getenv("UVICORN_HOST", "127.0.0.1")
        self.port = int(os.getenv("UVICORN_PORT", "8000"))
        self.health_url = f"http://{self.host}:{self.port}/health"
        self.docs_url = f"http://{self.host}:{self.port}/docs"
        self.config_url = f"http://{self.host}:{self.port}/v1/config"

        self._api_proc: Optional[psutil.Popen] = None
        self._worker_proc: Optional[psutil.Popen] = None
        self._lock = threading.Lock()

    # ---------- public API (called from UI) ----------

    def start_all(self) -> dict:
        with self._lock:
            self._ensure_api()
            self._ensure_worker()
        # Wait briefly for /health
        self._wait_for_health(timeout=10.0)
        return self.status()

    def stop_all(self) -> dict:
        with self._lock:
            self._terminate(self._worker_proc)
            self._worker_proc = None
            self._terminate(self._api_proc)
            self._api_proc = None
        return self.status()

    def status(self) -> dict:
        api_alive = self._alive(self._api_proc)
        worker_alive = self._alive(self._worker_proc)
        health = None
        try:
            r = requests.get(self.health_url, timeout=1.5)
            health = {
                "code": r.status_code,
                "body": (
                    r.json()
                    if r.headers.get("content-type", "").startswith("application/json")
                    else r.text
                ),
            }
        except Exception as e:
            health = {"error": str(e)}
        return {
            "api_pid": self._pid(self._api_proc),
            "worker_pid": self._pid(self._worker_proc),
            "api_alive": api_alive,
            "worker_alive": worker_alive,
            "health": health,
            "urls": {"docs": self.docs_url, "config": self.config_url},
        }

    def open_docs_url(self) -> str:
        return self.docs_url

    def open_config_url(self) -> str:
        return self.config_url

    # ---------- internals ----------

    def _detect_repo_root(self) -> Path:
        # desktop/ is placed at repo root; go one level up
        here = Path(__file__).resolve()
        return here.parents[2]

    def _load_env(self) -> None:
        # Prefer .env, fall back to .env.dev
        env_path = self.repo_root / ".env"
        dev_path = self.repo_root / ".env.dev"
        if env_path.exists():
            load_dotenv(dotenv_path=env_path)
        elif dev_path.exists():
            load_dotenv(dotenv_path=dev_path)
        # else: rely on OS env

    def _prepare_sys_path(self) -> None:
        # Make olympus_* packages importable without pip install -e
        sys.path.insert(0, str(self.repo_root / "apps" / "api"))
        sys.path.insert(0, str(self.repo_root / "apps" / "worker"))
        pkgs = self.repo_root / "packages"
        if pkgs.exists():
            for sub in pkgs.iterdir():
                if sub.is_dir():
                    sys.path.insert(0, str(sub))

    def _ensure_api(self) -> bool:
        if self._alive(self._api_proc):
            return True
        self._api_proc = self._spawn(self._run_uvicorn_entry)
        return True

    def _ensure_worker(self) -> bool:
        if self._alive(self._worker_proc):
            return True
        self._worker_proc = self._spawn(self._run_worker_entry)
        return True

    def _wait_for_health(self, timeout: float = 10.0) -> None:
        deadline = time.time() + timeout
        while time.time() < deadline:
            try:
                r = requests.get(self.health_url, timeout=0.75)
                if r.status_code == 200:
                    return
            except requests.RequestException:
                pass
            time.sleep(0.25)

    # ---------- process runners ----------

    def _spawn(self, target) -> psutil.Popen:
        # Launch a fresh Python interpreter process with same env + sys.path adjustments via code string
        # IMPORTANT: this code is run in a separate process, so it can't use any variables from this file
        code = f"""
import os, sys, asyncio, importlib, runpy
from pathlib import Path
# sys.path bootstrap (mirrors parent)
sys.path = {repr(sys.path)}
os.environ.update({repr(dict(os.environ))})

{target.__name__}()
"""
        # Use current python executable
        proc = psutil.Popen(
            [sys.executable, "-c", code], stdout=sys.stdout, stderr=sys.stderr
        )
        return proc

    def _run_uvicorn_entry(self) -> None:  # executed in child
        import uvicorn  # type: ignore

        host = os.getenv("UVICORN_HOST", "127.0.0.1")
        port = int(os.getenv("UVICORN_PORT", "8000"))
        log_level = os.getenv("LOG_LEVEL", "INFO").lower()

        # Try import the FastAPI app
        try:
            mod = importlib.import_module("olympus_api.main")
            app = getattr(mod, "app")
        except Exception as e:
            print(f"[desktop] Failed to import olympus_api.main:app: {e}", flush=True)
            raise

        uvicorn.run(app=app, host=host, port=port, log_level=log_level)

    def _run_worker_entry(self) -> None:  # executed in child
        # Prefer calling main() if present; otherwise run module as script.
        try:
            mod = importlib.import_module("olympus_worker.main")
            fn = getattr(mod, "main", None)
            if fn is None:
                runpy.run_module("olympus_worker.main", run_name="__main__")
            else:
                if asyncio.iscoroutinefunction(fn):
                    asyncio.run(fn())
                else:
                    fn()
        except Exception as e:
            print(f"[desktop] Failed to run olympus_worker.main: {e}", flush=True)
            raise

    # ---------- utils ----------

    def _terminate(self, proc: Optional[psutil.Popen]) -> None:
        if proc is None:
            return
        try:
            if proc.is_running():
                if sys.platform.startswith("win"):
                    proc.terminate()
                else:
                    proc.send_signal(signal.SIGTERM)
                proc.wait(timeout=10)
        except Exception:
            try:
                proc.kill()
            except Exception:
                pass

    @staticmethod
    def _alive(proc: Optional[psutil.Popen]) -> bool:
        return bool(
            proc and proc.is_running() and proc.status() != psutil.STATUS_ZOMBIE
        )

    @staticmethod
    def _pid(proc: Optional[psutil.Popen]) -> Optional[int]:
        try:
            return int(proc.pid) if proc else None
        except Exception:
            return None
