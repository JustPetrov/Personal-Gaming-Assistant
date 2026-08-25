from __future__ import annotations

import json
from pathlib import Path
import httpx
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()
TOKENS = Path('data/push_tokens.json')

class PushRegistration(BaseModel):
    token: str

@router.post('/api/notifications/register')
def register(reg: PushRegistration):
    TOKENS.parent.mkdir(parents=True, exist_ok=True)
    tokens = json.loads(TOKENS.read_text()) if TOKENS.exists() else []
    if reg.token not in tokens: tokens.append(reg.token)
    TOKENS.write_text(json.dumps(tokens, indent=2))
    return {'registered': True}

def send_push(title: str, body: str):
    if not TOKENS.exists(): return 0
    tokens = json.loads(TOKENS.read_text())
    messages = [{'to': t, 'title': title, 'body': body, 'sound': 'default'} for t in tokens]
    if not messages: return 0
    r = httpx.post('https://exp.host/--/api/v2/push/send', json=messages, timeout=20)
    r.raise_for_status()
    return len(messages)
