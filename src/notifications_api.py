from __future__ import annotations

import json
from pathlib import Path

import httpx
from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter()
TOKENS = Path("data/push_tokens.json")


class PushRegistration(BaseModel):
    token: str = Field(min_length=1)


@router.post("/api/notifications/register")
def register(reg: PushRegistration):
    TOKENS.parent.mkdir(parents=True, exist_ok=True)
    try:
        tokens = json.loads(TOKENS.read_text(encoding="utf-8")) if TOKENS.exists() else []
    except (OSError, json.JSONDecodeError):
        tokens = []
    if not isinstance(tokens, list):
        tokens = []
    if reg.token not in tokens:
        tokens.append(reg.token)
    TOKENS.write_text(json.dumps(tokens, indent=2), encoding="utf-8")
    return {"registered": True, "count": len(tokens)}


def send_push(title: str, body: str, url: str | None = None) -> int:
    if not TOKENS.exists():
        return 0
    try:
        tokens = json.loads(TOKENS.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return 0
    if not isinstance(tokens, list):
        return 0
    messages = []
    for token in tokens:
        if not isinstance(token, str) or not token.strip():
            continue
        messages.append({
            "to": token,
            "title": title,
            "body": body,
            "sound": "default",
            "priority": "high",
            "data": {"url": url} if url else {},
        })
    if not messages:
        return 0
    response = httpx.post(
        "https://exp.host/--/api/v2/push/send",
        json=messages,
        timeout=20,
    )
    response.raise_for_status()
    return len(messages)
