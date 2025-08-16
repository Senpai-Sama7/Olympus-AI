import os
from typing import List


def get_allow_write_roots() -> List[str]:
    raw = os.environ.get("ALLOW_WRITE_DIRS", "./workspace,./data")
    roots = [os.path.realpath(os.path.expanduser(p.strip())) for p in raw.split(",") if p.strip()]
    return roots


def is_path_allowed(path: str) -> bool:
    real = os.path.realpath(os.path.expanduser(path))
    for root in get_allow_write_roots():
        if real.startswith(os.path.realpath(root) + os.sep) or real == os.path.realpath(root):
            return True
    return False


def resolve_for_write(relative_or_abs_path: str) -> str:
    candidate = os.path.realpath(os.path.expanduser(relative_or_abs_path))
    if os.path.isabs(candidate):
        if not is_path_allowed(candidate):
            raise PermissionError(f"Path not allow-listed: {candidate}")
        return candidate
    # If relative, put under first allow-listed root
    roots = get_allow_write_roots()
    if not roots:
        raise RuntimeError("No allow-listed roots configured")
    abs_path = os.path.realpath(os.path.join(roots[0], relative_or_abs_path))
    if not is_path_allowed(abs_path):
        raise PermissionError(f"Resolved path not allow-listed: {abs_path}")
    return abs_path


def write_text(path: str, data: str) -> str:
    abs_path = resolve_for_write(path)
    os.makedirs(os.path.dirname(abs_path), exist_ok=True)
    with open(abs_path, "w", encoding="utf-8") as f:
        f.write(data)
    return abs_path


def read_text(path: str) -> str:
    abs_path = os.path.realpath(os.path.expanduser(path))
    if not is_path_allowed(abs_path):
        raise PermissionError(f"Path not allow-listed: {abs_path}")
    with open(abs_path, "r", encoding="utf-8") as f:
        return f.read()
