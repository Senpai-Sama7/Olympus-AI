import os
from typing import List


def get_allow_write_roots() -> List[str]:
    raw = os.environ.get("ALLOW_WRITE_DIRS", "./workspace,./data")
    roots = [
        os.path.realpath(os.path.expanduser(p.strip()))
        for p in raw.split(",")
        if p.strip()
    ]
    return roots


def is_path_allowed(path: str) -> bool:
    real = os.path.realpath(os.path.expanduser(path))
    for root in get_allow_write_roots():
        if real.startswith(os.path.realpath(root) + os.sep) or real == os.path.realpath(
            root
        ):
            return True
    return False


def resolve_for_write(relative_or_abs_path: str) -> str:
    candidate = os.path.realpath(os.path.expanduser(relative_or_abs_path))
    if os.path.islink(candidate):
        raise PermissionError(f"Path is a symlink: {candidate}")
    if os.path.isabs(candidate):
        if not is_path_allowed(candidate):
            raise PermissionError(f"Path not allow-listed: {candidate}")
        return candidate
    # If relative, put under first allow-listed root
    roots = get_allow_write_roots()
    if not roots:
        raise RuntimeError("No allow-listed roots configured")
    abs_path = os.path.realpath(os.path.join(roots[0], relative_or_abs_path))
    if os.path.islink(abs_path):
        raise PermissionError(f"Resolved path is a symlink: {abs_path}")
    if not is_path_allowed(abs_path):
        raise PermissionError(f"Resolved path not allow-listed: {abs_path}")
    return abs_path


from .consent import ConsentManager, ConsentScope

consent_manager = ConsentManager()

def write_text(path: str, data: str) -> str:
    if not consent_manager.has_consent(ConsentScope.WRITE_FS):
        raise PermissionError("Consent not granted for writing to the file system")
    abs_path = resolve_for_write(path)
    os.makedirs(os.path.dirname(abs_path), exist_ok=True)
    with open(abs_path, "w", encoding="utf-8") as f:
        f.write(data)
    return abs_path


def read_text(path: str) -> str:
    if not consent_manager.has_consent(ConsentScope.READ_FS):
        raise PermissionError("Consent not granted for reading from the file system")
    abs_path = os.path.realpath(os.path.expanduser(path))
    if not is_path_allowed(abs_path):
        raise PermissionError(f"Path not allow-listed: {abs_path}")
    with open(abs_path, "r", encoding="utf-8") as f:
        return f.read()

def safe_join(base: str, *paths: str) -> str:
    base = os.path.realpath(os.path.expanduser(base))
    if not is_path_allowed(base):
        raise PermissionError(f"Base path not allow-listed: {base}")

    path = os.path.normpath(os.path.join(base, *paths))

    if os.path.commonprefix((base, path)) != base:
        raise PermissionError("Path traversal detected")

    return path
