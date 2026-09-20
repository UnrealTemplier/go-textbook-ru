# 📋 ПЛАН ПЕРЕПИСЫВАНИЯ МОДУЛЯ 22 — «Вопросы и ответы с собеседований по Go (Теория)»

> **Версия:** 1.0  
> **Дата:** 2026-09-20  
> **Статус:** Утверждён, ожидает исполнения  
> **Связанный файл:** `MODULE22_NEW_QUESTIONS.md` — список новых вопросов по Go 1.22–1.27

---

## 🔴 КРИТИЧЕСКИ ВАЖНО: Прочитай перед началом работы

1. **Прочитай файл `AGENTS.md`** в корне проекта — это единый источник правды. Все стандарты стиля, цветовой палитры диаграмм, правила callout'ов и типографики описаны там.
2. **Железное правило границ:** Выполняй ровно один этап за раз. Достигнув конца этапа — **СТОП**. Зафиксируй изменения коммитом, доложи и жди дальнейших указаний пользователя.
3. **Политика нулевой потери знаний (AGENTS.md §3):** При переписывании ЗАПРЕЩЕНО удалять техническую фактуру: вопросы, ответы, код, термины, подводные камни, перекрёстные ссылки `[[...]]`. Переписывание должно *увеличивать* глубину, а не сокращать.
4. **Сборка и проверка:** После каждого этапа обязательно:
   ```bash
   python3 builder/build_all.py --all    # полная пересборка (~14 сек)
   python3 builder/audit_all.py          # QA: ошибки файлов, Mermaid, ссылки
   ```
   308 anchor warnings — известная норма, НЕ являются ошибками.
5. **Коммит после каждого этапа:**
   ```bash
   git add -A && git commit -m "refactor(module22): этап N — <краткое описание>"
   ```

---

## 📊 Текущее состояние модуля (аудит на 2026-09-20)

```
sources/22. Вопросы и ответы с собеседований по Go (Теория)/
├── 01. Введение и стратегия подготовки.md   (2322 строки, ~300 КБ)
├── 02. Основы Go. База.md                   (1812 строк,  ~244 КБ)
├── 03. Типы данных, slice, map, string.md
├── 04. Функции, методы, интерфейсы.md
├── 05. Ошибки, defer, panic recover.md
├── 06. Память. Stack, Heap, Escape Analysis.md
├── 07. Runtime Go. Общая архитектура.md
├── 08. Сборщик мусора GC.md                 (1641 строка, ~212 КБ)
├── 09. Планировщик и GMP модель.md
├── 10. Горутины и базовая конкурентность.md
├── 11. Каналы и синхронизация.md
├── 12. Продвинутая конкурентность.md
├── 13. Memory Model и happens before.md
├── 14. Производительность и оптимизация.md
├── 15. Профилирование и отладка.md
├── 16. Стандартная библиотека.md
├── 17. HTTP и сетевое взаимодействие.md
├── 18. Базы данных. Теория.md
├── 19. Базы данных в Go.md
├── 20. Очереди и брокеры.md
├── 21. System Design. База.md
├── 22. System Design. Highload и FinTech.md
├── 23. Linux и ОС.md
├── 24. Безопасность.md
├── 25. Практические задачи.md
├── 26. Поведенческие и архитектурные вопросы.md
├── 27. Вопросы уровня Senior и Staff.md
└── 28. Финальный чеклист.md
```

**Итого: 28 файлов, ~6.36 МБ, 0 диаграмм Mermaid**

### Выявленные проблемы

| Проблема | Критичность | Масштаб |
|---|---|---|
| ❌ **Нет ни одной диаграммы Mermaid** | 🔴 Критическая | 28 файлов |
| ❌ **Нет эпиграфов** (Кернигановский стандарт) | 🔴 Критическая | 28 файлов |
| ❌ **Нет вопросов по Go 1.22–1.27** | 🔴 Критическая | 12 файлов |
| ⚠️ **Callout-блоки** не используются `[!INTERVIEW]` | 🟡 Важная | 28 файлов |
| ⚠️ **Инженерные аналогии** отсутствуют (Кернигановский стиль) | 🟡 Важная | 28 файлов |
| ℹ️ **Нет таблиц сравнения** версий Go | 🔵 Желательная | 12 файлов |

---

## 🎯 Цели рефакторинга

1. **Добавить диаграммы Mermaid** в каждый файл (минимум 1–3 на лекцию) согласно семантической палитре AGENTS.md §2.5.
2. **Добавить эпиграфы** в Кернигановском формате в каждый файл.
3. **Интегрировать новые вопросы** по Go 1.22–1.27 (31 вопрос из `MODULE22_NEW_QUESTIONS.md`) в соответствующие лекции.
4. **Обогатить Callout-блоки:** обернуть вопросы для собеседований в `[!INTERVIEW]`, предупреждения — в `[!WARNING]`, советы — в `[!TIP]`.
5. **Добавить инженерные аналогии** (Mechanical Sympathy, физические модели) согласно §2.2.
6. **Актуализировать технические данные** до Go 1.27 (август 2026).

---

## 🗺️ Разбивка по этапам

Модуль разделён на 6 тематических этапов по 4–5 файлов, сгруппированных по смысловой близости:

| Этап | Файлы | Тема | Диаграмм (план) |
|---|---|---|---|
| **Этап 0** | 01 | Введение, стратегия, новые вопросы по версиям | 2 |
| **Этап 1** | 02–05 | Язык Go: основы, типы, функции, ошибки | 8–12 |
| **Этап 2** | 06–09 | Память, Runtime, GC, Планировщик | 12–16 |
| **Этап 3** | 10–13 | Конкурентность, каналы, Memory Model | 10–14 |
| **Этап 4** | 14–17 | Производительность, профилирование, stdlib, HTTP | 8–12 |
| **Этап 5** | 18–22 | БД, очереди, System Design | 8–10 |
| **Этап 6** | 23–28 | Linux, безопасность, практика, Senior, чеклист | 8–12 |

**Целевое количество диаграмм Mermaid: 56–76 (минимум 2 на файл)**

---

## 🛠️ ЭТАП 0 — Файл 01: Введение и стратегия подготовки

> **Приоритет:** 🔴 Высокий. Первый файл — лицо модуля.  
> **Файлов:** 1 (`01. Введение и стратегия подготовки.md`)  
> **Ожидаемое время:** 30–40 минут

### Задачи этапа 0:

- [x] **Эпиграф** (цитата Роба Пайка о собеседованиях/подготовке, на русском)
- [x] **Mermaid-диаграмма 1:** Roadmap подготовки к Go-собеседованию (flowchart с этапами: Junior → Middle → Senior → Staff)
- [x] **Mermaid-диаграмма 2:** Карта тем (mindmap-стиль через flowchart) — все 28 лекций с группировкой по блокам
- [x] **Callout `[!IMPORTANT]`:** ключевые советы по стратегии подготовки
- [x] **Новая секция:** «Что нового в Go 1.22–1.27» — краткая таблица актуальных фич, важных для собеседований
- [x] **Callout `[!TIP]`:** список наиболее частых вопросов на Go-интервью в 2025–2026

### Критерии приёмки этапа 0:
- [x] `python3 builder/build_all.py --all` → exit 0
- [x] `python3 builder/audit_all.py` → 0 errors
- [x] Файл содержит эпиграф в каноническом формате
- [x] Файл содержит минимум 2 Mermaid-диаграммы с цветами согласно §2.5
- [x] Коммит: `refactor(module22): этап 0 — введение, roadmap, таблица версий Go`

---

## 🛠️ ЭТАП 1 — Файлы 02–05: Основы языка

> **Приоритет:** 🔴 Высокий.  
> **Файлов:** 4  
> **Ожидаемое время:** 2–3 часа

### Файл 02: Основы Go. База

**Новые вопросы из MODULE22_NEW_QUESTIONS.md:** Q01, Q02, Q03, Q20

- [x] **Эпиграф** (Кен Томпсон или Роб Пайк — о простоте Go)
- [x] **Mermaid:** Жизненный цикл переменной Go (scope, zero value, escape)
- [x] **Mermaid:** Процесс компиляции Go (front-end → SSA → machine code)
- [x] **Callout `[!INTERVIEW]`:** на вопросах `iota`, `init()`, `_`
- [x] Интегрировать: Q01 (range over integers), Q02 (loop variable capture fix), Q03 (math/rand/v2), Q20 (new(expr)), Q05, Q06
- [x] **Таблица сравнения:** новые синтаксические возможности Go 1.22–1.27

### Файл 03: Типы данных, slice, map, string

**Новые вопросы:** Q07 (unique), Q09 (Swiss Tables)

- [x] **Эпиграф** (о структурах данных — Кнут)
- [x] **Mermaid:** Внутреннее устройство slice header (ptr + len + cap)
- [x] **Mermaid:** Swiss Tables vs классический map (сравнение структур)
- [x] **Mermaid:** string internals — immutable byte array + len
- [x] **Callout `[!WARNING]`:** ловушки при append со скрытой ёмкостью
- [x] Интегрировать: Q09 (Swiss Tables map), Q07 (unique.Handle)
- [x] ASCII-схема: раскладка slice в памяти (64-байтные cache lines)

### Файл 04: Функции, методы, интерфейсы

**Новые вопросы:** Q10 (generic type aliases), Q21 (self-referential generics), Q26 (generic methods), Q27 (generalized type inference)

- [x] **Эпиграф** (Роб Пайк о интерфейсах и утиной типизации)
- [x] **Mermaid:** Устройство iface (itab + data pointer)
- [x] **Mermaid:** Method set rules (value vs pointer receiver)
- [x] **Mermaid:** Generic type inference flowchart (Go 1.18 → 1.24 → 1.27)
- [x] Интегрировать: Q10, Q21, Q26, Q27 — блок «Generics на собеседовании: от 1.18 до 1.27»
- [x] **Callout `[!INTERVIEW]`:** «Почему Go не поддерживает generic methods в интерфейсах?»

### Файл 05: Ошибки, defer, panic, recover

- [x] **Эпиграф** (о явной обработке ошибок)
- [x] **Mermaid:** Порядок выполнения defer (LIFO stack)
- [x] **Mermaid:** Механизм panic/recover (unwind + recover capture)
- [x] **Mermaid:** Дерево паттернов обработки ошибок (sentinel, typed, wrapping, errors.Is/As)
- [x] **Callout `[!WARNING]`:** defer в цикле — классическая ловушка
- [x] **Callout `[!INTERVIEW]`:** «Что напечатает этот код с panic в defer?»

### Критерии приёмки этапа 1:
- [x] `python3 builder/build_all.py --all` → exit 0
- [x] `python3 builder/audit_all.py` → 0 errors (308 warnings — норма)
- [x] Каждый файл содержит эпиграф + минимум 2 Mermaid-диаграммы с цветами
- [x] Все новые вопросы (Q01, Q02, Q03, Q05, Q06, Q07, Q09, Q10, Q20, Q21, Q26, Q27) интегрированы
- [x] Коммит: `refactor(module22): этап 1 — основы языка (файлы 02–05)`

---

## 🛠️ ЭТАП 2 — Файлы 06–09: Память, Runtime, GC, Планировщик

> **Приоритет:** 🔴 Критически важный блок — чаще всего спрашивают на Senior интервью.  
> **Файлов:** 4  
> **Ожидаемое время:** 3–4 часа

### Файл 06: Память. Stack, Heap, Escape Analysis

**Новые вопросы:** Q11 (weak.Pointer)

- [x] **Эпиграф** (о модели памяти — Ритчи или Кернигановский)
- [x] **Mermaid:** Stack vs Heap — решение escape analysis (flowchart)
- [x] **Mermaid:** Goroutine stack growth (segmented → contiguous, копирование)
- [x] **Mermaid:** Слабые ссылки `weak.Pointer` — жизненный цикл с GC
- [x] ASCII-схема: структура виртуального адресного пространства процесса Go
- [x] **Callout `[!TIP]`:** как читать `go build -gcflags="-m"` — escape analysis output
- [x] Интегрировать: Q11 (weak.Pointer — новый тип Go 1.24)

### Файл 07: Runtime Go. Общая архитектура

- [x] **Эпиграф** (о рантайм-системах)
- [x] **Mermaid:** Архитектура рантайма Go (G, M, P + netpoller + GC goroutines)
- [x] **Mermaid:** Инициализация рантайма (m0, g0, schedinit sequence)
- [x] **Callout `[!NOTE]`:** Как рантайм встроен в бинарник (static linking)
- [x] Таблица: компоненты рантайма и их файлы в `src/runtime/`

### Файл 08: Сборщик мусора GC

**Новые вопросы:** Q17 (экспериментальный GC 1.25), Q22 (Green Tea GC 1.26), Q28 (size-specialized allocation 1.27)

- [x] **Эпиграф** (о сборке мусора — автоматизация vs контроль)
- [x] **Mermaid:** Фазы GC-цикла (mark setup STW → concurrent mark → mark termination STW → sweep)
- [x] **Mermaid:** Tri-color marking — переходы состояний (белый → серый → чёрный)
- [x] **Mermaid:** Эволюция GC Go: от Go 1.0 до 1.27 (timeline)
- [x] **Mermaid:** Green Tea GC vs классический — сравнение path для малых объектов
- [x] ASCII-схема: mspan структура в куче (page → mspan → mcache → mcentral → mheap)
- [x] **Callout `[!INTERVIEW]`:** «Объясните tri-color invariant за 60 секунд»
- [x] **Callout `[!WARNING]`:** когда GOMEMLIMIT может вызвать GC thrashing
- [x] Интегрировать: Q17, Q22, Q28 — блок «Эволюция GC в 2024–2026»
- [x] **Таблица:** Параметры настройки GC (GOGC, GOMEMLIMIT, GODEBUG=gctrace) с примерами

### Файл 09: Планировщик и GMP модель

**Новые вопросы:** Q18 (Container-aware GOMAXPROCS)

- [x] **Эпиграф** (о многозадачности и кооперативности)
- [x] **Mermaid:** GMP модель — состояния и переходы горутины (runnable → running → waiting → dead)
- [x] **Mermaid:** Work stealing алгоритм (локальная очередь → steal → global queue)
- [x] **Mermaid:** Syscall handling (handoff P, netpoller integration)
- [x] **Callout `[!TIP]`:** GOMAXPROCS tuning — контейнеры vs bare metal
- [x] Интегрировать: Q18 (Container-aware GOMAXPROCS, cgroups v2)
- [x] **Физическая аналогия:** Механическое сочувствие — P как станки ЧПУ, G как задания, M как рабочие

### Критерии приёмки этапа 2:
- [x] `python3 builder/build_all.py --all` → exit 0
- [x] `python3 builder/audit_all.py` → 0 errors
- [x] Каждый файл: эпиграф + минимум 2 Mermaid с цветами
- [x] Все новые вопросы Q11, Q17, Q18, Q22, Q28 интегрированы
- [x] Коммит: `refactor(module22): этап 2 — память, Runtime, GC, планировщик (файлы 06–09)`

---

## 🛠️ ЭТАП 3 — Файлы 10–13: Конкурентность и Memory Model

> **Приоритет:** 🔴 Высокий — конкурентность — главная тема Go-интервью.  
> **Файлов:** 4  
> **Ожидаемое время:** 2–3 часа

### Файл 10: Горутины и базовая конкурентность

- [x] **Эпиграф** (Хоар о CSP и «Communicating Sequential Processes»)
- [x] **Mermaid:** Создание горутины — стековый фрейм (g struct, 2KB начальный стек)
- [x] **Mermaid:** Паттерн «fan-out / fan-in» — диаграмма потоков данных
- [x] **Callout `[!INTERVIEW]`:** «Сколько горутин можно запустить? Что ограничивает?»
- [x] **Callout `[!WARNING]`:** goroutine leak — типичные причины и диагностика

### Файл 11: Каналы и синхронизация

**Новые вопросы:** Q08 (time.Timer/Ticker изменения в 1.23)

- [x] **Эпиграф** (Роб Пайк: «Don't communicate by sharing memory; share memory by communicating»)
- [x] **Mermaid:** Внутреннее устройство hchan (buf, sendx, recvx, sendq, recvq)
- [x] **Mermaid:** Select statement — алгоритм выбора готового case (pseudorandom)
- [x] **Mermaid:** sync.Mutex — состояния (unlocked → locked → starving mode)
- [x] **Callout `[!INTERVIEW]`:** «Чем буферизованный канал отличается от небуферизованного?»
- [x] Интегрировать: Q08 (time.Timer Reset() семантика в Go 1.23)
- [x] **Callout `[!WARNING]`:** паттерны deadlock с каналами — примеры кода

### Файл 12: Продвинутая конкурентность

- [x] **Эпиграф** (Лэмпорт о согласованности и параллелизме)
- [x] **Mermaid:** sync.Map vs RWMutex+map — когда что применять (flowchart)
- [x] **Mermaid:** Lock-free операции (atomic CAS loop)
- [x] **Mermaid:** sync.Pool — lifecycle (Get → Put → GC flush)
- [x] **Callout `[!INTERVIEW]`:** «Когда sync.Map быстрее RWMutex?»
- [x] **Callout `[!WARNING]`:** false sharing — паттерн и предотвращение (cache line 64B)

### Файл 13: Memory Model и happens-before

- [x] **Эпиграф** (Лэмпорт — о модели памяти и упорядочивании событий)
- [x] **Mermaid:** Happens-before граф (goroutine launch → channel send → channel receive → goroutine exit)
- [x] **Mermaid:** Acquire/Release барьеры — что видит CPU vs что видит программист
- [x] **Callout `[!WARNING]`:** Double-Checked Locking — почему не работает без atomic
- [x] **Callout `[!INTERVIEW]`:** «Что гарантирует запись в канал перед чтением?»

### Критерии приёмки этапа 3:
- [x] `python3 builder/build_all.py --all` → exit 0
- [x] `python3 builder/audit_all.py` → 0 errors
- [x] Каждый файл: эпиграф + минимум 2 Mermaid с цветами
- [x] Q08 интегрирован в файл 11
- [x] Коммит: `refactor(module22): этап 3 — конкурентность и memory model (файлы 10–13)`

---

## 🛠️ ЭТАП 4 — Файлы 14–17: Производительность, профилирование, stdlib, HTTP

> **Приоритет:** 🟡 Важный — практические навыки.  
> **Файлов:** 4  
> **Ожидаемое время:** 2–3 часа

### Файл 14: Производительность и оптимизация

**Новые вопросы:** Q04 (`go build -cover`), Q12 (`b.Loop()`), Q15 (`testing/synctest`), Q25 (`go fix` revamp)

- [x] **Эпиграф** (Кернигановский о преждевременной оптимизации — Кнут)
- [x] **Mermaid:** PGO pipeline (profile → build → optimized binary)
- [x] **Mermaid:** Benchmark workflow (написание → `go test -bench` → `benchstat` → вывод)
- [x] **Callout `[!TIP]`:** инструменты профилирования — выбор под задачу (CPU / heap / mutex / block)
- [x] Интегрировать: Q12 (`b.Loop()` в бенчмарках), Q15 (`testing/synctest`)
- [x] **Таблица:** Сравнение оптимизационных инструментов Go (PGO, inlining, escape analysis)

### Файл 15: Профилирование и отладка

**Новые вопросы:** Q19 (`FlightRecorder`), Q23 (goroutine leak profiling 1.26), Q29 (goroutineleak GA 1.27)

- [x] **Эпиграф** (о диагностике — «нельзя оптимизировать то, что нельзя измерить»)
- [x] **Mermaid:** pprof архитектура — как данные текут от рантайма до `go tool pprof`
- [x] **Mermaid:** Типы профилей и когда применять (CPU / heap / goroutine / mutex / block / goroutineleak)
- [x] **Mermaid:** FlightRecorder — кольцевой буфер и сценарий использования
- [x] Интегрировать: Q19 (FlightRecorder), Q23+Q29 (goroutineleak profiling)
- [x] **Callout `[!TIP]`:** как интерпретировать flamegraph — практическое руководство

### Файл 16: Стандартная библиотека

**Новые вопросы:** Q16 (`encoding/json/v2`), Q30 (`uuid` package)

- [x] **Эпиграф** (о стандартной библиотеке как основе)
- [x] **Mermaid:** Карта ключевых пакетов stdlib (io, sync, context, net, encoding)
- [x] **Mermaid:** Сравнение `encoding/json` v1 vs v2 (таблица различий как flowchart)
- [x] Интегрировать: Q16 (json/v2), Q30 (uuid — нативный)
- [x] **Callout `[!INTERVIEW]`:** «Как правильно закрывать resp.Body в net/http?»

### Файл 17: HTTP и сетевое взаимодействие

- [x] **Эпиграф** (о сетях — Таненбаум или Кернигановский)
- [x] **Mermaid:** HTTP/1.1 → HTTP/2 → HTTP/3 (QUIC) — ключевые отличия
- [x] **Mermaid:** net/http server pipeline (listener → accept → goroutine → handler)
- [x] **Mermaid:** gRPC vs REST — сравнение flow (protobuf, multiplexing)
- [x] **Callout `[!WARNING]`:** connection pooling — Transport.MaxIdleConns и утечки
- [x] **Callout `[!INTERVIEW]`:** «Как реализовать graceful shutdown HTTP-сервера?»

### Критерии приёмки этапа 4:
- [x] `python3 builder/build_all.py --all` → exit 0
- [x] `python3 builder/audit_all.py` → 0 errors
- [x] Каждый файл: эпиграф + минимум 2 Mermaid с цветами
- [x] Q12, Q15, Q16, Q19, Q23, Q29, Q30 интегрированы
- [x] Коммит: `refactor(module22): этап 4 — производительность, профилирование, stdlib, HTTP (файлы 14–17)`

---

## 🛠️ ЭТАП 5 — Файлы 18–22: Базы данных, очереди, System Design

> **Приоритет:** 🟡 Важный — системный дизайн на Senior уровне.  
> **Файлов:** 5  
> **Ожидаемое время:** 2–3 часа

### Файл 18: Базы данных. Теория

- [ ] **Эпиграф** (Грей или Клеппман о ACID)
- [ ] **Mermaid:** ACID свойства — flowchart с примерами нарушений
- [ ] **Mermaid:** Уровни изоляции транзакций и аномалии (таблица → flowchart)
- [ ] **Mermaid:** B-tree vs LSM-tree — сравнение write/read path
- [ ] **Callout `[!INTERVIEW]`:** «Что такое Serializable vs Repeatable Read?»

### Файл 19: Базы данных в Go

- [ ] **Эпиграф** (об абстракциях доступа к данным)
- [ ] **Mermaid:** database/sql архитектура (Driver → DB pool → Stmt → Rows)
- [ ] **Mermaid:** Connection pool lifecycle (MaxOpenConns, MaxIdleConns, ConnMaxLifetime)
- [ ] **Callout `[!WARNING]`:** забытый `rows.Close()` — goroutine + connection leak
- [ ] **Callout `[!INTERVIEW]`:** «В чём разница между `db.Query` и `db.Exec`?»

### Файл 20: Очереди и брокеры

- [ ] **Эпиграф** (о асинхронности и слабой связанности)
- [ ] **Mermaid:** Kafka архитектура (producers → partitions → consumer groups)
- [ ] **Mermaid:** At-least-once vs Exactly-once vs At-most-once delivery (flowchart)
- [ ] **Callout `[!INTERVIEW]`:** «Как обеспечить idempotency при exactly-once?»

### Файл 21: System Design. База

- [ ] **Эпиграф** (Клеппман о распределённых системах)
- [ ] **Mermaid:** CAP-теорема — треугольник с примерами систем (CP: etcd, AP: Cassandra)
- [ ] **Mermaid:** Consistent hashing — кольцо узлов с virtual nodes
- [ ] **Mermaid:** Rate limiting паттерны (token bucket / leaky bucket / sliding window)
- [ ] **Callout `[!INTERVIEW]`:** «Как спроектировать rate limiter для 1M RPS?»

### Файл 22: System Design. Highload и FinTech

- [ ] **Эпиграф** (о highload и отказоустойчивости)
- [ ] **Mermaid:** Сага-паттерн (choreography vs orchestration)
- [ ] **Mermaid:** Circuit Breaker — состояния (closed → open → half-open)
- [ ] **Callout `[!INTERVIEW]`:** «Как спроектировать систему переводов с гарантией атомарности?»

### Критерии приёмки этапа 5:
- [ ] `python3 builder/build_all.py --all` → exit 0
- [ ] `python3 builder/audit_all.py` → 0 errors
- [ ] Каждый файл: эпиграф + минимум 2 Mermaid с цветами
- [ ] Коммит: `refactor(module22): этап 5 — БД, очереди, System Design (файлы 18–22)`

---

## 🛠️ ЭТАП 6 — Файлы 23–28: Linux, безопасность, практика, Senior, чеклист

> **Приоритет:** 🟡 Завершающий блок.  
> **Файлов:** 6  
> **Ожидаемое время:** 2–3 часа

### Файл 23: Linux и ОС

**Новые вопросы:** Q13 (`os.Root` — file system scoping)

- [ ] **Эпиграф** (Ритчи о Unix и ОС)
- [ ] **Mermaid:** Жизненный цикл syscall в Go (goroutine → runtime.entersyscall → kernel → runtime.exitsyscall)
- [ ] **Mermaid:** epoll механизм — netpoller интеграция в Go (event loop)
- [ ] Интегрировать: Q13 (`os.Root` — sandboxing, path traversal protection)
- [ ] **Callout `[!INTERVIEW]`:** «Чем горутины лучше потоков OS?»

### Файл 24: Безопасность

**Новые вопросы:** Q14 (Post-Quantum TLS 1.24), Q24 (`crypto/hpke` 1.26), Q31 (`crypto/mldsa` 1.27)

- [ ] **Эпиграф** (о безопасности как слоях защиты)
- [ ] **Mermaid:** TLS 1.3 handshake — упрощённый (1-RTT, 0-RTT)
- [ ] **Mermaid:** Post-Quantum Cryptography в Go — хронология (X25519Kyber768 → HPKE → ML-DSA)
- [ ] **Mermaid:** OWASP Top 10 применительно к Go-сервисам
- [ ] Интегрировать: Q14, Q24, Q31 — блок «Постквантовая криптография в Go»
- [ ] **Callout `[!WARNING]`:** common Go security mistakes (hardcoded secrets, weak crypto, SSRF)

### Файл 25: Практические задачи

- [ ] **Эпиграф** (о практике vs теории)
- [ ] **Mermaid:** Типология задач на Go-собеседовании (алгоритмы / live coding / system design / review)
- [ ] **Callout `[!TIP]`:** стратегия решения live coding задачи за 45 минут

### Файл 26: Поведенческие и архитектурные вопросы

- [ ] **Эпиграф** (о soft skills в инженерии)
- [ ] **Mermaid:** STAR-метод ответа на behavioral вопросы (flowchart)
- [ ] **Callout `[!TIP]`:** как рассказать о failure (Post-mortem структура)

### Файл 27: Вопросы уровня Senior и Staff

- [ ] **Эпиграф** (о лидерстве и технической глубине)
- [ ] **Mermaid:** Уровни инженерной зрелости (Junior → Middle → Senior → Staff) и ожидания
- [ ] **Callout `[!INTERVIEW]`:** топ-10 вопросов Staff-level

### Файл 28: Финальный чеклист

- [ ] **Эпиграф** (о подготовке и уверенности)
- [ ] **Mermaid:** Чеклист подготовки к интервью (flowchart: теория → практика → система → поведение)
- [ ] Обновить чеклист с учётом Go 1.22–1.27 фич

### Критерии приёмки этапа 6:
- [ ] `python3 builder/build_all.py --all` → exit 0
- [ ] `python3 builder/audit_all.py` → 0 errors
- [ ] Каждый файл: эпиграф + минимум 2 Mermaid с цветами
- [ ] Q13, Q14, Q24, Q31 интегрированы
- [ ] Коммит: `refactor(module22): этап 6 — Linux, безопасность, практика, Senior, чеклист (файлы 23–28)`

---

## ✅ ЭТАП 7 — Финальная верификация

> **Выполняется ТОЛЬКО после завершения всех этапов 0–6**

### Задачи:

- [ ] **Полная пересборка:** `python3 builder/build_all.py --all` → exit 0, 0 errors
- [ ] **Аудит:** `python3 builder/audit_all.py` → 0 OS errors, 0 Mermaid errors, 0 broken links
- [ ] **Проверка эпиграфов:** все 28 файлов имеют эпиграфы в каноническом формате
- [ ] **Проверка Mermaid:** все диаграммы имеют цветовую семантику (classDef / style)
- [ ] **Подсчёт диаграмм:** `grep -r "mermaid" sources/22.\ */` → ≥ 56 диаграмм
- [ ] **Проверка новых вопросов:** все 31 вопрос из MODULE22_NEW_QUESTIONS.md присутствуют в лекциях
- [ ] **Проверка версий Go:** таблица версий Go 1.22–1.27 в файле 01 актуальна
- [ ] **Обновление AGENTS.md:** раздел 22 → `✅ Завершен (100%)`, обновить счётчик Mermaid
- [ ] **Финальный коммит:**
  ```bash
  git add -A && git commit -m "docs(module22): этап 7 — финальная верификация и завершение рефакторинга модуля 22"
  ```

---

## 📈 Целевые метрики после рефакторинга

| Метрика | До | После |
|---|---|---|
| Файлов | 28 | 28 |
| Диаграмм Mermaid | 0 | ≥ 56 (2+ на файл) |
| Эпиграфов | 0 | 28 (по одному в файл) |
| Вопросов по Go 1.22–1.27 | 0 | 31 |
| Callout-блоков `[!INTERVIEW]` | ~0 | ≥ 28 |
| Статус в AGENTS.md | `CONVERTED` | `✅ Завершен (100%)` |

---

## 🔗 Связанные документы

- [`MODULE22_NEW_QUESTIONS.md`](./MODULE22_NEW_QUESTIONS.md) — полный список 31 нового вопроса по Go 1.22–1.27
- [`AGENTS.md`](./AGENTS.md) — стандарты редактуры (§2.5 палитра Mermaid, §3 Zero Knowledge Loss)
- [`MODULE21_REWRITE_PLAN.md`](./MODULE21_REWRITE_PLAN.md) — образцовый план (шаблон)
