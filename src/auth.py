from __future__ import annotations

import hashlib
import hmac
import os
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, Request

USERNAME = os.getenv("APP_USERNAME", "bendemen")
# Never commit the real password. Configure APP_PASSWORD on the VPS.
PASSWORD = os.getenv("APP_PASSWORD")

SESSION_COOKIE = "pga_session"
SESSION_TTL = timedelta(hours=12)
_sessions: dict[str, datetime] = {}


def verify_password(candidate: str) -> bool:
    if not PASSWORD:
        return False
    return hmac.compare_digest(candidate, PASSWORD)


def create_session() -> str:
    token = secrets.token_urlsafe(32)
    _sessions[token] = datetime.now(timezone.utc) + SESSION_TTL
    return token


def valid_session(token: str | None) -> bool:
    if not token:
        return False
    expires = _sessions.get(token)
    if not expires:
        return False
    if expires <= datetime.now(timezone.utc):
        _sessions.pop(token, None)
        return False
    return True


def require_auth(request: Request) -> None:
    if not valid_session(request.cookies.get(SESSION_COOKIE)):
        raise HTTPException(status_code=401, detail="Authentication required")
