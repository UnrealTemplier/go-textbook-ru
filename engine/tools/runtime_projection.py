"""
engine/tools/runtime_projection.py
Рантайм-проекция сборки (анализ § 4.11): что браузер действительно отрисовал на каждой странице.

Для каждой HTML-страницы dist/ в headless Firefox по file:// считаются: .katex, .katex-display,
.katex-error, отрисованные SVG в pre.mermaid, SVG ошибки Mermaid (элемент .error-text: «Syntax error in text»), JS-ошибки.
Побайтная проверка HTML этого не видит (например, ошибку в разделителях KaTeX).

Как работает: во временном каталоге строится зеркало dist/ из символьных ссылок (сам dist/ не
трогается), рядом с каждой страницей — пробная копия со встроенными скриптами. N процессов
Firefox обходят свои части страниц цепочкой и отправляют результат маячком на локальный сервер.

  python3 engine/tools/runtime_projection.py dist --out runtime.json [--workers 12]
  python3 engine/tools/runtime_projection.py --compare old.json new.json
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import http.server
from typing import Dict, List, Optional
from urllib.parse import parse_qs, urlparse

METRICS = ("katex", "katex_display", "katex_error", "mermaid_blocks", "mermaid_svg", "mermaid_error", "js_errors")

EARLY = ("<script>window.__rp={e:0};window.addEventListener('error',function(){window.__rp.e++;});"
         "window.addEventListener('unhandledrejection',function(){window.__rp.e++;});</script>")

LATE = """<script>(function(){
var t0=Date.now(), LIMIT=%(limit)d;
function done(){
  var root=document.querySelector('.article-markdown')||document.body;
  var pres=document.querySelectorAll('pre.mermaid'), svg=0, err=0;
  pres.forEach(function(p){var s=p.querySelector('svg'); if(s){svg++; if(s.querySelector('.error-text')) err++;}});
  var r={p:%(page)s,katex:root.querySelectorAll('.katex').length,katex_display:root.querySelectorAll('.katex-display').length,
    katex_error:root.querySelectorAll('.katex-error').length,mermaid_blocks:pres.length,mermaid_svg:svg,mermaid_error:err,
    js_errors:window.__rp.e,ms:Date.now()-t0};
  var im=new Image();im.onload=im.onerror=function(){%(next)s};
  im.src='http://127.0.0.1:%(port)d/?d='+encodeURIComponent(JSON.stringify(r));
}
function ready(){var pres=document.querySelectorAll('pre.mermaid');
  for(var i=0;i<pres.length;i++){if(!pres[i].querySelector('svg')) return false;} return true;}
function poll(){ if(ready()||Date.now()-t0>LIMIT){done();} else setTimeout(poll,50); }
window.addEventListener('load',function(){setTimeout(poll,150);});
})();</script>"""


def list_pages(dist: str) -> List[str]:
    pages = []
    for d, _, files in os.walk(dist):
        for f in files:
            if f.endswith(".html"):
                pages.append(os.path.relpath(os.path.join(d, f), dist).replace(os.sep, "/"))
    return sorted(pages)


def mirror(dist: str, target: str) -> None:
    """Зеркало dist/ из символьных ссылок на файлы: пробные страницы кладутся рядом, оригиналы не трогаются."""
    for d, _, files in os.walk(dist):
        rel = os.path.relpath(d, dist)
        os.makedirs(os.path.join(target, rel), exist_ok=True)
        for f in files:
            os.symlink(os.path.abspath(os.path.join(d, f)), os.path.join(target, rel, f))


def probe_name(page: str) -> str:
    return page[:-5] + ".__rp.html"


def project(dist: str, workers: int = 12, page_limit_ms: int = 8000, pages: Optional[List[str]] = None,
            browser: Optional[str] = None, timeout_s: int = 1800) -> Dict[str, Dict[str, int]]:
    browser = browser or os.environ.get("MERMAID_BROWSER") or shutil.which("firefox")
    if not browser:
        raise RuntimeError("Firefox не найден (PATH или MERMAID_BROWSER)")
    pages = pages or list_pages(dist)
    results: Dict[str, Dict[str, int]] = {}
    finished = set()
    lock = threading.Lock()

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            q = parse_qs(urlparse(self.path).query)
            with lock:
                if "d" in q:
                    r = json.loads(q["d"][0])
                    results[r.pop("p")] = r
                if "end" in q:
                    finished.add(int(q["end"][0]))
            self.send_response(204)
            self.end_headers()

        def log_message(self, *a):
            pass

    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    port = server.server_address[1]
    threading.Thread(target=server.serve_forever, daemon=True).start()

    chunks = [pages[i::workers] for i in range(workers)]
    chunks = [c for c in chunks if c]
    procs = []
    with tempfile.TemporaryDirectory(prefix="runtime-projection-") as tmp:
        site = os.path.join(tmp, "site")
        mirror(dist, site)
        for w, chunk in enumerate(chunks):
            for i, page in enumerate(chunk):
                src = os.path.join(dist, page)
                with open(src, encoding="utf-8") as fp:
                    text = fp.read()
                if i + 1 < len(chunk):
                    nxt = "location.replace(%s);" % json.dumps("file://" + os.path.join(site, probe_name(chunk[i + 1])))
                else:
                    nxt = "new Image().src='http://127.0.0.1:%d/?end=%d';" % (port, w)
                late = LATE % {"limit": page_limit_ms, "page": json.dumps(page), "port": port, "next": nxt}
                head = text.find("<head>")
                text = text[:head + 6] + EARLY + text[head + 6:] if head >= 0 else EARLY + text
                text = text.replace("</body>", late + "</body>")
                with open(os.path.join(site, probe_name(page)), "w", encoding="utf-8") as fp:
                    fp.write(text)
        try:
            for w, chunk in enumerate(chunks):
                profile = os.path.join(tmp, f"profile-{w}")
                os.makedirs(profile)
                procs.append(subprocess.Popen(
                    [browser, "--headless", "--no-remote", "--profile", profile,
                     "file://" + os.path.join(site, probe_name(chunk[0]))],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL))
            deadline = time.time() + timeout_s
            while time.time() < deadline:
                with lock:
                    if len(finished) == len(chunks):
                        break
                time.sleep(0.5)
        finally:
            for p in procs:
                p.terminate()
            for p in procs:
                try:
                    p.wait(10)
                except subprocess.TimeoutExpired:
                    p.kill()
            server.shutdown()
    missing = [p for p in pages if p not in results]
    if missing:
        raise RuntimeError(f"нет результатов для {len(missing)} страниц, например {missing[:3]}")
    return {p: results[p] for p in sorted(results)}


def compare(old: Dict[str, Dict[str, int]], new: Dict[str, Dict[str, int]],
            expected: Optional[Dict[str, Dict[str, int]]] = None) -> List[str]:
    """Различия по метрикам (без времени). expected: {страница: {метрика: новое значение}} — разрешённые."""
    expected = expected or {}
    out = []
    for page in sorted(set(old) | set(new)):
        if page not in old or page not in new:
            out.append(f"{page}: {'нет в старой' if page not in old else 'нет в новой'} проекции")
            continue
        for m in METRICS:
            a, b = old[page].get(m), new[page].get(m)
            if a != b and expected.get(page, {}).get(m) != b:
                out.append(f"{page}: {m} {a} → {b}")
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Рантайм-проекция сборки в headless Firefox")
    ap.add_argument("dist", nargs="?")
    ap.add_argument("--out")
    ap.add_argument("--workers", type=int, default=12)
    ap.add_argument("--page-limit-ms", type=int, default=8000)
    ap.add_argument("--compare", nargs=2, metavar=("OLD", "NEW"))
    ap.add_argument("--expected", help="JSON разрешённых изменений для --compare")
    args = ap.parse_args(argv)

    if args.compare:
        load = lambda p: json.load(open(p, encoding="utf-8"))
        diffs = compare(load(args.compare[0]), load(args.compare[1]),
                        load(args.expected) if args.expected else None)
        for d in diffs[:200]:
            print(d)
        print(f"Различий: {len(diffs)}")
        return 1 if diffs else 0

    if not args.dist:
        ap.error("укажите dist или --compare")
    t0 = time.time()
    res = project(args.dist, workers=args.workers, page_limit_ms=args.page_limit_ms)
    totals = {m: sum(r[m] for r in res.values()) for m in METRICS}
    print(f"Страниц: {len(res)} за {time.time() - t0:.1f} с; итоги: {totals}")
    if args.out:
        with open(args.out, "w", encoding="utf-8") as fp:
            json.dump({p: {m: r[m] for m in METRICS} for p, r in res.items()}, fp,
                      ensure_ascii=False, indent=0, sort_keys=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
