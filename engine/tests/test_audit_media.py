"""Проверки аудита для изображений ([media], engine/audit.py п. 12) на пробной книге из test_media.py:
alt, атрибуция, лицензии, пределы размера, неиспользуемые файлы, бюджет. Без браузера."""
import unittest

from engine.tests.test_media import CREDITS_A, MediaBook, png_bytes


class AuditMediaTest(unittest.TestCase):
    CLEAN = "# Урок\n\n![a](media/a.png)\n\n![[scheme.svg|С]]\n\n![p](media/pd.gif)\n"
    DEEP = "# Глубокий\n\n![b](media/b.png)\n"

    def run_audit(self, lesson=CLEAN, deep=DEEP, extra_toml="", files=None, strict=False):
        book = MediaBook(lesson, deep=deep, extra_toml=extra_toml, files=files)
        try:
            book.build()
            return book.audit(strict=strict)
        finally:
            book.close()

    def test_clean_book_and_summary(self):
        ok, a, out = self.run_audit()
        self.assertTrue(ok, a.media_errors + a.media_warnings)
        self.assertEqual((a.media_errors, a.media_warnings), ([], []))
        self.assertIn("Медиа: файлов 4,", out)
        self.assertIn("из бюджета 700 МБ", out)

    def test_empty_alt(self):
        ok, a, _ = self.run_audit(deep="# Глубокий\n\n![](media/b.png)\n")
        self.assertFalse(ok)
        self.assertEqual(len(a.media_errors), 1)
        self.assertIn("b.png: пустой alt", a.media_errors[0])
        ok, a, _ = self.run_audit(deep="# Глубокий\n\n![](media/b.png)\n", extra_toml="require_alt = false\n")
        self.assertTrue(ok)

    def test_credit_requirements_and_license(self):
        files = {"sources/1. Модуль/2. Раздел/media/credits.toml": '["b.png"]\nlicense = "CC BY-NC 4.0"\n',
                 "sources/1. Модуль/media/c.png": png_bytes(1, 1)}
        ok, a, _ = self.run_audit(lesson=self.CLEAN + "\n![c](media/c.png)\n", files=files)
        self.assertFalse(ok)
        text = "\n".join(a.media_errors)
        self.assertIn('1. Модуль/media/c.png: нет записи ["c.png"] в credits.toml', text)
        self.assertIn("b.png: в credits.toml нет author, source", text)
        self.assertIn("b.png: лицензия «CC BY-NC 4.0» не из allowed_licenses", text)
        ok, a, _ = self.run_audit(lesson=self.CLEAN + "\n![c](media/c.png)\n", files=files,
                                  extra_toml='require_credit = false\nallowed_licenses = []\n')
        self.assertTrue(ok, a.media_errors)

    def test_limits_are_warnings_strict_errors(self):
        files = {"sources/1. Модуль/media/a.png": png_bytes(3000, 2)}
        ok, a, out = self.run_audit(files=files, extra_toml="max_file_kb = 0\n")
        self.assertTrue(ok)
        self.assertEqual(len(a.media_warnings), 1)
        self.assertIn("3000×2 px — сторона больше max_dimension_px = 2000", a.media_warnings[0])
        self.assertIn("Замечания по изображениям: 1", out)
        ok, a, out = self.run_audit(files=files, extra_toml="max_file_kb = 0\n", strict=True)
        self.assertFalse(ok)
        self.assertIn("ЗАМЕЧАНИЯ ПО ИЗОБРАЖЕНИЯМ (--strict)", out)
        big = {"sources/1. Модуль/media/a.png": png_bytes(40, 20) + b"\x00" * 3000}
        ok, a, _ = self.run_audit(files=big, extra_toml="max_file_kb = 2\n")
        self.assertTrue(any("КБ — больше max_file_kb = 2" in w for w in a.media_warnings), a.media_warnings)

    def test_unused_unknown_names_and_orphans(self):
        files = {"sources/1. Модуль/media/лишний.png": png_bytes(1, 1),
                 "sources/1. Модуль/media/notes.txt": "x",
                 "sources/1. Модуль/media/broken.webp": b"RIFF"}
        credits = CREDITS_A + '\n["лишний.png"]\nlicense = "own"\n\n["broken.webp"]\nlicense = "own"\n\n["gone.png"]\nlicense = "own"\n'
        files["sources/1. Модуль/media/credits.toml"] = credits
        ok, a, _ = self.run_audit(lesson=self.CLEAN + "\n![x](media/broken.webp)\n", files=files)
        self.assertTrue(ok, a.media_errors)
        text = "\n".join(a.media_warnings)
        self.assertIn("лишний.png: не используется ни на одной странице", text)
        self.assertIn("лишний.png: имя файла не латиницей", text)
        self.assertIn("notes.txt: расширение не из media.extensions", text)
        self.assertIn("broken.webp: размер из заголовка файла не прочитан", text)
        self.assertIn('1. Модуль/media/credits.toml: запись ["gone.png"] без файла', text)
        self.assertNotIn("broken.webp: не используется", text)

    def test_budget_and_missing_embed(self):
        ok, a, _ = self.run_audit(extra_toml="budget_mb = 0\n")
        self.assertTrue(ok)
        files = {"sources/1. Модуль/media/a.png": png_bytes(40, 20) + b"\x00" * (1024 * 1024 + 10)}
        ok, a, out = self.run_audit(files=files, extra_toml="budget_mb = 1\nmax_file_kb = 0\n")
        self.assertFalse(ok)
        self.assertIn("суммарный объём медиа 1.0 МБ больше budget_mb = 1", a.media_errors[-1])
        ok, a, out = self.run_audit(lesson=self.CLEAN + "\n![[nope.png|Нет]]\n")
        self.assertFalse(ok)
        self.assertTrue(any('<img src="media/nope.png">: файла нет' in m for _, m in a.missing_assets), a.missing_assets)


if __name__ == "__main__":
    unittest.main()
