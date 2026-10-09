"""Тест рантайма window.__BOOK__ в headless Firefox (анализ § 4.9, 7 сценариев) и модального окна Mermaid (А3м).

Собирает демо-книгу (корень репозитория движка) во временный каталог, кладёт рядом пробные страницы со скриптами сценариев
и обходит их одной цепочкой. Ранний скрипт стоит сразу после inline-скрипта рантайма и
фиксирует состояние <html> до отрисовки; поздний — после DOMContentLoaded. Результаты приходят
маячком на локальный сервер. Без Firefox тест пропускается.
"""
import contextlib
import io
import json
import os
import shutil
import subprocess
import tempfile
import threading
import http.server
import unittest
from urllib.parse import urlparse, parse_qs

from engine.build import build
from engine.config import load_config

from engine.tests import DEMO_ROOT, HAS_DEMO

BROWSER = os.environ.get("MERMAID_BROWSER") or shutil.which("firefox")
RUNTIME_END = "window.__BOOK__.init();</script>"

STATE_JS = ("({theme:document.documentElement.dataset.theme,"
            "attrs:Array.from(document.documentElement.attributes).map(a=>a.name)"
            ".filter(n=>n.startsWith('data-')&&!['data-theme','data-available-themes','data-theme-labels'].includes(n)),"
            "style:document.documentElement.getAttribute('style')||''})")

PAGES = {
    "formulas": "docs/01-osnovy/2-formuly.html",
    "code": "docs/01-osnovy/1-spiski-i-kod.html",
    "mermaid": "docs/01-osnovy/razdel-vynosok/1-vynoski-i-skhemy.html",
}

# (имя, страница, js до рантайма, js на ранней стадии и после загрузки, удалить рантайм, перезагрузка)
SCENARIOS = [
    ("empty", "formulas", "localStorage.clear();", "", False),
    ("saved", "formulas", "localStorage.setItem('demo_theme','paper');", "", True),
    ("unknown", "formulas", "localStorage.setItem('demo_theme','neon');", "", False),
    ("no_storage", "formulas", "Object.defineProperty(window,'localStorage',{get(){throw new Error('denied')}});", "", False),
    ("old_keys", "formulas",
     "localStorage.clear();localStorage.setItem('demo_retro_effects_dark','{\"site\":{\"crt\":{\"enabled\":true,\"strength\":80}}}');"
     "localStorage.setItem('demo_retro_effects','{\"trail\":{\"enabled\":true}}');", "", False),
    ("toggle", "mermaid", "localStorage.clear();", "toggle", False),
    ("old_html_mermaid", "mermaid", "", "", "strip"),
    ("old_html_code", "code", "", "copy", "strip"),
    ("old_html_math", "formulas", "", "", "strip"),
    ("modal", "mermaid", "", "modal", False),
    ("no_modal", "code", "", "nomodal", False),
]

LATE_JS = """<script>const sleep=ms=>new Promise(r=>setTimeout(r,ms));
window.addEventListener('load',()=>setTimeout(async()=>{const r={name:%(name)s};try{
 if(%(reload)s && !location.search.includes('r')){ location.replace(location.href+'?r'); return; }
 r.early=window.__early||null; r.late=%(state)s; r.book=!!window.__BOOK__;
 r.mermaid=[document.querySelectorAll('pre.mermaid').length,document.querySelectorAll('pre.mermaid svg').length];
 r.katex=document.querySelectorAll('.katex').length;
 if(%(action)s==='toggle'){document.getElementById('theme-switcher-btn').click();await sleep(800);
   r.afterToggle=document.documentElement.dataset.theme; r.stored=localStorage.getItem('demo_theme');
   r.mermaidAfter=document.querySelectorAll('pre.mermaid svg').length;
   r.syntaxError=document.body.innerText.includes('Syntax error in text');}
 if(%(action)s==='copy'){let copied=null;
   Object.defineProperty(navigator,'clipboard',{value:{writeText:t=>{copied=t;return Promise.resolve();}}});
   document.querySelector('[data-action="copy-code"]').click();await sleep(100);r.copied=(copied||'').length;}
 if(%(action)s==='modal'){const m=document.getElementById('mermaid-modal');
   const scale=()=>{const s=m.querySelector('svg');return s?s.style.transform:null;};
   const click=a=>document.querySelector('#mermaid-modal [data-action="'+a+'"]').click();
   document.querySelector('[data-action="mermaid-fullscreen"]').click();await sleep(100);
   r.opened=m.classList.contains('active');r.hidden=m.getAttribute('aria-hidden');r.svg=!!m.querySelector('svg');
   click('zoom-mermaid-in');click('zoom-mermaid-in');r.zoomIn=scale();click('zoom-mermaid-out');r.zoomOut=scale();
   click('zoom-mermaid-reset');r.zoomReset=scale();click('close-mermaid-modal');r.closedByButton=!m.classList.contains('active');
   document.querySelector('[data-action="mermaid-fullscreen"]').click();await sleep(100);
   document.dispatchEvent(new KeyboardEvent('keydown',{key:'Escape'}));r.closedByEsc=!m.classList.contains('active');}
 if(%(action)s==='nomodal'){r.modal=!!document.getElementById('mermaid-modal');
   document.dispatchEvent(new KeyboardEvent('keydown',{key:'Escape'}));window.zoomMermaid(0.2);window.resetMermaidZoom();}
}catch(e){r.exception=String(e);} r.errors=window.__errors;
const im=new Image();im.onload=im.onerror=()=>{%(next)s};
im.src='http://127.0.0.1:%(port)d/?d='+encodeURIComponent(JSON.stringify(r));},1200));</script>"""


@unittest.skipUnless(HAS_DEMO, "демо-книги нет: это книга, а не репозиторий движка")
@unittest.skipUnless(BROWSER, "нет Firefox (PATH или MERMAID_BROWSER)")
class BookRuntimeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.dist = os.path.join(cls.tmp.name, "dist")
        with contextlib.redirect_stdout(io.StringIO()):
            build(load_config(os.path.join(DEMO_ROOT, "book.toml")), dist_dir=cls.dist, is_pilot=False)
        cls.results = cls.run_scenarios()

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    @classmethod
    def run_scenarios(cls):
        results = {}
        done = threading.Event()

        class Handler(http.server.BaseHTTPRequestHandler):
            def do_GET(self):
                q = parse_qs(urlparse(self.path).query)
                if "d" in q:
                    r = json.loads(q["d"][0])
                    results[r["name"]] = r
                if "end" in q:
                    done.set()
                self.send_response(204)
                self.end_headers()

            def log_message(self, *a):
                pass

        server = http.server.HTTPServer(("127.0.0.1", 0), Handler)
        port = server.server_address[1]
        threading.Thread(target=server.serve_forever, daemon=True).start()
        probes = []
        for i, (name, page, _, _, _) in enumerate(SCENARIOS):
            src = os.path.join(cls.dist, PAGES[page])
            probes.append(src[:-5] + f".__rt{i}.html")
        for i, (name, page, before, action, mode) in enumerate(SCENARIOS):
            with open(os.path.join(cls.dist, PAGES[page]), encoding="utf-8") as fp:
                html = fp.read()
            nxt = (f"location.replace({json.dumps('file://' + probes[i + 1])});" if i + 1 < len(probes)
                   else f"new Image().src='http://127.0.0.1:{port}/?end=1';")
            pre = ("<script>window.__errors=[];window.addEventListener('error',e=>window.__errors.push(String(e.message)));"
                   + (before if mode is not True else f"if(!location.search.includes('r')){{{before}}}") + "</script>")
            if mode == "strip":                           # старый HTML: нет window.__BOOK__
                start = html.index("<script>/* Book runtime")
                html = html[:start] + pre + html[html.index(RUNTIME_END) + len(RUNTIME_END):]
            else:
                head = html.index("<head>") + len("<head>")
                html = html[:head] + pre + html[head:]
                k = html.index(RUNTIME_END) + len(RUNTIME_END)
                html = html[:k] + f"<script>window.__early={STATE_JS};</script>" + html[k:]
            late = LATE_JS % {"name": json.dumps(name), "reload": "true" if mode is True else "false",
                              "state": STATE_JS, "action": json.dumps(action), "port": port, "next": nxt}
            with open(probes[i], "w", encoding="utf-8") as fp:
                fp.write(html.replace("</body>", late + "</body>"))
        with tempfile.TemporaryDirectory() as profile:
            proc = subprocess.Popen([BROWSER, "--headless", "--no-remote", "--profile", profile, "file://" + probes[0]],
                                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            done.wait(180)
            proc.terminate()
            proc.wait(10)
        server.shutdown()
        server.server_close()
        return results

    def r(self, name):
        self.assertIn(name, self.results, f"сценарий {name} не завершился")
        res = self.results[name]
        self.assertNotIn("exception", res, res.get("exception"))
        self.assertEqual(res["errors"], [], name)
        return res

    def assert_clean(self, res, theme):
        self.assertEqual(res["early"], {"theme": theme, "attrs": [], "style": ""})
        self.assertEqual(res["late"], res["early"])           # до отрисовки = после загрузки

    def test_1_empty_storage_default_theme(self):
        res = self.r("empty")
        self.assert_clean(res, "dark")
        self.assertGreater(res["katex"], 0)

    def test_2_saved_theme_applied_before_render(self):
        self.assert_clean(self.r("saved"), "paper")

    def test_3_unknown_theme(self):
        self.assert_clean(self.r("unknown"), "dark")

    def test_4_storage_unavailable(self):
        self.assert_clean(self.r("no_storage"), "dark")

    def test_5_old_retro_keys_ignored(self):
        self.assert_clean(self.r("old_keys"), "dark")

    def test_6_toggle_saves_and_rerenders(self):
        res = self.r("toggle")
        self.assertEqual(res["afterToggle"], "paper")
        self.assertEqual(res["stored"], "paper")
        self.assertEqual(res["mermaidAfter"], res["mermaid"][0])
        self.assertFalse(res["syntaxError"])

    def test_7_old_html_without_book(self):
        mer, code, math = self.r("old_html_mermaid"), self.r("old_html_code"), self.r("old_html_math")
        for res in (mer, code, math):
            self.assertFalse(res["book"])
        self.assertEqual(mer["mermaid"][0], mer["mermaid"][1])
        self.assertGreater(mer["mermaid"][0], 0)
        self.assertGreater(code["copied"], 0)
        self.assertGreater(math["katex"], 0)

    def test_8_mermaid_modal(self):
        res = self.r("modal")
        self.assertTrue(res["opened"])
        self.assertEqual(res["hidden"], "false")
        self.assertTrue(res["svg"])
        self.assertEqual((res["zoomIn"], res["zoomOut"], res["zoomReset"]), ("scale(1.4)", "scale(1.2)", "scale(1)"))
        self.assertTrue(res["closedByButton"])
        self.assertTrue(res["closedByEsc"])

    def test_9_no_modal_without_diagrams(self):
        res = self.r("no_modal")                              # r() проверяет и отсутствие ошибок JS
        self.assertEqual(res["mermaid"], [0, 0])
        self.assertFalse(res["modal"])


if __name__ == "__main__":
    unittest.main()
