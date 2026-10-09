"""
engine/audit.py
Сквозной аудит качества (QA):
1. Проверка кроссплатформенной совместимости имен файлов (Windows, macOS, Linux).
2. Проверка целостности ссылок (0 broken links).
3. Валидность анкоров и структуры.
4. Отсутствие управляющих символов в sources/*.md (C0 кроме \n/\t, DEL; TAB внутри формул вне кода).
5. Корректность и синтаксис диаграмм Mermaid (статические проверки + реальный разбор
   вендорным mermaid.min.js в headless-браузере Firefox по протоколу file://).
"""

import os
import re
import sys
import html
import json
import shutil
import argparse
import tempfile
import threading
import subprocess
import http.server
from urllib.parse import unquote, urlparse, parse_qs
from typing import List, Dict, Tuple, Set, Optional

# Недопустимые символы Windows (NTFS / FAT): < > : " / \ | ? * и управляющие символы 0-31
WIN_FORBIDDEN_CHARS = set("<>:\"/\\|?*")
# Зарезервированные имена устройств DOS / Windows
WIN_RESERVED_NAMES = {
    "CON", "PRN", "AUX", "NUL",
    *(f"COM{i}" for i in range(1, 10)),
    *(f"LPT{i}" for i in range(1, 10))
}

# Максимальное время одного прогона разбора диаграмм в браузере, секунды
MERMAID_RUNTIME_TIMEOUT = 300

# Открывающая/закрывающая ограда кода (в выносках строка начинается с '>')
FENCE_RE = re.compile(r"^\s*(`{3,}|~{3,})")
CALLOUT_PREFIX_RE = re.compile(r"^(\s*>)+\s?")
INLINE_CODE_RE = re.compile(r"(`+)(.+?)(?<!`)\1(?!`)")


def code_mask(text: str) -> bytearray:
    """Отмечает символы, лежащие в коде: ограды (в том числе внутри выносок) и inline-код."""
    mask = bytearray(len(text))
    pos = 0
    fence = None
    for line in text.split("\n"):
        start, end = pos, pos + len(line)
        pos = end + 1
        body = CALLOUT_PREFIX_RE.sub("", line)
        m = FENCE_RE.match(body)
        if fence:
            mask[start:end] = b"\x01" * (end - start)
            if m and m.group(1)[0] == fence[0] and len(m.group(1)) >= len(fence) and body.strip() == m.group(1):
                fence = None
            continue
        if m:
            fence = m.group(1)
            mask[start:end] = b"\x01" * (end - start)
            continue
        for cm in INLINE_CODE_RE.finditer(line):
            mask[start + cm.start():start + cm.end()] = b"\x01" * (cm.end() - cm.start())
    return mask


def formula_spans(text: str, mask: bytearray) -> List[Tuple[int, int]]:
    """Границы формул $…$ (в пределах строки) и $$…$$ (через строки) вне кода."""
    spans = []
    i, n = 0, len(text)
    while i < n:
        if text[i] == "$" and not mask[i] and (i == 0 or text[i - 1] != "\\"):
            if text.startswith("$$", i):
                j = text.find("$$", i + 2)
                if j != -1:
                    spans.append((i, j + 2))
                    i = j + 2
                    continue
            else:
                j = i + 1
                while j < n and text[j] != "\n" and not (text[j] == "$" and text[j - 1] != "\\"):
                    j += 1
                if j < n and text[j] == "$":
                    spans.append((i, j + 1))
                    i = j + 1
                    continue
        i += 1
    return spans


class SiteAuditor:
    def __init__(self, dist_dir: str = "./dist", repo_root: str = ".", mermaid_runtime: bool = True):
        self.mermaid_runtime = mermaid_runtime
        # (страница, порядковый номер блока на странице, исходный код) — для рантайм-разбора
        self.mermaid_blocks: List[Tuple[str, int, str]] = []
        self.mermaid_warnings: List[Dict[str, str]] = []
        self.dist_dir = os.path.abspath(dist_dir)
        self.repo_root = os.path.abspath(repo_root)
        self.html_files: List[str] = []
        self.broken_links: List[Dict[str, str]] = []
        self.mermaid_errors: List[Dict[str, str]] = []
        self.missing_anchors: List[Dict[str, str]] = []
        self.filename_issues: List[Tuple[str, str]] = []
        self.control_char_issues: List[Tuple[str, int, str]] = []
        self.scanned_sources_count = 0
        self.scanned_dirs_count = 0
        self.scanned_files_count = 0

    def run_audit(self) -> bool:
        print("=====================================================================")
        print(f"🔬 Запуск сквозного аудита качества: {self.dist_dir}")
        print("=====================================================================")

        # 1. Проверка кроссплатформенной совместимости имен файлов
        print("[1/4] 🖥️ Проверка кроссплатформенной совместимости имен файлов (Windows / macOS / Linux)...")
        self._audit_filenames()
        print(f"      Просканировано каталогов: {self.scanned_dirs_count}, файлов: {self.scanned_files_count}")
        if self.filename_issues:
            print(f"      ❌ Найдено несовместимых имен: {len(self.filename_issues)}")
        else:
            print("      ✅ Все имена файлов и папок на 100% совместимы со всеми ОС.")

        # 1b. Управляющие символы в исходниках (порча вида '\text' -> TAB + 'ext')
        self._audit_control_chars()
        print(f"      Проверено исходников на управляющие символы: {self.scanned_sources_count}")
        if self.control_char_issues:
            print(f"      ❌ Найдено управляющих символов: {len(self.control_char_issues)}")
        else:
            print("      ✅ Управляющих символов в sources/ нет (TAB внутри формул тоже).")

        if not os.path.exists(self.dist_dir):
            print(f"❌ ОШИБКА: Директория {self.dist_dir} не найдена. Сначала выполните сборку!")
            return False

        # 2. Поиск всех HTML файлов
        for root, _, files in os.walk(self.dist_dir):
            for f in files:
                if f.endswith(".html"):
                    self.html_files.append(os.path.join(root, f))

        print(f"\n[2/4] 📄 Обнаружено HTML страниц: {len(self.html_files)}")
        if not self.html_files:
            print("❌ ОШИБКА: Нет сгенерированных страниц.")
            return False

        # 3. Аудит каждой страницы
        print(f"[3/4] 🔗 Проверка ссылок, анкоров и диаграмм...")
        
        # Кэш известных id для каждого файла
        file_ids_cache: Dict[str, Set[str]] = {}

        for page_path in self.html_files:
            self._audit_single_page(page_path, file_ids_cache)

        # 3b. Реальный разбор диаграмм рантаймом Mermaid (ловит ошибки, невидимые статическому анализу)
        if self.mermaid_runtime:
            self._audit_mermaid_runtime()
        else:
            print("      ℹ️ Рантайм-разбор Mermaid отключён (--no-mermaid-runtime).")

        # 4. Подведение итогов
        print("\n[4/4] 📊 Результаты проверки:")
        print(f"      Ошибок несовместимости имен файлов: {len(self.filename_issues)}")
        print(f"      Управляющих символов в sources/: {len(self.control_char_issues)}")
        print(f"      Всего проверено страниц: {len(self.html_files)}")
        print(f"      Битых ссылок (Broken Links): {len(self.broken_links)}")
        print(f"      Ошибок анкоров (Missing Anchors): {len(self.missing_anchors)}")
        print(f"      Ошибок диаграмм Mermaid: {len(self.mermaid_errors)}")
        print(f"      Предупреждений по диаграммам Mermaid: {len(self.mermaid_warnings)}")

        success = True

        if self.filename_issues:
            success = False
            print("\n❌ НАЙДЕНЫ НЕДОПУСТИМЫЕ ИМЕНА ФАЙЛОВ / ПАПОК ДЛЯ WINDOWS:")
            for path, desc in self.filename_issues[:15]:
                print(f"  Файл/Папка: {path}")
                print(f"  Проблема:   {desc}\n")
            if len(self.filename_issues) > 15:
                print(f"  ... и еще {len(self.filename_issues) - 15} ошибок имен файлов.")

        if self.control_char_issues:
            success = False
            print("\n❌ НАЙДЕНЫ УПРАВЛЯЮЩИЕ СИМВОЛЫ В ИСХОДНИКАХ:")
            for path, line_no, desc in self.control_char_issues[:15]:
                print(f"  {path}:{line_no}: {desc}")
            if len(self.control_char_issues) > 15:
                print(f"  ... и еще {len(self.control_char_issues) - 15} мест.")

        if self.broken_links:
            success = False
            print("\n❌ НАЙДЕНЫ БИТЫЕ ССЫЛКИ:")
            for item in self.broken_links[:10]:
                print(f"  В файле: {os.path.relpath(item['source'], self.dist_dir)}")
                print(f"  Цель:    {item['target']}")
                print(f"  Ссылка:  {item['raw_href']}\n")
            if len(self.broken_links) > 10:
                print(f"  ... и еще {len(self.broken_links) - 10} битых ссылок.")

        if self.missing_anchors:
            print(f"\n⚠️ Замечания по анкорам (#anchor): {len(self.missing_anchors)} штук.")
            for item in self.missing_anchors[:5]:
                print(f"  В файле: {os.path.relpath(item['source'], self.dist_dir)} -> {item['raw_href']}")

        if self.mermaid_warnings:
            print(f"\n⚠️ Замечания по диаграммам Mermaid: {len(self.mermaid_warnings)} штук.")
            for w in self.mermaid_warnings[:5]:
                print(f"  В файле: {os.path.relpath(w['file'], self.dist_dir)}")
                print(f"  Причина: {w['reason']}")

        if self.mermaid_errors:
            success = False
            print("\n❌ ОШИБКИ В ДИАГРАММАХ MERMAID:")
            for err in self.mermaid_errors[:20]:
                print(f"  В файле: {os.path.relpath(err['file'], self.dist_dir)}")
                print(f"  Причина: {err['reason']}\n")
            if len(self.mermaid_errors) > 20:
                print(f"  ... и еще {len(self.mermaid_errors) - 20} ошибок диаграмм.")

        print("=====================================================================")
        if success:
            print("🎉 АУДИТ ПРОЙДЕН УСПЕШНО! Все имена файлов, ссылки и диаграммы в безупречном состоянии.")
        else:
            print("⚠️ АУДИТ ВЫЯВИЛ ОШИБКИ, требующие внимания.")
        print("=====================================================================")

        return success

    def _audit_filenames(self):
        """Проверяет все файлы и папки репозитория на совместимость с Windows, macOS и Linux."""
        for root, dirs, files in os.walk(self.repo_root):
            # Пропускаем служебные директории
            rel_root = os.path.relpath(root, self.repo_root)
            parts = rel_root.split(os.sep)
            if any(p in {".git", ".idea", ".vscode", "__pycache__"} or p.startswith(".gemini") for p in parts):
                continue

            self.scanned_dirs_count += len(dirs)
            self.scanned_files_count += len(files)

            # 1. Проверка директорий
            for d in dirs:
                d_rel = os.path.join(rel_root, d) if rel_root != "." else d
                # Запрет точек и пробелов в конце
                if d.endswith(" ") or d.endswith("."):
                    self.filename_issues.append((d_rel, f"Имя директории оканчивается точкой или пробелом: {repr(d)}"))
                # Запрещенные символы
                bad = [c for c in d if c in WIN_FORBIDDEN_CHARS or ord(c) < 32]
                if bad:
                    self.filename_issues.append((d_rel, f"Директория содержит недопустимые для Windows символы {bad}: {repr(d)}"))
                # Зарезервированные имена
                base_name = os.path.splitext(d)[0].upper()
                if base_name in WIN_RESERVED_NAMES:
                    self.filename_issues.append((d_rel, f"Имя директории совпадает с зарезервированным именем устройства Windows: {repr(d)}"))

            # 2. Проверка файлов
            for f in files:
                f_rel = os.path.join(rel_root, f) if rel_root != "." else f
                if f.endswith(" ") or f.endswith("."):
                    self.filename_issues.append((f_rel, f"Имя файла оканчивается точкой или пробелом: {repr(f)}"))
                bad = [c for c in f if c in WIN_FORBIDDEN_CHARS or ord(c) < 32]
                if bad:
                    self.filename_issues.append((f_rel, f"Файл содержит недопустимые для Windows символы {bad}: {repr(f)}"))
                base_name = os.path.splitext(f)[0].upper()
                if base_name in WIN_RESERVED_NAMES:
                    self.filename_issues.append((f_rel, f"Имя файла совпадает с зарезервированным именем устройства Windows: {repr(f)}"))

            # 3. Проверка регистронезависимых коллизий в рамках одной директории
            lower_map = {}
            for name in dirs + files:
                low = name.lower()
                if low in lower_map:
                    col_rel = os.path.join(rel_root, name) if rel_root != "." else name
                    self.filename_issues.append((col_rel, f"Регистровый конфликт с {repr(lower_map[low])} на регистронезависимых ФС (Windows/macOS)"))
                else:
                    lower_map[low] = name

    def _audit_control_chars(self):
        """
        Ищет в sources/*.md управляющие символы. При редакторской переписке '\\text' уже
        превращался в TAB + 'ext', '\\approx' — в BEL + 'pprox' (U18). Ошибка:
        любой символ C0, кроме '\\n' и '\\t', и DEL; TAB — только внутри формулы вне кода.
        """
        sources_dir = os.path.join(self.repo_root, "sources")
        for root, _, files in os.walk(sources_dir):
            for f in sorted(files):
                if not f.endswith(".md"):
                    continue
                path = os.path.join(root, f)
                rel = os.path.relpath(path, self.repo_root)
                self.scanned_sources_count += 1
                # newline="" — иначе Python сам превратит CRLF в LF, и CR не найдётся
                with open(path, "r", encoding="utf-8", errors="replace", newline="") as fp:
                    text = fp.read()
                for k, ch in enumerate(text):
                    o = ord(ch)
                    if (o < 32 and ch not in "\n\t") or o == 127:
                        hint = " (переведите файл на LF)" if ch == "\r" else ""
                        self.control_char_issues.append(
                            (rel, text.count("\n", 0, k) + 1, f"управляющий символ {ch!r}{hint}"))
                if "\t" not in text or "$" not in text:
                    continue
                mask = code_mask(text)
                for a, b in formula_spans(text, mask):
                    for k in range(a, b):
                        if text[k] == "\t" and not mask[k]:
                            self.control_char_issues.append(
                                (rel, text.count("\n", 0, k) + 1,
                                 "TAB внутри формулы: …" + (text[max(a, k - 20):k] + "⟨TAB⟩" + text[k + 1:k + 12]).replace("\n", "⏎") + "…"))

    def _audit_single_page(self, page_path: str, file_ids_cache: Dict[str, Set[str]]):
        with open(page_path, "r", encoding="utf-8", errors="ignore") as fp:
            content = fp.read()

        # Извлекаем все id в текущем файле
        ids_in_page = set(re.findall(r'id=["\']([^"\']+)["\']', content))
        file_ids_cache[page_path] = ids_in_page

        # Проверяем ссылки <a href="...">
        hrefs = re.findall(r'<a\s+[^>]*href=["\']([^"\']+)["\']', content)
        page_dir = os.path.dirname(page_path)

        for href in hrefs:
            href_clean = href.strip()
            # Пропускаем внешние протоколы и javascript
            if href_clean.startswith(("http://", "https://", "mailto:", "javascript:", "tel:")):
                continue

            if href_clean.startswith("#"):
                # Анкор на текущей странице
                anchor = unquote(href_clean[1:])
                if anchor and anchor not in ids_in_page:
                    self.missing_anchors.append({
                        "source": page_path,
                        "raw_href": href_clean
                    })
                continue

            # Относительный путь к файлу
            parts = href_clean.split("#", 1)
            file_part = parts[0]
            anchor_part = parts[1] if len(parts) > 1 else ""

            target_file_path = os.path.normpath(os.path.join(page_dir, unquote(file_part)))
            if not os.path.exists(target_file_path):
                self.broken_links.append({
                    "source": page_path,
                    "target": target_file_path,
                    "raw_href": href_clean
                })
            elif anchor_part:
                # Проверим анкор в целевом файле
                if target_file_path not in file_ids_cache:
                    with open(target_file_path, "r", encoding="utf-8", errors="ignore") as tfp:
                        file_ids_cache[target_file_path] = set(re.findall(r'id=["\']([^"\']+)["\']', tfp.read()))
                
                target_ids = file_ids_cache[target_file_path]
                if unquote(anchor_part) not in target_ids:
                    self.missing_anchors.append({
                        "source": page_path,
                        "raw_href": href_clean
                    })

        # Проверяем блоки Mermaid
        mermaid_blocks = re.findall(r'<pre class="mermaid">(.*?)</pre>', content, re.DOTALL)
        for block_no, b in enumerate(mermaid_blocks, 1):
            clean_b = b.strip()
            if not clean_b:
                self.mermaid_errors.append({
                    "file": page_path,
                    "reason": "Пустой блок Mermaid"
                })
                continue

            if "Syntax error in text" in clean_b or "<svg" in clean_b:
                self.mermaid_errors.append({
                    "file": page_path,
                    "reason": "Блок Mermaid содержит остаточный SVG или текст ошибки"
                })
                continue

            # Проверка на типичные опечатки синтаксиса class (запятая вместо пробела перед именем класса)
            if re.search(r'^\s*class\s+[a-zA-Z0-9_-]+(?:,\s*[a-zA-Z0-9_-]+)*,\s*[a-zA-Z0-9_-]+\s*;', clean_b, re.MULTILINE):
                self.mermaid_errors.append({
                    "file": page_path,
                    "reason": "Опечатка синтаксиса class (запятая вместо пробела перед именем класса)"
                })
                continue

            # ":::class" внутри квотированной метки не падает при разборе, но выводится текстом
            # в узле: A["Текст:::entry"] вместо A["Текст"]:::entry
            unescaped_b = html.unescape(clean_b)
            if re.search(r':::\w+"\]', unescaped_b):
                self.mermaid_warnings.append({
                    "file": page_path,
                    "reason": f"Блок №{block_no}: ':::класс' внутри квотированной метки узла (будет выведен текстом)"
                })

            self.mermaid_blocks.append((page_path, block_no, unescaped_b))

            first_line = clean_b.splitlines()[0].strip()
            valid_headers = (
                "flowchart", "graph", "sequencediagram", "classdiagram",
                "statediagram", "statediagram-v2", "erdiagram", "gantt",
                "pie", "gitgraph", "c4context", "mindmap", "timeline",
                "xychart-beta", "block-beta"
            )
            
            header_cmd = first_line.split()[0].lower() if first_line.split() else ""
            if header_cmd not in valid_headers:
                self.mermaid_errors.append({
                    "file": page_path,
                    "reason": f"Неизвестный тип диаграммы Mermaid: \"{first_line[:40]}\""
                })

    @staticmethod
    def _find_browser() -> Optional[str]:
        """Путь к Firefox: переменная MERMAID_BROWSER, затем PATH."""
        env = os.environ.get("MERMAID_BROWSER")
        if env:
            return env if os.path.exists(env) or shutil.which(env) else None
        return shutil.which("firefox")

    def _mermaid_js_path(self) -> Optional[str]:
        """Вендорный Mermaid: сначала копия из dist, затем из engine/assets."""
        candidates = [
            os.path.join(self.dist_dir, "assets", "vendor", "mermaid.min.js"),
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "vendor", "mermaid.min.js"),
        ]
        return next((c for c in candidates if os.path.exists(c)), None)

    def _audit_mermaid_runtime(self):
        """
        Прогоняет каждый блок через mermaid.parse() в headless Firefox (тот же вендорный
        mermaid.min.js, что и на сайте). Результаты возвращаются в Python через
        Image-маячки на временный локальный HTTP-сервер: headless Firefox не умеет
        печатать DOM. Если браузер недоступен, проверка пропускается с предупреждением.
        """
        print(f"      🧪 Рантайм-разбор диаграмм Mermaid: {len(self.mermaid_blocks)} блоков...")
        if not self.mermaid_blocks:
            return
        browser = self._find_browser()
        mermaid_js = self._mermaid_js_path()
        if not browser or not mermaid_js:
            print("      ⚠️ Пропущено: не найден Firefox (PATH или MERMAID_BROWSER) или mermaid.min.js. "
                  "Установите Firefox либо отключите проверку флагом --no-mermaid-runtime.")
            return

        failures: Dict[int, str] = {}
        done = threading.Event()
        total_reported = {"n": -1}

        class Handler(http.server.BaseHTTPRequestHandler):
            def do_GET(self):
                q = parse_qs(urlparse(self.path).query)
                if "i" in q:
                    failures[int(q["i"][0])] = q.get("m", [""])[0]
                if "done" in q:
                    total_reported["n"] = int(q["done"][0])
                    done.set()
                self.send_response(204)
                self.end_headers()

            def log_message(self, *args):
                pass

        server = http.server.HTTPServer(("127.0.0.1", 0), Handler)
        port = server.server_address[1]
        threading.Thread(target=server.serve_forever, daemon=True).start()

        slim = [{"i": i, "c": code} for i, (_, _, code) in enumerate(self.mermaid_blocks)]
        # "</" внутри <script> преждевременно закрыл бы тег
        blocks_json = json.dumps(slim, ensure_ascii=False).replace("</", "<\\/")
        page = (
            '<!doctype html><meta charset="utf-8"><body>'
            f'<script src="{os.path.abspath(mermaid_js)}"></script><script>\n'
            f'const blocks = {blocks_json};\n'
            f'const PORT = {port};\n'
            "function send(q){return new Promise(r=>{const im=new Image();"
            "im.onload=im.onerror=()=>r();im.src='http://127.0.0.1:'+PORT+'/r?'+q;});}\n"
            "(async()=>{ mermaid.initialize({startOnLoad:false});\n"
            " for(const b of blocks){ try{ await mermaid.parse(b.c); } catch(e){\n"
            "   await send('i='+b.i+'&m='+encodeURIComponent(String(e.message||e).split('\\n').slice(0,3).join(' | ').slice(0,240))); } }\n"
            " await send('done='+blocks.length); })();\n"
            "</script>"
        )

        proc = None
        try:
            with tempfile.TemporaryDirectory(prefix="audit-mermaid-") as tmp:
                page_path = os.path.join(tmp, "mermaid_runtime.html")
                with open(page_path, "w", encoding="utf-8") as fh:
                    fh.write(page)
                profile = os.path.join(tmp, "profile")
                os.makedirs(profile)
                proc = subprocess.Popen(
                    [browser, "--headless", "--no-remote", "--profile", profile,
                     "file://" + page_path],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                )
                finished = done.wait(MERMAID_RUNTIME_TIMEOUT)
        except OSError as e:
            print(f"      ⚠️ Не удалось запустить браузер: {e}. Рантайм-разбор пропущен.")
            server.shutdown()
            return
        finally:
            if proc is not None:
                proc.terminate()
                try:
                    proc.wait(10)
                except subprocess.TimeoutExpired:
                    proc.kill()
            server.shutdown()

        if not finished:
            self.mermaid_errors.append({
                "file": self.dist_dir,
                "reason": f"Рантайм-разбор Mermaid не завершился за {MERMAID_RUNTIME_TIMEOUT} с"
            })
            return

        for i in sorted(failures):
            page_path, block_no, code = self.mermaid_blocks[i]
            first = failures[i].replace("\n", " ")
            self.mermaid_errors.append({
                "file": page_path,
                "reason": f"Блок №{block_no}: Mermaid не разбирает диаграмму ({first[:200]})"
            })
        print(f"      Рантайм-разбор завершён, не разобраны: {len(failures)}")


def main():
    parser = argparse.ArgumentParser(description="Аудитор сгенерированного сайта и совместимости имен файлов")
    parser.add_argument("--dist", default="./dist", help="Путь к скомпилированному сайту")
    parser.add_argument("--repo-root", default=".", help="Корень репозитория для проверки имен файлов")
    parser.add_argument("--no-mermaid-runtime", action="store_true",
                        help="Не запускать рантайм-разбор диаграмм Mermaid в headless Firefox")
    args = parser.parse_args()

    auditor = SiteAuditor(args.dist, args.repo_root, mermaid_runtime=not args.no_mermaid_runtime)
    success = auditor.run_audit()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
