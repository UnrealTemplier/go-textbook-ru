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
from engine.tests.test_toc_autohide import build_site, demo_config

ASSETS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")

# Сценарий поведения в окне 1440 (по умолчанию): курсор у левого края открывает сайдбар, дальше зоны прячет,
# кнопка и Escape работают, фокус внутри сайдбара не даёт ему закрыться.
BEHAVIOUR = """(function(){
function wait(ms){var t0=performance.now();return new Promise(function(res){(function f(){
  if(performance.now()-t0>=ms)res();else requestAnimationFrame(f);})();});}
var sb=function(){return document.getElementById('app-sidebar');};
var btn=function(){return document.getElementById('toggle-sidebar');};
function mv(x,y){document.dispatchEvent(new PointerEvent('pointermove',{clientX:x,clientY:y,pointerType:'mouse',bubbles:true}));}
function transitions(){return document.getAnimations().filter(function(a){return a.transitionProperty&&a.effect.target===sb();})
  .map(function(a){var t=a.effect.getTiming();return {prop:a.transitionProperty,duration:t.duration,easing:t.easing};});}
function state(){var cs=getComputedStyle(sb()),r=sb().getBoundingClientRect(),a=document.querySelector('.article-body').getBoundingClientRect();
  return {open:sb().classList.contains('is-open'),expanded:btn().getAttribute('aria-expanded'),opacity:parseFloat(cs.opacity),
  visibility:cs.visibility,width:r.width,article:[a.left,a.right]};}
window.addEventListener('load',function(){setTimeout(async function(){
  var out={},W=innerWidth,R=W*0.05,s;
  await wait(300);
  out.initial=state();
  document.dispatchEvent(new PointerEvent('pointermove',{clientX:R*0.5,clientY:300,pointerType:'touch',bubbles:true}));
  await wait(300); out.touchInZone=state();
  document.dispatchEvent(new MouseEvent('mousemove',{clientX:R*0.5,clientY:300,bubbles:true}));
  await wait(300); out.compatMouseInZone=state();
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


# Касание кнопки в шапке на узком экране: после него под пальцем не должна оказаться ссылка «Главная»
TAP = """(function(){
function wait(ms){var t0=performance.now();return new Promise(function(res){(function f(){
  if(performance.now()-t0>=ms)res();else requestAnimationFrame(f);})();});}
window.addEventListener('load',function(){setTimeout(async function(){
  var b=document.getElementById('toggle-sidebar').getBoundingClientRect(),x=b.left+2,y=b.top+b.height/2,out={};
  document.dispatchEvent(new PointerEvent('pointermove',{clientX:x,clientY:y,pointerType:'touch',bubbles:true}));
  document.dispatchEvent(new MouseEvent('mousemove',{clientX:x,clientY:y,bubbles:true}));
  await wait(300);
  out.openAfterTouch=document.getElementById('app-sidebar').classList.contains('is-open');
  var cx=b.left+b.width/2,cy=b.top+b.height/2,el=document.elementFromPoint(cx,cy),a=el&&el.closest('a');
  out.linkUnderButton=a?a.getAttribute('href'):null;
  send(out);
},300);});
})();"""


@unittest.skipUnless(HAS_DEMO, "демо-книги нет: это книга, а не репозиторий движка")
class SidebarMarkupTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.page = build_site(demo_config(), os.path.join(cls.tmp.name, "dist"))
        with open(cls.page, encoding="utf-8") as fp:
            cls.off_html = fp.read()

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

    def test_wrapper_is_plain_and_toc_is_the_popup(self):
        self.assertIn('<main class="content-wrapper" id="main-content">', self.off_html)
        self.assertNotIn("has-toc", self.off_html)
        self.assertIn('<aside class="article-toc" id="article-toc"', self.off_html)

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
        cls.path = build_site(demo_config(), os.path.join(cls.tmp.name, "dist"))
        cls.r = probe(cls.path, lambda h: h, BEHAVIOUR, timeout=90)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def setUp(self):
        self.assertIsNotNone(self.r, "страница не отправила результат в Firefox")

    def test_touch_and_compat_mouse_do_not_open_it(self):
        self.assertFalse(self.r["touchInZone"]["open"], "касание в зоне не должно открывать панель")
        self.assertFalse(self.r["compatMouseInZone"]["open"], "совместимый mousemove от касания не должен открывать панель")

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
        cls.path = build_site(demo_config(), os.path.join(cls.tmp.name, "dist"))

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
                self.assertLessEqual(r["tocR"], r["mainR"], "оглавление вылезло за окно")

    def test_desktop_sidebar_is_exactly_30_percent_of_window(self):
        for width in (1025, 1440, 1920):
            with self.subTest(width=width):
                r = self.measure(width)
                self.assertAlmostEqual(r["sbWidth"], 0.3 * r["win"], delta=0.5, msg="сайдбар — не 30% окна")

    def test_phone_drawer_is_70_percent_of_window(self):
        r = self.measure(390)
        self.assertAlmostEqual(r["sbWidth"], 0.7 * r["win"], delta=0.5, msg="на телефоне панель — не 70% окна")



@unittest.skipUnless(HAS_DEMO, "демо-книги нет: это книга, а не репозиторий движка")
@unittest.skipUnless(BROWSER, "нет Firefox (PATH или MERMAID_BROWSER)")
class SidebarTextTest(unittest.TestCase):
    """Текст пунктов сайдбара переносится и помещается в панель (и в узкой, и в широкой)."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.path = build_site(demo_config(), os.path.join(cls.tmp.name, "dist"))

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


@unittest.skipUnless(HAS_DEMO, "демо-книги нет: это книга, а не репозиторий движка")
@unittest.skipUnless(BROWSER, "нет Firefox (PATH или MERMAID_BROWSER)")
class SidebarTouchTest(unittest.TestCase):
    """Касание кнопки шапки на телефоне не открывает панель сам по себе и не уводит клик на «Главную»."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.path = build_site(demo_config(), os.path.join(cls.tmp.name, "dist"))

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_button_slides_out_70_percent_and_hides_again(self):
        r = probe(self.path, lambda h: h, PHONE_BUTTON, timeout=90, frame_width=390)
        self.assertIsNotNone(r, "страница не отправила результат в Firefox")
        self.assertTrue(r["openAfterClick"])
        self.assertAlmostEqual(r["widthOpen"], 0.7 * r["win"], delta=0.5, msg="панель — не 70% окна")
        self.assertEqual(r["leftOpen"], 0)
        self.assertFalse(r["openAfterSecondClick"])
        self.assertLess(r["leftClosed"], 0, "закрытая панель должна уехать за левый край")

    def test_tap_on_button_does_not_open_sidebar_or_hit_home_link(self):
        r = probe(self.path, lambda h: h, TAP, timeout=90, frame_width=390)
        self.assertIsNotNone(r, "страница не отправила результат в Firefox")
        self.assertFalse(r["openAfterTouch"], "касание открыло панель до click")
        self.assertIsNone(r["linkUnderButton"], "под кнопкой оказалась ссылка (например, «Главная»)")


HEADER = """(function(){
window.addEventListener('load',function(){setTimeout(function(){
  var h=document.querySelector('.content-header').getBoundingClientRect(),b=document.getElementById('toggle-sidebar').getBoundingClientRect();
  var t=document.getElementById('toc-toggle'),tr=t?t.getBoundingClientRect():null;
  send({crumbs:document.querySelectorAll('.breadcrumbs').length,headerL:h.left,headerR:h.right,btnL:b.left,btnR:b.right,
        tocL:tr?tr.left:null,tocR:tr?tr.right:null});
},300);});
})();"""


@unittest.skipUnless(HAS_DEMO, "демо-книги нет: это книга, а не репозиторий движка")
@unittest.skipUnless(BROWSER, "нет Firefox (PATH или MERMAID_BROWSER)")
class SidebarHeaderTest(unittest.TestCase):
    """Шапка статьи: кнопка сайдбара слева, значок оглавления справа, хлебных крошек нет."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.path = build_site(demo_config(), os.path.join(cls.tmp.name, "dist"))

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def check(self, width):
        r = probe(self.path, lambda h: h, HEADER, timeout=90, frame_width=width)
        self.assertIsNotNone(r, f"нет результата при ширине {width}")
        self.assertEqual(r["crumbs"], 0, "хлебные крошки должны быть удалены из шапки")
        self.assertLess(r["btnL"] - r["headerL"], 60, "кнопка сайдбара — не слева")
        if r["tocL"] is not None:
            self.assertLess(r["headerR"] - r["tocR"], 60, "значок оглавления — не справа")
            self.assertGreaterEqual(r["tocL"], r["btnR"], "значок оглавления налезает на кнопку сайдбара")

    def test_desktop(self):
        self.check(1440)

    def test_phone(self):
        self.check(390)


# Телефон: нажатие кнопки выдвигает панель на 70% ширины окна, второе нажатие её прячет
PHONE_BUTTON = """(function(){
function wait(ms){var t0=performance.now();return new Promise(function(res){(function f(){
  if(performance.now()-t0>=ms)res();else requestAnimationFrame(f);})();});}
window.addEventListener('load',function(){setTimeout(async function(){
  var sb=document.getElementById('app-sidebar'),btn=document.getElementById('toggle-sidebar'),out={win:innerWidth};
  btn.click(); await wait(400);
  out.openAfterClick=sb.classList.contains('is-open'); out.widthOpen=sb.getBoundingClientRect().width;
  out.leftOpen=sb.getBoundingClientRect().left; out.transformOpen=getComputedStyle(sb).transform;
  btn.click(); await wait(400);
  out.openAfterSecondClick=sb.classList.contains('is-open'); out.leftClosed=sb.getBoundingClientRect().left;
  send(out);
},300);});
})();"""


# Бегунок полосы дерева: список принудительно ниже содержимого (иначе не прокручивается)
SCROLL_CSS = "<style>.sidebar-content{height:120px!important;flex:none!important}</style>"

SCROLLBAR = """(function(){
function wait(ms){var t0=performance.now();return new Promise(function(res){(function f(){
  if(performance.now()-t0>=ms)res();else requestAnimationFrame(f);})();});}
window.addEventListener('load',function(){setTimeout(async function(){
  var nav=document.getElementById('sidebar-content'),sb=document.getElementById('app-sidebar'),th=sb.querySelector('.sidebar-thumb'),out={};
  out.hasThumb=!!th;
  nav.scrollTop=30; await wait(150);
  out.duringClass=sb.classList.contains('is-scrolling'); out.duringOpacity=parseFloat(getComputedStyle(th).opacity);
  var tr=th.getBoundingClientRect(),nr=nav.getBoundingClientRect();
  out.thumbTop=tr.top-nr.top; out.thumbH=tr.height; out.navH=nr.height; out.thumbRight=nr.right-tr.right;
  await wait(2000); out.afterClass=sb.classList.contains('is-scrolling'); out.afterOpacity=parseFloat(getComputedStyle(th).opacity);
  // перетаскивание бегунка: тянем вниз на 30 px
  var cy=tr.top+tr.height/2, before=nav.scrollTop;
  nav.scrollTop=0; await wait(100);
  var t2=th.getBoundingClientRect(), cy2=t2.top+t2.height/2;
  th.dispatchEvent(new PointerEvent('pointerdown',{clientX:t2.left+2,clientY:cy2,button:0,bubbles:true}));
  document.dispatchEvent(new PointerEvent('pointermove',{clientX:t2.left+2,clientY:cy2+30,bubbles:true}));
  document.dispatchEvent(new PointerEvent('pointerup',{clientX:t2.left+2,clientY:cy2+30,bubbles:true}));
  await wait(100); out.dragged=nav.scrollTop;
  send(out);
},300);});
})();"""


@unittest.skipUnless(HAS_DEMO, "демо-книги нет: это книга, а не репозиторий движка")
@unittest.skipUnless(BROWSER, "нет Firefox (PATH или MERMAID_BROWSER)")
class SidebarScrollbarTest(unittest.TestCase):
    """Бегунок дерева виден при прокрутке, гаснет после неё и тянется мышью."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.path = build_site(demo_config(), os.path.join(cls.tmp.name, "dist"))
        cls.r = probe(cls.path, lambda h: h.replace("</head>", SCROLL_CSS + "</head>", 1), SCROLLBAR, timeout=120)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def setUp(self):
        self.assertIsNotNone(self.r, "страница не отправила результат в Firefox")

    def test_thumb_exists(self):
        self.assertTrue(self.r["hasThumb"])

    def test_visible_while_scrolling(self):
        self.assertTrue(self.r["duringClass"])
        self.assertGreater(self.r["duringOpacity"], 0.9)

    def test_fades_out_after_scrolling_stops(self):
        self.assertFalse(self.r["afterClass"])
        self.assertLess(self.r["afterOpacity"], 0.05)

    def test_thumb_is_inside_the_list_and_shorter_than_it(self):
        self.assertGreater(self.r["thumbH"], 0)
        self.assertLess(self.r["thumbH"], self.r["navH"], "при прокрутке бегунок короче списка")
        self.assertGreaterEqual(self.r["thumbTop"], 0)
        self.assertLessEqual(self.r["thumbTop"] + self.r["thumbH"], self.r["navH"] + 1)

    def test_dragging_thumb_scrolls_list(self):
        self.assertGreater(self.r["dragged"], 0, "перетаскивание бегунка вниз должно прокручивать список")
