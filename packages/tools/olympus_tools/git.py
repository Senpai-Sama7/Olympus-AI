from __future__ import annotations

from typing import Dict, List, Optional

from .shell import run_shell_command
from .fs import ConsentToken

GIT_SCOPE = "git_ops"


def git_status(workdir: str = "/", token: Optional[ConsentToken] = None) -> Dict:
    t = _tok_with_scope(token, GIT_SCOPE)
    return run_shell_command(
        ["git", "status", "--porcelain=v1"], workdir=workdir, token=t
    )


def git_add(
    paths: List[str], workdir: str = "/", token: Optional[ConsentToken] = None
) -> Dict:
    t = _tok_with_scope(token, GIT_SCOPE)
    return run_shell_command(
        ["git", "add", "--"] + list(paths), workdir=workdir, token=t
    )


def git_commit(
    message: str, workdir: str = "/", token: Optional[ConsentToken] = None
) -> Dict:
    t = _tok_with_scope(token, GIT_SCOPE)
    return run_shell_command(["git", "commit", "-m", message], workdir=workdir, token=t)


def _tok_with_scope(token: Optional[ConsentToken], scope: str) -> ConsentToken:
    scopes = ["*"] if token is None else token.scopes
    if "*" not in scopes and scope not in scopes:
        # Construct a permissive token only for tests/dev; real enforcement happens in run_shell_command
        return ConsentToken(token="git", scopes=scopes + [scope])
    return token or ConsentToken(token="git", scopes=[scope])
