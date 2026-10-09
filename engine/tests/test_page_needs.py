"""Тесты условной загрузки библиотек (А3в): какие скрипты нужны странице."""
import unittest

from engine.config import BookConfig, FeaturesConfig
from engine.template import page_needs


class PageNeedsTest(unittest.TestCase):
    def test_detection(self):
        cfg = BookConfig()
        self.assertEqual(page_needs("<p>Просто текст</p>", cfg), {"mermaid": False, "prism": False, "katex": False})
        self.assertTrue(page_needs('<figure><pre class="mermaid">graph TD</pre></figure>', cfg)["mermaid"])
        self.assertTrue(page_needs('<div class="code-block" data-lang="go">', cfg)["prism"])
        self.assertTrue(page_needs("<p>Цена $x$ и \\(y\\)</p>", cfg)["katex"])

    def test_dollar_in_code_does_not_count(self):
        cfg = BookConfig()
        html = '<p>Без формул</p><pre><code>echo $HOME</code></pre><p><code>$GOPATH</code></p>'
        self.assertFalse(page_needs(html, cfg)["katex"])

    def test_disabled_loads_everything(self):
        cfg = BookConfig(features=FeaturesConfig(conditional_scripts=False))
        self.assertEqual(page_needs("<p>x</p>", cfg), {"mermaid": True, "prism": True, "katex": True})


if __name__ == "__main__":
    unittest.main()


class IconSpriteTest(unittest.TestCase):
    def test_copy_icon_uses_sprite(self):
        from engine.converter import MarkdownConverter
        from engine.template import ICON_SPRITE
        html = MarkdownConverter(None)._enhance_code_blocks('<pre><code class="language-go">x</code></pre>')
        self.assertIn('<use href="#icon-copy"></use>', html)
        self.assertNotIn("<rect", html)
        self.assertIn('<symbol id="icon-copy"', ICON_SPRITE)
