"""GET /api/headphones/status — статус режима наушников."""
from http.server import BaseHTTPRequestHandler
from _shared import send_json, auth_required, get_state


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if not auth_required(self):
            return
        hp = get_state()["hp"]
        send_json(self, 200, {
            "ok": True,
            "enabled":   hp["enabled"],
            "device":    hp["device"] or None,
            "mic":       hp["mic"]    or None,
            "activity":  hp["activity"],
            "connected": hp["connected"],
        })

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Authorization")
        self.end_headers()

    def log_message(self, *a, **k):  # noqa
        pass
