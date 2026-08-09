"""GET /api/queue — список отправленных команд (для синка с локальным ПК)."""
from http.server import BaseHTTPRequestHandler
from _shared import send_json, auth_required, get_state


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if not auth_required(self):
            return
        send_json(self, 200, {
            "ok": True,
            "items": get_state()["queue"][-50:],
        })

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Authorization")
        self.end_headers()

    def log_message(self, *a, **k):  # noqa
        pass
