import os
import sqlite3
from datetime import datetime
from typing import Dict, List, Literal, Optional

from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel

app = FastAPI(title="WebBot Service", version="0.1.0")

SANDBOX_ROOT = os.environ.get("SANDBOX_ROOT", "/sandbox/workspace")
DEFAULT_TIMEOUT = int(os.environ.get("WEB_TIMEOUT_SECONDS", "20"))
API_KEY = os.environ.get("API_KEY", "")
AUDIT_DB_PATH = os.environ.get("AUDIT_DB_PATH", "/app/data/audit.db")

ActionType = Literal[
    "goto",
    "click",
    "type",
    "select",
    "extract",
    "screenshot",
    "pdf",
    "upload",
    "download",
    "set_cookies",
    "get_cookies",
    "clear_storage",
]


class WebAction(BaseModel):
    type: ActionType
    selector: Optional[str] = None
    value: Optional[str] = None
    url: Optional[str] = None
    path: Optional[str] = None
    options: Dict = {}


class WebRequest(BaseModel):
    actions: List[WebAction]
    confirm_sensitive: bool = False
    proxy: Optional[str] = None


class WebResponse(BaseModel):
    results: List[Dict]


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
            CREATE TABLE IF NOT EXISTS web_audit (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              ts TEXT NOT NULL,
              actions_count INTEGER,
              sensitive INTEGER,
              status TEXT,
              error TEXT
            )
            """
        )
        conn.commit()
    finally:
        conn.close()


@app.post(
    "/interact-web", response_model=WebResponse, dependencies=[Depends(require_api_key)]
)
async def interact_web(req: WebRequest):
    sensitive = any(a.type in {"type", "upload", "pdf"} for a in req.actions)
    if sensitive and not req.confirm_sensitive:
        raise HTTPException(412, "Confirmation required for sensitive web actions")

    try:
        from playwright.async_api import async_playwright
    except Exception as e:
        raise HTTPException(500, f"Playwright not available: {e}")

    results: List[Dict] = []
    error_msg = None
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(accept_downloads=True)
            page = await context.new_page()

            for a in req.actions:
                if a.type == "goto":
                    if not a.url:
                        raise HTTPException(400, "goto requires url")
                    await page.goto(a.url, timeout=DEFAULT_TIMEOUT * 1000)
                    results.append({"type": "goto", "ok": True, "url": a.url})

                elif a.type == "click":
                    await page.click(a.selector, timeout=DEFAULT_TIMEOUT * 1000)
                    results.append(
                        {"type": "click", "ok": True, "selector": a.selector}
                    )

                elif a.type == "type":
                    await page.fill(
                        a.selector, a.value or "", timeout=DEFAULT_TIMEOUT * 1000
                    )
                    results.append({"type": "type", "ok": True, "selector": a.selector})

                elif a.type == "select":
                    await page.select_option(
                        a.selector, a.value or "", timeout=DEFAULT_TIMEOUT * 1000
                    )
                    results.append(
                        {"type": "select", "ok": True, "selector": a.selector}
                    )

                elif a.type == "extract":
                    text = await page.text_content(
                        a.selector, timeout=DEFAULT_TIMEOUT * 1000
                    )
                    results.append(
                        {"type": "extract", "selector": a.selector, "text": text}
                    )

                elif a.type == "upload":
                    rel = a.path or ""
                    abs_path = os.path.realpath(os.path.join(SANDBOX_ROOT, rel))
                    if not abs_path.startswith(os.path.realpath(SANDBOX_ROOT)):
                        raise HTTPException(
                            400, "upload path must be under SANDBOX_ROOT"
                        )
                    await page.set_input_files(a.selector, abs_path)
                    results.append({"type": "upload", "ok": True, "path": rel})

                elif a.type == "download":
                    results.append({"type": "download", "note": "downloads accepted"})

                elif a.type == "screenshot":
                    rel = a.path or "screenshot.png"
                    abs_path = os.path.realpath(os.path.join(SANDBOX_ROOT, rel))
                    os.makedirs(os.path.dirname(abs_path), exist_ok=True)
                    await page.screenshot(path=abs_path, full_page=True)
                    results.append({"type": "screenshot", "path": rel})

                elif a.type == "pdf":
                    rel = a.path or "page.pdf"
                    abs_path = os.path.realpath(os.path.join(SANDBOX_ROOT, rel))
                    os.makedirs(os.path.dirname(abs_path), exist_ok=True)
                    await page.pdf(path=abs_path)
                    results.append({"type": "pdf", "path": rel})

                elif a.type == "set_cookies":
                    await context.add_cookies(a.options.get("cookies", []))
                    results.append({"type": "set_cookies", "ok": True})

                elif a.type == "get_cookies":
                    cookies = await context.cookies()
                    results.append({"type": "get_cookies", "cookies": cookies})

                elif a.type == "clear_storage":
                    await context.clear_cookies()
                    await page.evaluate("localStorage.clear(); sessionStorage.clear();")
                    results.append({"type": "clear_storage", "ok": True})

            await context.close()
            await browser.close()
    except Exception as e:
        error_msg = str(e)
        raise
    finally:
        try:
            conn = sqlite3.connect(AUDIT_DB_PATH)
            conn.execute(
                """
                INSERT INTO web_audit (ts, actions_count, sensitive, status, error)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    datetime.utcnow().isoformat() + "Z",
                    len(req.actions or []),
                    1 if sensitive else 0,
                    "ok" if error_msg is None else "error",
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

    return WebResponse(results=results)
