# Primary Fact-Check · Модуль 2 «Устройство и работа ОС»

> **Роль:** primary source-based fact checker (Sonnet 5.5).
> **Вход:** `sources/2. Устройство и работа ОС/` (63 статьи, состояние после коммита `a8006dfc`), `2-opus-judge.md` (Master Fact-Check Brief) и `2-opus-blind-spot.md` (дополнительные находки; Master Brief они не заменяют).
> **Дата проверки:** 2026-10-03. **Среда:** go1.27.1 linux/amd64 (`/usr/local/go`), `golang.org/x/sys v0.46.0`, Fedora, Linux 7.2.8, Intel Core i9-12900K (24 потока, Meltdown: *Not affected*, то есть без KPTI), файловая система `/home` — btrfs, Mermaid 10.9.1 из `builder/assets/vendor/`, Firefox headless.
> **Состояние отчёта.** §§ 0–11 описывают результат первичной проверки (на момент написания файлы модуля не менялись). Последующие правки (Mermaid, конвертер, аудит, `AGENTS.md`) отражены в § 12 и помечены ниже как «после правок»; все они закоммичены (см. § 12.7). Фактические исправления текста статей по этому отчёту **не вносились**. Все пробные программы лежали в scratchpad сессии (в репозиторий не попали).

---

## 0. Как читать отчёт

### Статусы
`VERIFIED` · `INCORRECT` · `PARTIALLY CORRECT` · `OUTDATED` · `CONTEXT-DEPENDENT` · `OPINION / NOT A FACT CLAIM` · `NOT CHECKED`

Статус относится **к утверждению в тексте модуля**, а не к претензии брифа. Если претензия брифа подтверждена, статус текста — `INCORRECT` / `PARTIALLY CORRECT` / `OUTDATED`. Если претензия отклонена, статус текста — `VERIFIED`.

### Метки доказательств
| Метка | Что это |
|---|---|
| **[L]** | Проверено на этой машине по первоисточнику: исходники Go `/usr/local/go/src`, `/usr/local/go/api/*.txt` и `doc/godebug.md`, исходники `x/sys`, man-страницы (`man 2 open`, `man 7 unix` и т. д.), `/proc`, `/sys`, `go vet`, `gofmt`, `objdump`. |
| **[E]** | **Эксперимент:** программа написана и запущена здесь. Для подсчёта системных вызовов я собрал мини-`strace` на `ptrace` (в системе нет `strace`). Поведение относится к go1.27.1 / Linux 7.2.8. |
| **[R]** | Первичный источник вне машины, открыт в этой сессии: `docs.kernel.org` и `torvalds/linux` (по тегам), release notes go.dev, документация Docker, Kubernetes, Microsoft Learn, systemd man, SPECIFICATION Firecracker, kernelnewbies, upstream ltrace. |
| **[Л]** | Арифметика или логика, проверенная расчётом. |
| **[K]** | Утверждение опирается на «общеизвестное» (Intel SDM, Tanenbaum и т. п.), которое я **в этой сессии не открывал**. Такие пункты **не считаются проверенными**: статус `NOT CHECKED`. |

### Ограничения
- Модуль — ~1,7 МБ текста (63 статьи). Целиком я его не перечитывал. Я прочитал оба брифа целиком, нашёл в статьях каждое место из § 2 (High) и § 3 (конфликты) брифа, большинство кластеров, все 15 Medium-находок blind-spot и те Medium-пункты, где доказательство добывается без закрытых источников.
- Версию Go, названную в статье, я сверял с `api/go1.N.txt` и release notes. Поведение рантайма — по исходникам и запускам **1.27.1**; где поведение зависит от версии, это оговорено.
- Всё, что требует микроархитектурных таблиц, закрытых стандартов (PCI DSS, JEDEC, Intel SDM) или устройства ядра, которое я не открывал, оставлено `NOT CHECKED` (перечень — § 10).

---

## 1. Сводка

| Группа | Всего | Текст неверен / неточен (претензия подтверждена) | Претензия отклонена или смягчена (текст верен или контекстно-зависим) | NOT CHECKED |
|---|:---:|:---:|:---:|:---:|
| High J-H1…J-H31 | 31 | 29 | 2 смягчены: J-H26 (CONTEXT-DEPENDENT), J-H28 (PARTIALLY CORRECT); внутри J-H29 одна пометка судьи ложноположительная (Нейгл) | 0 (но отдельные подпункты внутри блоков — NOT CHECKED, см. текст) |
| Конфликты K1–K12 | 12 | 12 разрешены с уликами (в K1–K3 — уточнено, K3 — **судья неправ**) | — | 0 |
| Кластеры C-* (17) | 17 | 13 подтверждены | 0 | 4 частично |
| Blind-spot B-1…B-15 (+Low B-16…B-29) | 15 (+14) | **11 подтверждены напрямую** (из них 6 — запуском: B-1, B-2, B-3, B-4, B-5, B-14), 2 — по логике кода/документации без запуска (B-7, B-12) | 0 опровергнуто | 2 (B-11, B-15) + 12 из 14 Low |
| Medium (≈320) | ≈320 | ≈60 проверено (все подтверждены или смягчены; смягчены: 1.3, 6.5, 38.2, 43.4, 62.2, 63.5) | — | ≈260 |
| Low (≈285) | ≈285 | 5 проверено (23.5, 56.6, 40.6, 5.18, 13.11 — через J-H5 и § 7) | — | ≈280 |

**Главные результаты (проверено [L]/[E]/[R]):**

1. **Подтверждены 29 из 31 High и 11 из 15 пунктов blind-spot (ещё 2 — по логике кода); опровергнутых нет.** Смягчены J-H26 (дефолт RT-throttling зависит от дистрибутива: на этой машине `sched_rt_runtime_us = 1000000`) и J-H28 (IOCP: пул потоков создаёт приложение, но остальное описание верно). Ложноположительные пометки брифа найдены в J-H29 (Нейгл) и в тезисе о ст. 62:256 / `automaxprocs` (§ 9.2).
2. **Четыре утверждения про ядро Go опровергнуты запуском:** (а) рост стека не вызывает `mmap`/`madvise` на каждое удвоение (стек вырос 0,3 МБ → 67 МБ, `madvise` +0); (б) блокировка на `sync.Mutex` и в канале не делает `futex` на каждый вызов (200 000 «парковок» → 17 `futex`); (в) Go не использует `sigwaitinfo`/`rt_sigtimedwait` для `os/signal` (0 вызовов, 114 `rt_sigaction`); (г) Go в PID 1 **не** игнорирует `SIGTERM`, а завершается с кодом 143.
3. **Подтверждены экспериментом четыре «слепых пятна» blind-spot, которые судья отклонил или не заметил:** `TCPListener.File().Fd()` делает сокет блокирующим и `Close()` зависает (B-1, судья отклонил как R4/K3); блокирующий `RawSyscall` подвешивает **весь процесс** на ближайшем GC (B-2); хук `Control` не меняет keepalive принятых соединений (B-3); `unix.Capset` сбрасывает права **одного потока из девяти** (B-4).
4. **Новое, чего нет ни в брифе, ни в blind-spot (§ 9):**
   - **13 из 172 диаграмм Mermaid модуля 2 не парсятся** в вендорном Mermaid 10.9.1 (рендер: «Syntax error in text»); по всему проекту — **61 из 2485** (64 после штатного `_sanitize_mermaid`, который сам ломает 4). Статический `audit_all.py` их не ловит. Причины, рецепт починки для editor и план внесения в скрипты — § 12; **после правок: исправлено, 0 из 2486 не разобрано, аудит чистый, всё закоммичено (§ 12.7);**
   - детектор deadlock в Go **молчит у любого бинарника с cgo** (по умолчанию это любой бинарник, импортирующий `net`);
   - вопрос Interview ст. 47 основан на неверной посылке: `ListenConfig{KeepAlive: 30s}` **не** «лишь включает SO_KEEPALIVE»;
   - код `unix.Capset` в ст. 58 при `LINUX_CAPABILITY_VERSION_3` передаёт одну структуру вместо массива из двух;
   - в `runWithPipe` (ст. 26) гонка воспроизводится: из 200 запусков 10 дали усечённый вывод;
   - ошибки в самом брифе (§ 9.2): `fs/futex.c` вообще не существовал; ст. 62 не содержит `automaxprocs`; число Go-блоков 75, а не 76; `EINVAL` при `O_DIRECT` на btrfs **не** гарантирован.
5. **Числа (C-NUM):** syscall на этой машине 62–80 нс; переключение горутин через канал ≈140 нс; переключение потоков ОС ≈0,9 мкс; DRAM 74–88 нс. Утверждения «горутина 10–20 нс» и «DRAM 20–30 нс» неверны.

---

## 2. High (J-H1 … J-H31)

Формат: **утверждение в тексте** → **статус** → **доказательство** → **комментарий о брифе**. Если у блока несколько утверждений, статус дан по каждому.

### J-H1 · Сигналы в Go: `rt_sigprocmask`, `sigwaitinfo` (ст. 28, 109–111 и 220) — **INCORRECT**
- Утверждение: «Go блокирует сигналы через `rt_sigprocmask` на всех тредах, кроме основного; на основном запускается горутина, блокирующаяся на `sigwaitinfo`» — **INCORRECT**.
- **[L]** `grep -rn sigwaitinfo /usr/local/go/src/runtime /usr/local/go/src/os/signal` — пусто. Получение сигнала — `runtime/sigqueue.go: signal_recv` (через `note`, `notetsleepg`), доставка — обработчик `sighandler → sigsend`.
- **[E]** Программа с `signal.Notify(SIGUSR1)` + `kill(self)`: **114 `rt_sigaction`**, 21 `rt_sigprocmask`, 1 `rt_sigreturn`, **0 `rt_sigtimedwait`**, 0 `rt_sigsuspend`, 0 `signalfd4`. (`sigwaitinfo` в libc — это `rt_sigtimedwait`.)
- Итог ст. 28 («рантайм берёт на себя `rt_sigaction` и `rt_sigprocmask`») — **VERIFIED**: эти вызовы действительно есть.
- Бриф прав.

### J-H2 · Рост и переполнение стека горутин (ст. 21, 19, 20) — **INCORRECT** (по каждому подпункту)
| Утверждение | Статус | Доказательство |
|---|---|---|
| `newstack` выделяет новый стек через `mmap` | **INCORRECT** | **[L]** `runtime/stack.go`: `stackalloc` берёт блок из `stackpool`/`stackcache`/`stackLarge`/`mheap`. `sysAlloc` (стр. 361) только для стеков системных потоков. |
| после копирования зовётся `madvise(MADV_DONTNEED)` — «критически важный шаг» | **INCORRECT** | **[L]** в `stack.go` нет `madvise`; старый стек уходит в `stackfree`. **[E]** `stack` рекурсия, `StackInuse` 327 КБ → **67 МБ** (≈15 удвоений): `mmap` +10 (арены кучи), **`madvise` +0** (2 в базовом запуске). |
| копирование «если там есть жизненно важные данные» | **INCORRECT** | **[L]** `copystack` копирует всегда (стр. 929–). |
| проверка называется `gostacksplit` | **INCORRECT** | **[L]** такого символа нет в исходниках. **[L]** `objdump`: пролог `CMPQ R12, 0x10(R14)` (сравнение SP с `g.stackguard0`) → `JBE morestack`. |
| «`gostartcall` восстанавливает контекст и выполняет вызов с новым стеком» (21:92) | **INCORRECT** | **[L]** `gostartcall` существует (`sys_x86.go:16` и др.), но вызывается из `gostartcallfn` (`stack.go:1231`) в `newproc1` (`proc.go:5391`) при **создании** горутины, а не при росте стека. |
| лимит стека — `ulimit -v` / `RLIMIT_AS` | **INCORRECT** | **[L]** `runtime/proc.go:164`: `maxstacksize = 1000000000` (64-bit), меняется `debug.SetMaxStack`. В 1.27.1 есть ещё `maxstackceiling = 2*maxstacksize`. |
| «Это не паника, а `SIGSEGV`, перехваченный рантаймом» (21:136); «контролируемое завершение через panic» (20:155) | **INCORRECT** | **[L]** `stack.go:1202`: `print("runtime: goroutine stack exceeds …-byte limit")`, `throw("stack overflow")`. **[E]** бесконечная рекурсия: `fatal error: stack overflow`, **exit 2**, сигнала нет. Это `throw` (fatal error), не паника. |
| `go tool pprof -top http://host/debug/pprof/stack` | **INCORRECT** | **[L]** профили `runtime/pprof`: `goroutine`, `goroutineleak`, `threadcreate`, `heap`, `allocs`, `block`, `mutex`. Профиля `stack` нет. |
| `//go:nosplit` как «защита от рекурсии» (21:185–194) | **INCORRECT** | **[L]** `cmd/link/internal/ld/stackcheck.go:104`: линкер сообщает `nosplit stack over N byte limit`. `nosplit` убирает проверку роста, а не защищает; рекурсия в nosplit-цепочке отклоняется на линковке. |
| «стек защищён guard page» (ст. 19) | **PARTIALLY CORRECT** | Guard page — механизм потока ОС (`pthread`/главный поток). Для горутинного стека переполнение ловит пролог функции (`stackguard0`), не MMU. |
| Итог 3: «рантайм использует `mmap` + `madvise(MADV_DONTNEED)` для роста стека» | **INCORRECT** | см. выше. |
- Бриф добавил, что Gemini неточно описал `stackcache` «2–32 КБ». **[L]** `malloc.go:136,150`: `_StackCacheSize = 32 KiB`, `_NumStackOrders = 4` → пулы 2/4/8/16 КБ. Бриф прав.
- Контекст (blind-spot B-14, **[E]**): в контейнере с `MemoryMax=512M` та же рекурсия кончается **`SIGKILL` (exit 137) без единой строки диагностики**, потому что при последнем удвоении 256→512 МБ нужно ≈768 МБ. Без лимита: `fatal error: stack overflow`, exit 2.

### J-H3 · «`sync.Mutex` и каналы построены на futex» (ст. 1, 3, 22, 23, 24, 32, 34, 60, 63) — **INCORRECT** (в формулировке «блокировка = `futex(FUTEX_WAIT)`»)
- **[L]** `internal/sync/mutex.go:149`: `lockSlow` → `runtime_SemacquireMutex`. `runtime/sema.go:192`: `goparkunlock(&root.lock, …)`. `runtime/chan.go:283`: `gopark(chanparkcommit, …)`. В `sema.go` и `chan.go` вызовов futex нет (в `sema.go:9` — комментарий «targets the same goal as Linux's futex»).
- **[E]** `GOMAXPROCS=1`, 8 горутин, критическая секция с `runtime.Gosched()` (остальные массово паркуются на мьютексе): 200 000 захватов → **17 `futex` на весь процесс**. Канальный ping-pong 200 000 раз → 15 `futex`. Базовый старт даёт 5. То есть парковка горутины не делает `futex`.
- **Что верно (нюанс, которого нет в статьях и в брифе):** внутренние `lock()` рантайма (на них стоят `semaRoot.lock` и `hchan.lock`) при **конкуренции за сам runtime-lock** засыпают через `semasleep → futexsleep` (`runtime/lock_spinbit.go:259`, `lock_futex.go`). Простаивающий M тоже спит на futex (`notesleep`). Поэтому «futex где-то под капотом есть» — `PARTIALLY CORRECT`; «блокировка горутины на мьютексе/канале = `futex(WAIT)`» — `INCORRECT`.
- Затронуто: 23:45, Interview Q3 ст. 23; 24:145; 3:190–192; 1:71 (канал = `hchan` + **netpoller** — netpoller каналы не используют, **INCORRECT**); таблица ст. 63. Верная версия уже в 23:79–88 и в ст. 33. Бриф прав.

### J-H4 · `GOMAXPROCS`, cgroup, `automaxprocs` (ст. 1, 8, 52, 54, 62, 63) — **OUTDATED** (+ противоречие внутри модуля)
- **[L]** `runtime/debug.go:20–45` и `doc/godebug.md:251–258`: «Go 1.25 added a new `containermaxprocs` setting»; значение по умолчанию 1 учитывает квоту cgroup CPU и **периодически обновляется**; `containermaxprocs=0` и `updatemaxprocs=0` — по умолчанию для языковой версии `go ≤ 1.24` в `go.mod` (`internal/godebugs/table.go:30,71`, `Changed: 25`).
- **[E]** `systemd-run --user --scope -p CPUQuota=200%`: модуль с `go 1.27` → `NumCPU 24, GOMAXPROCS 2`; тот же код с `go 1.24` в `go.mod` → `GOMAXPROCS 24`. Бриф описал нюанс верно.
- Утверждения:
  - 8:134, 192: «Всегда подключайте `go.uber.org/automaxprocs`» — **OUTDATED** (нужен только при `go` < 1.25 в `go.mod`; явный `GOMAXPROCS` отключает автообновление).
  - 8:132: «`runtime.NumCPU()` возвращает физические ядра хост-ноды» — **INCORRECT**: **[L]** `runtime/os_linux.go: getCPUCount` читает `sched_getaffinity`, то есть логические CPU из маски потока (в этом эксперименте `NumCPU` = 24 при 16 физических ядрах и 24 логических процессорах).
  - 52:265: «Go не распознаёт лимиты cgroups автоматически без явного указания `GOMEMLIMIT` и `GOMAXPROCS`» — **OUTDATED** для `GOMAXPROCS` (с 1.25), **VERIFIED** для памяти (`GOMEMLIMIT` вручную: `SetMemoryLimit` по умолчанию `MaxInt64`).
  - 54:150 («Начиная с Go 1.25… `containermaxprocs`, `runtime/cgroup_linux.go`») — **VERIFIED** (файл существует, версия верна). Но Итог 3 ст. 54 («явная настройка `GOMAXPROCS`») — **OUTDATED** и противоречит 54:150.
- **Ошибка брифа:** бриф утверждает, что 62:256 рекомендует `uber-go/automaxprocs`. **[L]** `grep -n -i uber` по ст. 62 даёт только 62:149 и 62:256, а слова `automaxprocs` в ст. 62 нет. В ст. 62:256 речь о другом (`GOMAXPROCS` выше числа ядер). Автомаксипрокс рекомендуют ст. 8 и 54.

### J-H5 · Несуществующие API, флаги, идентификаторы — **INCORRECT** (все строки таблицы подтверждены)

| Ст. | Что в тексте | Статус | Доказательство |
|---|---|---|---|
| 11 | `GODEBUG=gcresidency=1` «в Go 1.21+» | **INCORRECT** | **[L]** нет в `runtime1.go` (`dbgvars`), `godebugs/table.go`, нигде в `src/`. Неизвестные ключи `GODEBUG` Go молча игнорирует. |
| 13 | `GODEBUG=pagealloc=1` | **INCORRECT** | **[L]** нет в `dbgvars`; реальный — `disablethp` (есть). |
| 13 | `MHeapMap_SpanInUse` | **INCORRECT** (в современном Go) | **[L]** нет в `src/`. Историческое существование не проверял — `NOT CHECKED`. |
| 17 | `debug.MemoryLimit()` | **INCORRECT** | **[L]** `runtime/debug/garbage.go:234`: только `SetMemoryLimit(limit int64) int64`; `SetMemoryLimit(-1)` возвращает текущее. |
| 9 | «`sched_gomaxprocs`» | **INCORRECT** | **[L]** нет в `src/`. |
| 20 | `GOEXPERIMENT=framepointer`, `stkblk` | **INCORRECT** | **[L]** `internal/buildcfg/exp.go:44–51`: «used to be an experiment, but now it's always enabled»; `stkblk` нет в `src/`. См. J-H19. |
| 21 | `gostacksplit`, `/debug/pprof/stack` | **INCORRECT** | см. J-H2. |
| 25 | `os.NewFile(int32(42), …)` | **INCORRECT** | **[L]** `os/file.go:133`: `NewFile(fd uintptr, name string)`. |
| 26 | `fds, err := syscall.Pipe2([]int{0,1}, …)` | **INCORRECT** | **[L]** `syscall_linux.go:295`: `Pipe2(p []int, flags int) error`. |
| 29 | `go-systemd/v22/sdnotify` | **INCORRECT** | **[R]** `pkg.go.dev/github.com/coreos/go-systemd/v22/sdnotify` → 404, `…/daemon` → 200; proxy: latest v22.7.0. Ст. 30 использует `daemon` верно. |
| 32 | `syscall.ShmOpen/ShmSetSize/ShmUnlink` | **INCORRECT** | **[L]** `go vet`: `undefined: syscall.ShmOpen`. |
| 33 | «пакет `sync/semaphore` с Go 1.21» | **INCORRECT** | **[L]** в `src/sync/` нет `semaphore`; есть только `golang.org/x/sync/semaphore`. |
| 34 | `GODEBUG=asyncpreempt=1`; `go tool pprof -goroutine` | **INCORRECT** | **[L]** в `dbgvars` есть `asyncpreemptoff`, `asyncpreempt` нет; `go tool pprof -h` не содержит `-goroutine`. |
| 36, 38, 47, 48 | `runtime.wakeG`, `netpollLock`, `netpollwake`, `runtime.park`, `type netpoller struct` | **INCORRECT** | **[L]** `wakeG`, `netpollLock`, `type netpoller` не найдены в `runtime/`, `net/`, `internal/poll`; `netpollwake` есть **только** в `netpoll_aix.go`; функции `park` в рантайме нет (есть `gopark`, `park_m`). |
| 37 | `netpollkqueue.go`, `netpollwindows.go`, `netpollLink` | **INCORRECT** | **[L]** файлы называются `netpoll_kqueue.go`, `netpoll_windows.go`; `netpollLink` нет. |
| 42 | `os.O_DIRECT` | **INCORRECT** | **[L]** `go vet`: `undefined: os.O_DIRECT`; есть `syscall.O_DIRECT = 0x4000`. |
| 47, 48 | `net.ListenConfig{Backlog: …}` | **INCORRECT** | **[L]** `net/dial.go`: поля нет. |
| 49 | `SO_MAX_CONN`; `SetsockoptInt(…, SOL_SOCKET, 1024, 65535)` | **INCORRECT** | **[L]** `SO_MAX_CONN` нет ни в `x/sys/unix`, ни в `include/uapi/asm-generic/socket.h` **[R]**; номера 1024 на `SOL_SOCKET` нет. Backlog — только аргумент `listen(2)`. |
| 51 | `GODEBUG=netdns=experimentalgo` | **INCORRECT** | **[L]** `net/conf.go:486–` (разбор `netdns`): `go`, `cgo`, `1`, `2`, сочетания `go+1`; значения `experimentalgo` нет. |
| 57 | `syscall.CAP_CLEAR`; `NoSetuid/NoSetgid` | **INCORRECT** | **[L]** нет в `syscall`; в `SysProcAttr` есть `AmbientCaps`, в `Credential` — `NoSetGroups`. |
| 57 | `github.com/capabilities/cap` | **INCORRECT** | **[R]** pkg.go.dev → 404. |
| 58 | `unix.CapHeader/CapData` | **INCORRECT** | **[L]** `go vet`: `undefined: unix.CapHeader`; в `x/sys` — `CapUserHeader`, `CapUserData`. |
| 59 | `dlv core … heap` | **INCORRECT** | **[R]** `Documentation/cli/README.md` Delve: команды `heap` нет. `golang.org/x/debug/cmd/viewcore` существует (HTTP 200). |
| 29 | `http.NewServer()` | **INCORRECT** | **[L]** есть `httptest.NewServer` и `http.NewServeMux`, `http.NewServer` нет. |
| 53 | `runtime.Grow` | **INCORRECT** | **[L]** нет. |
| 40 | `fs.ReadStat` | **INCORRECT** | **[L]** нет. |
| 5 | `runtime.forkExec` | **INCORRECT** | **[L]** есть `syscall.forkExec` (`exec_unix.go:143`) и `forkAndExecInChild`. |
| 23 | `src/runtime/sys_linux_amd64.go` | **INCORRECT** | **[L]** файл — `sys_linux_amd64.s`. |
| 4 | `arch/x86/boot/head.S` | **INCORRECT** | **[R]** `torvalds/linux` master: `head.S` → 404; существуют `arch/x86/boot/header.S` и `arch/x86/boot/compressed/head_64.S`. |

### J-H6 · Не компилирующиеся листинги (кластер C-COMPILE) — **INCORRECT** (подтверждено запуском)
**[L]** В модуле **75** блоков ```` ```go ```` (бриф говорит 76), из них **46** полных программ (`package main`; бриф — 47). `go vet` (go1.27.1 + x/sys v0.46.0):
- **компилируются (17)** — совпадает с брифом: ст. 2, 5 (1-й), 14, 16 (1-й), 20, 27 (2-й), 28, 31 (1-й), 42 (1-й и 3-й), 43 (2-й и 3-й), 46, 50, 54, 55, 57;
- **разорванные строковые литералы** (`"…` + реальный перевод строки). Проверка `go/scanner` («string literal not terminated»): ст. **5, 6, 7, 10, 17, 18, 19, 27, 29, 39, 40, 44, 49, 51, 53, 56, 61** — ровно 17 статей, как у судьи (`gofmt -e` ловит только полные программы, поэтому 29 в нём не видна);
- прочие ошибки: ст. 12 и 16 (2-й): `syscall.Madvise` с 3 аргументами (сигнатура `(b []byte, advice int)`); 13: `"unsafe"` не используется; 26 (3-й) и 41: `"log"`; 31 (3-й): `"os"`; 32: `ShmOpen`; 42 (2-й): `os.O_DIRECT`; 47: `"time"`; 48: `"fmt"`; 58: `unix.CapHeader`;
- требуют сторонних модулей: ст. 29 (`sdnotify` — пакета нет), 30 (`daemon`, существует), 61 (`cilium/ebpf`).
- **[E]** Листинг ст. 61 с починенным литералом против `cilium/ebpf v0.22.0` (последняя на 2026-10-03): `"os"`, `"time"` не используются; `collection.Maps.Lookup undefined (type map[string]*ebpf.Map has no field or method Lookup)`. Ошибки, спрятанные за литералами, подтверждены.
- Фрагмент передачи FD (ст. 27): **[E]** 7 ошибок компиляции (`*os.File`→`int`, `unix.Mmsghdr`, `unix.Mhdr`, `unix.Sendmmsg` не определены, `CmsgSpace(4)` — `int`, а не `uint64`).
- Отличие от брифа: счёт 75/46 вместо 76/47 (в брифе, видимо, посчитан лишний блок; на выводы не влияет).

### J-H7 · Netpoller: `EPOLLONESHOT`, регистрация «после `EAGAIN`», `close()` → `EPOLLHUP` (ст. 38, 35, 36, 48, 63) — **INCORRECT**
- **[L]** `runtime/netpoll_epoll.go:51`: `EPOLLIN|EPOLLOUT|EPOLLRDHUP|EPOLLET`; `EPOLLONESHOT` в файле нет. 38:190 («`EPOLLONESHOT` и `EV_ONESHOT` гарантируют точечный контроль») — **INCORRECT**.
- **[E]** Простаивающий сервер: `epoll_ctl(ADD)` ровно по одному разу на fd при создании; повторных регистраций нет. Утверждение «fd регистрируется в epoll после `EAGAIN`» (ст. 35, 36, 48) — **INCORRECT**; «один раз при создании» (38, 49, 62) — **VERIFIED**.
- 63:140: локальный `close()` → `EPOLLHUP`, `Read` вернёт `io.EOF` или `EBADF` — **INCORRECT**. **[L]** `internal/poll/fd.go:16–24`: `ErrNetClosing`, «use of closed network connection».
- Бриф прав.

### J-H8 · `SOCK_DGRAM` в UDS и FD passing (ст. 27) — **INCORRECT**
- 27:20 «`SOCK_DGRAM` ненадёжный; сообщения могут теряться или приходить вне порядка» — **INCORRECT** для Linux. **[L]** `man 7 unix`: «UNIX domain datagram sockets are always reliable and don't reorder datagrams». **[E]** `socketpair(AF_UNIX, SOCK_DGRAM|SOCK_NONBLOCK)`: отправлено 278 датаграмм до `EAGAIN`, получено 278, нарушений порядка 0.
- Код FD passing — **INCORRECT**, см. J-H6 (7 ошибок компиляции). Корректный путь (`UnixRights` + `Sendmsg`, либо `WriteMsgUnix`) — в брифе указан верно, **[L]** `x/sys/unix.UnixRights` и `Sendmsg` существуют.
- Нюанс про не-Linux (BSD/macOS) — `NOT CHECKED`.

### J-H9 · `ltrace` и диагностика futex в strace (ст. 24) — **INCORRECT**
- 24:90 «`ltrace` не требует прав на `ptrace`, работает в user-space» — **INCORRECT**. **[R]** upstream `ltrace/sysdeps/linux-gnu/trace.c`: `ptrace(PTRACE_TRACEME…)`, `PTRACE_ATTACH`, `PTRACE_SETOPTIONS`, `PTRACE_DETACH`; man 1 ltrace: «See also strace(1), ptrace(2)». Ст. 24:168 (Interview) уже говорит верно — **VERIFIED**; тело статьи с ним спорит.
- 24:127 «`LD_PRELOAD` — механизм ltrace; конфликтует с аллокатором Go (`mmap` + `sbrk`-эмуляция)» — **INCORRECT** (ltrace не использует `LD_PRELOAD`; «sbrk-эмуляции» в Go нет).
- 24:144–145: «`epoll_pwait(-1)` → возможный баг netpoller»; «`futex(FUTEX_WAIT)` → захвачен mutex/channel» — **INCORRECT** как диагностическое правило. **[E]** в простаивающем сервере M спят в `epoll_pwait` с таймаутом ближайшего таймера или −1, и это норма; `futex(WAIT)` — штатный сон простаивающих M (см. J-H3).

### J-H10 · DNS-резолвер (ст. 51) — **INCORRECT** (по подпунктам)
- «`go` — дефолт для `linux`, `darwin`, `windows`» — **INCORRECT**. **[L]** `net/conf.go:167–190 goosPrefersCgo()`: `windows`, `plan9`, `darwin`, `ios`, `android` → системный резолвер. На `linux` при `cgoAvailable` выбор зависит от `LOCALDOMAIN`, `RES_OPTIONS`, `HOSTALIASES`, `nsswitch.conf` (`conf.go:131–160`).
- «`experimentalgo`» — **INCORRECT** (J-H5).
- «Go опрашивает все серверы **параллельно**» (51:128–129, 240; Итог 1, диаграмма) — **INCORRECT**. **[L]** `net/dnsclient_unix.go:312–313`: вложенный цикл `for i := 0; i < cfg.attempts; i++ { for j := …sLen … r.exchange(…) }` — перебор последовательный. Параллельно идут только запросы разных типов (A/AAAA).
- «в случае усечения (`TC`) ядро прозрачно переключается на TCP» (Итог 2) — **INCORRECT**: переключение делает не ядро, а резолвер (`exchange`, ветка `Truncated`).
- K2 (darwin): `cgo_unix.go` имеет тег `!netgo && ((cgo && unix) || darwin)`, а `cgo_unix_syscall.go` — `!netgo && darwin` (copyright 2022). Системный резолвер на darwin доступен **без cgo**; отключает его только тег `netgo`. Версию, с которой это так, я **не** подтвердил (`NOT CHECKED`; судья предлагал Go 1.20, в release notes 1.20 такой записи я не нашёл).

### J-H11 · Listen backlog (ст. 47, 48, 49) — **INCORRECT** (кроме одного пункта)
- `net.ListenConfig.Backlog` — **INCORRECT** (поля нет).
- **[L]** `net/sock_linux.go:33`: `maxListenerBacklog()` читает `/proc/sys/net/core/somaxconn`, и `listen(fd, somaxconn)` вызывает сам Go.
- «`somaxconn` по умолчанию 128» (47:232) — **OUTDATED**. **[R]** `Documentation/networking/ip-sysctl.rst`: «Defaults to 4096. (Was 128 before linux-5.4)». На этой машине `4096`. Ст. 49 («128 раньше, 4096 сейчас») — **VERIFIED**.
- «при переполнении — `ECONNREFUSED`» (ст. 48; формулировка по брифу, строку не перечитывал) — **PARTIALLY CORRECT/INCORRECT**: **[R]** `tcp_abort_on_overflow` по умолчанию **FALSE** («if overflow occurred due to a burst, connection will recover»); RST — только при `=1`.
- K3 (`File()`/blocking) — см. § 3: судья отклонил G2 п.4, **blind-spot B-1 прав и подтверждён экспериментом**.

### J-H12 · TCP keepalive в Go (ст. 47) — **OUTDATED**
- 47:256 «`KeepAlive` в `ListenConfig` лишь активирует `SO_KEEPALIVE`; интервалы берутся из sysctl (7200 с); сервер держит мёртвое соединение два часа» — **INCORRECT/OUTDATED**. **[L]** `net/dial.go:18–24`: `defaultTCPKeepAliveIdle = 15s`, `defaultTCPKeepAliveInterval = 15s`; `KeepAliveConfig` (Go 1.23, `dial.go:178–191`).
- **[E]** (accepted-соединение, `getsockopt`):

| Конфигурация | `SO_KEEPALIVE` | `TCP_KEEPIDLE` | `TCP_KEEPINTVL` |
|---|:-:|:-:|:-:|
| по умолчанию | 1 | 15 | 15 |
| `ListenConfig{KeepAlive: 30s}` | 1 | **30** | 15 |
| `Control` с `KEEPIDLE=30, KEEPINTVL=10` (как в статье) | 1 | **15** | **15** |
| `Control` + `KeepAlive: -1` | 1 | 30 | 10 |

  Значит, **сама посылка вопроса Interview неверна** (`KeepAlive: 30s` задаёт idle=30 с), а предложенный рецепт `Control` **не работает** (B-3: Go затирает значения на принятом сокете). Работают `KeepAliveConfig` (≥1.23), `SetKeepAliveConfig` на `*TCPConn`, либо `KeepAlive: -1` + `Control`.
- Листинг к тому же не компилируется (`"time"` не используется).

### J-H13 · Длительность `TIME_WAIT` (ст. 50 против 48) — **INCORRECT**
- 50:43 «MSL = `TCP_TIMEWAIT_LEN` = 60 с, 2MSL = **ровно 120 с**» — **INCORRECT**. **[R]** `include/net/tcp.h:140`: `#define TCP_TIMEWAIT_LEN (60*HZ) /* how long to wait to destroy TIME-WAIT state, about 60 seconds */`. Константа — это **вся** длительность `TIME_WAIT`, а не MSL. Ст. 48:308 («жёстко зашито 60 секунд») — **VERIFIED**. Диаграмма «2MSL = 60–120 сек» (50:32), «без ожидания 120 секунд» (50:149) — **INCORRECT**.
- 50:79–82: «ядро вызывает `tcp_tw_recycle()` (в старых ядрах)» — **OUTDATED/INCORRECT**: **[R]** sysctl `tcp_tw_recycle` присутствует в `net/ipv4/sysctl_net_ipv4.c` v4.11 и отсутствует в v4.12; функцию с таким именем в ядре я не искал (`NOT CHECKED`). «`tcp_death_row` — глобальная хеш-таблица» и «`struct tcp_time_wait`» — `NOT CHECKED` (структуры ядра не открывал; бриф считает это неверным).
- 50:243 «`tcp_fin_timeout` … может ограничить разрастание зависших сессий» — **PARTIALLY CORRECT**: **[R]** `ip-sysctl.rst`: параметр относится к **орфанным соединениям в FIN_WAIT_2**, а не к `TIME_WAIT`.
- **[R]** В ядре есть `tcp_tw_reuse_delay` (мс; дефолт `tcp_tw_reuse` = **2**, только loopback) — формулировки «ничего нельзя настроить» нужно смягчить.

### J-H14 · Direct I/O (ст. 42, 43, 44, 39) — **INCORRECT** (код), **CONTEXT-DEPENDENT** (следствие)
- `os.O_DIRECT` (42:173, 184) — **INCORRECT**; в ст. 43 исправлено на `syscall.O_DIRECT` (**VERIFIED**).
- `writeDirectIO` (43:222–233): `aligned := make([]byte, len(data)+4096)` и запись `aligned[:len(data)]` — **INCORRECT**: код не сдвигает начало и не делает длину кратной блоку; сами комментарии признают «в production выравнивают через `posix_memalign`».
  - **[E]** `make([]byte, 100+4096)` пять раз подряд: адрес mod 4096 = **0, 768, 1536, 2304, 3072**, то есть в 4 из 5 случаев буфер не выровнен.
  - **[E, поправка к брифу]** на **btrfs, ядро 7.2**: запись с `O_DIRECT` невыровненным адресом (`+1`), длиной 100 и 5000 вернула `nil`, а не `EINVAL`. Бриф утверждает «`EINVAL` гарантирован» — это `CONTEXT-DEPENDENT` (зависит от ФС и ядра; ext4/xfs/f2fs поддерживают `STATX_DIOALIGN`, **[L]** `man 2 statx`: «since Linux 6.1; support varies by filesystem; supported by ext4, f2fs, and xfs»). Ст. 43:263 («проверьте кратность адреса, длины и смещения») — **VERIFIED** как рекомендация диагностики.
- «`O_DIRECT` критичен для продления ресурса ячеек NAND» (43:приём) — `NOT CHECKED` (маркетинговое утверждение без источника).
- «`fsync` обязателен и при `O_DIRECT`» — **VERIFIED** (man 2 open описывает `O_DIRECT` как попытку минимизировать влияние кэша, без гарантии durability) — **[L]** `man 2 open` стр. 180–190.

### J-H15 · Привилегии (ст. 56, 57, 58) — **INCORRECT**; **бриф прав, прошлый фактчек внёс ошибку**
- 56:305, 315, 322 «в Go нет `os.Setuid`; `setuid(2)` меняет только текущий поток M; используйте `syscall.AllThreadsSyscall`; `x/sys/unix` принудительно рассылает всем потокам» — **PARTIALLY CORRECT / вводит в заблуждение**.
  - Верно: в `os` нет `Setuid`. **[L]** `syscall/syscall_linux.go:1243–1251`: `Setuid` без cgo вызывает `AllThreadsSyscall(sys_SETUID…)`, с cgo — `cgo_libc_setuid`. **[R]** Go 1.16 release notes: «On Linux, Setgid, Setuid, and related calls are now implemented». `x/sys/unix.Setuid` — тонкая обёртка над `syscall.Setuid` (**[L]**).
  - Неверно: рекомендация вызывать `AllThreadsSyscall` **напрямую**. **[L]** (`syscall_linux.go:1118–1125`): «AllThreadsSyscall … always returns ENOTSUP in binaries that use cgo». Правильно: `syscall.Setuid`/`Setgid`.
  - Код ст. 57 (`Setgroups → Setgid → Setuid`) — **VERIFIED** (компилируется, логика верна).
- 56:51, 182 (`Effective UID == 0` → доступ разрешён) — `NOT CHECKED` (механизм `capable()` в `fs/namei.c` я не открывал; бриф прав по сути про `CAP_DAC_OVERRIDE`).
- 57:216 `syscall.CAP_CLEAR` (только в комментарии) — **INCORRECT**; 57:242 `NoSetuid/NoSetgid` — **INCORRECT**.
- 58:235–252 `dropPrivileges()` — **INCORRECT**: `unix.CapHeader/CapData` не существуют; **[E, новое]** при `LINUX_CAPABILITY_VERSION_3` ядро ждёт **массив из двух** `CapUserData`, а в статье передан один; `os.Chown(".", 1000, 1000)` меняет владельца каталога, а не UID процесса. B-4 — см. § 6.

### J-H16 · `os/exec`, пайпы, демоны, systemd (ст. 5, 6, 25, 26, 29, 30, 40) — **INCORRECT** (по подпунктам)
1. 5:239, 6:208 «`cmd.Wait` блокирует горутину, а не поток M» — **INCORRECT**. **[L]** `os/pidfd_linux.go:105–108`: блокирующий `unix.Waitid(P_PIDFD, …)` внутри `ignoringEINTR` → блокируется M; P отдаётся только через hand-off.
2. ст. 25 `os.NewFile(int32…)` — **INCORRECT**; «`net.Conn` реализует `io.ReaderAt`» — `NOT CHECKED` (по брифу `*TCPConn` реализует `ReadFrom`/`WriteTo`).
3. ст. 26 `Pipe2` — **INCORRECT**.
4. ст. 26 `runWithPipe` — **INCORRECT**. **[L]** doc `StdoutPipe`: «It is thus incorrect to call Wait before all reads from the pipe have completed». **[E]** 200 запусков `head -c 1MiB /dev/zero` через код из статьи: **11 ошибок** («file already closed») и **10 усечённых выводов**. Комментарий «`io.Copy` закрывает пайп автоматически» — **INCORRECT** (пайп закрывает `Wait`).
5. ст. 26 «в Go нет аналога `popen`»; «`cmd.Output` нельзя в production… deadlock» — `NOT CHECKED` (не открывал дословно).
6. ст. 29 `daemonize()` — **INCORRECT** (в приведённом коде нет защиты от рекурсивного запуска: `ForkExec("/proc/self/exe", os.Args, …)` перезапускает `main`, который снова вызывает `daemonize`; запуск не выполнял, чтобы не получить fork-bomb; вывод — по коду). «`os/exec` не умеет `setsid()`» — **INCORRECT**: **[L]** `syscall/exec_linux.go:74` `SysProcAttr.Setsid bool`.
7. ст. 30:42 `net.FileConn(os.NewFile(3, ""))` для listening-сокета — **INCORRECT**. **[E]** `FileConn` на listening-fd возвращает `*net.TCPConn` без ошибки, а `Read` падает с `read: transport endpoint is not connected`; `net.FileListener` — правильный вызов. Ст. 30:151 упоминает `FileListener` (противоречие).
8. ст. 40:264 `os.FileMode(w.Stat_t.Mode)` — **INCORRECT**. **[L]** `io/fs/fs.go:195`: `ModeDir = 1 << 31`, а `S_IFDIR = 0x4000` (`zerrors_linux_amd64.go:1043`): `IsDir()` вернёт `false` для каталога.
9. Ст. 29:115 «`Type=simple` — запущен сразу после `execve()`» — **INCORRECT**. **[L]** `man systemd.service`: «immediately after the main service process has been forked off (i.e. immediately after fork(), and before … execve())»; «Typically, Type=exec is the better choice».
10. Ст. 29/28: буфер канала сигналов — ст. 28:163 «по умолчанию 1» **INCORRECT** (**[L]** `os/signal/signal.go:114`: «Package signal will not block sending to c: the caller must ensure that c has sufficient buffer space»), ст. 29:35 («буферизованный ёмкостью ≥1») — **VERIFIED**; статьи противоречат друг другу.

### J-H17 · Разделяемая память (ст. 32, 31) — **INCORRECT**
- `syscall.ShmOpen…` — **INCORRECT** (`go vet`).
- 31:194 `mmap("/dev/zero", MAP_SHARED)` как shared memory для IPC — **INCORRECT**. **[E]** родитель отображает `/dev/zero` как `MAP_SHARED`, пишет 42, запускает `exec.Command(self, "child")`; потомок отображает так же и видит **0**. Такое отображение общее только для потомков после `fork`, а Go `fork` без `exec` не делает.
- Неиспользуемый `os` в 31 (3-й блок) — **INCORRECT** (компиляция).

### J-H18 · Память в контейнере и PID 1 (ст. 52, 53, 54) — **INCORRECT**
- 54:158–160 «для PID 1 `SIGTERM` будет молча проигнорирован; сервер работает до `SIGKILL`» — для Go **INCORRECT**. **[E]** Go-программа без `signal.Notify`, запущена как PID 1 в `unshare -Ur --pid --fork --mount-proc`; `kill -TERM` снаружи → процесс **завершился немедленно, код возврата 143**. **[L]** `runtime/signal_unix.go: dieFromSignal` (`setsig(SIG_DFL)`, `raise`, затем при PID 1 `exit(128+sig)`). Для C/Python без обработчика тезис верен; для Go — нет. Рекомендация «обрабатывать `SIGTERM` и делать graceful shutdown» остаётся верной.
- 53:126–129 «`mmap` вернёт `ENOMEM`, рантайм превратит в фатальное падение» при упоре в лимит cgroup — **INCORRECT**. **[E]** `MemoryMax=64M` (+`MemorySwapMax=0`), программа аллоцирует 400 МБ: процесс получил **`SIGKILL` (exit 137)** без сообщения Go. `ENOMEM` от `mmap` бывает при `RLIMIT_AS`/`overcommit=2`/`max_map_count`; **[L]** `runtime/mem_linux.go:172–176`: `sysMapOS` при `ENOMEM` → `throw("runtime: out of memory")` — это справедливо только для таких случаев.
- 53:126, 54 Q2 «аллокатор Go использует `mmap` и `brk`» — **INCORRECT**. **[L]** `runtime/malloc.go:677`: `sbrk0()` вызывается **только в ветке 32-битной архитектуры** (`} else { // On a 32-bit machine…`) для подсказки адреса арен; на 64-битных рост кучи через `brk` отсутствует.
- 52:153 «рантайм определяет объём доступной памяти через `sysinfo`/`/proc/meminfo`… GC запускался поздно» — `NOT CHECKED` построчно; по `SetMemoryLimit` (`garbage.go:181–195`) триггер GC считается от live heap, `GOGC` и `GOMEMLIMIT`, а не от памяти хоста — **PARTIALLY verified**.

### J-H19 · Frame pointer в Go (ст. 20 против ст. 60) — **INCORRECT**
- 20:72, 165, 170 «в Go frame pointer отключён по умолчанию, включается `GOEXPERIMENT=framepointer`; `-fomit-frame-pointer`; заголовок `stkblk`» — **INCORRECT**. **[L]** `internal/buildcfg/exp.go:44–51`: `FramePointerEnabled = GOARCH == "amd64" || GOARCH == "arm64"`, «now it's always enabled». **[E]** `go tool objdump`: каждый кадр начинается с `PUSHQ BP; MOVQ SP, BP`. Ст. 20:72 («хотя в современных версиях `RBP` сохраняется для `perf` и eBPF») — **VERIFIED** и противоречит 20:165/170.
- 60:247 «perf не мог раскручивать стеки Go… сегментированные стеки» — **OUTDATED**: сегментированные стеки убраны в Go 1.3 (`NOT CHECKED` по release notes; см. C-HIST).

### J-H20 · Core dump и `GOTRACEBACK` (ст. 59) — **INCORRECT** (центральный тезис)
- Статья (59:27–36 и диаграммы) строит разбор на том, что при сбое Go ядро делает дамп, если `ulimit -c > 0`; слово `GOTRACEBACK` в статье **не встречается** (`grep`).
- **[E]** `ulimit -c unlimited`, программа с `fatal error: all goroutines are asleep`: по умолчанию **exit 2, дампа нет**; `GOTRACEBACK=crash` → **exit 134, «Aborted (core dumped)»** (`core_pattern = |systemd-coredump`). **[L]** `runtime/extern.go:257`: «GOTRACEBACK=crash is like “system” but crashes in an operating system-specific manner instead of exiting … raises SIGABRT».
- 59:258 «`sysctl vm.core_uses_pid`» — **INCORRECT**: **[L]** `/proc/sys/vm/` не содержит `core_uses_pid`; параметр называется `kernel.core_uses_pid`. В той же фразе «выставлять в `1`» противоречит `=0`.
- `dlv core … heap` — **INCORRECT** (J-H5).

### J-H21 · Журналируемые ФС, RAID/LVM (ст. 41, 46) — **INCORRECT** (по проверенным подпунктам)
- 41:62 «EXT4, XFS, Btrfs поддерживают три режима журналирования (`data=`)» — **INCORRECT**. **[L]** `man 5 ext4`: `data={journal|ordered|writeback}`, «Metadata is always journaled», `ordered` — default. **[R]** `docs.kernel.org/admin-guide/xfs.html`: опции `data=` нет; `man 5 btrfs` — тоже. Что XFS журналирует только метаданные, я по документации XFS не подтверждал (`NOT CHECKED`).
- 41:104 «checkpointing — шаг, выполняемый до возврата `fsync`» — **INCORRECT** по документации ядра. **[R]** `docs.kernel.org/filesystems/ext4/journal.html`: «Checkpointing is used internally during critical updates to the filesystem including journal recovery, filesystem resizing, and freeing of the journal_t structure».
- Таблица RAID, путь I/O «Page Cache → I/O Scheduler → Device Mapper → RAID», `GroupCommitter` — `NOT CHECKED`.

### J-H22 · Теория примитивов синхронизации (ст. 33, 34) — **INCORRECT**
- 33:55 «spinlock эффективен в одноядерных средах» — **INCORRECT**. **[R]** `include/linux/spinlock_api_up.h`: `__LOCK(lock) = preempt_disable(); ___LOCK_…`, то есть на UP спинлок не спинит, а отключает вытеснение.
- 33:75, 101, 240 «`FUTEX_WAIT` → `TASK_UNINTERRUPTIBLE`» — **INCORRECT**. **[R]** `kernel/futex/waitwake.c:470`: `set_current_state(TASK_INTERRUPTIBLE|TASK_FREEZABLE)`; **[L]** `man 2 futex`: `EINTR` — «A FUTEX_WAIT … operation was interrupted by a signal».
- 33:101 «структура futex хранится в `fs/futex.c`» — **INCORRECT**. **[R]** файл `fs/futex.c` не существует ни в v5.15, ни в v5.16; в v5.15 это `kernel/futex.c`, в v5.16 — `kernel/futex/core.c`.
- 34:282 «если читатели непрерывны, писатели голодают; Go не гарантирует fairness в `RWMutex`» — **INCORRECT**. **[L]** `sync/rwmutex.go:21–25`: «If any goroutine calls Lock while the lock is already held by one or more readers, concurrent calls to RLock will block until the writer has acquired (and released) the lock, to ensure that the lock eventually becomes available to the writer».
- 34:97 `acquireWithTimeout` — **INCORRECT**. **[E]** после таймаута и последующего `Unlock` владельца вспомогательная горутина всё равно захватывает мьютекс, и `TryLock()` возвращает `false` («утечка» захвата навсегда). Комментарий «не вызывать `Unlock()`, так как мы его не взяли!» — ловушка. **[L]** `TryLock` есть с Go 1.18 (`api/go1.18.txt:183`).
- 34:84 (детектор deadlock) и 34:282 («отключить через `runtime.GOMAXPROCS(0)`») — **INCORRECT**, см. § 9 (эксперимент).

### J-H23 · Copy-on-Write (ст. 16) — **INCORRECT**
- 16:60 «CoW для `fork` реализован через бит `PTE_SOFT_DIRTY`» — **INCORRECT**. **[R]** `Documentation/admin-guide/mm/soft-dirty.rst`: «The soft-dirty is a bit on a PTE which helps to track which pages a task writes to» (CRIU).
- 16:88–92 «`SHR` у дочернего процесса в точности равен `RSS`» — `NOT CHECKED` (`/proc/PID/statm` определение не открывал; бриф: `SHR = RssFile + RssShmem`).
- Листинг `MADV_DONTFORK` — **INCORRECT** (`syscall.Madvise(b []byte, advice int)`, **[L]**).
- 16:103–110 «`os/exec` использует `clone` с `CLONE_VM|CLONE_VFORK|SIGCHLD` без `CLONE_FILES`» — **VERIFIED** **[L]** (`exec_linux.go:309,337`). Следовательно CoW к `os/exec` не относится — статья противоречит себе (бриф прав). «Вызовите `LockOSThread()` до форка» — `NOT CHECKED`.
- Уточнение B-6 (blind-spot): `CLONE_VFORK` приостанавливает **только вызывающий поток**, а не «родительский процесс» — **[L]** `man 2 vfork`: «When vfork() is called in a multithreaded process, only the calling thread is suspended».

### J-H24 · Возврат памяти, `MemStats`, аллокатор (ст. 12–15, 17, 19) — **INCORRECT** (по проверенным подпунктам)
1. 19:214 «sysmon вызывает `madvise`; ядро отменяет маппинг; `mmap` вернёт тот же адрес» — **INCORRECT**. **[L]** возвращает память фоновая горутина `bgscavenge` (`mgcscavenge.go:649`); `sysmon` лишь будит её (`proc.go:6642`). Маппинг сохраняется. «Scavenger возвращает память `MADV_DONTNEED`» — **VERIFIED** для Linux: **[L]** `runtime1.go:398–407` («Hence, default to MADV_DONTNEED»); на BSD по умолчанию `MADV_FREE`.
2. «`HeapAlloc` растёт, `HeapInuse` стабилен» — **INCORRECT**: **[L]** `mstats.go:155–166`: `HeapInuse` — байты в используемых спанах, «HeapInuse minus HeapAlloc estimates … fragmentation», то есть `HeapInuse ≥ HeapAlloc`.
3. 14:145 `badPattern` («миллион аллокаций в куче») против `goodPattern` — **INCORRECT**. **[L]** `go build -gcflags=-m`: `make([]byte, 256) does not escape` в `badPattern`; в `goodPattern` `bufPool.Put(buf)` → `make([]byte, 256) escapes to heap`. **[E]** бенчмарк: «плохой» 3,5 нс/оп, **0 аллокаций**; «хороший» (`sync.Pool` со срезом) 19,8 нс/оп, **1 аллокация (24 B)** на каждый `Put` (классическая SA6002).
4. 15:149 «аллокатор выравнивает спаны и объекты по границам степеней двойки, предотвращая false sharing» — **INCORRECT**. **[L]** `internal/runtime/gc/sizeclasses.go:98`: `SizeClassToSize = {0, 8, 16, 24, 32, 48, 64, 80, 96, 112, …}` — классы 24, 48, 80, 112 не кратны 64 и не степени двойки; объект класса 24 B может делить строку кэша с соседом. (Фраза про «68 классов» в 15:140 — **VERIFIED**: `NumSizeClasses = 68` с учётом нулевого.)
5. 13:110 `GODEBUG=pagealloc=1`, 12:148/16 `Madvise` из 3 аргументов, 17:185 `debug.MemoryLimit` — **INCORRECT** (J-H5, J-H6).
6. 13 Interview Q2 «при major fault планировщик Go отсоединяет P» — **INCORRECT** (см. C-HANDOFF/B-7: fault происходит в user-коде, P в `_Prunning`).

### J-H25 · Ст. 11 (affinity, NUMA) — **INCORRECT** (по проверенным пунктам)
- «локальная RAM ~20–30 нс, удалённая ~80–120 нс» (11:22, 26) и «~20 нс» (8:138) — **INCORRECT**. **[E]** pointer chase на этой машине (i9-12900K, L3 30 МиБ): 16 КиБ — 1,1 нс; 256 КиБ — 3,1 нс; 4 МиБ — 16 нс; 32 МиБ — **74 нс**; 512 МиБ — **88 нс**. Локальная DRAM — порядка 70–100 нс; 20–30 нс — масштаб L3. Удалённый узел NUMA на этой одно-узловой машине **измерить нельзя** (`NOT CHECKED`).
- 11:159–160 `cpuset.sched_load_balance`, `cpuset.mems_hardwall` «для cgroups v2» — **INCORRECT**. **[R]** `cgroup-v2.rst`: из cpuset есть `cpuset.cpus`, `.cpus.effective`, `.cpus.exclusive`, `.cpus.partition`, `.cpus.isolated`, `.mems`, `.mems.effective`; **[R]** `cgroup-v1/cpusets.rst`: `cpuset.mem_hardwall`, `cpuset.sched_load_balance` — только v1 (а `mems_hardwall` — вообще не такое имя).
- 11:201 `gcresidency=1` — **INCORRECT** (J-H5). 9:133 `sched_gomaxprocs` — **INCORRECT**.
- `MPOL_BIND` → «`ENOMEM`», auto-NUMA «запускает `migratepages` и KSM» — `NOT CHECKED`.

### J-H26 · Приоритеты, RT и `Setpriority` (ст. 10) — **CONTEXT-DEPENDENT / INCORRECT** (по подпунктам)
- 10:83 «пока есть готовый RT-поток, ни один CFS-процесс не получит ни одного такта» — **CONTEXT-DEPENDENT**. **[R]** `Documentation/scheduler/sched-rt-group.rst`: по умолчанию `sched_rt_runtime_us = 950000` из `sched_rt_period_us = 1000000` (5 % времени остаётся несущим), но **[L]** на этой машине (Fedora, ядро 7.2.8) `/proc/sys/kernel/sched_rt_runtime_us = 1000000`, то есть дефолт зависит от дистрибутива/версии; наличие fair server в 6.12+ я не подтверждал (`NOT CHECKED`; поиск дал только обсуждения LKML).
- 10:102–106 `syscall.Setpriority(PRIO_PROCESS, 0, …)`: сообщение «приоритет процесса обновлён» — `NOT CHECKED` (`man 2 setpriority` на атрибут потока не открывал; `syscall.Setpriority` существует **[L]**, сигнатура `(which, who, prio int)`).

### J-H27 · Регистры аргументов `syscall` x86-64 (ст. 23:70) — **INCORRECT**
**[L]** `man 2 syscall`, таблица x86-64: `rdi, rsi, rdx, r10, r8, r9` (номер — `rax`). Статья: «`R10` (первый), `R8` (второй), `R9` (третий)» — неверно. Ст. 2 и 22 дают верный порядок (подтверждено судьёй; сам я их не читал).

### J-H28 · IOCP: «встроенный пул потоков ядра» (ст. 37:114, 133) — **PARTIALLY CORRECT**
**[R]** Microsoft Learn «I/O Completion Ports»: порт имеет *concurrency value*, ограничивающую число runnable-потоков; пул потоков для обработки — **предварительно создаваемый приложением** («in conjunction with a pre-allocated thread pool»); Windows thread pool API строится поверх IOCP. Формулировка «встроенный пул потоков **ядра**» — **INCORRECT**; остальное описание (concurrency value, пробуждение следующего потока) — **VERIFIED**.

### J-H29 · Сводная таблица «Go → ядро» (ст. 63) — **INCORRECT**
- «`goroutine` → `clone(CLONE_VM|CLONE_FS|CLONE_FILES)`» — **INCORRECT**. **[L]** `runtime/os_linux.go:156–161`: `cloneFlags = CLONE_VM|CLONE_FS|CLONE_FILES|CLONE_SIGHAND|CLONE_SYSVSEM|CLONE_THREAD`; `clone` создаёт **M** (поток ОС), а не горутину.
- «`runtime.GC` → `madvise`/`mprotect`» — **INCORRECT**: **[L]** коммит страниц — `mmap(MAP_FIXED)` (`mem_linux.go:172`); возврат — `madvise` фонового scavenger; `runtime.GC` ничего из них напрямую не зовёт.
- «алгоритм Нейгла» (63:159: `net/http` — `epoll`/`kqueue` + `setsockopt(TCP_NODELAY)`, «обязательное отключение алгоритма Нейгла») — **VERIFIED**: **[L]** `net/tcpsock.go:290` `setNoDelay(fd, true)` — Go включает `TCP_NODELAY` по умолчанию. Пометка судьи здесь ложноположительная (в ст. 22 та же опция подана как «оптимизация», см. C-SOCKDEF).

### J-H30 · «>50 % мощности на системные вызовы» (ст. 2:163) — **INCORRECT**
**[Л]** 50 000 RPS × 20 syscalls = 1 млн вызовов/с. При заявленных самой статьёй 100–500 нс — это 0,1–0,5 с работы в секунду, то есть **10–50 % одного ядра**, а не «свыше 50 % всей мощности». **[E]** `RawSyscall(getppid)` на этой машине: **62 нс**, `Syscall(getppid)`: **80 нс**; KPTI на этом процессоре отсутствует (Meltdown: *Not affected*) → ≈6–8 % одного ядра из 24 потоков. Реальные `read`/`write` дороже `getppid`, но вывод «свыше 50 % всей мощности» в общем случае не следует.

### J-H31 · eBPF-листинг (ст. 61) — **INCORRECT**
- Компиляция: см. J-H6 (`os`, `time`, `Maps.Lookup`; `//go:embed` без `import "embed"` — ошибка выйдет после починки типов).
- Busy-loop по `Lookup` (цикл `for { metricsMap.Lookup(…) }` без паузы и без блокирующего ожидания) — **INCORRECT** как «наблюдение в реальном времени» (по коду: цикл крутится на 100 % одного ядра; запуск не выполнял — [Л]); «длительность из одного `sys_enter_write`» — **INCORRECT** (нужна пара enter/exit; `Duration` из одной точки получить нельзя).
- «карты читаются через mmap без syscall» — `NOT CHECKED` (бриф: верно только для `BPF_F_MMAPABLE` array и ringbuf; в `cilium/ebpf` я не проверял).

---

## 3. Конфликты между брифами (K1–K12)

| # | Тема | Решение | Статус претензии | Доказательство |
|---|---|---|---|---|
| K1 | `syscall.Setuid` в многопоточном Go | **Прав Sonnet / судья.** Gemini (G10 п.1) неверен | `syscall.Setuid` действует на все потоки с Go 1.16 | **[L]** `syscall_linux.go:1243–1251`; **[R]** Go 1.16 release notes; текст ст. 56 ошибочен (J-H15) |
| K2 | Резолвер на macOS | **Прав Sonnet.** Деталь Gemini («чистый Go при `CGO_ENABLED=0`») устарела; версию, с которой так, **не подтвердил** | на darwin системный резолвер по умолчанию и без cgo | **[L]** `conf.go:167–190`, `cgo_unix.go` (тег `…|| darwin`), `cgo_unix_syscall.go` (`!netgo && darwin`) |
| K3 | `TCPListener.File()` и блокирующий режим | **Судья неправ в итоговом выводе (R4/R10).** `File()` сам режим не меняет, но листинг ст. 49 следом вызывает `file.Fd()`, а он переводит **общий open file description** в блокирующий режим. Правы Gemini (по сути последствия) и blind-spot B-1 | **[E]** `nonblock` до: `true`; после `File()`: `true`; после `File().Fd()`: **`false`** (у исходного listener тоже); `Close()` при висящем `Accept` не вернулся за 2 с | `os/file_unix.go` (`Fd` → `SetBlocking`), `net/fd_unix.go:170–180` |
| K4 | Разорванные строковые литералы | **Список Sonnet точен**; список Gemini (4, 11, 16, 24, 30, 42, 57) — нет | 17 статей | **[L]** `go/scanner`: 5, 6, 7, 10, 17, 18, 19, 27, 29, 39, 40, 44, 49, 51, 53, 56, 61 |
| K5 | Ст. 54 и Go 1.25 | **Частично оба.** 54:150 верна; Итог 3 устарел | `OUTDATED` (Итог 3) | J-H4 |
| K6 | Приоритет `os.O_DIRECT`, `Pipe2`, `FileMode` | **High** | компиляция / `IsDir()` | **[L]** `go vet`; `ModeDir = 1<<31`, `S_IFDIR = 0x4000` |
| K7 | Приоритет `TIME_WAIT` | **High** | `TCP_TIMEWAIT_LEN` = 60 с = вся длительность | **[R]** `include/net/tcp.h:140` |
| K8 | `brk` и namespaces в ст. 53 | **Разделить** | `brk` — **INCORRECT** (J-H18); «7 типов namespaces» — `OUTDATED`: **[L]** `man 7 namespaces` перечисляет 8 (добавлен **Time**, `CLONE_NEWTIME`); таблица ст. 53:59–70 содержит 7 строк (нет `TIME`) | `man 7 namespaces` |
| K9 | Детали `stackcache` | **Прав судья** | пулы 2/4/8/16 КБ | **[L]** `malloc.go:136,150` |
| K10 | «`make` никогда не выравнивает по 4096» | **Формулировка Gemini слишком сильна, вывод верен** | **[E]** `make([]byte, 100+4096)`: адреса mod 4096 = 0, 768, 1536, 2304, 3072 → выравнивание случайное | эксперимент J-H14 |
| K11 | EEVDF и sysctl | **Medium**; версия EEVDF подтверждена, история sysctl — нет | EEVDF в 6.6: **VERIFIED** **[R]** kernelnewbies Linux 6.6 («replaces the CFS process scheduler with … EEVDF»). Перенос sysctl CFS в debugfs (5.13) — `NOT CHECKED` | — |
| K12 | `sendfile`, сокет как источник | **Прав судья**: в ст. 43 утверждения «сокет → файл» нет | **VERIFIED** (grep `sendfile` по 43: везде файл → сокет); остаток — ст. 31:235 («между файлами/сокетами», Low) | grep |

---

## 4. Сквозные кластеры

### C-COMPILE — **INCORRECT** (см. J-H6). Бриф прав, цифры уточнены (75/46).

### C-API — **INCORRECT** (см. J-H5). Все 33 строки таблицы подтверждены.

### C-NUM · Числа, которые расходятся между статьями — **INCORRECT** (по двум величинам), остальное — `NOT CHECKED`
Мои измерения на **этой** машине (Intel Core i9-12900K, ядро 7.2.8, без KPTI) — не «истина для всех», а нижняя граница для современного десктопа:

| Величина | Разброс в модуле (по брифу) | Мои измерения | Вывод |
|---|---|---|---|
| Стоимость syscall | 50–100 нс (5), 100–500 нс (2), 200–5000 тактов (22), 1000–5000 (23), 1000–2000 (31) | **62 нс** `RawSyscall(getppid)`, **80 нс** `Syscall(getppid)` **[E]** | 100–500 нс (ст. 2) допустимо при mitigations/KPTI; «1000–5000 тактов» для *пустого* syscall — `NOT CHECKED`/завышено |
| Переключение горутин | 10–20 нс (63, 62, 35), 10–50 (33), 10–200 (5, 7), 100–300 (62) | ping-pong по небуферизованному каналу, `GOMAXPROCS=1`: **283 нс на цикл (2 переключения) ≈ 140 нс на переключение** (включая канальные операции) **[E]** | «10–20 нс» **INCORRECT** (для переключения «чистого» контекста нужен отдельный микробенчмарк, я его не делал) |
| Переключение потоков ОС | 1–2 мкс (7), 2–5 мкс (5), 1–5 мкс (8), 3–15 мкс (9), «1000–3000 тактов = 5–10 мкс» (3) | pipe ping-pong на одном CPU: **2066 нс на цикл (2 переключения + 4 syscalls) ≈ 0,9 мкс на переключение** **[E]** | Нижняя граница модуля (1–2 мкс) согласуется; «3–15 мкс» и «5–10 мкс» — завышены для прямой стоимости. Прямую и косвенную (кэш/TLB) стоимость нужно разделять — `NOT CHECKED` |
| DRAM | 20 нс (8), 20–30 нс (11), 50–100 нс (9, 35) | 32 МиБ: **74 нс**; 512 МиБ: **88 нс** **[E]** | «20–30 нс» **INCORRECT**; «50–100 нс» **VERIFIED** (для локальной DRAM) |
| `somaxconn` | 128 (47), «128 раньше, 4096 сейчас» (49) | **[R]** `ip-sysctl.rst`: 4096, «was 128 before linux-5.4»; **[L]** здесь 4096 | 47: `OUTDATED`; 49: **VERIFIED** |
| `TIME_WAIT` | 60 с (48), 120 с (50) | **[R]** `tcp.h:140`: 60 с | 50: **INCORRECT** (J-H13) |
| TLB miss, major fault, NVMe, L1/L2/L3 «miss» | см. бриф | — | `NOT CHECKED` (нужны микроархитектурные источники Agner Fog / uops.info / Chips and Cheese, которые я не открывал) |

### C-TLB · «TLB shootdown», KPTI, «context switch» на syscall — `NOT CHECKED` (терминология ядра), частично **[E]**
- «syscall = переключение контекста»: **[E]** syscall = 62–80 нс, а переключение потоков ≈ 900 нс — разница на порядок; термин «mode switch» корректнее. Формальное определение «context switch» — `OPINION / терминология`.
- «KPTI заставляет перезагружать `CR3` при каждом входе в ядро» (ст. 2:157): **CONTEXT-DEPENDENT** — на CPU без Meltdown (эта машина: `/sys/devices/system/cpu/vulnerabilities/meltdown` = *Not affected*) KPTI отключён; **[Л]** поэтому «массовый сброс TLB на каждый syscall» не является общим фактом. Остальные пункты кластера (IPI, `LSTAR`, IBPB) — `NOT CHECKED`.

### C-BRK · «Go использует `brk`» — **INCORRECT** (64-bit)
**[L]** `runtime/malloc.go:677` `sbrk0()` вызывается только в ветке 32-битной архитектуры (`} else { // On a 32-bit machine…`); для 64-bit куча — арены через `mmap`. Статьи 12, 13, 15, 19, 21 («не использует») — **VERIFIED**; 1 (таблица), 53, 54 — **INCORRECT**.

### C-SCAV · Возврат памяти, scavenger — **PARTIALLY verified**
- Возвращает память фоновая `bgscavenge`, не `sysmon` и не GC — **VERIFIED** **[L]**.
- `MADV_DONTNEED` на Linux по умолчанию — **VERIFIED** **[L]** `runtime1.go:398–407` (комментарий: «On Linux, MADV_FREE is faster … Hence, default to MADV_DONTNEED»); `GODEBUG=madvdontneed=0` включает `MADV_FREE`.
- Коммит страниц — `mmap(MAP_FIXED)`, а не `mprotect` — **VERIFIED** **[L]** `mem_linux.go:172`.
- «С Go 1.11 куча разреженная»; «не lock-free начиная с mcentral» — `NOT CHECKED`.

### C-THP · Huge pages и THP — **NOT CHECKED** (кластер)
**[L]** Подтверждено только: в `sysMapOS` при `GODEBUG=disablethp` вызывается `sysNoHugePageOS` (`mem_linux.go:186–189`), `MADV_COLLAPSE` присутствует (`mem_linux.go:147`). История 1.21.0–1.21.4 / `disablethp` с 1.21.6 и issue-номер — `NOT CHECKED` (в `api/` и `godebug.md` я это не сверял).

### C-GOBUF · Что сохраняется при переключении горутины — **INCORRECT**
**[L]** `runtime/runtime2.go:303–320`: `gobuf = {sp, pc, g, ctxt, lr, bp}` — полей `ret` и «14 регистров» нет. Утверждения «сохраняются 14 регистров» (5:151, 9:94/104) и «rip, rsp, r12–r15» (63) — **INCORRECT**; ст. 33 («3 регистра: SP, PC, BP») — **VERIFIED** с поправкой (ещё `g` и `ctxt`).

### C-HANDOFF · Syscall, `retake`, hand-off — **PARTIALLY CORRECT** (ст. 22:139, 62)
**[L]** `runtime/proc.go:6681– retake`: P отбирается у потока в syscall, если он провёл в нём более одного тика sysmon и **либо** `runq` не пуст, **либо** нет spinning/idle P, **либо** прошло ≥10 мс (`pd.syscallwhen+10*1000*1000`). Формулировки «дольше ~10 мс» (22:139) и «немедленно отвязывает P» (62) — обе неточны. «Work stealing выполняет sysmon» — `NOT CHECKED` (но в `retake` его нет).

### C-NOFILE · Go ≥1.19 сам поднимает soft `RLIMIT_NOFILE` — **OUTDATED** (подтверждено)
**[L]** `syscall/rlimit.go:20–46`: при старте `Cur = Max − 1` (если меньше); **[R]** Go 1.19 release notes: «corrects artificially low limits set on some systems for compatibility with very old C programs using the select system call». Советы «поднимайте лимит вручную, иначе упадёте на 1025-м соединении» (5:293–322, 25:150/168, 52:70–94, 52:176/266) — **OUTDATED** (если `hard` лимит не занижен). **[L]** `man systemd.exec`: `LimitNOFILE=` задаёт **rlimit** (soft+hard), а не cgroup — утверждения 30:160/176 («применяется к cgroup… на уровне ядра и cgroup») — **INCORRECT**.

### C-SOCKDEF · Дефолтные опции сокетов — **INCORRECT**
**[L]** `net/sockopt_linux.go:28,34`: Go по умолчанию ставит только `SO_REUSEADDR`; `SO_REUSEPORT` — нет (ст. 48:294, Итог 3, ст. 1:73 «включает по умолчанию» — **INCORRECT**; ст. 50 — **VERIFIED**). `TCP_NODELAY` включён по умолчанию (`tcpsock.go:290`) — подача в ст. 22 как «оптимизации» — **PARTIALLY CORRECT**.

### C-MMAP-PC · «`mmap` обходит Page Cache» — `NOT CHECKED` (механизм ядра), логика статей противоречива — вывод судьи правдоподобен.

### C-HIST · Версии Go — **частично VERIFIED**
- `signal.NotifyContext` — **Go 1.16** **[L]** `api/go1.16.txt:409` (ст. 28: «Go 1.15+» — **INCORRECT**).
- `Mutex.TryLock`/`RWMutex.TryLock` — **Go 1.18** **[L]** `api/go1.18.txt:183–184`.
- `exec.Cmd.WaitDelay`, `Cancel` — Go 1.20 **[L]** `api/go1.20.txt:271–273`.
- `os.Root` — Go 1.24 **[L]** `api/go1.24.txt:199`.
- Адаптивный стартовый размер стека (`adaptivestackstart`) — есть в `runtime/stack.go:1422` и `dbgvars`; версия (1.19) — `NOT CHECKED`.
- Непрерывные стеки в Go 1.3, минимальный стек 2 КБ в 1.4 — `NOT CHECKED` (release notes 1.3/1.4 не открывал).

### C-OTHERLANG · Java, PHP, Python — `NOT CHECKED`
Java 21 virtual threads, удаление CMS в JDK 14, PEP 475 (Python 3.5), поведение PHP-FPM — первоисточники не открывались.

### C-K8S · K8s, Docker, systemd — **частично VERIFIED**
- `terminationGracePeriodSeconds` = 30 — **VERIFIED** **[R]** kubernetes.io/pod-lifecycle («defaults to 30 seconds»).
- «~44 syscalls блокирует seccomp» — **VERIFIED** **[R]** docs.docker.com/engine/security/seccomp («disables around 44 system calls out of 300+»). Ст. 58:265, приписывающая это AppArmor, — **INCORRECT**.
- Docker по умолчанию без userns — **VERIFIED** (userns-remap — опция, **[R]** docs.docker.com/engine/security/userns-remap).
- `Type=simple` считается запущенным после **fork**, а не `execve` — **VERIFIED** **[L]** `man systemd.service` (см. J-H16 п. 9).
- `LimitNOFILE` — rlimit — **VERIFIED** **[L]** `man systemd.exec`.
- `requests.memory` ↔ `memory.min/low`, NodeSwap — `NOT CHECKED`.

### C-KNAMES · Имена внутри ядра — **частично VERIFIED**
- `do_fork` → `kernel_clone`: **VERIFIED** **[R]** v5.9 `kernel/fork.c`: `long _do_fork(…)`, v5.10: `pid_t kernel_clone(…)`.
- `pdflush` удалён в 2.6.32: **VERIFIED** **[R]** `mm/pdflush.c` есть в v2.6.31 и отсутствует в v2.6.32.
- `fs/futex.c` → `kernel/futex/` с 5.16: **неточно** — **[R]** файла `fs/futex.c` не было никогда; в v5.15 — `kernel/futex.c`, в v5.16 — `kernel/futex/core.c`.
- VMA в maple tree с 6.1: **VERIFIED** **[R]** kernelnewbies Linux 6.1 («a Maple tree data structure with better algorithmic properties than red-black trees»); именно что VMA на нём — `NOT CHECKED`.
- `tcp_tw_recycle` удалён в 4.12: **VERIFIED** **[R]** присутствует в `net/ipv4/sysctl_net_ipv4.c` v4.11 и отсутствует в v4.12.
- `sendpage` удалён в 6.5, `syn_table/listen_sock` удалены в 4.4, `pid_hash_init` в 4.15 — `NOT CHECKED` (в v6.5 `include/linux/net.h` слово `sendpage` встречается ещё один раз — формулировка «удалён в 6.5» требует уточнения).
- Выдуманные имена (`VM_FILE`, `unix_inode_info`, `f_op->socket`, `struct namespace`, `irq_init`) — `NOT CHECKED` (ядро целиком я не просматривал).

### C-MARKUP · Разметка — **VERIFIED**, но число узлов отличается
- **KaTeX:** `\t…` превратился в TAB в статьях **12, 13, 14, 15, 17, 18, 54** (14 строк) — совпадает с брифом.
- **Mermaid `:::class` внутри метки:** **[E]** рендер в Mermaid 10.9.1 показывает `:::entry` **текстом** внутри узла (ст. 3, диаграмма 1: «Приложение на Go (User Space):::entry»). Мой подсчёт по шаблону `:::имя"]` в модуле 2 — **18 узлов в 14 статьях** (3, 4, 15, 44, 45, 46, 49, 51, 53, 55, 56, 57, 58, 63); бриф называет «≥21 узел». Расхождение объясняется шаблоном поиска. **Масштаб по проекту (найден позже): 216 узлов в 167 статьях всех модулей. После правок: исправлено** (`A["Текст:::entry"]` → `A["Текст"]:::entry`), коммит `a8d34615`; аудит выдаёт 0 предупреждений.
- **Вложенные кавычки Mermaid ст. 40:** **подтверждено, и это только часть проблемы** — см. § 9.1 (13 диаграмм не парсятся).

### C-QUOTE · Эпиграфы, атрибуции — `NOT CHECKED`/`OPINION` (первоисточники комментариев Таненбаума и Торвальдса, Хэмминга я не открывал).

---

## 5. Остатки прошлого фактчека `a8006dfc` (C-FIX)

| Ст. | Что уже верно | Что осталось | Статус остатка |
|---|---|---|---|
| 38 | тело: `EPOLLET` без ONESHOT | Итог п.2 (38:190) про `EPOLLONESHOT`/`EV_ONESHOT` | **INCORRECT** (J-H7, **[L]** `netpoll_epoll.go:51`) |
| 36, 62 | `EPOLLET`, регистрация один раз | 36 диаграмма «после EAGAIN», 35, 48 | **INCORRECT** (J-H7, **[E]** `epoll_ctl(ADD)` один раз) |
| 24 | Interview: ptrace + `int3` на PLT | тело 24:90, Gotcha 24:127, 24:145 | **INCORRECT** (J-H9) |
| 43 | `syscall.O_DIRECT` | ст. 42 `os.O_DIRECT`; `writeDirectIO` | **INCORRECT** (J-H14) |
| 23, 9 | 23:79–88 (gopark без syscall) | 23:45, Q3; ст. 3, 22, 24, 32, 34, 63 | **INCORRECT** (J-H3, **[E]**) |
| 50 | `tcp_fin_timeout` — только FIN_WAIT_2 | 50:243; TIME_WAIT 120 с | **INCORRECT** (J-H13) |
| 54 | Go 1.25 и `containermaxprocs` | Итог 3 ст. 54; ст. 8, 52 | **OUTDATED** (J-H4) |
| 5 | текст про `gobuf` (SP, PC, BP, g) | диаграмма 5:151 «14 регистров»; 9:94/104; ст. 63 | **INCORRECT** (C-GOBUF) |
| 56 | «нет `os.Setuid`» | исправление само внесло ошибку: `syscall.Setuid` уже действует на все потоки; `AllThreadsSyscall` при cgo → `ENOTSUP` | **INCORRECT** (J-H15, K1) |
| 19 | scavenger и `MADV_DONTNEED` | 19:212 таблица «`munmap` при sysmon», 19:214 «sysmon и madvise» | **INCORRECT** (J-H24 п.1) |
| 22 | hand-off и `retake` | 22:139 «дольше ~10 мс» | **PARTIALLY CORRECT** (C-HANDOFF) |
| 11 | `sched_getaffinity` при старте | ст. 8:132 «`NumCPU` = физические ядра хоста» | **INCORRECT** (J-H4) |

Бриф описывает все 12 строк верно.

---

## 6. Blind-spot (B-1 … B-29)

Blind-spot содержит 4 High (B-1…B-4), 11 Medium (B-5…B-15) и 14 Low (B-16…B-29). **Из 15 High+Medium: 11 подтверждены напрямую, 2 (B-7, B-12) — по логике кода/документации без запуска, 2 (B-11, B-15) — `NOT CHECKED`; опровергнутых нет.** Шесть пунктов (B-1, B-2, B-3, B-4, B-5, B-14) проверены воспроизводимо запуском; три из них (B-1, B-2, B-4) противоречат решению или правке Master Brief.

| ID | Утверждение blind-spot | Статус текста | Доказательство |
|---|---|---|---|
| **B-1** | ст. 49: `TCPListener.File()` + `file.Fd()` делает **слушающий сокет блокирующим**; `ln.Close()` и `server.Shutdown()` зависают | **INCORRECT** (код небезопасен) — **бриф (R4/R10/K3) неправ, blind-spot прав** | **[E]** до: `nonblock=true`; после `File()`: `true`; после `File().Fd()`: **`false`**; `ln.Close()` при висящем `Accept` не вернулся за 2 с. **[L]** `os/file_unix.go` (`Fd` → `SetBlocking`) |
| **B-2** | ст. 2: блокирующий `RawSyscall` подвешивает **весь процесс** на ближайшем STW | **INCORRECT** (формулировка «встанут намертво горутины этой очереди» и правка S 2.9 брифа «блокируется только P+M» — обе неполны) | **[E]** горутина в `RawSyscall(SYS_READ)` на пустом pipe + `runtime.GC()`: **процесс завис** (`timeout 5` → код 124); тот же код с `syscall.Syscall`: GC за **622 мкс** |
| **B-3** | ст. 47: хук `Control` не меняет keepalive принятых соединений | **INCORRECT** | **[E]** см. таблицу в J-H12: на accepted-сокете `KEEPIDLE=15, KEEPINTVL=15` вместо заданных 30/10. Рабочие варианты — `KeepAliveConfig` или `KeepAlive: -1` + `Control` (**[E]** → 30/10) |
| **B-4** | ст. 57–58: `capset`/`PR_CAP_AMBIENT` действуют на один поток | **INCORRECT** | **[E]** `unshare -Ur`, 9 потоков: после `unix.Capset(all zero)` `CapEff` обнулён у **1** потока, у остальных 8 — `ffff…`. **[L]** `x/sys/unix.Capset` = `RawSyscall(SYS_CAPSET)` |
| B-5 | ст. 28: «в Go EINTR абстрагирован» | **INCORRECT** | **[E]** `RawSyscall6(SYS_EPOLL_WAIT, …, 3000 мс)` и `unix.EpollWait` при работающем GC-активном соседе вернули **`EINTR` почти мгновенно**; **[L]** `os_linux.go:480`: обработчики с `SA_RESTART`, но `epoll_wait` не перезапускается ни при каких флагах |
| B-6 | `CLONE_VFORK` приостанавливает только вызывающий поток | **INCORRECT** (16:111) | **[L]** `man 2 vfork`: «When vfork() is called in a multithreaded process, only the calling thread is suspended» |
| B-7 | page fault на mmap-файле невидим планировщику Go | **VERIFIED** (логика) | **[L]** `retake` берёт P только у потока в syscall (`proc.go:6681`), fault происходит в user-коде; запуск не выполнял — `PARTIALLY verified` |
| B-8 | `O_NONBLOCK` не действует на обычные файлы | **VERIFIED** | **[L]** `man 2 open`: «this flag has no effect for regular files and block devices; that is, I/O operations will (briefly) block when device activity is required» |
| B-9 | Go не «вычитывает сокет до `EAGAIN`» | **INCORRECT** (35:246, 38:124) | **[L]** `internal/poll/fd_unix.go:165–173`: одно `read`, паркуется только при `EAGAIN` |
| B-10 | запас под `GOMEMLIMIT`: стеки и метаданные рантайма уже входят в лимит | **INCORRECT** (52:203, 234) | **[L]** `runtime/debug/garbage.go:181–195`: лимит включает «all memory mapped, managed, and not released by the Go runtime»; **не** включает память C, `syscall.Mmap`, ядро |
| B-11 | кастомный `Resolver.Dial` ломает TCP-fallback; `search`/`ndots` продолжают работать | `NOT CHECKED` (код читал, эксперимент не ставил) | **[L]** `net/dnsclient_unix.go: exchange` выбирает транспорт по `network`, переданному в `Dial`; логика совпадает с описанием |
| B-12 | `SetReadDeadline` — абсолютный срок | **VERIFIED** (логика) | **[L]** `net.Conn.SetDeadline` — «absolute time»; запуск не выполнял |
| B-13 | неудачный `clone` для M фатален; `RLIMIT_NPROC` на UID хоста | **INCORRECT** (52:147) | **[L]** `runtime/os_linux.go:190–200`: `print("runtime: failed to create new OS thread…")`, `throw("newosproc")` |
| B-14 | в контейнере бесконечная рекурсия → OOM-kill раньше `stack overflow` | **VERIFIED** (20:155, 19:229, 21:126–134 — `INCORRECT` в формулировке «получите диагностику») | **[E]** без лимита: `fatal error: stack overflow`, exit 2; с `MemoryMax=512M`: **exit 137**, строк диагностики нет |
| B-15 | листинги глотают ошибки `Flush`/`Sync`/`Close` | `NOT CHECKED` (по коду очевидно, документация `bufio`/`close(2)` — не открывалась) | — |
| B-16 | 6:47–50: причинность про `fork`/spawn перевёрнута | `NOT CHECKED` | — |
| B-17 | 6:114: «начало с `_start`» для Go | **PARTIALLY verified** | **[E]** бинарник, импортирующий `net`, на этой машине — динамически линкованный ELF (cgo). Точка входа Go — `_rt0_amd64_linux`: `NOT CHECKED` построчно |
| B-18 | 9:136 pipeline stall и `top` | `NOT CHECKED` | — |
| B-19 | 36:294 `EPOLLRDHUP` | `NOT CHECKED` | **[L]** `netpoll_epoll.go:51` включает `EPOLLRDHUP` — подтверждается лишь регистрация |
| B-20 | 2:95 `scratch` + HTTPS/tzdata | `NOT CHECKED` | — |
| B-21 | 8:146–155 `LockOSThread` | `NOT CHECKED` | — |
| B-22 | 29:15 `nohup` и `&` | `NOT CHECKED` | — |
| B-23 | 58:217 `scp`/`go build` и метка `user_home_t` | `NOT CHECKED` | — |
| B-24 | 63:213–214 `syscall.SetNonblock` вне netpoller | `NOT CHECKED` | — |
| B-25 | 1:76–78 `GOMAXPROCS > N_CPU` = «thrashing» | `NOT CHECKED` | — |
| B-26 | 41:204 PHP-FPM и page cache | `NOT CHECKED` | — |
| B-27 | 12:166–168 Zero Page | `NOT CHECKED` | — |
| B-28 | 30:121–124 «zero-downtime» через socket activation | `NOT CHECKED` | — |
| B-29 | 48:327 `SO_BACKLOG` | **VERIFIED** | **[L]** `SO_BACKLOG` не найден ни в `x/sys/unix`, ни в `include/uapi/asm-generic/socket.h` **[R]** |

---

## 7. Medium по статьям (проверенные пункты)

Проверены те пункты, где можно получить доказательство без закрытых источников. **Остальные ≈259 Medium-пунктов не проверялись → `NOT CHECKED`** (перечень групп — § 10). Если ID уже разобран выше (в J-H, C-*, B-*), он здесь не повторён.

| ID | Тема | Статус | Доказательство |
|---|---|---|---|
| 1.3 | «монолитный статический ELF» | **PARTIALLY CORRECT** | **[E]** бинарник, импортирующий `net`, на этой машине (cgo включён, `gcc` есть) — динамический ELF; без `net`/`os/user` — статический |
| 1.5 | `N_CPU` = «физические ядра» | **INCORRECT** | **[L]** `getCPUCount` → `sched_getaffinity` (логические CPU) |
| 2.8 | `RawSyscall`: `err` как `uintptr(-1)` | **INCORRECT** | **[L]** `syscall_linux.go:55`: `err Errno` (положительное значение, например `EAGAIN = 11`) |
| 2.9 | блокирующий `RawSyscall` — «встанут все горутины очереди» | **INCORRECT** (формулировка статьи и правка брифа) | B-2 |
| 3.3 | `getcpu` в рантайме «для привязки» | **INCORRECT** | **[L]** в `runtime/` слово `getcpu` встречается только в `os_illumos.go` |
| 4.3 | `arch/x86/boot/head.S` | **INCORRECT** | **[R]** файла нет (`header.S`, `compressed/head_64.S`) |
| 4.13 | Firecracker «загружает ядро Linux напрямую за 5 мс» (4:131) | **INCORRECT** | **[R]** `firecracker/SPECIFICATION.md`: «takes <= 125 ms to go from receiving the Firecracker InstanceStart API call to the start of the Linux guest user-space /sbin/init process»; «<= 5 MiB» — это *память*, а не время |
| 5.1 | `cmd.Wait` блокирует горутину, не M | **INCORRECT** | J-H16 п.1 |
| 5.2 | ручное повышение `RLIMIT_NOFILE` | **OUTDATED** | C-NOFILE |
| 6.5 | `forkAndExecInChild` «на чистом ассемблере» | **PARTIALLY CORRECT** | **[L]** `syscall/exec_linux.go:138,221`: функции написаны **на Go** (в `nosplit`-режиме, без аллокаций); ассемблерные только низкоуровневые `rawVforkSyscall` |
| 6.8 | `WaitDelay`/`Cancel` как пропущенное | **VERIFIED** (факт) | **[L]** `api/go1.20.txt:271–273` |
| 12.2 | «до 4 ПБ при 5-уровневой адресации» (12:10) | **INCORRECT** | **[R]** `Documentation/arch/x86/x86_64/mm.rst`: при 5-уровневой схеме пользовательское пространство — **~64 PB**; 128 TB для 4-уровневой — **VERIFIED** |
| 12.3, 13.4, 14.x | ARM64 4/16/64 КБ, `PML4→PGD→PUD→PMD→PTE` | `NOT CHECKED` | — |
| 13.6 | страница рантайма 8 КБ | **VERIFIED** (факт) | **[L]** `internal/runtime/gc/sizeclasses.go:91`: `PageShift = 13` |
| 19.4 | non-PIE по умолчанию, hint `0xc000000000` | **VERIFIED** | **[E]** `readelf -h`: `Type: EXEC` для linux/amd64; **[L]** `malloc.go:523–533`: арены начинаются с `0x00c0<<32` |
| 19.11 | `make` >64 КБ — всегда в куче | **VERIFIED** (порог) | **[L]** `cmd/compile/internal/ir/cfg.go:19`: `MaxImplicitStackVarSize = 64 * 1024` |
| 21.x | `gostartcall` | **INCORRECT** | J-H2 |
| 25.5 | у `*os.File` есть финализатор | **VERIFIED** (факт) | **[L]** `os/file_unix.go:225`: `runtime.SetFinalizer(f.file, (*file).close)` |
| 26.3 | `dup2` и `FD_CLOEXEC` | **VERIFIED** (факт) | **[L]** `man 2 dup`: «The close-on-exec flag (FD_CLOEXEC) for the duplicate descriptor is off» |
| 27.4 | абстрактные сокеты (`@name`) в Go | **VERIFIED** (поддерживаются) | **[E]** `net.Listen("unix", "@fc-test-abstract")` → `err = nil` |
| 28.2 | `NotifyContext` «Go 1.15+» | **INCORRECT** | **[L]** `api/go1.16.txt:409` |
| 28.4 | «пакеты `net`, `os`, `io` автоматически игнорируют SIGPIPE» | **INCORRECT** | **[L]** `os/signal/doc.go:91–100`: на fd 1 и 2 запись в закрытый pipe **завершает** программу; на других — `EPIPE` |
| 28.6 | «канал по умолчанию имеет буфер 1» | **INCORRECT** | **[L]** `signal.go:114` |
| 29.4 | `http.NewServer()` | **INCORRECT** | J-H5 |
| 29.5 | `Type=simple` после `execve()` | **INCORRECT** | **[L]** `man systemd.service` |
| 30.5 | `LimitNOFILE` «на уровне cgroup» | **INCORRECT** | **[L]** `man systemd.exec` |
| 34.4/34.10 | детектор deadlock и `GOMAXPROCS` | **INCORRECT** | § 9.1 (**[E]**) |
| 34.9 | «`TryLock` только в тестах или через unsafe» | **INCORRECT** | **[L]** `TryLock` — публичный API с Go 1.18 |
| 38.2 | «оба подхода edge-triggered» | **CONTEXT-DEPENDENT** | **[L]** Go регистрирует `EPOLLET` (`netpoll_epoll.go:51`) и `EV_ADD|EV_CLEAR` (`netpoll_kqueue.go:39`) — **для Go верно**; API epoll по умолчанию level-triggered (**[L]** `man 7 epoll` описывает оба режима) |
| 43.4 | `net/http` в `fs.go` «анализирует типы дескрипторов»; «на других ОС — `WriteFile`» | **PARTIALLY CORRECT** | **[L]** в `net/http/fs.go` нет `sendfile`/`ReadFrom`; `fs.go` вызывает `io.CopyN`, а `sendfile` делает `TCPConn.ReadFrom` (`net/tcpsock.go:161`). **[L]** `sendfile` есть не только на Linux: `internal/poll/sendfile_unix.go`, `sendfile_solaris.go`, `sendfile_windows.go` |
| 47.14 | `SO_RCVBUF` ×2 | **VERIFIED** (факт) | **[L]** `man 7 socket`: «The kernel doubles this value … when it is set using setsockopt(2)» |
| 50.2 | RFC 793 заменён RFC 9293 | **VERIFIED** (факт) | **[R]** rfc-editor.org/rfc/rfc9293: `Obsoletes: 793, …` |
| 50.3 | `tcp_tw_recycle` как функция | **INCORRECT** | C-KNAMES |
| 50.4 | `MaxIdleConnsPerHost = 2` по умолчанию | **VERIFIED** (факт) | **[L]** `net/http/transport.go:62`: `const DefaultMaxIdleConnsPerHost = 2` |
| 51.5 | лимит одновременных cgo-lookup | **VERIFIED** (механизм) | **[L]** `net/rlimit_unix.go: concurrentThreadsLimit` — выводится из `RLIMIT_NOFILE`, при ошибке 500; для plan9/windows/js фиксированные 500 |
| 52.3 | `RLIMIT_RSS` не действует | **VERIFIED** (факт) | **[L]** `man 2 setrlimit`: «This limit has effect only in Linux 2.4.x, x < 30» |
| 53.2 | «7 типов namespaces» | **OUTDATED** | **[L]** `man 7 namespaces` (8, с Time) |
| 53.4 | Docker по умолчанию без userns | **VERIFIED** | **[R]** docs.docker.com/engine/security/userns-remap |
| 56.6 | `ModeSticky = 1<<20` | **VERIFIED** (факт) | **[E]** `fs.ModeSticky = 1048576` |
| 58.2 | «~44 syscalls блокирует docker-default AppArmor» | **INCORRECT** | **[R]** seccomp |
| 59.5 | `vm.core_uses_pid` | **INCORRECT** | `/proc/sys/vm` не содержит; есть `kernel.core_uses_pid` |
| 60.8, 61.3, 62.x | остальное | `NOT CHECKED` | — |
| 62.2 | `pthread_create` против `clone` | **PARTIALLY CORRECT** | **[L]** `os_linux.go:156–161` создаёт M через `clone`; `pthread_create` возможен только при cgo (`runtime/cgo`) — не открывалось |
| 62.9 | `gopark` на ассемблере | **INCORRECT** | **[L]** `gopark` написан на Go (`proc.go`); проверил только факт присутствия функции |
| 63.5 | 63:127: «`GOMAXPROCS` определяет количество потоков ОС (`M`), способных одновременно выполнять пользовательский байткод Go» | **PARTIALLY CORRECT** | **[L]** `go doc runtime.GOMAXPROCS`: «sets the maximum number of CPUs that can be executing simultaneously». Смысл (предел одновременно исполняющих Go-код потоков) верен; «байткод» — неточный термин (Go компилируется в машинный код); число P ≠ число M (M может быть больше при блокирующих syscall) |

---

## 8. Low

Отдельно Low-пункты не проверялись. Из ≈285 пересеклись с проверенным выше пять: 23.5 (`sys_linux_amd64.go` → `.s`) — **INCORRECT**; 56.6 (`ModeSticky = 1<<20`) — **VERIFIED** **[E]**; 40.6 (`fs.ReadStat`) — **INCORRECT**; 5.18 (`runtime.forkExec`) — **INCORRECT**; 13.11 (`MHeapMap_SpanInUse`) — **INCORRECT** в современном Go. Остальные ≈280 → **`NOT CHECKED`**. R9 брифа (`0x55AA` против `0xAA55`, УПРОЩ.) — **OPINION / упрощение**: проверка по спецификации не выполнялась, с судьёй не спорю.

---

## 9. Что пропустили оба брифа и ошибки самих брифов

### 9.1 Новые находки (не упомянуты ни в Master Brief, ни в blind-spot)

**N-1 · 13 диаграмм Mermaid из 172 не парсятся в вендорном Mermaid 10.9.1 — High (рендер).** **[E]** **После правок: исправлено (все 13 в модуле 2 — коммит `1598e5d8`; проект целиком — § 12).**
Метод: все 172 блока ```` ```mermaid ```` модуля извлечены в `blocks.json`, прогнаны через `mermaid.parse()` в Firefox headless (`file://`, `builder/assets/vendor/mermaid.min.js`, версия 10.9.1). `_sanitize_mermaid()` из `builder/converter.py` вызван над теми же блоками — **изменил 0 блоков**, то есть конвейер сборки этих ошибок не исправляет. Падают:

| Блок (ст.#№, строка в файле) | Причина |
|---|---|
| 15#1 (L76), 25#1 (L28), 29#1 (L32), 40#1 (L8), 40#5 (L179), 56#1 (L8), 56#4 (L171), 58#3 (L121), 60#2 (L149), 61#1 (L14), 62#5 (L208) | круглые скобки в **неквотированной** метке ребра `-->|open() или socket()|`, `|fork()|`, `|Нет (r/w)|` (Mermaid ждёт `SQE`, `PE`, …) |
| 40#1 (L8) | дополнительно вложенные кавычки `GoApp["os.Open("/etc/nginx/nginx.conf")"]` (подтверждает опасение брифа) |
| 35#1 (L12), 43#2 (L47) | синтаксис «толстой стрелки» с квотированной меткой `<==|"…"|` (ожидается `LINK`, найдено `STR`) |

Полный рендер `25#1` и `40#1` в той же среде дал **«Syntax error in text · mermaid version 10.9.1»** (скриншот проверен). Это ровно тот класс дефектов, что описан в `AGENTS.md` § 8–9: статический `audit_all.py` их не ловит, а браузер показывает бомбу вместо схемы. Оба брифа упоминают только 40:10/40:180 и «`:::class` в метках». **Масштаб по всему проекту, причины и рецепт починки — в § 12.**

**N-2 · Детектор deadlock молчит у любого бинарника с cgo — Medium.** **[E]** (`go1.27.1`, `GOMAXPROCS` задан через окружение)

| Сценарий (все остальные условия одинаковы) | `CGO_ENABLED=0` | cgo (по умолчанию при импорте `net`) |
|---|---|---|
| `mu.Lock(); mu.Lock()`, `GOMAXPROCS=1` | `fatal error: all goroutines are asleep` | **завис, детектор молчит** |
| то же, `GOMAXPROCS=8` | `fatal error` | **завис** |
| то же + фоновая горутина `select{}` | `fatal error` | **завис** |
| то же + живой `time.Ticker` | завис (таймер) | завис |
| то же + `net.Listen` + `Accept` | завис (netpoll) | завис |

Следствия для ст. 34 (34:84, 34:282): (а) детектор **не зависит** от `GOMAXPROCS`, а `runtime.GOMAXPROCS(0)` вообще ничего не отключает — это запрос текущего значения; (б) фоновая *заблокированная* горутина детектору не мешает; (в) мешают таймеры, netpoll, `signal.Notify` и **cgo**. **[L]** `runtime/proc.go:6418 checkdead` (`run > run0` → `return` при лишних M).

**N-3 · Вопрос Interview ст. 47 построен на неверной посылке — High.** **[E]** `ListenConfig{KeepAlive: 30s}` на принятом соединении даёт `SO_KEEPALIVE=1, TCP_KEEPIDLE=30, TCP_KEEPINTVL=15` (таблица в J-H12). Утверждение «лишь активирует `SO_KEEPALIVE`» неверно с Go 1.13; бриф ловит только «дефолт 7200 с» и импорт.

**N-4 · `unix.Capset` с `VERSION_3` требует массив из двух `CapUserData` — Medium.** **[L]** `x/sys/unix/ztypes_linux.go:3166–3180` (`CapUserHeader`, `CapUserData`, `LINUX_CAPABILITY_VERSION_3`); **[E]** корректный вызов в моём эксперименте передавал `&data[0]` массива `[2]CapUserData`. В ст. 58 передан один элемент.

**N-5 · Внутренние противоречия, которых нет в брифе — Medium.**
- ст. 28:163 «буфер канала по умолчанию 1» ↔ ст. 29:35 «рекомендуется буфер ≥1» (верно только второе; J-H16 п. 10).
- 20:72 («`RBP` сохраняется в современных версиях») ↔ 20:165/170 («отключён по умолчанию»).
- 59:258: `vm.core_uses_pid=0` «рекомендуется выставлять в 1».

**N-6 · `unix.EpollWait` тоже возвращает `EINTR` — Medium.** Blind-spot B-5 говорит о «сырых» syscalls; **[E]** не только `RawSyscall6`, но и `unix.EpollWait` (через `Syscall`) вернул `EINTR` при работающем GC. Рецепт «в Go EINTR абстрагирован» неверен и для обёрток `x/sys/unix`.

### 9.2 Ошибки и неточности в самих брифах

| # | Где | Что не так | Доказательство |
|---|---|---|---|
| E-1 | Judge § 1/§ 3: **R4/R10/K3** | Решение «`File()` не переводит в blocking — дефект отклонён» верно для самого `File()`, но не для листинга ст. 49, который вызывает `Fd()`; blind-spot B-1 прав | **[E]** § 3, K3 |
| E-2 | Judge J-H4: «62:256 рекомендует `uber-go/automaxprocs`» | В ст. 62 слова `automaxprocs` нет | `grep -n -i automaxprocs 62.*.md` — пусто |
| E-3 | Judge J-H6: «76 Go-блоков, 47 полных» | 75 и 46 | `python3`-экстракция + `grep '^package main'` |
| E-4 | Judge J-H14 (G3): «если длина некратна, `EINVAL` гарантирован» | `CONTEXT-DEPENDENT`: на btrfs (ядро 7.2) `O_DIRECT` с невыровненным буфером/длиной проходит без ошибки | **[E]** J-H14 |
| E-5 | Judge § 4 C-KNAMES: «`fs/futex.c` → `kernel/futex/` с 5.16» | Файла `fs/futex.c` не было; до 5.15 включительно — `kernel/futex.c` | **[R]** `torvalds/linux` по тегам v5.15/v5.16 (HTTP 404 для `fs/futex.c`) |
| E-6 | Judge J-H29: «алгоритм Нейгла» в числе ошибок ст. 63 | Формулировка 63:159 **верна** (Go включает `TCP_NODELAY`) | **[L]** `net/tcpsock.go:290` |
| E-7 | Judge J-H26: дефолт `sched_rt_runtime_us=950000` | зависит от дистрибутива и ядра (здесь `1000000`) | **[L]** `/proc/sys/kernel/sched_rt_runtime_us` |
| E-8 | Judge C-MARKUP: «≥21 узел `:::class` в метках в 14 статьях» | Мой подсчёт по `:::\w+"\]` — 18 узлов в 14 статьях | регэксп по `sources/` |
| E-9 | Judge J-H5: `netpollwake` «в рантайме нет» | есть, но только в `netpoll_aix.go` | **[L]** |
| E-10 | Judge J-H18/J-H9: советы «`epoll_pwait(-1)`» | подтверждено; но и `futex WAIT` — не признак блокировки на Go-мьютексе (см. J-H3) — дополнение, а не ошибка | **[E]** |
| E-11 | Blind-spot B-5 | не называет `unix.EpollWait` (см. N-6) — неполнота | **[E]** |

Остальные 100+ проверенных пунктов брифа и blind-spot подтвердились.

---

## 10. NOT CHECKED — что не проверено и почему

1. **Ядро Linux (внутреннее устройство):** CFS/EEVDF-детали (кроме версии 6.6), RT/fair server (6.12), `futex`-структуры, VMA/`mm_struct`, page fault, THP-поведение (`defrag`, `khugepaged`), `jbd2`-коммиты, XFS-журнал, `dm`/`md`, scheduler диска, conntrack, SYN-очередь, `tcp_death_row`/`tcp_time_wait`/`listen_sock`, `do_coredump`, SELinux/AppArmor-хуки, `sendpage`, `pid_hash_init`. Причина: ядро в сессии не просматривалось целиком; открыты только перечисленные в тексте файлы и man-страницы.
2. **Аппаратное:** латентности TLB/L1/L2/L3, NVMe, стоимость VM-exit, размер TLB, Zen/Apple регистры, `CLFLUSH`, DMA/когерентность. Причина: нет микроархитектурных первоисточников; измерено только локальное.
3. **Многоузловое NUMA:** удалённый доступ, `migratepages`, auto-NUMA, `MPOL_BIND` — на этой машине один узел.
4. **Стандарты и политики:** PCI DSS, SOC 2, ISO 27001 (56.2); Intel SDM, UEFI/Secure Boot (4.8, 4.9), RFC (кроме RFC 9293).
5. **Другие языки/рантаймы:** Java 21 VT, CMS, Python PEP 475, PHP-FPM, Tokio, jemalloc — не открывались.
6. **Kubernetes/Docker/systemd:** `requests.memory`↔`memory.min`, NodeSwap, `LimitNOFILE` в Docker, `ProtectSystem`, `Type=notify` таймауты, `FileDescriptorStoreMax` — не открывались (проверены только grace period, seccomp, userns, `Type=simple`, `LimitNOFILE`).
7. **Go: история версий:** непрерывные стеки 1.3, 2 КБ 1.4, адаптивный старт 1.19, история THP в 1.21.x, `disablethp` с 1.21.6 — release notes не открывались.
8. **Статьи целиком:** текст модуля я не перечитывал. Если утверждение не попало ни в один из двух брифов и не встретилось при проверке, оно **не** считается проверенным.
9. **Medium: ≈259 пунктов; Low: ≈270.** Перечень групп — ст. 3.4–3.18 (кроме 3.3), 4.1/4.2/4.4–4.12/4.15–4.23, 5.3–5.20 (кроме 5.1, 5.2), 6.1–6.14 (кроме 6.5, 6.8), 7.x, 8.x (кроме 8.1/8.8), 9.x (кроме 9.7/9.8), 10.x, 11.x (кроме 11.1–11.5, 11.10), 12.x–19.x (кроме названных), 20.x–22.x, 23.x–27.x (кроме 27.4), 31.x–33.x, 35.x–37.x, 39.x–42.x, 44.x–49.x, 52.x, 54.x–55.x, 57.x–61.x, 62.x (кроме 62.2, 62.9), 63.x (кроме 63.5).
10. **Не воспроизведено запуском** (только чтение кода/документации): `daemonize()` без guard (risk fork-bomb), `GroupCommitter`, `eBPF`-листинг (нет прав на загрузку BPF), `MADV_DONTFORK`, `sendfile` и `splice` пути, `CLONE_VFORK` + многопоточность, `O_DIRECT` на ext4/XFS (на машине только btrfs/tmpfs).

---

## 11. Приложение: воспроизводимость

Все эксперименты — короткие программы Go 1.27.1 + мини-`strace` на `ptrace` (C, 60 строк, `PTRACE_O_TRACECLONE`, `PTRACE_SYSCALL`). Файлы остались в scratchpad сессии; за пределы репозитория не выходили.

| Эксперимент | Что показывает |
|---|---|
| `stack.go` + `mytrace` | `StackInuse` 327 КБ → 67 МБ, `madvise` +0, `mmap` +10 |
| `mu.go` | 200 000 парковок на мьютексе/канале: 17/15 `futex` |
| `sig.go` | `os/signal`: 114 `rt_sigaction`, 0 `rt_sigtimedwait` |
| `mp.go` + `systemd-run -p CPUQuota=200%` | `GOMAXPROCS=2` при `go 1.27`, 24 при `go 1.24` |
| `fd.go`, `raw.go`, `ka.go`, `cap.go`, `eintr.go` | B-1…B-5 |
| `pid1.go` + `unshare -Ur --pid` | Go в PID 1: `SIGTERM` → exit 143 |
| `oom.go`, `rec.go` + `MemoryMax` | `SIGKILL` без диагностики |
| `dl/main.go` | детектор deadlock: cgo vs `CGO_ENABLED=0` |
| `wp/main.go` | гонка `runWithPipe`: 11 ошибок / 10 усечённых из 200 |
| `fc/main.go` | `FileConn` на listen-fd |
| `zero/main.go` | `/dev/zero` `MAP_SHARED` не видно потомку-`exec` |
| `dg.go` | UDS `SOCK_DGRAM`: без потерь и без реордеринга |
| `pool/main_test.go` | `sync.Pool` со срезом: 19,8 нс, 1 аллокация против 3,5 нс, 0 |
| `bench/main.go` | syscall 62/80 нс; DRAM 74–88 нс |
| `cs/` + `pp.c` | горутина ≈140 нс, поток ≈0,9 мкс на переключение |
| `mm/t.html` (Firefox headless, Mermaid 10.9.1) | 13 из 172 диаграмм не парсятся |


---

## 12. Mermaid: причины, рецепт починки для editor и предложение по скриптам (по всему проекту)

> **Статус: выполнено и закоммичено.** Разделы 12.1–12.6 сохранены как описание проблемы и хода работы (формулировки «предложение» относятся к моменту написания); итог внедрения — § 12.7.
>
> Дополнение к N-1 (§ 9.1). Здесь только то, что **проверено запуском** в вендорном Mermaid 10.9.1 (`builder/assets/vendor/mermaid.min.js`, Firefox headless, `mermaid.parse()`). Это проверка *синтаксиса*; визуальную эквивалентность исправленных схем при первом проходе я не сверял (позже сверял — § 12.7).

### 12.1 Масштаб: проблема не ограничена модулем 2
Все **2485** блоков ```` ```mermaid ```` из `sources/` (22 модуля, рекурсивно):

| Вариант | Не парсятся | Комментарий |
|---|:---:|---|
| Исходники как есть | **61** | в 15 модулях из 22 |
| Как их видит сборка: после `_sanitize_mermaid()` из `builder/converter.py` | **64** | санитайзер чинит 1 (`class Domain,succ;`, мод. 9 ст. 7), но **ломает 4** ранее рабочие схемы (см. 12.3) |
| Санитайзер с защитой от кавычек + правила 12.2 | **18** | все 13 диаграмм модуля 2 починены; остаток — в других модулях, нужен ручной разбор (12.4) |
| **После правок** (`8aef090d`, `1598e5d8`, `8a4bfb2e`, `a8d34615`), полная сборка + новый аудит | **0** | рантайм-разбор: не разобрано 0 из 2486; предупреждений `:::class` 0; `audit_all.py` завершается с кодом 0 |

Контрольный прогон нового аудита на состоянии HEAD до правок (старый конвертер + старые источники) дал **65**, а не 64: ещё одна диаграмма — `mindmap` ст. 40 модуля 10 — ломалась только в сборке, потому что `_extract_mermaid` срезал отступы (см. 12.7). Распределение 64 неработающих «как собирается» по модулям: 1 — 6, **2 — 13**, 3 — 10, 7 — 1, 10 — 1, 11 — 4, 12 — 3, 13 — 2, 14 — 12, 15 — 1, 16 — 1, 17 — 1, 20 — 1, 21 — 8. Статический `audit_all.py` показывает «0 Mermaid errors», потому что проверяет только заголовок и наличие `<svg`, а не разбор рантаймом (это прямо оговорено в `AGENTS.md` § 9).

### 12.2 Что именно сломано в модуле 2 и как чинить (13 диаграмм) — проверено
| Класс дефекта | Диаграммы (ст.#№, строка файла) | Как исправлять в `sources/` |
|---|---|---|
| **A. Круглые скобки в неквотированной метке ребра** `-->\|open() или socket()\|` | 15#1 (L76), 25#1 (L28), 29#1 (L32), 40#5 (L179), 56#1 (L8), 56#4 (L171), 58#3 (L121), 60#2 (L149), 61#1 (L14), 62#5 (L208) | Заключить метку в кавычки: `-->\|"open() или socket()"\|`. То же для `-.->\|…\|` и `==>\|…\|`. Правило механическое: *любая* метка ребра, содержащая `()`, `:`, `;`, `/`, `&` и т. п., должна быть квотирована; безопаснее квотировать все |
| **B. Вложенные двойные кавычки в метке узла** `GoApp["os.Open("/etc/nginx/nginx.conf")"]` | 40#1 (L8), 40#5 (L179, вместе с классом A) | Внутренние `"` заменить на `#quot;` (Mermaid-сущность) или на `'`: `GoApp["os.Open(#quot;/etc/nginx/nginx.conf#quot;)"]` |
| **C. «Толстая» двунаправленная стрелка с квотированной меткой** `A <==\|"текст"\|==> B` | 35#1 (L12), 43#2 (L47) | `A <== "текст" ==> B` |
| D. `:::class` внутри квотированной метки (**не падает, а печатает `:::имя` текстом**; C-MARKUP) — **исправлено после правок: 216 узлов в 167 статьях проекта, `a8d34615`** | 3, 4, 15, 44, 45, 46, 49, 51, 53, 55, 56, 57, 58, 63 (18 узлов в модуле 2) | Вынести `:::имя` наружу: `A["Текст"]:::entry` (а не `A["Текст:::entry"]`). Парсер не падает, поэтому `mermaid.parse` это не поймает — нужен отдельный регэксп `:::\w+"\]` |

**После правок:** правила A–C применены к 13 диаграммам модуля 2 (`1598e5d8`); класс D исправлен проектно (`a8d34615`). Проверка: все 172 блока модуля 2 дают **0 ошибок разбора** (в том числе блоки, которые не менялись, остаются рабочими).

### 12.3 Побочный дефект: `_sanitize_mermaid()` ломает 4 рабочие диаграммы
Регэксп `(\w+)\s*\[([^"\]]*\([^"\]]*\)[^"\]]*)\]` ищет «узел со скобками в неквотированном `[...]`», но **матчится и внутри уже квотированной метки**, если там есть `x[...(...)...]` (индексы срезов Go). Все четыре — модуль 21, они рабочие в исходнике и ломаются после санитайзера:

| Блок | Было | Стало после `_sanitize_mermaid` |
|---|---|---|
| 21 / `03. С…` #1 L24 | `F["…window[s[i]-'a']++…window[s[i-len(p)]-'a']--"]` | `…window["s[i-len(p)"]-'a']--"]` |
| 21 / `07. О…` #1 L41 | `PopTail["dq = dq[:len(dq)-1]<br>…"]` | `dq = dq[":len(dq)-1"]<br>…` |
| 21 / `10. B…` #1 L20 | `Backtrack["Unchoose: cur = cur[:len(cur)-1]"]` | `cur = cur[":len(cur)-1"]` |
| 21 / `22. Б…` #1 L19 | `M2["…ans[i & (i - 1)] + 1"]` | `ans["i & (i - 1)"] + 1` |

Исправление: применять первое и второе правила санитайзера только если перед позицией совпадения **чётное** число `"` в строке (то есть совпадение не внутри кавычек). С такой защитой эти 4 схемы снова парсятся.

### 12.4 Остаток (18 схем): причины и фактические исправления — **выполнено, `8a4bfb2e`**
Автоправила эти схемы не чинят; каждая исправлена вручную в `sources/`. В первой версии отчёта часть причин была названа по тексту ошибки парсера предположительно; после разбора файлов они уточнены (помечены ★).

| Блок | Причина | Исправление |
|---|---|---|
| 1 / `7. Цикл исполнения…` #3 | ★ id участника `Loop` совпадает с ключевым словом `loop` (не «непрерывное исполнение…») | `Loop` → `Spin` |
| 10 / `23. Server Sent Events` #3 | ★ в тексте сообщений реальный перевод строки (`id: 101 ⏎ data: {...}`) | `id: 101<br>data: …` |
| 11 / `26. Saga…` #3 | `Note over …` (синтаксис `sequenceDiagram`) во `flowchart` | узел `Note1[...]` с пунктирной связью `Orchestrator -.- Note1` |
| 11 / `28. Кэширование…` #6 | ★ вместо `classDef Def …` записано `class Def fill:…` (не «испорченные символы») | `classDef Def …` |
| 11 / `46. Версионирование…` #5; 3 / `21. HTTP 1.1…` #5 | ★ второе двоеточие в описании перехода `stateDiagram-v2` (`Deprecation: true`, `'Connection: close'`) | `#58;` (рисуется как `:`) |
| 17 / `3. JWT…` #1 | ★ у трёх строк потерян ключевой глагол `style` (`P fill:…`) | `style P fill:…`, `style Sign …`, `style Res …` |
| 12 / `6. Consistency модели` #3 | ★ опечатка `"] R` вместо `"| R` в метке ребра | `"| R` (петля `R -.-> R` с подписью) |
| 12 / `7. CAP теорема` #2; 14 / `7. CAP теорема на практике` #3 | стрелка `-.x` не существует | `--x` |
| 14 / `4. Network policies` #1; `5. Traffic shaping` #1 | ★ метка ребра открыта `\|"…`, но не закрыта кавычкой | добавлена закрывающая `"` (6 строк) |
| 14 / `8. Kubernetes networking` #2 | `Eth0 ==="veth-pair"=== VethHost` | `Eth0 == "veth-pair" === VethHost` |
| 13 / `10. Итоги раздела…` #1 | `[[wikilink]]` внутри `mindmap`; после снятия скобок ★ рендер **стирает** подписи вида `1. Текст` | скобки убраны, `1. ` → `№1 ` |
| 15 / `9. Тестирование внешних API` #1 | ромб `subgraph Decision{"…"}` недопустим | `Client --> Decision{"…"}` без `subgraph` |
| 20 / `4. Два указателя…` #1 | заголовки `subgraph` с ` - `, `=` без кавычек | `subgraph It1["…"]`, `subgraph It2["…"]` |
| 21 / `N Queens` #1; `1. Теория. DFS` #1 | `[ . Q . . ]` и `->` в неквотированном заголовке `subgraph` | `subgraph Board["…"]`, `subgraph Stack["…"]` |

### 12.5 План внесения в проект — выполнен
1. **Источники (`sources/`):** 13 диаграмм модуля 2 — `1598e5d8`; 18 диаграмм других модулей — `8a4bfb2e`; класс D (`:::class` в метках), 216 узлов — `a8d34615`.
2. **Конвертер (`builder/converter.py`), `8aef090d`:** защита правил санитайзера проверкой чётности кавычек (12.3); автоправила A–C для `flowchart`/`graph`; `_extract_mermaid` больше не срезает отступы (12.7).
3. **Аудит (`builder/audit_all.py`), `8aef090d`:** рантайм-разбор в headless Firefox по схеме из этого раздела (вендорный `mermaid.min.js`, временный HTTP-сервер на `127.0.0.1`, таймаут 300 с, флаг `--no-mermaid-runtime`, переменная `MERMAID_BROWSER`); падения — ошибки аудита (код возврата 1).
4. **Класс D** — статическое **предупреждение** в `audit_all.py` (`:::\w+"\]` по распакованному `html`); после исправления источников предупреждений 0. Не ошибка, потому что `mermaid.parse` такие блоки принимает.
5. **Документация:** `AGENTS.md` обновлён (§ 2, 3.2, 7, 9, 13, 14.7), `9d912bb2`.

### 12.6 Код, которым получены цифры (для воспроизведения; в репозиторий не добавлялся)
> Правило 2 здесь — исправленная версия: первый вариант (`.+?` с lookahead по концу узла) захватывал соседние узлы в строках вида `A["a"] & B["b"] --> …` и давал регрессию, найденную при сравнении отрисовки (§ 12.7). В репозиторий (`converter.py`) попала исправленная версия.

`fix.py` (правила A–C для `flowchart`/`graph`):
```python
import re,json,sys
ARROW=r'(?:<?-{2,}>?|<?={2,}>?|-\.+-?>?|~~~)'
def fix(code):
    lines=code.split('\n')
    if not lines or not re.match(r'\s*(flowchart|graph)\b',lines[0]): return code
    out=[]
    for l in lines:
        # 1. thick bidirectional with quoted label: A <==|"x"|==> B  ->  A <== "x" ==> B
        l=re.sub(r'<==\|"([^"]*)"\|==>',r'<== "\1" ==>',l)
        # 2. nested quotes in node label ["...("...")..."]
        def nest(m):
            inner=m.group(2)
            if '"' in inner: inner=inner.replace('"','#quot;')
            return m.group(1)+'["'+inner+'"]'
        l=re.sub(r'(\w+)\["((?:(?!"\]).)+)"\]',nest,l)
        # 3. unquoted edge labels: -->|text| -> -->|"text"|
        l=re.sub(r'('+ARROW+r')\|([^|"\n]+)\|',lambda m:f'{m.group(1)}|"{m.group(2).strip()}"|',l)
        out.append(l)
    return '\n'.join(out)
```
`mk.py` (генерация страницы-прогона; JS внутри) и `srv.py` (приёмник результатов):
```python
import json,sys
src,out,port=sys.argv[1],sys.argv[2],sys.argv[3]
b=json.load(open(src))
slim=[{"i":i,"c":x['code']} for i,x in enumerate(b)]
h='''<!doctype html><meta charset=utf-8><body><script src="mermaid.min.js"></script><script>
const blocks=%s;
const PORT=%s;
function send(q){return new Promise(r=>{const im=new Image();im.onload=im.onerror=()=>r();im.src='http://127.0.0.1:'+PORT+'/r?'+q;});}
(async()=>{
 mermaid.initialize({startOnLoad:false});
 let bad=[];
 for(const b of blocks){ try{await mermaid.parse(b.c);}catch(e){ bad.push(b.i); } }
 await send('bad='+bad.join(',')+'&n='+blocks.length);
 await send('done=1');
})();
</script>'''%(json.dumps(slim,ensure_ascii=False),port)
open(out,'w').write(h)
```
```python
import http.server,sys,urllib.parse
class H(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        q=urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        open(sys.argv[2],'a').write(repr(q)+"\n")
        self.send_response(204);self.end_headers()
    def log_message(self,*a):pass
http.server.HTTPServer(('127.0.0.1',int(sys.argv[1])),H).serve_forever()
```
Запуск: `python3 srv.py PORT result.txt &`, затем `firefox --headless --no-remote --profile <пустой каталог> file://…/t.html`; в `result.txt` попадает строка `bad=<индексы>`.

### 12.7 Итоги внедрения (после правок)

| Коммит | Что сделано |
|---|---|
| `8aef090d` | `builder/converter.py`: защита санитайзера по кавычкам, автоправила рёбер/узлов `flowchart`, сохранение отступов в `_extract_mermaid`; `builder/audit_all.py`: рантайм-разбор Mermaid, предупреждение про `:::класс` в метке |
| `1598e5d8` | `sources/` модуля 2: 13 диаграмм (классы A–C), 11 файлов, 67 строк |
| `8a4bfb2e` | `sources/` других модулей: 18 диаграмм (12.4), 18 файлов |
| `a8d34615` | `sources/`: `:::class` вынесен из меток, 216 узлов в 167 статьях |
| `9d912bb2` | `AGENTS.md`: описание аудита, правил санитайзера, правил авторинга Mermaid, хронология |

**Результат (полная сборка в scratch-каталог + новый аудит):** рантайм-разбор — не разобрано 0 из 2486; Mermaid-ошибок 0; предупреждений 0; битых ссылок 0; ошибок анкоров 0; `audit_all.py` завершается с кодом 0.

**Что выяснилось в ходе внедрения и чего не было в первой версии отчёта:**
1. **`_extract_mermaid` срезал отступы** (`l.strip()`), из-за чего `mindmap` ст. 40 модуля 10 ломался только в сборке (в исходниках он парсится). Исправлено: `rstrip` + `textwrap.dedent`. Побочный эффект — изменился вывод во всех 2486 блоках `dist` (отступы сохраняются); семантически изменились 295 блоков.
2. **Первая версия правила вложенных кавычек давала регрессию** (захват соседних узлов в строке `A["a"] & B["b"] --> …`, диаграмма ст. 37 модуля 1); найдена сравнением отрисовки, исправлена до коммита.
3. **Рендер `mindmap` Mermaid 10.9.1 стирает подпись узла вида `1. Текст`** (в т. ч. в `[..]`, `id["…"]`); рабочие варианты — `№1 …`, `1 · …`, `1 - …`.
4. Причины части из 18 схем в первой версии были названы предположительно (повреждённые символы, «Loop» как парсинг сообщения и т. п.); фактические — в таблице 12.4 (помечены ★).

**Проверка отрисовки (не только разбора):**
- Автоправила конвертера: из 295 блоков, чей вывод изменился, **248** рисуются идентично (текст, число узлов и рёбер), **46** были неработающими и теперь работают, **1** оставалась сломанной (исправлена вручную, 12.4), **регрессий нет** (после исправления п. 2).
- Класс D (193 затронутых диаграммы): у **84** текст, узлы и рёбра совпали, а число узлов с классом окраски выросло; для остальных 109 мой критерий давал расхождение из-за артефакта сравнения (регэксп вырезал `:::имя` вместе с соседним словом). На четырёх выборочных диаграммах число узлов и рёбер совпало, ст. 38 модуля 10 дополнительно проверена по скриншоту. Для остальных 105 диаграмм число узлов и рёбер отдельно не сверялось; правка чисто лексическая.
- Скриншотами проверены все 18 диаграмм из 12.4 и модульные диаграммы `25#1`, `35#1`, `40#1`.

**Что не сделано и остаётся в силе:**
- Репозиторный `dist/` не пересобирался: на готовом сайте исправления появятся после `python3 builder/build_all.py --all`.
- Фактические ошибки текста статей модуля 2 (разделы 2–7 этого отчёта) **не исправлялись**.
- Рантайм-аудит требует Firefox; без него он пропускается с предупреждением (флаг `--no-mermaid-runtime`).
- Проверка Mermaid — синтаксическая; визуальная верность по-прежнему проверяется человеком или скриншотами.
