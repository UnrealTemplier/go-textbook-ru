"""Тесты рантайм-проекции без браузера: сравнение проекций и зеркало каталога."""
import os
import tempfile
import unittest

from engine.tools import runtime_projection as rp


class CompareTest(unittest.TestCase):
    def test_equal_and_changed(self):
        a = {"p.html": {"katex": 2, "mermaid_svg": 1}}
        self.assertEqual(rp.compare(a, a), [])
        b = {"p.html": {"katex": 3, "mermaid_svg": 1}}
        self.assertEqual(rp.compare(a, b), ["p.html: katex 2 → 3"])
        self.assertEqual(rp.compare(a, b, {"p.html": {"katex": 3}}), [])

    def test_missing_pages(self):
        self.assertEqual(rp.compare({"a.html": {}}, {"b.html": {}}),
                         ["a.html: нет в новой проекции", "b.html: нет в старой проекции"])


class MirrorTest(unittest.TestCase):
    def test_symlink_tree_and_pages(self):
        with tempfile.TemporaryDirectory() as tmp:
            dist = os.path.join(tmp, "dist")
            os.makedirs(os.path.join(dist, "docs", "m"))
            for rel in ("index.html", "docs/m/a.html", "docs/m/x.css"):
                with open(os.path.join(dist, rel), "w") as fp:
                    fp.write(rel)
            self.assertEqual(rp.list_pages(dist), ["docs/m/a.html", "index.html"])
            site = os.path.join(tmp, "site")
            rp.mirror(dist, site)
            self.assertTrue(os.path.islink(os.path.join(site, "docs/m/x.css")))
            with open(os.path.join(site, "docs/m/a.html")) as fp:
                self.assertEqual(fp.read(), "docs/m/a.html")
            self.assertEqual(rp.probe_name("docs/m/a.html"), "docs/m/a.__rp.html")


if __name__ == "__main__":
    unittest.main()
