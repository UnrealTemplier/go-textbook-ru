# Primary Fact-Check · Модуль 1 «Архитектура компьютера»

> **Роль:** primary source-based fact checker (Sonnet 5.5).
> **Вход:** `sources/1. Архитектура компьютера/` (41 статья, состояние после `6d1334d3`), `1-opus-judge.md` (Master Fact-Check Brief). Файла `1-opus-blind-spot.md` в репозитории нет, поэтому он не учитывался.
> **Дата проверки:** 2026-10-02. **Среда:** go1.27.1 linux/amd64 (`/usr/local/go`), Intel Core i9-12900K, Linux 7.2.8, btrfs.
> **Файлы модуля не изменялись.** Все пробные программы лежали в scratchpad.

---

## 0. Как читать отчёт

### Статусы
`VERIFIED` · `INCORRECT` · `PARTIALLY CORRECT` · `OUTDATED` · `CONTEXT-DEPENDENT` · `OPINION / NOT A FACT CLAIM` · `NOT CHECKED`

Статус относится **к утверждению в тексте модуля**, а не к претензии брифа. Если претензия брифа подтверждена, статус текста обычно `INCORRECT` или `PARTIALLY CORRECT`. Если претензия отклонена, статус текста `VERIFIED`.

### Метки доказательств
| Метка | Что это |
|---|---|
| **[L]** | Проверено на этой машине: исходники `/usr/local/go/src`, сборка и дизассемблирование (`go tool objdump`), запуск кода, `sysfs`, `lscpu`. Это поведение **go1.27.1**, а не обязательно более старых версий. |
| **[R]** | Проверено по первичному источнику вне машины: release notes go.dev (1.14–1.27), история `golang/go` (блоб-less клон, `git log`, `git tag --contains`), документация ядра Linux, man-страница `open(2)`, спецификация JVM, исходники сторонних модулей (`go-sqlite3`, `confluent-kafka-go`), Pike «Go at Google», Kanev et al. 2015. |
| **[Л]** | Арифметика или логика, проверенная расчётом и текстом самой статьи. |
| **[K]** | Утверждение опирается только на общеизвестную литературу (Intel SDM, Patterson–Hennessy и т. п.), которую я **в этой сессии не открывал**. Такие пункты **не считаются проверенными**. Для них стоит `NOT CHECKED` с предварительной оценкой. |

### Важное ограничение
Модуль содержит ~1 МБ текста. Я не перечитывал его целиком. Я прочитал бриф судьи целиком и проверил исходное место каждого пункта из §§ 2–3, всех кластеров C1–C14 и тех Medium-пунктов, где проверка возможна без закрытых источников. Пункты **Low**, для которых нужны микроархитектурные таблицы (Agner Fog, uops.info, Chips and Cheese) или платные стандарты (JEDEC, Intel SDM), оставлены как `NOT CHECKED`. Их список в § 7.

---

## 1. Сводка

| Группа (числа приблизительные) | Всего | Подтверждено претензией (текст неверен / неточен) | Претензия отклонена (текст верен) | NOT CHECKED |
|---|:---:|:---:|:---:|:---:|
| High J-H1…J-H7 | 7 | 7 | 0 | 0 |
| Конфликты K1–K14 | 14 | 11 | 3 (K5, K9, K11-часть) | 0 |
| Кластеры C1–C14 | 14 | 11 | 0 | 3 (C8-часть, C9-часть, C12 — вне скоупа) |
| Medium (по статьям) | ~75 | ~35 | 1 | ~38 |
| Low | ~120 | 11 | 3 | ~105 |

**Главные результаты (проверено [L]/[R]):**
1. **J-H1 (порядок бутстрапа)** подтверждён по `asm_amd64.s` и `proc.go`: диаграмма в ст. 1 ставит шаги в неверном порядке и противоречит сама себе.
2. **J-H2 (Register Renaming)**: пример собран `go tool asm`. `MOVQ AX, 10` в Plan 9 — **запись AX в память по адресу 10**, а не загрузка константы. `ADDQ BX, AX` — это `AX += BX`, а комментарий пишет `BX = BX + AX`. Пример неверен целиком.
3. **J-H3**: оба примера не компилируются (`"time" imported and not used`, `"sort" imported and not used`).
4. **J-H6**: **обе** заявленные ошибки сборки неверны. `go-sqlite3` собирается и падает в рантайме. `confluent-kafka-go` собирается, а ошибка возникает у вызывающего кода (`undefined: kafka.NewProducer`). Ни в одном случае нет `build constraints exclude all Go files`.
5. **ABIInternal**: «прирост 5–15 %» в ст. 6 **неверен**. Release notes Go 1.17 говорят «about 5 %», Go 1.18 добавляет «10 % or more» только для arm64 и ppc64.
6. **Kanev et al.** (ст. 17) профилировали **C++-код**, а не Go-сервисы, и back-end bound там больше 60 % слотов у большинства задач, а не «20–40 %».
7. **Бенчмарк ст. 18**: «≈ 19×» на этой же модели CPU не воспроизвёлся (≈ 11×: 7,5 мс против 84 мс). Ряд 7,1 мс сошёлся, столбец 136 мс нет.
8. **`crypto/subtle` и `CMOV`** (ст. 13): в пакете нет ни одного `CMOV`; `WithDataIndependentTiming` включает DIT только на arm64 (FEAT_DIT), на остальных архитектурах это no-op.

---

## 2. High (J-H1 … J-H7)

### J-H1 · Порядок бутстрапа рантайма (ст. 1, диаграмма и итог п. 4) — **INCORRECT** (порядок), итог п. 4 — **PARTIALLY CORRECT**
**Доказательство [L]:**
- `runtime/asm_amd64.s` (`rt0_go`): стек `g0` задаётся через `LEAQ (-64*1024)(SP), BX` (стр. ~160), затем `m0.g0 = g0`, `g0.m = m0` (стр. ~262–268), и **только после этого** вызываются `args`, `osinit`, `schedinit` (~337–340), `newproc(mainPC)` и `mstart`.
- `runtime/proc.go:892` — `maps.AlgInit()` вызывается **внутри `schedinit`**, как и `mallocinit()`, `mcommoninit`, `modulesinit`, `itabsinit`, `stkobjinit`, `gcinit()` (стр. ~912).
- В `func main()` (`proc.go`): `newm(sysmon…)`, `lockOSThread()`, `doInit(runtime_inittasks)`, `gcenable()`, `doInit` для модулей, `fn := main_main` — вызов **напрямую**, без «запуска горутины main.main в планировщике».

**Что не так в тексте:** (1) привязка `m0/g0` стоит **после** `schedinit`, а на деле до `osinit`; (2) `alginit` вынесен рядом с `osinit`, хотя это часть `schedinit`; (3) узел «gcinit (вызывается внутри schedinit)» стоит после `schedinit`, то есть сам себе противоречит; (4) `runtime.main` и есть главная горутина, а «горутина main.main» — это её вызов `main_main`. Подпись узла D («schedinit: аллокатор mheap и планировщик») верна: `mallocinit` действительно внутри `schedinit`.
**Итог п. 4** («m0/g0 → mheap → GC и планировщик → main.main») верен как идея, но «старт GC» — это `gcenable()` в `runtime.main`, а не `gcinit`.
**Что исправить:** `rt0_go` (стек g0, m0↔g0, CPUID) → `args` → `osinit` → `schedinit` (внутри: `mallocinit`, `AlgInit`, `mcommoninit`, … `gcinit`, `procresize`) → `newproc(runtime.main)` → `mstart` → `runtime.main` (sysmon, `doInit`, `gcenable`, `main_main`).

### J-H2 · Ассемблер в разборе Register Renaming (ст. 12) — **INCORRECT**
**Доказательство [L]:** файл `x_amd64.s` из четырёх строк статьи собран `go tool asm` и разобран `objdump`:
```
MOVQ AX, 0xa     // 4889042 50a000000 — STORE из AX по абсолютному адресу 0xa
ADDQ BX, AX      // 4801d8            — AX = AX + BX
MOVQ AX, 0x14    // STORE из AX по адресу 0x14
SUBQ CX, AX      // 4829c8            — AX = AX - CX
```
Ст. 9 учит «источник, приёмник». Комментарии `BX = BX + AX` и `CX = CX - AX` описывают Intel-порядок. Анализ RAW/WAR/WAW по такому примеру не соответствует показанному коду (в Plan 9 первая и третья строки вообще пишут в память, а не в регистр). Та же ошибка в mermaid (`I1…I4`).
**Что исправить:** либо Plan 9: `MOVQ $10, AX; ADDQ AX, BX; MOVQ $20, AX; SUBQ AX, CX`, либо Intel: `mov rax, 10; add rbx, rax; mov rax, 20; sub rcx, rax`. Идея (ложные зависимости по имени `AX`) от этого не меняется.
**Заметка [R]:** «224 регистра в AMD Zen 4» — найдено подтверждение числа (224 integer PRF), но источник — поисковая выдача, а не статья Chips and Cheese. Статус для числа: `NOT CHECKED` (правдоподобно). «Более 300 в Apple M3» — `NOT CHECKED`.

### J-H3 · Примеры, которые не собираются (ст. 4, ст. 13) — **INCORRECT** (оба)
**Доказательство [L]:** код извлечён из статей слово в слово.
- ст. 4 (`DFlipFlop`): `go vet` → `"time" imported and not used`. Текст обещает «обновляемую строго по каналу-тикеру», а ни канала, ни `time.Ticker` в примере нет.
- ст. 13: `go build` → `"sort" imported and not used` при закомментированном `sort.Ints`.
**Побочно подтверждено [L]:** при раскомментированном `sort.Ints` пример компилируется. Замер на этой машине: отсортировано ≈ 0,85 мс, не отсортировано ≈ 3,0 мс (≈ 3,5×). Утверждение статьи «в несколько раз быстрее» **VERIFIED** для этой машины.
**Что исправить:** убрать `"time"` или добавить реальный `time.Ticker`; в ст. 13 использовать `_ "sort"` либо оставить `sort.Ints` с флагом/комментарием, который не ломает компиляцию.

### J-H4 · THP: «фризы ушли ⇒ виноват khugepaged» (ст. 30) — **PARTIALLY CORRECT**
**Доказательство [R]:** `Documentation/admin-guide/mm/transhuge.rst` (torvalds/linux, master):
- `defrag=always` — «application requesting THP will stall on allocation failure and directly reclaim pages and compact memory»;
- `defrag=madvise` (**по умолчанию**) — «will enter direct reclaim like `always` but **only for regions that have used `madvise(MADV_HUGEPAGE)`**»;
- `khugepaged` — фоновый поток, стартует при включённом THP.
**[L]** Этот хост: `enabled=[madvise]`, `defrag=[madvise]`.
**[L]** Рантайм Go вызывает `sysHugePage` только для метаданных `pageAlloc.chunks` (`mpagealloc.go:420`); `sysMapOS` (`mem_linux.go:172–190`) под `GODEBUG=disablethp` ставит `MADV_NOHUGEPAGE`. Текст ст. 30 об этом сказан верно.
**[R]** `doc/godebug.md`: поведение откачено в Go 1.21.1, переменная `disablethp` доступна с 1.21.6 → версия «Go 1.21.6 / 1.22» **VERIFIED**.

| Утверждение | Статус |
|---|---|
| Режимы `enabled`, `madvise`/`never`, различие дистрибутивов | **VERIFIED** |
| «Ядро обязано выдать 2 МБ … Подождите!» в режиме `always` | **INCORRECT** при дефолтном `defrag=madvise`: ядро быстро откатывается на 4 КБ; синхронная компактизация нужна `defrag=always` (или `defer+madvise` для madvised-регионов). Параметр `defrag` в тексте упомянут, но дальше сценарий описан так, как будто он не действует |
| «зависает на 50–200 мс» | **NOT CHECKED** (числа нет в источниках; порядок величин правдоподобен для direct compaction, но без измерения это не факт) |
| Строка 152: `khugepaged` «создаёт паузы синхронной компактизации» | **INCORRECT**: khugepaged не блокирует поток мутатора на аллокации. Он даёт RSS-bloat и конкуренцию за `mmap_lock` |
| Строка 175: «если после `disablethp=1` фризы исчезли — виноват khugepaged» | **INCORRECT** как диагностический вывод. `disablethp` убирает huge pages из арен целиком и тем самым снимает и прямую компактизацию (при `defrag=always`), и khugepaged. Исчезновение фризов не различает эти механизмы |
| RSS-петля «scavenger возвращает арены, khugepaged собирает обратно» | **CONTEXT-DEPENDENT**: механизм описан в GC guide и release notes 1.21/1.22, зависит от `max_ptes_none` |

### J-H5 · Double-Checked Locking: «читает мусор» (ст. 24) — **PARTIALLY CORRECT**
**Доказательство [L]:** `runtime/malloc.go:1304, 1416, 1485` — `publicationBarrier()` с комментарием: «Ensure that the stores above that initialize x … occur before the caller can make x observable to the garbage collector. Otherwise, on weakly ordered machines, the garbage collector could follow a pointer to x, but see uninitialized memory».
- Для `Singleton{data int}` `new` возвращает **обнулённую** память, барьер публикации стоит до возврата указателя. «Мусор» невозможен: в худшем случае читатель увидит нулевые поля.
- «Процессор **спекулятивно** выполняет Действие Б» — **INCORRECT**: спекулятивное выполнение не делает store видимым другому ядру. Перестановка store–store — следствие store buffer и слабой модели (ARM64).
- «Сервис падает с паникой или повреждением памяти» — не следует из показанного кода.
- Вывод статьи (гонка данных, нужен `sync.Once`/`atomic.Pointer`) **VERIFIED** (по Go Memory Model читающая сторона без синхронизации — гонка).
- Версии `sync.Once.done`: **VERIFIED [R]** (git): `atomic.Uint32` — `be3d5fb6e6` (2023-10-06, цикл 1.22); `atomic.Bool` — `95611c0eb4` (2025-04-20, первый тег `go1.25rc1`); до 1.22 `done uint32`.
**Что исправить:** показать конструктор, который пишет ненулевые значения после `new`, убрать «спекулятивно» и «мусор». Это предмет редактора.

### J-H6 · Ловушка CGO (ст. 8) — **INCORRECT**
**Доказательство [R], воспроизведено:**
- `mattn/go-sqlite3` v1.14.52: файл `static_mock.go` с тегом `//go:build !cgo` регистрирует драйвер-заглушку. `GOOS=linux GOARCH=arm64 CGO_ENABLED=0 go build` → **успех (exit 0)**. Запуск с `CGO_ENABLED=0` печатает: `Binary was compiled with 'CGO_ENABLED=0', go-sqlite3 requires cgo to work. This is a stub`.
- `confluent-kafka-go/v2` v2.15.1: заглушки нет, но часть файлов пакета без `import "C"`, поэтому пакет не «пустой». Результат: `undefined: kafka.NewProducer`, `undefined: kafka.ConfigMap` в коде пользователя. Сообщения `build constraints exclude all Go files` **нет**.
- Утверждение «при смене `GOOS`/`GOARCH` cgo по умолчанию выключается» **VERIFIED [L]** (`cmd/go/internal/cfg/cfg.go:140–184`).
- Утверждение «с `CGO_ENABLED=1` без кросс-тулчейна ошибку даёт C-компилятор» — **PARTIALLY CORRECT**: ошибка зависит от `CC` и платформы; общий смысл верен.
- Совет про `modernc.org/sqlite` — **OPINION** (чистый Go, но с компромиссами по скорости и совместимости).
**Что исправить:** описать режим отказа точно: либо тихая сборка с рантайм-ошибкой (`go-sqlite3`), либо «undefined: …» (`confluent-kafka-go`).

### J-H7 · Вывод `-gcflags=-m` (ст. 40) — **PARTIALLY CORRECT**
**Доказательство [L]:** для `cfg := Config{…}; return &cfg` go1.27.1 печатает **только** `moved to heap: cfg`. Строка `&cfg escapes to heap` не выводится ни с `-m`, ни с `-m=2` (в `-m=2` вместо неё `cfg escapes to heap in NewConfig:` и цепочка `flow:`). Строка `&Config{…} escapes to heap` относится к `&T{…}`.
- Без `//go:noinline` функция инлайнится (`can inline NewConfig`, `inlining call to NewConfig`), и для места вызова строки `moved to heap` нет. Безусловный вердикт «Плохо» — упрощение.
- Рекомендация «возврат по значению для малых структур» — **OPINION / CONTEXT-DEPENDENT**.
**Что исправить:** вывод заменить на `moved to heap: cfg`, добавить оговорку про инлайнинг.

---

## 3. Конфликты брифов (K1–K14)

| # | Тема | Статус текста | Доказательство и вывод |
|---|---|---|---|
| **K1** | Стек `g0` (ст. 1:95) | **VERIFIED** | [L] `proc.go:2347–2351`: `iscgo \|\| mStackIsSystemAllocated()` → `malg(-1)`, иначе `malg(16384 * sys.StackGuardMultiplier)`. `asm_amd64.s:161` — граница 64 КБ для `m0`. Gemini (8 КБ) неправ. Текст ст. 1 («около 64 КБ» для главного потока) верен. Остаток: не сказано про 16 КБ и стек ОС при cgo — Low-уточнение |
| **K2** | LSE на ARM64 (ст. 20, 23) | ст. 23:81 **PARTIALLY CORRECT**; ст. 23 итог п. 2 **PARTIALLY CORRECT** | [L] `GOARCH=arm64`, `atomic.AddInt64`. При `GOARM64=v8.0` (default): `MOVBU` флага `ARM64HasATOMICS` + `TBZ`, ветка с `LDAXR/STLXR/CBNZ` и ветка с LSE (`f8e10040` = `LDADDAL`, objdump его не декодирует). При `v8.1`: один `LDADDAL`, без ветвления. Значит «LSE активен на Graviton2+» верно **по умолчанию через рантайм-проверку**, а не безусловно. Итог п. 2 («спаренные инструкции в ARM64») верен только для fallback |
| **K3** | `MOVBE` и `binary.BigEndian` (ст. 26) | **PARTIALLY CORRECT** | [L] `binary.BigEndian.Uint32`: amd64 `GOAMD64=v1` → `MOVL (AX), AX; BSWAPL`, `v3` → `MOVBE 0(AX), AX`; arm64 → `MOVWU; REVW`. Везде также одна проверка границ. Статья пишет «ровно одну инструкцию» и `REV`: инструкций две (load + swap), а на arm64 для 32 бит `REVW`. Прав Sonnet |
| **K4** | Вектор. регистры при async preemption (ст. 7, 14, 16) | ст. 16:124 **VERIFIED**; ст. 14:170 **VERIFIED** | [R] `preempt_xreg.go` появился коммитом `af0c4fe2ca` (2025-04-29), первый тег — `go1.26rc1`. Сообщение коммита: GPR и XMM раньше сохранялись на стек (368 байт), `xRegs` — механизм для AVX-512 (2,5 КиБ). Gemini неправ, что была «проблема»; ст. 16 («с Go 1.26 … `xRegs`») точна. Но ст. 7 (механика) — см. C4 |
| **K5** | `x-8(SP)` (ст. 9) | **VERIFIED** | [L] `doc/asm.html:219–229`: «`x-8(SP)` and `-8(SP)` are different memory locations». Gemini — ложное срабатывание |
| **K6** | CF и OF (ст. 3) | **VERIFIED** (в части CF для `uint64`); **PARTIALLY CORRECT** (в части «Go даёт прямой доступ к флагу») | [L] `bits.Add64` на amd64 = `ADDQ BX, AX; SETB CL; MOVZX` (флаг превращается в значение). Интринсик есть для AMD64, ARM64, PPC64, S390X, RISCV64, Loong64, MIPS64 (`intrinsics.go:1264–1268`), для 386/arm/wasm — нет. Заголовок «целочисленное переполнение» без «беззнаковое» — Low |
| **K7** | False sharing и выравнивание (ст. 21, 40) | **CONTEXT-DEPENDENT** | [Л] Счётчики с шагом 64 Б никогда не делят 64-байтную линию при любом выравнивании массива (механика Gemini неверна). Для структур с двумя горячими полями сдвиг 56 mod 64 действительно разносит поля. Оговорка о выравнивании в тексте есть. Свойства аллокатора и линкера (глобалы ≤ 32 Б) — `NOT CHECKED` |
| **K8** | AVX-512 downclocking (ст. 15) | **CONTEXT-DEPENDENT**; цифры и «−30 %» — **NOT CHECKED** | Оговорка «эпоха Skylake-SP» в тексте есть. Исходные цифры (4.8/4.3/3.2 ГГц) проверить по Intel spec update не удалось. «Сгорит за миллисекунды» — **OPINION / гипербола** (проверки по первоисточнику не делал, `NOT CHECKED`). «Аппаратно» (стр. 95) против «программно» (стр. 123) — внутреннее противоречие по тексту (подтверждено чтением), способ отключения AVX-512 на Alder Lake — `NOT CHECKED` |
| **K9** | `sync.Mutex` в 1.24+ (ст. 2) | **VERIFIED** | [L][R] `internal/sync/mutex.go:20–23`: `state int32; sema uint32`. Перенос реализации — коммит `6c66005285` (2024-06-21), первый тег `go1.24rc1`. Ст. 2:214 («до Go 1.24 — прямо в `src/sync/mutex.go`») точна |
| **K10** | Статус `simd` (ст. 14:126, 16:102, 158) | ст. 14:126 **VERIFIED**; ст. 16:158 «пока только amd64» **OUTDATED** (для 1.27) | [R] release notes: Go 1.26 — `simd/archsimd` экспериментален, «currently available on the amd64»; Go 1.27 — «adds support for arm64 “Neon” 128-bit SIMD and WebAssembly 128-bit SIMD», а также новый портируемый `simd` «available on all architectures». «Пока только amd64» верно ровно для 1.26 |
| **K11** | `entersyscallblock` для CGO (ст. 34) | **VERIFIED** (текст) | [L] `cgocall.go:167` вызывает `entersyscall()`. Утверждение Gemini неверно. Остаток — Low |
| **K12** | USL: σ/κ или α/β (ст. 39) | **OPINION / NOT A FACT CLAIM** | Оба обозначения встречаются; ссылка Gemini на `coder/usl` не проверялась. `NOT CHECKED` |
| **K13** | `GOMAXPROCS` в контейнерах (ст. 32) | ст. 32:102 **VERIFIED**; строка 194 **CONTEXT-DEPENDENT** | [L] `cgroup_linux.go:109–118`: `ceil(limit)`, `max(limit, 2)`, значение только **уменьшается**. [L] `doc/godebug.md:251–260`: `containermaxprocs`, `updatemaxprocs` (периодическое обновление). [R] release notes 1.25: «Container-aware GOMAXPROCS». Строка 194 «GOMAXPROCS = суммарное число vCPU» неверна для cgroup-лимита на Go ≥ 1.25 |
| **K14** | 500 мкс RTT в ЦОД | **CONTEXT-DEPENDENT** | Число из списка Дина/Норвига (2009). Внутренняя несогласованность подтверждена по тексту: ст. 38:92 «в хорошей сети 10–150 мкс», ст. 38:119 то же, ст. 38:147 «от 500 µs внутри стойки». Таблица ст. 1:148 оговорки не содержит. Точные современные цифры (10–30 мкс, 1–5 мкс RDMA) — `NOT CHECKED` (по запросу найдены лишь вторичные описания AWS) |

---

## 4. Кластеры

### C1. Plan 9 / Intel, порядок операндов
- ст. 12 — **J-H2: INCORRECT** (см. § 2).
- ст. 8 «слева направо» как общее правило — **PARTIALLY CORRECT**: для Go-ассемблера на всех архитектурах источник идёт первым, но суффиксы и набор операндов различаются; детали arm64/riscv64 — **NOT CHECKED**.
- ст. 9 суффиксы `W/L/Q` — **CONTEXT-DEPENDENT** (amd64); arm64 `W`/`D` — **NOT CHECKED**.
- ст. 2 `XOR AX,AX` — **PARTIALLY CORRECT**: Go печатает `XORL AX, AX` (на практике; пробного прогона не делал → **NOT CHECKED**).

### C2. Непомеченное x86-допущение
- ст. 3:228, 277 — **PARTIALLY CORRECT** ([L] интринсик, см. K6).
- ст. 5 (`CALL` кладёт `RIP` на стек), ст. 34 (Ring 0/3, `SYSCALL`) — **CONTEXT-DEPENDENT** (x86-64) [K].
- ст. 6:18 «Ни один современный x86-64 или ARM не может …»: утверждение для арифметики **VERIFIED** [K] (RISC — load/store; x86 — один операнд в памяти, самой статьёй оговорено). «GPR всего 16» — **CONTEXT-DEPENDENT** (x86-64; ARM64 — 31 GPR [K]). Intel APX (32 GPR) — **NOT CHECKED**.
- ст. 23:209 — см. K2.

### C3. ABIInternal
- **ст. 6:181 «прирост от 5 % до 15 %» — INCORRECT** [R]: Go 1.17 release notes: «performance improvements of about 5 %, and a typical reduction in binary size of about 2 %», только `linux/amd64`, `darwin/amd64`, `windows/amd64`. Go 1.18: «On 64-bit ARM and 64-bit PowerPC systems, benchmarking shows typical performance improvements of 10 % or more»; amd64 на всех ОС.
- **ст. 6:214, ст. 1:47, ст. 10 «примерно 5 %»** — **VERIFIED** [R]. Ст. 1:47 «в Go 1.18 регистровая передача добавлена на arm64 и ppc64/ppc64le» — **VERIFIED** [R].
- «9 целочисленных регистров `RAX, RBX, RCX, RDI, RSI, R8, R9, R10, R11`» — **VERIFIED** [L] `abi-internal.md:385–392`. «Числа с плавающей точкой: `X0–X14`» (15) — **VERIFIED**.
- ст. 6:186 «более 9 аргументов int исчерпывают регистры» — **PARTIALLY CORRECT**: распределение идёт по значениям целиком; `string` занимает 2 регистра, slice 3, interface 2; структура, не поместившаяся, уходит на стек целиком (текст это говорит). Для 128-байтной структуры (ст. 17:199–207) вывод «не умещается в 9 регистров → стек» **VERIFIED** по правилу ABI.
- ст. 6:197 «`-gcflags=-S` выдаёт листинг SSA» — **INCORRECT**: `-S` печатает финальный Go-asm; SSA — `GOSSAFUNC`. [K] (подтверждено видом вывода `-S` в моих прогонах, SSA в нём нет).
- ст. 6:181 «нулевая задержка (0 нс)» — **OPINION / гипербола**.
- ст. 15 «5–15 тактов на вызов asm-функции» — **NOT CHECKED**.
- ст. 10:143 «callee-saved нет» — **VERIFIED** [L] `abi-internal.md:221`. Нюанс: `RSP`, `RBP`, `R14`, `X15` — fixed («Same» при возврате), `MXCSR` status bits — callee-save (`abi-internal.md:408–415, 503`) → Low.

### C4. Асинхронное вытеснение
- **ст. 7:144 «обработчик подменяет адрес возврата в `ucontext`»** — **PARTIALLY CORRECT** [L]. `signal_amd64.go:80`: `pushCall` кладёт прерванный PC на стек горутины и ставит `rip = asyncPreempt`. Это эмуляция вызова, а не подмена адреса возврата.
- **ст. 7:161, 163 «`asyncPreempt` паркует горутину»** — **INCORRECT** [L]. `asyncPreempt2` → `gopreempt_m` → `goschedImpl`: горутина становится `_Grunnable` и попадает в **глобальную очередь** (`globrunqput`), а `preemptPark` вызывается только при `preemptStop`.
- **ст. 7:139, 156 «горутина > 10 мс на одном M»** — **PARTIALLY CORRECT** [L]: `retake` сравнивает `schedtick` и `schedwhen` по **P**; `forcePreemptNS = 10 мс`.
- sysmon: «20 мкс, затем удваивается до 10 мс» — **VERIFIED** [L] (`proc.go`, `sysmon`: `delay = 20`, после 50 пустых циклов `delay *= 2`, потолок `10*1000`).
- `SIGURG` — **VERIFIED** [L] (`signal_unix.go:67`).
- Механика до 1.14 — **NOT CHECKED** (текст ст. 7 верен по общим сведениям; детали `stackguard0 = stackPreempt` не перепроверялись).

### C5. Когерентность / консистентность / барьеры
- ст. 20:118, 160 «никогда не отдаст устаревшее значение» — **PARTIALLY CORRECT**: инвариант когерентности (последовательность записей по одному адресу) верен, но «никогда не прочитает старое» без оговорки про store buffer и invalidate queue вводит в заблуждение. [K], статья сама различает когерентность и консистентность.
- ст. 24:15, 74–75, 196 «ни при каких условиях … даже спекулятивно» — **PARTIALLY CORRECT** [K]: спекулятивные загрузки выполняются и откатываются; запрещён наблюдаемый порядок.
- ст. 22 мотивировка «компилятор переставит ради регистров» — **OPINION**; сам факт допустимости перестановки по Go Memory Model — **VERIFIED** (`doc/go_mem.html`, [L] локально присутствует, но формулировки не перечитывал → `NOT CHECKED` на уровне цитаты).
- ст. 8:194 «x86 работал случайно», «барьеры заставляют сбросить очереди записи» — **PARTIALLY CORRECT** [Л]: гонка данных — ошибка на любой архитектуре; acquire/release не обязаны делать flush. Утверждение «на x86 запись `atomic.Store` стоит дороже обычной (`XCHG`)» — **NOT CHECKED** (судья отметил как верное; мой прогон не делался).
- ст. 12/13 «PRF» против «ROB» — **NOT CHECKED** (Low).

### C6. Интерфейсы, `[]any`
- ст. 38:82–83 «`[]interface{}` — гарантированный cache miss на каждом элементе» — **INCORRECT/преувеличение** по самому модулю (ст. 18: pointer-shaped значения и малые целые не аллоцируются, `staticuint64s`) — внутреннее противоречие подтверждено по тексту; сами свойства рантайма не перепроверял.
- ст. 41 «`interface{}` … `itab`/VMT лишают инлайнинга» — **NOT CHECKED** (предварительно **PARTIALLY CORRECT**: у `any` нет методов и `itab`; девиртуализация через PGO подтверждена release notes 1.21/1.22 [R], остальное [K]).
- ст. 10 итог п. 6 — **PARTIALLY CORRECT** (противоречит оговорке в той же статье).

### C7. Каналы
- **ст. 23:3 «на дне рантайма нет магических мьютексов»** — **PARTIALLY CORRECT** [L]: `hchan` защищается `lock mutex` (`runtime.mutex`, `chan.go`). Сам `runtime.mutex` построен на атомиках/futex, так что «всё на атомиках» верно на самом нижнем уровне, но фраза про `chan.go` вводит в заблуждение.
- **ст. 33:106 «канал — структура с `sync.Mutex`»** — **INCORRECT** [L]: тип `runtime.mutex`, а не `sync.Mutex`.

### C8. Таблицы задержек
- Масштаб ст. 1 («1 такт = 1 с» при 3 ГГц): **VERIFIED** [Л] — 20–50 мкс ≈ 0,7–1,7 дня, 500 мкс ≈ 17 суток, 150 мс ≈ 14,3 года.
- Масштаб ст. 38 (1 нс = 1 с): 500 000 нс = 5,79 суток — **VERIFIED** [Л].
- Mispredict «3 нс» (ст. 38:26) против 15–20 тактов (ст. 11, 13) — **PARTIALLY CORRECT** [Л]: 15–20 тактов при 3–5 ГГц = 3–7 нс; оригинал Дина — 5 нс. Внутренне несогласовано, цифры — `NOT CHECKED` по первичному источнику.
- NVMe «20–50 мкс», L1/L2 такты, page walk «десятки нс» против «40–100+ нс» — **CONTEXT-DEPENDENT / NOT CHECKED** (нужны Agner Fog, Chips and Cheese).
- ст. 38:130 «инвалидируются части TLB при переключении потоков» — **PARTIALLY CORRECT** [K]: поток того же процесса `CR3` не меняет; `NOT CHECKED`.

### C9. Числа микроархитектуры
- **ст. 8:32 «Golden Cove: L3 36 МБ, 3.8 ГГц»** — **INCORRECT** [L]: `lscpu` и `/sys/.../cache/index3` на i9-12900K (Golden Cove): L3 = **30 МиБ**, 12-way. 36 МБ у Raptor Lake [K]. «6 декодеров» у Golden Cove — **NOT CHECKED**.
- **ст. 19 «L1d почти всегда 8-way»** — **INCORRECT** [L]: на этой машине L1d **48 КиБ, 12-way**, 64 B линия, 64 sets (L1i 32 КиБ 8-way; L2 1,25 МиБ 10-way).
- ст. 8:56 «монолит Intel против чиплетов AMD» — **OUTDATED** [K] (Sapphire Rapids, Meteor Lake — тайлы); `NOT CHECKED` по источнику.
- ст. 18 (L2 «локален», L3 «768–1152 МБ общий для ядер»), ст. 29 (DTLB 64 / STLB 1024–2048), ст. 33 (ring/mesh) — **NOT CHECKED**.
- **ст. 32 «SMT < 5 % площади»**: **CONTEXT-DEPENDENT** [R]: источник — Marr et al., *Hyper-Threading Technology Architecture and Microarchitecture*, Intel Technology Journal, v.6 № 1, 2002 («costs less than 5 percent in added die area», «25 % boost»). Это оценка для Pentium 4/Xeon 2002 года, а не общее свойство.
- Ст. 32 «Intel HT как стандарт»: Lunar Lake / Arrow Lake без HT — **NOT CHECKED** [K]; на i9-12900K HT только у P-ядер, у E-ядер (CPU 16–23) его нет — **VERIFIED** [L] (`thread_siblings_list`).

### C10. Ядро Linux
- **ст. 34:32 и ст. 41 «планировщик Linux (CFS)»** — **OUTDATED** [R]: `docs.kernel.org/scheduler/sched-eevdf.html` — переход на EEVDF с 6.6 (слияние 29.08.2023 [W: Phoronix]). Для LTS 5.15/6.1 CFS остаётся верным → `CONTEXT-DEPENDENT`.
- **ст. 34:75 «syscall инвалидирует таблицы предсказания ветвлений и сбрасывает конвейер»** — **PARTIALLY CORRECT** [K]: сброс предсказателя даёт только митигации (IBRS/IBPB). `NOT CHECKED` по документации.
- **ст. 28:134 «Никакого строгого OOM-killer не существует»** — **PARTIALLY CORRECT / вводит в заблуждение** [K]: OOM killer есть, а в cgroup v2 `memory.max` убивает процесс при превышении; `NOT CHECKED` по docs ядра. Сам пример с `vm.overcommit_memory=0/1` — **CONTEXT-DEPENDENT**.
- **ст. 28 «scavenger: `MADV_DONTNEED` по умолчанию с Go 1.16»** — **VERIFIED** [R] (Go 1.16 release notes).

### C11. Виртуальная память
- **ст. 27:163–197 nil** — **PARTIALLY CORRECT**:
  - [L] `vm.mmap_min_addr = 65536` на этом хосте; ядро не отдаёт процессам адреса ниже порога, независимо от «первой страницы 4 КБ».
  - [L] `nilcheck.go:192`: `minZeroPage = 4096`, «All platforms are guaranteed to fault … smaller than this address».
  - [L] Структура с `[8192]byte` перед полем: `main.Big` содержит явную `TESTB AL, 0(AX)` перед `MOVQ 0x2000(AX), AX`; для маленького смещения (`Small`) проверка не нужна (`MOVQ 0x8(AX)`). Текст описывает только вариант с малым смещением.
  - «Помечается флагом отсутствия прав (Guard Page)» — неточно: на Linux это просто отсутствие отображения.
- ст. 27:39–48 «48-битное пространство без LA57» — **CONTEXT-DEPENDENT**; PML5 в ст. 28:45 упомянут. Утверждение «PML5 стал стандартом» — `NOT CHECKED`.
- ст. 28/29 — 2D page walk (EPT/NPT, ≤ 24 обращений) не упомянут: **пропуск**, оговорка желательна, но это не ошибка факта.
- ст. 27:126 «`malloc()` регулярно приводит к `brk`/`mmap`» — **PARTIALLY CORRECT** [K] (glibc/jemalloc обслуживают большинство вызовов из арен), `NOT CHECKED`.
- ст. 27: стеки горутин 2 КБ — **VERIFIED** по смыслу; адаптивный старт — **VERIFIED** [R][L] (Go 1.19 release notes: «allocate initial goroutine stacks based on the historic average stack usage»; `runtime1.go:397` `adaptivestackstart = 1`).

### C12. Mermaid `:::class` в метках — **NOT CHECKED (вне скоупа фактчекинга)**
[L] Подтверждено существование всех 11 мест: ст. 1:83, 2:36, 17:80, 23:36, 23:37, 29:31, 30:50, 31:170, 34:124, 34:125, 38:50. Передать редактору.

### C13. Код-примеры
- J-H3, J-H7 — см. § 2.
- **ст. 18 бенчмарки**: файл не назван, `package main` + `import "testing"` — `go test` ищет бенчмарки только в `*_test.go` (поведение `go test`, **PARTIALLY CORRECT** как инструкция; в моём прогоне код помещён в `m_test.go`). Результат: **ряд 7,5 мс (≈ 7,1 мс в тексте) ✓; столбец 84 мс против «136 мс»; отношение ≈ 11×, а не «≈ 19×»** — **PARTIALLY CORRECT** (порядок величин верен, заявленный множитель на той же модели CPU не воспроизведён). Диапазон «5–20×» — **CONTEXT-DEPENDENT**.
- **ст. 37:72 `write` 100 байт с `O_DIRECT|O_SYNC` даёт EINVAL** — **CONTEXT-DEPENDENT** [R][L]: `open(2)`: «alignment restrictions vary by filesystem and kernel version and might be absent entirely»; «misaligned O_DIRECT I/Os … can either fail with EINVAL or fall back to buffered I/O». На btrfs (Linux 7.2.8) такая запись **завершилась без ошибки**. Текст ст. 37 приводит `write` лишь как иллюстрацию усиления записи (WAF ≈ 40) — сам расчёт `4096/100` — **VERIFIED** [Л].
- ст. 5 `TCPMachine` + `RWMutex` — **OPINION** («для максимальной производительности» — рекомендация, поданная как факт).

### C14. False sharing / padding / `sync.Pool`
- **ст. 21:201 «128 байт, чтобы нейтрализовать спаренные запросы prefetcher'ов»** — **PARTIALLY CORRECT** [L]: комментарий в `sync/pool.go:76–77`: «Prevents false sharing on widespread platforms with 128 mod (cache line size) = 0». Про prefetcher там ничего нет.
- «Штраф 50 нс» — **NOT CHECKED**. `CacheLinePadSize` совпадает с `internal/cpu` — **NOT CHECKED**.

---

## 5. Medium по статьям

Статус относится к утверждению в тексте. Ссылки «→ Cn» значат, что вердикт дан в кластере выше.

### Ст. 1
| ID | Статус | Основание |
|---|---|---|
| 1-a `fork()` в `go run` | **PARTIALLY CORRECT** | [L] `syscall/exec_linux.go:309, 858`: `CLONE_VFORK \| CLONE_VM`; запуск бинарника делает `go` через `os/exec`, не shell. Для `./main` из shell верно |
| 1-b bootstrap | → J-H1 | |
| 1-c g0 | → K1 | |
| 1-d 500 мкс | → K14 | |
| PGO: preview 1.20, GA 1.21, «2–14 %» (1.22), hot-block alignment 1.23 | **VERIFIED** [R] | 1.20: «preview support»; 1.21: «added as a preview in Go 1.20, is now ready for general use»; 1.22: «between 2 and 14 % improvement»; 1.23: «align certain hot blocks in loops … 1–1.5 %», только 386/amd64 |
| `go run` и `$GOTMPDIR` | **VERIFIED** [L] | `helpdoc.go:622` |
| Статическая линковка, динамическая при cgo | **CONTEXT-DEPENDENT** [L] | `cfg.go:140–184`: с Go 1.20 cgo отключается автоматически, если нет C-компилятора |
| IR-фаза: escape analysis, инлайнинг, девиртуализация до SSA | **NOT CHECKED** | не открывал `cmd/compile`; общепринятая схема |
| Fault-around | **NOT CHECKED** | |

### Ст. 2
| ID | Статус | Основание |
|---|---|---|
| 2-a утечка = «квантовое туннелирование» | **NOT CHECKED** | предварительно **PARTIALLY CORRECT** [K] (FinFET: доминирует подпороговая утечка; затворная подавлена high-k) |
| 2-b подпись «TTL / LVCMOS» при 1.2/0.8/0.4 В | **NOT CHECKED** | JESD8 не открывал |
| 2-c «lock-free … как в `sync.Mutex`» | **INCORRECT** [L] | мьютекс блокирующий (паркуется на `sema`), lock-free только быстрый путь `CompareAndSwap` (`internal/sync/mutex.go`) |
| 2-d сдвиги | **VERIFIED** (поведение Go) [L] | `uint32(1)<<40 == 0`, `int32(-8)>>40 == -1`, отрицательный счётчик → `panic: runtime error: negative shift amount`. В тексте это не сказано (пропуск) |
| `atomic.And/Or` с Go 1.23 | **VERIFIED** [R] | |
| Атомики Go определены от 32 бит | **VERIFIED** [L] | нет `atomic.Uint8` |
| `-7 >> 1 == -4`, `-7 / 2 == -3` | **VERIFIED** [L] (по спецификации) | |
| `mutex`: два поля, `sema` | **VERIFIED** [L] | `state int32; sema uint32` |

### Ст. 3
| 3-a (C2) | **PARTIALLY CORRECT** | → K6 |
| 3-b CF/OF | **VERIFIED** (текст) | → K6 |

### Ст. 4
| ID | Статус | Основание |
|---|---|---|
| 4-a SR-триггер: «NOR или NAND, запрещено S=1,R=1» | **PARTIALLY CORRECT** [Л] | у NOR-защёлки запрещено S=R=1. У NAND-защёлки с активным нулём — S̄=R̄=0 (оба выхода 1, затем неопределённость). Утверждение верно, если вход NAND-защёлки мыслить как инвертированный |
| 4-b tREFI ≈ 7,8 мкс | **PARTIALLY CORRECT** [W] | tREFI ≈ 7,8 мкс — DDR3/DDR4; для DDR5 **3,9 мкс** при 0–85 °C, 1,95 мкс при > 85 °C (datasheets DDR5, выдача поиска; JESD79-5 не открывал). Окно 64 мс подтверждается. Текст описывает «период примерно 7,8 мкс» без привязки к поколению → **OUTDATED** для DDR5 |
| 4-c интервью про аллокации | **NOT CHECKED** | `mallocgc`, mark assist, write barrier; в `runtime/malloc.go` присутствуют, но объяснение причин p99 — редакторское |
| 4-d `DFlipFlop` | → J-H3 | |

### Ст. 5
| 5-a RIP | **PARTIALLY CORRECT** [Л] | строка 94: «следующую команду»; строка 356: «текущей исполняемой» → внутреннее противоречие. Для x86-64 при исполнении `RIP` указывает на следующую инструкцию [K]; для ARM64 `PC` — текущая [K]. `NOT CHECKED` по SDM |

### Ст. 6
| 6-a память–память | **PARTIALLY CORRECT** | `MOVS`/`CMPS`/`PUSH m`/`POP m` существуют [K]; текст говорит об арифметике → корректно в этом контексте |
| 6-b | → C2 | |
| 6-c, 6-d, 6-e | → C3 | |

### Ст. 7 — 7-a → C4. Ст. 8
| 8-a | → C9 (**INCORRECT**, L3 = 30 МиБ) | |
| 8-b ELF для «Apple Silicon» | **INCORRECT** [Л] | в самой ст. 1:49 сказано «Mach-O в macOS»; диаграмма ст. 8 ставит ELF на «Apple Silicon». Формат Mach-O для `darwin/arm64` по существу общеизвестен [K], но противоречие внутри модуля подтверждено текстом |
| 8-c | → C5 | |
| 8-d | → C1 | |
| 8-e | → J-H6 | |
| System/360 «под руководством Брукса и Амдала» | **PARTIALLY CORRECT** [K] | пропущен Блау (Amdahl–Blaauw–Brooks) |
| Томпсон и Пайк — разработчики Plan 9, Гризмер — нет | **NOT CHECKED** (общеизвестно) | |
| `FP`, `SB`, `SP`, `PC` — 4 псевдорегистра | **VERIFIED** [L] | `doc/asm.html` |

### Ст. 9
| 9-a `LEA` «за один такт» | **CONTEXT-DEPENDENT** | трёхкомпонентный `LEA` на Intel до Ice Lake — 3 такта [K]; `NOT CHECKED` по uops.info |
| 9-b `x-8(SP)` | **VERIFIED** | → K5 |

### Ст. 11 — 11-a «EX в такте 3» — **INCORRECT** [Л]: по таблице самой статьи (`IF` такт 2, `ID` такт 3) `EX` приходится на такт 4. Два пузыря в таблице соответствуют классическому конвейеру (чтение регистров после WB). Остальная таблица согласована.

### Ст. 12
| 12-a | → J-H2 | |
| 12-b Itanium = VLIW | **NOT CHECKED** | предварительно **PARTIALLY CORRECT** [K]: EPIC |
| 12-c окно OoO | **NOT CHECKED** | пропуск, не ошибка |

### Ст. 13
| 13-a `CMOV` и `crypto/subtle` | **INCORRECT** [L] | `grep CMOV crypto/subtle/*.go` — пусто; пакет на масках. `WithDataIndependentTiming` — Go 1.24 **VERIFIED** [R]; но по godoc «On Arm64 processors with FEAT_DIT … enables PSTATE.DIT»; «on all other architectures … executes f immediately with no other side-effects» (`dit.go:33–38`). Статья пишет о включении DIT у процессора без оговорки |
| 13-b | → J-H3 | |
| Spectre: январь 2018, потери 15–20 % | **CONTEXT-DEPENDENT** | дата — общеизвестно; число — `NOT CHECKED` |
| `-spectre=index,ret` | **VERIFIED** [L] | `go tool compile -h`: «-spectre list … (all, index, ret)» |

### Ст. 14 — 14-a → K10 (**VERIFIED** для 1.26). Флинн в 1966 в Стэнфорде — **NOT CHECKED** (Wikipedia не содержит должности в 1966).

### Ст. 15
| 15-a «SSE3/SSE4.2 гарантированы на x86-64» | **INCORRECT** [R] | `go.dev/wiki/MinimumRequirements`: `GOAMD64=v1` — «instructions that all 64-bit x86 processors can execute»; SSE3, SSE4.1, SSE4.2, SSSE3, POPCNT, CMPXCHG16B — с `v2`; AVX, AVX2, BMI1/2, FMA, MOVBE — с `v3`; AVX512 — `v4`. [L] `go help environment`: default `v1` |
| 15-b | → K8 | |
| 15-c | → C3 | |

### Ст. 16
| 16-a «главная причина медлительности C++ — оптимизации и автовекторизация» | **INCORRECT** [R] | Pike: «The construction of a single C++ binary … can open and read hundreds of individual header files tens of thousands of times»; ~2000-кратное раздувание через `#include`; шаблоны; автовекторизация не упоминается. «45 минут» — **VERIFIED** («It was during one of those 45 minute builds that Go was conceived») |
| 16-b aliasing «непреодолимо / неразрешимо» | **NOT CHECKED** | предварительно **PARTIALLY CORRECT** [K] (runtime-проверки перекрытия) |
| `gobuf` — шесть слов | **VERIFIED** [L] | `runtime2.go`: `sp, pc, g, ctxt, lr, bp` |
| «ни GPR, ни YMM/ZMM при `gogo`/`mcall` не сохраняются» | **VERIFIED** [L] по составу `gobuf` | |

### Ст. 17
| 17-a Kanev и «Go-сервисы» | **INCORRECT** [R] | PDF статьи: «We focus these studies on code written in C++»; Go в профилировании не упомянут. «20–40 % ожидания бэкенда» — **INCORRECT**: «The majority of these stall slots are clearly due to back-end pressures – except for search2 and search3, more than 60 % of µop slots are held up due to the back-end» |

### Ст. 18 — 18-a → C9; 18-b → C13; 18-c «80 нс замораживает конвейер» — **PARTIALLY CORRECT** [Л]: в самой статье 136 мс / 16,8 млн ≈ 8 нс на элемент; MLP перекрывает промахи (**NOT CHECKED** по Intel manual). 18-d «невыровненная переменная окажется на границе линий» — **PARTIALLY CORRECT** [K] (Go-выравнивание исключает пересечение для скаляров ≤ 8 Б; split возможен при `unsafe`/packed), `NOT CHECKED` по spec.

### Ст. 19 — 19-a (Tag 52 / Set 6 / Offset 6; VIPT) — **NOT CHECKED**; L1d: [L] 64 sets × 12-way × 64 B = 48 КиБ — подтверждает ограничение VIPT 4 КБ × ways не 8-way. 19-b → C9. 19-c арена — **CONTEXT-DEPENDENT**; «`arena` приостановлен» — **NOT CHECKED**.

### Ст. 20 — 20-a → C5. Ст. 21 — 21-a → C14. Ст. 22 — 22-a → C5; Apple M TSO-режим — **NOT CHECKED**.

### Ст. 23 — 23-a → C7; 23-b → K2 (**PARTIALLY CORRECT**); «ABA нивелируется GC» — **PARTIALLY CORRECT** [Л]: GC не запрещает повторного использования адресов, если объект вернули в `sync.Pool` или пул свободных узлов; для узлов, выделяемых `new`, адрес не переиспользуется, пока на него есть ссылка.

### Ст. 24 — 24-a → C5; 24-b → J-H5; **24-c VERIFIED** (версии `sync.Once.done`).

### Ст. 25
| 25-a bus 8 байт | **NOT CHECKED** | упрощение |
| 25-b `CMPXCHG8B` | **PARTIALLY CORRECT** | строка 214 «аппаратно требовали строгого 8-байтного выравнивания» — **NOT CHECKED** по Intel SDM (предварительно **INCORRECT**: инструкция выравнивания не требует, невыровненная `LOCK`-операция дорога/вызывает split-lock; внутри ст. 25 строки 214 и 219 противоречат друг другу — подтверждено чтением). Строка 219 «с Go 1.19 используйте `atomic.Int64`, тип несёт `align64`» — **VERIFIED** [L][R] (`sync/atomic/type.go:109, 176`; Go 1.19 notes: `atomic.Int64`); `sync/atomic/doc.go:64–69`: «types Int64 and Uint64 are automatically aligned» |
| 25-c «сортируйте по убыванию размера» | **PARTIALLY CORRECT** [L] | `{x [5]byte; z int32; y int16}` (по размеру) = **16 Б**, `{z int32; y int16; x [5]byte}` (по выравниванию) = **12 Б**. Для скаляров размер и выравнивание совпадают, и правило работает; с массивами и вложенными структурами — нет. Пример ст. 25 (`int64, bool, bool` = 16 Б) **VERIFIED** [Л] |
| 25-d `fieldalignment -fix` | **NOT CHECKED** | пропуск |

### Ст. 26 — 26-a → K3 (**PARTIALLY CORRECT**). **26-b: «TIFF, WAV или протокол JVM содержат маркерные поля»**: **PARTIALLY CORRECT**. JVM — **INCORRECT** [R] (JVMS §4: «Multibyte data items are always stored in big-endian order», маркера порядка байт нет). TIFF (`II`/`MM`) и RIFF/WAV — **NOT CHECKED**. `binary.NativeEndian` в Go 1.21 — **VERIFIED** [R].

### Ст. 27 — 27-a → C11; 27-b → C11.
### Ст. 28 — 28-a → C11; 28-b → C10.
### Ст. 29 — 29-a → C9; 29-b → C11.
### Ст. 30 — J-H4.

### Ст. 31
| 31-a «p99 сокращается в 2–3 раза» | **OPINION / NOT CHECKED** | число без источника |
| «70–90 / 140–200+ нс» (локальная/удалённая NUMA) | **NOT CHECKED** | |

### Ст. 32
| 32-a | → C9 | |
| 32-b «чётные физические ядра» | **CONTEXT-DEPENDENT** [L] | на этой машине `thread_siblings_list` у CPU 0 и 1 = `0-1`, то есть сиблинги соседние, а CPU 16 (E-ядро) без пары. Нумерация зависит от платформы |
| 32-c L1TF/MDS | **PARTIALLY CORRECT** [R] | `docs.kernel.org/admin-guide/hw-vuln/l1tf.html`: L1TF — доступ к данным **в L1D**, SMT критичен («Hyperthreads … share the L1D»), митигации `nosmt` и L1D flush. `mds.html`: MDS — утечка из **store/fill buffers и load ports**, «not directly from L1D». Статья объединяет их как «подсматривать строки в L1 другой VM» |
| 32-d | → K13 | |
| «GOMAXPROCS = логических ядер»; `sched_getaffinity` | **VERIFIED** (поведение) [R][K] | release notes 1.25; `osinit` использует affinity |
| «Каждая P закрепится за отдельным потоком ОС (M)» | **PARTIALLY CORRECT** [L] | P и M не связаны намертво: при блокирующем syscall `retake`/`handoffp` отдаёт P другому M, M может быть больше P (`proc.go`, `retake`). **Новая находка** |
| Прирост SMT 15–30 % | **CONTEXT-DEPENDENT** | Marr 2002 даёт 25 % для P4 [R]; современные значения `NOT CHECKED` |

### Ст. 33 — 33-a → C7; 33-b → C9.
### Ст. 34 — 34-a → C10; 34-b → K11.

### Ст. 35
| 35-a DDIO / некогерентный DMA | **NOT CHECKED** | пропуск, не ошибка |

### Ст. 36
| 36-a «стек Linux захлёбывается: миллионы прерываний, 100 % CPU» | **PARTIALLY CORRECT** | [K] NAPI и interrupt moderation; `NOT CHECKED` по `napi.rst`. Фраза «задержка падает с 30–50 до 1–2 мкс» — **NOT CHECKED** |
| 36-b | **NOT CHECKED** | G17 |

### Ст. 37
| 37-a | → C13 | |
| 37-b «подавляющее большинство БД — LSM» | **PARTIALLY CORRECT** | вопрос в тексте сужен до «распределённых БД и хранилищ временных рядов (Cassandra, RocksDB, ClickHouse, BadgerDB, Pebble)» — это LSM-подобные [K]. Оговорка про WAF LSM (10–30× против единиц) есть. Формулировка «подавляющее» остаётся **OPINION**; PostgreSQL/InnoDB названы как B-Tree в том же предложении |

### Ст. 38 — 38-a → K14, C8; 38-b → C6; 38-c → C8.

### Ст. 39
| 39-a `ρ/(1−ρ)` | **CONTEXT-DEPENDENT** | формула для M/M/1; для M/M/c ожидание при том же ρ меньше (Erlang C). Правило «60–70 %» — эвристика. `NOT CHECKED` по Harchol-Balter |
| 39-b S(10) | **INCORRECT** [Л][L] | 1/(0,05 + 0,95/10) = **6,897 ≈ 6,9×** (текст: 6,8×). Остальные значения **VERIFIED**: S(32) = 12,55, S(64) = 15,42, прирост 23 %, S(1000) = 19,63 |
| 39-c RWMutex `LOCK CMPXCHG` | **INCORRECT** (деталь) [L] | `RLock` = `rw.readerCount.Add(1)` (`rwmutex.go:72`), то есть `LOCK XADD`, а не `CMPXCHG`. Для `Lock`/`RUnlock` картина другая |
| 39-d | → K12 | |

### Ст. 40
| 40-a «передача по значению быстрее в подавляющем большинстве» | **INCORRECT** (внутреннее противоречие) | ст. 40:67 против ст. 17:199–207 («Однозначного ответа нет … “по значению почти всегда быстрее” было бы неверным обобщением») — обе цитаты найдены. Для 128-байтной структуры по ABI — стек (**VERIFIED**) |
| 40-b | → J-H7 | |
| 40-c | → K7 | |
| 40-d «ровно 0 тактов» на выделение стека | **OPINION / гипербола** | |

### Ст. 41 — 41-a → C6; 41-b → C10.

---

## 6. Подтверждения отклонений судьи (R1–R9) и спорные места

| # | Решение судьи | Моя проверка |
|---|---|---|
| R1 (`x-8(SP)`) | отклонено | **подтверждаю** [L] `doc/asm.html` |
| R2 (CF/OF) | отклонено | **подтверждаю** по тексту ст. 3; остаток про «прямой доступ к CF» (см. K6) |
| R3 (`sync.Mutex`) | отклонено | **подтверждаю** [L][R] |
| R4 (`g0` = 8 КБ) | отклонено | **подтверждаю** [L] `proc.go:2351` |
| R5 (`MOVBE`) | отклонено | **подтверждаю** [L] — на `v1` `BSWAPL`, на `v3` `MOVBE` |
| R6 (механика false sharing) | отклонено | **подтверждаю** [Л] |
| R7 (CGO → `entersyscallblock`) | отклонено | **подтверждаю** [L] `cgocall.go:167` |
| R8 (S:M-47 «по умолчанию LL/SC») | отклонено | **подтверждаю** [L] — по умолчанию runtime-ветка с LSE |
| R9 (Бонер «не автор») | отклонено | не перепроверял (`NOT CHECKED`) |

Бриф **недооценил** J-H6: он предлагал «если заглушки нет — VERIFIED». Заглушка есть в `go-sqlite3`, а для `confluent-kafka-go` сообщение другое. Оба варианта отличаются от текста.

---

## 7. Новые находки, которых нет в брифе

1. **ст. 6:181 «5–15 %»** — бриф отметил противоречие 181/214, но не указал, какое число верно: верно «≈ 5 %» на amd64 (Go 1.17) и «≥ 10 %» на arm64/ppc64 (Go 1.18) [R].
2. **ст. 17 — Kanev:** бриф просил «сверить 20–40 %»; первоисточник говорит о **> 60 %** back-end-bound слотов для большинства задач и о **C++** [R].
3. **ст. 18 — «≈ 19×»:** на i9-12900K (той же модели, что в тексте) воспроизводится ≈ 11× (84 мс вместо 136 мс) [L].
4. **ст. 13 — DIT:** `WithDataIndependentTiming` — no-op вне arm64 [L].
5. **ст. 37 — O_DIRECT:** на btrfs 100-байтная запись с `O_DIRECT\|O_SYNC` прошла без ошибки [L][R].
6. **ст. 32 — «каждая P закрепится за отдельным M»** — неверно [L].
7. **ст. 16 — Pike:** бриф пометил это как ФАКТ/МНЕНИЕ; первоисточник однозначно говорит о заголовках и зависимостях [R].
8. **ст. 15 — «сгорит за миллисекунды»** без защиты — преувеличение (K8).
9. **ст. 8 — Mach-O для Apple Silicon:** подтверждено; в ст. 1:49 про Mach-O для macOS сказано верно, то есть **внутри модуля противоречие**.
10. **ст. 7:161 — глобальная очередь:** `goschedImpl` при `preempted && sched.gcwaiting` кладёт горутину в `runnext` локального P (случай STW), иначе — в глобальную очередь (`proc.go:4346–4353`). Бриф упоминает только вторую ветку.

---

## 8. NOT CHECKED: что осталось

**Не проверено, т. к. нужен недоступный первоисточник или нет бесплатного доступа:**
- Intel SDM / Agner Fog / uops.info: латентности `LEA`, `IDIV`, `MUL`; `RIP` при исполнении; `CMPXCHG8B`; MLP и line fill buffers; store-to-load forwarding; число декодеров и размеры ROB/PRF у Zen 4/5, Golden Cove, Apple M3.
- JEDEC (JESD79-5, JESD8): точные tREFI для DDR5, уровни логики; DDR3/DDR4.
- Chips and Cheese / Intel optimization manual: размеры DTLB/STLB, кольцо/mesh, L2/L3 «локальность», latency core-to-core, AVX-512 licenses (цифры 4.8/4.3/3.2).
- Linux: `memory.max`/cgroup OOM; NAPI; поведение KPTI/IBRS/IBPB в syscall; PCID (6 ASID).
- История вычислительной техники: Flynn 1966, System/360, UNIVAC/DYSEAC и прерывания, PDP-7/PDP-11, германиевый/кремниевый транзистор.
- Go: NUMA-латентности «70–90 / 140–200 нс», `GC`-воркеры как горутины, issue #28808, `arena`, `fieldalignment -fix`, Swiss Tables (`maps.AlgInit`) и SIMD.
- Мелкие: `XORL` в выводе Go-asm, `DUFFZERO` в новых версиях, «ровно один syscall на блок 4 КБ у `bufio`», Zen 5c, «700–800 мм²».

**Low-пункты брифа из § 7**, не вошедшие в кластеры и Medium выше (≈ 105 из ≈ 120), остаются `NOT CHECKED`. Предварительные оценки судьи (✓/~/✗) не подтверждены мной. Из Low проверены и закрыты: ст. 1 (PGO, `GOTMPDIR`, ABI), ст. 2 (`&^`/`atomic.And`), ст. 8 (Mach-O, Plan 9 псевдорегистры), ст. 24 (версии `sync.Once`), ст. 26 (JVM, `NativeEndian`), ст. 27 (стек и адаптивный старт), ст. 28 (`MADV_DONTNEED` 1.16), ст. 30 (`disablethp`), ст. 32 (SMT-нумерация), ст. 39 (S(10)), ст. 21 (`sync/pool.go`).

---

## 9. Приоритеты для редактора

1. **Исправить, не требуя спорной оценки:** J-H1 (порядок бутстрапа), J-H2 (синтаксис ассемблера), J-H3 (импорты), J-H6 (режим отказа CGO), C3 (5–15 % → ≈ 5 %), 8-b (Mach-O), 13-a (`CMOV`/DIT), 15-a (SSE-уровни), 16-a (причина медленных сборок C++), 17-a (Kanev: C++, > 60 %), 23/33 (`sync.Mutex` в канале), 39-b (6,9×), 25-b (`CMPXCHG8B`), 26-a/b (BSWAP, JVM), 11-a (такт 4), 8-a/19 (L3 30 МиБ, L1d 12-way).
2. **Переформулировать диагностику:** J-H4 (THP: `defrag` определяет компактизацию; `disablethp` не различает механизмы), J-H5 (DCL: нули, а не «мусор»), C4 (асинхронное вытеснение: `pushCall`, глобальная очередь).
3. **Добавить оговорки (CONTEXT-DEPENDENT):** K2, K10 (1.27: arm64/wasm), K13 (cgroup), K14 (500 мкс), C10 (EEVDF с 6.6), C13 (O_DIRECT, 19× → «порядка 10×»), C11 (nil: `mmap_min_addr`, явная проверка для больших смещений).
4. **Передать как техническую правку разметки:** C12 (Mermaid `:::class`).
