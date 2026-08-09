"""POST /api/command — отправка команды ассистенту (кладётся в очередь)."""
from http.server import BaseHTTPRequestHandler
import uuid, time
from _shared import (
    send_json, read_json, auth_required, get_state, now, env_assistant_name,
)


# Простые шаблоны ответов для UI, чтобы было живо без OpenAI.
# На проде подключи свой ИИ-бэкенд через webhook.
_LOCAL_REPLIES = {
    "status":  "Система в норме. Все модули онлайн.",
    "time":    f"Локальное время сервера: {time.strftime('%H:%M:%S')}",
    "news":    "Последние новости загружаются… (подключи news API в command.py)",
    "notes":   "Заметка принята. Сохраню в очередь.",
}


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        if not auth_required(self):
            return
        data = read_json(self)
        text = str(data.get("text", "")).strip()
        if not text:
            send_json(self, 400, {"ok": False, "error": "Пустая команда"})
            return

        key = text.lower().strip()
        reply = _LOCAL_REPLIES.get(
            key,
            f"{env_assistant_name()} принял: «{text}». На реальном ПК это запустит соответствующий скилл.",
        )

        # В очередь — чтобы твой локальный MARK мог её забрать
        item = {
            "id":   uuid.uuid4().hex[:8],
            "text": text,
            "ts":   now(),
            "status": "pending",
        }
        get_state()["queue"].append(item)
        # обрезаем до 200
        if len(get_state()["queue"]) > 200:
            get_state()["queue"] = get_state()["queue"][-200:]

        send_json(self, 200, {"ok": True, "reply": reply, "id": item["id"]})

    def do_OPTIONS(self):
        self._cors()

    def _cors(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()

    def log_message(self, *a, **k):  # noqa
        pass
