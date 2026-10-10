"""Оглавление «На этой странице» в headless Firefox: блок не шире --toc-max-width (доля ширины окна),
пункты всегда с новой строки, длинный текст переносится внутри блока.

Собирает демо-книгу во временный каталог, подменяет текст первого пункта оглавления на длинный и измеряет
блок по file://. Результаты приходят маячком на локальный сервер. Без Firefox тест пропускается.
"""
import contextlib
import http.server
import io
import json
import os
import re
import shutil
import subprocess
import tempfile
import threading
import time
import unittest
from urllib.parse import urlparse, parse_qs

from engine.build import build
from engine.config import load_config
from engine.tests import DEMO_ROOT, HAS_DEMO

BROWSER = os.environ.get("MERMAID_BROWSER") or shutil.which("firefox")
PAGE = "docs/01-osnovy/1-spiski-i-kod.html"
LONG_TITLE = ("Очень длинный пункт оглавления " * 20)[:260]
TOC_LINK = re.compile(r'(<li class="toc-item toc-h\d"><a href="#[^"]+">)([^<]*)(</a>)')

# Геометрия: блок, его ширина, пункты. Окно отдаёт innerWidth — доля считается от него же.
MEASURE = """<script>(function(){function go(){
var t=document.getElementById('article-toc'),r={win:window.innerWidth};
if(t){var b=t.getBoundingClientRect();
r.toc={w:b.width,left:b.left,right:b.right,sw:t.scrollWidth,cw:t.clientWidth,disp:getComputedStyle(t).display};
r.items=[].map.call(t.querySelectorAll('li'),function(li){var x=li.getBoundingClientRect();return {top:x.top,bottom:x.bottom,left:x.left,right:x.right};});}
var im=new Image();im.src='http://127.0.0.1:%(port)d/?d='+encodeURIComponent(JSON.stringify(r));}
setTimeout(go,1200);})();</script>"""


def measure(html_path, transform):
    """Открывает подготовленную страницу в Firefox и возвращает результат маячка."""
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
    probe = html_path[:-5] + ".__toc_probe.html"
    with open(probe, "w", encoding="utf-8") as fp:
        fp.write(html.replace("</body>", MEASURE % {"port": server.server_address[1]} + "</body>"))
    try:
        with tempfile.TemporaryDirectory() as profile:
            proc = subprocess.Popen([BROWSER, "--headless", "--no-remote", "--profile", profile,
                                     "--window-size=1440,900", "file://" + probe],
                                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            try:
                for _ in range(600):
                    if "r" in got:
                        break
                    time.sleep(0.1)
            finally:
                proc.terminate()
                proc.wait(10)
    finally:
        server.shutdown()
        server.server_close()
        os.remove(probe)
    return got.get("r")


@unittest.skipUnless(HAS_DEMO, "демо-книги нет: это книга, а не репозиторий движка")
@unittest.skipUnless(BROWSER, "нет Firefox (PATH или MERMAID_BROWSER)")
class TocLayoutTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.dist = os.path.join(cls.tmp.name, "dist")
        with contextlib.redirect_stdout(io.StringIO()):
            build(load_config(os.path.join(DEMO_ROOT, "book.toml")), dist_dir=cls.dist, is_pilot=False)
        cls.path = os.path.join(cls.dist, PAGE)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def long_item(self, html):
        return TOC_LINK.sub(lambda m: m.group(1) + LONG_TITLE + m.group(3), html, count=1)

    def assert_block(self, r):
        self.assertIsNotNone(r, "страница не отправила результат в Firefox")
        self.assertGreater(r["win"], 1024, "окно уже порога, при котором оглавление скрыто")
        toc, items = r["toc"], r["items"]
        self.assertEqual(toc["disp"], "block")
        self.assertGreater(len(items), 1)
        for i, item in enumerate(items):
            self.assertGreaterEqual(item["left"], toc["left"] - 0.5, f"пункт {i} вылез слева")
            self.assertLessEqual(item["right"], toc["right"] + 0.5, f"пункт {i} вылез справа")
            if i:
                self.assertGreaterEqual(item["top"], items[i - 1]["bottom"] - 0.5, f"пункт {i} начат внутри предыдущего")
        self.assertLessEqual(toc["sw"], toc["cw"], "блок оглавления прокручивается по горизонтали")

    def test_long_item_capped_at_twenty_percent(self):
        r = measure(self.path, self.long_item)
        self.assert_block(r)
        share = r["toc"]["w"] / r["win"]
        self.assertLessEqual(share, 0.2 + 1e-6)
        self.assertGreater(share, 0.199, "длинный пункт должен упираться в предел, а не быть уже него")
        first = r["items"][0]
        self.assertGreater(first["bottom"] - first["top"], 40, "длинный пункт должен переноситься на вторую строку")

    def test_short_items_do_not_stretch_block(self):
        r = measure(self.path, lambda h: h)
        self.assert_block(r)
        self.assertLess(r["toc"]["w"] / r["win"], 0.2, "короткое оглавление не должно доходить до предела")

    def test_limit_is_one_variable(self):
        style = "<style>:root{--toc-max-width:30vw}</style>"
        r = measure(self.path, lambda h: self.long_item(h).replace("</head>", style + "</head>", 1))
        self.assert_block(r)
        self.assertAlmostEqual(r["toc"]["w"] / r["win"], 0.30, places=3)


if __name__ == "__main__":
    unittest.main()
