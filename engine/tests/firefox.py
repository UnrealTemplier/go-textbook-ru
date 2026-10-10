"""Общий маячок для браузерных тестов: страница открывается в headless Firefox по file://, её скрипт
присылает результат GET-запросом на локальный сервер (?d=<JSON>). Без Firefox тесты пропускаются
(PATH или MERMAID_BROWSER).
"""
import http.server
import json
import os
import shutil
import subprocess
import tempfile
import threading
import time
from urllib.parse import urlparse, parse_qs

BROWSER = os.environ.get("MERMAID_BROWSER") or shutil.which("firefox")

# Функция send(obj) — из страницы в тест; вызывается скриптом сценария
SEND_JS = "<script>window.send=function(d){var im=new Image();im.src='http://127.0.0.1:%(port)d/?d='+encodeURIComponent(JSON.stringify(d));};</script>"


def probe(html_path, transform, script, timeout=60):
    """Открывает страницу с добавленным в конец скриптом сценария и возвращает присланный send(obj) или None.

    transform(html) — подготовка HTML; script — JS, который вызывает send(...) когда готов.
    """
    with open(html_path, encoding="utf-8") as fp:
        html = transform(fp.read())
    got = {}

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            q = parse_qs(urlparse(self.path).query)
            if "d" in q:
                got["r"] = json.loads(q["d"][0])
            self.send_response(204)
            self.end_headers()

        def log_message(self, *a):
            pass

    server = http.server.HTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    inject = (SEND_JS % {"port": server.server_address[1]}) + "<script>" + script + "</script>"
    probe_path = html_path[:-5] + ".__probe.html"
    with open(probe_path, "w", encoding="utf-8") as fp:
        fp.write(html.replace("</body>", inject + "</body>", 1))
    try:
        with tempfile.TemporaryDirectory() as profile:
            proc = subprocess.Popen([BROWSER, "--headless", "--no-remote", "--profile", profile,
                                     "--window-size=1440,900", "file://" + probe_path],
                                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            try:
                for _ in range(int(timeout * 10)):
                    if "r" in got:
                        break
                    time.sleep(0.1)
            finally:
                proc.terminate()
                proc.wait(10)
    finally:
        server.shutdown()
        server.server_close()
        os.remove(probe_path)
    return got.get("r")
