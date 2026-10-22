"""Окно увеличения изображений ([media] lightbox, assets/media.js) и стили рисунков в headless Firefox.

Страница демо-книги «Иллюстрации»: шесть картинок (рисунки, галерея, строчная, встраивание). Сценарий: клик
открывает окно, картинка вписана в область, фокус на кнопке «Закрыть», стрелки листают, «1:1» даёт
натуральный размер, Esc, фон и пустое место вокруг картинки закрывают, фокус возвращается; Enter на картинке
открывает окно. Отдельно: инверсия схемы только в тёмных темах, галерея в одну колонку на телефоне.
Без Firefox или демо-книги тест пропускается.
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

PAGE = "docs/01-osnovy/3-illyustratsii.html"

LIGHTBOX_JS = """(function(){
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
window.addEventListener('load',()=>setTimeout(async()=>{const r={};try{
 const m=document.getElementById('md-lightbox'),body=document.getElementById('md-lightbox-body'),
   view=document.getElementById('md-lightbox-img'),counter=document.getElementById('md-lightbox-counter'),
   cap=document.getElementById('md-lightbox-caption');
 const imgs=Array.from(document.querySelectorAll('.article-markdown img.md-zoom'));
 r.count=imgs.length;r.tabindex=imgs.every(i=>i.getAttribute('tabindex')==='0');
 r.hiddenBefore=m.getAttribute('aria-hidden');
 imgs[0].click();await sleep(300);
 r.opened=m.classList.contains('active');r.hidden=m.getAttribute('aria-hidden');
 r.src=view.getAttribute('src');r.counter=counter.textContent;r.caption=cap.textContent.trim();
 r.focusClose=document.activeElement&&document.activeElement.getAttribute('data-action');
 const fits=()=>{const b=body.getBoundingClientRect(),v=view.getBoundingClientRect();
   return v.width>0&&v.left>=b.left-1&&v.right<=b.right+1&&v.top>=b.top-1&&v.bottom<=b.bottom+1;};
 r.fit=fits();r.fitWidth=Math.round(view.getBoundingClientRect().width);
 document.dispatchEvent(new KeyboardEvent('keydown',{key:'ArrowRight',bubbles:true}));await sleep(300);
 r.nextSrc=view.getAttribute('src');r.nextCounter=counter.textContent;r.nextCaption=cap.textContent.trim();
 m.querySelector('[data-action="lightbox-fit"]').click();await sleep(50);
 r.naturalWidth=Math.round(parseFloat(view.style.width));
 m.querySelector('[data-action="lightbox-fit"]').click();await sleep(50);r.refit=fits();
 document.dispatchEvent(new KeyboardEvent('keydown',{key:'ArrowLeft',bubbles:true}));
 document.dispatchEvent(new KeyboardEvent('keydown',{key:'ArrowLeft',bubbles:true}));await sleep(200);
 r.wrapCounter=counter.textContent;
 document.dispatchEvent(new KeyboardEvent('keydown',{key:'Escape',bubbles:true}));await sleep(50);
 r.closedByEsc=!m.classList.contains('active');r.focusBack=document.activeElement===imgs[0];
 r.overflow=document.body.style.overflow;
 imgs[1].focus();imgs[1].dispatchEvent(new KeyboardEvent('keydown',{key:'Enter',bubbles:true}));await sleep(200);
 r.openedByEnter=m.classList.contains('active');r.enterCounter=counter.textContent;
 m.querySelector('.modal-backdrop').click();await sleep(50);r.closedByBackdrop=!m.classList.contains('active');
 imgs[2].click();await sleep(200);body.click();await sleep(50);r.closedByBody=!m.classList.contains('active');
 const inv=document.querySelector('.article-markdown img.md-invert-dark'),plain=imgs.find(i=>!i.classList.contains('md-invert-dark'));
 const filt=t=>{document.documentElement.dataset.theme=t;return getComputedStyle(inv).filter;};
 r.filters={amber:filt('amber'),synthwave:filt('synthwave'),light:filt('light'),vintage:filt('vintage'),paper:filt('paper')};
 document.documentElement.dataset.theme='amber';r.plainFilter=getComputedStyle(plain).filter;
 r.figcaptionAlign=getComputedStyle(document.querySelector('.md-figure figcaption')).textAlign;
}catch(e){r.error=String(e&&e.stack||e);} send(r);},300));})();"""

PHONE_JS = """(function(){window.addEventListener('load',()=>setTimeout(()=>{
const g=document.querySelector('.md-gallery'),figs=g.querySelectorAll('.md-figure');
send({cols:getComputedStyle(g).gridTemplateColumns.split(' ').length,
      stacked:figs[1].getBoundingClientRect().top>=figs[0].getBoundingClientRect().bottom,
      overflow:document.documentElement.scrollWidth<=window.innerWidth+1,width:window.innerWidth});},300));})();"""


@unittest.skipUnless(HAS_DEMO, "демо-книги нет: это книга, а не репозиторий движка")
@unittest.skipUnless(BROWSER, "нет Firefox (PATH или MERMAID_BROWSER)")
class MediaLightboxRuntimeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.dist = os.path.join(cls.tmp.name, "dist")
        with contextlib.redirect_stdout(io.StringIO()):
            build(load_config(os.path.join(DEMO_ROOT, "book.toml")), dist_dir=cls.dist, is_pilot=False)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_lightbox(self):
        r = probe(os.path.join(self.dist, PAGE), lambda h: h, LIGHTBOX_JS)
        self.assertIsNotNone(r, "страница не прислала результат")
        self.assertNotIn("error", r, r.get("error"))
        self.assertEqual(r["count"], 6)
        self.assertTrue(r["tabindex"])
        self.assertEqual((r["hiddenBefore"], r["opened"], r["hidden"]), ("true", True, "false"))
        self.assertTrue(r["src"].endswith("media/scheme.svg"), r["src"])
        self.assertEqual(r["counter"], "1 / 6")
        self.assertIn("Процессор и память", r["caption"])
        self.assertIn("Автор: html-textbook-engine", r["caption"])
        self.assertEqual(r["focusClose"], "lightbox-close")
        self.assertTrue(r["fit"])
        self.assertGreater(r["fitWidth"], 560)                     # схема 560 px растянута на окно
        self.assertTrue(r["nextSrc"].endswith("media/sunset.png"), r["nextSrc"])
        self.assertEqual(r["nextCounter"], "2 / 6")
        self.assertIn("Закат над горами", r["nextCaption"])
        self.assertEqual(r["naturalWidth"], 480)                   # «1:1» — натуральный размер
        self.assertTrue(r["refit"])
        self.assertEqual(r["wrapCounter"], "6 / 6")                # листание по кругу
        self.assertTrue(r["closedByEsc"])
        self.assertTrue(r["focusBack"])
        self.assertEqual(r["overflow"], "")
        self.assertTrue(r["openedByEnter"])
        self.assertEqual(r["enterCounter"], "2 / 6")
        self.assertTrue(r["closedByBackdrop"])
        self.assertTrue(r["closedByBody"])
        for theme in ("amber", "synthwave"):
            self.assertIn("invert(1)", r["filters"][theme], theme)
        for theme in ("light", "vintage", "paper"):
            self.assertEqual(r["filters"][theme], "none", theme)
        self.assertEqual(r["plainFilter"], "none")                 # фотографии не инвертируются
        self.assertEqual(r["figcaptionAlign"], "center")

    def test_gallery_single_column_on_phone(self):
        r = probe(os.path.join(self.dist, PAGE), lambda h: h, PHONE_JS, frame_width=390)
        self.assertIsNotNone(r, "страница не прислала результат")
        self.assertEqual(r["width"], 390)
        self.assertEqual(r["cols"], 1)
        self.assertTrue(r["stacked"])
        self.assertTrue(r["overflow"], "горизонтальная прокрутка страницы")


if __name__ == "__main__":
    unittest.main()
