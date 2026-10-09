"""Тесты engine.sync (анализ § 4.2): источник — каталог, архив, git; локальные правки; удаление лишнего."""
import contextlib
import io
import os
import subprocess
import tarfile
import tempfile
import unittest

from engine import checksums
from engine.sync import main

GIT_ENV = dict(os.environ, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@t", GIT_COMMITTER_NAME="t",
               GIT_COMMITTER_EMAIL="t@t", GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM="1")


def write(root, rel, text):
    path = os.path.join(root, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fp:
        fp.write(text)


def read(root, rel):
    with open(os.path.join(root, rel), encoding="utf-8") as fp:
        return fp.read()


def make_engine(root, version, files):
    write(root, "engine/VERSION", version + "\n")
    write(root, "engine/build.py", "# build\n")
    for rel, text in files.items():
        write(root, "engine/" + rel, text)
    checksums.write(os.path.join(root, "engine"))


def git(cwd, *args):
    subprocess.run(["git", "-C", cwd, *args], check=True, capture_output=True, env=GIT_ENV)


class SyncTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.src = os.path.join(self.tmp.name, "engine-repo")
        self.book = os.path.join(self.tmp.name, "book")
        make_engine(self.src, "1.2.0", {"a.py": "new\n", "sub/c.py": "c\n"})
        make_engine(self.book, "1.1.0", {"a.py": "old\n", "gone.py": "x\n"})
        write(self.book, "book.toml", "")

    def tearDown(self):
        self.tmp.cleanup()

    def run_sync(self, *args):
        out = io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(out):
            code = main(["--book", self.book, *args])
        return code, out.getvalue()

    def test_replace_from_directory(self):
        code, out = self.run_sync("--from", self.src, "--no-commit")
        self.assertEqual(code, 0, out)
        self.assertEqual(read(self.book, "engine/a.py"), "new\n")
        self.assertEqual(read(self.book, "engine/VERSION"), "1.2.0\n")
        self.assertFalse(os.path.exists(os.path.join(self.book, "engine/gone.py")))
        self.assertEqual(checksums.verify(os.path.join(self.book, "engine")), [])
        self.assertIn("1.1.0 → 1.2.0", out)
        self.assertFalse(any(n.startswith(".engine-sync") for n in os.listdir(self.book)))

    def test_local_change_stops_sync(self):
        write(self.book, "engine/a.py", "my local fix\n")
        code, out = self.run_sync("--from", self.src, "--no-commit")
        self.assertEqual(code, 1)
        self.assertIn("изменён: a.py", out)
        self.assertIn("+my local fix", out)
        self.assertEqual(read(self.book, "engine/a.py"), "my local fix\n")
        code, _ = self.run_sync("--from", self.src, "--no-commit", "--force")
        self.assertEqual((code, read(self.book, "engine/a.py")), (0, "new\n"))

    def test_broken_source_rejected(self):
        write(self.src, "engine/a.py", "tampered\n")
        code, out = self.run_sync("--from", self.src, "--no-commit")
        self.assertEqual(code, 2)
        self.assertIn("контрольными суммами", out)

    def test_tarball(self):
        archive = os.path.join(self.tmp.name, "engine-1.2.0.tar.gz")
        with tarfile.open(archive, "w:gz") as tar:
            tar.add(self.src, arcname="html-textbook-engine-1.2.0")
        code, out = self.run_sync("--from", archive, "--no-commit")
        self.assertEqual(code, 0, out)
        self.assertEqual(read(self.book, "engine/sub/c.py"), "c\n")

    def test_git_url_and_commit(self):
        for repo in (self.src, self.book):
            git(repo, "init", "-q", "-b", "main")
            git(repo, "add", "-A")
            git(repo, "commit", "-q", "-m", "init")
        old_env = os.environ.copy()
        os.environ.update(GIT_ENV)
        try:
            code, out = self.run_sync("--from", "file://" + self.src)
        finally:
            os.environ.clear()
            os.environ.update(old_env)
        self.assertEqual(code, 0, out)
        log = subprocess.run(["git", "-C", self.book, "log", "-1", "--format=%s"], capture_output=True, text=True).stdout
        self.assertEqual(log.strip(), "chore(engine): sync to v1.2.0")
        status = subprocess.run(["git", "-C", self.book, "status", "--porcelain"], capture_output=True, text=True).stdout
        self.assertEqual(status, "")


if __name__ == "__main__":
    unittest.main()
