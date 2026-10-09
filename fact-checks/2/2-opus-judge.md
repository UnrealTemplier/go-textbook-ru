# Master Fact-Check Brief · Модуль 2 «Устройство и работа ОС»

> **Роль:** senior research judge (Opus).
> **Входные данные:**
> - `sources/2. Устройство и работа ОС/` — 63 статьи, текущее состояние. Модуль уже проходил один фактчек в коммите `a8006dfc docs(factcheck): correct module 2 technical claims` (2026-09-24), см. § 5.
> - `2-gemini-scout.md` — 22 кандидата (11 High, 8 Medium, 3 Low).
> - `2-sonnet-alt.md` — 738 кандидатов (107 High, 341 Medium, 290 Low), 13 сквозных тем (T1–T13), таблица числовых расхождений.
>
> **Адресат:** следующий шаг конвейера, первичный фактчек по источникам.

---

## 0. Как пользоваться этим брифом

1. **Это не вердикт.** Бриф говорит, *что* проверить и *почему*, и называет решающий источник. Окончательный статус (VERIFIED / INCORRECT / PARTIALLY CORRECT / OUTDATED / CONTEXT-DEPENDENT / OPINION / NOT CHECKED) присваивает фактчекер.
2. **Улики судьи.** Часть пунктов я сверил сам. Такие места помечены **[улика судьи]** с путём и строкой. Использовалось:
   - локальный тулчейн **go1.27.1 linux/amd64** (`/usr/local/go/src`);
   - `golang.org/x/sys v0.46.0` и `golang.org/x/sync v0.22.0` из локального кэша модулей;
   - извлечение всех 76 Go-блоков модуля и прогон `gofmt -e` и `go vet` (§ 4, C-COMPILE);
   - `grep` по тексту статей: каждая находка обоих брифов прослежена до конкретной строки.

   Это сильная подсказка, но не замена проверки. Тулчейн показывает поведение только 1.27.1; границы версий («с Go 1.xx») надо подтверждать по release notes. Утверждения о ядре Linux, железе, systemd, K8s, Docker я **не** проверял по первоисточникам, только указываю решающий источник.
3. **Названия статей у Gemini не совпадают с файлами.** Например, «32. Разделяемая память (Shared Memory). POSIX и System V shm.md» на деле файл `32. Shared Memory и race condition между процессами.md`, а «28. Сигналы в Linux. Архитектура и надёжная доставка.md» — файл `28. Сигналы в Linux.md`. Номера статей при этом верны. Я прошёл по всем 22 кандидатам: суть 19 из них в тексте есть. Цитаты кода у Gemini местами неточны (G15, G16). Номера строк у Gemini не совпадают с файлами, поэтому ориентируйтесь на строки из этого брифа.
4. **Происхождение находок:** `G#` — кандидат Gemini; `S n.m` — строка Sonnet (номер статьи.порядковый номер); `S:T#` — сквозная тема Sonnet; `J` — добавлено судьёй.
5. **Типы находок:** **ФАКТ** — фактическая ошибка; **КОД** — пример не компилируется или не делает заявленного; **API** — несуществующий идентификатор, флаг или функция; **УСТАР.** — устарело; **ДОПУЩ.** — скрытое допущение (версия, ОС, архитектура); **ПРОТИВ.** — противоречие внутри статьи или между статьями; **ЧИСЛО** — цифра без источника или расходится с другими статьями; **УПРОЩ.** — допустимое учебное упрощение, нужна разве что оговорка; **МНЕНИЕ** — оценка, поданная как факт; **РАЗМЕТКА** — дефект рендеринга, а не факт.
6. **Порядок работы фактчекера:** § 2 (High) → § 3 (конфликты брифов) → § 4 (кластеры) → § 5 (остатки прошлого фактчека) → § 6 (Medium по статьям) → § 7 (Low). Пункты из § 8 («Отклонено») перепроверять не нужно, если не появятся новые улики.

---

## 1. Сводка

| Категория | Кол-во | Комментарий |
|---|:---:|---|
| High-блоки (после слияния) | 31 | объединяют ≈95 строк обоих брифов; ≈50 подтверждены судьёй по исходникам Go или `go vet` |
| Конфликты между брифами | 12 | у каждого указана решающая улика |
| Сквозные кластеры | 17 | одна и та же проблема в нескольких статьях |
| Остатки прошлого фактчека `a8006dfc` | 12 мест | исправление сделано частично, и в статье осталось противоречие |
| Medium (после слияния) | ≈ 320 | § 6, по статьям |
| Low | ≈ 285 | § 7, компактно |
| Отклонено или понижено как ложное срабатывание | 11 | § 8, с уликами |

**Общая картина.** Gemini дал узкий, но точный по сути список: 19 из 22 кандидатов подтверждаются текстом. Почти всё, что нашёл Gemini, нашёл и Sonnet. Уникальны у Gemini только G2 п.4, G7 (детали stackcache), G9 (детали по macOS), G10 п.1, G21 (удалённые sysctl) и G22. Sonnet охватил модуль на порядок шире, и его утверждения о Go, которые я перепроверил, подтвердились. Ложных срабатываний у Sonnet мало (§ 8). Главная слабость Sonnet — инфляция приоритетов: 107 High при том, что часть из них — числа, терминология или пропуски.

**Главные изменения приоритетов:**
- **G10 п.1 отклонён:** `syscall.Setuid` в Go ≥1.16 на Linux действует на все потоки. Код ст. 57 верен; ошибка в тексте ст. 56 (§ 3, K1).
- **G14 отклонён:** утверждения «sendfile читает из сокета» в ст. 43 нет.
- **G20 повышен с Low до High** как кластер: разорванные строковые литералы ломают компиляцию в 17 статьях. Список статей у Gemini почти весь неверен, у Sonnet точен (§ 3, K4).
- **G15, G16, G17 повышены с Medium до High:** код не компилируется или даёт заведомо неверный результат.
- **G12 повышен с Medium до High:** прямое противоречие ст. 48 и ст. 50, плюс в ст. 50 перепутаны MSL и `TCP_TIMEWAIT_LEN`.
- **Sonnet High понижены до Medium:** S 2.2, 3.1, 3.3, 4.1–4.5 (Medium, верхняя граница), 9.1, 9.2, 14.1, 21.1 (пропуск), 28.2, 30.1, 31.2, 35.1, 58.2. Причины: числа без проверки, терминология, периферийные утверждения, пропуски вместо ошибок.
- **Новый кластер C-FIX** (§ 5): прошлый фактчек `a8006dfc` исправил часть мест, но оставил старые формулировки рядом. Отсюда большинство «внутренних противоречий» модуля.

---

## 2. High: проверить в первую очередь

### J-H1. Модель обработки сигналов в Go: `sigwaitinfo` и блокировка через `rt_sigprocmask` (ст. 28, строки 109–111, 220) · ФАКТ
*Источники: G5, S 28.1; связанные S 62.7, S 28.8.*
- **Утверждение:** «Go runtime блокирует целевые сигналы через `rt_sigprocmask` на всех тредах, кроме основного. На основном треде запускается фоновый goroutine, который блокируется на `sigwaitinfo`».
- **Почему проверять:** в Go обработчики ставятся через `rt_sigaction` (`sigtramp` → `sighandler` → `sigsend`). Сигналы обрабатываются на `gsignal`-стеке (`sigaltstack`) того потока, куда их доставило ядро. Затем `os/signal` получает их через `signal_recv` (note/futex). Синхронные `SIGSEGV`/`SIGBUS`/`SIGFPE` и `SIGURG` (вытеснение) по природе потоковые и через `sigwaitinfo` получены быть не могут.
- **[улика судьи]** `grep -rln sigwaitinfo /usr/local/go/src/runtime /usr/local/go/src/os/signal` ничего не находит.
- **Решающий источник:** `runtime/signal_unix.go` (`sighandler`, `sigsend`), `runtime/sigqueue.go` (`signal_recv`), `runtime/sys_linux_amd64.s` (`sigtramp`), `os/signal/signal.go`.
- **Приоритет: High.**

### J-H2. Рост и переполнение стека горутин: `mmap`/`madvise` на каждый рост, guard page, `SIGSEGV`, лимит `ulimit -v` (ст. 21 §4 и Итоги; ст. 19; ст. 20) · ФАКТ + API
*Источники: G7, S 21.2, 21.3, 21.4, 21.6, 21.7, 21.11, 21.13, 19.10, 19.14, 19.15, 20.7, 20.10.*
- **Утверждения (ст. 21):**
  - строки 88–90: `newstack` «аллоцирует через `mmap`», копирует «если там есть жизненно важные данные», вызывает `madvise(MADV_DONTNEED)` («критически важный шаг»);
  - строка 126: лимит — «`ulimit -v` или `RLIMIT_AS`»;
  - строка 136: «Это не паника Go, а `SIGSEGV`, перехваченный рантаймом»;
  - строка 174: `go tool pprof -top http://host/debug/pprof/stack`;
  - строки 185–194: `//go:nosplit` как «защита от рекурсии»;
  - строка 202 (итог): рантайм использует `mmap` + `madvise(MADV_DONTNEED)` для динамического роста стека;
  - символ `gostacksplit`;
  - ст. 19: «стек горутины защищён guard page», «`morestack` делает `mmap`»;
  - ст. 20: «fatal error: stack overflow — контролируемое завершение через panic».
- **Почему проверять:**
  1. Стек берётся из `stackpool`/`stackcache` (порядки 2–16 КБ на Linux) или из `stackLarge`/`mheap`, без отдельного `mmap` на каждый рост.
  2. Старый стек возвращается через `stackfree`, `madvise` при росте нет.
  3. `copystack` копирует всегда.
  4. Переполнение детектирует пролог функции (сравнение SP со `stackguard0`), а не guard page; сигнала нет.
  5. Лимит задаёт `maxstacksize`, который меняется через `debug.SetMaxStack`.
  6. Эндпоинта `/debug/pprof/stack` не существует.
  7. Линкер отклоняет рекурсию в цепочках `nosplit`.
- **[улика судьи]**
  - `runtime/stack.go:1202–1207`: печать `runtime: goroutine stack exceeds <maxstacksize>-byte limit`, затем `throw("stack overflow")`. Это fatal error, а не паника и не сигнал.
  - `runtime/proc.go:164–166`: `maxstacksize = 1000000000` (64-bit) / `250000000` (32-bit).
  - `runtime/malloc.go:136,150`: `_StackCacheSize = 32*1024`, `_NumStackOrders = 4` на Linux, то есть пул 2/4/8/16 КБ. У Gemini «stackcache от 2 до 32 КБ» неточно.
  - `net/http/pprof/pprof.go:100–104`: обработчики `/debug/pprof/`, `cmdline`, `profile`, `symbol`, `trace`; профиля `stack` в `runtime/pprof` нет.
- **Решающий источник:** `runtime/stack.go` (`newstack`, `copystack`, `stackalloc`, `stackfree`), `runtime/malloc.go`, `cmd/internal/obj/x86/obj6.go` (пролог), `cmd/link/internal/ld/stackcheck.go` (проверка nosplit), `runtime/debug.SetMaxStack`.
- **Приоритет: High.** Ошибка в центральном разделе статьи, повторяется в Interview и Итогах ст. 19, 20, 21.

### J-H3. «`sync.Mutex` и каналы построены на futex» (ст. 1, 3, 22, 23, 24, 32, 34, 60, 63) · ФАКТ + ПРОТИВ. (кластер C-FIX)
*Источники: S:T1, S 1.1, 3.2, 22.5, 23.1, 24.2, 32.4, 34.3, 34.6, 60.6, 63.2.*
- **Утверждения:**
  - ст. 23:45: «Именно на нём [futex] построены `sync.Mutex`, `sync.RWMutex` и каналы»;
  - ст. 23, Interview Q3: «вызывается `futex(FUTEX_WAIT)`, ядро усыпляет горутину»;
  - ст. 24:145: «`futex(FUTEX_WAIT)` → захвачен `sync.Mutex` или `channel`»;
  - ст. 3:190–192: «`sync.Mutex` и системный примитив futex»;
  - ст. 1:71: канал = «`hchan` + `netpoller` (epoll/kqueue) + атомарные операции»;
  - ст. 63, таблица: «sync.Mutex → futex», «Channel → runtime.sema + epoll/futex».
- **Почему проверять:** медленный путь `sync.Mutex` — `runtime_SemacquireMutex` → `semaRoot` → `gopark`, без syscall. Futex рантайм вызывает на уровне M (`note`, `runtime.mutex`), когда поток простаивает. Каналы — это `hchan.lock` (runtime.mutex) + `gopark`; netpoller они не используют. В ст. 23:79–88 (§ Go) и в ст. 33 это уже написано верно: прошлый фактчек исправил одно место и оставил соседние.
- **[улика судьи]** `internal/sync/mutex.go:95,149`: `lockSlow` → `runtime_SemacquireMutex(&m.sema, queueLifo, 2)`. В `runtime/sema.go` и `runtime/chan.go` вызовов futex нет; в `sema.go:9` есть только комментарий-сравнение «same goal as Linux's futex».
- **Решающий источник:** `internal/sync/mutex.go`, `runtime/sema.go`, `runtime/chan.go`, `runtime/lock_futex.go`.
- **Приоритет: High.** Ошибка повторяется в 9 статьях и в ответах для собеседований, а с соседними абзацами противоречит прямо.

### J-H4. `GOMAXPROCS`, cgroup и `automaxprocs`: устарело с Go 1.25 (ст. 1, 7, 8, 30, 52, 54, 62, 63) · УСТАР. + ПРОТИВ.
*Источники: G11, S:T2, S 1.5, 8.1, 8.8, 11.10, 30.14, 52.2, 54.3, 62.1, 62.4, 63.5.*
- **Утверждения:**
  - ст. 8:134 и 8:192: «Всегда подключайте `go.uber.org/automaxprocs`»;
  - ст. 62:256: «используйте `uber-go/automaxprocs` в средах Kubernetes»; число P «фиксируется при старте»;
  - ст. 52: «Go не распознаёт cgroup без явных `GOMEMLIMIT` и `GOMAXPROCS`»;
  - ст. 8: «`NumCPU` = число физических ядер хост-ноды».
- **Почему проверять:** с Go 1.25 рантайм сам учитывает CPU-квоту cgroup (v1/v2) и периодически обновляет `GOMAXPROCS`. Это работает, только если в `go.mod` стоит `go ≥ 1.25`; для 1.24 и ниже действует старое поведение по GODEBUG. `GOMEMLIMIT` по-прежнему задаётся вручную. `NumCPU` — логические CPU из маски `sched_getaffinity`, а не физические ядра. Ст. 54:150 про Go 1.25 знает, но её Итог 3 («требуется явная настройка») устарел.
- **[улика судьи]** `runtime/debug.go:20–45` (учёт «cgroup CPU quota», «periodically updates», «containermaxprocs=0 is default for language version 1.24 and below»); `internal/godebugs/table.go:30,71` (`containermaxprocs`, `updatemaxprocs`, `Changed: 25`); `runtime/cgroup_linux.go`, `internal/runtime/cgroup/`.
- **Решающий источник:** Go 1.25 release notes; go.dev/blog/container-aware-gomaxprocs; `runtime/debug.go`.
- **Нюанс для правки:** `automaxprocs` нужен при `go` < 1.25 в `go.mod`. Явный `GOMAXPROCS` отключает автообновление.
- **Приоритет: High.**

### J-H5. Несуществующие API, флаги и идентификаторы · API
*Источники: S:T3 и S § 3.1 (полный список), G1, G9 п.2, G10 п.3, G16. Каждую строку проверяет фактчекер.*

| Ст. | Что в тексте | Улика судьи / что проверить |
|---|---|---|
| 11 (201–202) | `GODEBUG=gcresidency=1` «в Go 1.21+» | флага нет; проверить `runtime/runtime1.go` (`dbgvars`), `internal/godebugs/table.go` |
| 13 (110) | `GODEBUG=pagealloc=1`; `MAP_HUGETLB` для кучи Go | флага нет; реальный — `disablethp` (1.21.6+) |
| 13 | `MHeapMap_SpanInUse` | идентификатор Go ≤1.2 |
| 17 (185) | `debug.MemoryLimit()` | нет; `runtime/debug/garbage.go:181,231` — только `SetMemoryLimit` (`SetMemoryLimit(-1)` возвращает текущее значение) |
| 9 (133) | «механизм `sched_gomaxprocs`» | нет такого |
| 20 (165, 170) | `GOEXPERIMENT=framepointer`, `stkblk` | см. J-H18 |
| 21 | `gostacksplit`, `/debug/pprof/stack` | см. J-H2 |
| 25 | `os.NewFile(int32, …)` | `os/file.go:133`: `NewFile(fd uintptr, name string)` |
| 26 (26) | `fds, err := syscall.Pipe2([]int{0,1}, …)` | `syscall/syscall_linux.go:295`: `Pipe2(p []int, flags int) error`. Gemini процитировал код неточно (`Pipe2(syscall.O_NONBLOCK)`), но вывод тот же |
| 29 (140) | `github.com/coreos/go-systemd/v22/sdnotify` | в go-systemd v22 пакет называется `daemon` (ст. 30 использует его верно) |
| 32 (67–75) | `syscall.ShmOpen/ShmSetSize/ShmUnlink` | `go vet`: `undefined: syscall.ShmOpen` |
| 33 (116, 218, 241) | «пакет `sync/semaphore` с Go 1.21», «на `semaRoot`» | в stdlib нет (`ls /usr/local/go/src/sync`); `x/sync/semaphore` устроен на `container/list` + `sync.Mutex` (x/sync v0.22.0, `semaphore.go:9–11,28–33`) |
| 34 | `GODEBUG=asyncpreempt=1`, `go tool pprof -goroutine` | есть только `asyncpreemptoff`; флага `-goroutine` у pprof нет |
| 36, 38, 47, 48 | `runtime.wakeG`, `netpollLock`, `netpollwake`, `runtime.park`, `type netpoller struct` | в рантайме нет; есть `netpollready`, `netpollunblock`, `injectglist`, `gopark`, `pollDesc.lock` |
| 37 | `netpollkqueue.go`, `netpollwindows.go`, `netpollLink` | файлы называются `netpoll_kqueue.go`, `netpoll_windows.go` |
| 42 (184) | `os.O_DIRECT` | `go vet`: `undefined: os.O_DIRECT`. Gemini процитировал файл как «log.dat», в тексте «data.bin» |
| 47 (198, 232), 48 | `net.ListenConfig{Backlog: …}` | `net/dial.go:816–855`: полей `Backlog` нет (`Control`, `KeepAlive`, `KeepAliveConfig`, MPTCP) |
| 49 (163, 189) | `SO_MAX_CONN`, `SetsockoptInt(…, SOL_SOCKET, 1024, 65535)` | см. J-H11 |
| 51 (129) | `GODEBUG=netdns=experimentalgo` | нет; значения `go`, `cgo`, `1`, `2` и сочетания вида `go+1` |
| 57 (216, 242) | `syscall.CAP_CLEAR`; `SysProcAttr.NoSetuid/NoSetgid` | нет; для наследования — `SysProcAttr.AmbientCaps` |
| 57 | `github.com/capabilities/cap` | такого модуля нет; реальные — `kernel.org/pub/linux/libs/security/libcap/cap`, `syndtr/gocapability` |
| 58 (235) | `unix.CapHeader/CapData` | `go vet`: `undefined: unix.CapHeader`; правильно `unix.CapUserHeader/CapUserData` |
| 59 | `dlv core … heap` | у Delve нет команды `heap`; для дампов Go — `golang.org/x/debug/cmd/viewcore` (проверить статус) |
| 29 | `http.NewServer()` | нет |
| 53 | `runtime.Grow` | нет |
| 40 | `fs.ReadStat` | нет |
| 5 | `runtime.forkExec` | нет; `syscall.forkExec` / `forkAndExecInChild` |
| 23 | `src/runtime/sys_linux_amd64.go` | файла нет; есть `.s` |
| 4 (85, 89) | `arch/x86/boot/head.S` | см. § 6, ст. 4 |

- **Приоритет: High** для всех строк, где идентификатор встречается в коде, в рекомендации или в Interview. Для упоминаний внутри повествования — Medium.

### J-H6. Код-примеры, которые не компилируются (17 статей с разорванными литералами плюс отдельные дефекты) · КОД (кластер C-COMPILE)
*Источники: G20, G15, G16, G17, S:T4, S § 3.2.*
- **[улика судьи]** Из 76 Go-блоков модуля полных программ (`package main`) 47. `go vet` (Go 1.27.1, x/sys v0.46.0):
  - **компилируются (17):** ст. 2, 5 (1-й), 14, 16 (1-й), 20, 27 (2-й), 28, 31 (1-й), 42 (1-й, 3-й), 43 (2-й, 3-й), 46, 50, 54, 55, 57;
  - **не компилируются (26);**
  - **требуют сторонних модулей (3):** ст. 29 (`go-systemd/.../sdnotify` — такого пакета нет), ст. 30 (`go-systemd/.../daemon`), ст. 61 (`cilium/ebpf`).
- **Разорванные строковые литералы** (`"…\n` + перевод строки): ≈35 мест в **17 статьях — 5, 6, 7, 10, 17, 18, 19, 27, 29, 39, 40, 44, 49, 51, 53, 56, 61**. Список совпадает с Sonnet. В статьях 4, 11, 16, 24, 30, 42, 57 из списка Gemini разорванных литералов **нет**.
  - **Происхождение:** механический артефакт. В ст. 5 в первичном коммите `2d3bd27d` литерал был целым (`\n`), а разорван в редакторском переписывании `68d52870`. Последовательность `\n` превратилась в реальный перевод строки. Тот же механизм испортил KaTeX (`\t` → TAB, см. C-MARKUP).
  - **Исправление:** механическое восстановление `\n` в 17 статьях. Сверять с `git log -p` по каждой статье.
- **Прочие ошибки компиляции:**

  | Ст. | Ошибка (`go vet`) |
  |---|---|
  | 12, 16 (2-й) | `syscall.Madvise` с 3 аргументами; сигнатура `Madvise(b []byte, advice int)` |
  | 13 | неиспользуемый `"unsafe"` |
  | 26 (3-й), 41 | неиспользуемый `"log"` |
  | 31 (3-й) | неиспользуемый `"os"` |
  | 32 | `undefined: syscall.ShmOpen` |
  | 42 (2-й) | `undefined: os.O_DIRECT` |
  | 47 | неиспользуемый `"time"` |
  | 48 | неиспользуемый `"fmt"` |
  | 58 | `undefined: unix.CapHeader` |

  Фрагменты без `package` (ст. 25 `NewFile`, ст. 26 `Pipe2`, ст. 35 `setNonblocking`, ст. 27 FD passing через `Mmsghdr`) не компилируются по сигнатурам; это видно в S 25.1, 26.1, 35.2, 27.2. Ошибки, скрытые за разорванными литералами (ст. 18 `unsafe`/`bytes`, ст. 40 `FileMode`, ст. 61 `embed`/`Maps.Lookup`), проявятся после починки литералов.
- **Компилируются, но не делают заявленного:** ст. 14 (`badPattern`, J-H23), 16 (1-й), 26 (`runWithPipe`, J-H16), 31 (1-й, `/dev/zero`, J-H15), 40 (`os.FileMode(stat.Mode)`, J-H16), 43 (`writeDirectIO`, J-H13), 46 (`GroupCommitter`, J-H20), 10 (`Setpriority`, J-H25), 34 (`acquireWithTimeout`, J-H21), 49 (тюнинг backlog, J-H11).
- **Решающий источник:** Go spec (String literals, Import declarations); прогон `go vet` на извлечённых блоках.
- **Приоритет: High.**

### J-H7. Netpoller: `EPOLLONESHOT` в Итогах, регистрация «после EAGAIN», `close()` → `EPOLLHUP` (ст. 38, 35, 36, 48, 63) · ФАКТ + ПРОТИВ. (C-FIX)
*Источники: G4, S 38.1, 35.4, 36.4, 48.4, 63.1; связанные S 38.3, 38.5, 9.14.*
- **Утверждения:**
  - ст. 38:190: «Флаги `EPOLLONESHOT` и `EV_ONESHOT` гарантируют точечный контроль». Тело статьи (38:116) и ст. 62:267 верно говорят про `EPOLLET` без ONESHOT.
  - ст. 35, 36 (диаграмма), 48: fd регистрируется в epoll «после `EAGAIN`»; ст. 38, 49, 62 — «один раз при создании».
  - ст. 63:140 (Interview): `close()` порождает `EPOLLHUP`/`EPOLLERR`, `Read` вернёт `io.EOF` или `EBADF`.
- **[улика судьи]** `runtime/netpoll_epoll.go:51`: `EPOLLIN | EPOLLOUT | EPOLLRDHUP | EPOLLET`; `ONESHOT` в файле не встречается. Регистрация идёт в `netpollopen` при создании pollDesc. При локальном `Close` → `pollDesc.evict` → `runtime_pollUnblock` ошибка будет `net.ErrClosed` (`internal/poll/fd.go:16–20`, `errNetClosing`, «use of closed network connection»).
- **Решающий источник:** `runtime/netpoll_epoll.go`, `runtime/netpoll.go`, `internal/poll/fd_unix.go`, `internal/poll/fd_poll_runtime.go`; man 7 epoll (закрытие fd удаляет его из interest list).
- **Приоритет: High** для 38.1 и 63.1; **Medium** для 35.4, 36.4, 48.4 (уровень схемы).

### J-H8. Unix Domain Sockets: «`SOCK_DGRAM` ненадёжен» и код передачи FD (ст. 27, строка 20; листинг FD passing) · ФАКТ + КОД
*Источники: G6, S 27.1, 27.2.*
- **Утверждение (27:20):** «`SOCK_DGRAM` — ненадёжный… Сообщения могут теряться или приходить вне порядка».
- **Почему проверять:** man 7 unix: в Linux датаграммные сокеты домена UNIX надёжны и не переупорядочивают сообщения. При заполненной очереди отправитель блокируется или получает `EAGAIN`.
- **Код FD passing:** `unix.Mmsghdr{…Control: unix.Cmsghdr{…}}` + `Sendmmsg` в listener-fd не компилируется и по сути неверен. Правильно: `unix.Sendmsg(fd, data, unix.UnixRights(fds…), nil, 0)` или `(*net.UnixConn).WriteMsgUnix` + `unix.ParseUnixRights`.
- **Решающий источник:** man 7 unix; `net/af_unix.c`; `x/sys/unix` (`UnixRights`, `Sendmsg`); `net/unixsock.go`.
- **Нюанс:** утверждение верно только для Linux. На других ОС семантика может отличаться, и это стоит оговорить.
- **Приоритет: High.**

### J-H9. `ltrace` «не требует ptrace, работает через `LD_PRELOAD`» и диагностика futex в strace (ст. 24, строки 90, 127, 144–145) · ФАКТ + ПРОТИВ. (C-FIX)
*Источники: G8, S 24.1, 24.2.*
- **Утверждения:**
  - 24:90: «он не требует прав на `ptrace` и работает практически полностью в user-space»;
  - 24:127: «`LD_PRELOAD` (механизм, который использует `ltrace`) конфликтует с аллокатором Go (`mmap` + `sbrk`-эмуляция)»;
  - 24:144–145: «`epoll_pwait(-1)` → возможный баг netpoller»; «`futex(FUTEX_WAIT)` → захвачен `sync.Mutex` или channel».
- **Почему проверять:** ст. 24:168 (Interview, исправлено в `a8006dfc`) сама говорит, что ltrace работает через ptrace и `int3` на PLT, то есть статья противоречит себе. «sbrk-эмуляции» в Go нет. В Go `futex WAIT` — норма для простаивающих M; `epoll_pwait(-1)` на неактивном сервисе тоже норма.
- **Решающий источник:** man 1 ltrace; исходники ltrace (`sysdeps/linux-gnu/trace.c`); `runtime/lock_futex.go`, `runtime/proc.go` (`stopm`/`notesleep`), `runtime/netpoll_epoll.go`.
- **Приоритет: High.**

### J-H10. DNS: резолвер по умолчанию на darwin/windows, «`experimentalgo`», «параллельный опрос всех nameserver» (ст. 51, строки 128–129, 137, 221, 240) · ФАКТ + API
*Источники: G9, S 51.1, 51.2, 51.4.*
- **Утверждения:** `go` — «дефолт для всех современных сборок на linux, darwin, windows»; режим `experimentalgo`; Go «запускает параллельные DNS-запросы ко всем указанным серверам… первый корректный ответ».
- **[улика судьи]**
  - `net/conf.go:167–190`, `goosPrefersCgo()`: `windows`, `plan9`, `darwin`, `ios`, `android` → системный резолвер;
  - `net/cgo_unix.go:1`: `//go:build !netgo && ((cgo && unix) || darwin)`. На darwin системный резолвер доступен **и без cgo**, через `cgo_unix_syscall.go`. Утверждение Gemini, что чистый Go-резолвер на macOS работает «при `CGO_ENABLED=0`», для текущего Go **устарело**: отключает системный резолвер только тег `netgo`;
  - `net/dnsclient_unix.go:312–313`: вложенный цикл `attempts × servers`, перебор последовательный. Параллельно идут только запросы разных типов (A/AAAA), `dnsclient_unix.go:695`;
  - `net/conf.go:131–160`: при доступном cgo выбор зависит от env (`LOCALDOMAIN`, `RES_OPTIONS`, `HOSTALIASES`) и от `nsswitch.conf`/`resolv.conf`. Утверждение «`CGO_ENABLED=1` → всегда netcgo» (S 51.4) неверно.
- **Решающий источник:** `net/conf.go`, `net/dnsclient_unix.go`, документация пакета `net` («Name Resolution»); Go 1.20 release notes (системный резолвер на macOS без cgo) — подтвердить версию.
- **Приоритет: High.**

### J-H11. Listen backlog: `ListenConfig.Backlog`, `setsockopt(…, 1024, 65535)`, `somaxconn` = 128 (ст. 47, 48, 49) · API + КОД + УСТАР.
*Источники: G2, S 47.1, 48.3, 49.4, 49.5, 4.15.*
- **Утверждения:**
  - 47:198 и 47:232: `net.ListenConfig.Backlog`; «`somaxconn` по умолчанию 128»;
  - 49:163, 49:189: «через `SO_MAX_CONN`»; `unix.SetsockoptInt(int(file.Fd()), unix.SOL_SOCKET, 1024, 65535)`;
  - 48: «передают backlog через ListenConfig»; при переполнении — «`ECONNREFUSED`».
- **[улика судьи]**
  - `net/dial.go:816–855`: поля `Backlog` нет;
  - `net/sock_linux.go:33–36`: `maxListenerBacklog()` читает `/proc/sys/net/core/somaxconn`, и Go вызывает `listen(fd, somaxconn)`;
  - `net/fd_unix.go:170–180`: `TCPListener.File()` делает `pfd.Dup()` и **не** переводит сокет в блокирующий режим. П. 4 G2 («`File()` ломает netpoller, переводя сокет в blocking») для Go 1.27.1 неверен; так было в старых версиях, и момент изменения надо подтвердить по истории `net/fd_unix.go`.
- **Почему проверять (ядро):** опции с номером 1024 на уровне `SOL_SOCKET` нет (`include/uapi/asm-generic/socket.h`). Backlog задаётся только аргументом `listen(2)`. Default `somaxconn` = 4096 с ядра 5.4. RST при переполнении — только при `tcp_abort_on_overflow=1`, иначе ядро дропает ACK/SYN. `somaxconn` — per-netns.
- **Решающий источник:** man 2 listen; `Documentation/networking/ip-sysctl.rst`; `net/ipv4/tcp_input.c`; коммит ядра 5.4 про `SOMAXCONN 4096`.
- **Приоритет: High.**

### J-H12. TCP keepalive в Go (ст. 47, Interview, строка 256; листинг `keepAliveControl`) · УСТАР. + КОД
*Источники: S 47.2, 47.3.*
- **Утверждение:** «`KeepAlive` в `net.ListenConfig` лишь активирует `SO_KEEPALIVE`»; интервалы берутся из sysctl (7200 с), сервер держит мёртвое соединение 2 часа.
- **[улика судьи]** `net/dial.go:18–24`: `defaultTCPKeepAliveIdle = 15 * time.Second`, `defaultTCPKeepAliveInterval = 15 * time.Second`. Есть `KeepAliveConfig` (`dial.go:845`). Листинг не компилируется из-за неиспользуемого `"time"`.
- **Решающий источник:** Go 1.13 release notes (дефолтный keepalive), Go 1.23 release notes (`KeepAliveConfig`), `net/tcpsockopt_unix.go`.
- **Приоритет: High.**

### J-H13. Длительность `TIME_WAIT` (ст. 50 vs ст. 48) · ФАКТ + ПРОТИВ.
*Источники: G12, S 50.1, 48.11, 50.3; J.*
- **Утверждения:**
  - 50:43: «MSL жёстко зафиксировано константой `TCP_TIMEWAIT_LEN` и составляет 60 секунд. Соответственно, интервал 2MSL длится ровно 120 секунд (2 минуты) (в современных ядрах иногда калибруется до 60 с)»;
  - 50:32: «2MSL = 60–120 сек»;
  - 50:149: «без ожидания 120 секунд».
  - При этом ст. 48:308 верно говорит: «в Linux жёстко зашито 60 секунд».
- **Почему проверять:** **[J]** `TCP_TIMEWAIT_LEN` — это сама длительность TIME_WAIT (`include/net/tcp.h`: `#define TCP_TIMEWAIT_LEN (60*HZ)`), а не MSL. Статья ошибочно выводит из неё 120 с. Попутно проверить:
  - `tcp_tw_recycle` удалён в 4.12; «`tcp_tw_recycle()` как функция» (50:82) — неверно;
  - `tcp_death_row` — не «глобальная хеш-таблица»;
  - RFC 793 заменён RFC 9293;
  - появились ли в ядрах 6.x sysctl, меняющие поведение TIME_WAIT (например, `tcp_tw_reuse_delay`), — проверить, чтобы не утверждать «невозможно изменить» абсолютно.
- **Решающий источник:** `include/net/tcp.h`; RFC 9293 §3.6.1; `Documentation/networking/ip-sysctl.rst`.
- **Приоритет: High.**

### J-H14. Direct I/O: `os.O_DIRECT`, «выравнивание» через `make(len+4096)`, проверка выравнивания (ст. 42, 43, 44, 39) · КОД + ПРОТИВ. (C-FIX)
*Источники: G3, G16, S 42.1, 43.1, 43.3, 44.1, 39.4, 39.9.*
- **Утверждения:**
  - 42:173, 42:184: `os.O_DIRECT`. В ст. 43 это исправлено на `syscall.O_DIRECT` прошлым фактчеком, и статьи теперь противоречат друг другу;
  - 43:222–233: `aligned := make([]byte, len(data)+4096); copy(…); f.Write(aligned[:len(data)])`;
  - 44: «проверяйте выравнивание через `os.File.Stat()` и `syscall.Statfs()`»;
  - 39: «используйте `Mmap`… проверяя через `file.Readdir(0)`».
- **Почему проверять:** код не сдвигает начало буфера до границы и не делает длину кратной блоку. Если данные некратной длины, `EINVAL` гарантирован. Ст. 43:263 сама предлагает правильную проверку (`uintptr(unsafe.Pointer(&data[0])) % 4096`), и это противоречит листингу. Требование к выравниванию — logical block size устройства (512/4096) и `dma_alignment`; с Linux 6.0 его можно узнать через `statx(STATX_DIOALIGN)`. `Stat`/`Statfs.Bsize` выравнивания не дают.
- **Нюанс к G3:** «`make` никогда не выравнивает по 4096» — слишком сильно. Большие объекты (>32 КБ) в Go на практике выровнены по странице рантайма (8 КБ), но спецификация этого не гарантирует. Пример может «случайно работать» на больших буферах, и это ещё один довод показать явное выравнивание.
- **Решающий источник:** man 2 open (`O_DIRECT`); man 2 statx (`STATX_DIOALIGN`); `syscall/zerrors_linux_amd64.go`; `runtime/malloc.go` (выравнивание large-объектов).
- **Приоритет: High.**

### J-H15. Привилегии: «EUID==0 → разрешено», `AllThreadsSyscall` вместо `Setuid`, `NoSetuid`, `CAP_CLEAR`, `Capset`-пример (ст. 56, 57, 58) · ФАКТ + API + КОД
*Источники: G10, S 56.1, 56.7, 57.1, 57.3, 57.4, 58.1; конфликт K1.*
- **Утверждения:**
  - 56:51 и 56:182: проверка доступа начинается с `Effective UID == 0` → разрешено;
  - 56:305, 315, 322: «в Go… стандартный пакет `os` намеренно не имеет `Setuid`, поэтому используется `syscall.AllThreadsSyscall(SYS_SETUID…)`»; «`golang.org/x/sys/unix` принудительно рассылает всем потокам»;
  - 57:242: «capabilities не наследуются, если не установлен флаг `NoSetuid`/`NoSetgid`»;
  - 57:216: комментарий про `syscall.CAP_CLEAR`;
  - 58:235–252: `unix.CapHeader`, `Capset(0)` и затем `Capset(NET_BIND_SERVICE)`, «переход на non-root» через `os.Chown(".", 1000, 1000)`.
- **[улика судьи]**
  - `syscall/syscall_linux.go:1243–1251`: `Setuid` без cgo вызывает `AllThreadsSyscall(sys_SETUID, …)`, с cgo — `cgo_libc_setuid`. Значит, `syscall.Setuid` в Go ≥1.16 меняет UID **всех** потоков.
  - `syscall_linux.go:1118–1125`: `AllThreadsSyscall` в бинарниках с cgo **всегда возвращает `ENOTSUP`**. Рекомендация ст. 56 вызывать `AllThreadsSyscall` напрямую не работает при cgo (а cgo включён по умолчанию при сборке с net/os/user и gcc).
  - Код ст. 57 (`Setgroups` → `Setgid` → `Setuid`) компилируется (`go vet` OK) и корректен; `CAP_CLEAR` есть только в комментарии.
  - `unix.CapHeader` — `undefined`.
- **Почему проверять (ядро):** обход DAC даёт `CAP_DAC_OVERRIDE`/`CAP_DAC_READ_SEARCH` (`capable()`), а не `uid==0`; root с `cap_drop: ALL` проверки не обходит. После обнуления permitted поднять capability нельзя (`EPERM`). `os.Chown` меняет владельца каталога, а не UID процесса.
- **Решающий источник:** `syscall/syscall_linux.go`; Go 1.16 release notes («syscall.Setuid… now implemented on Linux»); man 7 capabilities; man 2 capset; `fs/namei.c` (`generic_permission`).
- **Приоритет: High.**

### J-H16. Процессы, пайпы, демоны и systemd: сигнатуры и семантика `os/exec` (ст. 5, 6, 25, 26, 29, 30, 40) · КОД + ФАКТ
*Источники: S 5.1, 6.1, 25.1, 25.2, 26.1, 26.2, 26.4, 26.5, 29.1, 29.2, 29.3, 30.2, 40.1; G15, G17.*
- **Пункты:**
  1. **ст. 5:239, ст. 6:208:** `cmd.Wait` «блокирует горутину (не поток M)»; «фоновый поток рантайма будит горутину». **[улика судьи]** `os/pidfd_linux.go:107–108`: блокирующий `unix.Waitid(P_PIDFD, …)` внутри `ignoringEINTR`. Поток M блокируется, P отдаётся через hand-off.
  2. **ст. 25:** `os.NewFile(int32(42), …)` — сигнатура `NewFile(fd uintptr, name string)` (`os/file.go:133`). «`os.File` буферизован», «`net.Conn` реализует `io.ReaderAt`» — неверно: `*TCPConn` реализует `ReadFrom`/`WriteTo` (`net/tcpsock.go:161,173`).
  3. **ст. 26:26:** `fds, err := syscall.Pipe2(...)` — `Pipe2` возвращает только `error` (`syscall_linux.go:295`).
  4. **ст. 26:128–160 `runWithPipe`:** `cmd.Wait()` вызывается параллельно с `io.Copy` из `StdoutPipe`. Документация `StdoutPipe`: «incorrect to call Wait before all reads from the pipe have completed». Это гонка с потерей вывода. Комментарий «`io.Copy` закрывает пайп автоматически» неверен. Interview той же статьи говорит правильно.
  5. **ст. 26:** «в Go нет аналога popen»; «`cmd.Output` нельзя в production… deadlock». Аналог — `os/exec` + `StdoutPipe`; `Output` не даёт deadlock, риск в неограниченном буфере.
  6. **ст. 29:** `daemonize()` через `syscall.ForkExec("/proc/self/exe", os.Args…)` без guard-переменной и без `Setsid` даёт бесконечный каскад самозапусков. «`os/exec` не умеет `setsid()`» — неверно: `SysProcAttr{Setsid: true}`.
  7. **ст. 30:42:** `net.FileConn(os.NewFile(3, ""))` для listen-сокета — нужен `net.FileListener`. Ст. 30:151 сама упоминает `FileListener`, то есть противоречие с листингом. Нет проверки `LISTEN_PID`.
  8. **ст. 40:264, G17:** `os.FileMode(w.Stat_t.Mode)` — битовые раскладки разные: `io/fs/fs.go:195`, `ModeDir = 1<<31`, а `S_IFDIR = 0o040000`. `IsDir()` вернёт false для каталога, `Type()` неверен.
- **Решающий источник:** документация `os/exec` (`StdoutPipe`, `Wait`, `SysProcAttr`); `syscall/exec_linux.go`; `io/fs/fs.go`; man 3 sd_listen_fds.
- **Приоритет: High.**

### J-H17. Разделяемая память и IPC-код (ст. 32, 31) · КОД + ФАКТ
*Источники: G1, S 32.1, 31.1.*
- **ст. 32:67–75:** `syscall.ShmOpen/ShmSetSize/ShmUnlink` не существуют. `shm_open(3)` — функция libc поверх `/dev/shm`; размер задаётся `ftruncate`.
- **ст. 31:194–195:** `mmap("/dev/zero", MAP_SHARED)` как «shared memory для IPC». Такое отображение видно только потомкам после `fork`, а Go fork без exec не делает, поэтому неродственные процессы его не увидят. Неиспользуемый `os` ломает компиляцию.
- **Решающий источник:** man 7 shm_overview; man 3 shm_open; man 2 memfd_create; man 2 mmap.
- **Корректные варианты для правки:** `os.OpenFile("/dev/shm/…")` + `Truncate` + `unix.Mmap(MAP_SHARED)`; `unix.MemfdCreate` + передача fd.
- **Приоритет: High.**

### J-H18. Память в контейнере и PID 1 (ст. 52, 53, 54) · ФАКТ + ПРОТИВ.
*Источники: G18 п.1, S 52.1, 53.1, 54.1, 54.4.*
- **Утверждения:**
  - 52:153: «рантайм Go определяет объём доступной памяти через `sysinfo` или `/proc/meminfo`… GC запускался поздно»;
  - 53:126–129: «аллокатор Go… через `mmap` и `brk`… `mmap` вернёт `ENOMEM`, которую рантайм Go преобразует в фатальное падение»;
  - 54:158–160: «SIGTERM [для Go в PID 1 без обработчика] будет молча проигнорирован»;
  - 54 Q2: «Go аллоцирует через `mmap()` и `brk()`».
- **Почему проверять:** триггер GC считается от live heap и `GOGC`, память хоста не используется. При упоре в `memory.max` вызов `mmap` успешен, страницы выделяются при page fault, дальше reclaim и cgroup OOM-kill (`SIGKILL` без трейса). `ENOMEM` от `mmap` бывает только при `RLIMIT_AS`, `overcommit=2` или исчерпании `max_map_count`.
- **[улика судьи]**
  - `runtime/signal_unix.go:985–996` (`dieFromSignal`): `setsig(SIG_DFL)`, `raise`, затем при «PID 1 immune to signals» — `exit(128+sig)`. Go в PID 1 без `Notify` завершается сразу с кодом 143, без graceful shutdown. Это не «игнор до SIGKILL». Для C/Python без обработчика тезис статьи верен.
  - `runtime/mem_linux.go:172–176`: `sysMapOS` → `mmap(MAP_FIXED)`, при `ENOMEM` → `throw("runtime: out of memory")`.
  - `brk` в рантайме: только `sbrk0()` в `runtime/malloc.go:677` для подсказки адреса арен на 32-bit; куча на 64-bit Linux через brk не растёт.
- **Решающий источник:** `runtime/mgc.go`, `runtime/mgcpacer.go`, `runtime/signal_unix.go`, `runtime/mem_linux.go`; `Documentation/admin-guide/cgroup-v2.rst` (memory.max, OOM); `kernel/signal.c` (`SIGNAL_UNKILLABLE`).
- **Приоритет: High.**

### J-H19. Frame pointer в Go: ст. 20 против ст. 60 · ФАКТ + ПРОТИВ.
*Источники: S 20.1, 60.1, S:T13.*
- **Утверждения:**
  - ст. 20:72, 165, 170: «в Go по умолчанию… frame pointer отключён, включается `GOEXPERIMENT=framepointer`», «`-fomit-frame-pointer`», «`stkblk`»;
  - ст. 60:247: «исторически perf не мог раскручивать стеки Go… сегментированные стеки»; рекомендации `-buildmode=pie`, `GOEXPERIMENT=strictfipsruntime`, `GODEBUG=…`.
- **[улика судьи]** `internal/buildcfg/exp.go:44–51`: «This used to be an experiment, but now it's always enabled», `FramePointerEnabled = GOARCH == "amd64" || GOARCH == "arm64"`.
- **Решающий источник:** Go 1.7 release notes (FP на amd64), Go 1.12 (arm64); `internal/buildcfg/exp.go`. Сегментированные стеки убраны в Go 1.3.
- **Приоритет: High.**

### J-H20. Core dump в Go и `GOTRACEBACK` (ст. 59) · ФАКТ + API
*Источники: S 59.1, 59.2.*
- **Утверждение:** вся логика статьи построена на том, что при фатальном сбое Go «ядро делает дамп», если `ulimit -c > 0` (59:35–36). `GOTRACEBACK` в статье **не упоминается ни разу** (проверено grep). Предлагается `dlv core … heap`.
- **Почему проверять:** по умолчанию Go при `fatal error` и при неперехваченном сигнале печатает трейс и завершается через `exit(2)`, без core. Core даёт `GOTRACEBACK=crash` или `debug.SetTraceback("crash")`.
- **[улика судьи]** `runtime/extern.go:257–258`: «GOTRACEBACK=crash is like "system" but crashes in an operating system-specific manner instead of exiting… raises SIGABRT».
- **Решающий источник:** `runtime/extern.go`; документация `runtime/debug.SetTraceback`; документация Delve (список команд); `golang.org/x/debug/cmd/viewcore`.
- **Приоритет: High.**

### J-H21. Журналируемые ФС и путь I/O в стеке RAID/LVM (ст. 41, 46) · ФАКТ + КОД
*Источники: S 41.1, 41.2, 46.1, 46.2, 46.3.*
- **Утверждения:**
  - 41:62: «EXT4, XFS, Btrfs поддерживают три режима журналирования» (`data=`); «`data=ordered` по умолчанию в ext4 и XFS»;
  - 41:104: checkpointing — шаг коммита до возврата `fsync`;
  - 46: таблица RAID («RAID5/6/10 чтение ~1×», «RAID0… `tmpfs`»); путь I/O «Page Cache → I/O Scheduler → Device Mapper → RAID» (46:28–29, Итог 3); листинг `GroupCommitter`.
- **Почему проверять:**
  - `data=` — опция только ext3/ext4. XFS журналирует только метаданные. Btrfs — COW без журнала (tree-log для fsync).
  - В jbd2 `fsync` возвращается после надёжного commit-блока (preflush + FUA); checkpoint асинхронный.
  - dm и md — bio-based слои; scheduler висит на request queue нижнего физического устройства.
  - `GroupCommitter` делает `notify` на каждый `Append`, то есть fsync на каждую запись; держит `mu` во время fsync и не ждёт durability.
- **Решающий источник:** `Documentation/filesystems/ext4/` (journal), `fs/jbd2/commit.c`; XFS docs; `Documentation/admin-guide/md.rst`, `device-mapper/`; `block/blk-mq.c`.
- **Приоритет: High.**

### J-H22. Теория примитивов синхронизации (ст. 33, 34) · ФАКТ + КОД
*Источники: S 33.1, 33.2, 34.1, 34.2; G13 (Medium) и S 33.4.*
- **Утверждения:**
  - 33:58: spinlock эффективен в «одноядерных средах (где переключение контекста дороже, чем спин)»;
  - 33:116, 218, 241: `sync/semaphore` (см. J-H5);
  - 34:97 `acquireWithTimeout`: захват мьютекса через горутину + канал + таймаут;
  - 34:287: «если читатели непрерывны, писатели голодают. Go не гарантирует fairness»;
  - 33:75, 101, 240: `FUTEX_WAIT` → `TASK_UNINTERRUPTIBLE`.
- **Почему проверять:**
  - На UP спиннинг бессмыслен: владелец не выполняется. Ядро на UP превращает `spin_lock` в `preempt_disable`.
  - В `acquireWithTimeout` после таймаута фоновая горутина всё равно захватит мьютекс и никогда его не отпустит. `TryLock` есть с Go 1.18.
  - Go `RWMutex` блокирует новых читателей, как только ждёт писатель, поэтому писатели не голодают.
  - `futex_wait` спит в `TASK_INTERRUPTIBLE` (сигнал → `EINTR`/рестарт).
- **Решающий источник:** `include/linux/spinlock_api_up.h`; `sync/rwmutex.go` (документация `RLock`); `sync/mutex.go` (`TryLock`); `kernel/futex/waitwake.c` (`futex_wait_queue`); man 2 futex.
- **Приоритет: High** для 33.1, 33.2, 34.1, 34.2; **Medium (верхняя граница)** для 33.4/G13.

### J-H23. Copy-on-Write (ст. 16) · ФАКТ + КОД
*Источники: S 16.1, 16.2, 16.3, 16.4, 16.9, 16.10.*
- **Утверждения:**
  - 16:60: «флаг CoW для `fork` реализован через бит `PTE_SOFT_DIRTY`»; «для `MAP_SHARED` аналогичный механизм»;
  - 16:88–92: «`SHR` у дочернего процесса в точности равен его `RSS`»;
  - листинг `MADV_DONTFORK` с `syscall.Madvise(unsafe.Pointer, len, flag)`;
  - «используйте `LockOSThread` до форка».
- **Почему проверять:** soft-dirty служит для трекинга записей (CRIU), а не для COW. COW бывает только у `MAP_PRIVATE`. `SHR` = RssFile + RssShmem; анонимные COW-страницы туда не входят. Код не компилируется (`go vet`: too many arguments). В Go-пути `os/exec` используется `CLONE_VM|CLONE_VFORK`, поэтому COW не участвует; ст. 16:109–111 это и говорит, то есть статья противоречит себе.
- **Решающий источник:** `mm/memory.c` (`do_wp_page`, `wp_page_copy`); `Documentation/admin-guide/mm/soft-dirty.rst`; man 5 proc (`statm`, `smaps_rollup`); `syscall/exec_linux.go`.
- **Приоритет: High.**

### J-H24. Возврат памяти, `MemStats`, аллокатор Go (ст. 12, 13, 14, 15, 17, 19) · ФАКТ + КОД
*Источники: S 19.1, 19.2, 19.3, 15.1, 12.1, 13.1, 13.2, 13.3, 17.1, 14.2.*
- **Пункты:**
  1. **19:214:** «sysmon… вызывает `madvise`; ядро отменяет маппинг; `mmap` вернёт тот же адрес». Возвращает память фоновый scavenger (`bgscavenge`), маппинг сохраняется.
  2. **19, Interview п.1–4:** набор ложных обоснований («Go мьютексы для heap не нужны» и т.п.).
  3. **19:** «`HeapAlloc` растёт, `HeapInuse` стабилен → mmap-подпись» — невозможно, так как `HeapInuse ≥ HeapAlloc` по определению.
  4. **15:149:** «Аллокатор Go предотвращает [false sharing], выравнивая спаны и объекты по границам степеней двойки». Size-классы 24, 48, 80… не выровнены по 64 Б, tiny-allocator склеивает объекты.
  5. **12:148, 16:** `syscall.Madvise` с 3 аргументами (`go vet`).
  6. **13:110:** см. J-H5. **13:** неиспользуемый `unsafe` (`go vet`).
  7. **13, Interview Q2:** при major fault «планировщик Go замечает и отсоединяет P». Fault происходит в user-коде (P в `_Prunning`), и `retake` (см. C-HANDOFF) отбирает P только у потока в syscall.
  8. **17:185:** `debug.MemoryLimit()` (J-H5).
  9. **14:145–147 `badPattern`:** «миллион аллокаций в куче». **[улика судьи]** `go build -gcflags=-m`: `make([]byte, 256) does not escape` для `badPattern`. В `goodPattern` `bufPool.Put(buf)` даёт `buf escapes to heap` — это классический SA6002, то есть «хороший» паттерн как раз аллоцирует.
- **Решающий источник:** `runtime/mgcscavenge.go`, `runtime/mstats.go` (документация `MemStats`), `runtime/sizeclasses.go`, `runtime/proc.go` (`retake`), staticcheck SA6002.
- **Приоритет: High.**

### J-H25. Статья 11 (CPU affinity, NUMA): вымышленные флаги и файлы, неверные латентности (ст. 11; ст. 8, 9) · API + ФАКТ + ЧИСЛО
*Источники: S 11.1, 11.2, 11.3, 11.4, 11.5, 8.2, 9.3.*
- **Утверждения:**
  - 11:22, 26: «локальная RAM ~20–30 нс, удалённая ~80–120 нс»; 8:138: «~20 нс»;
  - 11:159–160: `cpuset.sched_load_balance`, `cpuset.mems_hardwall` для cgroups v2;
  - 11:201: `GODEBUG=gcresidency=1`;
  - `MPOL_BIND` → «ядро вернёт `ENOMEM`»;
  - auto NUMA balancing «запускает `migratepages` и KSM»;
  - 9:133: «`sched_gomaxprocs`».
- **Почему проверять:** локальная DRAM ≈ 70–100 нс (20–30 нс — масштаб L3). Перечисленные файлы есть только в cgroup v1 (там и называется `mem_hardwall`). Страницы выделяются при first touch, и при исчерпании узла дальше идут reclaim и OOM. `migratepages` — userspace-утилита. Go не NUMA-aware.
- **Решающий источник:** Intel MLC / Chips and Cheese (латентности); `Documentation/admin-guide/cgroup-v2.rst` (cpuset); `Documentation/admin-guide/mm/numa_memory_policy.rst`; `kernel/sched/fair.c` (`task_numa_fault`).
- **Приоритет: High.**

### J-H26. Приоритеты: RT-задачи и `Setpriority` в Go (ст. 10) · ФАКТ + КОД
*Источники: S 10.1, 10.2.*
- **Утверждения:** 10:86: RT-задачи — «ни один CFS-процесс не получит ни одного такта»; 10:102–106: `syscall.Setpriority(PRIO_PROCESS, 0, priority)` с сообщением «приоритет процесса обновлён».
- **Почему проверять:**
  - По умолчанию действует RT throttling: `sched_rt_runtime_us=950000` из `1000000`. В 6.12 появился fair/deadline server — подтвердить версию.
  - В Linux nice — атрибут потока: `setpriority(PRIO_PROCESS, 0)` меняет только текущий M. Это man 2 setpriority, раздел BUGS/NOTES.
- **Решающий источник:** `Documentation/scheduler/sched-rt-group.rst`; man 2 setpriority; man 7 sched.
- **Приоритет: High.**

### J-H27. Регистры аргументов системного вызова x86-64 (ст. 23, строка 70) · ФАКТ + ПРОТИВ.
*Источник: S 23.2.*
- **Утверждение:** «Аргументы: `R10` (первый), `R8` (второй), `R9` (третий), номер в `RAX`».
- **Почему проверять:** по Linux x86-64 syscall ABI аргументы идут в `RDI, RSI, RDX, R10, R8, R9`. Ст. 2 и 22 дают верный порядок.
- **Решающий источник:** man 2 syscall (таблица регистров); `arch/x86/entry/entry_64.S`.
- **Приоритет: High.**

### J-H28. IOCP: «встроенный пул потоков ядра» (ст. 37, строки 114, 133) · ФАКТ
*Источник: S 37.1.*
- **Почему проверять:** пул рабочих потоков создаёт приложение (или Windows Thread Pool API). Ядро лишь ограничивает concurrency порта и будит ожидающие потоки в LIFO-порядке.
- **Решающий источник:** Microsoft Learn «I/O Completion Ports».
- **Приоритет: High.**

### J-H29. Сводная таблица «Go → ядро» в итоговой статье (ст. 63, строка 157 и соседние) · ФАКТ + ПРОТИВ.
*Источник: S 63.2 (часть — в J-H3).*
- **Утверждения:**
  - «`goroutine` → `clone(CLONE_VM | CLONE_FS | CLONE_FILES)`»;
  - «`runtime.GC` → `madvise`/`mprotect`»;
  - «алгоритм Нейгла»;
  - mutex и каналы — см. J-H3.
- **[улика судьи]** `runtime/os_linux.go:156–161`: `cloneFlags = CLONE_VM|CLONE_FS|CLONE_FILES|CLONE_SIGHAND|CLONE_SYSVSEM|CLONE_THREAD`. `clone` создаёт M, а не горутину. `runtime/mem_linux.go:172–173`: коммит памяти через `mmap(MAP_FIXED)`, не `mprotect`.
- **Приоритет: High.** Итоговая статья закрепляет ошибки всего модуля.

### J-H30. «>50% мощности на системные вызовы» (ст. 2, строка 163) · ЧИСЛО + ФАКТ
*Источник: S 2.1.*
- **Утверждение:** 50 000 RPS × 20 syscalls → «свыше 50% всей мощности» процессора.
- **Почему проверять:** 1 млн syscalls/с × 0,1–0,5 мкс = 0,1–0,5 ядра, то есть единицы процентов многоядерной машины. Цифра — главный аргумент раздела «Цена перехода».
- **Решающий источник:** арифметика плюс измерения стоимости syscall с учётом mitigations (lmbench `lat_syscall`, `perf bench syscall`).
- **Приоритет: High.**

### J-H31. eBPF-листинг (ст. 61) · КОД + ФАКТ
*Источник: S 61.1; связанные S 61.2, 61.3.*
- **Почему проверять:**
  - `//go:embed` без `import "embed"`, `collection.Maps.Lookup(...)` (`Maps` — map) и разорванный литерал — код не компилируется;
  - busy-loop по `Lookup` грузит CPU на 100%;
  - длительность из одного `sys_enter_write` получить нельзя;
  - «карты читаются через mmap без syscall» верно только для `BPF_F_MMAPABLE` array и ringbuf.
- **Решающий источник:** документация `cilium/ebpf` (bpf2go, ringbuf); man 2 bpf.
- **Приоритет: High.**

---

## 3. Конфликты между брифами и решающие улики

| # | Тема | Gemini | Sonnet | Решение судьи / решающая улика |
|---|---|---|---|---|
| K1 | `syscall.Setuid` в многопоточном Go | G10 п.1: меняет UID одного потока, нужен `AllThreadsSyscall` | S 56.7: с Go 1.16 `Setuid` действует на все потоки | **Прав Sonnet.** `syscall/syscall_linux.go:1243–1251` (через `AllThreadsSyscall` или glibc при cgo); `AllThreadsSyscall` при cgo → `ENOTSUP` (1118–1125). Код ст. 57 верен, текст ст. 56 ошибочен. Утверждение Gemini отклонено (§ 8) |
| K2 | Резолвер на macOS | G9: чистый Go на macOS при `netgo` **или** `CGO_ENABLED=0` | S 51.1: на darwin по умолчанию системный резолвер | **Прав Sonnet, у Gemini устаревшая деталь.** `net/cgo_unix.go:1`: build tag включает `darwin` без cgo; отключает только `netgo`. Подтвердить по Go 1.20 release notes |
| K3 | `TCPListener.File()` и блокирующий режим | G2 п.4: `File()` переводит сокет в blocking и ломает netpoller | S 49.8: в 1.27.1 dup без смены режима | **Прав Sonnet для текущего Go.** `net/fd_unix.go:170–180`. Фактчекеру — найти версию, в которой поведение изменилось |
| K4 | Разорванные строковые литералы | G20: Low; статьи 4, 11, 16, 24, 27, 30, 42, 57 | S § 3.2: High; 17 статей | **Список Sonnet точен** (`gofmt -e`, судья): 5, 6, 7, 10, 17, 18, 19, 27, 29, 39, 40, 44, 49, 51, 53, 56, 61. Из списка Gemini подтверждается только 27. **Приоритет High** (кластер) |
| K5 | Ст. 54 и Go 1.25 | G11: ст. 54 в числе устаревших | S 54.3: ст. 54 знает про 1.25, устарел только Итог 3 | **Частично оба.** 54:150 верна; противоречие с 8/52/62 и устаревший Итог 3 остаются |
| K6 | Приоритет `os.O_DIRECT`, `Pipe2`, `FileMode` | G15–G17: Medium | S: High | **High**: код не компилируется (`go vet`) или даёт заведомо неверный результат (`IsDir`) |
| K7 | Приоритет TIME_WAIT | G12: Medium | S 50.1: High | **High**: противоречие 48 ↔ 50 и неверный вывод «2MSL = 120 с» из `TCP_TIMEWAIT_LEN` |
| K8 | Брк и namespaces в ст. 53 | G18: Medium (одним пунктом) | S 53.1: High; S 53.2: Medium | **Разделить:** `brk` + `ENOMEM` + `runtime.Grow` — High (J-H18); «7 типов namespaces» без time ns (5.6) — Medium |
| K9 | Детали stackcache | G7: стеки 2–32 КБ из `mcache.stackcache` | S 21.2: из stackpool/stackLarge/mheap | **Уточнение:** пулы — порядки 2/4/8/16 КБ (`malloc.go:150`, `_NumStackOrders=4`), ≥32 КБ — `stackLarge`/mheap. Суть (нет `mmap`/`madvise` на рост) у обоих верна |
| K10 | «`make` никогда не выравнивает по 4096» | G3 | S 43.1 (только про код) | **Формулировка Gemini слишком сильна:** large-объекты в Go выровнены по 8 КБ странице рантайма, но без гарантии в спецификации. Вывод «код не выравнивает» верен |
| K11 | EEVDF и sysctl | G21: Low; параметры удалены из `/proc/sys/kernel/` и debugfs | S 8.3: Medium; с 5.13 перенесены в debugfs, в 6.6 заменены `base_slice_ns` | **Medium.** Уточнить: в `/proc/sys` их не было уже с 5.13. Решающий источник — коммит EEVDF (6.6) и `kernel/sched/debug.c` |
| K12 | `sendfile` и сокет как источник | G14: ст. 43 утверждает «из сокета в файл» | — | **В тексте такого утверждения нет** (grep по ст. 43; есть только «файл → сокет»). Отклонено (§ 8). Остаток: ст. 31:235 «между файлами/сокетами» (Low) |

---

## 4. Сквозные кластеры (одна проблема в нескольких статьях)

### C-COMPILE. Некомпилируемые листинги
См. J-H6. Приоритет кластера **High**. Чинить механически (литералы) плюс точечно (сигнатуры и импорты). После починки литералов прогнать `go vet` повторно: под ними скрыты ошибки ст. 18, 40, 61.

### C-API. Несуществующие идентификаторы
См. J-H5. Приоритет **High**.

### C-NUM. Числа, которые расходятся между статьями · ЧИСЛО
*Источник: S § 2.*
- **Что сделать:** выбрать в модуле один диапазон для каждой величины, указать CPU, mitigations и методику, и согласовать все статьи.

| Величина | Разброс в модуле | Ориентир для проверки |
|---|---|---|
| Стоимость syscall | 50–100 нс (5), 100–500 нс (2), 200–5000 тактов (22), 1000–5000 (23), 1000–2000 (31) | `perf bench syscall`, lmbench; vDSO отдельно |
| Context switch ОС | 1–2 мкс (7), 2–5 мкс (5), 1–5 мкс при «1000–5000 тактов» (8), 3–15 мкс при «10 000–50 000 тактов» (9), «1000–3000 тактов = 5–10 мкс» (3) | lmbench `lat_ctx`; прямую и косвенную стоимость разделять. **Такты и мкс в одной фразе не сходятся** (3 ГГц) |
| Переключение горутин | 10–20 нс (63, 62 п.1, 35), 10–50 (33), 10–200 (5, 7), 100–200 «= 1000–2000 тактов» (9), 100–300 (62) | бенчмарк `Gosched`/chan ping-pong. Ст. 62 противоречит сама себе |
| TLB miss / page walk | 10–50 нс (12), 50–100+ тактов (13), 50–150 / 150–400 нс / 50–200 тактов (14, внутри одной статьи), 50–150 нс (17); везде «4 обращения к DRAM» | PTE кэшируются в L1–L3 и PWC; DRAM — worst case |
| DRAM | 20 нс (8), 20–30 (11), 50–100 (9, 35) | 70–100 нс локально, 120–200+ нс удалённо |
| L1/L2/L3 «miss» | «L1 miss ~4 такта, L2 ~12–14, L3 ~40+» (9) | это латентности **попадания** (S 9.2) |
| Major page fault | 1–10 мс (12, 13), NVMe 50–100 мкс (17), 1–5 мс (18, рис.) | NVMe ≈ 100 мкс, HDD — мс |
| NVMe | 20 мкс (35), 50–100 мкс (17, 42), «1–2 дня» на шкале (44) | |
| `somaxconn` | 128 (47), «128 раньше, 4096 сейчас» (49) | 4096 с ядра 5.4 |
| TIME_WAIT | 60 с (48), 120 с (50) | см. J-H13 |

Приоритет кластера **Medium**. Исключения уже вынесены в High: DRAM 20 нс в ст. 8 и 11 (J-H25), «>50%» в ст. 2 (J-H30).

### C-TLB. TLB shootdown, KPTI, «context switch» на syscall · ФАКТ (терминология)
*Источники: S:T7, S 2.2, 2.3, 2.4, 3.9, 5.6, 7.2, 8.13, 9.4, 9.5, 9.6, 10.6, 14.4, 14.6, 22.1, 22.2, 22.7, 31.4, 33.5, 43.6, 44.7.*
- **Суть:**
  - «TLB shootdown» везде применён к локальному сбросу TLB. На деле это межпроцессорная инвалидация через IPI при изменении mm (`munmap`, `mprotect`, `madvise`, миграция).
  - KPTI работает только на CPU, уязвимых к Meltdown, а с PCID полного flush нет.
  - Syscall — это mode switch, а не context switch.
  - `SYSCALL` использует MSR `LSTAR`, а не IDT; стек ядра переключает `entry_SYSCALL_64` программно.
  - Предиктор переходов сбрасывается только при определённых mitigations (IBPB).
  - CSR — терминология RISC-V.
- **Решающий источник:** `Documentation/arch/x86/tlb.rst`, `Documentation/arch/x86/pti.rst`, Intel SDM Vol.2 (`SYSCALL`), Vol.3 §4.10; `arch/x86/entry/entry_64.S`; `Documentation/admin-guide/hw-vuln/spectre.rst`.
- **Приоритет:** Medium (верхняя граница) — повторяется в 15+ местах.

### C-BRK. «Go использует `brk`» · ПРОТИВ.
*Источники: G18 п.1, S 1.4, 19.2, 19.20, 53.1, 54.4; S § 3.4.*
- Статьи 12, 13, 15, 19, 21 говорят «не использует», статьи 53, 54 и ст. 1 (таблица) — «`mmap` и `brk`».
- **[улика судьи]** `runtime/malloc.go:677`: `sbrk0()` (`brk(0)`) — только чтение текущего brk для подсказки адресов арен на 32-bit. Роста кучи через brk нет.
- Приоритет: **High** в составе J-H18, иначе Medium.

### C-SCAV. Go heap: резервирование, scavenger, `madvise` · ФАКТ
*Источники: S 12.5, 12.6, 13.7, 13.8, 15.4, 15.5, 15.6, 15.7, 19.8, 19.13, 62.5, 62.10, 63.2.*
- **Суть:**
  - С Go 1.11 куча разреженная: арены по 64 МБ резервируются по мере роста, а не «сотни ГБ при старте».
  - Память возвращает фоновый scavenger с pacing, а не «GC вызывает madvise» и не sysmon.
  - `MADV_DONTNEED` зачищает PTE (это тоже TLB flush/IPI).
  - Коммит памяти — `mmap(MAP_FIXED)`, а не `mprotect` (**[улика судьи]** `mem_linux.go:172–173`).
  - Начиная с mcentral, аллокатор не lock-free.
- **Решающий источник:** `runtime/mgcscavenge.go`, `runtime/mheap.go`, `runtime/malloc.go`, Go 1.11 и 1.16 release notes.
- Приоритет: Medium.

### C-THP. Huge pages и THP в Go · ФАКТ + УСТАР.
*Источники: S 13.1, 13.5, 14.7, 14.8, 15.5, 16.8, 17.11, 18.8, 55.7.*
- **Суть:**
  - Go heap не использует `MAP_HUGETLB`.
  - История Go 1.21.0–1.21.4: `MADV_HUGEPAGE`/`MADV_COLLAPSE` введены и откачены; появился `GODEBUG=disablethp`.
  - hugetlbfs и THP перепутаны: `ENOMEM`/`SIGBUS` против тихого fallback.
  - Для latency-чувствительных сервисов рекомендация `always` спорна.
  - Цифры «15–25%», «в десятки раз» даны без источника.
- **Решающий источник:** Go 1.21.x release notes и issue #63334 (подтвердить номер); `Documentation/admin-guide/mm/transhuge.rst`.
- Приоритет: Medium.

### C-GOBUF. Что сохраняется при переключении горутины · ФАКТ + ПРОТИВ. (C-FIX)
*Источники: S 5.16, 9.7, 9.8, 33.10, 63.4, 20.3, 20.9.*
- 5:151 и 9:94/104: «сохраняются 14 регистров»; 63: «rip, rsp, r12–r15». Ст. 33 верно: «3 регистра (SP, PC, BP)». Прошлый фактчек правил текст ст. 5, но диаграмма осталась.
- **[улика судьи]** `runtime/runtime2.go:303–320`: в Go 1.27.1 `gobuf` = `sp, pc, g, ctxt, lr, bp`; поля `ret` нет (у Sonnet в S 5.16 и 63.4 оно указано — для старых версий).
- **Решающий источник:** `runtime/runtime2.go`; `cmd/compile/abi-internal.md` (в ABIInternal нет callee-saved регистров; R14 = g).
- Приоритет: Medium.

### C-HANDOFF. Блокирующий syscall, sysmon, retake, netpoll в планировщике · ФАКТ
*Источники: S 2.9, 7.4, 7.5, 8.7, 9.10, 9.11, 9.14, 13.3, 22.3, 35.5, 38.3, 38.5, 62.6.*
- **[улика судьи]** `runtime/proc.go` (`retake`, ≈6743–6765):
  - P забирается, если поток в syscall дольше одного тика sysmon (≥20 мкс);
  - и при этом runq не пуст, **или** нет idle P/spinning M, **или** прошло ≥10 мс.
  - Ст. 22:139 («дольше ~10 мс») и ст. 62 («немедленно отвязывает P») неточны.
- Work stealing делает сам M в `findRunnable`, а не sysmon. Netpoll опрашивают `findRunnable` и блокирующий `epoll_wait` простаивающего M; sysmon — только fallback (>10 мс). Простаивающие M спят на futex, а не в `sched_yield`.
- **Решающий источник:** `runtime/proc.go` (`retake`, `findRunnable`, `sysmon`, `stopm`).
- Приоритет: Medium. Исключение — 13.3, это High в J-H24.

### C-NOFILE. Go ≥1.19 сам поднимает soft `RLIMIT_NOFILE` · УСТАР.
*Источники: S 4.14, 5.2, 25.6, 30.7, 50.5, 52.2.*
- Советы «поднимайте лимит вручную, иначе сервис рухнет на 1025-м соединении» устарели.
- **[улика судьи]** `syscall/rlimit.go:30–46`: при старте `Cur = Max − 1` (если `Cur < Max−1`), с последующей корректировкой.
- `net/http` при `EMFILE` делает backoff-retry, а не падает. `fs.file-max` даёт `ENFILE`, а не `EMFILE`.
- **Решающий источник:** Go 1.19 release notes; `net/http/server.go` (`Serve`, temporary error backoff).
- Приоритет: Medium (5.2 — High в составе J-H16 по смыслу).

### C-SOCKDEF. Дефолтные опции сокетов в Go · ФАКТ + ПРОТИВ.
*Источники: S 1.2, 22.6, 48.6, 48.10, 50.10.*
- **[улика судьи]**
  - `net/sockopt_linux.go:28,34`: Go ставит только `SO_REUSEADDR`; `SO_REUSEPORT` по умолчанию не включается. Ст. 48:294 и Итог 3 («включает по умолчанию»), ст. 1:73 противоречат ст. 50.
  - `net/tcpsock.go:290`: `TCP_NODELAY` включён по умолчанию; ст. 22 подаёт его как «оптимизацию».
- Приоритет: Medium.

### C-MMAP-PC. «`mmap` обходит Page Cache» · ФАКТ + ПРОТИВ.
*Источники: S 42.5, 60.5, 18.5, 32.9, 43 (таблица «Zero Copy (`sendfile`/`mmap`)»).*
- Ст. 42 (Итог 5) и ст. 60 противоречат ст. 18 и ст. 43: file-backed `mmap` отображает сам Page Cache. Для чтения есть `pread`, утверждение «альтернатив в POSIX нет» неверно.
- Приоритет: Medium.

### C-HIST. Версии и история Go · УСТАР.
*Источники: S 1.7, 19.17, 20.2, 21.10, 28.2, 29.10, 25.4, 34.9.*
- Непрерывные стеки появились в Go 1.3 (а не 1.4); в 1.4 минимальный стек уменьшен до 2 КБ.
- `NotifyContext` — Go 1.16 (**[улика судьи]** `api/go1.16.txt:409`), а не 1.15/1.20.
- `TryLock` — Go 1.18.
- Стартовый стек адаптивный с Go 1.19.
- `O_CLOEXEC` в os/net появился задолго до 1.11.
- Приоритет: Medium.

### C-OTHERLANG. Сравнения с Java, PHP, Python · УСТАР.
*Источники: S 1.8, 7.3, 7.6, 7.7, 12.13, 16.16, 21.15, 28.7, 33.13, 35.7, 41.9, 42.10.*
- Java 21 virtual threads (не 17); в Java нет async/await; CMS удалён в JDK 14; PEP 475 (Python 3.5); PHP-FPM не делает fork на каждый запрос.
- Приоритет: Low–Medium.

### C-K8S. Kubernetes, Docker, systemd: дефолты · УСТАР. + ФАКТ
*Источники: S 17.4, 28.5, 29.5, 29.6, 30.3, 30.5, 30.6, 52.4, 53.4, 58.2, 58.4, 10.9, 11.14, 51.6.*
- `terminationGracePeriodSeconds` = 30 (а не 10).
- `Type=simple` считается запущенным после fork, а не после exec.
- `LimitNOFILE` — это rlimit, а не cgroup.
- Docker по умолчанию не использует userns.
- ~44 syscalls блокирует seccomp, а не AppArmor.
- `requests.memory` не выставляет `memory.min`/`memory.low`.
- NodeSwap (статус в 1.28–1.34) — проверить.
- Решающий источник: документация K8s, Docker, systemd соответствующих версий.
- Приоритет: Medium.

### C-KNAMES. Устаревшие и выдуманные имена внутри ядра · ФАКТ
*Источники: S 4.11, 12.11, 15.3, 16.14, 18.2, 18.7, 27.6, 27.7, 33.8, 40.3, 48.2, 48.8, 49.1, 49.3, 50.3, 54.2, 59.8.*
- `do_fork` → `kernel_clone`; `pdflush` удалён в 2.6.32; VMA хранятся в maple tree с 6.1; `syn_table`/`listen_sock` удалены в 4.4; `fs/futex.c` → `kernel/futex/` с 5.16; `sendpage` удалён в 6.5.
- Выдуманы: `VM_FILE`, `unix_inode_info`, `f_op->socket`, `struct namespace`, `pid_hash_init` (удалён в 4.15), `irq_init`.
- Приоритет: Low–Medium.

### C-MARKUP. Разметка и рендеринг · РАЗМЕТКА (не факт)
*Источники: S § 3.3; проверено судьёй.*
- **KaTeX:** `\t` в `\text`, `\times`, `\to` превратился в TAB. Ст. 12:44, 13:98, 14:24/189, 15:180–181, 17:129–131, 18:186, 54:112. Механизм тот же, что у разорванных литералов (C-COMPILE).
- **Mermaid:** `:::class` внутри кавычек метки выводится текстом. По шаблону `:::имя"]` найдено ≥21 узел в 14 статьях (3, 4, 15, 44, 45, 46, 49, 51, 53, 55, 56, 57, 58, 63); у Sonnet ≈27 узлов в 18 статьях с учётом других форм.
- **Mermaid ст. 40:10, 40:180:** вложенные кавычки `GoApp["os.Open("/etc/nginx/nginx.conf")"]`. Проверить в рантайме Mermaid 10.9.1: статический аудит такое может не поймать (AGENTS.md § 9).
- **Висячие wikilink'и:**
  - ст. 11 — `[[17. NUMA (Non-Uniform Memory Access) и Hyper-Threading]]`;
  - ст. 12 — `[[13. Страничная организация памяти. Page Tables, TLB, Page Fault.md]]`;
  - ст. 13 — `[[Page Table]]`, `[[Page Table Entry]]`;
  - ст. 48 — `[[5. Учебник по Go (Основы и синтаксис)]].net`.
- **Прочее:** заголовок `## > [!tip] Собеседование` (ст. 40); английская цитата в ст. 32 нарушает AGENTS.md § 11.3.
- Приоритет для фактчека: Low. Для редактора — обязательно; после правки нужна пересборка и `audit_all.py`.

### C-QUOTE. Эпиграфы и атрибуции · МНЕНИЕ / ФАКТ
*Источники: S 3.4, 8.12, 10.8, 25.7, 32.7, 44.2, 47.9, 51.7, 54.5.*
- Цитаты Таненбаума и Торвальдса (ст. 3) поданы как прямые, но не совпадают с архивом comp.os.minix. У Хэмминга реальна только первая половина фразы. «Старинная пословица» про DNS — интернет-мем. Часть эпиграфов («в духе Bell Labs») — вымысел.
- Решение: либо найти первоисточник, либо снять кавычки и атрибуцию.
- Приоритет: Low (Medium для ст. 3, где цитаты — часть исторического сюжета).

---

## 5. Остатки прошлого фактчека `a8006dfc`: проверить только остаток (C-FIX)

Коммит `a8006dfc` (2026-09-24) исправил часть мест, но соседние формулировки остались. Это главный источник внутренних противоречий модуля. В каждой строке: что уже верно, что осталось.

| Ст. | Что исправлено в `a8006dfc` (верно) | Что осталось (проверить) | Связано |
|---|---|---|---|
| 38 | тело: `EPOLLET`, без ONESHOT (38:116) | Итог п.2 (38:190) про `EPOLLONESHOT`/`EV_ONESHOT` | J-H7 |
| 36, 62 | `EPOLLET`, регистрация один раз (62:267) | ст. 36 — диаграмма «после EAGAIN → `epoll_ctl(ADD)`»; ст. 35, 48 | J-H7 |
| 24 | Interview (24:168): ptrace + `int3` на PLT | тело (24:90), Gotcha (24:127) про `LD_PRELOAD`; диагностика futex (24:145) | J-H9 |
| 43 | `syscall.O_DIRECT` | ст. 42 — `os.O_DIRECT` (не компилируется); листинг `writeDirectIO` | J-H14 |
| 23, 9 | § Go (23:79–88): gopark без syscall | 23:45, Interview Q3; ст. 3, 22, 24, 32, 34, 63 | J-H3 |
| 50 | абзац: `tcp_fin_timeout` — только FIN-WAIT-2 | 50:243: «может ограничить разрастание зависших сессий»; TIME_WAIT 120 с | J-H13 |
| 54 | Go 1.25 и `containermaxprocs` (54:150) | Итог 3 ст. 54; ст. 8, 52, 62 | J-H4 |
| 5 | текст про gobuf (SP, PC, BP, g) | диаграмма 5:151 «Сохранение 14 регистров»; ст. 9:94/104; ст. 63 | C-GOBUF |
| 56 | «нет `os.Setuid`» | исправление само ввело ошибку: `syscall.Setuid` уже действует на все потоки; `AllThreadsSyscall` при cgo → `ENOTSUP` | J-H15, K1 |
| 19 | scavenger и `MADV_DONTNEED` (19:120) | таблица 19:212 «`munmap` при sysmon», раздел 19:214 «sysmon и madvise» | J-H24 |
| 22 | hand-off и retake | 22:139 «дольше ~10 мс» — условия retake сложнее | C-HANDOFF |
| 11 | `sched_getaffinity` при старте | ст. 8 — «`NumCPU` = физические ядра хоста» | J-H4 |

---

## 6. Medium по статьям (слитый перечень)

Формат: `ID` — короткая суть. Подробности — в строке Sonnet с тем же номером. Пометка ↓ значит понижено из High судьёй. Пункты, уже вошедшие в High-блоки или кластеры, здесь не повторяются, кроме ссылок.

**Ст. 1. Обзор.**
- 1.1 ↓ — канал = «netpoller + атомики» (см. J-H3).
- 1.2 ↓ — `net/http` + `SO_REUSEPORT` (C-SOCKDEF).
- 1.3 — «монолитный статический ELF»: при cgo бинарник динамический.
- 1.4 — `brk` (C-BRK).
- 1.5 — «за каждым P закреплён M»; «N_CPU = физические ядра» (J-H4).
- 1.6 — EEVDF с 6.6 без указания версии.

**Ст. 2. ОС, ядро, user/kernel space.**
- 2.2 ↓ — KPTI и shootdown (C-TLB).
- 2.3, 2.4 — C-TLB.
- 2.5 — «Go полностью отказывается от glibc»: верно только для Linux без cgo (macOS — libSystem, OpenBSD — libc).
- 2.6 — «glibc привязана к версии ядра»: на деле это версионирование символов glibc.
- 2.7 — «скрытые мьютексы в обёртках read/write».
- 2.8 — `RawSyscall` «err как uintptr(-1)»: `Errno` положительный.
- 2.9 — «все горутины встанут намертво»: блокируется только P+M.
- 2.10 — сигналы как механизм входа в ядро.
- 2.11 — «сегментная архитектура» на x86-64.
- 2.12 — пропуск vDSO.

**Ст. 3. Архитектура ядра.**
- 3.1 ↓ — «Zero-Copy IPC» для `copy_to_user`.
- 3.3 ↓ — `getcpu` «для привязки к процессорам» (3:216). **[улика судьи]** в `runtime/` getcpu встречается только в `os_illumos.go`.
- 3.4 — цитаты Таненбаума и Торвальдса (C-QUOTE).
- 3.5 — «единый контекст прерывания» (hardirq → NAPI/softirq).
- 3.6 — kdump как средство трассировки.
- 3.7 — `tcp_connect()`, «нулевые накладные расходы».
- 3.8 — NT/XNU «гибрид»; DriverKit/UMDF.
- 3.9 — C-TLB.
- 3.10 — 1000–3000 тактов «= 5–10 мкс» (C-NUM).
- 3.11 — «контейнеры возможны исключительно благодаря монолиту» (контрпримеры: jails, zones).

**Ст. 4. Загрузка** (весь блок — Medium, верхняя граница; ↓ из High).
- 4.1 — Long Mode включает не загрузчик (EFI stub / `startup_32`).
- 4.2 — bzImage — Linux x86 Boot Protocol, не Multiboot (4:87).
- 4.3 — `arch/x86/boot/head.S` не существует (4:85, 89).
- 4.4 — «до `sched_init()` нет `task_struct`»: есть статический `init_task`.
- 4.5 — PID 1 через `kernel_thread()` → `kernel_clone()` → `copy_process()` (4:113, 147).
- 4.6 — вектор сброса.
- 4.7 — UEFI 32/64.
- 4.8 — Secure Boot: PK/KEK/db в NVRAM, проверку делает прошивка; shim.
- 4.9 — `kvm=off`, «rsi на стеке».
- 4.10 — SMP startup после `start_kernel`.
- 4.11 — `irq_init`, `pid_hash_init`.
- 4.12 — initramfs монтирует не PID 1.
- 4.13 — Firecracker «5 мс» (4:131): спецификация даёт ≤125 мс; вероятно, перепутано с «<5 MiB» (проверить).
- 4.14 — C-NOFILE.
- 4.15 — `somaxconn` (J-H11).
- 4.16 — lockdown «ломает сборку CGO».
- **Решающий источник для блока:** `Documentation/arch/x86/boot.rst`, `init/main.c`, `init/init_task.c`, `kernel/fork.c`, firecracker `SPECIFICATION.md`.

**Ст. 5. Процессы.**
- 5.1 — см. J-H16.
- 5.2 — C-NOFILE.
- 5.3 — `TASK_ZOMBIE` → `EXIT_ZOMBIE`; `TASK_KILLABLE`.
- 5.4 — «логический процессор M» (в Go это P).
- 5.5 — `pid_max`, `EAGAIN` против `ENOMEM`, `pids.max`.
- 5.6 — C-TLB.
- 5.7 — C-NUM (горутины).
- 5.8 — C-NUM (syscall).
- 5.9 — subreaper: containerd-shim, а не dockerd.
- 5.10 — `RLIMIT_FSIZE` → `SIGXFSZ`.
- 5.11 — C-COMPILE.
- 5.12 — «100 000 потоков исчерпают сотни ГБ RAM»: стек виртуальный.

**Ст. 6. fork/exec/wait.**
- 6.1 — J-H16.
- 6.2 — диаграмма «вернуть PID родителя».
- 6.3 — exec читает program headers, а не секции.
- 6.4 — `SIGCHLD`/`SA_NOCLDWAIT`.
- 6.5 — `forkAndExecInChild` написан на Go (nosplit), а не «на чистом ассемблере».
- 6.6 — исключения `FD_CLOEXEC`.
- 6.7 — `defer cmd.Wait()` как решение.
- 6.8 — `WaitDelay`/`Cancel` (Go 1.20).

**Ст. 7. Потоки.**
- 7.1 — стек потока выделяет user space (glibc), у musl 128 КБ.
- 7.2 — C-TLB.
- 7.3 — Java 21 virtual threads (C-OTHERLANG).
- 7.4, 7.5 — C-HANDOFF.
- 7.6, 7.7 — C-OTHERLANG.

**Ст. 8. Планировщик ОС.**
- 8.1, 8.8 — J-H4.
- 8.3 + G21 — параметры CFS масштабируются по log2(ncpu), с 5.13 в debugfs, в 6.6 заменены `base_slice_ns` (K11).
- 8.4 — EEVDF: дедлайн зависит от slice, а не от «I/O-характера» (8:75).
- 8.5 — регистры в `thread_info`; «JMP/IRET».
- 8.6 — C-NUM.
- 8.7 — C-HANDOFF.
- 8.9 — арифметика CFS throttling; `cpu.max`.
- 8.10 — LockOSThread: «флаг MLOCKED» не существует, пропущен кейс с per-thread состоянием (setns).
- 8.11 — `/proc/PID/sched` показывает только главный поток.

**Ст. 9. Context switch.**
- 9.1 ↓, 9.2 ↓ — C-NUM.
- 9.4, 9.5 (вымышленный псевдокод `switch_to` с `flush_tlb_mm`), 9.6 — C-TLB.
- 9.7, 9.8 — C-GOBUF.
- 9.9 — 100–200 нс ≠ 1000–2000 тактов.
- 9.10, 9.11 — C-HANDOFF.
- 9.12 — NUMA «×3–5».
- 9.13 — `gopark` в CPU-профиле.
- 9.14 — C-HANDOFF.
- 9.15 — «STW сканирует стеки 100 000 горутин»: сканирование конкурентное.

**Ст. 10. Приоритеты.**
- 10.3 — `SCHED_DEADLINE`/`BATCH`/`IDLE`.
- 10.4 — `CAP_SYS_ADMIN` не нужен; `RLIMIT_RTPRIO`.
- 10.5 — «инверсия приоритетов» вместо starvation.
- 10.6 — C-TLB.

**Ст. 11. Affinity и NUMA.**
- 11.6 — права на affinity.
- 11.7 — флага `SCHED_AFFINITY` нет.
- 11.8 — `taskset -p` без `-a` меняет только основной поток (важно для Go).
- 11.9 — «sticky task».
- 11.10 — противоречие со ст. 8.
- 11.11 — политика по умолчанию `MPOL_DEFAULT`.
- 11.12 — NUMA balancing с 3.8; числа «p99 2→150 мс» выдуманы.
- 11.13 — без `+cpuset` в `subtree_control` пример не работает.
- 11.14 — Memory Manager.
- 11.15 — «выигрыш 30–40%» без источника.

**Ст. 12. Виртуальная память.**
- 12.2 — «до 4 ПБ» на процесс (12:10): 57-bit VA = 128 ПиБ, 4 ПиБ — физический предел.
- 12.3 — `PML4 -> PGD -> PUD -> PMD -> PTE`: пять имён на четыре уровня (12:44).
- 12.4 — C-NUM.
- 12.5, 12.6 — C-SCAV.
- 12.7 — `mmap` «без взаимных блокировок»: `mmap_lock`.
- 12.8 — glibc и `malloc_trim`.

**Ст. 13. Страницы и Page Table.**
- 13.4 — ARM64: 4/16/64 КБ.
- 13.5 — C-THP.
- 13.6 — страница рантайма 8 КБ; спаны 8–80 КБ.
- 13.7, 13.8 — C-SCAV.
- 13.9 — C-NUM.
- 13.10 — «Major PF ⇒ swap» неверно (бывает file-backed).

**Ст. 14. TLB.**
- 14.1 ↓ — C-NUM.
- 14.3 — page walker — аппаратный автомат, а не микрокод.
- 14.4 — C-TLB.
- 14.5 — «GC рассеивает данные»: GC в Go не перемещает объекты.
- 14.6 — C-TLB.
- 14.7, 14.8 — C-THP.

**Ст. 15. malloc.**
- 15.2 — «brk для стека / `MAP_GROWSDOWN`».
- 15.3 — C-KNAMES (maple tree).
- 15.4, 15.5, 15.6, 15.7 — C-SCAV / C-THP.

**Ст. 16. COW.**
- 16.5 — «доли микросекунды, нулевой расход»: копирование PTE.
- 16.6 — бита `PTE_RDONLY` на x86 нет.
- 16.7 — reuse при refcount==1.
- 16.8 — C-THP.
- 16.9, 16.10 — J-H23.
- 16.11 — `ForkExec` написан не на ассемблере.
- 16.12 — «терабайты без копирования через pipe/socketpair».
- 16.13 — `posix_spawn` — библиотечная функция, а не syscall.

**Ст. 17. Paging и swap.**
- 17.2 — «Invalid = Hard Page Fault».
- 17.3 — C-NUM.
- 17.4 — NodeSwap в K8s (проверить статус GA), PSI, MGLRU.
- 17.5 — `GOMEMLIMIT` — мягкий лимит, death spiral.

**Ст. 18. mmap.**
- 18.1 — SQLite и RocksDB по умолчанию без mmap; у bbolt нет WAL; CIDR'22 «Are You Sure You Want to Use MMAP».
- 18.2 — C-COMPILE; `pdflush`.
- 18.3 — `file.Munmap` не существует.
- 18.4 — GC не видит указателей внутри mmap-области.
- 18.5 — C-MMAP-PC (`pread`).

**Ст. 19. Сегменты памяти.**
- 19.4 — ASLR в Go: фиксированные hint-адреса арен (`0xc000000000`), non-PIE по умолчанию на linux/amd64.
- 19.5 — строковые литералы в `.rodata`, а не `.data`.
- 19.6 — BSS ленивый.
- 19.7 — mmap-порог решает libc, а не ядро.
- 19.8 — C-SCAV.
- 19.9 — определение `HeapAlloc`; «`runtime.GC()` инициализирует runtime».
- 19.10 — J-H2.
- 19.11 — `make` >64 КБ (`maxImplicitStackVarSize`) всегда в куче.
- 19.12, 19.13 — размеры спанов; «power-of-two».
- 19.14, 19.15 — J-H2.

**Ст. 20. Стек кадра.**
- 20.2 — «Go использует сегментированный стек» (C-HIST).
- 20.3 — C-GOBUF.
- 20.4 — смешение Intel- и Go-синтаксиса в ASM-листинге.
- 20.5 — «каждый SUBQ/ADDQ — запись в L1/L2».
- 20.6 — вывод `-m`: «moved to heap», а не «leaking params».
- 20.7 — J-H2.

**Ст. 21. Переполнение стека.**
- 21.1 ↓ — пропуск: canaries, NX, ASLR/PIE, RELRO, CET, stack clash (раздел заявлен как «защита памяти»).
- 21.8 — guard gap главного потока (`stack_guard_gap`) против guard page pthread.
- 21.9 — Stack Clash (CVE-2017-1000364).
- 21.10 — C-HIST.

**Ст. 22. Системные вызовы.**
- 22.1, 22.2 — C-TLB.
- 22.3 — C-HANDOFF (**[улика судьи]** `retake`).
- 22.4 — cgo-вызов — не syscall (≈десятки нс).
- 22.5 — J-H3.
- 22.6 — C-SOCKDEF.

**Ст. 23. Основные syscalls.**
- 23.3 — netpoll: регистрация один раз; `epoll_wait` вызывает планировщик.
- 23.4 — C-NUM.

**Ст. 24. strace/ltrace.**
- 24.3 — `-f` критично из-за M-потоков.
- 24.4 — `PTRACE_SEIZE`.
- 24.5 — оверхед до 100×; `--seccomp-bpf`.
- 24.6 — «Go статически линкует libc».
- 24.7 — `recvfrom` для TCP.
- 24.8 — `-c` не про «переключение горутин».
- 24.9 — `gdb info goroutines` после «gdb на проде роняет» — противоречие.
- 24.10 — `ptrace_scope`, шум `SIGURG`.

**Ст. 25. FD.**
- 25.2 — J-H16.
- 25.3 — fdtable: массив + bitmap, без RB-деревьев.
- 25.4 — C-HIST.
- 25.5 — у `*os.File` есть финализатор.
- 25.6 — «go sysfs» не существует; C-NOFILE.
- G22 — контраст `dup` против повторного `open` (общий или раздельный `f_pos`): пропуск, Low.

**Ст. 26. Pipe.**
- 26.3 — `dup2` не наследует `FD_CLOEXEC` («всегда используйте `O_CLOEXEC` при дублировании» — неверно для stdio).
- 26.4, 26.5 — J-H16.

**Ст. 27. UDS.**
- 27.3 — на loopback нет ни ARP, ни проверки checksum; цифры «+20–40%» без источника.
- 27.4 — «`SOCK_MAX_ADDR` и libc» выдуманы; Go принимает `@` для абстрактных сокетов.
- 27.5 — область видимости абстрактных сокетов — netns; `SO_PEERCRED`.

**Ст. 28. Сигналы.**
- 28.2 ↓ — `NotifyContext` с 1.16 (C-HIST).
- 28.3 — process-directed доставка выбирает любой поток без маски; blocked ≠ ignored.
- 28.4 — `SIGPIPE` в Go: на fd 1/2 завершает программу, на остальных даёт `EPIPE`. Решающий источник — `os/signal` doc «SIGPIPE».
- 28.5 — grace period 30 с; `sh -c` не форвардит сигналы.
- 28.6 — «канал по умолчанию имеет буфер 1».
- 28.7 — Python PEP 475.
- 28.8 — пропуск: `SIGQUIT`, `SIGURG`, `SIGPROF`.

**Ст. 29. Демоны.**
- 29.4 — `http.NewServer`.
- 29.5 — `Type=simple` против `Type=exec`.
- 29.6 — у `simple` нет старт-таймаута.
- 29.7 — `Type=notify` без `Ready()` → `TimeoutStartSec`.

**Ст. 30. systemd.**
- 30.1 ↓ — Alpine использует OpenRC (30:3).
- 30.3 — reload ≠ SIGTERM.
- 30.4 — socket activation не убирает TCP/TLS handshake.
- 30.5 — `LimitNOFILE` — rlimit; `MemoryHigh` мягкий.
- 30.6 — `ProtectSystem` → mount ns, а не `NEWPID`/`NEWNET`.
- 30.7 — C-NOFILE.
- 30.8 — watchdog-пинг из отдельной горутины переживёт дедлок бизнес-логики.
- 30.9 — `SIGKILL` не создаёт core.

**Ст. 31. IPC.**
- 31.2 ↓ — «ядро отправит IPI для инвалидации кэша»: когерентность обеспечивает железо (31:260).
- 31.3 — pipe в Linux однонаправленный; противоречие в абзаце.
- 31.4 — mode switch против context switch.
- 31.5 — «race на уровне кэш-линий»: проблема в упорядочивании и атомарности.

**Ст. 32. Shared memory.**
- 32.2 — InnoDB и Redis — не cross-process SHM.
- 32.3 — 128 Б (Apple Silicon, adjacent-line prefetch); `cpu.CacheLinePad`.
- 32.4 — J-H3.

**Ст. 33. Mutex/Semaphore/Spinlock.**
- 33.3 — авторы futex (Franke, Kirkwood, Russell).
- 33.4 + G13 — `TASK_INTERRUPTIBLE` (J-H22).
- 33.5 — CSR (C-TLB).
- 33.6 — starvation mode ≠ защита от инверсии; PI-futex.
- 33.7 — профили block/mutex выключены по умолчанию.

**Ст. 34. Deadlock/Livelock/Starvation.**
- 34.3 — J-H3.
- 34.4 — детектор deadlock не зависит от GOMAXPROCS; его «отключают» таймеры, netpoll, `signal.Notify`.
- 34.5 — J-H5.
- 34.6 — паркуется горутина, а не поток.
- 34.7 — «exponential backoff with jitter» без экспоненты.
- 34.8 — «Stack Starvation» — выдуманный термин; async preemption с 1.14.
- 34.9 — «`TryLock` только в тестах или через unsafe» — неверно, с 1.18.
- 34.10 — «детектор отключается `GOMAXPROCS(0)`».

**Ст. 35. Async/blocking IO.**
- 35.1 ↓ — таблица против Interview: Go то «Async Non-blocking» (35:166), то «синхронный неблокирующий» (35:171). Внутреннее противоречие; таксономия частично дело вкуса (МНЕНИЕ), но выбрать одну.
- 35.2 — `setNonblocking` не компилируется; есть `syscall.SetNonblock`.
- 35.3 — у Стивенса пять моделей.
- 35.4 — J-H7.
- 35.5 — C-HANDOFF; LockOSThread здесь не по теме.

**Ст. 36. select/poll/epoll.**
- 36.1 — `FD_SETSIZE` — константа libc.
- 36.2 — poll ≠ обёртка над select.
- 36.3 — callback висит на wait-queue сокета, а не в драйвере NIC.
- 36.4 — J-H7.
- 36.5 — `sync.Pool` в netpoller не используется.

**Ст. 37. kqueue/IOCP.**
- 37.2 — kqueue-fd и epoll-fd структурно эквивалентны.
- 37.3 — файл `kern_event.c`; «авторегистрация `EVFILT_WRITE`» выдумана.
- 37.4 — select/WSAPoll на Windows нативные.
- 37.5 — `EVFILT_TIMER` в Go не используется.
- 37.6 — пропуск: io_uring.

**Ст. 38. Netpoller.**
- 38.2 — «оба подхода edge-triggered»: epoll и kqueue по умолчанию level-triggered.
- 38.3, 38.5 — C-HANDOFF.
- 38.4 — «сотни тысяч соединений в 1 ГБ».

**Ст. 39. После write.**
- 39.1 — `mapping->dirty_pages` не существует; folio.
- 39.2 — для NVMe scheduler по умолчанию `none`.
- 39.3 — delalloc, `auto_da_alloc`.
- 39.4 — `O_DIRECT` ≠ durability.
- 39.5 — нет `fsync` каталога; C-COMPILE.
- 39.6 — DMA на x86 когерентен, `clflush`/`wbinvd` не нужны.
- 39.7 — Go не вызывает `sync_file_range`.
- 39.8 — fsyncgate, паттерн atomic rename.
- 39.9 — J-H14.

**Ст. 40. inode/dentry.**
- 40.2 — C-MARKUP (вложенные кавычки в Mermaid).
- 40.3 — `s_inodes_count` — поле on-disk ext4, а не VFS; `s_op`.
- 40.4 — HTree/B+tree: lookup не линейный.
- 40.5 — RCU-walk.
- 40.10 (Low ↑ проверка) — `openat2` в `os` (проверить `os.Root`, 1.24).

**Ст. 41. Журналирование.**
- 41.3 — barrier удалён в 2.6.37 → `REQ_PREFLUSH`/`REQ_FUA`.
- 41.4 — `fdatasync` при растущем файле всё равно коммитит.
- 41.5 — пропуск: fast_commit.

**Ст. 42. Page Cache.**
- 42.2 — readahead — часть mm, а не I/O scheduler.
- 42.3 — проценты от available memory.
- 42.4 — PostgreSQL, Redis и O_DIRECT (42:168).
- 42.5 — C-MMAP-PC.
- 42.6 — page cache учитывается в cgroup memory (`working_set`).

**Ст. 43. Direct IO и Zero Copy.**
- 43.2 — путь `iomap_dio_rw`, а не `blk_rq_map_user`.
- 43.3 — logical block size, `STATX_DIOALIGN`, `EINVAL` вместо bounce buffer.
- 43.4 — решение принимает `TCPConn.ReadFrom` (43:261 «`fs.go` анализирует типы… на других ОС `WriteFile`» — проверить; sendfile есть и на BSD/Darwin).
- 43.5 — `O_DIRECT` не «продлевает ресурс NAND».

**Ст. 44. Диски.**
- 44.1 — J-H14.

**Ст. 45. Disk scheduler.**
- 45.1 — mq-deadline не даёт чтению «безусловного» приоритета (`writes_starved`).
- 45.2 — для NVMe-БД по умолчанию `none`; `nr_requests`.
- 45.3 — история blk-mq: 3.13 / 3.19 / 4.11 / 5.0.

**Ст. 46. RAID/LVM.**
- 46.4 — full-stripe write, write hole, URE.
- 46.5 — «snapshot split» — выдуманный термин; thin-снимки работают иначе.
- 46.6 — противоречие про BBU.

**Ст. 47. Сетевая подсистема.**
- 47.4 — NAPI ≠ interrupt coalescing.
- 47.5 — LISTEN: SYN → request_sock, а не `receive_queue`.
- 47.6 — DMA «копированием» не является; число «60% CPU» без источника.
- 47.7 — для TCP при заполнении rcvbuf работает flow control, тихие дропы — для UDP.
- 47.8 — пропуск: conntrack, RSS/RPS.

**Ст. 48. Socket API.**
- 48.2 — C-KNAMES.
- 48.3 — J-H11.
- 48.4 — J-H7.
- 48.5 — `pollDesc`.
- 48.6 — C-SOCKDEF.

**Ст. 49. Backlog.**
- 49.1 — C-KNAMES.
- 49.2 — `tcp_max_syn_backlog` с 4.4.
- 49.3 — `listen_lock`.
- 49.5 — `somaxconn` per-netns.
- 49.6 — «пауза GC → переполнение accept queue»: STW < 1 мс.

**Ст. 50. TIME_WAIT/CLOSE_WAIT.**
- 50.2 — RFC 9293.
- 50.3 — C-KNAMES; `tcp_tw_recycle` удалён в 4.12.
- 50.4 — TIME_WAIT уникален по 4-tuple; `MaxIdleConnsPerHost = 2` по умолчанию в `http.Transport`.
- 50.5 — `EMFILE`, а не паника (C-NOFILE).
- 50.6 — `tcp_fin_timeout` (C-FIX).

**Ст. 51. DNS.**
- 51.3 — glibc ≥2.26 перечитывает `resolv.conf`.
- 51.4 — musl: TCP fallback с 1.2.4; «`CGO_ENABLED=1` → всегда cgo» неверно (J-H10).
- 51.5 — cgo-lookup занимает поток (лимит одновременных — проверить значение в `net/net.go`).
- 51.6 — K8s: conntrack race при A/AAAA, `ndots`.

**Ст. 52. ulimit/cgroups.**
- 52.3 — `RLIMIT_RSS` не действует.
- 52.4 — C-K8S.
- 52.5 — пропуск: `memory.events`, PSI.

**Ст. 53. Контейнеры.**
- 53.2 + G18 п.2 — 8 типов namespaces (time ns с 5.6).
- 53.3 — `pivot_root`; порядок шагов runc.
- 53.4 — Docker по умолчанию без userns.
- 53.5 — пропуск: seccomp, capabilities, LSM.

**Ст. 54. Изоляция.**
- 54.2 — `struct namespace`; time ns.
- 54.3 — J-H4.
- 54.4 — C-BRK; `oom.event` не существует.

**Ст. 55. ВМ и гипервизоры.**
- 55.1 — QEMU — процесс в Ring 3 хоста; AMD использует VMCB.
- 55.2 — гостевой affinity не мешает гипервизору мигрировать vCPU.
- 55.3 — пропуск: steal time, kvm-clock (на Xen и без TSC `clock_gettime` идёт без vDSO).

**Ст. 56. Права доступа.**
- 56.2 — «PCI DSS/SOC2/ISO 27001 категорически запрещают root» — МНЕНИЕ; стандарты требуют least privilege.

**Ст. 57. ACL/capabilities.**
- 57.2 — `CAP_DAC_OVERRIDE` ≠ «аналог chmod»; capabilities — атрибут потока.
- 57.3 — `cred_guard_mutex` и `os.Setuid` (57:179) — выдумано.
- 57.5 — пропуск: `setcap`, `ip_unprivileged_port_start`, `AmbientCapabilities=`.

**Ст. 58. SELinux/AppArmor.**
- 58.2 ↓ — «~44 syscalls блокирует docker-default AppArmor»; «чтение `/proc/self/status` и pprof дадут EACCES» (58:265). Это seccomp; чтение разрешено.
- 58.3 — метка читается из xattr один раз при инициализации inode.
- 58.4 — AppArmor ≠ «стандарт в K8s».
- 58.5 — `profile … sha256:abc123` — такого синтаксиса нет.
- 58.6 — LSM-хук `task_kill`.
- 58.7 — пропуск: метки `:z`/`:Z`, Landlock.

**Ст. 59. Core dump.**
- 59.3 — `allgs`; «с Go 1.11 дескрипторы горутин в куче».
- 59.4 — шаблон `core_pattern` systemd; `core_pattern` не namespaced.
- 59.5 — `vm.core_uses_pid` не существует.
- 59.6 — pipe-handler без shell, `>` не сработает.

**Ст. 60. perf/top/vmstat.**
- 60.2 — сеть в Go неблокирующая.
- 60.3 — `vmstat`: колонки `r`, `cs`, `b`.
- 60.4 — `%util` для NVMe.
- 60.5 — C-MMAP-PC.
- 60.6 — J-H3; `perf c2c`.

**Ст. 61. eBPF.**
- 61.2 — uretprobe опасны для Go (перемещение стека).
- 61.3 — mmap только для `MMAPABLE` array и ringbuf.
- 61.4 — `CAP_PERFMON`.
- 61.5 — пропуск: CO-RE/BTF.

**Ст. 62. Go runtime и ОС.**
- 62.2 + G19 — `pthread_create`/`pthread_exit` (62:161, 187, 261) против `clone` (62:63). **[улика судьи]** `os_linux.go:156–161`. Простаивающие M не уничтожаются.
- 62.3 — C-NUM.
- 62.4 — J-H4.
- 62.5 — C-SCAV.
- 62.6 — C-HANDOFF.
- 62.7 — `SIGSTKFLT` «для переполнения стека», `SIGWINCH` «обрабатывает stdlib» (`sigtab_linux_generic.go`).
- 62.8 — пропуск: futex, vDSO, sigaltstack.

**Ст. 63. Итоги.**
- 63.3 — C-NUM.
- 63.4 — C-GOBUF.
- 63.5 — «GOMAXPROCS = число M, исполняющих байткод»; tight loop вытесняется с 1.14.

---

## 7. Low (компактно, по статьям)

Без переоценки. Суть каждой строки — в таблице Sonnet под тем же номером. Пометка «отклонить?» — кандидат на снятие (см. § 8).

| Ст. | Low-строки |
|---|---|
| 1 | 1.7 (стек 2 КБ, адаптивный с 1.19); 1.8 (Java virtual threads) |
| 2 | 2.13 (вытеснение кэша против инвалидации); 2.14 (musl); 2.15 (`SYS_OPEN` нет на arm64); 2.16 (диаграмма без сна); 2.17 (обёрток `EpollPwait2`/`IoUringSetup` в x/sys нет); 2.18 (panic завершает сам рантайм) |
| 3 | 3.12 (oops ≠ panic); 3.13 (seL4 «широко»); 3.14 (C-MARKUP); 3.15 (утечка ≠ порча slab); 3.16 (non sequitur про NUMA); 3.17 (`epoll_create1`, eventfd); 3.18 («идеально под Linux») |
| 4 | 4.17 (0x55AA — отклонить? см. § 8); 4.18 (кириллица в «KЕК»); 4.19 (UEFI-драйверы ≠ приложения); 4.20 (порядок kernel_init/kthreadd); 4.21 (rootfs ramfs/tmpfs); 4.22 (`sync.Once` для мьютексов); 4.23 (`vm.max_map_count`) |
| 5 | 5.13–5.20 (SIGTERM перехватываем; `sighand`; «сотни мкс» cold cache; «14 регистров» → C-GOBUF; счётчик сценариев; `runtime.forkExec` → J-H5; `syscall` против x/sys; ядерный стек 16 КБ) |
| 6 | 6.9 (датировка exec); 6.10 (#PF — исключение); 6.11 (`VMAP_STACK`); 6.12 («segfault при ошибке exec»); 6.13 (числа fork 30 ГБ); 6.14 (vfork/clone3/pidfd) |
| 7 | 7.8–7.13 («в сотни раз»; «90% на ctx switch»; нотация M:N; «физических» в коде; `runnext`; «защищает от Segfault») |
| 8 | 8.12 (Хэмминг, C-QUOTE); 8.13 (C-TLB); 8.14 (sched_ext, PREEMPT_RT); 8.15 (C-NUM); 8.16 (steal time) |
| 9 | 9.16 («до половины мощности») |
| 10 | 10.7 (`nice` на FIFO); 10.8 (атрибуция, «Redis Priority Queues»); 10.9 (QoS Guaranteed); 10.10; 10.11 (`cpu.weight` ≠ точный аналог nice) |
| 11 | 11.16 (висячая ссылка, C-MARKUP); 11.17 (`pthread_setaffinity_np`); 11.18 (`mbind` без `MPOL_MF_MOVE`); 11.19 («Remote TLB Miss»); 11.20 (directory/snoop filter) |
| 12 | 12.9 (dirty-бит и GC); 12.10 (Page Cache в TLB); 12.11 (`exc_page_fault`); 12.12 (C-NUM); 12.13 (CMS); 12.14 (C-MARKUP) |
| 13 | 13.11 (`MHeapMap_SpanInUse`); 13.12 (NUMA и mcache); 13.13 (non sequitur); 13.14 («кратно 4 КБ») |
| 14 | 14.9 (размеры TLB); 14.10 (`sync.Pool` и `[]byte`, SA6002 — подтверждено судьёй, см. J-H24); 14.11 («GC сканирует всю кучу») |
| 15 | 15.8 («95% времени»); 15.9 (free и `M_TRIM_THRESHOLD`); 15.10 (арены glibc); 15.11 (C-MARKUP); 15.12 (смежность); 15.13 (jemalloc обещан, но не раскрыт) |
| 16 | 16.14 (`do_fork`); 16.15 (GC в потомке); 16.16 (ProcessHandle); 16.17 (PHP-FPM refcount) |
| 17 | 17.6 («петабайты»); 17.7 (page cache вытесняется первым); 17.8; 17.9 (`swapon --show`); 17.10; 17.11 (C-THP) |
| 18 | 18.6 (C-NUM); 18.7 (`VM_FILE`); 18.8 (C-THP); 18.9 (`SetPanicOnFault`); 18.10 (`MAP_POPULATE`, fault-around) |
| 19 | 19.16 (`mmap_min_addr`); 19.17 (C-HIST); 19.18 (инвалидация строки); 19.19 (write barriers); 19.20 (Java); 19.21 (диаграмма) |
| 20 | 20.8 («16 байт кэш-линия»); 20.9 (RSP/RBP); 20.10 (`newstack`, а не планировщик) |
| 21 | 21.12 (`PROT_NONE` в PTE); 21.13 (`stackguard1`); 21.14 (`gostartcall`); 21.15 (PHP 8.3); 21.16 (`MemoryMax` и стек) |
| 22 | 22.7 (C-TLB); 22.8 («99% на сброс конвейера»); 22.9 (seccomp и io_uring) |
| 23 | 23.5 (`sys_linux_amd64.go`); 23.6 (clone «аналог fork»); 23.7 (`set_robust_list`); 23.8 (timerfd); 23.9 («за 1 такт»); 23.10 («Эпюл»); 23.11 (sendfile делает сам Go); 23.12 (`strace` без `-f`; epoll_pwait — проверить) |
| 24 | 24.11 (`-T` в секундах); 24.12 (`EADDRNOTAVAIL`) |
| 25 | 25.7 (C-QUOTE); 25.8–25.12 (пропуски; `struct file`; «десятки нс»; размер `struct file`); G22 (`dup` против `open`, `f_pos`) |
| 26 | 26.6 (сокеты ≠ пайпы); 26.7 (`F_SETPIPE_SZ`); 26.8 (FIFO с `O_NONBLOCK`); 26.9 («объединяет filp»); 26.10 (закрыть write-end, `SIGPIPE`) |
| 27 | 27.6 (`unix_inode_info`); 27.7 (`sendpage` удалён в 6.5); 27.8 (`os.Remove` против `SetUnlinkOnClose`); 27.9; 27.10 (таблица pipes/SHM); 27.11 (`SOCK_SEQPACKET`, `SO_PEERCRED`) |
| 28 | 28.9 («Thread Control Block»); 28.10 (sigaltstack); 28.11 (номера сигналов по архитектурам); 28.12 (`WaitGroup` по значению); 28.13 (PHP CLI) |
| 29 | 29.8 (двойной fork, `umask(0)`); 29.9 («только одна горутина слушает»); 29.10 (C-HIST) |
| 30 | 30.10 (`unset_environment`); 30.11 (PHP-FPM socket activation — ⚠ проверить); 30.12 (`STOPPING=1`); 30.13 (`MemoryHigh` и `GOMEMLIMIT`); 30.14 (`CPUQuota` и 1.25) |
| 31 | 31.6 (siginfo); 31.7 (C-NUM); 31.8 (checksum на loopback); 31.9 (пропуски POSIX IPC); K12-остаток (31:235 «между файлами/сокетами» про sendfile) |
| 32 | 32.5 (COW-формулировка); 32.6 (MESI); 32.7 (цитата на английском — C-MARKUP); 32.8 (helgrind для Go); 32.9 (C-MMAP-PC) |
| 33 | 33.8 (`fs/futex.c`, `wait_queue_head_t`); 33.9 (`sem_wait` против `semop`); 33.10 (C-NUM / C-GOBUF); 33.11 (условия спина); 33.12 («spurious wakeup»); 33.13 («в 10–100 раз») |
| 34 | 34.11 (`_Gdead`); 34.12 (MESI, «тераватты»); 34.13 (нотация, стек `std::thread`); 34.14 (пропуски) |
| 35 | 35.6 (NVMe 20 мкс, C-NUM); 35.7 (Java 17 против 21); 35.8 (псевдокод); 35.9 (C-NUM) |
| 36 | 36.6 (история poll); 36.7 (`epoll_filefd`); 36.8 («экспоненциальный выигрыш»); 36.9 (epoll и обычные файлы, `EPERM`) |
| 37 | 37.7 (имена файлов, J-H5); 37.8 (масштабирование); 37.9 (pinning буферов) |
| 38 | 38.6 (хеш-таблица в epoll); 38.7 (`type netpoller`); 38.8 (`netpollLock`); 38.9 (Tokio); 38.10 (deadlines) |
| 39 | 39.10 (`dirty_*_ratio`) |
| 40 | 40.6 (`EBADF`, `fs.ReadStat`); 40.7 (`EXT4_N_BLOCKS`); 40.8 (ctime); 40.9 (negative dentry); 40.11 (C-MARKUP) |
| 41 | 41.6 (числа fsync); 41.7, 41.8 (что журналируется в ordered); 41.9 (Redis SAVE) |
| 42 | 42.7 (xarray/folio); 42.8 (C-NUM); 42.9 (fsync и write-back); 42.10 (PHP streams) |
| 43 | 43.6 (C-TLB); 43.7 (tmpfs и `O_DIRECT` до 6.6); 43.8 («порог 2 ГБ»); 43.9 (`copy_file_range`, `MSG_ZEROCOPY`) |
| 44 | 44.2 (C-QUOTE); 44.3 (C-MARKUP); 44.4–44.6 (шкала времени, Gen5, erase); 44.7 (C-TLB) |
| 45 | 45.4 (scheduler и износ NAND); 45.5 (Merge & Sort у `none`); 45.6 (io_uring и Go); 45.7 (верно — противоречит ст. 41) |
| 46 | 46.7 (megacli, «RAID ≠ backup»); 46.8 (O_DIRECT для логов) |
| 47 | 47.9 (эпиграф, «80%»); 47.10 (C-MARKUP); 47.11 (`net_rx_action`, budget); 47.12 (`recvmsg`); 47.13 («страницы подкачки»); 47.14 (`SO_RCVBUF` ×2; `SetReadBuffer` отключает autotuning); 47.15 (checksum); 47.16 (`runtime.park`, pollcache) |
| 48 | 48.7 (C-MARKUP); 48.8 (`f_op->socket`); 48.9 (таймеры в `accept`); 48.10 (верно, C-SOCKDEF); 48.11 (верно, J-H13) |
| 49 | 49.7 (ограничения SYN cookies); 49.8 (`File()`, K3); 49.9 («use of closed network connection»); 49.10 (`perf trace`); 49.11 (`nstat`) |
| 50 | 50.7 (CLOSE_WAIT бывает временным); 50.8 (`listen_lock`); 50.9 (`ip_local_port_range` пересекается с портами сервисов); 50.10 (`SO_REUSEADDR`) |
| 51 | 51.7 (C-QUOTE); 51.8 («утечки в net/http»); 51.9 (порядок nsswitch); 51.10 (`resolv.conf` ≠ UDS); 51.11 (`netdns=go+1`, EDNS0) |
| 52 | 52.6 (rlim в `signal_struct`); 52.7 (cgroup v2 «с 5.8+» против «5.3+» в ст. 53); 52.8 (page cache в memcg v1); 52.9 («netpoller требует потоков») |
| 53 | 53.6 («0 оверхеда»); 53.7 (версия cgroup v2); 53.8 (`EAGAIN` при throttling); 53.9 (на хосте пример молчит; C-COMPILE) |
| 54 | 54.5 (C-QUOTE); 54.6 (`sched_tick`, `__alloc_pages`); 54.7 (`ENOSPC`); 54.8 (C-MARKUP) |
| 55 | 55.4 («95% контейнеров в ВМ»); 55.5 (IDT, C-TLB); 55.6 (стоимость VM-exit); 55.7 (C-THP) |
| 56 | 56.3 (sticky: ещё и владелец каталога); 56.4 («`openat` — десятки нс»); 56.5 (`info` до `Chmod`); 56.6 (`ModeSticky` = 1<<20 — подтверждено `io/fs/fs.go:195–206`); 56.8 (`/etc/shadow`); 56.9 (`ip_unprivileged_port_start`) |
| 57 | 57.6 (кэширование ACL в inode); 57.7 (порядок DAC → capable → LSM); 57.8 («setuid даёт UID=0»; `capabilities/cap`) |
| 58 | 58.8 («5–10 нс на хук»); 58.9 (`/var/log/myapp w,` — файл, а не каталог); 58.10 (permissive и аудит) |
| 59 | 59.7 («80% информации»); 59.8 (maple tree); 59.9; 59.10 (GDB против Delve); 59.11 (`core_pipe_limit`) |
| 60 | 60.7 (`top -o %us`, getrusage); 60.8 («gcwait» в gctrace нет); 60.9 (`perf_event_paranoid`) |
| 61 | 61.6 (eBPF уже не аббревиатура; «10–15% CPU»); 61.7 (тексты ошибок verifier, bounded loops) |
| 62 | 62.9 (`gopark` написан на Go, не на asm); 62.10 (RSS и page cache); 62.11 (pollCache); 62.12 (привязка к L1/L2); 62.13 (текст OOM); 62.14 («виртуальная машина») |
| 63 | 63.6 (`schedtick` в p); 63.7 (`sync.Pool` и page cache; «WaitGroup гарантирует утечку»; connect блокирующий); 63.8 (`GOMEMLIMIT` не гарантия) |

---

## 8. Отклонено или понижено как ложное срабатывание

| # | Находка | Почему отклонено | Улика |
|---|---|---|---|
| R1 | **G10 п.1:** «`syscall.Setuid` меняет UID только текущего потока M» | Для Go ≥1.16 на Linux неверно, с cgo и без | `syscall/syscall_linux.go:1243–1251`. Код ст. 57 корректен (`go vet` OK) |
| R2 | **G10, оценка кода ст. 57 как High** | В коде нет `CAP_CLEAR`, только комментарий; код верен | `sources/…/57…md:200–218`. Остаток — вводящий в заблуждение комментарий (Medium, S 57.4) |
| R3 | **G14:** «ст. 43 утверждает, что `sendfile` читает из сокета в файл» | Такого утверждения в ст. 43 нет; везде «файл → сокет» | grep `sendfile` по ст. 43: строки 97–135, 257–272. Остаток — ст. 31:235 (Low) |
| R4 | **G2 п.4:** «`TCPListener.File()` переводит сокет в blocking» | Для Go 1.27.1 неверно (устаревшее поведение) | `net/fd_unix.go:170–180` |
| R5 | **G9, деталь:** «чистый Go-резолвер на macOS при `CGO_ENABLED=0`» | На darwin системный резолвер работает и без cgo; отключает только `netgo` | `net/cgo_unix.go:1` (build tag), `net/conf.go:131–139` |
| R6 | **G20, список статей** 4, 11, 16, 24, 30, 42, 57 | Разорванных литералов в этих статьях нет (кроме 27, которая есть и у Sonnet) | `gofmt -e` и подсчёт нечётных кавычек по всем 76 блокам |
| R7 | **G7, деталь:** «stackcache 2–32 КБ» | Пулы — порядки 2/4/8/16 КБ; ≥32 КБ — stackLarge/mheap | `runtime/malloc.go:136,150` |
| R8 | **G3, формулировка:** «`make` никогда не выравнивает по 4096» | Слишком сильно: large-объекты на практике выровнены по 8 КБ (без гарантии). Вывод про код верен | `runtime/malloc.go` (large alloc) — подтвердить |
| R9 | **S 4.17:** «сигнатура MBR 0x55AA некорректна» | Общепринятая запись последовательности байтов `55 AA` на смещении 510; формально слово `0xAA55`. Это УПРОЩ., не ошибка | — (по желанию оставить Low) |
| R10 | **S 49.8:** «побочные эффекты `File()` на старых версиях — проверить» | Для текущего Go не дефект; оставить как историческую оговорку, если статья обсуждает версии | `net/fd_unix.go:170–180` |
| R11 | **S T4 (счёт листингов):** «2 листинга требуют сторонних модулей» | Таких листингов 3: ст. 29, 30 и 61; ст. 30 использует `go-systemd/v22/daemon` | прогон `go vet` судьёй |

Отдельно о **Sonnet в целом.** Все его утверждения о Go-рантайме и stdlib, которые я выборочно перепроверил, подтвердились по исходникам 1.27.1. Это `retake`, `maxstacksize`, `FramePointerEnabled`, `dieFromSignal`, `ListenConfig`, `maxListenerBacklog`, keepalive 15 с, `SO_REUSEADDR`, `TCP_NODELAY`, `NotifyContext` 1.16, `rlimit`, `sysMapOS`, `cloneFlags`, `goosPrefersCgo`, `dnsclient` (последовательный перебор), `x/sync/semaphore`, `Setuid`, `pidfdWait`. Его пометки «— (не перепроверено)» по ядру и инструментам — честные гипотезы: проверять по указанным источникам.

---

## 9. Важные пропуски (кандидаты на добавление, не ошибки)

Не исправлять как ошибки. Решение о добавлении — за редактором, по Zero Knowledge Loss Policy только расширение.

1. **vDSO** (`clock_gettime` без входа в ядро) — ст. 2, 22, 23, 62; и оговорка ст. 55 про kvm-clock/Xen.
2. **`GOTRACEBACK=crash`** как способ получить core от Go — ст. 59 (это High, J-H20); `SIGQUIT` для дампа горутин — ст. 28.
3. **Go 1.25 container-aware GOMAXPROCS** и нюанс с `go` в `go.mod` — ст. 1, 8, 52, 62 (High, J-H4).
4. **Защиты памяти:** canaries, NX/W^X, ASLR/PIE, RELRO, CET, stack clash — ст. 21 (S 21.1, 21.9).
5. **fsync каталога и atomic rename**, fsyncgate — ст. 39, 41.
6. **`statx(STATX_DIOALIGN)`** — ст. 43, 44.
7. **Time namespace** (5.6) — ст. 53, 54.
8. **`dup` против повторного `open`** (общий или раздельный `f_pos`) — ст. 25 (G22).
9. **`SO_PEERCRED`, `SOCK_SEQPACKET`** (`unixpacket` в Go) — ст. 27.
10. **`exec.Cmd.WaitDelay`/`Cancel`** (Go 1.20) — ст. 6.
11. **`http.Transport.MaxIdleConnsPerHost` = 2** как частая причина TIME_WAIT-шторма — ст. 50.
12. **steal time (`%st`)** — ст. 8, 55.
13. **`nstat` ListenOverflows/ListenDrops**, dmesg «Possible SYN flooding» — ст. 49.
14. **io_uring и seccomp-ограничения** в контейнерах — ст. 22, 37, 45.

---

## 10. Рекомендации фактчекеру

1. **Сначала механика, потом факты.** Разорванные литералы (17 статей) и KaTeX-TAB (7 статей) — это один артефакт экранирования, внесённый при редакторском переписывании. Восстанавливайте по `git log -p` (например, для ст. 5 — по `2d3bd27d` и `68d52870`), а не правкой «на глаз». Потом повторите `go vet` на всех полных листингах: под литералами скрыты ошибки ст. 18, 40, 61.
2. **Сначала противоречия C-FIX (§ 5).** В каждом из 12 мест верная формулировка уже есть в модуле. Задача — довести её до всех соседних абзацев, Interview и Итогов.
3. **Go-утверждения проверять по исходникам той версии, которую называет текст.** Улики в брифе даны для 1.27.1. Если статья говорит «в Go 1.21+», нужна проверка по release notes именно этой версии (`gcresidency`, `pagealloc`, Go 1.21.x и THP, Go 1.20 и darwin-резолвер).
4. **Числа (C-NUM) — одно решение на модуль.** Выбрать диапазоны с указанием CPU и методики и привести к ним все статьи, а не править каждую цифру по отдельности.
5. **Не принимать решения по совпадению брифов.** Пример: G10 и исправление в ст. 56, сделанное прошлым фактчеком, совпадают в ошибке про `Setuid`, но исходник показывает обратное.
6. **Mermaid после правок.** Вложенные кавычки в ст. 40 и `:::class` в метках проверить в реальном рантайме Mermaid 10.9.1 (AGENTS.md § 9). Статический `audit_all.py` их может не поймать.
7. **Границы задачи.** Этот бриф — план исследования. Исправления в `sources/` вносит следующий шаг конвейера; `dist/` руками не трогать (AGENTS.md § 8).
