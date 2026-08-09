"""
⚠️  STUB-файл, оставлен для обратной совместимости.

Vercel пытается собрать ЛЮБОЙ .py в api/ как endpoint, и для каждого требует
класс `handler`. Этот файл раньше лежал тут как общий хелпер и ломал билд
с ошибкой:
    Error: Could not find a top-level "handler" in "api/_shared.py".

Сейчас настоящий модуль — `vercel_app/_lib/shared.py`. Этот файл содержит
только no-op `handler` на случай, если Vercel по какой-то причине всё ещё
видит старую копию. Реальные endpoint'ы импортируют из `_lib.shared`.
"""
from http.server import BaseHTTPRequestHandler


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Этот endpoint не должен вызываться; если кто-то всё-таки стукнул —
        # отдадим 404, чтобы Vercel не отдавал 500.
        self.send_response(404)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(b'{"ok":false,"error":"use /lib/shared.py"}')

    def do_POST(self):
        self.do_GET()

    def log_message(self, *args, **kwargs):
        pass
