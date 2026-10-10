"""Сайдбар-оверлей и центровка статьи (ядро 1.8.0).

Разметка и CSS — без браузера. Поведение и раскладка — в headless Firefox на собранной демо-книге:
синтетические mousemove, click и keydown; ширина окна задаётся iframe (firefox.probe, frame_width).
Зона отклика сайдбара — 5% ширины окна; без Firefox поведенческие тесты пропускаются.
"""
import os
import tempfile
import unittest

from engine.tests import DEMO_ROOT, HAS_DEMO
from engine.tests.firefox import BROWSER, probe
from engine.tests.test_toc_autohide import PAGE, build_site, demo_config

ASSETS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")

# Сценарий поведения в окне 1440 (по умолчанию): курсор у левого края открывает сайдбар, дальше зоны прячет,
# кнопка и Escape работают, фокус внутри сайдбара не даёт ему закрыться.
BEHAVIOUR = """(function(){
function wait(ms){var t0=performance.now();return new Promise(function(res){(function f(){
  if(performance.now()-t0>=ms)res();else requestAnimationFrame(f);})();});}
var sb=function(){return document.getElementById('app-sidebar');};
var btn=function(){return document.getElementById('toggle-sidebar');};
function mv(x,y){document.dispatchEvent(new MouseEvent('mousemove',{clientX:x,clientY:y,bubbles:true}));}
function transitions(){return document.getAnimations().filter(function(a){return a.transitionProperty&&a.effect.target===sb();})
  .map(function(a){var t=a.effect.getTiming();return {prop:a.transitionProperty,duration:t.duration,easing:t.easing};});}
function state(){var cs=getComputedStyle(sb()),r=sb().getBoundingClientRect(),a=document.querySelector('.article-body').getBoundingClientRect();
  return {open:sb().classList.contains('is-open'),expanded:btn().getAttribute('aria-expanded'),opacity:parseFloat(cs.opacity),
  visibility:cs.visibility,width:r.width,article:[a.left,a.right]};}
window.addEventListener('load',function(){setTimeout(async function(){
  var out={},W=innerWidth,R=W*0.05,s;
  await wait(300);
  out.initial=state();
  mv(R*0.5,300); out.openTransitions=transitions(); await wait(300); out.inZone=state();
  s=sb().getBoundingClientRect(); mv(s.right-2,300); await wait(300); out.insideSidebar=state();
  mv(s.right+0.8*R,300); await wait(300); out.nearEdge=state();
  mv(s.right+1.3*R,300); out.closeTransitions=transitions(); await wait(300); out.far=state();
  mv(R*0.5,300); await wait(300); out.reopened=state();
  mv(W*0.5,300); await wait(300); out.centreLeaves=state();
  btn().click(); await wait(300); out.buttonOpen=state();
  btn().click(); await wait(300); out.buttonClosed=state();
  mv(R*0.5,300); await wait(300); out.zoneAfterButtonClose=state();
  mv(W*0.5,300); await wait(300); mv(R*0.5,300); await wait(300); out.zoneAfterLeavingZone=state();
  document.dispatchEvent(new KeyboardEvent('keydown',{key:'Escape',bubbles:true}));
  await wait(300); out.escape=state();
  mv(R*0.5,300); await wait(300);
  document.getElementById('sidebar-filter').focus(); mv(W*0.5,300); await wait(300); out.focusInside=state();
  document.getElementById('sidebar-filter').blur(); mv(W*0.5,300); await wait(300); out.focusOutside=state();
  send(out);
},300);});
})();"""

# Раскладка: ширина окна задаётся iframe; сайдбар скрыт (по умолчанию); центр статьи — по центру основной области
LAYOUT = """(function(){
window.addEventListener('load',function(){setTimeout(function(){
  var m=document.getElementById('app-main').getBoundingClientRect(),a=document.querySelector('.article-body').getBoundingClientRect();
  var t=document.getElementById('article-toc'),tr=t?t.getBoundingClientRect():null,sb=document.getElementById('app-sidebar');
  send({win:innerWidth,mainL:m.left,mainR:m.right,artL:a.left,artR:a.right,
    tocL:tr?tr.left:null,tocR:tr?tr.right:null,tocDisplay:t?getComputedStyle(t).display:null,
    sbWidth:sb.getBoundingClientRect().width,sbPosition:getComputedStyle(sb).position,
    tocTop:tr?tr.top:null});
},300);});
})();"""

# Перенос текста: длинные названия пункта, модуля и подраздела переносятся внутри панели, а не обрезаются
TEXT = """(function(){
window.addEventListener('load',function(){setTimeout(function(){
  var nav=document.getElementById('sidebar-content'),sb=document.getElementById('app-sidebar');
  var long='Очень длинное название пункта, которое не должно обрезаться многоточием '+'ЁЖЗ'.repeat(60);
  var els=[nav.querySelector('.nav-item.active a'),nav.querySelector('.nav-module.active-module .mod-text'),
    nav.querySelector('.nav-submodule.active-submodule .sub-text')].filter(function(e){return e;});
  els.forEach(function(e){e.textContent=long;});
  send({win:innerWidth,sbRight:sb.getBoundingClientRect().right,items:els.map(function(e){
    var r=e.getBoundingClientRect(),cs=getComputedStyle(e);
    return {cls:e.className,h:r.height,right:r.right,sw:e.scrollWidth,cw:e.clientWidth,
      ws:cs.whiteSpace,to:cs.textOverflow,lh:parseFloat(cs.lineHeight)||parseFloat(cs.fontSize)*1.2};})});
},300);});
})();"""

WIDTH_CAP = "<style>:root{--sidebar-width:90vw}</style>"


@unittest.skipUnless(HAS_DEMO, "демо-книги нет: это книга, а не репозиторий движка")
class SidebarMarkupTest(unittest.TestCase):
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

    def test_no_resizer_left(self):
        self.assertNotIn("drag-resizer", self.off_html)
        self.assertNotIn('class="resizer"', self.off_html)

    def test_sidebar_is_overlay_markup_kept(self):
        self.assertIn('<aside class="app-sidebar" id="app-sidebar"', self.off_html)
        self.assertIn('id="toggle-sidebar"', self.off_html)
        self.assertIn('aria-expanded="false" aria-controls="app-sidebar"', self.off_html)

    def test_toc_in_flow_marks_wrapper(self):
        self.assertIn('<main class="content-wrapper has-toc" id="main-content">', self.off_html)

    def test_autohide_toc_leaves_wrapper_plain(self):
        self.assertIn('<main class="content-wrapper" id="main-content">', self.on_html)
        self.assertNotIn("has-toc", self.on_html)

    def test_assets_have_no_resize_code(self):
        with open(os.path.join(ASSETS, "main.js"), encoding="utf-8") as fp:
            js = fp.read()
        with open(os.path.join(ASSETS, "style.css"), encoding="utf-8") as fp:
            css = fp.read()
        self.assertNotIn("sidebar_width", js)
        self.assertNotIn("drag-resizer", js)
        self.assertNotIn(".resizer", css)
        self.assertNotIn("sidebar-default-width", css)


@unittest.skipUnless(HAS_DEMO, "демо-книги нет: это книга, а не репозиторий движка")
@unittest.skipUnless(BROWSER, "нет Firefox (PATH или MERMAID_BROWSER)")
class SidebarBehaviourTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.path = build_site(demo_config(False), os.path.join(cls.tmp.name, "dist"))
        cls.r = probe(cls.path, lambda h: h, BEHAVIOUR, timeout=90)

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

    def test_left_strip_opens_it(self):
        s = self.r["inZone"]
        self.assertTrue(s["open"])
        self.assertEqual(s["expanded"], "true")
        self.assertEqual(s["visibility"], "visible")
        self.assertEqual(s["opacity"], 1)

    def test_opening_and_closing_use_the_toc_timing(self):
        for name in ("openTransitions", "closeTransitions"):
            props = {t["prop"]: t for t in self.r[name]}
            for prop in ("opacity", "transform"):
                self.assertIn(prop, props, f"{name}: нет перехода {prop}")
                self.assertLessEqual(props[prop]["duration"], 200, f"{name}/{prop}: переход должен быть быстрым")
                self.assertIn("cubic-bezier", props[prop]["easing"], f"{name}/{prop}: нужна кривая, а не linear")

    def test_stays_open_inside_and_near_the_panel(self):
        self.assertTrue(self.r["insideSidebar"]["open"])
        self.assertTrue(self.r["nearEdge"]["open"], "курсор в 0.8 радиуса от панели — панель не прячется")

    def test_leaves_beyond_zone(self):
        self.assertFalse(self.r["far"]["open"], "курсор в 1.3 радиуса от панели — панель прячется")

    def test_reopens_from_strip(self):
        self.assertTrue(self.r["reopened"]["open"])

    def test_centre_of_window_keeps_it_hidden(self):
        self.assertFalse(self.r["centreLeaves"]["open"])

    def test_button_opens_and_closes(self):
        self.assertTrue(self.r["buttonOpen"]["open"])
        self.assertEqual(self.r["buttonOpen"]["expanded"], "true")
        self.assertFalse(self.r["buttonClosed"]["open"])
        self.assertEqual(self.r["buttonClosed"]["expanded"], "false")

    def test_button_keeps_closed_until_cursor_leaves_zone(self):
        self.assertFalse(self.r["zoneAfterButtonClose"]["open"], "после закрытия кнопкой курсор в зоне не открывает")
        self.assertTrue(self.r["zoneAfterLeavingZone"]["open"], "после выхода из зоны курсор снова открывает")

    def test_escape_hides(self):
        self.assertFalse(self.r["escape"]["open"])

    def test_focus_inside_keeps_it_open(self):
        self.assertTrue(self.r["focusInside"]["open"])

    def test_focus_outside_lets_it_hide(self):
        self.assertFalse(self.r["focusOutside"]["open"])

    def test_opening_does_not_move_content(self):
        base = self.r["initial"]["article"]
        for name in ("inZone", "buttonOpen", "far"):
            self.assertEqual(self.r[name]["article"], base, f"{name}: статья сдвинулась при открытии сайдбара")


@unittest.skipUnless(HAS_DEMO, "демо-книги нет: это книга, а не репозиторий движка")
@unittest.skipUnless(BROWSER, "нет Firefox (PATH или MERMAID_BROWSER)")
class SidebarLayoutTest(unittest.TestCase):
    """Статья — по центру основной области при любой ширине; оглавление в правом поле, не за пределами."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.path = build_site(demo_config(False), os.path.join(cls.tmp.name, "dist"))

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def measure(self, width, transform=lambda h: h):
        r = probe(self.path, transform, LAYOUT, timeout=90, frame_width=width)
        self.assertIsNotNone(r, f"нет результата при ширине {width}")
        return r

    def test_article_centred_and_toc_inside_window(self):
        for width in (1025, 1280, 1440, 1920):
            with self.subTest(width=width):
                r = self.measure(width)
                self.assertEqual(r["sbPosition"], "fixed", "сайдбар вне потока (fixed)")
                self.assertEqual(r["tocDisplay"], "block", "при этой ширине оглавление видно")
                centre = (r["artL"] + r["artR"]) / 2
                self.assertAlmostEqual(centre, (r["mainL"] + r["mainR"]) / 2, delta=1, msg="статья не по центру")
                self.assertGreaterEqual(r["tocL"], r["artR"], "оглавление залезло на статью")
                self.assertLessEqual(r["tocR"], r["mainR"], "оглавление вылезло за окно")

    def test_sidebar_never_wider_than_30_percent(self):
        for width in (800, 1280):
            with self.subTest(width=width):
                r = self.measure(width, lambda h: h.replace("</head>", WIDTH_CAP + "</head>", 1))
                self.assertLessEqual(r["sbWidth"], 0.3 * r["win"] + 0.5, "сайдбар шире 30% окна")
                self.assertGreater(r["sbWidth"], 0.29 * r["win"], "при большой --sidebar-width ширина должна упереться в 30%")

    def test_default_sidebar_width_is_320_when_room_allows(self):
        r = self.measure(1440)
        self.assertAlmostEqual(r["sbWidth"], 320, delta=0.5)


@unittest.skipUnless(HAS_DEMO, "демо-книги нет: это книга, а не репозиторий движка")
@unittest.skipUnless(BROWSER, "нет Firefox (PATH или MERMAID_BROWSER)")
class SidebarTextTest(unittest.TestCase):
    """Текст пунктов сайдбара переносится и помещается в панель (и в узкой, и в широкой)."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.path = build_site(demo_config(False), os.path.join(cls.tmp.name, "dist"))

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def check(self, width):
        r = probe(self.path, lambda h: h, TEXT, timeout=90, frame_width=width)
        self.assertIsNotNone(r, f"нет результата при ширине {width}")
        self.assertGreaterEqual(len(r["items"]), 2, "в демо-книге должны быть пункт и заголовок модуля")
        for item in r["items"]:
            with self.subTest(item=item["cls"], width=width):
                self.assertNotEqual(item["ws"], "nowrap", "текст запрещено переносить: nowrap")
                self.assertEqual(item["to"], "clip", "многоточие не должно обрезать текст")
                self.assertLessEqual(item["sw"], item["cw"] + 1, "текст шире пункта — выходит за его край")
                self.assertGreater(item["h"], item["lh"] * 1.5, "длинный текст должен занимать несколько строк")
                self.assertLessEqual(item["right"], r["sbRight"] + 0.5, "текст выходит за панель")

    def test_wraps_in_wide_sidebar(self):
        self.check(1440)

    def test_wraps_in_narrow_sidebar(self):
        self.check(600)
