"""Golden-тест демо-книги: HTML-страницы побайтно равны эталону demo-golden/.

Демо-книга лежит в корне репозитория html-textbook-engine (book.toml, demo-sources/, book/).
В книгах, куда ядро приходит через engine.sync, её нет — тест пропускается.
Эталон обновляется намеренно: UPDATE_GOLDEN=1 python -m unittest engine.tests.test_demo
(изменение вывода демо — повод записать «меняет вывод: да» в CHANGELOG).
"""
import contextlib
import io
import os
import shutil
import tempfile
import unittest

from engine.audit import SiteAuditor
from engine.build import build
from engine.config import load_config

from engine.tests import DEMO_ROOT, HAS_DEMO

GOLDEN = os.path.join(DEMO_ROOT, "demo-golden")


def html_files(root):
    out = {}
    for d, _, files in os.walk(root):
        for f in files:
            if f.endswith(".html"):
                path = os.path.join(d, f)
                with open(path, encoding="utf-8") as fp:
                    out[os.path.relpath(path, root)] = fp.read()
    return out


@unittest.skipUnless(HAS_DEMO, "демо-книги нет: это книга, а не репозиторий движка")
class DemoGoldenTest(unittest.TestCase):
    def test_demo_matches_golden_and_passes_audit(self):
        cfg = load_config(os.path.join(DEMO_ROOT, "book.toml"))
        with tempfile.TemporaryDirectory() as tmp:
            dist = os.path.join(tmp, "dist")
            with contextlib.redirect_stdout(io.StringIO()):
                warnings = build(cfg, dist_dir=dist, is_pilot=False, strict=True)
                self.assertEqual(warnings, [])
                auditor = SiteAuditor(dist, cfg.path(cfg.content.root), mermaid_runtime=False, config=cfg)
                self.assertTrue(auditor.run_audit())
            pages = html_files(dist)
            if os.environ.get("UPDATE_GOLDEN"):
                shutil.rmtree(GOLDEN, ignore_errors=True)
                for rel, text in pages.items():
                    os.makedirs(os.path.dirname(os.path.join(GOLDEN, rel)), exist_ok=True)
                    with open(os.path.join(GOLDEN, rel), "w", encoding="utf-8") as fp:
                        fp.write(text)
            golden = html_files(GOLDEN)
            self.assertEqual(sorted(pages), sorted(golden))
            for rel in pages:
                self.assertEqual(pages[rel], golden[rel], rel)


if __name__ == "__main__":
    unittest.main()
