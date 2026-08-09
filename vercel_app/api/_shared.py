"""
Shared helpers for Vercel Python Functions.

Хранилище — in-memory (живёт только во время "холодного старта" функции).
Для постоянного состояния подключи Vercel KV / Upstash Redis (см. README).
"""
import os
import json
import time
import uuid
from http.server import BaseHTTPRequestHandler

# Простое in-memory состояние.
# ВНИМАНИЕ: между холодными стартами разных функций состояние НЕ делится.
# Для реального prod подключи Vercel KV.
_STATE = {
    "queue": [],          # [{"id":..,"text":..,"ts":..,"status":"pending"}]
    "hp": {
        "enabled": False,
        "device":  "",
        "mic":     "",
        "activity": "idle",
        "connected": False,
        "log": [],        # [{"ts":..,"text":..,"kind":..}]
    },
    "tokens": {},         # token -> {"created":..}
}


def now() -> int:
    return int(time.time())


def gen_token() -> str:
    return uuid.uuid4().hex


def get_state():
    return _STATE


def is_valid_token(token: str) -> bool:
    if not token:
        return False
    t = _STATE["tokens"].get(token)
    if not t:
        return False
    # токен живёт 30 дней
    if now() - t["created"] > 30 * 86400:
        del _STATE["tokens"][token]
        return False
    return True


def auth_required(handler: BaseHTTPRequestHandler) -> bool:
    auth = handler.headers.get("Authorization", "")
    token = ""
    if auth.startswith("Bearer "):
        token = auth[7:].strip()
    else:
        # fallback: ?token=...  для удобства
        token = handler.path.split("token=", 1)[-1].split("&")[0] if "token=" in handler.path else ""
    if not is_valid_token(token):
        send_json(handler, 401, {"ok": False, "error": "Unauthorized"})
        return False
    return True


def send_json(handler: BaseHTTPRequestHandler, status: int, payload: dict):
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.send_header("Cache-Control", "no-store")
    handler.send_header("Access-Control-Allow-Origin", "*")
    handler.end_headers()
    handler.wfile.write(body)


def read_json(handler: BaseHTTPRequestHandler) -> dict:
    length = int(handler.headers.get("Content-Length", "0") or 0)
    if length <= 0:
        return {}
    raw = handler.rfile.read(length)
    try:
        return json.loads(raw.decode("utf-8"))
    except Exception:
        return {}


def env_pin() -> str:
    """PIN берётся из env, фоллбэк 1234."""
    return os.environ.get("EDIT_PIN", "1234")


def env_assistant_name() -> str:
    return os.environ.get("ASSISTANT_NAME", "EDIT")


def env_user_name() -> str:
    return os.environ.get("USER_NAME", "Владелец")
