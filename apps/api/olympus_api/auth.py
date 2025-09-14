import os
import time
from typing import Dict, Optional

import jwt
from fastapi import HTTPException, Request


ALGO = "HS256"


def _secret() -> Optional[str]:
    return os.getenv("AUTH_JWT_SECRET")


def get_current_user(request: Request) -> Dict:
    if os.getenv("AUTH_REQUIRED", "false").lower() not in ("1", "true", "yes"):
        # auth disabled; attach anonymous identity
        request.state.user = {"sub": "anon", "scopes": ["*"]}
        return request.state.user
    authz = request.headers.get("Authorization", "")
    if not authz.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="missing bearer token")
    token = authz.split(" ", 1)[1]
    sec = _secret()
    if not sec:
        raise HTTPException(status_code=500, detail="server auth not configured")
    try:
        claims = jwt.decode(token, sec, algorithms=[ALGO])
        if "exp" in claims and int(claims["exp"]) < int(time.time()):
            raise HTTPException(status_code=401, detail="token expired")
        request.state.user = claims
        return claims
    except jwt.PyJWTError as e:
        raise HTTPException(status_code=401, detail=f"invalid token: {e}")
