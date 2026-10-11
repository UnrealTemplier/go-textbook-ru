"""Переключатель тем: значок открывает список всех тем над собой (как оглавление, но по нажатию).

Поведение — в headless Firefox на собранной демо-книге: открытие значком, клик мимо списка и Escape закрывают
без смены темы, клик по теме применяет её и сохраняет, список остаётся открытым. Без Firefox тесты пропускаются.
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

# Сценарий: нажатия как у пользователя (через click и Escape), ожидание по таймеру после каждого шага.
SCENARIO = """(function(){
function sleep(ms){return new Promise(function(res){setTimeout(res,ms);});}
var btn=function(){return document.getElementById('theme-switcher-btn');};
var menu=function(){return document.getElementById('theme-menu');};
function state(){var m=menu();return {open:m.classList.contains('is-open'),expanded:btn().getAttribute('aria-expanded'),
  theme:document.documentElement.dataset.theme,stored:localStorage.getItem('demo_theme'),
  items:m.querySelectorAll('.theme-menu-item').length,icons:m.querySelectorAll('.theme-menu-icon').length,
  current:(m.querySelector('.theme-menu-item.is-current')||{dataset:{}}).dataset.themeKey,
  visibility:getComputedStyle(m).visibility};}
window.addEventListener('load',async function(){await sleep(300);
  var out={};
  localStorage.clear();
  out.initial=state();
  btn().click(); await sleep(300); out.opened=state();
  document.querySelector('.article-body').click(); await sleep(300); out.outside=state();
  btn().click(); await sleep(300);
  btn().click(); await sleep(300); out.toggledClosed=state();
  btn().click(); await sleep(300);
  document.dispatchEvent(new KeyboardEvent('keydown',{key:'Escape',bubbles:true})); await sleep(300); out.escape=state();
  btn().click(); await sleep(300);
  menu().querySelector('[data-theme-key="paper"]').click(); await sleep(300); out.picked=state();
  menu().querySelector('[data-theme-key="light"]').click(); await sleep(300); out.switched=state();
  document.dispatchEvent(new KeyboardEvent('keydown',{key:'Escape',bubbles:true})); await sleep(300); out.afterPickEscape=state();
  send(out);
});})();"""


def build_site(cfg, dist):
    with contextlib.redirect_stdout(io.StringIO()):
        build(cfg, dist_dir=dist, is_pilot=False)
    return os.path.join(dist, PAGE)


@unittest.skipUnless(HAS_DEMO, "демо-книги нет: это книга, а не репозиторий движка")
@unittest.skipUnless(BROWSER, "нет Firefox (PATH или MERMAID_BROWSER)")
class ThemeMenuBehaviourTest(unittest.TestCase):
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

    def test_closed_by_default_and_lists_every_theme(self):
        s = self.r["initial"]
        self.assertFalse(s["open"])
        self.assertEqual(s["expanded"], "false")
        self.assertEqual(s["visibility"], "hidden")
        self.assertEqual(s["items"], 10)
        self.assertEqual(s["icons"], 10)

    def test_click_on_icon_opens_list_with_current_theme_marked(self):
        s = self.r["opened"]
        self.assertTrue(s["open"])
        self.assertEqual(s["expanded"], "true")
        self.assertEqual(s["visibility"], "visible")
        self.assertEqual(s["current"], "amber")

    def test_click_outside_closes_without_changing_theme(self):
        s = self.r["outside"]
        self.assertFalse(s["open"])
        self.assertEqual(s["theme"], "amber")
        self.assertIsNone(s["stored"])

    def test_second_click_on_icon_closes(self):
        self.assertFalse(self.r["toggledClosed"]["open"])

    def test_escape_closes_without_changing_theme(self):
        s = self.r["escape"]
        self.assertFalse(s["open"])
        self.assertEqual(s["theme"], "amber")
        self.assertIsNone(s["stored"])

    def test_picking_a_theme_applies_saves_and_keeps_list_open(self):
        s = self.r["picked"]
        self.assertTrue(s["open"])
        self.assertEqual(s["theme"], "paper")
        self.assertEqual(s["stored"], "paper")
        self.assertEqual(s["current"], "paper")

    def test_list_stays_open_to_switch_themes_quickly(self):
        s = self.r["switched"]
        self.assertTrue(s["open"])
        self.assertEqual(s["theme"], "light")
        self.assertEqual(s["stored"], "light")
        self.assertEqual(s["current"], "light")

    def test_escape_after_picking_closes_and_keeps_last_theme(self):
        s = self.r["afterPickEscape"]
        self.assertFalse(s["open"])
        self.assertEqual(s["theme"], "light")


if __name__ == "__main__":
    unittest.main()
