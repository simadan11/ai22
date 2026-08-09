"""GET /api/health — статус сервиса."""
from http.server import BaseHTTPRequestHandler
from _shared import send_json, env_assistant_name, env_user_name, now


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        h = now() // 3600
        send_json(self, 200, {
            "ok": True,
            "service": "edit-mobile",
            "version": "1.0.0",
            "assistant": env_assistant_name(),
            "user": env_user_name(),
            "greeting": _greet(h),
            "subtitle": "Ассистент на связи. Выбери действие.",
            "uptime_hint": "Vercel serverless",
        })

    def log_message(self, *a, **k):  # noqa
        pass


def _greet(hour_utc: int) -> str:
    # локально у пользователя — мы на это не влияем, даём нейтральное
    if 5 <= hour_utc < 12:
        return "Доброе утро"
    if 12 <= hour_utc < 18:
        return "Добрый день"
    if 18 <= hour_utc < 23:
        return "Добрый вечер"
    return "Доброй ночи"
