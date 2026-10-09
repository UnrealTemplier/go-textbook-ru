"""
engine/checksums.py
Контрольные суммы файлов ядра (анализ § 4.2): engine/.checksums.json — SHA-256 каждого файла.

В книге engine/ не редактируется: сборка сверяет суммы и предупреждает о локальных правках.
Файл сумм создаётся при выпуске версии ядра (А5) и обновляется engine.sync.

  python -m engine.checksums --write    записать engine/.checksums.json
  python -m engine.checksums            проверить (код возврата 1 при расхождении)
"""

import hashlib
import json
import os
import sys
from typing import Dict, List

ENGINE_DIR = os.path.dirname(os.path.abspath(__file__))
CHECKSUMS_FILE = os.path.join(ENGINE_DIR, ".checksums.json")
SKIP_DIRS = {"__pycache__"}


def compute(engine_dir: str = ENGINE_DIR) -> Dict[str, str]:
    out = {}
    for root, dirs, files in os.walk(engine_dir):
        dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS)
        for f in sorted(files):
            path = os.path.join(root, f)
            rel = os.path.relpath(path, engine_dir).replace(os.sep, "/")
            if rel == ".checksums.json" or f.endswith(".pyc"):
                continue
            with open(path, "rb") as fp:
                out[rel] = hashlib.sha256(fp.read()).hexdigest()
    return out


def verify(engine_dir: str = ENGINE_DIR) -> List[str]:
    """Расхождения с .checksums.json; пустой список — совпадает или файла сумм нет."""
    path = os.path.join(engine_dir, ".checksums.json")
    if not os.path.isfile(path):
        return []
    with open(path, encoding="utf-8") as fp:
        expected = json.load(fp)
    actual = compute(engine_dir)
    issues = [f"изменён: {p}" for p in sorted(expected) if p in actual and actual[p] != expected[p]]
    issues += [f"удалён: {p}" for p in sorted(set(expected) - set(actual))]
    issues += [f"добавлен: {p}" for p in sorted(set(actual) - set(expected))]
    return issues


def write(engine_dir: str = ENGINE_DIR) -> None:
    with open(os.path.join(engine_dir, ".checksums.json"), "w", encoding="utf-8") as fp:
        json.dump(compute(engine_dir), fp, ensure_ascii=False, indent=1, sort_keys=True)
        fp.write("\n")


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if "--write" in argv:
        write()
        print(f"Записано: {CHECKSUMS_FILE}")
        return 0
    issues = verify()
    for i in issues:
        print(i)
    return 1 if issues else 0


if __name__ == "__main__":
    sys.exit(main())
