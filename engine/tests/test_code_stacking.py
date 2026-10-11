"""Блоки кода не выводятся поверх шапки при прокрутке (headless Firefox, демо-книга).

Страница прокручивается так, чтобы блок кода зашёл под шапку; точка проверки — внутри полосы перекрытия,
слева от крошек. Должна попасть шапка, а не блок. Без Firefox тест пропускается.
"""
import contextlib
import io
import os
import tempfile
import unittest

from engine.build import build
from engine.config import load_config
from engine.tests import DEMO_ROOT, HAS_DEMO
from engine.tests.firefox import BROWSER, probe

PAGE = "docs/01-osnovy/1-spiski-i-kod.html"

SCENARIO = """(function(){
function sleep(ms){return new Promise(function(res){setTimeout(res,ms);});}
window.addEventListener('load',async function(){await sleep(400);
  var out={};
  var cb=document.querySelector('.code-block');
  window.scrollTo({top:cb.getBoundingClientRect().top+scrollY-40,behavior:'instant'});
  await sleep(800);
  var h=document.querySelector('.content-header').getBoundingClientRect();
  var c=cb.getBoundingClientRect();
  out.overlap=c.top<h.bottom&&c.bottom>h.top;
  var y=(Math.max(c.top,h.top)+h.bottom)/2, x=c.left+40;
  var el=document.elementFromPoint(x,y);
  out.hitInHeader=!!(el&&el.closest('.content-header'));
  out.hit=el?el.tagName+'.'+el.className:null;
  send(out);
});})();"""


def build_site(cfg, dist):
    with contextlib.redirect_stdout(io.StringIO()):
        build(cfg, dist_dir=dist, is_pilot=False)
    return os.path.join(dist, PAGE)


@unittest.skipUnless(HAS_DEMO, "демо-книги нет: это книга, а не репозиторий движка")
@unittest.skipUnless(BROWSER, "нет Firefox (PATH или MERMAID_BROWSER)")
class CodeBlockUnderHeaderTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        path = build_site(load_config(os.path.join(DEMO_ROOT, "book.toml")), os.path.join(cls.tmp.name, "dist"))
        cls.r = probe(path, lambda h: h, SCENARIO, timeout=90)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def setUp(self):
        self.assertIsNotNone(self.r, "страница не отправила результат в Firefox")

    def test_code_block_really_scrolls_under_header(self):
        self.assertTrue(self.r["overlap"], "сценарий должен завести блок кода под шапку")

    def test_header_stays_on_top_of_code_block(self):
        self.assertTrue(self.r["hitInHeader"], f"поверх шапки оказался: {self.r['hit']}")


if __name__ == "__main__":
    unittest.main()
