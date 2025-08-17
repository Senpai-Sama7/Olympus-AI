import os
from typing import Optional


def _sandbox_root() -> str:
    return os.path.realpath(
        os.path.expanduser(os.environ.get("SANDBOX_ROOT", "./workspace"))
    )


def _resolve(rel_path: str) -> str:
    root = _sandbox_root()
    abs_path = os.path.realpath(os.path.join(root, rel_path))
    if not abs_path.startswith(root + os.sep) and abs_path != root:
        raise PermissionError("Artifact path must be under SANDBOX_ROOT")
    return abs_path


def save_bytes(rel_path: str, content: bytes, mode: Optional[str] = None) -> str:
    path = _resolve(rel_path)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, mode or "wb") as f:
        f.write(content)
    return path


def save_text(rel_path: str, content: str, encoding: str = "utf-8") -> str:
    path = _resolve(rel_path)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding=encoding) as f:
        f.write(content)
    return path
