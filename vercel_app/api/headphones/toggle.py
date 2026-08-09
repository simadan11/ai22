"""POST /api/headphones/toggle — вкл/выкл режим наушников."""
from http.server import BaseHTTPRequestHandler
from _lib.shared import send_json, read_json, auth_required, get_state, now


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        if not auth_required(self):
            return
        data = read_json(self)
        on = bool(data.get("on", False))

        hp = get_state()["hp"]
        hp["enabled"]   = on
        hp["activity"]  = "idle" if not on else "ready"
        hp["connected"] = on
        hp["device"]    = "Bluetooth Headset" if on else ""
        hp["mic"]       = "BT Hands-Free"     if on else ""

        ev = {
            "ts":   now(),
            "text": "Режим наушников активирован" if on else "Режим наушников выключен",
            "kind": "ok" if on else "muted",
        }
        hp["log"].append(ev)
        if len(hp["log"]) > 100:
            hp["log"] = hp["log"][-100:]

        send_json(self, 200, {"ok": True, "enabled": on})

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()

    def log_message(self, *a, **k):  # noqa
        pass
