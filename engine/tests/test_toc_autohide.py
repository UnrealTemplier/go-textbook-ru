"""Оглавление по наведению ([toc] autohide).

Разметка и конфиг — без браузера. Поведение — в headless Firefox: синтетические mousemove, mouseout и клавиша Escape
на собранной демо-книге с включённым ключом (сама демо-книга ключ не включает: её эталон меняется только в ?v=).
Зона отклика — 5% ширины окна; точки сценария строятся от реальных прямоугольников значка и блока, поэтому
проверка не зависит от вёрстки. Без Firefox поведенческие тесты пропускаются.
"""
import contextlib
import io
import os
import tempfile
import unittest

from engine.build import build
from engine.config import BookConfig, ConfigError, load_config
from engine.tests import DEMO_ROOT, HAS_DEMO
from engine.tests.firefox import BROWSER, probe

PAGE = "docs/01-osnovy/1-spiski-i-kod.html"

# Сценарий: каждый шаг — курсор в заданной точке, ожидание по кадрам (переходы идут по кадрам), снимок.
# transitions() сразу после mousemove: браузер создаёт CSSTransition для переходов блока оглавления
SCENARIO = """(function(){
function wait(ms){var t0=performance.now();return new Promise(function(res){(function f(){
  if(performance.now()-t0>=ms)res();else requestAnimationFrame(f);})();});}
var toc=function(){return document.getElementById('article-toc');};
var btn=function(){return document.getElementById('toc-toggle');};
function box(el){var r=el.getBoundingClientRect();return {l:r.left,r:r.right,t:r.top,b:r.bottom};}
function mid(b){return {x:(b.l+b.r)/2,y:(b.t+b.b)/2};}
function mv(x,y){document.dispatchEvent(new MouseEvent('mousemove',{clientX:x,clientY:y,bubbles:true}));}
function transitions(){return document.getAnimations().filter(function(a){return a.transitionProperty&&a.effect.target===toc();})
  .map(function(a){var t=a.effect.getTiming();return {prop:a.transitionProperty,duration:t.duration,easing:t.easing};});}
function state(){var cs=getComputedStyle(toc());return {open:toc().classList.contains('is-open'),
  expanded:btn().getAttribute('aria-expanded'),opacity:parseFloat(cs.opacity),visibility:cs.visibility};}
window.addEventListener('load',function(){setTimeout(async function(){
  var out={},R=innerWidth*0.05,g,t,p;
  await wait(300);
  out.initial=state();
  mv(5,5); await wait(300); out.farAway=state();
  g=box(btn()); p=mid(g);
  mv(g.l-0.8*R,p.y); out.openTransitions=transitions(); await wait(300); out.iconZone=state();
  t=box(toc()); p=mid(t);
  mv(t.l-0.8*R,p.y); await wait(300); out.stayNearToc=state();
  mv(t.l-1.3*R,p.y); out.closeTransitions=transitions(); await wait(300); out.leftToc=state();
  g=box(btn()); p=mid(g);
  mv(p.x,p.y); await wait(300); out.onToggle=state();
  document.dispatchEvent(new MouseEvent('mouseout',{bubbles:true,relatedTarget:null}));
  await wait(300); out.leftWindow=state();
  btn().click(); await wait(300); out.clickOpen=state();
  document.dispatchEvent(new KeyboardEvent('keydown',{key:'Escape',bubbles:true}));
  await wait(300); out.escape=state();
  send(out);
},300);});
})();"""


def build_site(cfg, dist):
    with contextlib.redirect_stdout(io.StringIO()):
        build(cfg, dist_dir=dist, is_pilot=False)
    return os.path.join(dist, PAGE)


def demo_config(autohide):
    cfg = load_config(os.path.join(DEMO_ROOT, "book.toml"))
    cfg.toc.autohide = autohide
    return cfg


@unittest.skipUnless(HAS_DEMO, "демо-книги нет: это книга, а не репозиторий движка")
class TocAutohideMarkupTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.off = build_site(demo_config(False), os.path.join(cls.tmp.name, "off"))
        cls.on = build_site(demo_config(True), os.path.join(cls.tmp.name, "on"))
        with open(cls.off, encoding="utf-8") as fp:
            cls.off_html = fp.read()
        with open(cls.on, encoding="utf-8") as fp:
            cls.on_html = fp.read()

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_default_page_has_no_toggle_and_no_autohide_class(self):
        self.assertNotIn("toc-toggle", self.off_html)
        self.assertNotIn("toc-autohide", self.off_html)
        self.assertIn('<aside class="article-toc" id="article-toc"', self.off_html)

    def test_autohide_page_has_toggle_in_header_and_hidden_aside(self):
        self.assertIn('<aside class="article-toc toc-autohide" id="article-toc"', self.on_html)
        button = self.on_html.index('<button type="button" class="toc-toggle" id="toc-toggle"')
        start = self.on_html.index('<header class="content-header">')
        end = self.on_html.index("</header>", start)
        self.assertTrue(start < button < end, "значок должен стоять в шапке страницы")
        self.assertIn('aria-controls="article-toc" aria-expanded="false"', self.on_html)

    def test_autohide_keeps_the_same_items(self):
        self.assertEqual(self.on_html.count('<li class="toc-item'), self.off_html.count('<li class="toc-item'))
        self.assertGreater(self.on_html.count('<li class="toc-item'), 1)

    def test_key_defaults_to_off_and_rejects_unknown_keys(self):
        self.assertFalse(BookConfig().toc.autohide)
        with tempfile.TemporaryDirectory() as tmp:
            on = os.path.join(tmp, "on.toml")
            with open(on, "w", encoding="utf-8") as fp:
                fp.write("[toc]\nautohide = true\n")
            self.assertTrue(load_config(on).toc.autohide)
            bad = os.path.join(tmp, "bad.toml")
            with open(bad, "w", encoding="utf-8") as fp:
                fp.write("[toc]\nautohide_typo = true\n")
            with self.assertRaises(ConfigError):
                load_config(bad)


@unittest.skipUnless(HAS_DEMO, "демо-книги нет: это книга, а не репозиторий движка")
@unittest.skipUnless(BROWSER, "нет Firefox (PATH или MERMAID_BROWSER)")
class TocAutohideBehaviourTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.path = build_site(demo_config(True), os.path.join(cls.tmp.name, "dist"))
        cls.r = probe(cls.path, lambda h: h, SCENARIO, timeout=90)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def setUp(self):
        self.assertIsNotNone(self.r, "страница не отправила результат в Firefox")

    def test_hidden_by_default(self):
        s = self.r["initial"]
        self.assertFalse(s["open"])
        self.assertEqual(s["expanded"], "false")
        self.assertEqual(s["visibility"], "hidden")
        self.assertEqual(s["opacity"], 0)

    def test_far_cursor_keeps_it_hidden(self):
        self.assertFalse(self.r["farAway"]["open"])

    def test_icon_zone_opens_it(self):
        s = self.r["iconZone"]
        self.assertTrue(s["open"])
        self.assertEqual(s["expanded"], "true")
        self.assertEqual(s["visibility"], "visible")
        self.assertEqual(s["opacity"], 1)

    def test_opening_runs_a_fast_eased_transition(self):
        self.assert_transition(self.r["openTransitions"])

    def test_closing_runs_a_fast_eased_transition(self):
        self.assert_transition(self.r["closeTransitions"])

    def assert_transition(self, transitions):
        props = {t["prop"]: t for t in transitions}
        for prop in ("opacity", "transform"):
            self.assertIn(prop, props, f"у блока нет перехода: {prop}")
            self.assertGreater(props[prop]["duration"], 0, prop)
            self.assertLessEqual(props[prop]["duration"], 200, f"{prop}: переход должен быть быстрым")
            self.assertIn("cubic-bezier", props[prop]["easing"], f"{prop}: нужна кривая, а не linear")

    def test_stays_open_within_zone_of_block(self):
        self.assertTrue(self.r["stayNearToc"]["open"], "курсор в 0.8 радиуса от блока — блок не должен пропасть")

    def test_leaves_beyond_zone(self):
        self.assertFalse(self.r["leftToc"]["open"], "курсор в 1.3 радиуса от блока — блок должен спрятаться")

    def test_returns_through_icon(self):
        self.assertTrue(self.r["onToggle"]["open"])

    def test_leaving_window_hides_it(self):
        self.assertFalse(self.r["leftWindow"]["open"])

    def test_click_opens_and_escape_hides(self):
        self.assertTrue(self.r["clickOpen"]["open"])
        self.assertFalse(self.r["escape"]["open"])


if __name__ == "__main__":
    unittest.main()
