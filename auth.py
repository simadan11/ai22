"""POST /api/auth — вход по PIN, выдаёт токен."""
from http.server import BaseHTTPRequestHandler
from _shared import send_json, read_json, gen_token, now, get_state, env_pin


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        data = read_json(self)
        pin = str(data.get("pin", "")).strip()

        if pin != env_pin():
            send_json(self, 200, {"ok": False, "error": "Неверный PIN"})
            return

        token = gen_token()
        get_state()["tokens"][token] = {"created": now()}
        send_json(self, 200, {
            "ok": True,
            "token": token,
            "expires_in": 30 * 86400,
        })

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()

    def log_message(self, *a, **k):  # noqa
        pass
