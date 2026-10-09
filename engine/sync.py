"""
engine/sync.py
Обновление ядра в книге (анализ § 4.2): python -m engine.sync --from <путь | git-URL | tarball>

В книге engine/ не редактируется: вся настройка — book.toml, book/overrides/, book/assets/,
book/hooks.py. Синхронизация:

1. Получает новую версию ядра: каталог (корень репозитория движка или сам engine/),
   git-URL (git clone --depth 1) или архив .tar.gz/.tgz/.tar.
2. Проверяет источник: engine/.checksums.json обязан совпадать с файлами (выпуск не повреждён).
3. Проверяет книгу: если engine/ правили локально (расхождение с её .checksums.json), печатает
   изменения и останавливается (--force — заменить всё равно). Без файла сумм (первая
   синхронизация) локальные правки проверить нельзя — об этом печатается предупреждение.
4. Заменяет engine/ целиком и атомарно: файлы, которых нет в новой версии, удаляются.
5. Делает один коммит «chore(engine): sync to vX.Y.Z» (только engine/; --no-commit — без коммита).

Запуск из корня книги; --book задаёт корень книги явно (например, первый запуск из репозитория
движка, когда в книге ещё нет engine/sync.py).
"""

import argparse
import difflib
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
from typing import List, Optional, Tuple

from . import checksums

SKIP = shutil.ignore_patterns("__pycache__", "*.pyc")


def read_version(engine_dir: str) -> str:
    path = os.path.join(engine_dir, "VERSION")
    if not os.path.isfile(path):
        return "?"
    with open(path, encoding="utf-8") as fp:
        return fp.read().strip()


def _engine_in(root: str) -> Optional[str]:
    """engine/ внутри каталога: сам каталог, root/engine или единственный подкаталог/engine (архив)."""
    if os.path.isfile(os.path.join(root, "VERSION")) and os.path.isfile(os.path.join(root, "build.py")):
        return root
    if os.path.isdir(os.path.join(root, "engine")):
        return os.path.join(root, "engine")
    subdirs = [d for d in os.listdir(root) if os.path.isdir(os.path.join(root, d))]
    if len(subdirs) == 1 and os.path.isdir(os.path.join(root, subdirs[0], "engine")):
        return os.path.join(root, subdirs[0], "engine")
    return None


def _safe_extract(archive: str, dest: str) -> None:
    with tarfile.open(archive) as tar:
        if hasattr(tarfile, "data_filter"):
            tar.extractall(dest, filter="data")
            return
        root = os.path.realpath(dest)
        for member in tar.getmembers():
            target = os.path.realpath(os.path.join(dest, member.name))
            if not (target == root or target.startswith(root + os.sep)) or member.issym() or member.islnk():
                raise SyncError(f"небезопасный путь в архиве: {member.name}")
        tar.extractall(dest)


class SyncError(Exception):
    pass


def fetch(source: str, tmp: str) -> str:
    """Каталог engine/ новой версии (во временном каталоге для git-URL и архивов)."""
    if os.path.isdir(source):
        found = _engine_in(os.path.abspath(source))
    elif source.endswith((".tar.gz", ".tgz", ".tar")) and os.path.isfile(source):
        _safe_extract(source, tmp)
        found = _engine_in(tmp)
    else:
        clone = os.path.join(tmp, "clone")
        res = subprocess.run(["git", "clone", "--quiet", "--depth", "1", source, clone],
                             capture_output=True, text=True)
        if res.returncode != 0:
            raise SyncError(f"git clone {source}: {res.stderr.strip()}")
        found = _engine_in(clone)
    if not found:
        raise SyncError(f"в {source} нет каталога engine/ с VERSION и build.py")
    return found


def local_changes(target: str, source: str) -> Tuple[List[str], List[str]]:
    """(расхождения engine/ книги с её суммами, unified diff изменённых файлов против новой версии)."""
    issues = checksums.verify(target)
    diffs = []
    for issue in issues:
        kind, rel = issue.split(": ", 1)
        if kind != "изменён":
            continue
        new_path = os.path.join(source, rel)
        with open(os.path.join(target, rel), encoding="utf-8", errors="replace") as fp:
            mine = fp.readlines()
        theirs = []
        if os.path.isfile(new_path):
            with open(new_path, encoding="utf-8", errors="replace") as fp:
                theirs = fp.readlines()
        diffs.extend(difflib.unified_diff(theirs, mine, f"новая версия/{rel}", f"книга/{rel}"))
    return issues, diffs


def replace_engine(source: str, book: str) -> Tuple[List[str], List[str], List[str]]:
    """Атомарная замена book/engine копией source; (добавлены, удалены, изменены)."""
    target = os.path.join(book, "engine")
    old = checksums.compute(target) if os.path.isdir(target) else {}
    new = checksums.compute(source)
    staging = os.path.join(book, ".engine-sync-new")
    backup = os.path.join(book, ".engine-sync-old")
    for path in (staging, backup):
        shutil.rmtree(path, ignore_errors=True)
    shutil.copytree(source, staging, ignore=SKIP)
    if os.path.isdir(target):
        os.rename(target, backup)
    try:
        os.rename(staging, target)
    except OSError:
        if os.path.isdir(backup):
            os.rename(backup, target)
        raise
    shutil.rmtree(backup, ignore_errors=True)
    added = sorted(set(new) - set(old))
    removed = sorted(set(old) - set(new))
    changed = sorted(p for p in set(old) & set(new) if old[p] != new[p])
    return added, removed, changed


def commit(book: str, version: str) -> bool:
    if subprocess.run(["git", "-C", book, "rev-parse", "--git-dir"], capture_output=True).returncode != 0:
        print("Книга не в git: коммит не сделан")
        return False
    subprocess.run(["git", "-C", book, "add", "-A", "--", "engine"], check=True)
    if subprocess.run(["git", "-C", book, "diff", "--cached", "--quiet", "--", "engine"]).returncode == 0:
        print("engine/ не изменился: коммит не нужен")
        return False
    subprocess.run(["git", "-C", book, "commit", "--quiet", "-m", f"chore(engine): sync to v{version}", "--", "engine"],
                   check=True)
    return True


def sync(source: str, book: str, force: bool = False, do_commit: bool = True) -> int:
    book = os.path.abspath(book)
    target = os.path.join(book, "engine")
    with tempfile.TemporaryDirectory(prefix="engine-sync-") as tmp:
        src = fetch(source, tmp)
        if os.path.realpath(src) == os.path.realpath(target):
            raise SyncError("источник и engine/ книги — один и тот же каталог")
        if not os.path.isfile(os.path.join(src, ".checksums.json")):
            raise SyncError(f"в источнике нет engine/.checksums.json: это не выпуск ядра ({src})")
        broken = checksums.verify(src)
        if broken:
            raise SyncError("файлы источника не совпадают с его контрольными суммами: " + "; ".join(broken[:5]))
        new_version, old_version = read_version(src), read_version(target)
        if os.path.isdir(target):
            if os.path.isfile(os.path.join(target, ".checksums.json")):
                issues, diffs = local_changes(target, src)
                if issues and not force:
                    print("engine/ книги изменён локально — синхронизация остановлена:")
                    for i in issues:
                        print("  " + i)
                    sys.stdout.writelines(diffs)
                    print("Перенесите правки в репозиторий движка или запустите с --force (правки пропадут).")
                    return 1
            else:
                print("⚠️ В книге нет engine/.checksums.json: локальные правки ядра проверить нельзя "
                      "(первая синхронизация). Файлы, которых нет в новой версии, будут удалены.")
        added, removed, changed = replace_engine(src, book)
    print(f"engine: {old_version} → {new_version}; добавлено {len(added)}, удалено {len(removed)}, изменено {len(changed)}")
    for title, items in (("добавлены", added), ("удалены", removed), ("изменены", changed)):
        if items:
            print(f"  {title}: " + ", ".join(items[:20]) + (" …" if len(items) > 20 else ""))
    if do_commit:
        commit(book, new_version)
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Обновление engine/ книги из репозитория html-textbook-engine")
    ap.add_argument("--from", dest="source", required=True, help="каталог, git-URL или архив .tar.gz с engine/")
    ap.add_argument("--book", default=".", help="корень книги (по умолчанию текущий каталог)")
    ap.add_argument("--force", action="store_true", help="заменить engine/, даже если его правили локально")
    ap.add_argument("--no-commit", action="store_true", help="не делать коммит")
    args = ap.parse_args(argv)
    try:
        return sync(args.source, args.book, force=args.force, do_commit=not args.no_commit)
    except SyncError as e:
        print(f"Ошибка синхронизации: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
