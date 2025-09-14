from __future__ import annotations

import os
import shutil
import stat
from dataclasses import dataclass
from typing import Dict, List, Optional

try:
    import olympus_tools_rs  # type: ignore
except Exception:  # Fallback pure-Python implementation for tests/dev
    olympus_tools_rs = None  # type: ignore

SANDBOX_ROOT = os.path.abspath(os.getenv("OLYMPUS_SANDBOX_ROOT", ".sandbox"))
REQUIRE_CONSENT = os.getenv("OLY_REQUIRE_CONSENT", "true").lower() == "true"

os.makedirs(SANDBOX_ROOT, exist_ok=True)

READ_SCOPE = "read_fs"
WRITE_SCOPE = "write_fs"
DELETE_SCOPE = "delete_fs"
LIST_SCOPE = "list_fs"

ALL_SCOPES = {READ_SCOPE, WRITE_SCOPE, DELETE_SCOPE, LIST_SCOPE}


@dataclass
class ConsentToken:
    token: str
    scopes: List[str]


class ConsentError(Exception):
    pass


class PathError(Exception):
    pass


def _normalize(path: str) -> str:
    """
    Normalize a user-supplied path into an absolute path under SANDBOX_ROOT.
    - Disallow escaping the sandbox via .. or absolute paths
    - Disallow symlink traversal at any component in the path
    Returns the fully resolved real path.
    """
    # Strip drive letters and leading separators in a cross-platform way
    rel = path.lstrip("/\\")
    # Join and resolve symlinks to a canonical path
    candidate = os.path.join(SANDBOX_ROOT, rel)
    real = os.path.realpath(candidate)
    # Ensure resulting path stays within sandbox
    if not (real == SANDBOX_ROOT or real.startswith(SANDBOX_ROOT + os.sep)):
        raise PathError(f"Path escapes sandbox: {real}")
    # Walk each component and reject any symlink within the sandbox
    norm_rel = os.path.normpath(rel)
    # Handle the case where rel could be '.' or ''
    if norm_rel in (".", ""):
        return SANDBOX_ROOT
    cur = SANDBOX_ROOT
    for part in norm_rel.split(os.sep):
        if not part or part == ".":
            continue
        cur = os.path.join(cur, part)
        try:
            if os.path.islink(cur):
                raise PathError(f"Symlink in path not allowed: {cur}")
        except FileNotFoundError:
            # If the path doesn't exist yet, we cannot check islink; stop checking further.
            break
    return real


def _check_consent(token: Optional[ConsentToken], scope: str):
    if not REQUIRE_CONSENT:
        return
    if token is None:
        raise ConsentError("Consent token required")
    if scope not in token.scopes and "*" not in token.scopes:
        raise ConsentError(f"Scope '{scope}' not granted")


# ----------------- Public API -----------------


def list_dir(path: str = "/", token: Optional[ConsentToken] = None) -> Dict:
    _check_consent(token, LIST_SCOPE)
    p = _normalize(path)
    if olympus_tools_rs is not None:
        return {"path": p, "entries": olympus_tools_rs.list_dir(p)}
    # Fallback: Python implementation
    entries = []
    try:
        for name in os.listdir(p):
            full = os.path.join(p, name)
            st = os.stat(full)
            entries.append(
                {"name": name, "is_dir": stat.S_ISDIR(st.st_mode), "size": st.st_size}
            )
    except FileNotFoundError:
        entries = []
    return {"path": p, "entries": entries}


def read_file(path: str, token: Optional[ConsentToken] = None) -> Dict:
    _check_consent(token, READ_SCOPE)
    p = _normalize(path)
    if not os.path.exists(p):
        raise FileNotFoundError(p)
    if olympus_tools_rs is not None:
        data = olympus_tools_rs.read_file(p)
        return {"path": p, "bytes": len(data), "content": data.decode(errors="replace")}
    with open(p, "rb") as f:
        data = f.read()
    return {"path": p, "bytes": len(data), "content": data.decode(errors="replace")}


def write_file(
    path: str,
    content: str,
    overwrite: bool = True,
    token: Optional[ConsentToken] = None,
) -> Dict:
    _check_consent(token, WRITE_SCOPE)
    p = _normalize(path)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    if os.path.exists(p) and not overwrite:
        raise FileExistsError(p)
    if olympus_tools_rs is not None:
        olympus_tools_rs.write_file(p, content.encode())
    else:
        with open(p, "wb") as f:
            f.write(content.encode())
    return {"path": p, "bytes": len(content)}


def delete_path(
    path: str, recursive: bool = False, token: Optional[ConsentToken] = None
) -> Dict:
    _check_consent(token, DELETE_SCOPE)
    p = _normalize(path)
    if not os.path.exists(p):
        return {"path": p, "deleted": False}
    if olympus_tools_rs is not None:
        olympus_tools_rs.delete_path(p, recursive)
    else:
        if os.path.isdir(p):
            if recursive:
                shutil.rmtree(p)
            else:
                os.rmdir(p)
        else:
            os.remove(p)
    return {"path": p, "deleted": True}
