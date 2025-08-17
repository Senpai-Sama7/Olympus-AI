import os
from enum import Enum

class ConsentScope(str, Enum):
    READ_FS = "read_fs"
    WRITE_FS = "write_fs"
    NET_GET = "net_get"
    NET_POST = "net_post"
    EXEC_CODE = "exec_code"

class ConsentManager:
    def __init__(self):
        self.granted_scopes = set()

    def request_consent(self, scope: ConsentScope) -> bool:
        try:
            from desktop.app.main import api
            return api.show_consent_prompt(f"Allow access to {scope.value}?")
        except (ImportError, AttributeError):
            # Fallback for non-desktop environments: default deny in prod,
            # allow only if explicitly enabled for development convenience.
            return os.getenv("OLY_AUTO_CONSENT", "false").lower() in ("1", "true", "yes")

    def has_consent(self, scope: ConsentScope) -> bool:
        if scope in self.granted_scopes:
            return True
        if self.request_consent(scope):
            self.granted_scopes.add(scope)
            return True
        return False
