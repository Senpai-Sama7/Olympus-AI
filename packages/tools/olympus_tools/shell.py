from __future__ import annotations

import os
import shlex
import subprocess
from typing import Dict, List, Optional

from .fs import _normalize, ConsentToken, REQUIRE_CONSENT

EXEC_SCOPE = "exec_shell"


def _check_exec_consent(token: Optional[ConsentToken]):
    if not REQUIRE_CONSENT:
        return
    if token is None or ("*" not in token.scopes and EXEC_SCOPE not in token.scopes):
        raise PermissionError("Consent with 'exec_shell' scope required")


def run_shell_command(
    cmd: List[str] | str,
    workdir: str = "/",
    timeout: int = 120,
    token: Optional[ConsentToken] = None,
) -> Dict:
    """
    Execute a shell command within the sandboxed workdir.
    - cmd: list or string; if string, executed via /bin/sh -lc
    - workdir: relative path under sandbox root
    - timeout: seconds
    """
    _check_exec_consent(token)
    cwd = _normalize(workdir)
    os.makedirs(cwd, exist_ok=True)
    if isinstance(cmd, str):
        args = ["/bin/sh", "-lc", cmd]
        display = cmd
    else:
        args = cmd
        display = " ".join(shlex.quote(x) for x in cmd)
    try:
        proc = subprocess.run(
            args,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            text=True,
            check=False,
        )
        return {
            "cwd": cwd,
            "cmd": display,
            "exit_code": proc.returncode,
            "stdout": proc.stdout,
            "stderr": proc.stderr,
        }
    except subprocess.TimeoutExpired as e:
        return {
            "cwd": cwd,
            "cmd": display,
            "exit_code": 124,
            "stdout": e.stdout or "",
            "stderr": (e.stderr or "") + f"\nTIMEOUT after {timeout}s",
        }
