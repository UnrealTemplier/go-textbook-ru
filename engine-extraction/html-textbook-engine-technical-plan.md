# Технический план: задача А (движок `html-textbook-engine`)

> **Основание:** `html-engine-extracting-analysis-final.md` (дальше — «анализ»). План раскладывает этапы А0–А5 на коммиты: какие файлы, что делаем, как проверяем. Решения здесь не меняются. Если при работе выясняется, что решение анализа неисполнимо, работа останавливается, а вопрос уходит владельцу через раздел «Изменения решений» дорожной карты.
> **Статус работ:** `html-textbook-engine-extraction-roadmap.md`.
> **Дата:** 2026-10-09. Трек Б пока не планируется (решение владельца: трек А приоритетен).

---

## 0. Общие правила исполнения

1. **Один коммит — одно изменение.** Пересборка `dist/` — отдельным коммитом `chore(dist): rebuild site`, только если `dist/` изменился.
2. **После каждого коммита с кодом:**
   * `python -m unittest discover <пакет>/tests` — зелёный;
   * полная сборка в чистый каталог `/tmp/…/dist-new`;
   * `verify_diff.py <эталон> <dist-new> …` с ожидаемым результатом этапа;
   * аудит (`audit_all.py`, после А1 — `python -m engine.audit`) — 0 ошибок, включая рантайм Mermaid.
3. **Эталон** — `dist/` предыдущего шага. Для А0–А2 это `dist/` коммита `bbb4b1f7`.
4. **Рабочие файлы проверок** (временные сборки, отчёты) — во временном каталоге сессии, не в репозитории.
5. **Документация** (`AGENTS.md`, `README.md`) обновляется в том же коммите, что и код, который она описывает.
6. **Дорожная карта** отмечается после каждого завершённого этапа (`docs(engine-extraction): …`).

---

## 1. Раскладка файлов по этапам

| Что | До А1 | С А1 |
|---|---|---|
| генератор | `builder/` | `engine/` (`python -m engine.build`) |
| тесты ядра | `builder/tests/` | `engine/tests/` |
| инструменты проверки | `builder/tools/` (`verify_diff.py`, `runtime_projection.py`) | `engine/tools/` |
| книжные тесты (корпус `go-textbook`) | `builder/tests/` с пометкой `book_` | `book/tests/` |
| книжные инструменты (`verify_editorial.py`) | `builder/` | `book/tools/` |
| конфиг книги | — | `book.toml` (корень) |
| слой книги | — | `book/` (`assets/`, `overrides/`, `hooks.py`, `tests/`, `tools/`) |
| зависимости | — | `requirements.txt` (корень, с А0) |
| эталон рантайм-проекции | — | `engine-extraction/baseline/runtime-bbb4b1f7.json` (с А0) |
| исторический `batch_runner.py` | `builder/` | удаляется в А1 (запуск запрещён `AGENTS.md`, зависимостей нет) |

Корень репозитория после А1: `sources/`, `engine/`, `book/`, `book.toml`, `dist/`, `fact-checks/`, `engine-extraction/`, `.github/`, `AGENTS.md`, `README.md`, `requirements.txt`, `favicon.ico`, `favicon.svg`, `.gitignore`. Список разрешённых имён в `AGENTS.md` § 2 обновляется в коммите, который добавляет имя.

---

## 2. А0. Страховочная сетка

Ни одного изменения вывода. Все коммиты — `test(...)`/`feat(tools)`.

| № | Коммит | Содержание |
|---|---|---|
| А0.1 | `chore: pin markdown dependency` | `requirements.txt`: `markdown>=3.10,<3.11`; `AGENTS.md` § 1.3, § 2 |
| А0.2 | `test(builder): add characterization tests` | `builder/tests/`: `test_slugify.py` (выборка реальных названий и якорей корпуса + граничные случаи: пусто, только знаки, ё, длины 20/25/35/55/60/80), `test_callouts.py` (8 типов, неизвестный тип → `note`, interview-эвристика, пустая строка внутри выноски, выноска в конце файла), `test_wikilinks.py` (`[[X]]`, `[[X\|Y]]`, `[[X#якорь]]`, `C#` в названии, ненайденная цель, `#якорь` без статьи), `test_clean_cliches.py` (5 шаблонов, регистр), `test_headings.py` (TOC, ограды, экранирование хвоста `#` в H1/H5/H6), `test_katex_config.py` (значения `main.js:831–838` заморожены), `test_version.py` (одна строка, ноль, две, не SemVer). Книжный тест `test_book_corpus.py`: для всех 1 413 статей `convert_article` даёт байты из эталонного `dist/` внутри `.article-markdown` (защищает от случайного изменения конвертера); санитайзер на всех 2 486 диаграммах корпуса = зафиксированный снимок (хэш) |
| А0.3 | `feat(tools): add verify_diff` | `builder/tools/verify_diff.py`: режимы `--full` (как `diff -r`, список файлов), `--article` (побайтное сравнение `<article class="article-body">` после нормализаторов), `--normalizers a,b,c`, `--exceptions FILE --stage А3x`; нормализаторы `whitespace_between_tags`, `code_chrome`, `strip_sidebar`, `strip_conditional_scripts`, `strip_asset_query`, `map_dedup_ids` (таблица из файла); функции проекций: `text_projection(html)` (текст с маркерами пунктов, номерами `<ol>`, маркерами `<em>/<strong>`), `heading_visible_texts(html)` (через `html.parser`), `block_in_p(html)` (блочные элементы внутри `<p>`), `code_blocks_multiset(html)`. Юнит-тесты на синтетике |
| А0.4 | `feat(tools): add runtime projection` | `builder/tools/runtime_projection.py`: N параллельных headless Firefox (по умолчанию 8 профилей), каждая обходит свою часть страниц цепочкой; на странице ждёт готовности (все `pre.mermaid` с SVG или ошибкой, но не дольше 8 с), считает `.katex`, `.katex-display`, `.katex-error`, `pre.mermaid svg`, `Syntax error in text`, JS-ошибки. Результат — JSON. Сравнение двух JSON с поддержкой ожидаемых различий. Замер времени |
| А0.5 | `feat(builder): add code line mask` | `builder/code_mask.py` (`find_list_context`, `scan_indented_fences`, `UnifiedCodeLineMask`) по Приложению А.1 анализа; в сборке не используется; `test_code_mask.py`: синтетика + свойство-тест на корпусе (блоки маски = `<pre><code>` того же `md` для текста статьи на шаге 4 и для каждого тела выноски, `include_indented=False`) |
| А0.6 | `chore(engine-extraction): add runtime baseline` | прогон проекции по `dist/` `bbb4b1f7` → `engine-extraction/baseline/runtime-bbb4b1f7.json`; повторный прогон даёт тот же JSON |

**Критерий А0:** тесты зелёные; `verify_diff.py --full dist dist` пуст; `verify_diff.py --full dist <свежая сборка>` пуст; рантайм-проекция воспроизводима (два прогона равны).

---

## 3. А1. Выделение на месте

Вывод побайтно не меняется: `verify_diff.py --full <эталон> <новая сборка>` пуст **целиком**.

| № | Коммит | Содержание |
|---|---|---|
| А1.1 | `refactor: move builder to engine package` | `git mv builder engine`; относительные импорты; `engine/build.py` (бывший `build_all.py`) с `main()`, `python -m engine.build`; `engine/audit.py` (бывший `audit_all.py`), `python -m engine.audit`; удалить `batch_runner.py`; `verify_editorial.py` → `book/tools/`; книжные тесты → `book/tests/`; убрать `sys.path`-хак. `AGENTS.md`, `README.md`: все команды и пути |
| А1.2 | `feat(engine): load book.toml` | `engine/config.py`: `tomllib` + `dataclasses`, неизвестный ключ — ошибка, поиск `book.toml` от текущего каталога или `--book`; `book.toml` `go-textbook` с текущими значениями (анализ § 4.4): проект, версия из `AGENTS.md` (`version_file` + `version_pattern`), `storage_prefix`, длины slug, `canonical_replacements` (30 правил, порядок), `clean_cliches` (5 шаблонов), выноски (типы, алиасы — пусто, `interview_heuristic = true`), KaTeX, `reading_time`; `test_config.py`. Код читает значения из конфига, а не из констант |
| А1.3 | `refactor(engine): move book texts to book.toml` | тексты шаблонов, специфичные для книги: заголовок и подзаголовок, hero, цитата Кернигана, статистика, дорожная карта главной (4 шага), подписи футеров, плейсхолдер поиска, `description`, `<title>`-суффикс, логотип Go (`book/assets/logo-go.svg`, читается как текст), числа «22» (считаются из дерева); фавиконки — путь из конфига |

**Критерий А1:** пустой `diff -r`; `sources/` не изменён; аудит чистый; тесты зелёные.

---

## 4. А2. Обобщение ядра без изменения вывода

| № | Коммит | Содержание |
|---|---|---|
| А2.1 | `feat(engine): add UI strings dictionary` | `engine/strings/ru.toml` — все общие строки интерфейса из `template.py`, `converter.py` (заголовки выносок по умолчанию, «Скопировать», «Архитектурная схема», навигация, TOC) и `main.js` (тексты, которые JS вставляет: «Скопировано!», подписи темы); `[strings]` в `book.toml` переопределяет; неизвестный ключ — ошибка. Строки `main.js` передаются через `data-`атрибуты или остаются в JS до А3ж (решение — в коммите, с обоснованием; вывод не меняется) |
| А2.2 | `feat(engine): recursive content scanner` | дерево узлов произвольной глубины; ошибки сборки (анализ § 4.5 п. 2); пути и slug `go-textbook` прежние; `title_source`; удаление первого H1 при `h1`; `index_file` (U22) с заглавными страницами, списком дочерних страниц, `is_index`, пагинацией и счётчиком задач — на демо-книге; `test_scanner.py` на временных деревьях |
| А2.3 | `feat(engine): add disabled markdown extensions` | `engine/converter/` как пакет: `IndentedFencePreprocessor`, препроцессор списков (`obsidian_lists.py`, по правилам анализа § 4.7.4), `MathProtectExtension`, `HeadingTreeprocessor`, `CalloutExtractor`; флаги `[markdown]`, `[math].protect` выключены; конфигурационные ошибки; `test_indented_fence.py` (18 входов, со списками), `test_math.py`, `test_headings.py` (treeprocessor) |
| А2.4 | `feat(engine): add overrides, hooks and versioning` | `book/overrides/` (частичные шаблоны `sidebar_header`, `article_header`, `index_hero`, `footer`), `book/assets/extra.css|js`, `book/hooks.py` (реестр хуков), `engine/VERSION` = `1.2.0-dev`, `engine/CHANGELOG.md`, генерация и проверка `engine/.checksums.json` |
| А2.5 | `feat(engine): add demo book` | `demo-sources/` + `demo/book.toml` (значения по умолчанию для новых книг, `index_file`, `title_source = "h1"`, оба препроцессора и защита формул включены); golden-тест сборки демо |
| А2.6 | `feat(engine): wikilinks switch, callout aliases, overlays` | `wikilinks = false`; алиасы и предупреждения неизвестных выносок, `--strict`; оверлеи (только данные и проверка, отображение — для `go-workout` позже) |

**Критерий А2:** пустой `diff -r` для `go-textbook`; демо собирается и проходит аудит; тесты зелёные.

---

## 5. А3. Санкционированные изменения

Порядок и оракулы — анализ § 6.4. Для каждого коммита: код → тесты → сборка → `verify_diff.py` с нормализаторами и исключениями этапа → рантайм-проекция против предыдущего эталона → аудит → `content-exceptions.txt` (строки этапа) → коммит → `chore(dist)` → новый эталон.

| Коммит | Ключевые действия в коде | Проверка (кроме общих) |
|---|---|---|
| А3а | маска на шаге 1 и 4 (`include_indented = indented_fences = false`) | `<pre>` отличаются ровно на 5 страницах U10 |
| А3а′ | `CalloutExtractor` в конвейере; рекурсия wikilinks; U20 в inline-коде | после `whitespace_between_tags` — только 38 + 6 страниц; `<pre>` побайтно равны |
| А3б | гибридный сайдбар, `nav-data.js` (`<script defer>`), гидрация в `main.js`, счётчик статей из `nav-data.js` | `strip_sidebar`; браузер: фильтр, раскрытие модулей, без JS виден текущий модуль |
| А3в | условная загрузка: Mermaid по `pre.mermaid`, KaTeX по формулам вне кода (правило = `auto-render`), Prism по блокам кода | рантайм-проекция постранично равна |
| А3г | `<svg><symbol>` на странице + `<use href>` в шапке кода | `code_chrome`; Firefox и **Chromium** по `file://` (Chromium нужен — см. § 8) |
| А3д | дедупликация `id` (`-2`, `-3`), TOC на новые `id` | `map_dedup_ids`; аудит дублей `id` = 0 |
| А3е | `HeadingTreeprocessor` + экранирование хвоста `#` в H2–H4 | видимый текст заголовков = старый без парных `` `…` ``/`**…**`; `id` = TOC |
| А3ж | `window.__BOOK__` (тема), `?v=` по sha256 из `dist/`, guard в `DOMContentLoaded` | `test_runtime.py` (7 сценариев анализа § 4.9), `strip_asset_query` |
| А3и | `protect = ["\\(", "\\["]` | ровно 1 страница |
| А3к | удаление точных дублей H1 (по исходному тексту) + генератор реестра 236 пар | 60 страниц (по инструменту), реестр создан |
| А3м | модальное окно только на страницах с диаграммами | браузер: окно открывается, масштаб, закрытие |
| `fix(sources)` U23 | только если оракул А3л найдёт места класса (5) | владелец видит каждое место |
| А3л | `obsidian_lists = true` | 5 классов, тексты `<pre><code>` не меняются |
| А3з | `indented_fences = true`, регулярка языка `[\w#.+-]+` в `_enhance_code_blocks` | оракул анализа § 6.4 (0 блоков в `<p>`, 222 из 222 в своём `<li>`) |

А3л и А3з пушатся вместе (локально коммиты по одному; в этом репозитории push делает владелец).

---

## 6. А4. QA-харденинг

`engine/audit.py`: длина путей, дубли `id`, Offline Guard (`src`, `href`, `srcset`, `<source>`, `<iframe>`, CSS `url(`/`@import`), существование ассетов, `audit-baseline.json` для мёртвых wikilinks (`go-textbook`: 355), рантайм KaTeX (`.katex-error` не растёт относительно эталона), `--strict`, `extra_audit_checks`. Тесты на синтетических `dist/`.

---

## 7. А5. Публикация ядра

1. Создать `/home/ut/work/html-textbook-engine` (git init): `engine/`, `book/` (пример), `demo-sources/`, `book.toml` (демо), `requirements.txt`, `README.md`, `templates/ci/` (два workflow), `.gitignore`.
2. `engine/sync.py`: `--from <путь|git-URL|tarball>`, проверка `.checksums.json`, атомарная замена, удаление лишних файлов, обновление `VERSION`, один коммит.
3. `engine/VERSION = 1.2.0`, `CHANGELOG.md`.
4. В `go-textbook`: `python -m engine.sync --from /home/ut/work/html-textbook-engine` → `dist/` побайтно равен прежнему.
5. Удалённый репозиторий (GitHub) не создаётся без команды владельца.

---

## 8. Ресурсы и риски исполнения

| Что | Где нужно | Состояние |
|---|---|---|
| Chromium | А3г (проверка `<symbol>` по `file://`) | **не установлен**; к А3г нужен `sudo dnf install chromium` (владелец) |
| Firefox | А0.4, все рантайм-проверки | есть (157) |
| Время рантайм-проекции | каждый коммит А3 | замер в А0.4; при > 5 мин — проекция только по изменённым страницам + выборка |
| `localStorage` в тестах | `test_runtime.py` | в Firefox у каждого `file://`-файла своё хранилище: сценарии с сохранённой темой — перезагрузкой той же страницы |
