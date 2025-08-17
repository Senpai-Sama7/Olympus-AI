from __future__ import annotations

import fnmatch
import os
import re
from typing import Dict, List, Optional

from .fs import _normalize, ConsentToken, REQUIRE_CONSENT

SEARCH_SCOPE = "search_fs"


def _check_search_consent(token: Optional[ConsentToken]):
    if not REQUIRE_CONSENT:
        return
    if token is None or ("*" not in token.scopes and SEARCH_SCOPE not in token.scopes):
        raise PermissionError("Consent with 'search_fs' scope required")


def glob_paths(pattern: str, start: str = "/", token: Optional[ConsentToken] = None) -> Dict:
    _check_search_consent(token)
    root = _normalize(start)
    matches: List[str] = []
    for base, _dirs, files in os.walk(root):
        rel_base = os.path.relpath(base, root)
        for name in files:
            rel = os.path.normpath(os.path.join(rel_base, name))
            if rel == ".":
                rel = name
            if fnmatch.fnmatch(rel, pattern) or fnmatch.fnmatch(name, pattern):
                matches.append(os.path.join(base, name))
    return {"root": root, "pattern": pattern, "matches": matches}


def search_file_content(pattern: str, path: str, token: Optional[ConsentToken] = None, max_bytes: int = 2_000_000) -> Dict:
    _check_search_consent(token)
    p = _normalize(path)
    flags = re.MULTILINE
    rx = re.compile(pattern, flags)
    try:
        with open(p, "rb") as f:
            data = f.read(max_bytes)
    except FileNotFoundError:
        raise
    text = data.decode(errors="replace")
    matches = []
    for i, line in enumerate(text.splitlines(), start=1):
        if rx.search(line):
            matches.append({"line": i, "text": line})
    return {"path": p, "pattern": pattern, "matches": matches}

