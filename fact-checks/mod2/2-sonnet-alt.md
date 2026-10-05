# Модуль 2 «Устройство и работа ОС» — независимая фактчек-проверка (sonnet-alt)

> Роль: второй независимый исследователь. Модуль разобран с нуля, все 63 статьи прочитаны целиком; чужой бриф не использовался и не открывался.
> Дата прогона: 2026-10-02. Объём: `sources/2. Устройство и работа ОС/` (63 файла).

## 0. Метод, границы и как читать документ

* **Как искал.** Каждая статья прочитана полностью; для каждого утверждения проверялось: (а) соответствует ли оно ядру Linux / железу / рантайму Go; (б) зависит ли от версии или архитектуры; (в) не противоречит ли другим статьям модуля; (г) компилируется ли пример и делает ли он то, что про него написано.
* **Что проверено «железно».** Все утверждения про Go (рантайм, `net`, `os`, `syscall`, `x/sys/unix`) выборочно сверены с исходниками локального Go **1.27.1** (`/usr/local/go/src`) и `golang.org/x/sys v0.46.0`. Такие строки помечены **✔ src**. Там, где результат проверки подтвердил или опроверг конкретное утверждение, это указано в самой строке.
* **Что НЕ проверено по первоисточнику.** Утверждения про ядро Linux, железо и сторонние инструменты (K8s, systemd, Docker, AppArmor/SELinux и т.д.) сделаны по знаниям, интернет-поиск не использовался. В колонке «Статус» такие строки идут как **— (не перепроверено)**; если я сам не уверен — **⚠ проверить**. Колонка «Что проверить» — это либо точная ссылка (файл/символ/man), либо **тип источника**, который закрывает вопрос (Documentation ядра, man-страница, SDM, release notes и т.п.).
* **Приоритеты.** **High** — фактическая ошибка, которая вводит читателя в заблуждение в основной тезис статьи/собеседовании, несуществующий API, не компилирующийся или неверный по смыслу код, прямое противоречие другим статьям. **Medium** — неточность, устаревание, зависимость от версии/архитектуры, неверная причинно-следственная связь, существенный пропуск. **Low** — мелкая неточность, спорная формулировка, цифра без источника. Стилистические замечания в фактчек не включены (кроме случаев, когда они ломают разметку диаграммы/формулы).
* **Нумерация.** `№ = номер статьи.порядковый номер`. Внутри статьи строки отсортированы High → Medium → Low.
* **Масштаб.** Всего кандидатов в разделе 4: **738** (High — 107, Medium — 341, Low — 290); сквозные темы вынесены в разделы 1–3 и в основную таблицу не дублируются. Большая часть проблем сосредоточена в статьях 2–5, 8–14, 16–22, 33–34, 41–43, 46–52, 54, 58–63 (самые «технические» и самые цифро-насыщенные).

## 1. Резюме для редактора (что чинить в первую очередь)

**Системная картина.** Модуль написан уверенно и хорошо структурирован, но в нём повторяется один и тот же набор дефектов: (1) цифры «на глаз» без источника и **расходящиеся между статьями**; (2) термины ядра/CPU используются не по назначению (TLB shootdown, «контекстное переключение» на syscall, «Zero-Copy IPC»); (3) о Go-рантайме написаны **правдоподобные, но выдуманные** детали (идентификаторы, GODEBUG-флаги, API); (4) примеры кода часто **не компилируются**; (5) ряд советов **устарел** (Go 1.19/1.25 изменили поведение рантайма); (6) статьи местами **противоречат друг другу** по базовым вещам (futex в `sync.Mutex`, frame pointer, GOMAXPROCS, регистрация fd в epoll).

**High-приоритеты, сгруппированные по темам (детали — в разделе 4):**

| # | Тема | Где | Суть | Проверка |
|---|---|---|---|---|
| T1 | `sync.Mutex`/каналы «построены на futex» | 3, 22(табл.), 23(§2, Interview), 24, 32, 34, 63 (при том что 23(§Go) и 33 пишут верно) | Slow path `sync.Mutex` — `runtime_SemacquireMutex` → `gopark` без syscall; `futex` вызывает рантайм на уровне M (note/runtime.mutex). Каналы — `hchan.lock` + `gopark`, без futex/epoll. Диагностика «futex WAIT = мьютекс» в ст.24 вводит в заблуждение | `sync/mutex.go`, `runtime/sema.go`, `runtime/lock_futex.go`, `runtime/chan.go` |
| T2 | `GOMAXPROCS`, cgroup, `automaxprocs` | 1, 8, 52, 62 vs 54 | С **Go 1.25** рантайм сам учитывает CPU-лимит cgroup и динамически обновляет `GOMAXPROCS` (**✔ src**: `runtime/cgroup_linux.go`, GODEBUG `containermaxprocs`/`updatemaxprocs` Changed:25). Совет «всегда подключайте automaxprocs / Go не видит cgroup» устарел; ст.54 это знает, остальные нет | Go 1.25 release notes |
| T3 | Выдуманные API/идентификаторы | см. раздел 3.1 | `GODEBUG=gcresidency`, `pagealloc`, `experimentalgo`, `asyncpreempt=1`; `ListenConfig.Backlog`; `SO_MAX_CONN`; `debug.MemoryLimit()`; `syscall.ShmOpen`; `os.O_DIRECT`; `sync/semaphore` в stdlib; `NoSetuid/NoSetgid`; `sched_gomaxprocs`; `stkblk`; `/debug/pprof/stack`; `dlv … heap`; `github.com/capabilities/cap`; `unix.CapHeader`; `syscall.CAP_CLEAR` (в x/sys/unix — только AIX) | **✔ src** (по тексту исходников Go 1.27.1 и x/sys 0.46) |
| T4 | Примеры не компилируются / не делают заявленного | см. раздел 3.2 | из 45 прогнанных через `go vet` листингов компилируются 17; 26 не компилируются (15 — разорванные литералы, остальные — неверные сигнатуры, несуществующие идентификаторы, неиспользуемые импорты); 2 (ст. 29, 61) требуют сторонних модулей (в ст. 61 `gofmt` всё равно находит разорванный литерал); у компилирующихся остаются логические проблемы | `go vet`/`go build` каждого листинга |
| T5 | Pure-Go резолвер «опрашивает nameserver параллельно» | 51 | Нет: перебор **последовательный** `attempts × servers` (**✔ src** `net/dnsclient_unix.go`); `netgo` не «по умолчанию» на darwin/windows (**✔ src** `net/conf.go:goosPrefersCgo`); режима `experimentalgo` не существует | `net/dnsclient_unix.go`, `net/conf.go` |
| T6 | Арифметика/числа | 2, 8, 9, 11, 12–14, 35 | «>50% всей мощности на syscalls» (на самом деле единицы % машины); «L1/L2/L3 miss 4/12/40 тактов» (это hit-латентности); локальная DRAM «20 нс»; page walk «4 обращения к DRAM» | Intel SDM/Optimization Manual, измерения |
| T7 | TLB/KPTI/Context switch | 2, 3, 5, 7, 8, 9, 14, 22 | «TLB Shootdown» применён к локальному сбросу; «KPTI при каждом входе в ядро» (только на Meltdown-уязвимых CPU, с PCID без полного flush); syscall ≠ context switch | `Documentation/x86/pti.rst`, Intel SDM |
| T8 | Загрузка/ядро | 4 | `arch/x86/boot/head.S` не существует; образ ядра — не Multiboot; «до `sched_init()` нет `task_struct`» (есть статический `init_task`); PID 1 создаётся тем же `kernel_clone`; «Firecracker 5 мс»; «Long Mode включает загрузчик» | `Documentation/arch/x86/boot.rst`, `init/main.c` |
| T9 | I/O-путь и durability | 39, 41–43, 45, 46 | `data=ordered` приписан XFS/Btrfs; checkpoint в пути `fsync`; scheduler «выше» LVM/RAID; `os.O_DIRECT`; невыровненный `O_DIRECT`-пример; нет fsync каталога | `Documentation/filesystems/ext4`, `jbd2`, `Documentation/block/` |
| T10 | Сеть/TCP | 47–50 | `Backlog` в ListenConfig; `KeepAlive` в Go ≥1.13 задаёт TCP_KEEPIDLE/INTVL (**✔ src**: default 15 с, есть `KeepAliveConfig`); `TIME_WAIT` = 60 с, а не 120 (ст.50 противоречит ст.48); `tcp_fin_timeout` противоречиво описан | `net/dial.go`, `include/net/tcp.h` (`TCP_TIMEWAIT_LEN`) |
| T11 | Контейнеры/безопасность | 52–58 | cgroup-OOM ≠ `ENOMEM` от `mmap`; Docker по умолчанию без userns; «44 syscalls» — это seccomp, а не AppArmor; для non-root нужны `AmbientCaps` (**✔ src**: `SysProcAttr.AmbientCaps`); root обходит DAC через `CAP_DAC_OVERRIDE`, а не «uid==0» | `man 7 capabilities`, Docker docs |
| T12 | Go runtime детали | 12, 19, 21, 35–38, 48, 62, 63 | `pthread_create` (на деле `clone` — **✔ src** `os_linux.go`), `mprotect` (на деле `mmap(MAP_FIXED)` — **✔ src** `mem_linux.go:sysMapOS`), «sysmon/GC вызывает `madvise`», «рост стека → `mmap`+`madvise`», регистрация fd «после EAGAIN», `close()` порождает epoll-событие, `PID 1` в Go «игнорирует SIGTERM» (**✔ src** `dieFromSignal` → `exit(128+sig)`) | `runtime/*.go` |
| T13 | Frame pointer | 20 vs 60 | Ст.20: «Go по умолчанию без FP, `GOEXPERIMENT=framepointer`». Факт: FP включён на amd64/arm64 (**✔ src** `internal/buildcfg/exp.go:FramePointerEnabled`) | Go 1.7 release notes |

## 2. Сводная таблица сквозных расхождений числовых оценок

| Величина | Что написано (статья: значение) | Замечание |
|---|---|---|
| Стоимость системного вызова | 2: 100–500 нс; 5: 50–100 нс; 22: 200–5000 тактов; 23: 1000–5000 тактов; 31: 1000–2000 тактов | Разброс в 10–100×, нет привязки к CPU/mitigations; не учтён vDSO (`clock_gettime` вообще без входа в ядро) |
| Context switch ОС (процессы/потоки) | 1: 1000–2000 тактов; 3: 1000–3000 тактов и «5–10 мкс»; 5: 2–5 мкс; 7: 1–2 мкс (потоки); 8: 1000–5000 тактов «=1–5 мкс»; 9: 10 000–50 000 тактов «=3–15 мкс» | Тактов и мкс в одной формулировке не сходятся (1000–3000 тактов ≈ 0.3–1 мкс на 3 ГГц); прямая и косвенная стоимость смешаны |
| Переключение горутин | 5: 10–200 / 100–200 / 10–20 нс; 7: 10–200 нс; 8: «десятки нс»; 9: 100–200 нс «=1000–2000 тактов»; 33: 10–50 нс; 38: 10–15 нс; 62: 10–20 **и** 100–300 нс (в одной статье); 63: 10–20 нс | 100–200 нс ≈ 300–600 тактов, не 1000–2000; единого диапазона нет |
| TLB-miss / page walk | 12: 10–50 нс; 13: 50–100+ тактов; 14: 50–150 нс (рис.), 150–400 нс (текст), 50–200 тактов (код); 17: 50–150 нс | Везде «4 обращения к DRAM», хотя PTE кэшируются в L1–L3 и PWC |
| Латентность DRAM | 8: «локальная ~20 нс, чужая 70–120»; 11: «20–30 / 80–120»; 9: «50–100 нс»; 35: «50–100 нс» | Локальная DRAM ≈ 70–100 нс, удалённая ≈ 120–200+ нс; 20 нс — масштаб L3 |
| Major page fault | 12/13: 1–10 мс; 17: NVMe 50–100 мкс; 18: 1–5 мс (рис.) vs 50–100 мкс (текст) | Для NVMe-swap ≈100 мкс; 1–10 мс — HDD |
| TIME_WAIT | 48: 60 с; 50: «2MSL = 120 с / 60–120 с» | Linux: `TCP_TIMEWAIT_LEN = 60 с` |
| `somaxconn` по умолчанию | 47: 128; 49: «128 раньше, 4096 сейчас» | С ядра 5.4 — 4096 |

## 3. Сквозные проблемы по всему модулю

### 3.1. Несуществующие или неверные идентификаторы и API (**✔ src** — сверено с Go 1.27.1 / x/sys 0.46.0)

| Ст. | Что написано | Факт |
|---|---|---|
| 2 | `x/sys/unix` «включает io_uring, epoll_pwait2» | Есть только `SYS_*`-константы (`SYS_IO_URING_SETUP`, `SYS_EPOLL_PWAIT2`) и типы; готовых обёрток `EpollPwait2/IoUringSetup` нет (есть `PidfdOpen`) |
| 2 | `unix.SYS_OPEN` в примере | Нет на arm64 (только `openat`) |
| 9 | «внутренние механизмы `sched_gomaxprocs`» | Такого идентификатора в рантайме нет |
| 11 | `GODEBUG=gcresidency=1` (Go 1.21+) | Не существует (нет ни в `runtime1.go:dbgvars`, ни в `godebugs`) |
| 12, 16 | `syscall.Madvise(ptr, size, flag)` | Сигнатура `Madvise(b []byte, advice int)` — 3 аргумента не компилируются |
| 13 | `GODEBUG=pagealloc=1`; `MHeapMap_SpanInUse` | Нет такого флага; идентификатор из Go ≤1.2 |
| 17 | `debug.MemoryLimit()` | Нет; есть только `SetMemoryLimit(int64) int64` (`SetMemoryLimit(-1)` возвращает текущее) |
| 20 | `stkblk`, «`-fomit-frame-pointer` по умолчанию» | `stkblk` нет; FP включён по умолчанию на amd64/arm64 |
| 21 | `gostacksplit`; `mmap`+`madvise` при росте стека; «лимит стека = `ulimit -v`»; `/debug/pprof/stack`; `//go:nosplit` как защита от рекурсии | Нет `gostacksplit`; лимит — `maxstacksize` (1e9 на 64-bit, 250e6 на 32-bit — `runtime/proc.go`), настраивается `debug.SetMaxStack`; стек берётся из stackpool/mheap без отдельного `mmap`/`madvise` на каждый рост; эндпоинта `/debug/pprof/stack` нет (есть `cmdline, profile, symbol, trace` + профили по имени) |
| 25 | `os.NewFile(int32, string)` | Сигнатура `NewFile(fd uintptr, name string)` |
| 26 | `fds, err := syscall.Pipe2([]int{0,1}, …)` | `Pipe2(p []int, flags int) error` — возвращает только `error` |
| 28, 29 | `signal.NotifyContext` «Go 1.15+/1.20+» | Добавлен в **Go 1.16** (`api/go1.16.txt`) |
| 28 | `os/signal` блокирует сигналы и ждёт в `sigwaitinfo` | В рантайме и `os/signal` `sigwaitinfo` не используется; обработчики `rt_sigaction` на всех потоках → `sigsend` → `signal_recv` |
| 29 | «`os/exec` не умеет `setsid`»; `sdnotify` в `go-systemd/v22` | `syscall.SysProcAttr` имеет `Setsid, Setpgid, Setctty, Noctty, Credential, AmbientCaps`; пакет в go-systemd — `daemon`, не `sdnotify` |
| 32 | `syscall.ShmOpen/ShmSetSize/ShmUnlink` | В `syscall` таких функций нет |
| 33 | `sync/semaphore` «с Go 1.21» | В stdlib нет; есть `golang.org/x/sync/semaphore` (на `container/list`+`sync.Mutex`, не на `semaRoot`) |
| 34 | `GODEBUG=asyncpreempt=1` | Существует только `asyncpreemptoff` |
| 37 | `netpollkqueue.go`, `netpollwindows.go`, `netpollLink` | Файлы `netpoll_kqueue.go`, `netpoll_windows.go`; `netpollLink` нет |
| 36, 38, 48 | `runtime.wakeG`, `netpollLock`, `netpollwake`, `runtime.park` | В рантайме нет (есть `netpollready/netpollunblock/injectglist`, `gopark`) |
| 42, 43 | `os.O_DIRECT` (ст.42) | В `os` нет; `syscall.O_DIRECT`/`unix.O_DIRECT` (ст.43 говорит верно) |
| 47–49 | `net.ListenConfig{Backlog:…}`, `SO_MAX_CONN` | В `ListenConfig` нет `Backlog` (только `Control`, `KeepAlive`, `KeepAliveConfig`, mptcp); `listen()` вызывается с `somaxconn` (`net/sock_linux.go: maxListenerBacklog`) |
| 51 | режим `GODEBUG=netdns=experimentalgo` | Нет; значения — `go`, `cgo`, `1`/`2` (и комбинации `go+1`) |
| 52, 54, 62 | «Go определяет память/CPU хоста; без automaxprocs…» | Устарело с Go 1.25 (см. T2) |
| 57 | `SysProcAttr.NoSetuid/NoSetgid` | Нет; для наследования capabilities — `SysProcAttr.AmbientCaps` |
| 57 | `syscall.CAP_CLEAR`; `github.com/capabilities/cap` | Не существуют |
| 58 | `unix.CapHeader/CapData` | `unix.CapUserHeader/CapUserData`; `Capset(hdr *CapUserHeader, data *CapUserData)` |
| 59 | `dlv core … heap` | У Delve нет команды `heap` |
| 61 | `//go:embed` без `import "embed"`; `collection.Maps.Lookup("…").Lookup(&m)` | Не компилируется (`Maps` — `map[string]*ebpf.Map`) |
| 62 | `pthread_create`, «лишние потоки уничтожаются `pthread_exit`» | Потоки создаёт `clone` (**✔ src** `os_linux.go: cloneFlags`); простаивающие M не уничтожаются |
| 62 | `mprotect` для «коммита» | `sysMapOS` вызывает `mmap(MAP_FIXED, PROT_READ\|PROT_WRITE)` (**✔ src** `mem_linux.go`) |
| 62 | SIGSTKFLT/SIGUSR1/2 «для стека горутины»; SIGWINCH «обрабатывается stdlib» | SIGSTKFLT в `sigtab` — `_SigThrow`; SIGUSR1 — `_SigNotify`; SIGWINCH — `_SigNotify+_SigIgn` (**✔ src** `sigtab_linux_generic.go`) |
| 63 | «`goroutine` = `clone(CLONE_VM\|FS\|FILES)`» | `clone` создаёт M; флаги: `CLONE_VM\|FS\|FILES\|SIGHAND\|SYSVSEM\|THREAD` |

### 3.2. Примеры кода: не компилируются или не делают заявленного

_Метод: все полные листинги (`package main`) извлечены из статей и прогнаны через `go vet` на Go 1.27.1 с `golang.org/x/sys v0.46.0`; листинги ст. 29 и 61 не проверены (требуют `go-systemd`/`cilium/ebpf`). Компилируются без ошибок, но с логическими проблемами: ст. 2, 5 (1-й), 14, 16 (1-й), 20, 27 (2-й), 28, 31 (1-й), 42 (1-й и 3-й), 43, 46, 50, 54, 55, 57._

| Ст. | Проблема |
|---|---|
| 2 | `unix.Syscall(SYS_OPEN…)` (нет на arm64); комментарий «возвращает error» при `Errno` |
| 5, 6, 7, 10, 17, 18, 19, 27, 29, 39, 40, 44, 49, 51, 53, 56, 61 | Литерал `"…\n"` разорван реальным переводом строки внутри кавычек — **не менее 34 мест в 17 статьях** (✔ подтверждено `gofmt -e`/`go vet` на сырых блоках из `.md`); код не компилируется (скорее всего артефакт конвертации) |
| 12, 16 | `syscall.Madvise` с 3 аргументами (✔ `go vet`: `too many arguments`; сигнатура `Madvise(b []byte, advice int)`) |
| 13 | неиспользуемый `import "unsafe"` (✔ `go vet`) |
| 14 | `badPattern`: `make([]byte,256)` не уходит в кучу (non-escaping) — пример не демонстрирует тезис |
| 17 | `debug.MemoryLimit()` |
| 18 | не импортирован `unsafe`, импортирован неиспользуемый `bytes`; `file.Munmap` |
| 21 | `//go:nosplit`-«защита от рекурсии»; `defer free(buf)`; `make([]byte,100<<20)` «в стеке» |
| 25 | `os.NewFile(int32,…)` |
| 26 | `Pipe2` возвращает `error`; **`runWithPipe`: `cmd.Wait()` вызывается параллельно с чтением из `StdoutPipe`** — по документации так делать нельзя (потеря вывода) |
| 27 | отправка FD: `unix.Mmsghdr/Sendmmsg` вместо `unix.Sendmsg(..., unix.UnixRights(fd), …)` |
| 29 | `daemonize()`: самозапуск без guard → бесконечный каскад; `http.NewServer()` не существует; нет `Setsid` |
| 30 | `net.FileConn` вместо `net.FileListener` для listen-сокета; нет проверки `LISTEN_PID` |
| 31 | `/dev/zero`+`MAP_SHARED` как «shared memory для IPC» — видимо только потомкам fork; неиспользуемый `import "os"` во втором листинге (✔ `go vet`) |
| 32 | `syscall.ShmOpen…` не существует (✔ `go vet`: `undefined`) |
| 34 | `acquireWithTimeout`: после таймаута фоновая горутина всё равно захватит мьютекс и никогда не отпустит; `TryLock` есть с Go 1.18 |
| 35 | `setNonblocking` возвращает 2 значения как `error` |
| 40 | `os.FileMode(stat.Mode)` — разные битовые раскладки (`IsDir/Type` неверны); вложенные кавычки в Mermaid |
| 42 | `os.O_DIRECT` не определён (✔ `go vet`; есть `syscall.O_DIRECT`/`unix.O_DIRECT`) |
| 43 | `writeDirectIO`: не выравнивает адрес и длину |
| 46 | `GroupCommitter`: `notify` на каждый `Append` → fsync на каждую запись; `mu` держится на время fsync; нет ожидания durability |
| 26, 41 | неиспользуемый `import "log"` (✔ `go vet`) |
| 47 | неиспользуемый `import "time"` (✔ `go vet`) |
| 48 | неиспользуемый `import "fmt"` (✔ `go vet`) |
| 49 | «настройка backlog» ничего не настраивает (`SO_REUSEPORT` + бессмысленный `setsockopt`) |
| 58 | `unix.CapHeader` (✔ `go vet`: `undefined`; есть `unix.CapUserHeader`); повторный `Capset` после обнуления; `os.Chown(".")` вместо смены UID |
| 61 | `//go:embed` без `embed`; `Maps.Lookup`; busy-loop по `Map.Lookup`; `Duration` из `sys_enter_write` |
| 10 | `Setpriority(PRIO_PROCESS,0)` меняет nice только вызывающего потока (`M`), а в сообщении «Приоритет процесса обновлён» |

### 3.3. Разметка и ссылки

* **Формулы KaTeX/LaTeX испорчены**: `\to`, `\times`, `\text{…}` превратились в TAB + `o/imes/ext` — строки с `$…$` в статьях **12, 13, 14, 15, 17, 18, 54** (⚠ при повторной конвертации).
* **Mermaid**: в метках узлов написано `["Текст:::класс"]` (класс внутри кавычек) — классы не применяются, `:::имя` выводится текстом: статьи 3, 4, 15, 44–51, 53, 55–58, 60, 63 (≈ 27 узлов в 18 статьях). В статье 40 вложенные кавычки в метке `GoApp["os.Open("/etc/…")"]` — синтаксическая ошибка Mermaid.
* **Висячие wikilink'и**: `[[17. NUMA (Non-Uniform Memory Access) и Hyper-Threading]]` (ст.11; в модуле 1 это «31. NUMA…» и «32. Hyper Threading и SMT»), `[[13. Страничная организация памяти. Page Tables, TLB, Page Fault]]` (ст.12; реально «13. Страницы памяти и Page Table»), `[[Page Table]]`, `[[Page Table Entry]]` (ст.13), `[[5. Учебник по Go (Основы и синтаксис)]].net` (ст.48).
* Заголовок `## > [!tip] Собеседование` (ст.40) — сломанная разметка callout внутри заголовка.

### 3.4. Прямые противоречия между статьями

| Тема | Статьи | Суть |
|---|---|---|
| futex в `sync.Mutex` | 3, 22, 24, 32, 34, 63 vs 23(§Go), 33 | см. T1 |
| Frame pointer в Go | 20 vs 60 | 20: «отключён, нужен `GOEXPERIMENT=framepointer`»; 60: «включён по умолчанию». Верно 60 (**✔ src**) |
| `GOMAXPROCS` и cgroup | 54 vs 8, 52, 62 | 54 знает про Go 1.25, остальные — нет |
| `brk` в Go | 12, 13, 15, 19, 21 («Go не использует brk») vs 53, 54 («mmap и brk») | Go не использует `brk` (на Linux) |
| Регистрация fd в epoll | 38, 49, 62 («при создании fd, один раз») vs 35, 36, 48 («после `EAGAIN`») | Верно «при создании» (`netpollopen`) |
| `SO_REUSEPORT` по умолчанию | 48 («включает по умолчанию») vs 50 («через `Control`»), 1 (таблица) | Go по умолчанию ставит только `SO_REUSEADDR` (**✔ src** `net/sockopt_linux.go`) |
| `TCP_NODELAY` | 22 (как «оптимизация») vs 48 | Go включает его по умолчанию (**✔ src** `net/tcpsock.go: setNoDelay(fd,true)`) |
| `mmap` и Page Cache | 42(Итог 5), 60 («mmap обходит Page Cache») vs 18, 43 | `mmap` отображает сам Page Cache |
| `O_DIRECT` константа | 42 (`os.O_DIRECT`) vs 43 (`syscall.O_DIRECT`) | см. 3.1 |
| `tcp_fin_timeout` | 50 (внутри) | Сначала «только FIN-WAIT-2», потом «ограничит CLOSE_WAIT» |
| Стартовый soft `RLIMIT_NOFILE` | 5, 25, 30, 52 (советуют вручную поднимать/«1024») | Go ≥1.19 сам поднимает soft до `hard-1` при старте (**✔ src** `syscall/rlimit.go`) |
| NUMA-осведомлённость Go | 9 («`sched_gomaxprocs`») vs 11, 62 | Go не NUMA-aware |
| Позиция I/O scheduler | 45 vs 46 | Scheduler висит на очереди нижнего физического устройства, после dm/md (46 рисует его выше LVM/RAID) |
| TIME_WAIT | 48 vs 50 | 60 с vs 120 с |

### 3.5. Что в модуле в целом верно (чтобы не потерять при правках)

Транспортные факты, которые я проверил и считаю корректными: схема `RAID 5/6` write-penalty (4/6 I/O); `ndots:5` в K8s; `GOMEMLIMIT` с Go 1.19; `MADV_DONTNEED` по умолчанию с Go 1.16; `tcp_syncookies` и очереди SYN/accept (в части семантики `ss -lnt`: Send-Q/Recv-Q); `SO_LINGER=0` → RST; TCP_NODELAY по умолчанию; `SCM_RIGHTS`; 24 обращения при EPT-walk; async-preemption через `SIGURG` (Go 1.14); `GOMAXPROCS` ≠ число M; PID-1-семантика сигналов внутри pid-namespace; `ctime`/`mtime` различие; `fsync` vs `fdatasync` семантика (за вычетом перечисленного ниже).

---

## 4. Детальный перечень кандидатов по статьям

Столбцы: **№**; **Приоритет**; **Раздел**; **Утверждение (как в тексте)**; **Проблема / что проверить**; **Источник**; **Статус**.
Если в «Источнике» указан только тип — это тип первоисточника, который закрывает вопрос.

### Статья 1. Обзор раздела. Как устроена современная ОС и зачем это Go-разработчику

| № | Приор. | Раздел | Утверждение | Проблема / что проверить | Источник | Статус |
|---|:---:|---|---|---|---|---|
| 1.1 | High | Таблица Mechanical Sympathy, строка channel | «hchan + netpoller (epoll/kqueue) + атомики» | каналы НЕ используют netpoller; hchan защищён runtime.mutex (lock, на Linux futex только при contention); «системные примитивы синхронизации» вводят в заблуждение | runtime/chan.go, lock_futex.go | — (не перепроверено) |
| 1.2 | High | строка net/http | «netpoller поверх epoll + флаг SO_REUSEPORT» | net/http не включает SO_REUSEPORT; в net.ListenConfig нужно явно через Control; смешивает механизмы | net/http, net/sockopt | ✔ src |
| 1.3 | Medium | Общий вывод / Обзор | «Скомпилированная программа на Go — монолитный статический ELF» | не всегда: при cgo (net, os/user по умолчанию при CGO_ENABLED=1 и наличии gcc) бинарник динамически линкуется с libc; на macOS/Windows иначе | go doc cmd/cgo, net package doc "Name Resolution" | — (не перепроверено) |
| 1.4 | Medium | строка gc | «взаимодействие с brk и mmap» | Go runtime на Linux не использует brk для кучи (только mmap/munmap/madvise) | runtime/mem_linux.go | ✔ src |
| 1.5 | Medium | Interview GOMAXPROCS | «за каждым P закрепляется системный поток M»; «N_CPU — число физических ядер» | M↔P не закреплены (M может быть в syscall без P; M > P); дефолт = число логических CPU (SMT), Go 1.25+ учитывает cgroup CPU limit; Go 1.25 container-aware GOMAXPROCS — важный пропуск для темы контейнеров | Go 1.25 release notes; runtime/proc.go | — (не перепроверено) |
| 1.6 | Medium | Roadmap | CFS и EEVDF | EEVDF заменил CFS в Linux 6.6 (ноя 2023) - нужно уточнение версии | LWN, kernel 6.6 | — (не перепроверено) |
| 1.7 | Low | таблица goroutine | «стек от 2 КБ», «ctx switch 1000–2000 тактов» | с Go 1.19 стартовый размер стека адаптивный (по средней); цифра такта без источника | Go 1.19 notes | — (не перепроверено) |
| 1.8 | Low | Сравнение с Java | стек 1МБ, нет упоминания virtual threads (Java 21) | устарело/неполно | JEP 444 (virtual threads), JDK/Python/PHP release notes | — (не перепроверено) |

### Статья 2. Что такое операционная система. Ядро, user space и kernel space

| № | Приор. | Раздел | Утверждение | Проблема / что проверить | Источник | Статус |
|---|:---:|---|---|---|---|---|
| 2.1 | High | «Цена перехода» | «50000 RPS × 20 syscalls → >50% всей мощности процессора» | арифметика: 1M syscalls/s × 0.1–0.5 мкс = 0.1–0.5 ядра, т.е. единицы % от многоядерной машины | расчёт | — (не перепроверено) |
| 2.2 | High | «Цена перехода» п.3 | «TLB Shootdown ... KPTI перезагружает CR3 при каждом входе в ядро» | shootdown = межпроцессорная инвалидация TLB по IPI, не то; KPTI включается только на уязвимых к Meltdown CPU (не на AMD, не на новых Intel), с PCID не полный сброс TLB; Spectre ≠ KPTI | Documentation/x86/pti.rst | — (не перепроверено) |
| 2.3 | Medium | п.1 «Смена контекста» | процессор атомарно сохраняет регистры и переключает стек | SYSCALL сохраняет только RIP→RCX, RFLAGS→R11; стек ядра переключает программно entry_SYSCALL_64 (swapgs); syscall ≠ context switch | Intel SDM SYSCALL; arch/x86/entry/entry_64.S | — (не перепроверено) |
| 2.4 | Medium | Q2 | сброс предсказателя переходов при входе в ядро | только при некоторых mitigations (IBRS/IBPB), не всегда | исходники и Documentation/ ядра, man-страницы (man 2/7) | — (не перепроверено) |
| 2.5 | Medium | «Почему Go избегает glibc» | «по умолчанию Go полностью отказывается от glibc» | верно только для Linux без cgo; macOS (libSystem, с 1.12), OpenBSD (libc, с 1.16), Windows (DLL), Solaris идут через библиотеки; net/os/user по умолчанию с cgo | glibc symbol versioning docs; man 7 libc | — (не перепроверено) |
| 2.6 | Medium | п.1 | «glibc жёстко привязана к версии ядра на хосте» | проблема GLIBC_2.34 not found — версионирование символов glibc (нужен glibc ≥ версии сборки), не ядра | glibc symbol versioning docs; man 7 libc | — (не перепроверено) |
| 2.7 | Medium | п.2 | обёртки glibc: проверки локали, скрытые мьютексы | read()/write() обёртки так не работают; преувеличение; реальные причины: cgo-вызов дорогой, стек, vDSO | glibc symbol versioning docs; man 7 libc | — (не перепроверено) |
| 2.8 | Medium | Gotcha RawSyscall | «err как uintptr(-1)»; «вернёт (r1,r2,err uintptr)» | в syscall/x/sys err — syscall.Errno = положительный errno; ядро возвр. -errno, обёртка конвертирует | syscall/syscall_linux.go; x/sys/unix; man 2 syscalls | — (не перепроверено) |
| 2.9 | Medium | Gotcha RawSyscall | «все горутины в очереди встанут намертво» | другие P могут украсть горутины из local runq; блокируется только P + M | syscall/syscall_linux.go; x/sys/unix; man 2 syscalls | — (не перепроверено) |
| 2.10 | Medium | «три механизма» | сигналы — механизм перехода границы | сигналы — доставка ядра→процесс, не вход в ядро; механизмы: syscall, прерывания, исключения (traps/faults); SIGUSR1 шлёт не ядро | man 7 signal; os/signal doc; runtime/signal_unix.go | — (не перепроверено) |
| 2.11 | Medium | Under the hood | go run main.go: ядро загружает код в Text... Heap через mmap | go run компилирует и запускает tmp-бинарник; «сегментная архитектура» — x86-64 flat, не сегменты | man 2 mmap; mm/mmap.c; Documentation/mm/; man 5 elf; Documentation/arch/x86/x86_64/mm.rst | — (не перепроверено) |
| 2.12 | Medium | Gotcha / omission | vDSO | time.Now / clock_gettime в Go идёт через vDSO без входа в ядро — важный пропуск в статье про цену syscall | man 7 vdso; runtime/vdso_linux.go | — (не перепроверено) |
| 2.13 | Low | п.4 | «инвалидация кэшей L1/L2» | это вытеснение (pollution), не инвалидация | Intel SDM / AMD APM, Optimization Manual | — (не перепроверено) |
| 2.14 | Low | п.3 | «Linux (musl, uclibc)» | Go не зависит от libc, musl важен только для cgo | net/dnsclient_unix.go, net/conf.go; man 5 resolv.conf; musl release notes | — (не перепроверено) |
| 2.15 | Low | Код | SYS_OPEN | нет на arm64; лучше unix.Open; комментарий «возвращает error» а err Errno | syscall/syscall_linux.go; x/sys/unix; man 2 syscalls | ✔ src |
| 2.16 | Low | sequence diagram | syscall → DMA → IRQ → sysret | показывает синхронный сценарий; сон/планирование при блокирующем I/O не отражено; vDSO не упомянут | Intel SDM (SYSCALL/SYSRET); arch/x86/entry/entry_64.S | — (не перепроверено) |
| 2.17 | Low | Q5 | x/sys/unix включает io_uring, epoll_pwait2, pidfd | проверить фактическое наличие обёрток | runtime/netpoll.go, netpoll_epoll.go; man 7 epoll | ✔ src |
| 2.18 | Low | User space | «panic... ОС изолирует и завершает процесс» | Go panic завершает процесс сам рантайм через exit(2), не ОС | runtime/panic.go; runtime/extern.go (GOTRACEBACK) | — (не перепроверено) |

### Статья 3. Архитектура ядра. Monolithic, Microkernel, Hybrid

| № | Приор. | Раздел | Утверждение | Проблема / что проверить | Источник | Статус |
|---|:---:|---|---|---|---|---|
| 3.1 | High | «Zero-Copy IPC» в Linux | syscalls копируют copy_to_user за один проход = «Zero-Copy IPC» | это копирование (1 копия), не zero-copy; терминологическая ошибка, конфликтует с лекцией 43 | man 2 sendfile/splice; net/tcpsock_posix.go (ReadFrom) | — (не перепроверено) |
| 3.2 | High | Go Runtime п.1 sync.Mutex/futex | «при контеншене рантайм Go вызывает futex, погружая горутину в ядровую очередь» | sync.Mutex slow path: runtime_SemacquireMutex → sema root → gopark (горутина паркуется в планировщике Go); futex вызывается лишь рантаймом на M (notesleep/lock) когда M простаивает; также есть spin | sync/mutex.go, runtime/sema.go, runtime/lock_futex.go | — (не перепроверено) |
| 3.3 | High | Interview | «системный вызов getcpu для привязки к процессорам» | Go не использует getcpu для привязки; runtime читает число CPU через sched_getaffinity; getcpu нужен для другого; привязка (affinity) в Go не делается | man 2 sched_setaffinity/mbind; Documentation/admin-guide/mm/numa_memory_policy.rst | ✔ src |
| 3.4 | Medium | Вступление (Таненбаум–Торвальдс) | дословные «цитаты» обоих | реальные тексты другие («LINUX is obsolete», «giant step back into the 1970s»; Торвальдс: «from a theoretical (and aesthetical) standpoint Linux loses»); приведены как прямые цитаты, а это вольный перевод/выдумка | архив comp.os.minix 29–30.01.1992 | — (не перепроверено) |
| 3.5 | Medium | Монолит, «Преимущества» | «пакет обрабатывается драйвером, TCP-стеком и сокетом в рамках единого непрерывного контекста прерывания» | hardirq → NAPI poll в softirq (net_rx_action), TCP в softirq/ksoftirqd, чтение — в контексте процесса; не «единый контекст» | Documentation/networking/napi.rst | — (не перепроверено) |
| 3.6 | Medium | Монолит, «Преимущества» | ftrace, kdump, perf, eBPF как профилирование | kdump — механизм crash dump, не трассировка | man perf/vmstat/iostat; B.Gregg «Linux Performance»; Documentation/bpf/; cilium/ebpf docs; man 2 bpf | — (не перепроверено) |
| 3.7 | Medium | «Как работает» | «tcp_connect()» как то, что вызывает приложение; «нулевые накладные расходы», «никаких переключений контекстов» | tcp_connect — внутренняя ф-я ядра; есть indirect calls/retpolines, lock-contention; FUSE/UIO/VFIO/eBPF показывают, что не всё в Ring 0 | Documentation/bpf/; cilium/ebpf docs; man 2 bpf | — (не перепроверено) |
| 3.8 | Medium | Гибридные ядра | NT/XNU «гибрид» | термин спорный (Торвальдс/Таненбаум: маркетинг); не упомянуты DriverKit/system extensions (macOS 11+ депрекейт kext) и UMDF — драйверы уходят в user space → тезис «сбой драйвера всегда BSOD» устарел частично | seL4 whitepaper; архив comp.os.minix (29–30.01.1992) | — (не перепроверено) |
| 3.9 | Medium | IPC и ctx switch | «TLB shootdown»; «вымывание L1i/L1d при переключении контекста» | shootdown ≠ локальный flush; с PCID/ASID TLB не сбрасывается целиком; L1 кэши физически адресуемые (VIPT) и не сбрасываются при ctx switch | Intel SDM Vol.3 §4.10 (TLB); Documentation/arch/x86/tlb.rst | — (не перепроверено) |
| 3.10 | Medium | IPC | «1000–3000 тактов» → «5–10 мкс на каждый read/write» | 1000–3000 тактов ≈ 0.3–1 мкс на 3ГГц; внутр. противоречие | Intel SDM / AMD APM, Optimization Manual; воспроизводимое измерение (lmbench/perf/fio) или публикация с методикой | — (не перепроверено) |
| 3.11 | Medium | п.3 | «Контейнеризация возможна исключительно благодаря монолитной природе ядра» | FreeBSD jails, Solaris zones, Windows Server Containers (NT «гибрид») – контр-примеры | исходники и Documentation/ ядра, man-страницы (man 2/7); воспроизвести: go build / go vet | — (не перепроверено) |
| 3.12 | Low | Недостатки монолита | «деление на ноль в драйвере → kernel panic» | Oops ≠ panic: без panic_on_oops ядро может продолжить (killing task); в ядре деление на 0 даёт oops | runtime/panic.go; runtime/extern.go (GOTRACEBACK) | — (не перепроверено) |
| 3.13 | Low | seL4 | «широко применяются в авионике, космосе, медицине, авто» | seL4 применяется ограниченно (оборонка, DARPA HACMS и т.п.); широко — QNX | seL4 whitepaper; архив comp.os.minix (29–30.01.1992) | — (не перепроверено) |
| 3.14 | Low | Mermaid | `App["Приложение на Go (User Space):::entry"]` | `:::entry` внутри кавычек выводится как текст, класс не применяется (то же в ст.4 `:::process`) | Mermaid Live Editor; повторная сборка (builder/audit_all.py) | — (не перепроверено) |
| 3.15 | Low | Память и изоляция | утечка в драйвере → «повредит slab/slub» → panic | утечка ≠ порча памяти; приведёт к OOM/ухудшению; | runtime/panic.go; runtime/extern.go (GOTRACEBACK) | — (не перепроверено) |
| 3.16 | Low | «NUMA» | «частая смена таблиц страниц на NUMA приводит к деградации» | non sequitur | man 2 sched_setaffinity/mbind; Documentation/admin-guide/mm/numa_memory_policy.rst | — (не перепроверено) |
| 3.17 | Low | п.2 netpoller | «epoll_pwait или epoll_create» | на linux/amd64 epoll_create1/epoll_ctl/epoll_pwait (arm64) ; netpollBreak через eventfd | runtime/netpoll.go, netpoll_epoll.go; man 7 epoll | — (не перепроверено) |
| 3.18 | Low | Итог | «Go идеально оптимизирован под Linux» | рантайм имеет отдельные netpoll под kqueue/IOCP/Plan 9 | runtime/netpoll.go, netpoll_epoll.go; man 7 epoll; kqueue(2); Microsoft IOCP docs; runtime/netpoll_kqueue.go | — (не перепроверено) |

### Статья 4. Загрузка компьютера. BIOS, UEFI, Bootloader и старт ядра

| № | Приор. | Раздел | Утверждение | Проблема / что проверить | Источник | Статус |
|---|:---:|---|---|---|---|---|
| 4.1 | High | Bootloader п.3 | «Загрузчик переводит CPU в Long Mode (LME в EFER, PML4)» | при UEFI x64 CPU уже в long mode (EFI stub); при BIOS+GRUB переход в long mode делает код ядра (startup_32 в compressed/head_64.S), не загрузчик | Documentation/arch/x86/boot.rst | — (не перепроверено) |
| 4.2 | High | «Старт ядра» | «Образ ядра ... собран по спецификации multiboot» | Linux bzImage использует Linux x86 Boot Protocol, не Multiboot; vmlinux — ELF, bzImage — нет | Documentation/arch/x86/boot.rst | — (не перепроверено) |
| 4.3 | High | head.S | `arch/x86/boot/head.S` | такого файла нет: arch/x86/boot/header.S (real-mode setup), arch/x86/boot/compressed/head_64.S (декомпрессия), arch/x86/kernel/head_64.S (startup_64) | Documentation/arch/x86/boot.rst; arch/x86/boot/* | — (не перепроверено) |
| 4.4 | High | Under the hood task_struct | «До sched_init() task_struct нет» | init_task статически определён в init/init_task.c | init/main.c, init/init_task.c, kernel/fork.c; kernel/fork.c; man 2 clone/execve/wait | — (не перепроверено) |
| 4.5 | High | Interview Q1 | PID1 создаётся kernel_thread(), «аллоцирует сырую task_struct», в отличие от copy_process() | kernel_thread() → kernel_clone() → copy_process(); тот же путь, что fork/clone; PID1 клонируется от init_task | init/main.c, init/init_task.c, kernel/fork.c; kernel/fork.c; man 2 clone/execve/wait | — (не перепроверено) |
| 4.6 | Medium | BIOS п.2 | CS:IP → 0xFFFFFFF0, «доступен 1 МБ» | сброс: CS selector=0xF000, base=0xFFFF0000, IP=0xFFF0; real mode с «скрытой» базой; детали (A20, unreal mode) | UEFI Spec 2.x; Documentation/admin-guide/efi-stub.rst | — (не перепроверено) |
| 4.7 | Medium | GPT/UEFI | «Нативный 32- и 64-битный защищённый режим» | x64 UEFI работает в 64-bit long mode (по спецификации); 32-bit UEFI редкость; первые фазы SEC/PEI стартуют в real/protected | UEFI Spec 2.x; Documentation/admin-guide/efi-stub.rst | — (не перепроверено) |
| 4.8 | Medium | Secure Boot | «Root Key (ключ вендора в чипе) → KEK → DB; процессор на аппаратном уровне блокирует старт» | в UEFI: PK → KEK → db/dbx (хранятся в NVRAM, не «в чипе»); проверку выполняет прошивка (софт), не CPU; в Linux цепочка: shim (подпись MS UEFI CA) → GRUB → ядро; MOK; не упомянут dbx/revocation | UEFI Spec 2.x; Documentation/admin-guide/efi-stub.rst | — (не перепроверено) |
| 4.9 | Medium | Bootloader п.4 | cmdline `kvm=off`; «указатель на неё в регистре rsi на стеке» | `kvm=off` не параметр ядра; boot protocol x86-64: RSI = указатель на boot_params (zero page), cmd_line_ptr — поле в setup header; «на стеке» бессмыслица | Documentation/arch/x86/boot.rst; arch/x86/boot/*; runtime/runtime2.go (gobuf); cmd/compile/abi-internal.md | — (не перепроверено) |
| 4.10 | Medium | SMP Startup | описан ДО start_kernel | APs поднимаются в smp_init() из kernel_init_freeable() (из PID 1 контекста), уже после start_kernel/rest_init | init/main.c, init/init_task.c, kernel/fork.c | — (не перепроверено) |
| 4.11 | Medium | start_kernel | `irq_init()`, `pid_hash_init()` | irq_init нет (init_IRQ, early_irq_init); pid_hash_init удалён (pid_idr_init с 4.15) | init/main.c, init/init_task.c, kernel/fork.c; go.dev/ref/spec#Package_initialization; sync/once.go | — (не перепроверено) |
| 4.12 | Medium | rest_init п.3 | «PID 1 монтирует initramfs» | initramfs распаковывается ядром в rootfs (populate_rootfs) до запуска userspace; PID 1 исполняет /init из него, затем switch_root; «rootfs» в тексте путает с боевым корнем | init/main.c, init/init_task.c, kernel/fork.c; Documentation/filesystems/ramfs-rootfs-initramfs.rst | — (не перепроверено) |
| 4.13 | Medium | Cold start | «Firecracker загружает ядро Linux за 5 мс» | Firecracker заявляет ≤125 мс до userspace и <5 MiB overhead — вероятно, перепутаны «5 MiB» и «5 мс» (⚠ проверить цифру 5 мс по бенчмаркам Firecracker/Cloud Hypervisor) | firecracker SPECIFICATION.md | ⚠ проверить |
| 4.14 | Medium | sysctl fs.file-max | «too many open files» из‑за fs.file-max | EMFILE определяется RLIMIT_NOFILE (ulimit -n); fs.file-max даёт ENFILE («in system»); Go 1.19+ автоматически поднимает soft limit до hard | man 2 getrlimit; syscall/rlimit.go | — (не перепроверено) |
| 4.15 | Medium | somaxconn | «потеря пакетов, connection reset by peer» | при переполнении accept queue — дропы ACK/SYN, ретрансмиты; RST только при tcp_abort_on_overflow=1; default somaxconn 4096 с ядра 5.4; Go читает somaxconn при Listen | man 2 listen; Documentation/networking/ip-sysctl.rst; net/ipv4/tcp_input.c | — (не перепроверено) |
| 4.16 | Medium | Secure Boot/Lockdown | «может сломать сборку Go-приложений с CGO» | lockdown не влияет на сборку CGO; влияет на /dev/mem, kprobes, часть perf/bpf, модули; ptrace не блокируется lockdown'ом | man kernel_lockdown(7) | — (не перепроверено) |
| 4.17 | Low | MBR | «сигнатура 0x55AA» | в little-endian слово 0xAA55 (байты 55 AA по смещению 510) | UEFI Spec 2.x; Documentation/admin-guide/efi-stub.rst | — (не перепроверено) |
| 4.18 | Low | — | — | Cyrillic «KЕК» (смешение алфавитов) | первоисточник по теме (спецификация/документация) | — (не перепроверено) |
| 4.19 | Low | Under the hood UEFI | UEFI drivers = «UEFI-приложения» | драйверы (EFI_BOOT_SERVICES_DRIVER) ≠ приложения; фазы PI (SEC/PEI/DXE/BDS) не названы | UEFI Spec 2.x; Documentation/admin-guide/efi-stub.rst | — (не перепроверено) |
| 4.20 | Low | rest_init | kthreadd создаётся ДО kernel_init | порядок обратный: сначала kernel_init (PID1), потом kthreadd (PID2) | init/main.c, init/init_task.c, kernel/fork.c | — (не перепроверено) |
| 4.21 | Low | Q2 | initramfs извлекается «в tmpfs» | rootfs = ramfs или tmpfs; initramfs может быть встроен в образ ядра | Documentation/filesystems/ramfs-rootfs-initramfs.rst | — (не перепроверено) |
| 4.22 | Low | init() Go | «глобальные мьютексы» «через sync.Once» | zero-value мьютекс; совет упрощён | go.dev/ref/spec#Package_initialization; sync/once.go | — (не перепроверено) |
| 4.23 | Low | vm.max_map_count | «аллокатор Go упадёт с out of memory» | ок как симптом (ENOMEM от mmap), но редкая проблема; default 65530 | runtime/mheap.go, runtime/sizeclasses.go, runtime/malloc.go | — (не перепроверено) |

### Статья 5. Процессы. Жизненный цикл процесса в ОС

| № | Приор. | Раздел | Утверждение | Проблема / что проверить | Источник | Статус |
|---|:---:|---|---|---|---|---|
| 5.1 | High | Go: sync-wait | «cmd.Wait блокирует горутину (не поток M)...» | os.Process.Wait → wait4/waitid блокирующий syscall в текущем M; P передаётся через entersyscallblock/sysmon; поток блокируется; (Go 1.23 на Linux — pidfd + waitid) | os/exec_unix.go, os/pidfd_linux.go | — (не перепроверено) |
| 5.2 | High | RLIMIT_NOFILE | «Если лимит 1024, сервис рухнет на 1025-м (accept: too many open files)»; рекомендация Setrlimit Cur=Max | (1) net/http не падает: Accept → EMFILE, сервер делает backoff-retry; (2) с Go 1.19 runtime сам поднимает soft NOFILE до hard при старте — рекомендация и пример устарели; (3) fatal только при cgo/подпроцессах с select() и т.п. | Go 1.19 release notes (os) | ✔ src |
| 5.3 | Medium | Состояния/ps | TASK_ZOMBIE; D «игнорирует kill -9» | в ядре EXIT_ZOMBIE (exit_state), TASK_ZOMBIE устарел; есть TASK_KILLABLE (NFS/многие ожидания с 2.6.25 убиваются SIGKILL), TASK_IDLE; ps 't' для ptrace-stop, 'T' для job-control stop | man 7 signal; os/signal doc; runtime/signal_unix.go; man 2 ptrace; strace(1) | — (не перепроверено) |
| 5.4 | Medium | Running: «логический процессор M (терминология Go)» | — | в Go логический процессор = P, M = OS thread | runtime/os_linux.go (newosproc, cloneFlags) | — (не перепроверено) |
| 5.5 | Medium | Gotcha зомби | pid_max «обычно 32768 на 32-bit или 4194304 на 64-bit»; ошибка «Cannot allocate memory» | дефолт ядра 32768 (масштабируется по CPU до 4194304 макс); 4194304 выставляет systemd; fork при исчерпании PID → EAGAIN, ENOMEM иное; не упомянут cgroup pids.max | man 5 proc; kernel/pid.c | — (не перепроверено) |
| 5.6 | Medium | Context switch п.2 | «TLB shootdown при миграции процесса между ядрами» | shootdown возникает при изменении mm (munmap/mprotect/COW) когда mm активен на других CPU; миграция сама по себе его не вызывает; противоречит ст.2/3 (там shootdown при каждом CR3) | Intel SDM Vol.3 §4.10 (TLB); Documentation/arch/x86/tlb.rst; arch/x86/kernel/process_64.c (__switch_to); kernel/sched/core.c | — (не перепроверено) |
| 5.7 | Medium | Диаграмма vs текст | горутина ctx switch: диаграмма ~10–200 нс, текст 100–200 нс, Interview ~10–20 нс «в сотни раз быстрее» | внутреннее противоречие; измерения ≈100–250 нс (Gosched/chan ping-pong) | Go benchmarks | — (не перепроверено) |
| 5.8 | Medium | syscall cost | «~50–100 нс» | расходится со ст.2 (100–500 нс); обе без привязки к mitigations | исходники Go (runtime/net/os/syscall), release notes версии; воспроизводимое измерение (lmbench/perf/fio) или публикация с методикой | — (не перепроверено) |
| 5.9 | Medium | Subreaper | «Docker, containerd так работают» | subreaper-ом является containerd-shim/runc-init; сам dockerd — нет; Docker --init использует tini | man 2 prctl (PR_SET_CHILD_SUBREAPER); Docker/containerd docs | — (не перепроверено) |
| 5.10 | Medium | rlimit | «RLIMIT_FSIZE → SIGXCPU или SIGKILL» | FSIZE → SIGXFSZ; RLIMIT_CPU soft → SIGXCPU, hard → SIGKILL | man 2 getrlimit; syscall/rlimit.go; man 7 signal; os/signal doc; runtime/signal_unix.go | — (не перепроверено) |
| 5.11 | Medium | Код Printf | строковый литерал с реальным переносом строки внутри "..." | не компилируется (в ст.6 также) | go build / go vet на листинге | — (не перепроверено) |
| 5.12 | Medium | Interview: память | «100 000 процессов/потоков с стеком 2–8 МБ исчерпает сотни ГБ RAM» | стек потока — виртуальный; резидентно ~ десятки КБ + 16 КБ ядерный стек; реальные лимиты: threads-max, pid_max, max_map_count, cgroup pids; 100k потоков достижимы | runtime/os_linux.go (newosproc, cloneFlags) | — (не перепроверено) |
| 5.13 | Low | Ожидание → Завершен «Сигнал (SIGKILL, SIGTERM)» | — | SIGTERM можно перехватить; не всегда завершает | man 7 signal; os/signal doc; runtime/signal_unix.go; runtime/os_linux.go (newosproc, cloneFlags) | — (не перепроверено) |
| 5.14 | Low | task_struct диагр. | `struct signal_struct *sig // обработчики сигналов` | поле signal (общее состояние), обработчики — sighand_struct *sighand | kernel/fork.c; man 2 clone/execve/wait; man 7 signal; os/signal doc; runtime/signal_unix.go | — (не перепроверено) |
| 5.15 | Low | Cold Cache | «первые сотни микросекунд» | завышено | первоисточник по теме (спецификация/документация) | — (не перепроверено) |
| 5.16 | Low | диаграмма | «Сохранение 14 регистров» | gobuf хранит sp, pc, g, ctxt, ret, lr, bp; число 14 неоткуда | runtime/runtime2.go (gobuf); cmd/compile/abi-internal.md | — (не перепроверено) |
| 5.17 | Low | Release() | счётчик «три сценария», перечислено 4 | редакторское; Release после Start без Wait оставит зомби — ок | os/exec docs; man 2 wait | — (не перепроверено) |
| 5.18 | Low | Under the hood | `runtime.forkExec` | нет такой функции; syscall.forkExec / forkAndExecInChild; флаги зависят от SysProcAttr (Cloneflags, Pdeathsig, Setpgid), в 1.23 CLONE_PIDFD | исходники Go (runtime/net/os/syscall), release notes версии; исходники и Documentation/ ядра, man-страницы (man 2/7) | — (не перепроверено) |
| 5.19 | Low | пакет syscall | пример на syscall, замороженный пакет | лучше x/sys/unix (конфликт с ст.2) | исходники Go (runtime/net/os/syscall), release notes версии; воспроизвести: go build / go vet | — (не перепроверено) |
| 5.20 | Low | task_struct ~8 КБ | — | \| не учтён ядерный стек 16 КБ (THREAD_SIZE) и mm_struct | kernel/fork.c; man 2 clone/execve/wait | — (не перепроверено) |

### Статья 6. Как Linux создает процессы. fork, exec, wait

| № | Приор. | Раздел | Утверждение | Проблема / что проверить | Источник | Статус |
|---|:---:|---|---|---|---|---|
| 6.1 | High | Go: Wait | «Фоновый поток рантайма ... будит горутину» (+ комментарий «уступая поток M») | нет фонового наблюдателя: сама горутина блокируется в wait4/waitid (M блокируется, P отбирается) | runtime/os_linux.go (newosproc, cloneFlags) | — (не перепроверено) |
| 6.2 | Medium | Диаграмма fork | «Kernel-->>Parent: Вернуть PID родителя» | родителю возвращается PID потомка (противоречит тексту выше) | kernel/fork.c; man 2 clone/execve/wait | — (не перепроверено) |
| 6.3 | Medium | exec | «определяются сегменты .text/.data/.bss» | ядро читает program headers (PT_LOAD/PT_INTERP), не секции | man 5 elf; fs/binfmt_elf.c; cmd/link; man 5 elf; Documentation/arch/x86/x86_64/mm.rst | — (не перепроверено) |
| 6.4 | Medium | wait/сигналы | — | не объяснено, что SIGCHLD по умолчанию игнорируется и не жнёт зомби; SA_NOCLDWAIT/SIG_IGN; также PID1 сироты — ок | man 7 signal; os/signal doc; runtime/signal_unix.go | — (не перепроверено) |
| 6.5 | Medium | Go: ForkExec | «рантайм Go написан на чистом ассемблере» | forkAndExecInChild — Go-код //go:nosplit с rawSyscall; ассемблер только rawVforkSyscall; причина CLONE_VM\|VFORK — скорость и невозможность запускать Go-код в потомке | os/exec/exec.go; syscall/exec_linux.go; cmd/compile/abi-internal.md; go.dev/doc/asm | — (не перепроверено) |
| 6.6 | Medium | FD_CLOEXEC | «абсолютно все дескрипторы» | исключения: os.NewFile, унаследованные 0/1/2, syscall.Open без O_CLOEXEC (гонка с ForkLock), cmd.ExtraFiles | man 2 open/fcntl; os/file_unix.go | — (не перепроверено) |
| 6.7 | Medium | Zombie в Docker | «defer cmd.Wait()» как решение | defer в функции после Start заблокирует выход; fire-and-forget нужно `go func(){ cmd.Wait() }()` | os/exec docs; man 2 wait; man 2 prctl (PR_SET_CHILD_SUBREAPER); Docker/containerd docs | — (не перепроверено) |
| 6.8 | Medium | D-state/Wait | Wait виснет бесконечно | пропущен exec.Cmd.WaitDelay и Cmd.Cancel (Go 1.20): без них Wait может зависнуть, если внук держит pipe; также NFS killable | man 7 pipe; os/exec docs (StdoutPipe) | — (не перепроверено) |
| 6.9 | Low | Вступление | «1969 ... fork+exec» | в PDP-7 Unix был fork, exec появился позже (1970–71); датировка упрощена | kernel/fork.c; man 2 clone/execve/wait | — (не перепроверено) |
| 6.10 | Low | fork | «#PF — прерывание процессора» | это исключение (fault), не прерывание; при refcount==1 страница переиспользуется без копии; не упомянуты anon-exclusive (6.x), MADV_DONTFORK, shared mappings | kernel/fork.c; man 2 clone/execve/wait | — (не перепроверено) |
| 6.11 | Low | fork | «kernel stack через kmem_cache» | с 4.9 VMAP_STACK — стек через vmalloc с кэшем | kernel/fork.c; man 2 clone/execve/wait | — (не перепроверено) |
| 6.12 | Low | exec Gotcha | «при ошибке в аргументах ... segfault» | недостоверно: execve при ошибке возвращает -1/errno | kernel/fork.c; man 2 clone/execve/wait; syscall/syscall_linux.go; x/sys/unix; man 2 syscalls | — (не перепроверено) |
| 6.13 | Low | 4. fork 30ГБ | таблицы ~60 МБ, 20–50 мс | число похоже на оценку; для 5-level, hugepages, MADV_DONTFORK иначе; без источника | kernel/fork.c; man 2 clone/execve/wait | — (не перепроверено) |
| 6.14 | Low | omission | — | vfork/posix_spawn/clone3/pidfd; Go 1.23 pidfd | runtime/os_linux.go (newosproc, cloneFlags) | — (не перепроверено) |

### Статья 7. Потоки выполнения. Thread vs Process

| № | Приор. | Раздел | Утверждение | Проблема / что проверить | Источник | Статус |
|---|:---:|---|---|---|---|---|
| 7.1 | Medium | Под капотом, создание потока | «ядро ... резервирует VM под стек потока 8 МБ (ulimit -s), добавляет в VMA» | стек выделяет user space (glibc pthread_create → mmap), ядро получает готовый SP через clone; у musl дефолт 128 КБ (Alpine!), у Go M — g0-стек 16 КБ (без cgo) | man 2 mmap; mm/mmap.c; Documentation/mm/; man 2 getrlimit; syscall/rlimit.go | — (не перепроверено) |
| 7.2 | Medium | TLB Flush | CR3 → сброс TLB без оговорок | PCID/ASID (Linux ≥4.14) — полный flush не нужен; экономия «50–200 тактов» без источника | Intel SDM Vol.3 §4.10 (TLB); Documentation/arch/x86/tlb.rst | — (не перепроверено) |
| 7.3 | Medium | Go vs остальные | «1:1 (Java, C#, Python)» | Java 21 virtual threads (M:N), C# async; Python — 1:1, но GIL/free-threaded 3.13; устарело | JEP 444 (virtual threads), JDK/Python/PHP release notes | — (не перепроверено) |
| 7.4 | Medium | Таблица | «Блокировка на I/O: блокирует только горутину» | верно для сети (netpoller); для файловых/блокирующих syscalls блокируется M, P передаётся (sysmon retake) — противоречит ст.2 | runtime/proc.go (sysmon, retake, handoffp); runtime/netpoll.go, netpoll_epoll.go; man 7 epoll | — (не перепроверено) |
| 7.5 | Medium | Work stealing | «стопроцентная загрузка ядер без участия ядра ОС» | пробуждение простаивающих M требует futex syscall; спиннинговые M жгут CPU | Documentation/virt/kvm/; man top (st) | — (не перепроверено) |
| 7.6 | Medium | PHP | «на каждый HTTP-запрос отдельный процесс» | воркеры пула переиспользуются; запрос↔воркер, не fork на запрос; не упомянуты long-running (Swoole/RoadRunner/FrankenPHP) | JEP 444 (virtual threads), JDK/Python/PHP release notes | — (не перепроверено) |
| 7.7 | Medium | C#/Java | «async/await в Java» | в Java нет async/await (CompletableFuture, виртуальные потоки) | JEP 444 (virtual threads), JDK/Python/PHP release notes | — (не перепроверено) |
| 7.8 | Low | CoW | «ускоряет fork в сотни раз» | без источника | kernel/fork.c; man 2 clone/execve/wait | — (не перепроверено) |
| 7.9 | Low | Gotcha 100 000 потоков | 800 ГБ virtual — верно; «90% времени на ctx switch» | голословно; расходится со ст.5 («сотни ГБ RAM») | runtime/os_linux.go (newosproc, cloneFlags) | — (не перепроверено) |
| 7.10 | Low | «M:N» нотация | в статье M — горутины, N — потоки; в G-M-P M = thread | путаница обозначений | runtime/os_linux.go (newosproc, cloneFlags) | — (не перепроверено) |
| 7.11 | Low | Код | «runtime.GOMAXPROCS(4) – количество физических процессоров» | P — логические, не физические; time.Sleep вместо WaitGroup; Printf с разрывом строки | runtime/debug.go; runtime/cgroup_linux.go; Go 1.25 release notes | — (не перепроверено) |
| 7.12 | Low | `go func()` → «локальная очередь runq» | — | сначала runnext | runtime/proc.go (runqput, runnext) | — (не перепроверено) |
| 7.13 | Low | C++ vs Go | «защищает от Segfault» | nil deref → panic, а data race на slice/interface может портить память | runtime/panic.go; runtime/extern.go (GOTRACEBACK) | — (не перепроверено) |

### Статья 8. Планировщик ОС. Как CPU выбирает, что исполнять

| № | Приор. | Раздел | Утверждение | Проблема / что проверить | Источник | Статус |
|---|:---:|---|---|---|---|---|
| 8.1 | High | Gotcha GOMAXPROCS в K8s | «Всегда подключайте go.uber.org/automaxprocs» | с Go 1.25 (авг 2025) runtime сам учитывает cgroup CPU limit (v1/v2) и обновляет GOMAXPROCS динамически; совет устарел; автомаксы нужен только при go.mod <1.25 или ручном GOMAXPROCS | Go 1.25 release notes; go.dev/blog/container-aware-gomaxprocs | ✔ src |
| 8.2 | High | NUMA | «локальная память ~20 нс, чужая 70–120 нс» | локальная DRAM ≈ 70–100 нс (20 нс — масштаб L3); remote ≈ 130–200+ нс; | Intel MLC, Chips and Cheese | — (не перепроверено) |
| 8.3 | Medium | CFS параметры | sched_latency_ns≈6 мс, min_granularity≈0.75 мс | значения умножаются на (1+log2 ncpu); с 5.13 sysctl→debugfs; в EEVDF (6.6+) параметров нет (base_slice_ns ≈3 мс) — статья не говорит | Documentation/scheduler/sched-eevdf.rst; kernel/sched/fair.c | — (не перепроверено) |
| 8.4 | Medium | EEVDF | «дедлайн раньше для потока, отвечающего на сетевой пакет, получает CPU немедленно» | дедлайн = eligible time + slice/weight; зависит от slice (sched_attr.sched_runtime, поддерж. в 6.12), а не от «I/O-характера»; дерево теперь по deadline с augment min-vruntime; нет lag/eligibility | Documentation/scheduler/sched-eevdf.rst; kernel/sched/fair.c | — (не перепроверено) |
| 8.5 | Medium | Context Switch шаг 1,5 | регистры в thread_info; «JMP/IRET» | switch_to сохраняет callee-saved в task_struct->thread (thread_info на x86_64 — только флаги), остальные — pt_regs при входе в ядро; возврат через ret на новом стеке; FPU/XSAVE — отдельно | runtime/runtime2.go (gobuf); cmd/compile/abi-internal.md; arch/x86/kernel/process_64.c (__switch_to); kernel/sched/core.c | — (не перепроверено) |
| 8.6 | Medium | Цена | «1000–5000 тактов (1–5 мкс)» | 1000–5000 тактов ≈ 0.3–1.7 мкс; «100 000 перекл/с → 30–50% мощности машины» арифметика даёт 10–50% ОДНОГО ядра | исходники и Documentation/ ядра, man-страницы (man 2/7); Intel SDM / AMD APM, Optimization Manual | — (не перепроверено) |
| 8.7 | Medium | IO-bound | P отсоединяется от M в syscall | не сказано: sysmon делает retake только после ≥20 мкс (до 10 мс), поэтому короткие syscalls P не отдают | runtime/os_linux.go (newosproc, cloneFlags) | — (не перепроверено) |
| 8.8 | Medium | NumCPU | «возвращает число физических ядер хост-ноды» | NumCPU = логические CPU в sched_getaffinity на старте (учитывает cpuset/taskset), не физические; квоты CFS не учитывает | runtime/debug.go; runtime/cgroup_linux.go; Go 1.25 release notes | — (не перепроверено) |
| 8.9 | Medium | CFS throttling числа | «исчерпает квоту за первые 10 мс, заморозит на 90 мс» | limit 2 CPU = 200 мс/100 мс; 64 потока выжигают её за ~3 мс; cfs_quota_us — v1, v2 → cpu.max; не упомянут cpu.stat nr_throttled | Documentation/scheduler/sched-eevdf.rst; kernel/sched/fair.c | — (не перепроверено) |
| 8.10 | Medium | LockOSThread | «флаг MLOCKED», «допустимо ... pthread_setaffinity_np» | такого флага нет (lockedg/lockedm/lockedExt); пропущен главный легитимный кейс: per-thread состояние ядра — setns/unshare/network namespaces, seccomp, capabilities; Go не вызывает pthread_* | man 2 sched_setaffinity/mbind; Documentation/admin-guide/mm/numa_memory_policy.rst; runtime/os_linux.go (newosproc, cloneFlags) | — (не перепроверено) |
| 8.11 | Medium | Практика | `/proc/PID/sched`, pidstat -w | для многопоточных процессов /proc/PID/sched и /proc/PID/status показывают только главный поток; нужно /proc/PID/task/TID/ или pidstat -wt | man 5 proc; sysstat docs | — (не перепроверено) |
| 8.12 | Low | эпиграф | «перефразировка Хэмминга» | реальна лишь первая половина («purpose of computing is insight, not numbers»), вторая — выдумка | оригинальный источник цитаты | — (не перепроверено) |
| 8.13 | Low | п.2 | миграция потока «сбрасывает TLB» | миграция даёт холодный TLB/кэш на новом CPU, а не flush | Intel SDM Vol.3 §4.10 (TLB); Documentation/arch/x86/tlb.rst | — (не перепроверено) |
| 8.14 | Low | omission | — | sched_ext (6.12), PREEMPT_RT (6.12), классы RT/DEADLINE | LWN; Documentation/scheduler/sched-ext.rst | — (не перепроверено) |
| 8.15 | Low | G-M-P | «десятки нс» | расходится с ст.5/7 (100–200 нс) | runtime/os_linux.go (newosproc, cloneFlags) | — (не перепроверено) |
| 8.16 | Low | omission | — | steal time на VM, nr_throttled | Documentation/virt/kvm/; man top (st); runtime/os_linux.go (newosproc, cloneFlags) | — (не перепроверено) |

### Статья 9. Context Switch. Почему переключение между потоками дорого

| № | Приор. | Раздел | Утверждение | Проблема / что проверить | Источник | Статус |
|---|:---:|---|---|---|---|---|
| 9.1 | High | Под капотом PCID | «Реальная стоимость ctx switch ... 10 000–50 000 тактов (3–15 мкс)» | расходится со ст.5 (2–5 мкс), ст.7 (1–2), ст.8 (1–5); измерения прямой стоимости ≈1–3 мкс (lmbench lat_ctx, Li et al. 2007 — косвенные до ~мс при больших рабочих наборах) | Intel SDM Vol.3 §4.10 (TLB); Documentation/arch/x86/tlb.rst | — (не перепроверено) |
| 9.2 | High | Cache latencies | «L1 miss ~4 такта, L2 miss ~12–14, L3 miss ~40+ тактов до RAM» | это латентности ПОПАДАНИЯ (L1 hit ≈4–5, L2 hit ≈12–14, L3 hit ≈40–50 тактов); промах L3 → DRAM ≈ 200–300 тактов (≈70–100 нс) — противоречит строкой выше (50–100 нс) | Intel Opt. Manual, Chips and Cheese | — (не перепроверено) |
| 9.3 | High | NUMA | «внутренние механизмы `sched_gomaxprocs`» | такого механизма нет; Go не NUMA-aware (противоречит ст.11) | man 2 sched_setaffinity/mbind; Documentation/admin-guide/mm/numa_memory_policy.rst | ✔ src |
| 9.4 | Medium | Прямые/косвенные | «Branch Predictor Flush / BTB теряет историю при ctx switch» | предиктор не сбрасывается при каждом ctx switch; IBPB выполняется лишь условно при mitigations (Spectre v2) между разными mm | Documentation/admin-guide/hw-vuln/spectre.rst | — (не перепроверено) |
| 9.5 | Medium | switch_to псевдокод | `switch_to` макрос с save_prev_state, flush_tlb_mm | вымышленный код: реально context_switch() вызывает switch_mm_irqs_off() до switch_to(); switch_to→__switch_to_asm сохраняет callee-saved (rbx, rbp, r12–r15, rsp) в thread_struct; flush_tlb_mm не вызывается; код в один ряд | arch/x86/kernel/process_64.c (__switch_to); kernel/sched/core.c | — (не перепроверено) |
| 9.6 | Medium | task_struct | «включает thread_info и массив сохранённых регистров pt_regs» | pt_regs лежит на вершине ядерного стека, не в task_struct | kernel/fork.c; man 2 clone/execve/wait; runtime/runtime2.go (gobuf); cmd/compile/abi-internal.md | — (не перепроверено) |
| 9.7 | Medium | Go-контекст | «контекст G сохраняется на стеке M» | сохраняется в g.sched (gobuf); mcall переключается на g0-стек M | runtime/os_linux.go (newosproc, cloneFlags) | — (не перепроверено) |
| 9.8 | Medium | Go: 14 регистров | «сохраняются 14 регистров общего назначения» | ABIInternal не имеет callee-saved регистров; gobuf: sp, pc, bp, ctxt, ret (+g) — см. ст.5 | runtime/runtime2.go (gobuf); cmd/compile/abi-internal.md | — (не перепроверено) |
| 9.9 | Medium | Go: стоимость | «100–200 нс (1000–2000 тактов)» | 100–200 нс при 3 ГГц = 300–600 тактов | Intel SDM / AMD APM, Optimization Manual; воспроизводимое измерение (lmbench/perf/fio) или публикация с методикой | — (не перепроверено) |
| 9.10 | Medium | work stealing | «Если локальная очередь пуста, рантайм активирует sysmon и делает work stealing» | stealing делает сам M в findRunnable; sysmon не участвует | runtime/proc.go (sysmon, retake, handoffp); runtime/proc.go (runqput, runnext) | — (не перепроверено) |
| 9.11 | Medium | Gotcha п.1 | «если P не находит задачу, рантайм обращается к ядру через sched_yield/pthread_yield» | idle M после spinning засыпает на futex (notesleep) / блокируется в epoll_wait; osyield используется лишь в коротких спин-циклах | runtime/os_linux.go (newosproc, cloneFlags) | — (не перепроверено) |
| 9.12 | Medium | NUMA | «задержка возрастает в 3–5 раз» | типично ×1.3–2 (на 2-сокетных); | man 2 sched_setaffinity/mbind; Documentation/admin-guide/mm/numa_memory_policy.rst | — (не перепроверено) |
| 9.13 | Medium | pprof пример | «высокий % gopark в CPU-профиле = избыточное ожидание» | CPU-профиль не показывает время парковки (оно не жжёт CPU); для этого — block/mutex profile, runtime/trace, goroutine profile; URL без кавычек | net/http/pprof/pprof.go; runtime/pprof | — (не перепроверено) |
| 9.14 | Medium | Оптимизация п.2 | «sysmon будит горутину, когда сокет готов» | netpoll опрашивают M в findRunnable/schedule (блокирующий epoll_wait idle-M) и sysmon лишь если не опрашивали >10 мс | runtime/proc.go (sysmon, retake, handoffp) | — (не перепроверено) |
| 9.15 | Medium | Interview | «STW и сканирование корней стеков обходит все 100 000 горутин» | сканирование стеков конкурентное (GC workers), не в STW; STW-фазы короткие (sweep termination, mark termination) | runtime/mgcmark.go | — (не перепроверено) |
| 9.16 | Low | Итог | «до половины мощности сервера» | гипербола без источника | первоисточник по теме (спецификация/документация) | — (не перепроверено) |

### Статья 10. Приоритеты процессов и потоков. nice, renice, realtime

| № | Приор. | Раздел | Утверждение | Проблема / что проверить | Источник | Статус |
|---|:---:|---|---|---|---|---|
| 10.1 | High | RT доминирует | «ни один CFS-процесс не получит ни одного такта» | по умолчанию RT-throttling: kernel.sched_rt_runtime_us=950000 из sched_rt_period_us=1000000 — 5% резервируется для не-RT; (при -1 отключён; в 6.x есть RT_RUNTIME_SHARE/DL server — fair server в 6.12) | Documentation/scheduler/sched-rt-group.rst; LWN «deadline servers» | — (не перепроверено) |
| 10.2 | High | Go-пример Setpriority | «меняем приоритет процесса ... PRIO_PROCESS, 0» | в Linux nice — свойство потока: setpriority(PRIO_PROCESS,0) меняет только вызывающий поток (текущий M, случайный для горутины); новые потоки наследуют nice от создающего; чтобы менять весь процесс — до старта рантайма (nice/exec) или по /proc/self/task/*; сообщение «Приоритет процесса обновлён» ложно | man 2 setpriority (NOTES), man 7 sched | — (не перепроверено) |
| 10.3 | Medium | Шкала | 140 уровней | не упомянут SCHED_DEADLINE (выше RT, prio −1), SCHED_BATCH/IDLE; маппинг RT: prio = 99 − rt_priority | man 7 sched; Documentation/scheduler/sched-rt-group.rst | — (не перепроверено) |
| 10.4 | Medium | Права RT | «CAP_SYS_ADMIN или SYS_NICE» vs ранее «CAP_SYS_NICE» | CAP_SYS_ADMIN не требуется; также RLIMIT_RTPRIO/RLIMIT_NICE позволяют непривилегированно | man 7 capabilities; syscall.SysProcAttr | — (не перепроверено) |
| 10.5 | Medium | RT в Go | «инверсия приоритетов или зависание демонов» | путаница терминов: это голодание (starvation), инверсия — иное; на SMP остальные CPU работают, RT-throttling защищает | sync/mutex.go; Documentation/locking/ | — (не перепроверено) |
| 10.6 | Medium | Механика п.3 | «TLB thrashing от борьбы потоков с разными приоритетами» | non sequitur: потоки одного mm не инвалидируют TLB друг друга | Intel SDM Vol.3 §4.10 (TLB); Documentation/arch/x86/tlb.rst | — (не перепроверено) |
| 10.7 | Low | Gotcha | `nice` на SCHED_FIFO → EINVAL | setpriority на RT-задачу разрешён (значение хранится, не влияет); EINVAL — не тот случай | man 7 sched; Documentation/scheduler/sched-rt-group.rst; man 2 setpriority; man 7 sched | — (не перепроверено) |
| 10.8 | Low | Interview | «осознанное решение Роба Пайка и Кена Томпсона»; «Redis Priority Queues» | атрибуция без источника; в Redis нет приоритетных очередей (sorted set/несколько списков); select с «приоритетом» требует вложенного select (выбор случайный) | оригинальный источник цитаты | — (не перепроверено) |
| 10.9 | Low | K8s QoS | Guaranteed: «requests==limits» | для ВСЕХ контейнеров и по CPU и по памяти; CPU Manager static даёт эксклюзивные логические CPU, а не «физические ядра» (full-pcpus-only опционально) | Kubernetes docs (kubelet, QoS, CPU Manager) | — (не перепроверено) |
| 10.10 | Low | «миллионы тактов cache warm-up», «задержка в сотни раз» при mcache | — | завышено без источника | runtime/mheap.go, runtime/sizeclasses.go, runtime/malloc.go | — (не перепроверено) |
| 10.11 | Low | cgroup v2 cpu.weight | «точный аналог nice» | аналог, не точный; k8s маппит requests → shares → weight с нелинейным преобразованием | man 2 setpriority; man 7 sched; Documentation/admin-guide/cgroup-v2.rst | — (не перепроверено) |

### Статья 11. CPU Affinity и NUMA

| № | Приор. | Раздел | Утверждение | Проблема / что проверить | Источник | Статус |
|---|:---:|---|---|---|---|---|
| 11.1 | High | Латентности (диаграмма + текст) | «локальная RAM 20–30 нс, удалённая 80–120 нс; L3 10–15 нс» | локальная DRAM ≈ 70–100 нс, удалённая ≈ 120–200+ нс; L3 на серверных Xeon/EPYC ≈ 20–40 нс; ст.8 говорит «20 нс»/70–120 — тот же дефект и разночтение | Intel MLC, AnandTech/Chips and Cheese | — (не перепроверено) |
| 11.2 | High | MPOL_BIND | «ядро вернёт ENOMEM»; mmap/malloc consults mempolicy | страницы аллоцируются при page fault (first touch), а не при mmap; при исчерпании узла идёт reclaim, затем OOM-killer (cgroup/cpuset), не ENOMEM из mmap | Documentation/admin-guide/mm/numa_memory_policy.rst | — (не перепроверено) |
| 11.3 | High | Auto NUMA balancing | «ядро запускает фоновый процесс миграции migratepages и дедупликацию через ksm» | миграция выполняется inline в hinting-fault (task_numa_fault→migrate_misplaced_page) и task_numa_work; migratepages — userspace-утилита; KSM — не про NUMA; | Documentation/admin-guide/sysctl/kernel.rst numa_balancing | — (не перепроверено) |
| 11.4 | High | cgroups v2 cpuset | `cpuset.sched_load_balance`, `cpuset.mems_hardwall` | эти файлы есть только в v1 (и называется cpuset.mem_hardwall); в v2: cpuset.cpus.partition, cpuset.cpus.exclusive, *.effective | Documentation/admin-guide/cgroup-v2.rst | — (не перепроверено) |
| 11.5 | High | GODEBUG=gcresidency=1 | «в Go 1.21+ появился флаг» | такого GODEBUG-флага не существует (проверить runtime/runtime1.go dbgvars; реальные — gctrace, madvdontneed, gcstoptheworld…); весь пункт «мониторинг» вымышлен | исходники Go (runtime/net/os/syscall), release notes версии | ✔ src |
| 11.6 | Medium | Affinity «права» | «менять можно только себе или дочерним» | нужен тот же euid или CAP_SYS_NICE; «дочерним» — неточно | man 7 capabilities; syscall.SysProcAttr | — (не перепроверено) |
| 11.7 | Medium | Under the hood | «активирует флаг SCHED_AFFINITY» | такого флага нет (есть PF_NO_SETAFFINITY, user_cpus_ptr, cpus_mask) | man 1 taskset; kernel/sched/core.c | — (не перепроверено) |
| 11.8 | Medium | taskset gotcha | не упомянуто: `taskset -p` без `-a` меняет только основной поток; потоки Go, созданные до этого, остаются прежними; `taskset -cp` — list-формат, hex — `-p` | практическая ловушка для Go | man 1 taskset; kernel/sched/core.c | — (не перепроверено) |
| 11.9 | Medium | Sticky Task | «при блокировке поток может перейти в TASK_UNINTERRUPTIBLE» | бессмысленно; affinity проверяется при пробуждении/балансировке (select_task_rq), а не «при каждом schedule()» | man 2 sched_setaffinity/mbind; Documentation/admin-guide/mm/numa_memory_policy.rst | — (не перепроверено) |
| 11.10 | Medium | Go runtime / ст.8 | NumCPU = число CPU маски (верно) vs ст.8 «NumCPU = физические ядра хоста» | противоречие между статьями; в Go 1.25 GOMAXPROCS обновляется при смене affinity/cgroup limit | runtime/debug.go; runtime/cgroup_linux.go; Go 1.25 release notes | — (не перепроверено) |
| 11.11 | Medium | mempolicy | «MPOL_PREFERRED — политика по умолчанию» | по умолчанию MPOL_DEFAULT (local с fallback); PREFERRED — один предпочитаемый узел | Documentation/arch/x86/boot.rst; arch/x86/boot/*; man 2 sched_setaffinity/mbind; Documentation/admin-guide/mm/numa_memory_policy.rst | — (не перепроверено) |
| 11.12 | Medium | Auto NUMA | «2.6.38 и 3.8+», «p99 с 2 до 150 мс», «всегда отключают» | NUMA balancing — с 3.8; числа выдуманы; рекомендация отключать — не универсальна (нужен бенчмарк) | man 2 sched_setaffinity/mbind; Documentation/admin-guide/mm/numa_memory_policy.rst | — (не перепроверено) |
| 11.13 | Medium | cgroup пример | echo в cpuset.cpus без `+cpuset` в cgroup.subtree_control родителя | файлов cpuset.* в новой cgroup нет; пример не сработает | man 2 sched_setaffinity/mbind; Documentation/admin-guide/mm/numa_memory_policy.rst; Documentation/admin-guide/cgroup-v2.rst | — (не перепроверено) |
| 11.14 | Medium | K8s | — | пропущен Memory Manager (static) для NUMA-выравнивания памяти (GA 1.32); Topology Manager без него не выравнивает память | Kubernetes docs (kubelet, QoS, CPU Manager) | — (не перепроверено) |
| 11.15 | Medium | Gotcha GOMAXPROCS > NUMA node | «почти гарантированно деградация», «2 процесса по 64 → выигрыш 30–40%» | без источника; зависит от нагрузки; Go GC/планировщик нормально масштабируются на сокеты (в пределах); цифра не подтверждена | man 2 sched_setaffinity/mbind; Documentation/admin-guide/mm/numa_memory_policy.rst; runtime/debug.go; runtime/cgroup_linux.go; Go 1.25 release notes | — (не перепроверено) |
| 11.16 | Low | Вводная | ссылка [[17. NUMA и Hyper-Threading]] «в предыдущей статье» | такого файла нет (в модуле 1: «31. NUMA», «32. Hyper Threading и SMT»); ссылка висячая | man 2 sched_setaffinity/mbind; Documentation/admin-guide/mm/numa_memory_policy.rst; Mermaid Live Editor; повторная сборка (builder/audit_all.py) | — (не перепроверено) |
| 11.17 | Low | pthread_setaffinity_np | «sched_setaffinity для вызывающего потока» | вызывает sched_setaffinity(tid потока-цели) | man 2 sched_setaffinity/mbind; Documentation/admin-guide/mm/numa_memory_policy.rst; runtime/os_linux.go (newosproc, cloneFlags) | — (не перепроверено) |
| 11.18 | Low | mbind | «привязывает уже выделенный диапазон» | без MPOL_MF_MOVE уже размещённые страницы не мигрируют | man 2 sched_setaffinity/mbind; Documentation/admin-guide/mm/numa_memory_policy.rst | — (не перепроверено) |
| 11.19 | Low | «Remote TLB Miss» | — | нет такого термина | Intel SDM Vol.3 §4.10 (TLB); Documentation/arch/x86/tlb.rst | — (не перепроверено) |
| 11.20 | Low | MESI/MOESI snooping по UPI | — | современные Xeon/EPYC используют directory/snoop-filter, а не broadcast snoop | Intel/AMD Optimization Manuals (cache coherency) | — (не перепроверено) |

### Статья 12. Виртуальная память. Почему процессу кажется, что у него своя память

| № | Приор. | Раздел | Утверждение | Проблема / что проверить | Источник | Статус |
|---|:---:|---|---|---|---|---|
| 12.1 | High | Код | `syscall.Madvise(ptr, size, syscall.MADV_WILLNEED)` | сигнатура Madvise(b []byte, advice int) — 3 аргумента не компилируются; MADV_WILLNEED на свежей anon-памяти ничего не префолтит | man 2 madvise; runtime/mgcscavenge.go | ✔ src |
| 12.2 | Medium | Вступление | «5-уровневая адресация — до 4 ПБ» | 57-битное VA: пользовательская половина 2^56 = 64 ПиБ (всего 128 ПиБ) | Documentation/arch/x86/x86_64/5level-paging.rst; Intel SDM Vol.3 §4 | — (не перепроверено) |
| 12.3 | Medium | Под капотом | «PML4 -> PGD -> PUD -> PMD -> PTE» (5 имён на 4 уровня) | в Linux при 4 уровнях PGD≡PML4, PUD≡PDPT, PMD≡PD, PTE≡PT; 5 уровней: PGD(PML5)→P4D(PML4)→PUD→PMD→PTE; противоречит «четыре индекса» | Documentation/arch/x86/x86_64/5level-paging.rst; Intel SDM Vol.3 §4; arch/x86/include/asm/pgtable.h; mm/memory.c | — (не перепроверено) |
| 12.4 | Medium | TLB miss стоимость | «10–50 нс (сотни тактов)» | расходится со ст.13 (50–100+ тактов) и ст.14 (150–400 нс); page walk идёт через кэши (L1/L2/L3) + paging-structure caches, обычно 20–100 тактов, в DRAM — только worst-case; в виртуализации (nested paging) до 24 обращений | Intel SDM Vol.3 §4.10 (TLB); Documentation/arch/x86/tlb.rst | — (не перепроверено) |
| 12.5 | Medium | Go heap | «резервирует сотни ГБ аренами 64 МБ за наносекунды» | с Go 1.11 разреженная куча: арены 64 МБ резервируются по мере роста, а не сотни ГБ заранее; mmap — микросекунды | Go 1.11 notes (sparse heap) | — (не перепроверено) |
| 12.6 | Medium | Scavenger | «GC вызывает madvise и RSS мгновенно падает» | возвращает фоновый scavenger с pacing (~1% CPU, retain ≈ goal+10%, memory limit); RSS падает с задержкой; Go 1.12–1.15 использовал MADV_FREE | man 2 madvise; runtime/mgcscavenge.go; runtime/mgc.go; go.dev/doc/gc-guide | — (не перепроверено) |
| 12.7 | Medium | Interview п.3 | «mmap позволяет выделять без взаимных блокировок» | mmap/munmap берут mmap_lock процесса (write) — глобально; Go снижает частоту через 64 МБ арены | man 2 mmap; mm/mmap.c; Documentation/mm/ | — (не перепроверено) |
| 12.8 | Medium | Таблица glibc | «возврат ОС практически невозможен без malloc_trim» | free() сжимает top через brk (M_TRIM_THRESHOLD=128К), большие блоки (mmap threshold) возвращаются munmap; | glibc symbol versioning docs; man 7 libc | — (не перепроверено) |
| 12.9 | Low | Dirty bit | «критично для сборщика мусора» | Go GC dirty-бит не использует | runtime/mgc.go; go.dev/doc/gc-guide | — (не перепроверено) |
| 12.10 | Low | Mermaid | «Запись адреса в TLB и Page Cache» | Page Cache к TLB не относится | Intel SDM Vol.3 §4.10 (TLB); Documentation/arch/x86/tlb.rst; Documentation/admin-guide/sysctl/vm.rst; mm/filemap.c, mm/page-writeback.c | — (не перепроверено) |
| 12.11 | Low | do_page_fault | — | в современных x86-ядрах exc_page_fault/handle_page_fault | исходники и Documentation/ ядра, man-страницы (man 2/7) | — (не перепроверено) |
| 12.12 | Low | Major fault | «1–10 мс» | для NVMe-swap ~100 мкс; 1–10 мс — HDD; file-backed fault ожидание killable | Documentation/admin-guide/sysctl/vm.rst; mm/vmscan.c, mm/oom_kill.c; NVMe spec; JEDEC/ONFI; документация вендора SSD | — (не перепроверено) |
| 12.13 | Low | JVM | «CMS» | CMS удалён в JDK 14; Parallel тоже может уменьшать кучу (ограниченно) | JEP 444 (virtual threads), JDK/Python/PHP release notes; runtime/os_linux.go (newosproc, cloneFlags) | — (не перепроверено) |
| 12.14 | Low | ссылка | [[13. Страничная организация памяти. Page Tables, TLB, Page Fault.md]] | реальное название «13. Страницы памяти и Page Table» | Intel SDM Vol.3 §4.10 (TLB); Documentation/arch/x86/tlb.rst; Mermaid Live Editor; повторная сборка (builder/audit_all.py) | — (не перепроверено) |

### Статья 13. Страницы памяти и Page Table

| № | Приор. | Раздел | Утверждение | Проблема / что проверить | Источник | Статус |
|---|:---:|---|---|---|---|---|
| 13.1 | High | Go и Huge Pages | «mmap с MAP_HUGETLB или GODEBUG=pagealloc=1» | Go heap не использует MAP_HUGETLB; такого GODEBUG нет; реальные: THP через /sys/kernel/mm/transparent_hugepage, GODEBUG=disablethp=1 (1.21.6+), история 1.21.0–1.21.4 (MADV_COLLAPSE/hugepage hints убраны) | Intel SDM Vol.3 §4.10 (TLB); Documentation/arch/x86/tlb.rst; Documentation/admin-guide/mm/transhuge.rst, hugetlbpage.rst | ✔ src |
| 13.2 | High | Код releaseUnusedPages | import "unsafe" не используется | ошибка компиляции | go build / go vet на листинге | — (не перепроверено) |
| 13.3 | High | Interview Q2 | «M блокируется на major fault; планировщик Go замечает и отсоединяет P» | page fault происходит в user-коде (статус P=_Prunning, не syscall): sysmon не делает handoff (retake освобождает P только у потока в syscall); P простаивает, пока M ждёт I/O (горутины из его runq могут быть украдены другими P) | runtime/proc.go retake | — (не перепроверено) |
| 13.4 | Medium | Размер страницы | «4 КБ на x86-64 и ARM64» | ARM64: 4/16/64 КБ (Apple Silicon/macOS 16 КБ; RHEL/Alma aarch64 64 КБ) | Documentation/arch/arm64/memory.rst; ARM ARM | — (не перепроверено) |
| 13.5 | Medium | Gotcha Huge Pages | «выделение Huge Page завершится ENOMEM» | смешаны hugetlbfs (ENOMEM/SIGBUS) и THP (тихий fallback на 4К, compaction stalls); «резервировать на старте» верно только для hugetlb | Documentation/admin-guide/mm/transhuge.rst, hugetlbpage.rst; runtime/os_linux.go (newosproc, cloneFlags) | — (не перепроверено) |
| 13.6 | Medium | mspan | «span = 1–16 страниц, 4–64 КБ» | страница runtime = 8 КБ (не 4 КБ ОС); small-спаны 8–80 КБ (1–10 страниц), large — произвольно | runtime/mheap.go, runtime/sizeclasses.go, runtime/malloc.go | — (не перепроверено) |
| 13.7 | Medium | Возврат памяти | «munmap вызвал бы дорогой TLB shootdown; madvise — нет» | madvise(MADV_DONTNEED) тоже зачищает PTE и требует TLB flush/IPI; | Intel SDM Vol.3 §4.10 (TLB); Documentation/arch/x86/tlb.rst; man 2 madvise; runtime/mgcscavenge.go | — (не перепроверено) |
| 13.8 | Medium | scavenger trigger | «при срабатывании триггеров GC (GOGC/GOMEMLIMIT) скавенджер вызывает madvise» | скавенджер — отдельная пейсируемая горутина (bgscavenge), не вызывается триггером GC | man 2 madvise; runtime/mgcscavenge.go; Go 1.19 release notes; runtime/debug/garbage.go | — (не перепроверено) |
| 13.9 | Medium | TLB Miss | «4 последовательных чтения из DRAM, 50–100+ тактов» | внутреннее противоречие и см. [12]; | Intel SDM Vol.3 §4.10 (TLB); Documentation/arch/x86/tlb.rst; runtime/os_linux.go (newosproc, cloneFlags) | — (не перепроверено) |
| 13.10 | Medium | Диагностика | «растут Major PF → ушли в swap!» | major faults бывают и при mmap-файлах/холодном бинаре без swap; противоречит определению выше | Documentation/admin-guide/sysctl/vm.rst; mm/vmscan.c, mm/oom_kill.c | — (не перепроверено) |
| 13.11 | Low | `MHeapMap_SpanInUse` | — | идентификатор Go ≤1.2, сейчас mSpanInUse/mSpanFree | man 5 elf; Documentation/arch/x86/x86_64/mm.rst | ✔ src |
| 13.12 | Low | NUMA | «mcache стараются держать память ближе к коду» | NUMA-логики у mcache нет (см. 9/11) | man 2 sched_setaffinity/mbind; Documentation/admin-guide/mm/numa_memory_policy.rst; runtime/mheap.go, runtime/sizeclasses.go, runtime/malloc.go | — (не перепроверено) |
| 13.13 | Low | Escape analysis | «sync.Pool снизит оверхед на madvise» | non sequitur | man 2 madvise; runtime/mgcscavenge.go; cmd/compile escape analysis; go build -gcflags=-m | — (не перепроверено) |
| 13.14 | Low | рекомендация «буферы кратны 4 КБ» | — | в Go размеры идут по size-классам; рекомендация сомнительна | runtime/mheap.go, runtime/sizeclasses.go, runtime/malloc.go | — (не перепроверено) |

### Статья 14. TLB и стоимость промаха по таблице страниц

| № | Приор. | Раздел | Утверждение | Проблема / что проверить | Источник | Статус |
|---|:---:|---|---|---|---|---|
| 14.1 | High | Стоимость | «4 последовательных чтения из DRAM, 150–400 нс» | PTE кэшируются в L1/L2/L3 и PWC; типичный TLB-miss 20–100 тактов; DRAM-worst-case; diagram 50–150 нс, text 150–400 нс, bash 50–200 тактов — внутренние противоречия | runtime/os_linux.go (newosproc, cloneFlags) | — (не перепроверено) |
| 14.2 | High | badPattern | `make([]byte,256)` в цикле «миллион аллокаций в куче» | не уходит в кучу: константный размер, не escapes → стек/выкидывается; пример не демонстрирует тезис | man 5 elf; Documentation/arch/x86/x86_64/mm.rst | — (не перепроверено) |
| 14.3 | Medium | Page Walk | «в микрокоде процессора» | отдельный аппаратный page-walker (FSM), не микрокод; на некоторых RISC TLB программный | Intel SDM Vol.3 §4, §28 (EPT); AMD APM Vol.2 | — (не перепроверено) |
| 14.4 | Medium | TLB shootdown | «при смене контекста процессор шлёт IPI всем ядрам» | shootdown — при изменении mm (munmap/mprotect/migrate) и только CPU из mm_cpumask; при ctx switch IPI нет; «10–30 тыс. тактов» без источника | Intel SDM Vol.3 §4.10 (TLB); Documentation/arch/x86/tlb.rst | — (не перепроверено) |
| 14.5 | Medium | GC «рассеивает данные» | «GC начинает рассеивать связанные данные по страницам» | Go GC non-moving, не компактирует; разброс определяется аллокатором (size-классы, спаны) | runtime/mgc.go; go.dev/doc/gc-guide | — (не перепроверено) |
| 14.6 | Medium | блокирующий syscall | «M засыпает → честное переключение контекста с вымыванием TLB» | переключение на другой поток того же процесса TLB не сбрасывает (противоречит ст.7 и тексту выше) | Intel SDM Vol.3 §4.10 (TLB); Documentation/arch/x86/tlb.rst; runtime/os_linux.go (newosproc, cloneFlags) | — (не перепроверено) |
| 14.7 | Medium | THP | рекомендация `always` | для latency-sensitive чаще `madvise`/never из-за compaction stalls и раздувания RSS; история Go 1.21 с THP не упомянута | Documentation/admin-guide/mm/transhuge.rst, hugetlbpage.rst | — (не перепроверено) |
| 14.8 | Medium | Interview Q1 | «Huge Pages ускоряют на 15–25%», «hit rate ≈100%, полностью устраняя» | числа без источника; в L1 dTLB на 2М-страницы всего ~32 записи | Documentation/admin-guide/mm/transhuge.rst, hugetlbpage.rst | — (не перепроверено) |
| 14.9 | Low | TLB размеры | Zen4/SPR: L1 dTLB 64–96, STLB 1536–2048 | Zen4 L2 DTLB 3072; Golden Cove iTLB 256; цифры устарели/неточны | Intel SDM Vol.3 §4.10 (TLB); Documentation/arch/x86/tlb.rst | — (не перепроверено) |
| 14.10 | Low | sync.Pool | «хранит []byte; страницы вечно горячие, давление падает до нуля» | пул чистится за 2 GC (victim cache); хранение []byte вызывает аллокацию заголовка (SA6002), лучше *[]byte | sync/pool.go; staticcheck SA6002 | — (не перепроверено) |
| 14.11 | Low | Q2 | «GC сканирует всю кучу» | сканируются достижимые объекты (mark); sweep — спаны | runtime/mgc.go; go.dev/doc/gc-guide; man 5 elf; Documentation/arch/x86/x86_64/mm.rst | — (не перепроверено) |

### Статья 15. malloc под капотом. Откуда ОС берет память

| № | Приор. | Раздел | Утверждение | Проблема / что проверить | Источник | Статус |
|---|:---:|---|---|---|---|---|
| 15.1 | High | False Sharing | «Аллокатор Go предотвращает false sharing, выравнивая спаны и объекты по степеням двойки» | неверно: size-классы (24, 48, 80…) не выровнены по 64 Б; разные объекты в одном span делят cache line; tiny allocator склеивает <16 Б; защита — ручной padding (cpu.CacheLinePad) | golang.org/x/sys/cpu (CacheLinePad); Intel Optimization Manual | — (не перепроверено) |
| 15.2 | Medium | brk | «brk используется для выделения стека (mmap с MAP_GROWSDOWN)»; диаграмма «Стек потока MAP_GROWSDOWN» | бессмыслица: стек главного потока растёт через VMA growsdown, стеки потоков (glibc) — mmap(MAP_STACK\|MAP_PRIVATE\|MAP_ANONYMOUS) с guard-page; brk к стеку отношения не имеет | man 2 mmap; mm/mmap.c; Documentation/mm/; man 2 brk; runtime/mem_linux.go | — (не перепроверено) |
| 15.3 | Medium | VMA | «связанный список и красно-чёрное дерево» | с Linux 6.1 VMA хранятся в maple tree (rbtree и mm->mmap list удалены) | LWN maple tree | — (не перепроверено) |
| 15.4 | Medium | Go аллокатор | «lock-free менеджер runtime.malloc» | lock-free только быстрый путь mcache; mcentral/mheap берут блокировки (mheap_.lock, pageAlloc); функция — mallocgc | runtime/mheap.go, runtime/sizeclasses.go, runtime/malloc.go | — (не перепроверено) |
| 15.5 | Medium | Huge Pages в Go | «рантайм может подсказать madvise(MADV_HUGEPAGE)… полностью ликвидирует Page Walk» | Go 1.21.0 использовал MADV_HUGEPAGE/COLLAPSE, убрано в 1.21.4; по умолчанию сейчас не вызывает; «полностью ликвидирует» — нет | Intel SDM Vol.3 §4, §28 (EPT); AMD APM Vol.2; Documentation/admin-guide/mm/transhuge.rst, hugetlbpage.rst | — (не перепроверено) |
| 15.6 | Medium | MADV_DONTNEED | «сохраняет запись в таблице страниц» | PTE зачищаются (zap), остаётся VMA; повторное обращение — page fault на нулевую страницу; «в сотни раз дешевле munmap+mmap» без источника | man 2 madvise; runtime/mgcscavenge.go | — (не перепроверено) |
| 15.7 | Medium | Interview п.3, Q2 | «исключить глобальные блокировки кучи»; «скавенджер вычищает через madvise или munmap» | у mheap есть глобальные локи; скавенджер munmap не вызывает | man 2 madvise; runtime/mgcscavenge.go; man 5 elf; Documentation/arch/x86/x86_64/mm.rst | — (не перепроверено) |
| 15.8 | Low | вступление | «95% времени на переход в Ring 0» | гипербола | Intel SDM / AMD APM, Optimization Manual | — (не перепроверено) |
| 15.9 | Low | free и brk | «free не может вернуть ядру ни байта» | free() сжимает top (M_TRIM_THRESHOLD), malloc_trim() освобождает страницы в середине через madvise(DONTNEED) (glibc ≥2.8) | man 2 brk; runtime/mem_linux.go | — (не перепроверено) |
| 15.10 | Low | glibc | «арены: brk (или суб-арены)» | только main arena использует brk; остальные — mmap-кучи по 64 МБ; mmap_threshold динамический (растёт до 32 МБ) | man 2 brk; runtime/mem_linux.go; glibc symbol versioning docs; man 7 libc | — (не перепроверено) |
| 15.11 | Low | Mermaid | — | `:::process` внутри label (см. выше) | Mermaid Live Editor; повторная сборка (builder/audit_all.py) | — (не перепроверено) |
| 15.12 | Low | mspan | «смежные физические страницы ядра, 8–64 КБ» | страница runtime = 8 КБ виртуальных; физическая смежность не требуется | runtime/mheap.go, runtime/sizeclasses.go, runtime/malloc.go | — (не перепроверено) |
| 15.13 | Low | Roadmap (ст.1) обещает jemalloc/tcmalloc | — | в статье только glibc и описание Go | glibc symbol versioning docs; man 7 libc | — (не перепроверено) |

### Статья 16. Copy On Write. Почему fork не копирует всю память сразу

| № | Приор. | Раздел | Утверждение | Проблема / что проверить | Источник | Статус |
|---|:---:|---|---|---|---|---|
| 16.1 | High | Под капотом | «флаг CoW для fork реализован через бит PTE_SOFT_DIRTY» | soft-dirty — трекинг записей (CRIU), к COW не относится | kernel/fork.c; man 2 clone/execve/wait; arch/x86/include/asm/pgtable.h; mm/memory.c | — (не перепроверено) |
| 16.2 | High | Под капотом | «MAP_SHARED использует аналогичный механизм» | COW только для MAP_PRIVATE; MAP_SHARED пишет в общую страницу/page cache, без копирования | man 2 mmap; mm/mmap.c; Documentation/mm/ | — (не перепроверено) |
| 16.3 | High | RSS/SHR после fork | «SHR == RSS, оба процесса делят 100% памяти; доказательство CoW» | `SHR` (top/statm) = RssFile+RssShmem (file/shmem), анонимные COW-страницы там НЕ учитываются, у обоих они в RssAnon; для оценки нужен PSS (/proc/PID/smaps_rollup); для Go-потомка с CLONE_VM вообще нет отдельного RSS до exec | kernel/fork.c; man 2 clone/execve/wait | — (не перепроверено) |
| 16.4 | High | Код MADV_DONTFORK | `syscall.Madvise(unsafe.Pointer(&buf[0]), len, flag)` | сигнатура Madvise([]byte, int) — не компилируется; адрес должен быть page-aligned (иначе EINVAL), make([]byte,1024) лежит в общем spans с другими объектами; в Go-сценарии exec/CLONE_VM DONTFORK смысла не имеет (память не копируется, после exec исчезает); корректный инструмент для секретов — MADV_WIPEONFORK / memfd_secret / mlock | man 2 madvise; runtime/mgcscavenge.go | ✔ src |
| 16.5 | Medium | Введение | «клон процесса за доли микросекунды с нулевым расходом физической памяти» | копируются PTE (десятки мкс – десятки мс на ГБ-кучи, ср. ст.6: 20–50 мс/30 ГБ) и тратится память на сами page tables; | arch/x86/include/asm/pgtable.h; mm/memory.c; man 5 elf; Documentation/arch/x86/x86_64/mm.rst | — (не перепроверено) |
| 16.6 | Medium | PTE flags | «снимает PTE_WRITE, ставит PTE_RDONLY» | на x86 нет бита RDONLY (только R/W сбрасывается); COW-флага нет: do_wp_page решает по VMA (private+writable) и refcount/AnonExclusive; | arch/x86/include/asm/pgtable.h; mm/memory.c | — (не перепроверено) |
| 16.7 | Medium | omission | — | если refcount==1 (родитель уже exec/exit) страница переиспользуется без копирования — ключ для fork+exec | kernel/fork.c; man 2 clone/execve/wait | — (не перепроверено) |
| 16.8 | Medium | hugepages COW | «снижает оверхед» | COW-fault на THP/HugeTLB копирует 2 МБ (или сплитит PMD) — известный источник latency spikes и раздувания памяти (Redis рекомендует отключать THP) | mm/memory.c (do_wp_page); Documentation/mm/; Documentation/admin-guide/mm/transhuge.rst, hugetlbpage.rst | — (не перепроверено) |
| 16.9 | Medium | Go os/exec и CoW | комментарий «fork() -> CoW»; Итог п.3 «благодаря CoW и CLONE_VFORK» | в Go-пути COW не используется вообще (CLONE_VM, общий mm); статья противоречит себе | kernel/fork.c; man 2 clone/execve/wait; os/exec/exec.go; syscall/exec_linux.go | — (не перепроверено) |
| 16.10 | Medium | fork в Go | «Если нужен fork с долгоживущим потомком, вызовите LockOSThread до форка» | LockOSThread этого не решает; fork без exec в Go-процессе не поддерживается (в потомке остаётся один поток, нет GC-воркеров/sysmon, runtime непригоден); пример «как PHP-FPM» — это C-приложение | kernel/fork.c; man 2 clone/execve/wait | — (не перепроверено) |
| 16.11 | Medium | ForkExec | «ассемблерный syscall.ForkExec» | Go-код (nosplit) | os/exec/exec.go; syscall/exec_linux.go; cmd/compile/abi-internal.md; go.dev/doc/asm | — (не перепроверено) |
| 16.12 | Medium | Q2 | «терабайты без копирования: pipe()/socketpair()» | pipe/socketpair копируют данные через буфер ядра (2 копии); без копий — shared memory (memfd+MAP_SHARED), либо COW до fork; пример неверен | man 7 pipe; os/exec docs (StdoutPipe) | — (не перепроверено) |
| 16.13 | Medium | Q5 posix_spawn | «объединяет fork+exec в один системный вызов ядра» | posix_spawn — библиотечная функция; в glibc ≥2.24 реализована через clone(CLONE_VM\|CLONE_VFORK)+exec; | kernel/fork.c; man 2 clone/execve/wait | — (не перепроверено) |
| 16.14 | Low | Under the hood fork | «do_fork()» | в современных ядрах kernel_clone() (ст.6 правильно) | kernel/fork.c; man 2 clone/execve/wait | — (не перепроверено) |
| 16.15 | Low | Q4 | «GC в потомке сканирует и порождает COW» | в потомке после fork нет GC-воркеров (один поток); сценарий гипотетический | mm/memory.c (do_wp_page); Documentation/mm/; runtime/mgc.go; go.dev/doc/gc-guide | — (не перепроверено) |
| 16.16 | Low | Java | «Java 9+ ProcessHandle и нативная posix_spawn» | ProcessHandle — API мониторинга; spawn через jspawnhelper (POSIX_SPAWN дефолт на Linux с JDK 12) | JEP 444 (virtual threads), JDK/Python/PHP release notes | — (не перепроверено) |
| 16.17 | Low | PHP-FPM | COW-пример | refcount-записи в zval постепенно ломают COW; opcache — shared memory | mm/memory.c (do_wp_page); Documentation/mm/; JEP 444 (virtual threads), JDK/Python/PHP release notes | — (не перепроверено) |

### Статья 17. Paging и Swapping

| № | Приор. | Раздел | Утверждение | Проблема / что проверить | Источник | Статус |
|---|:---:|---|---|---|---|---|
| 17.1 | High | Код | `debug.MemoryLimit()` | такой функции нет (SetMemoryLimit(-1) возвращает текущее значение); не компилируется; Printf с переносом | Go 1.19 release notes; runtime/debug/garbage.go; go build / go vet на листинге | ✔ src |
| 17.2 | Medium | Page fault типы | «Invalid = Hard Page Fault / Ошибка сегментации» | в литературе (Windows) hard fault = major (чтение с диска); в Linux — minor/major/invalid; противоречит ст.12–13 (Major) | Documentation/admin-guide/mm/; man 2 getrusage (ru_majflt); man 5 elf; Documentation/arch/x86/x86_64/mm.rst | — (не перепроверено) |
| 17.3 | Medium | Latencies | NVMe 50–100 мкс — верно, но ст.12–13 «major fault 1–10 мс» | разночтения; для swap на NVMe major ≈ 100 мкс | NVMe spec; JEDEC/ONFI; документация вендора SSD; Documentation/admin-guide/mm/; man 2 getrusage (ru_majflt) | — (не перепроверено) |
| 17.4 | Medium | Swap в K8s | «swap отключают swapoff -a» | kubelet по умолчанию failSwapOn=true; но NodeSwap (beta 1.28, LimitedSwap) уже поддерживается — статья не отражает (проверить статус GA 1.34); не упомянуты cgroup v2 memory.swap.max/memory.high, zswap/zram, PSI (/proc/pressure/memory), systemd-oomd/earlyoom, MGLRU (6.1) | Documentation/admin-guide/sysctl/vm.rst; mm/vmscan.c, mm/oom_kill.c; Kubernetes docs (kubelet, QoS, CPU Manager) | ⚠ проверить |
| 17.5 | Medium | GOMEMLIMIT | «предотвращает вытеснение в swap и защищает от OOM» | soft limit; не учитывает cgo/нерантаймовую память; при live heap ≥ limit GC уходит в «death spiral» (CPU cap 50%); рекомендуют ~90–95% от cgroup limit; в примере захардкожено 2 GiB | Documentation/admin-guide/sysctl/vm.rst; mm/vmscan.c, mm/oom_kill.c; Go 1.19 release notes; runtime/debug/garbage.go | — (не перепроверено) |
| 17.6 | Low | Под капотом | «таблица для 64-битного процесса занимала бы петабайты» | для 48 бит плоская таблица = 512 ГиБ; для полных 64 — 32 ПиБ | первоисточник по теме (спецификация/документация) | — (не перепроверено) |
| 17.7 | Low | swap | — | сначала вытесняется page cache (чистые файловые страницы), не только anon; vm.swappiness=0 ≠ «без swap» | Documentation/admin-guide/sysctl/vm.rst; mm/vmscan.c, mm/oom_kill.c | — (не перепроверено) |
| 17.8 | Low | Interview стек горутин | «защищает ядро от траты страниц и накладных расходов на perf и strace» | не имеет отношения; стек — из mheap (stackalloc), с 1.19 стартовый размер адаптивный | runtime/stack.go, runtime/proc.go (maxstacksize); man perf/vmstat/iostat; B.Gregg «Linux Performance» | — (не перепроверено) |
| 17.9 | Low | swapon -s | — | устарело, `swapon --show` | Documentation/admin-guide/sysctl/vm.rst; mm/vmscan.c, mm/oom_kill.c | — (не перепроверено) |
| 17.10 | Low | Prometheus | «любое ненулевое pswpin — тревога» | избыточно строго | первоисточник по теме (спецификация/документация) | — (не перепроверено) |
| 17.11 | Low | «Huge Pages снижает TLB misses на 10–30%» | — | без источника | Intel SDM Vol.3 §4.10 (TLB); Documentation/arch/x86/tlb.rst; Documentation/admin-guide/mm/transhuge.rst, hugetlbpage.rst | — (не перепроверено) |

### Статья 18. mmap. Отображение файлов и памяти

| № | Приор. | Раздел | Утверждение | Проблема / что проверить | Источник | Статус |
|---|:---:|---|---|---|---|---|
| 18.1 | Medium | Вступление | «BoltDB, LMDB, SQLite, RocksDB используют mmap… WAL-журналы» | SQLite mmap выключен по умолчанию (mmap_size=0), RocksDB allow_mmap_reads=false по умолчанию, у bbolt нет WAL; не упомянуты минусы (статья Crotty/Leis/Pavlo «Are You Sure You Want to Use MMAP in Your DBMS?», CIDR 2022; MongoDB MMAPv1 удалён) | CIDR'22 | — (не перепроверено) |
| 18.2 | Medium | Код | не импортирован `unsafe`, импортирован неиспользуемый `bytes`; Printf с разрывом строки | не компилируется; лучше unix.Msync; pdflush удалён в 2.6.32 | go build / go vet на листинге | — (не перепроверено) |
| 18.3 | Medium | Q1/Q3 | «Вызовом file.Munmap(buf)» | нет такого метода (сам же текст говорит, что os.File.Mmap нет); «гипотетический os.File.Mmap» — соломенное чучело | исходники Go (runtime/net/os/syscall), release notes версии | — (не перепроверено) |
| 18.4 | Medium | GC | — | не сказано: Go-указатели в mmap-области GC не видит; хранить там указатели на кучу нельзя | runtime/mgc.go; go.dev/doc/gc-guide | — (не перепроверено) |
| 18.5 | Medium | Таблица | «random access через read — катастрофически медленный (lseek+read)»; «альтернатив mmap в POSIX не существует» | есть pread/pwrite (1 syscall), O_DIRECT, io_uring, пулы буферов (Postgres, MySQL, RocksDB по умолчанию); утверждение неверно | man 2 mmap; mm/mmap.c; Documentation/mm/ | — (не перепроверено) |
| 18.6 | Low | Диаграмма vs текст | — | major fault «1–5 мс» на диаграмме vs «50–100 мкс NVMe» в тексте; cache-hit «5–10 нс» (для уже отображённой страницы — это просто доступ к памяти: L1 ≈1 нс, DRAM ≈80 нс) | NVMe spec; JEDEC/ONFI; документация вендора SSD; Documentation/admin-guide/mm/; man 2 getrusage (ru_majflt) | — (не перепроверено) |
| 18.7 | Low | Под капотом | «флаг VM_FILE» | такого флага нет; признак — vma->vm_file != NULL | первоисточник по теме (спецификация/документация) | — (не перепроверено) |
| 18.8 | Low | Влияние на TLB | MAP_HUGETLB для file mmap | недоступно на обычных ФС (только hugetlbfs/anon); «15–20% потерь» без источника | Intel SDM Vol.3 §4.10 (TLB); Documentation/arch/x86/tlb.rst; man 2 mmap; mm/mmap.c; Documentation/mm/ | — (не перепроверено) |
| 18.9 | Low | SIGBUS | — | в Go SIGBUS из mmap-региона → fatal error unexpected fault address; смягчается debug.SetPanicOnFault(true) — не упомянуто; чтение хвоста последней страницы за EOF даёт нули | man 7 signal; os/signal doc; runtime/signal_unix.go | — (не перепроверено) |
| 18.10 | Low | omission | — | MAP_POPULATE, madvise(MADV_SEQUENTIAL/RANDOM/WILLNEED), mlock, fault-around (64 КБ); mmap_lock contention в многопоточных сервисах | man 2 mmap; mm/mmap.c; Documentation/mm/; man 2 madvise; runtime/mgcscavenge.go | — (не перепроверено) |

### Статья 19. Сегментация памяти процесса. Stack, Heap, Data, Text

| № | Приор. | Раздел | Утверждение | Проблема / что проверить | Источник | Статус |
|---|:---:|---|---|---|---|---|
| 19.1 | High | «sysmon и madvise» | «sysmon каждые 10 мс–1 с проверяет свободную память и вызывает madvise; ядро отменяет маппинг; mmap возвращает тот же адрес» | возвращает фоновый scavenger (bgscavenge, sysmon лишь будит); маппинг остаётся, меняется только резидентность; повторного mmap нет | man 2 mmap; mm/mmap.c; Documentation/mm/; man 2 madvise; runtime/mgcscavenge.go | — (не перепроверено) |
| 19.2 | High | Interview п.1–4 | «brk возвращает при sbrk(0)−old_brk», «упрощает конкурентный GC», «избегает race brk/mmap», «Go мьютексы для heap не нужны» | набор ложных обоснований; у mheap есть блокировки; Go munmap почти не использует | man 2 mmap; mm/mmap.c; Documentation/mm/; man 2 brk; runtime/mem_linux.go | — (не перепроверено) |
| 19.3 | High | Диагностика утечки | «HeapAlloc растёт, HeapInuse стабилен → mmap-подпись» | HeapInuse ≥ HeapAlloc по определению; рекомендация бессмысленна | man 2 mmap; mm/mmap.c; Documentation/mm/; runtime/mstats.go; runtime.MemStats docs | — (не перепроверено) |
| 19.4 | Medium | ASLR | «ядро смещает стек, кучу, mmap и код» | в Go: heap-арены запрашиваются по фиксированным hint-адресам (0xc000000000), text для non-PIE (default linux/amd64) не рандомизируется (нужен -buildmode=pie) | man 2 mmap; mm/mmap.c; Documentation/mm/; GCC -fstack-protector/-fstack-clash-protection; CVE-2017-1000364 | — (не перепроверено) |
| 19.5 | Medium | Go text | пропущены .rodata/.noptrdata/.noptrbss/.gopclntab; строковые литералы названы в .data | литералы в .rodata (read-only) | man 5 elf; fs/binfmt_elf.c; cmd/link; man 5 elf; Documentation/arch/x86/x86_64/mm.rst | — (не перепроверено) |
| 19.6 | Medium | BSS | «выделяет физическую память сразу при старте, заполняя нулями (или zero page)» | BSS — anonymous zero-fill, физические страницы выделяются лениво при первом касании; формулировка противоречит сама себе | Mermaid Live Editor; повторная сборка (builder/audit_all.py) | — (не перепроверено) |
| 19.7 | Medium | Heap | «если запрос больше страницы, ядро делает mmap» | решение о mmap принимает аллокатор libc по mmap_threshold, не ядро | man 2 mmap; mm/mmap.c; Documentation/mm/; man 5 elf; Documentation/arch/x86/x86_64/mm.rst | — (не перепроверено) |
| 19.8 | Medium | Go heap | «резервирует колоссальный непрерывный диапазон» | см. [12]: sparse heap, арены по мере роста | исходники Go (runtime/net/os/syscall), release notes версии | — (не перепроверено) |
| 19.9 | Medium | MemStats | «HeapAlloc — живые объекты, включая метаданные span'ов»; `runtime.GC()` «инициализирует runtime» | HeapAlloc = байты выделенных (ещё не освобождённых) объектов, без метаданных; GC — не инициализация; Printf-разрыв | runtime/mstats.go; runtime.MemStats docs; runtime/mgc.go; go.dev/doc/gc-guide | — (не перепроверено) |
| 19.10 | Medium | morestack | «runtime.morestack_noctxt делает mmap новой страницы» | newstack→stackalloc из пулов/спанов mheap; mmap на каждый рост не вызывается | man 2 mmap; mm/mmap.c; Documentation/mm/; runtime/stack.go, runtime/proc.go (maxstacksize) | — (не перепроверено) |
| 19.11 | Medium | Gotcha make([]int,1000000) | «если убегает — в heap» | слайс >64 КБ (maxImplicitStackVarSize) всегда в куче независимо от escape | cmd/compile escape analysis; go build -gcflags=-m | — (не перепроверено) |
| 19.12 | Medium | TLB | «Go группирует объекты в span'ы по 64–512 КБ» | спаны 8–80 КБ (large — произвольно); 64 МБ — арены; противоречит ст.13/15 | Intel SDM Vol.3 §4.10 (TLB); Documentation/arch/x86/tlb.rst | — (не перепроверено) |
| 19.13 | Medium | Таблица | «mspan: power-of-two sizing, free lists»; «Выделение: madvise, munmap» | size-классы не степени двойки; используется allocBits/freeindex; madvise/munmap — освобождение, не выделение | man 2 madvise; runtime/mgcscavenge.go; runtime/mheap.go, runtime/sizeclasses.go, runtime/malloc.go | — (не перепроверено) |
| 19.14 | Medium | Стек overflow | «fatal error: goroutine stack exceeds 1GB»; «через mmap» | точный вывод: «runtime: goroutine stack exceeds 1000000000-byte limit» + «fatal error: stack overflow»; не восстановим recover; стек — не mmap | man 2 mmap; mm/mmap.c; Documentation/mm/; runtime/stack.go, runtime/proc.go (maxstacksize) | — (не перепроверено) |
| 19.15 | Medium | Итог | «стек горутины защищён guard page» | у горутин нет guard page: защита — пролог (stackguard); guard page — у OS-потоков | runtime/stack.go, runtime/proc.go (maxstacksize) | — (не перепроверено) |
| 19.16 | Low | NULL page | «PROT_NONE 4–64 КБ» | область не отображена; граница задаётся vm.mmap_min_addr (4096/65536) | man 2 mmap; mm/mmap.c; Documentation/mm/ | — (не перепроверено) |
| 19.17 | Low | Стек | «непрерывные стеки появились в Go 1.4» | contiguous stacks — Go 1.3; 1.4 уменьшил минимум 8 КБ→2 КБ | исходники Go (runtime/net/os/syscall), release notes версии | — (не перепроверено) |
| 19.18 | Low | False sharing | «сбрасывают L1/L2 кэши друг друга» | инвалидируют строку (cache line), не кэши | golang.org/x/sys/cpu (CacheLinePad); Intel Optimization Manual | — (не перепроверено) |
| 19.19 | Low | write barriers | «переменная в куче порождает барьеры записи» | барьеры — при записи указателей в heap-объекты во время mark-фазы | man 5 elf; Documentation/arch/x86/x86_64/mm.rst | — (не перепроверено) |
| 19.20 | Low | Java | «brk/mmap гибридно» | HotSpot heap — mmap; brk только glibc malloc для нативной части | man 2 mmap; mm/mmap.c; Documentation/mm/; man 2 brk; runtime/mem_linux.go | — (не перепроверено) |
| 19.21 | Low | Диаграмма | — | Env/Stack: «0x7FFFFFFFFFFF» метка; heap «brk» для Go неприменимо — раздел C-центричен; нет vDSO/vvar, vsyscall, thread stacks | man 7 vdso; runtime/vdso_linux.go; man 2 brk; runtime/mem_linux.go | — (не перепроверено) |

### Статья 20. Стек вызовов и стек кадра функции

| № | Приор. | Раздел | Утверждение | Проблема / что проверить | Источник | Статус |
|---|:---:|---|---|---|---|---|
| 20.1 | High | §3, таблица, Interview, Итог 4 | «Go по умолчанию -fomit-frame-pointer / frame pointer отключён; включается GOEXPERIMENT=framepointer»; «заголовок stkblk» | на amd64/arm64 Go сохраняет RBP/FP по умолчанию с Go 1.7; GOEXPERIMENT=framepointer давно неактуален; `-fomit-frame-pointer` — флаг GCC, не Go; `stkblk` не существует; Go 1.21+ использует FP-unwinding в execution tracer | Go 1.7 release notes; runtime/traceback | ✔ src |
| 20.2 | Medium | §1,4,Итоги | «Go использует сегментированный стек (split stacks)» / «динамический сегментированный стек» | с Go 1.3 стеки непрерывные (copying), split stacks (hot split problem) убраны; ст.21 повторяет путаницу | man 5 elf; Documentation/arch/x86/x86_64/mm.rst | — (не перепроверено) |
| 20.3 | Medium | §2 | — | не сказано: ABIInternal Go (1.17+) без callee-saved регистров, регистры передачи (RAX,RBX,RCX,RDI,RSI,R8–R11); регистр g (R14) и R15 с зарезервированной ролью | runtime/runtime2.go (gobuf); cmd/compile/abi-internal.md; cmd/compile/abi-internal.md; go.dev/doc/asm | — (не перепроверено) |
| 20.4 | Medium | ASM-листинг | `SUBQ $16, RSP … ADDQ …` | Go-ассемблер использует SP/pseudo-SP, пролог `PUSHQ BP; MOVQ SP,BP; SUBQ`; листинг смешивает Intel и Go-синтаксис | cmd/compile/abi-internal.md; go.dev/doc/asm; runtime/os_linux.go (newosproc, cloneFlags) | — (не перепроверено) |
| 20.5 | Medium | Mechanical | «каждый SUBQ/ADDQ — запись в L1/L2» | это операции над регистром, обращения к кэшу нет; call/ret — не «переключение контекста» | cmd/compile/abi-internal.md; go.dev/doc/asm | — (не перепроверено) |
| 20.6 | Medium | Escape-пример | вывод `-m`: «main.heapEscape: leaking params: buffer to heap» | для локальной переменной выводится «moved to heap: buffer»; `leaking param` — про параметры; комментарий «stackLocal НЕ вызывает эскейп-анализ» неверен (анализ выполняется всегда) | cmd/compile escape analysis; go build -gcflags=-m | — (не перепроверено) |
| 20.7 | Medium | Gotcha | «fatal error: stack overflow — контролируемое завершение через panic» | это fatal error (runtime.throw), не panic: recover не поможет; ст.21 называет это то «panic», то «SIGSEGV, перехваченный рантаймом» — противоречие | runtime/panic.go; runtime/extern.go (GOTRACEBACK) | — (не перепроверено) |
| 20.8 | Low | §2 | «Padding для кэш-линий (обычно 16 байт)» | 16 Б — выравнивание стека по ABI; кэш-линия 64 Б | Intel SDM / AMD APM, Optimization Manual | — (не перепроверено) |
| 20.9 | Low | Под капотом | переменные «в регистры (RAX, RSP, RBP)» | RSP/RBP не используются под локальные | runtime/runtime2.go (gobuf); cmd/compile/abi-internal.md | — (не перепроверено) |
| 20.10 | Low | планировщик | «если места не хватает, планировщик выделяет новый блок» | делает runtime.newstack (по morestack), не планировщик | runtime/stack.go, runtime/proc.go (maxstacksize) | — (не перепроверено) |

### Статья 21. Переполнение стека и защита памяти

| № | Приор. | Раздел | Утверждение | Проблема / что проверить | Источник | Статус |
|---|:---:|---|---|---|---|---|
| 21.1 | High | omission | — | Статья «Переполнение стека и защита памяти» не раскрывает защиту: stack canaries (-fstack-protector), NX/W^X, ASLR/PIE, RELRO, CET/shadow stack, stack clash (-fstack-clash-protection); ст.20 обещает «guard pages, ASLR», ASLR отсутствует; нет Go-аспектов (bounds checks, unsafe, cgo) | GCC -fstack-protector/-fstack-clash-protection; CVE-2017-1000364 | — (не перепроверено) |
| 21.2 | High | newstack | «аллоцирует через mmap; вызывает madvise(MADV_DONTNEED) на старом стеке — критически важный шаг» | stackalloc берёт из stackpool/stackLarge/mheap (allocManual); старый стек возвращается stackfree в пул/кучу; madvise при росте стека не вызывается (память вернёт scavenger); ложен и совет strace…grep dontneed, Interview, Итог 3 | man 2 mmap; mm/mmap.c; Documentation/mm/; man 2 madvise; runtime/mgcscavenge.go | — (не перепроверено) |
| 21.3 | High | Лимит стека | «лимит стека в Go — лимит виртуальной памяти (ulimit -v); в таблице Go: ulimit -v» | лимит — runtime maxstacksize (1 ГБ на 64-bit, 250 МБ на 32-bit), настраивается debug.SetMaxStack; RLIMIT_AS тут второстепенен | man 2 getrlimit; syscall/rlimit.go | ✔ src |
| 21.4 | High | «stack overflow: это SIGSEGV, перехваченный рантаймом» | — | stack overflow детектится в newstack (newsize > maxstacksize → throw), без сигнала; вывод «runtime: goroutine stack exceeds 1000000000-byte limit» + «fatal error: stack overflow» | man 7 signal; os/signal doc; runtime/signal_unix.go | ✔ src |
| 21.5 | High | Gotcha 100 МБ | `buf := make([]byte, 100<<20)` «в стеке»; лечится тем же `make`; `defer free(buf)` | make >64 КБ всегда в куче (пример и «лечение» идентичны); `free` в Go нет; `var arr [100<<20]byte` (>10 МБ, maxStackVarSize) тоже уезжает в кучу | man 5 elf; Documentation/arch/x86/x86_64/mm.rst | — (не перепроверено) |
| 21.6 | High | pprof | `go tool pprof -top http://host/debug/pprof/stack` | эндпоинта /debug/pprof/stack нет (есть goroutine?debug=2, `stack` — не профиль); размер стека по горутинам pprof не показывает (MemStats.StackInuse, runtime/metrics /memory/classes/heap/stacks:bytes) | net/http/pprof/pprof.go; runtime/pprof | ✔ src |
| 21.7 | High | //go:nosplit | «идиоматичный паттерн защиты от рекурсии; компилятор не вызывает newstack; упадёт SIGSEGV» | nosplit убирает проверку пролога; линкер проверяет цепочки nosplit на помещаемость в StackLimit и отклоняет рекурсию («nosplit stack overflow»); это не защита и не «идиоматично» вне runtime | runtime/stack.go, runtime/proc.go (maxstacksize); man 7 signal; os/signal doc; runtime/signal_unix.go | — (не перепроверено) |
| 21.8 | Medium | Guard page | «ядро выделяет guard page PROT_NONE на краю стека процесса» | у главного потока Linux нет guard page — используется stack guard gap (stack_guard_gap, 256 стр.=1 МиБ, с 4.12) при расширении VMA; guard page PROT_NONE — у pthread-стеков (glibc); у горутин нет вовсе | man 2 mmap; mm/mmap.c; Documentation/mm/; glibc symbol versioning docs; man 7 libc | — (не перепроверено) |
| 21.9 | Medium | omission | — | Stack Clash: большие кадры/alloca перепрыгивают guard page (CVE-2017-1000364) | GCC -fstack-protector/-fstack-clash-protection; CVE-2017-1000364; man 5 elf; Documentation/arch/x86/x86_64/mm.rst | — (не перепроверено) |
| 21.10 | Medium | Рост стека | «Split Stacks … с Go 1.4 непрерывные» | непрерывные — Go 1.3 | man 5 elf; Documentation/arch/x86/x86_64/mm.rst | — (не перепроверено) |
| 21.11 | Medium | пролог | «проверка gostacksplit; порог ~8 КБ» | символа gostacksplit нет; пролог сравнивает SP со stackguard0 = stack.lo + StackGuard (≈928 Б, ×multiplier), плюс StackSmall=128 для маленьких кадров | runtime/stack.go, runtime/proc.go (maxstacksize); man 5 elf; Documentation/arch/x86/x86_64/mm.rst | ✔ src |
| 21.12 | Low | page fault | «PTE с флагом PROT_NONE» | PROT_NONE — свойство VMA; PTE при этом Present=0; MAPERR vs ACCERR | Documentation/admin-guide/mm/; man 2 getrusage (ru_majflt); arch/x86/include/asm/pgtable.h; mm/memory.c | — (не перепроверено) |
| 21.13 | Low | g.stackguard1 | «предотвращает рекурсивные newstack» | stackguard1 — порог для проверок на системном стеке (g0/gsignal), не защита от рекурсии newstack | runtime/stack.go, runtime/proc.go (maxstacksize) | — (не перепроверено) |
| 21.14 | Low | `gostartcall` | «восстанавливает контекст» | gostartcall — инъекция вызова для sigpanic/asyncPreempt; возврат — gogo(&gp.sched) | runtime/panic.go; runtime/extern.go (GOTRACEBACK) | ✔ src |
| 21.15 | Low | Таблица | PHP: «8 МБ, Segmentation fault» | PHP 8.3+ zend.max_allowed_stack_size даёт Error вместо segfault | JEP 444 (virtual threads), JDK/Python/PHP release notes | — (не перепроверено) |
| 21.16 | Low | «LimitAS/MemoryMax» как лимит стека | — | MemoryMax не ограничивает стек отдельно | первоисточник по теме (спецификация/документация) | — (не перепроверено) |

### Статья 22. Системные вызовы. Как программа просит ОС что-то сделать

| № | Приор. | Раздел | Утверждение | Проблема / что проверить | Источник | Статус |
|---|:---:|---|---|---|---|---|
| 22.1 | Medium | Инструкции | «SYSCALL прыгает по адресам в IDT (MSR IA32_LSTAR)» | SYSCALL использует только MSR LSTAR, IDT не задействован (IDT — для INT/exception) | Intel SDM (SYSCALL/SYSRET); arch/x86/entry/entry_64.S | — (не перепроверено) |
| 22.2 | Medium | Диаграмма/текст | «CPU переключает стек на Kernel Stack», «сброс предсказателя и кэшей», «контекстное переключение, сохранение дескрипторов сегментов» | SYSCALL не меняет RSP (swapgs + загрузка kernel RSP делает entry_SYSCALL_64); кэши/предиктор не инвалидируются; ctx switch нет (повтор [2]) | man 2 open/fcntl; os/file_unix.go; man 5 elf; Documentation/arch/x86/x86_64/mm.rst | — (не перепроверено) |
| 22.3 | Medium | handoff | «sysmon отбирает P, если M в syscall > ~10 мс» | retake в sysmon: P в syscall ≥1 тика (≥20 мкс) И (runq не пуст ИЛИ нет idle P/spinning M ИЛИ прошло ≥10 мс) (✔ runtime/proc.go retake, Go 1.27.1; статус _Psyscall в новых версиях удалён, #64318); «P отвязывается» — не сразу, а по retake | runtime/proc.go (sysmon, retake, handoffp); runtime/os_linux.go (newosproc, cloneFlags) | ✔ src |
| 22.4 | Medium | CGO | «каждый переход в CGO — это отдельный syscall и контекстный переход» | cgo-вызов не syscall: ≈40–60 нс накладных (entersyscall/exitsyscall + смена стека на g0), без входа в ядро | Go issue / bench | — (не перепроверено) |
| 22.5 | Medium | Таблица, futex | «futex … позволяет мьютексам и каналам работать в user-space» | sync.Mutex/каналы паркуют горутины в рантайме; futex — для M внутри runtime (см. [3]) | man 2 futex; runtime/lock_futex.go, sync/mutex.go; runtime/chan.go | — (не перепроверено) |
| 22.6 | Medium | Оптимизации | «TCP_NODELAY» как оптимизация | Go net включает TCP_NODELAY по умолчанию для TCPConn; | net/sockopt_linux.go, net/tcpsock.go; man 7 tcp/socket | — (не перепроверено) |
| 22.7 | Low | TLB shootdown | «если syscall меняет таблицу страниц (mmap/brk)» | shootdown нужен при unmap/mprotect/madvise, а не при создании нового отображения | Intel SDM Vol.3 §4.10 (TLB); Documentation/arch/x86/tlb.rst; man 2 mmap; mm/mmap.c; Documentation/mm/ | — (не перепроверено) |
| 22.8 | Low | «99% времени уходит на сброс конвейера» | — | гипербола; реальная доля — mitigations+entry, но и Go File.Write — ещё poll.FD lock, | man 2 select/poll; fs/select.c | — (не перепроверено) |
| 22.9 | Low | io_uring | — | не упомянуты seccomp-ограничения (Docker ≥25 default seccomp, GKE/ChromeOS отключают), vDSO, x/sys/unix; статья 21 обещала «почему syscall в Go — не просто syscall.Syscall» — не раскрыто | man 7 vdso; runtime/vdso_linux.go; Documentation/admin-guide/LSM/; SELinux/AppArmor docs; Docker seccomp/AppArmor docs | — (не перепроверено) |

### Статья 23. Основные системные вызовы Linux для бэкенд-разработчика

| № | Приор. | Раздел | Утверждение | Проблема / что проверить | Источник | Статус |
|---|:---:|---|---|---|---|---|
| 23.1 | High | Внутреннее противоречие | §2: «futex — на нём построены sync.Mutex, RWMutex и каналы»; Interview Q3: «Если занято, вызывается futex(FUTEX_WAIT), ядро усыпляет горутину» | тот же текст ниже верно говорит: sync.Mutex slow path = gopark без futex; futex — только для M (notesleep/runtime.mutex); каналы тоже без futex (противоречие и со ст.3/22) | man 2 futex; runtime/lock_futex.go, sync/mutex.go; sync/mutex.go, sync/rwmutex.go, runtime/sema.go | — (не перепроверено) |
| 23.2 | High | Под капотом | «Аргументы: R10 (1-й), R8 (2-й), R9 (3-й), номер в RAX» | неверно: RDI, RSI, RDX, R10, R8, R9 (ст.2 и ст.22 дают верный порядок) | первоисточник по теме (спецификация/документация) | — (не перепроверено) |
| 23.3 | Medium | netpoll | «ядро возвращает управление горутине» / Interview: «runtime вызывает epoll_wait при попытке чтения» | read → EAGAIN → gopark на pollDesc; epoll_wait вызывает планировщик (findRunnable/netpoll), затем готовит горутины; регистрация fd в epoll — один раз при создании (edge-triggered) | runtime/netpoll.go, netpoll_epoll.go; man 7 epoll | — (не перепроверено) |
| 23.4 | Medium | Стоимость syscall | «1000–5000 тактов, очистка TLB» | ещё одно число (ст.2: 100–500 нс; ст.5: 50–100 нс; ст.22: 200–5000) | Intel SDM Vol.3 §4.10 (TLB); Documentation/arch/x86/tlb.rst | — (не перепроверено) |
| 23.5 | Low | пути | `src/runtime/sys_linux_amd64.go` | файла нет (sys_linux_amd64.s — ассемблер; номера — syscall/zsysnum_linux_amd64.go; runtime использует свои константы в sys_linux_amd64.s); значения номеров (291, 56, 202, 9, 228) верны | cmd/compile/abi-internal.md; go.dev/doc/asm | — (не перепроверено) |
| 23.6 | Low | «clone (аналог fork в Go)» | — | в Go нет fork; clone — база для M и ForkExec | kernel/fork.c; man 2 clone/execve/wait; runtime/os_linux.go (newosproc, cloneFlags) | — (не перепроверено) |
| 23.7 | Low | set_tid_address/set_robust_list | «автоматическая разблокировка мьютексов при падении потока» | set_tid_address — для CLONE_CHILD_CLEARTID (join потока); robust list — для robust pthread-мьютексов (glibc); Go-рантайм их не использует для sync.Mutex | sync/mutex.go, sync/rwmutex.go, runtime/sema.go; glibc symbol versioning docs; man 7 libc | — (не перепроверено) |
| 23.8 | Low | timerfd | — | Go-таймеры не используют timerfd (таймаут epoll_wait/futex; netpoll deadlines) | man 2 futex; runtime/lock_futex.go, sync/mutex.go; runtime/netpoll.go, netpoll_epoll.go; man 7 epoll | — (не перепроверено) |
| 23.9 | Low | Диаграмма Mutex | «Захвачен за 1 такт» | LOCK CMPXCHG ≈ 18–25 тактов без contention | Intel SDM / AMD APM, Optimization Manual; воспроизводимое измерение (lmbench/perf/fio) или публикация с методикой | — (не перепроверено) |
| 23.10 | Low | заголовок «Эпюл (epoll)» | — | опечатка/транслитерация | runtime/netpoll.go, netpoll_epoll.go; man 7 epoll | — (не перепроверено) |
| 23.11 | Low | sendfile | — | не сказано, что Go делает это сам: io.Copy(*net.TCPConn, *os.File) → sendfile/splice (TCPConn.ReadFrom; WriteTo с 1.22), http.ServeContent/FileServer | man 2 sendfile/splice; net/tcpsock_posix.go (ReadFrom) | — (не перепроверено) |
| 23.12 | Low | диагностика | `strace -e trace=read,write,epoll_wait … go run main.go` | без -f не увидит потоки и дочерний бинарник; на linux/amd64 рантайм вызывает epoll_pwait (ст.24 использует его) — проверить; «epoll_wait >80% = ждёт IO» — наивно: -c считает system time, не wall (нужен -w) | runtime/netpoll.go, netpoll_epoll.go; man 7 epoll; man 2 ptrace; strace(1) | ⚠ проверить |

### Статья 24. strace, ltrace и чтение поведения процесса

| № | Приор. | Раздел | Утверждение | Проблема / что проверить | Источник | Статус |
|---|:---:|---|---|---|---|---|
| 24.1 | High | ltrace принцип | «не требует ptrace и работает в user-space»; «перехватывает mmap/mprotect в ld.so»; «заменяет адреса .rela.plt trampolines»; «LD_PRELOAD — механизм ltrace» | ltrace использует ptrace + breakpoints (int3) на PLT (сам Interview ниже говорит это); LD_PRELOAD не использует; «конфликт с аллокатором Go (mmap+sbrk-эмуляция)» — бессмысленно | man 2 mmap; mm/mmap.c; Documentation/mm/; man 2 ptrace; strace(1) | — (не перепроверено) |
| 24.2 | High | Диагностика | «futex(FUTEX_WAIT) → захвачен sync.Mutex или channel»; «epoll_pwait(-1) → баг netpoller» | в Go futex-wait — норма для простаивающих M; sync.Mutex/каналы futex не используют (противоречит ст.23); epoll_pwait(-1) на неактивном сервисе — норма; | man 2 futex; runtime/lock_futex.go, sync/mutex.go; sync/mutex.go, sync/rwmutex.go, runtime/sema.go | — (не перепроверено) |
| 24.3 | Medium | Флаги | «-f — отслеживать fork/exec дочерних процессов (критично для Go)» | -f следует и за потоками (clone); критично для Go именно из-за M-потоков | kernel/fork.c; man 2 clone/execve/wait | — (не перепроверено) |
| 24.4 | Medium | ptrace | «PTRACE_ATTACH, SIGSTOP» | современный strace -p использует PTRACE_SEIZE (без SIGSTOP); syscall-stop = SIGTRAP\|0x80 с TRACESYSGOOD; | man 2 ptrace; strace(1) | — (не перепроверено) |
| 24.5 | Medium | Оверхед | «два контекстных переключения… ×10–50» | на каждый syscall 2 остановки (entry+exit), каждая — переключения в трейсер и обратно; замедление до 100× (Gregg); не упомянут `strace --seccomp-bpf` (≥5.3, -f) | Documentation/admin-guide/LSM/; SELinux/AppArmor docs; Docker seccomp/AppArmor docs; man 2 ptrace; strace(1) | — (не перепроверено) |
| 24.6 | Medium | Go и libc | «Go статически линкует libc»; «-linkmode=external или встроенные» | Go вообще не линкует libc без cgo; internal vs external linkmode — иное; | исходники Go (runtime/net/os/syscall), release notes версии | — (не перепроверено) |
| 24.7 | Medium | recvfrom(0, …) | — | Go TCP читает через read/write; recvfrom — для UDP; fd 0 = stdin | исходники Go (runtime/net/os/syscall), release notes версии; исходники и Documentation/ ядра, man-страницы (man 2/7) | — (не перепроверено) |
| 24.8 | Medium | -c epoll_pwait | «проверьте, не переключает ли Go слишком много горутин» | не связано; -c показывает system time | runtime/netpoll.go, netpoll_epoll.go; man 7 epoll | — (не перепроверено) |
| 24.9 | Medium | Альтернативы | «gdb -p … info goroutines» после «gdb на проде — верный способ уронить» | противоречие; `info goroutines` требует runtime-gdb.py (deprecated); правильнее SIGQUIT/pprof goroutine?debug=2/dlv/runtime/trace | net/http/pprof/pprof.go; runtime/pprof; man 7 signal; os/signal doc; runtime/signal_unix.go | — (не перепроверено) |
| 24.10 | Medium | omission | — | ptrace_scope (Yama=1) и CAP_SYS_PTRACE/seccomp в контейнерах; шум SIGURG (async preemption) и nanosleep/usleep от sysmon в Go-стрейсе; `strace -k`, `-yy`, `-tt`, `perf trace`, `bpftrace` | runtime/proc.go (sysmon, retake, handoffp); man 7 capabilities; syscall.SysProcAttr | — (не перепроверено) |
| 24.11 | Low | -T | «в микросекундах» | выводится в секундах `<0.000045>` | первоисточник по теме (спецификация/документация) | — (не перепроверено) |
| 24.12 | Low | TIME_WAIT | «ECONNREFUSED/ETIMEDOUT → TIME_WAIT/CLOSE_WAIT» | TIME_WAIT-исчерпание даёт EADDRNOTAVAIL; CLOSE_WAIT — утечка fd, не ECONNREFUSED | RFC 9293; Documentation/networking/ip-sysctl.rst; include/net/tcp.h | — (не перепроверено) |

### Статья 25. Файловые дескрипторы. Все в Linux является файлом

| № | Приор. | Раздел | Утверждение | Проблема / что проверить | Источник | Статус |
|---|:---:|---|---|---|---|---|
| 25.1 | High | Код NewFile | `rawFD := int32(42); os.NewFile(rawFD, …)` | сигнатура NewFile(fd uintptr, name string) — не компилируется | go build / go vet на листинге | ✔ src |
| 25.2 | High | os.File vs net.Conn | «os.File оптимизирован с буферизацией»; «net.Conn реализует io.ReaderAt и WriterTo, если FD поддерживает sendfile/splice»; «syscall используется в netpoller» | os.File не буферизован; net.Conn — интерфейс без ReaderAt; *TCPConn реализует io.ReaderFrom (sendfile/splice) и WriterTo (с 1.22); netpoller — внутри runtime, не пакет syscall | runtime/netpoll.go, netpoll_epoll.go; man 7 epoll; man 2 sendfile/splice; net/tcpsock_posix.go (ReadFrom) | — (не перепроверено) |
| 25.3 | Medium | Таблица FD | «O(1) или O(log N); bitmaps или RB-деревья» | в Linux fdtable — массив + bitmaps (open_fds/full_fds_bits), RB-деревьев нет; расширение через expand_files | fs/file.c | — (не перепроверено) |
| 25.4 | Medium | O_CLOEXEC | «В Go 1.11+ большинство функций os и net ставят автоматически»; «проверяйте, поддерживает ли драйвер» | os/net ставят O_CLOEXEC/SOCK_CLOEXEC на Linux существенно раньше (≈Go 1.4–1.5 для os.Open; ForkLock-обходы раньше); «драйвер поддерживает флаг» — не имеет смысла | man 2 open/fcntl; os/file_unix.go | — (не перепроверено) |
| 25.5 | Medium | GC и fd | «GC не спасает от утечек FD» | у *os.File есть finalizer (закрывает fd при GC), net.FD тоже; недетерминированно — но утверждение неполно | runtime/mgc.go; go.dev/doc/gc-guide | — (не перепроверено) |
| 25.6 | Medium | Gotcha ulimit | «мониторьте go sysfs и go goroutines» | «go sysfs» не существует; мониторить /proc/PID/fd, process_open_fds; не упомянуто: Go 1.19+ сам поднимает soft NOFILE до hard; дефолт LimitNOFILE у containerd/docker часто 1048576/infinity | man 2 getrlimit; syscall/rlimit.go | ✔ src |
| 25.7 | Low | Эпиграф | — | цитата-пересказ Томпсона/Ритчи без источника | оригинальный источник цитаты | — (не перепроверено) |
| 25.8 | Low | «Всё есть файл» | сетевые интерфейсы/сокеты не имеют пути; нет eventfd/timerfd/signalfd/pidfd, dup/dup2, SCM_RIGHTS, FD_SETSIZE=1024 | пропуски | man 2 select/poll; fs/select.c; man 7 unix; net/unixsock*.go | — (не перепроверено) |
| 25.9 | Low | Под капотом | «os и syscall работают с struct file» | struct file — внутри ядра; Go хранит int fd (poll.FD, netFD) | man 2 select/poll; fs/select.c | — (не перепроверено) |
| 25.10 | Low | Interview | — | про panic/defer: unrecovered panic выполняет defer в панике горутины; ядро закрывает fd при любом завершении ✓; «Go не гарантирует defer при SIGKILL» ✓ | man 7 signal; os/signal doc; runtime/signal_unix.go; runtime/panic.go; runtime/extern.go (GOTRACEBACK) | — (не перепроверено) |
| 25.11 | Low | Mechanical | «os.File может стать узким местом по сравнению с raw syscall» | накладные poll.FD ≈ десятки нс; утверждение вводит в заблуждение | man 2 select/poll; fs/select.c | — (не перепроверено) |
| 25.12 | Low | память FD | «~1–2 КБ на struct file+inode» | struct file ≈256 Б; inode общий; сокет — единицы КБ (struct sock+буферы) | Documentation/filesystems/vfs.rst; fs/dcache.c | — (не перепроверено) |

### Статья 26. Pipe, Named Pipe и перенаправление потоков

| № | Приор. | Раздел | Утверждение | Проблема / что проверить | Источник | Статус |
|---|:---:|---|---|---|---|---|
| 26.1 | High | Код Pipe2 | `fds, err := syscall.Pipe2([]int{0,1}, O_CLOEXEC)` | сигнатура Pipe2(p []int, flags int) error — возвращает только error, заполняет p; код не компилируется | man 2 open/fcntl; os/file_unix.go | ✔ src |
| 26.2 | High | «Production-ready» runWithPipe | `cmd.Start()`; `go io.Copy(&sb, stdoutPipe)`; затем СРАЗУ `cmd.Wait()` | документация StdoutPipe: «Wait закроет pipe после завершения процесса; неверно вызывать Wait до завершения всех чтений» — гонка: Wait может закрыть read-end до того, как io.Copy дочитает → потеря вывода/ошибка "file already closed"; «io.Copy закрывает пайп» — неверно; диаграмма (Wait после EOF) противоречит коду; ниже Interview п.4 говорит правильно (Wait после чтения) | os/exec docs; man 2 wait | ✔ src |
| 26.3 | Medium | dup2 | «Всегда используйте O_CLOEXEC при дублировании дескрипторов» | dup2 не наследует FD_CLOEXEC (флаг на дескрипторе, не на open file description) — для stdio перед exec нужен именно сброшенный CLOEXEC (dup3) | man 7 pipe; os/exec docs (StdoutPipe); man 2 open/fcntl; os/file_unix.go | — (не перепроверено) |
| 26.4 | Medium | Текст | «в Go нет аналога popen/subprocess.Popen» | os/exec (Cmd.StdoutPipe/StdinPipe) и есть аналог | os/exec/exec.go; syscall/exec_linux.go | ✔ src |
| 26.5 | Medium | cmd.Output | «нельзя в production: fatal error out of memory или deadlock; всегда используйте io.Pipe» | Output не даёт deadlock (параллельно читает сам); риск — неограниченный буфер; io.Pipe — in-memory синхронный pipe, не решение; правильно: StdoutPipe+Scanner/лимитирование/запись в файл | sync/mutex.go; Documentation/locking/ | ✔ src |
| 26.6 | Low | Введение | «gRPC/net.Conn — мы по сути оперируем пайпами» | сокеты ≠ пайпы | исходники Go (runtime/net/os/syscall), release notes версии; исходники и Documentation/ ядра, man-страницы (man 2/7) | — (не перепроверено) |
| 26.7 | Low | omission | — | pipe-max-size (1 МиБ), F_SETPIPE_SZ, лимиты pipe-user-pages-soft, vmsplice/splice/tee; pipe vs socketpair; packet mode (O_DIRECT) | man 2 sendfile/splice; net/tcpsock_posix.go (ReadFrom); man 2 open (O_DIRECT); statx(2) | — (не перепроверено) |
| 26.8 | Low | FIFO | пример с O_NONBLOCK: «os.Open может заблокировать навсегда» | с O_NONBLOCK open(O_RDONLY) не блокируется (O_WRONLY без читателя → ENXIO); чтение без писателей даёт EOF — нюанс не описан | man 7 pipe; os/exec docs (StdoutPipe) | — (не перепроверено) |
| 26.9 | Low | Диаграмма dup2 | «ядро объединяет filp структуры» | никакого слияния: оба fd указывают на один struct file | man 7 pipe; os/exec docs (StdoutPipe) | — (не перепроверено) |
| 26.10 | Low | omission | — | родитель должен закрыть свою копию write-end, иначе EOF не придёт (os/exec делает сам); SIGPIPE/EPIPE при записи в закрытый pipe | man 7 signal; os/signal doc; runtime/signal_unix.go; man 7 pipe; os/exec docs (StdoutPipe) | — (не перепроверено) |

### Статья 27. Unix Domain Socket

| № | Приор. | Раздел | Утверждение | Проблема / что проверить | Источник | Статус |
|---|:---:|---|---|---|---|---|
| 27.1 | High | Типы | «SOCK_DGRAM (UDS) ненадёжный: могут теряться/приходить вне порядка» | AF_UNIX SOCK_DGRAM в Linux надёжен и сохраняет порядок (отправитель блокируется/EAGAIN при полной очереди; нет потерь) | man 7 unix | — (не перепроверено) |
| 27.2 | High | Код FD passing | `unix.Mmsghdr{Hdr: unix.Mhdr{Control: unix.Cmsghdr{…}}}`, `unix.Sendmmsg(listenerFD, …)`, `int(fd)` от *os.File | не компилируется (Control — []byte/*byte, Sendmmsg не для SCM_RIGHTS, fd ≠ int, отправка в listener-fd); корректно: unix.Sendmsg(fd, data, unix.UnixRights(fd), nil, 0) или (*net.UnixConn).WriteMsgUnix + ParseUnixRights | man 7 unix; net/unixsock*.go; go build / go vet на листинге | — (не перепроверено) |
| 27.3 | Medium | Производительность | «TCP loopback: проверка контрольных сумм, ARP, маршрутизация…» | на lo checksum не вычисляется/не проверяется (CHECKSUM_PARTIAL/UNNECESSARY), ARP не нужен; «+20–40% / −10–30%» без источника (бенчмарки Redis/Postgres обычно дают от +30% до ×2) | Documentation/networking/napi.rst, skbuff.rst | — (не перепроверено) |
| 27.4 | Medium | Gotcha abstract | «Go поддерживает абстрактные сокеты только с \x00; нестабильно из-за SOCK_MAX_ADDR и libc» | Go принимает имя с «@» (и ведущий NUL); `SOCK_MAX_ADDR` не существует, libc в Go нет — утверждение выдумано | net/unixsock_posix.go; man 7 unix | — (не перепроверено) |
| 27.5 | Medium | Права | «абстрактные сокеты доступны всем процессам с доступом к ядру» | область — network namespace; проверок прав нет (любой процесс в netns подключится); для аутентификации — SO_PEERCRED; в статье нет | man 7 namespaces; man 2 pivot_root | — (не перепроверено) |
| 27.6 | Low | Namespaces | «struct unix_inode_info» | такой структуры нет | Documentation/filesystems/vfs.rst; fs/dcache.c | — (не перепроверено) |
| 27.7 | Low | Под капотом | «unix_sendpage + splice → zero copy» | sendpage удалён в 6.5 (MSG_SPLICE_PAGES); утверждение устарело/неточно | man 2 sendfile/splice; net/tcpsock_posix.go (ReadFrom) | — (не перепроверено) |
| 27.8 | Low | Go-сервер | `defer os.Remove(path)` | net.UnixListener по умолчанию unlink'ит файл при Close() (SetUnlinkOnClose); os.Remove перед Listen опасен (удалит живой сокет другого инстанса); os.Stat перед Dial — лишний/гоночный | net/unixsock_posix.go; man 7 unix | — (не перепроверено) |
| 27.9 | Low | FD passing | «Docker передаёт stdin/stdout» | реальный пример — runc --console-socket (SCM_RIGHTS pty master), systemd socket activation; не упомянут GC in-flight fd | man 2 prctl (PR_SET_CHILD_SUBREAPER); Docker/containerd docs | — (не перепроверено) |
| 27.10 | Low | Таблица | Pipes «Half-duplex (обычно)» | всегда однонаправленные; SHM «надёжность ❌» — некорректная колонка | runtime/os_linux.go (newosproc, cloneFlags) | — (не перепроверено) |
| 27.11 | Low | omission | — | SOCK_SEQPACKET («unixpacket» в Go), SO_PEERCRED/SCM_CREDENTIALS, systemd LISTEN_FDS, k8s device-plugin/CSI через UDS | man systemd.service, sd_listen_fds(3), sd_notify(3); man 7 unix; net/unixsock*.go | — (не перепроверено) |

### Статья 28. Сигналы в Linux

| № | Приор. | Раздел | Утверждение | Проблема / что проверить | Источник | Статус |
|---|:---:|---|---|---|---|---|
| 28.1 | High | os/signal механизм | «runtime блокирует сигналы через rt_sigprocmask на всех потоках кроме основного; горутина блокируется в sigwaitinfo» | Go устанавливает rt_sigaction-обработчики на все потоки (sigtramp→sighandler→sigsend), сигналы не блокируются; os/signal.loop ждёт на signal_recv (note/futex), не sigwaitinfo | runtime/sigqueue.go | ✔ src |
| 28.2 | High | NotifyContext | «Go 1.15+» | добавлен в Go 1.16 | исходники Go (runtime/net/os/syscall), release notes версии | ✔ src |
| 28.3 | Medium | Доставка | «ищет целевой тред по PID/TID»; «sigmask — игнорируются» | kill(pid) — process-directed: ядро выбирает ЛЮБОЙ поток без блокировки сигнала (shared_pending); blocked ≠ ignored (остаётся pending); для Go (много потоков) критично | man 7 signal; os/signal doc; runtime/signal_unix.go | — (не перепроверено) |
| 28.4 | Medium | SIGPIPE | «в Go по умолчанию игнорируется; net/os/io игнорируют; с raw socket/CGO падение гарантировано» | Go ставит обработчик: запись в закрытый pipe на fd 1/2 завершает программу по SIGPIPE; на остальных fd — EPIPE; при cgo тоже EPIPE (обработчик Go установлен) | os/signal doc «SIGPIPE» | — (не перепроверено) |
| 28.5 | Medium | K8s | «зависает или падает через 10 секунд»; «liveness → SIGKILL» | default terminationGracePeriodSeconds = 30; liveness-kill тоже сначала SIGTERM; не упомянуты: SIGTERM получает только PID 1 (sh -c не форвардит), preStop/endpoint-removal race | man 7 signal; os/signal doc; runtime/signal_unix.go; Kubernetes docs (kubelet, QoS, CPU Manager) | — (не перепроверено) |
| 28.6 | Medium | os/signal | «Channel по умолчанию имеет буфер 1» | канал создаёт вызывающий; требуется буферизованный (≥1); отправка non-blocking → потеря при переполнении ✓ | runtime/chan.go | — (не перепроверено) |
| 28.7 | Medium | Python | «time.sleep блокирует доставку сигнала» | с PEP 475 (3.5) sleep прерывается, обработчик Python выполняется в главном потоке между байткод-инструкциями; задержка — только в C-коде без проверки сигналов | man 7 signal; os/signal doc; runtime/signal_unix.go; JEP 444 (virtual threads), JDK/Python/PHP release notes | — (не перепроверено) |
| 28.8 | Medium | omission | — | SIGQUIT → дамп горутин (GOTRACEBACK), SIGURG (async preemption 1.14+), SIGSEGV→panic, SIGPROF; PID 1 в контейнере и сигналы без обработчика | man 7 signal; os/signal doc; runtime/signal_unix.go; man 5 core; runtime/extern.go (GOTRACEBACK) | — (не перепроверено) |
| 28.9 | Low | Термин | «Thread Control Block» | в Linux task_struct | kernel/fork.c; man 2 clone/execve/wait | — (не перепроверено) |
| 28.10 | Low | Доставка | — | не упомянуты sigaltstack (Go обрабатывает на gsignal-стеке), SA_RESTART | исходники Go (runtime/net/os/syscall), release notes версии | — (не перепроверено) |
| 28.11 | Low | таблица | — | номера сигналов зависят от архитектуры (alpha/mips/sparc); «SIGKILL обрабатывается планировщиком» — неточно (get_signal) | man 7 signal; os/signal doc; runtime/signal_unix.go | — (не перепроверено) |
| 28.12 | Low | Гонка cleanup | пример `cleanup(wg)` | реальная ошибка — копирование WaitGroup по значению (vet copylocks) и Add внутри горутины; текст про «race» поверхностный | go vet copylocks; sync docs | — (не перепроверено) |
| 28.13 | Low | PHP | «CLI игнорирует большинство сигналов» | действуют дефолтные действия ОС; pcntl_signal для обработчиков | man 7 signal; os/signal doc; runtime/signal_unix.go; JEP 444 (virtual threads), JDK/Python/PHP release notes | — (не перепроверено) |

### Статья 29. Демоны и фоновые процессы

| № | Приор. | Раздел | Утверждение | Проблема / что проверить | Источник | Статус |
|---|:---:|---|---|---|---|---|
| 29.1 | High | Go: daemonize() | `syscall.ForkExec("/proc/self/exe", os.Args…)` без Setsid, без guard-переменной | потомок исполняет тот же код → бесконечный каскад самозапусков (fork-bomb); без SysProcAttr{Setsid:true} не отрывается от терминала; Printf с разрывом строки | os/exec/exec.go; syscall/exec_linux.go; man 5 proc; sysstat docs | ✔ src |
| 29.2 | High | Gotcha | «os/exec не умеет setsid()» | у syscall.SysProcAttr есть Setsid, Setpgid, Setctty, Noctty (exec.Command(...).SysProcAttr = &syscall.SysProcAttr{Setsid:true}) — утверждение неверно | os/exec/exec.go; syscall/exec_linux.go | ✔ src |
| 29.3 | High | sdnotify | импорт `github.com/coreos/go-systemd/v22/sdnotify`, `sdnotify.Ready()/Stopping()` | в go-systemd v22 пакет называется `daemon` (daemon.SdNotify; ст.30 использует его правильно); `sdnotify` — другой модуль (okzk/sdnotify) | man systemd.service, sd_listen_fds(3), sd_notify(3) | — (не перепроверено) |
| 29.4 | Medium | Код | `srv := http.NewServer()` | такой функции нет; внутри горутины shadow ctx | исходники Go (runtime/net/os/syscall), release notes версии; воспроизвести: go build / go vet | — (не перепроверено) |
| 29.5 | Medium | systemd | «Type=simple: считается запущенным после execve()» | simple — сразу после fork(); после exec — Type=exec (v240+) | kernel/fork.c; man 2 clone/execve/wait; man systemd.service, sd_listen_fds(3), sd_notify(3) | — (не перепроверено) |
| 29.6 | Medium | Interview | «Type=simple: приложение зависнет на старте → systemd пришлёт SIGKILL по таймауту» | для simple старт-таймаута нет (TimeoutStartSec — для notify/forking/oneshot/exec) | man 7 signal; os/signal doc; runtime/signal_unix.go; man systemd.service, sd_listen_fds(3), sd_notify(3) | — (не перепроверено) |
| 29.7 | Medium | Идиоматичный демон | Type=notify, но `sdnotify.Ready()` не вызывается; defer’ы не выполнятся после log.Fatalf | сервис зависнет в activating и будет убит по TimeoutStartSec | man systemd.service, sd_listen_fds(3), sd_notify(3) | — (не перепроверено) |
| 29.8 | Low | Классич. демонизация | «fork+exit предотвращает SIGHUP»; «после setsid процесс не может получить терминал»; umask(0) | SIGHUP предотвращает setsid, а не осиротение; лидер сессии МОЖЕТ получить CTTY при open без O_NOCTTY — поэтому второй fork (в списке его нет, на диаграмме есть); umask(0) — плохая практика (обычно 022/027) | kernel/fork.c; man 2 clone/execve/wait; man 7 signal; os/signal doc; runtime/signal_unix.go | — (не перепроверено) |
| 29.9 | Low | Итог 3 | «только одна горутина может слушать канал сигналов» | читать канал могут несколько горутин (каждый сигнал получит один); копию получает каждый канал, зарегистрированный в Notify | runtime/chan.go; man 7 signal; os/signal doc; runtime/signal_unix.go | — (не перепроверено) |
| 29.10 | Low | Gotcha | «Go 1.20+ NotifyContext» | NotifyContext — Go 1.16 (повтор [28]) | исходники Go (runtime/net/os/syscall), release notes версии | ✔ src |

### Статья 30. systemd. Управление сервисами в Linux

| № | Приор. | Раздел | Утверждение | Проблема / что проверить | Источник | Статус |
|---|:---:|---|---|---|---|---|
| 30.1 | High | Вступление | «systemd — PID 1 в RHEL, Ubuntu, Debian, Alpine-based images» | Alpine использует OpenRC (musl), в Alpine-контейнерах нет init вообще; в контейнерах systemd как PID 1 — исключение | man 7 signal; os/signal doc; runtime/signal_unix.go; man systemd.service, sd_listen_fds(3), sd_notify(3) | — (не перепроверено) |
| 30.2 | High | Socket activation (код) | `net.FileConn(os.NewFile(3,""))` для listen-сокета; LISTEN_PID не проверяется; «else … conn = net.Listen» (переменная названа conn); программа завершается без Serve | для listening-сокета нужен net.FileListener (FileConn — для соединений); без LISTEN_PID можно принять чужие fd; пример нерабочий; удобнее activation.Listeners() из go-systemd | man systemd.service, sd_listen_fds(3), sd_notify(3) | — (не перепроверено) |
| 30.3 | Medium | ExecReload / graceful | «systemd посылает SIGTERM при stop или reload»; «используйте SIGUSR1/SIGHUP … запускают graceful shutdown» | reload выполняет ExecReload (не SIGTERM); смысл reload — перечитать конфиг, не остановка | man 7 signal; os/signal doc; runtime/signal_unix.go; man systemd.service, sd_listen_fds(3), sd_notify(3) | — (не перепроверено) |
| 30.4 | Medium | Socket activation польза | «устраняет холодный старт: TCP-handshake и TLS 1–3 RTT» | активация не убирает handshake (ядро принимает SYN в backlog, TLS всё равно делает приложение); выгода — lazy start/параллельная загрузка и отсутствие потерь соединений при рестарте; «балансировка между инстансами» — при Accept=no несколько процессов могут принимать с одного сокета, не «балансировка systemd» | man 2 listen; Documentation/networking/ip-sysctl.rst; net/ipv4/tcp_input.c; man systemd.service, sd_listen_fds(3), sd_notify(3) | — (не перепроверено) |
| 30.5 | Medium | Под капотом | «LimitNOFILE/MemoryMax/CPUQuota применяются к cgroup … жёсткие» | LimitNOFILE — setrlimit процесса, не cgroup; MemoryHigh — мягкий; CPUQuota — throttling, не kill | man 2 getrlimit; syscall/rlimit.go; Documentation/admin-guide/cgroup-v2.rst | ✔ src |
| 30.6 | Medium | Под капотом | «clone с CLONE_NEWPID/NEWNS/NEWNET при ProtectSystem/ProtectHome/PrivateTmp» | эти опции используют mount-namespace (NEWNS); NEWNET — PrivateNetwork=, NEWPID — PrivatePIDs/ProcSubset; | man 7 namespaces; man 2 pivot_root; runtime/os_linux.go (newosproc, cloneFlags) | — (не перепроверено) |
| 30.7 | Medium | Interview LimitNOFILE | «systemd применяет до запуска на уровне ядра и cgroup; goroutines исчерпают лимит 1024» | rlimit, не cgroup; горутины fd не потребляют; Go ≥1.19 сам поднимает soft до hard; systemd default 1024:524288 (v240+) | man 2 getrlimit; syscall/rlimit.go; Documentation/admin-guide/cgroup-v2.rst | ✔ src |
| 30.8 | Medium | Watchdog | диаграмма: «горутины в дедлоке → watchdog срабатывает» | отдельная горутина-пингер продолжит слать WATCHDOG=1 даже при дедлоке бизнес-логики; нужна привязка пинга к health-проверке; интервал надо брать из WATCHDOG_USEC (daemon.SdWatchdogEnabled), обычно WatchdogSec/2 | man systemd.service, sd_listen_fds(3), sd_notify(3) | — (не перепроверено) |
| 30.9 | Medium | SIGKILL по таймауту | «Это вызовет core dump (coredumpctl)» | SIGKILL не создаёт core; дамп даёт SIGABRT (watchdog / TimeoutStopFailureMode=abort) | man 7 signal; os/signal doc; runtime/signal_unix.go; man 5 core; runtime/extern.go (GOTRACEBACK) | — (не перепроверено) |
| 30.10 | Low | LISTEN_* | — | не сброшены env (unset_environment) → унаследуют дочерние процессы; не использован LISTEN_FDNAMES | man systemd.service, sd_listen_fds(3), sd_notify(3) | — (не перепроверено) |
| 30.11 | Low | сравнение | «Go выигрывает от Type=notify благодаря отсутствию тяжёлых фреймворков» | бессмысленно; «PHP-FPM тоже поддерживает socket activation» — проверить | man systemd.service, sd_listen_fds(3), sd_notify(3) | ⚠ проверить |
| 30.12 | Low | STOPPING=1 | «для ускорения таймаута» | только информирует systemd о состоянии, таймаут не меняет | man systemd.service, sd_listen_fds(3), sd_notify(3) | — (не перепроверено) |
| 30.13 | Low | MemoryMax/Go | «MemoryHigh вместо MemoryMax» | MemoryHigh throttles/reclaim (не kill) — верно, но не упомянут GOMEMLIMIT как согласующий механизм; «ложные срабатывания из-за MADV_DONTNEED» — недоказано | Documentation/admin-guide/sysctl/vm.rst; mm/vmscan.c, mm/oom_kill.c; man 2 madvise; runtime/mgcscavenge.go | — (не перепроверено) |
| 30.14 | Low | CPUQuota=80% | — | не упомянута связь с GOMAXPROCS (Go <1.25 игнорирует квоту → throttling; ≥1.25 учитывает) | runtime/debug.go; runtime/cgroup_linux.go; Go 1.25 release notes | — (не перепроверено) |

### Статья 31. Межпроцессное взаимодействие. IPC

| № | Приор. | Раздел | Утверждение | Проблема / что проверить | Источник | Статус |
|---|:---:|---|---|---|---|---|
| 31.1 | High | Код SHM | mmap(/dev/zero, MAP_SHARED) «shared memory»; импорты os, unsafe не используются | такое отображение видимо только потомкам fork (Go fork делать не может) — неродственные процессы его не получат; для IPC нужны memfd_create / shm_open(/dev/shm)+MAP_SHARED / shmget; код не компилируется (unused imports) | man 2 mmap; mm/mmap.c; Documentation/mm/; man 7 shm_overview; man 2 memfd_create | — (не перепроверено) |
| 31.2 | High | Cache coherency | «ядро отправляет IPI для инвалидации кэша B» | когерентность (MESI/MOESI) — аппаратные snoop/directory-сообщения по интерконнекту, не IPI (IPI — программные межпроцессорные прерывания ОС) | Intel/AMD Optimization Manuals (cache coherency) | — (не перепроверено) |
| 31.3 | Medium | Pipes | «pipe() создаёт неименованный двунаправленный канал… однонаправлен» | в Linux pipe однонаправленный (двунаправленные — на BSD/Solaris); противоречие в одном абзаце; mkfifo — special file (p), не «обычный файл» | runtime/chan.go; man 7 pipe; os/exec docs (StdoutPipe) | — (не перепроверено) |
| 31.4 | Medium | Терминология | «два контекстных переключения (User→Kernel→User)» | это переходы режима (mode switches), не context switch; на передачу — 2 syscall, т.е. 4 перехода | arch/x86/kernel/process_64.c (__switch_to); kernel/sched/core.c | — (не перепроверено) |
| 31.5 | Medium | Gotcha | «race condition на уровне кэш-линий; мьютексов в пространстве ядра» | когерентность кэша гарантирована; проблема — упорядочивание/атомарность без барьеров; кросс-процессная синхронизация — PTHREAD_PROCESS_SHARED/futex в shm/atomic, sync.Mutex не работает между процессами | man 2 futex; runtime/lock_futex.go, sync/mutex.go; sync/mutex.go, sync/rwmutex.go, runtime/sema.go | — (не перепроверено) |
| 31.6 | Low | Signals | «только номер сигнала и optional errno» | siginfo несёт si_code/si_pid/si_uid; sigqueue — payload (sigval) | man 7 signal; os/signal doc; runtime/signal_unix.go; syscall/syscall_linux.go; x/sys/unix; man 2 syscalls | — (не перепроверено) |
| 31.7 | Low | Mechanical | «User→Kernel ≈1000–2000 тактов», «переключение планировщика горутин при блокировке процесса на read» | ещё одна цифра; блокируется поток, а не горутина планировщика Go | исходники Go (runtime/net/os/syscall), release notes версии; Intel SDM / AMD APM, Optimization Manual | — (не перепроверено) |
| 31.8 | Low | UDS vs TCP | «нет проверки checksum (checksum offloading)»; «нет блокировок TCP backlog/SYN queue» | на loopback checksum не считается из-за CHECKSUM_UNNECESSARY, не «offloading»; у AF_UNIX listen тоже есть backlog; «20–40%» без источника | Documentation/networking/napi.rst, skbuff.rst; man 2 listen; Documentation/networking/ip-sysctl.rst; net/ipv4/tcp_input.c | — (не перепроверено) |
| 31.9 | Low | omission | — | POSIX shm/семафоры/mq, memfd_create, eventfd, SO_PEERCRED, ipcs/ipcrm и утечки SysV IPC | man 7 shm_overview; man 2 memfd_create | — (не перепроверено) |

### Статья 32. Shared Memory и race condition между процессами

| № | Приор. | Раздел | Утверждение | Проблема / что проверить | Источник | Статус |
|---|:---:|---|---|---|---|---|
| 32.1 | High | Код | `syscall.ShmOpen/ShmSetSize/ShmUnlink` | в пакете syscall таких функций нет (shm_open — функция glibc, открывающая /dev/shm/name); корректно: os.OpenFile("/dev/shm/…")+Truncate, unix.MemfdCreate; unused imports (os, unsafe) | man 7 shm_overview; man 2 memfd_create; glibc symbol versioning docs; man 7 libc | ✔ src |
| 32.2 | Medium | Вступление | «InnoDB buffer pool, Redis, Dragonfly» как примеры cross-process SHM | это память одного (многопоточного) процесса; cross-process SHM — PostgreSQL shared_buffers, nginx/Apache scoreboard и т.п. | runtime/os_linux.go (newosproc, cloneFlags) | — (не перепроверено) |
| 32.3 | Medium | Padding | `_ [56]byte` «до 64» | на Apple Silicon линия 128 Б, у Intel spatial prefetcher спаривает линии (std использует 128 Б в sync.Pool); лучше cpu.CacheLinePad (x/sys/cpu) | Documentation/arch/arm64/memory.rst; ARM ARM; sync/pool.go; staticcheck SA6002 | — (не перепроверено) |
| 32.4 | Medium | Таблица | «Что такое futex … Основа sync.Mutex в Go» | неверно (ср. ст.23, 33): sync.Mutex использует runtime sema + gopark; futex — на уровне M | man 2 futex; runtime/lock_futex.go, sync/mutex.go; sync/mutex.go, sync/rwmutex.go, runtime/sema.go | — (не перепроверено) |
| 32.5 | Low | Gotcha | «MAP_PRIVATE нарушит правило Copy-On-Write» | формулировка неверна (COW как раз и даёт приватность) | mm/memory.c (do_wp_page); Documentation/mm/; man 2 mmap; mm/mmap.c; Documentation/mm/ | — (не перепроверено) |
| 32.6 | Low | MESI | «Ядро 2 должно инвалидировать свою копию» | при чтении у ядра 2 копия уже Invalid; Modified→Shared у ядра 1 | Intel/AMD Optimization Manuals (cache coherency) | — (не перепроверено) |
| 32.7 | Low | Цитата | «— Кен Томпсон / Роб Пайк», на английском | Go proverb Роба Пайка (2015, Effective Go); цитата на английском противоречит редполитике (русский перевод) | оригинальный источник цитаты | — (не перепроверено) |
| 32.8 | Low | Race detector | «helgrind/valgrind для Go» | не применимо; -race замедляет 5–10× и тяжёл по памяти | первоисточник по теме (спецификация/документация) | — (не перепроверено) |
| 32.9 | Low | Таблица | «mmap убирает копирование, оставляя один переход в ядро» | page faults, TLB, mmap_lock (см. ст.18) | man 2 mmap; mm/mmap.c; Documentation/mm/ | — (не перепроверено) |

### Статья 33. Mutex, Semaphore, Spinlock на уровне ОС

| № | Приор. | Раздел | Утверждение | Проблема / что проверить | Источник | Статус |
|---|:---:|---|---|---|---|---|
| 33.1 | High | Spinlock | «Spinlock эффективен … в одноядерных средах (где переключение дороже спина)» | наоборот: на UP спиннинг бессмыслен (владелец не выполняется), ядро на UP превращает spin_lock в preempt_disable | sync/mutex.go; Documentation/locking/ | — (не перепроверено) |
| 33.2 | High | Go semaphore | «пакет sync/semaphore (с Go 1.21 и golang.org/x/sync/semaphore) … опирается на semaRoot» (повтор в Итогах) | в stdlib нет sync/semaphore (ни в 1.21, ни позже); x/sync/semaphore реализован на container/list + sync.Mutex + каналах, а не на runtime semaRoot; semaRoot — treap по адресу (не «двусвязный список»), служит sync.Mutex/WaitGroup/RWMutex | sync/mutex.go, sync/rwmutex.go, runtime/sema.go; sync/mutex.go; Documentation/locking/ | ✔ src |
| 33.3 | Medium | Futex | «Франк ван де Вен, Расти Расселл, Ульрих Дреппер» | авторы: Hubertus Franke, Matthew Kirkwood (IBM), Rusty Russell; Ingo Molnar; Drepper — robust futex/NPTL (futex.2) | man 2 futex; runtime/lock_futex.go, sync/mutex.go; runtime/os_linux.go (newosproc, cloneFlags) | — (не перепроверено) |
| 33.4 | Medium | Slow path | «TASK_UNINTERRUPTIBLE» | FUTEX_WAIT спит в TASK_INTERRUPTIBLE (сигнал → EINTR) | man 7 signal; os/signal doc; runtime/signal_unix.go | — (не перепроверено) |
| 33.5 | Medium | Mechanical | «TLB invalidation и переключение CSR (Control Status Register)» | CSR — терминология RISC-V; на x86 — CR3/PCID | Intel SDM Vol.3 §4.10 (TLB); Documentation/arch/x86/tlb.rst | — (не перепроверено) |
| 33.6 | Medium | Priority inversion | «starvation mode защищает от инверсии приоритетов» | разные явления; в Go приоритетов нет; в Linux — PI-futex (FUTEX_LOCK_PI), PTHREAD_PRIO_INHERIT — не упомянуты | sync/mutex.go; Documentation/locking/ | — (не перепроверено) |
| 33.7 | Medium | Итог 5 | pprof block/mutex | профили выключены по умолчанию: нужны runtime.SetBlockProfileRate/SetMutexProfileFraction | net/http/pprof/pprof.go; runtime/pprof | — (не перепроверено) |
| 33.8 | Low | Futex | «wait_queue_head_t», «fs/futex.c», «WAKE_OP» | futex — хэш-бакеты futex_q с plist; с 5.16 kernel/futex/; WAKE_OP — отдельная операция, mutex unlock использует FUTEX_WAKE | man 2 futex; runtime/lock_futex.go, sync/mutex.go | — (не перепроверено) |
| 33.9 | Low | Semaphore | «sem_wait через semop()» | sem_wait — POSIX (futex), semop — SysV; разные API | sync/mutex.go; Documentation/locking/ | — (не перепроверено) |
| 33.10 | Low | Диаграмма | Go switch «~10–50 нс» | расходится с 100–200 нс в ст.5/7/9; «3 регистра (SP, PC, BP)» верно (против «14 регистров» в ст.5/9) | runtime/runtime2.go (gobuf); cmd/compile/abi-internal.md | — (не перепроверено) |
| 33.11 | Low | Адаптивный spin | «пока waiters равны 0» | условия: multicore, GOMAXPROCS>1, есть другие работающие P и пустой runq, ≤4 итераций ×30 PAUSE; waiters может быть >0 | runtime/debug.go; runtime/cgroup_linux.go; Go 1.25 release notes; runtime/proc.go (runqput, runnext) | — (не перепроверено) |
| 33.12 | Low | Slow path | «защита от spurious wakeup» | пробуждения не ложные: разбуженная горутина конкурирует с новыми и при неудаче встаёт в начало очереди (LIFO) | исходники Go (runtime/net/os/syscall), release notes версии | — (не перепроверено) |
| 33.13 | Low | Сравнение | «Go в 10–100 раз ниже» | без источника; Java synchronized — не «просто OS mutex» (thin/inflated monitors со спином), virtual threads (21) | JEP 444 (virtual threads), JDK/Python/PHP release notes | — (не перепроверено) |

### Статья 34. Deadlock, Livelock, Starvation

| № | Приор. | Раздел | Утверждение | Проблема / что проверить | Источник | Статус |
|---|:---:|---|---|---|---|---|
| 34.1 | High | acquireWithTimeout | паттерн «захват мьютекса с таймаутом через горутину+канал» | при таймауте фоновая горутина всё равно получит Lock и никогда не отпустит → мьютекс навсегда занят + утечка горутины; антипаттерн; в Go ≥1.18 есть TryLock; корректный — канал-семафор (chan struct{}, 1) | runtime/chan.go | ✔ src |
| 34.2 | High | RWMutex | «если читатели непрерывны, писатели голодают; fairness не гарантирован» | в Go RWMutex блокирует новых читателей, как только писатель ждёт Lock (writer-preferring); голодание писателей предотвращено; документация sync.RWMutex | sync/mutex.go, sync/rwmutex.go, runtime/sema.go | ✔ src |
| 34.3 | Medium | Вступление/§Deadlock | «горутины засыпают в системном вызове futex»; «runtime_Semacquire — обёртка над futex»; «Go опирается на futex ядра» | противоречит ст.23/33 и самому тексту ниже («Gwaiting»): futex не вызывается | man 2 futex; runtime/lock_futex.go, sync/mutex.go; sync/mutex.go, sync/rwmutex.go, runtime/sema.go | — (не перепроверено) |
| 34.4 | Medium | Gotcha detector | «без GOMAXPROCS=1 и с фоновой горутиной детектор не сработает» | GOMAXPROCS не влияет; checkdead срабатывает, если нет runnable/running G, таймеров и netpoll-ожиданий (тикер, сетевой поллер, signal.Notify его отключают) | runtime/debug.go; runtime/cgroup_linux.go; Go 1.25 release notes | — (не перепроверено) |
| 34.5 | Medium | Инструменты | `go tool pprof -goroutine …`; `GODEBUG=asyncpreempt=1` | флага -goroutine нет (pprof URL …/goroutine или ?debug=2); asyncpreempt включён по умолчанию, отключается asyncpreemptoff=1; описание неверно | net/http/pprof/pprof.go; runtime/pprof | ✔ src |
| 34.6 | Medium | Under the hood | «после спина sync.Mutex уходит в futex и паркует поток» | паркуется горутина (sema), не поток | man 2 futex; runtime/lock_futex.go, sync/mutex.go; sync/mutex.go, sync/rwmutex.go, runtime/sema.go | — (не перепроверено) |
| 34.7 | Medium | retryWithJitter | «Exponential Backoff with Jitter» | delay = rand.Intn(100) мс — ни экспоненты, ни роста; math/rand без seed (до 1.20) | воспроизводимое измерение (lmbench/perf/fio) или публикация с методикой | — (не перепроверено) |
| 34.8 | Medium | «Stack Starvation» | «Решение: GOMAXPROCS>=2 или Gosched; ctx.Done не прервёт — добавляйте Gosched» | термин выдуман (это CPU starvation); с 1.14 async preemption (sysmon, SIGURG) вытесняет tight loops; корректное — проверять ctx.Err()/select в цикле, а не Gosched | sync/mutex.go; Documentation/locking/; runtime/debug.go; runtime/cgroup_linux.go; Go 1.25 release notes | — (не перепроверено) |
| 34.9 | Medium | fairLockAcquire | «TryLock доступен только в тестах или через unsafe» | sync.Mutex.TryLock есть с Go 1.18; в цикле time.After → таймеры (до 1.23 утекают); Gosched бессмысленен | sync/mutex.go, sync/rwmutex.go, runtime/sema.go | ✔ src |
| 34.10 | Medium | Interview | «детект можно отключить через runtime.GOMAXPROCS(0) и фоновый режим» | бессмыслица; отключить нельзя, «обойти» — таймером/netpoll/signal.Notify | runtime/debug.go; runtime/cgroup_linux.go; Go 1.25 release notes | — (не перепроверено) |
| 34.11 | Low | Interview | «при deadlock горутина Gwaiting или Gdead» | _Gdead — завершённая горутина | sync/mutex.go; Documentation/locking/ | — (не перепроверено) |
| 34.12 | Low | MESI | «широковещательный запрос», «тераватты» | directory/snoop-filter; гипербола; 20–50 тактов vs 100–300 нс в ст.31 | Intel/AMD Optimization Manuals (cache coherency) | — (не перепроверено) |
| 34.13 | Low | Таблица | «М-н-1 / М-н-М», «std::thread 2 МБ стека» | M:N; на Linux default 8 МБ virtual | runtime/os_linux.go (newosproc, cloneFlags) | — (не перепроверено) |
| 34.14 | Low | omission | — | go-deadlock, mutex profile, RLock-рекурсия, WaitGroup/Cond ловушки | sync/mutex.go; Documentation/locking/; go vet copylocks; sync docs | — (не перепроверено) |

### Статья 35. Асинхронный IO и блокирующий IO

| № | Приор. | Раздел | Утверждение | Проблема / что проверить | Источник | Статус |
|---|:---:|---|---|---|---|---|
| 35.1 | High | Таблица моделей / Interview | Interview: Go = «синхронный неблокирующий»; таблица: Go netpoll, Node.js — «Async Non-blocking»; Nginx/epoll — «Sync Non-blocking»; «Async Blocking = aio_*» | внутреннее противоречие (Go, Node и Nginx используют один и тот же readiness-механизм); aio_* не блокирует при инициации | runtime/netpoll.go, netpoll_epoll.go; man 7 epoll | — (не перепроверено) |
| 35.2 | Medium | Код setNonblocking | `return syscall.FcntlInt(...)` из функции, возвращающей error; `os` не используется | не компилируется; есть syscall.SetNonblock(fd, true) | go build / go vet на листинге | — (не перепроверено) |
| 35.3 | Medium | Стивенс | «в классификации Стивенса sync/async — два ортогональных измерения» | у Стивенса пять моделей (blocking, nonblocking, multiplexing, signal-driven, async/POSIX aio); по POSIX мультиплексирование — синхронный I/O; «ортогональность» — популярная, но не стивенсовская трактовка | первоисточник по теме (спецификация/документация) | — (не перепроверено) |
| 35.4 | Medium | Go Read | «если EAGAIN → регистрирует fd в netpoll (epoll)» | fd регистрируется в epoll один раз при создании (netpollopen, EPOLLET); при EAGAIN — только park на pollDesc (runtime_pollWait); ст.36 повторяет ошибку в диаграмме и противоречит себе | runtime/netpoll.go, netpoll_epoll.go; man 7 epoll; runtime/runtime2.go (gobuf); cmd/compile/abi-internal.md | — (не перепроверено) |
| 35.5 | Medium | Gotcha CPU-bound | «если все M заняты вычислениями, netpoller не найдёт свободный тред»; LockOSThread как решение | с 1.14 async preemption + sysmon (netpoll если не опрашивали >10 мс) — поллер работает; LockOSThread не по теме | runtime/netpoll.go, netpoll_epoll.go; man 7 epoll; runtime/os_linux.go (newosproc, cloneFlags) | — (не перепроверено) |
| 35.6 | Low | Шкала времени | NVMe «20 мкс» | в других статьях 50–100 мкс; разброс (Optane/enterprise vs consumer) не оговорён | NVMe spec; JEDEC/ONFI; документация вендора SSD | — (не перепроверено) |
| 35.7 | Low | Блокирующий | «кэши L1/L2 полностью вымываются»; «Java до версии 17» | гипербола; virtual threads — Java 21 (GA), не 17; NIO с 1.4; стек «1–2 МБ ×50 000 = 100 ГБ» — virtual, не RAM; «90% CPU на ctx switch» без источника | JEP 444 (virtual threads), JDK/Python/PHP release notes | — (не перепроверено) |
| 35.8 | Low | Псевдокод netpoll | `epoll.Wait`, `pollCache.get` | концептуально; реальные: netpoll→netpollready | runtime/netpoll.go, netpoll_epoll.go; man 7 epoll | — (не перепроверено) |
| 35.9 | Low | Таблица | «Go ~10–20 нс» | ещё один вариант оценки | исходники Go (runtime/net/os/syscall), release notes версии; воспроизводимое измерение (lmbench/perf/fio) или публикация с методикой | — (не перепроверено) |

### Статья 36. select, poll и epoll

| № | Приор. | Раздел | Утверждение | Проблема / что проверить | Источник | Статус |
|---|:---:|---|---|---|---|---|
| 36.1 | Medium | select | «FD_SETSIZE — константа ядра»; «select сканирует все 1024 бита» | FD_SETSIZE — константа libc (glibc), ядро принимает nfds ≤ RLIMIT_NOFILE; сканируется 0..nfds-1, не всегда 1024 | man 2 select/poll; fs/select.c | — (не перепроверено) |
| 36.2 | Medium | poll/select | «poll — обёртка над select; используют core_sys_select/do_select» | poll идёт через do_sys_poll/do_poll; общее — механизм poll_table (f_op->poll), не те же функции | man 2 select/poll; fs/select.c | — (не перепроверено) |
| 36.3 | Medium | epoll | «callback регистрируется в драйвере устройства; прямая интеграция с драйверами NIC» | callback вешается на wait-queue файла/сокета (sock_poll→poll_wait), срабатывает из sk_data_ready в softirq | runtime/netpoll.go, netpoll_epoll.go; man 7 epoll; runtime/runtime2.go (gobuf); cmd/compile/abi-internal.md | — (не перепроверено) |
| 36.4 | Medium | Go-sequence | диаграмма: после EAGAIN → epoll_ctl(ADD, EPOLLET); `runtime.wakeG` | противоречит последующему абзацу «регистрация один раз»; wakeG не существует (netpollready/netpollunblock/injectglist) | runtime/netpoll.go, netpoll_epoll.go; man 7 epoll | ✔ src |
| 36.5 | Medium | «Пул буферов sync.Pool в netpoller» | — | runtime netpoller не использует sync.Pool; пулы — в net/http, не в netpoll | runtime/netpoll.go, netpoll_epoll.go; man 7 epoll; sync/pool.go; staticcheck SA6002 | — (не перепроверено) |
| 36.6 | Low | История | «poll — 1989» на диаграмме vs «конец 1980-х»; «почти три десятилетия» | SVR3 (1986–87); 1983→2002 ≈ два десятилетия | man 2 select/poll; fs/select.c | — (не перепроверено) |
| 36.7 | Low | struct epoll_filefd | «защита от циклических зависимостей» | это ключ (file*, fd) для rb-tree; проверка циклов — ep_loop_check | runtime/netpoll.go, netpoll_epoll.go; man 7 epoll | — (не перепроверено) |
| 36.8 | Low | Interview | «многократный экспоненциальный выигрыш» | разница O(n) vs O(ready), не экспонента | первоисточник по теме (спецификация/документация) | — (не перепроверено) |
| 36.9 | Low | omission | — | epoll не работает с обычными файлами (EPERM); закрытие fd при dup'ах не удаляет его из epoll; EPOLLONESHOT; EPOLLEXCLUSIVE актуален для нескольких процессов/epoll-инстансов, Go использует один; io_uring | runtime/netpoll.go, netpoll_epoll.go; man 7 epoll; runtime/os_linux.go (newosproc, cloneFlags) | — (не перепроверено) |

### Статья 37. kqueue и IOCP. Чем отличаются BSD и Windows

| № | Приор. | Раздел | Утверждение | Проблема / что проверить | Источник | Статус |
|---|:---:|---|---|---|---|---|
| 37.1 | High | IOCP | «встроенный пул потоков ядра» (текст + диаграмма) | пул создаёт приложение (или ThreadpoolIo); ядро лишь ограничивает concurrency и будит рабочие потоки LIFO | kqueue(2); Microsoft IOCP docs; runtime/netpoll_kqueue.go | — (не перепроверено) |
| 37.2 | Medium | kqueue | «в отличие от epoll, где один контекст, kqueue — очереди событий» | kqueue-fd и epoll-fd структурно эквивалентны; различие — набор фильтров | runtime/netpoll.go, netpoll_epoll.go; man 7 epoll; kqueue(2); Microsoft IOCP docs; runtime/netpoll_kqueue.go | — (не перепроверено) |
| 37.3 | Medium | Внутр. | «sys/kern/kern_kqueue.c»; «автоматическая регистрация EVFILT_WRITE при LISTEN» | файл — sys/kern/kern_event.c; автоматической регистрации нет (выдумка) | kqueue(2); Microsoft IOCP docs; runtime/netpoll_kqueue.go; runtime/runtime2.go (gobuf); cmd/compile/abi-internal.md | — (не перепроверено) |
| 37.4 | Medium | Gotcha | «select/poll на Windows эмулируются через GetQueuedCompletionStatus» | Winsock select()/WSAPoll — нативные; утверждение выдумано | man 2 select/poll; fs/select.c | — (не перепроверено) |
| 37.5 | Medium | Ловушки | «EVFILT_TIMER и Go», «пул IOCP — Go нивелирует gopark» | Go не использует EVFILT_TIMER; gopark к IOCP-пулу отношения не имеет | kqueue(2); Microsoft IOCP docs; runtime/netpoll_kqueue.go | — (не перепроверено) |
| 37.6 | Medium | omission | — | Linux io_uring — completion-модель (Proactor) на Linux, Windows RIO, BSD aio; Go не использует io_uring | исходники Go (runtime/net/os/syscall), release notes версии; исходники и Documentation/ ядра, man-страницы (man 2/7) | — (не перепроверено) |
| 37.7 | Low | Go-файлы | `netpollkqueue.go`, `netpollwindows.go`, `netpollLink` | реальные: runtime/netpoll_kqueue.go, netpoll_windows.go; `netpollLink` — проверить (структуры операций живут в internal/poll/fd_windows.go: operation/ioSrv) | runtime/netpoll.go, netpoll_epoll.go; man 7 epoll; kqueue(2); Microsoft IOCP docs; runtime/netpoll_kqueue.go | ✔ src |
| 37.8 | Low | Таблица | «kqueue масштабирование ограничено дескрипторами; IOCP высокое» | обе модели масштабируются до сотен тыс. соединений | kqueue(2); Microsoft IOCP docs; runtime/netpoll_kqueue.go; man 2 open/fcntl; os/file_unix.go | — (не перепроверено) |
| 37.9 | Low | «удерживать буферы заблокированными в памяти» | — | Go-GC не двигает объекты; блокировки (pinning) не нужны, но нужен KeepAlive | net/dial.go, net/tcpsockopt_posix.go; man 7 tcp; runtime/mgc.go; go.dev/doc/gc-guide | — (не перепроверено) |

### Статья 38. Как netpoller Go использует epoll и kqueue

| № | Приор. | Раздел | Утверждение | Проблема / что проверить | Источник | Статус |
|---|:---:|---|---|---|---|---|
| 38.1 | High | Итог 2 | «Флаги EPOLLONESHOT и EV_ONESHOT гарантируют точечный контроль» | прямо противоречит телу статьи («в отличие от EPOLLONESHOT» — Go использует ET, не oneshot) | runtime/netpoll.go, netpoll_epoll.go; man 7 epoll | — (не перепроверено) |
| 38.2 | Medium | Ссылка на ст.35 | «оба подхода работают по принципу edge-triggered» | epoll по умолчанию level-triggered; kqueue — тоже level, edge-подобное поведение даёт EV_CLEAR; статья 36 сама описывает LT/ET | runtime/netpoll.go, netpoll_epoll.go; man 7 epoll; kqueue(2); Microsoft IOCP docs; runtime/netpoll_kqueue.go | — (не перепроверено) |
| 38.3 | Medium | sysmon и netpoll | «sysmon просыпается и вызывает netpoll(0)» (основной механизм); диаграмма Sysmon→goready | sysmon опрашивает netpoll лишь как fallback (если >10 мс не опрашивали); основной путь — findRunnable/schedule (в т.ч. блокирующий netpoll у простаивающего M) | runtime/proc.go (sysmon, retake, handoffp); runtime/netpoll.go, netpoll_epoll.go; man 7 epoll | — (не перепроверено) |
| 38.4 | Medium | Mechanical | «сотни тысяч соединений в одном гигабайте» | на соединение: стек 2–8 КБ + g + буферы (bufio/http ≈ 4–8 КБ) + netFD/pollDesc ≈ 10–20 КБ; 100k ≈ 1–2 ГБ | runtime/netpoll.go, netpoll_epoll.go; man 7 epoll | — (не перепроверено) |
| 38.5 | Medium | Interview | «M используют неблокирующий epoll_wait с расчётным таймаутом»; sysmon+startm | блокирующий epoll_wait с таймаутом ближайшего таймера делает один простаивающий M; остальные M спят на futex | runtime/proc.go (sysmon, retake, handoffp); runtime/netpoll.go, netpoll_epoll.go; man 7 epoll | — (не перепроверено) |
| 38.6 | Low | Таблица | «epoll использует хеш-таблицу и rb-tree» | только rb-tree (+rdllist) | runtime/netpoll.go, netpoll_epoll.go; man 7 epoll | — (не перепроверено) |
| 38.7 | Low | Код | `type netpoller struct{fd int}` «из runtime/netpoll.go» | такой структуры нет: глобальные epfd (netpoll_epoll.go), pollDesc; Go также создаёт eventfd для netpollBreak (с 1.21; раньше pipe) | runtime/netpoll.go, netpoll_epoll.go; man 7 epoll | — (не перепроверено) |
| 38.8 | Low | netpollReady / goready / netpollLock | функции и «спинлок netpollLock» | netpollready/netpollunblock + injectglist; блокировка — pollDesc.lock (mutex); `netpollLock` не существует (и в таблице: «>500k сокетов — конкуренция netpollLock» — выдумка) | runtime/netpoll.go, netpoll_epoll.go; man 7 epoll | ✔ src |
| 38.9 | Low | Tokio | «epoll / io_uring (Linux)» | Tokio — epoll через mio; io_uring — отдельно (tokio-uring/monoio) | runtime/netpoll.go, netpoll_epoll.go; man 7 epoll | — (не перепроверено) |
| 38.10 | Low | omission | — | deadlines (SetReadDeadline) и интеграция таймеров с netpoll; pipes/FIFO через netpoll | runtime/netpoll.go, netpoll_epoll.go; man 7 epoll; man 7 pipe; os/exec docs (StdoutPipe) | — (не перепроверено) |

### Статья 39. Файловые системы. Что происходит после write

| № | Приор. | Раздел | Утверждение | Проблема / что проверить | Источник | Статус |
|---|:---:|---|---|---|---|---|
| 39.1 | Medium | Under hood | «mapping->dirty_pages», struct page | счётчика нет: учёт через xarray-теги PAGECACHE_TAG_DIRTY и NR_FILE_DIRTY/wb_stat; с 5.16 основа — folio (large folios в ext4/XFS) | Documentation/admin-guide/sysctl/vm.rst; mm/filemap.c, mm/page-writeback.c | — (не перепроверено) |
| 39.2 | Medium | blk-mq | «сортирует запросы по LBA, coalescing» | для NVMe дефолт scheduler=none (сортировки нет); mq-deadline/bfq/kyber — для HDD/SATA (см. ст.45) | Documentation/block/; block/blk-mq.c | — (не перепроверено) |
| 39.3 | Medium | Журнал/ordered | «потеряете все 100 МБ» | с delalloc после краша размер файла может быть 0/старый; нюанс data=ordered/XFS не раскрыт; ext4 `auto_da_alloc` для rename/truncate | man 2 fsync; Documentation/filesystems/ext4/; fs/jbd2 | — (не перепроверено) |
| 39.4 | Medium | O_DIRECT | «обходит кэш; DMA» | не гарантирует durability: без O_DSYNC/fdatasync данные могут остаться в кэше устройства; выравнивание — по logical block size (512/4096) | man 2 open (O_DIRECT); statx(2) | — (не перепроверено) |
| 39.5 | Medium | Код | строки "…\n" с разрывом; нет fsync родительского каталога | при создании файла/rename без fsync(dir) запись о файле может пропасть после краша — главный пропуск для статьи о durability; Go: File.Sync() = fsync (macOS — F_FULLFSYNC); os-пакет не имеет fdatasync (нужен unix.Fdatasync) | man 2 fsync; Documentation/filesystems/ext4/; fs/jbd2 | — (не перепроверено) |
| 39.6 | Medium | Mechanical | «ядро обеспечивает согласованность кэшей для DMA через clflush/wbinvd» | на x86 DMA когерентен (snoop), wbinvd/clflush не нужны (нужны на некогерентных ARM/MIPS) | Intel/AMD Optimization Manuals (cache coherency); runtime/os_linux.go (newosproc, cloneFlags) | — (не перепроверено) |
| 39.7 | Medium | Go | «file.Sync — fsync, а для диапазона — sync_file_range» | Go sync_file_range не вызывает | man 2 fsync; Documentation/filesystems/ext4/; fs/jbd2 | ✔ src |
| 39.8 | Medium | omission | — | fsync error semantics (fsyncgate: после EIO страницы чистые, повтор небезопасен); atomic rename pattern (tmp+fsync+rename+fsync dir) | man 2 fsync; Documentation/filesystems/ext4/; fs/jbd2 | — (не перепроверено) |
| 39.9 | Medium | O_DIRECT Go | «используйте Mmap … проверяя через file.Readdir(0)» | бессмыслица; практичный способ — аллокация с выравниванием (offset внутри буфера, библиотека directio) | man 2 open (O_DIRECT); statx(2) | — (не перепроверено) |
| 39.10 | Low | Триггеры | «dirty_background_ratio ~10% RAM; dirty_ratio 20% блокирует write» | проценты от доступной (available) памяти, не всего RAM; throttling в balance_dirty_pages плавный, задолго до порога; есть *_bytes | Documentation/admin-guide/sysctl/vm.rst; mm/filemap.c, mm/page-writeback.c; runtime/os_linux.go (newosproc, cloneFlags) | — (не перепроверено) |

### Статья 40. Устройство файловых систем. inode, dentry, superblock

| № | Приор. | Раздел | Утверждение | Проблема / что проверить | Источник | Статус |
|---|:---:|---|---|---|---|---|
| 40.1 | High | Код inspectFile | `os.FileMode(w.Stat_t.Mode)` | st_mode ≠ os.FileMode (разные битовые раскладки): IsDir()/Type() вернут неверно; «прямой syscall.Stat выигрывает микросекунды» — нет (обёртка аллоцирует); Printf-разрывы | go build / go vet на листинге | — (не перепроверено) |
| 40.2 | Medium | Mermaid | `GoApp["os.Open("/etc/nginx/nginx.conf")"]` и `A["Go: os.Open("/etc/nginx…")"]` | вложенные двойные кавычки в label ломают парсер Mermaid (Syntax error) | Mermaid Live Editor; повторная сборка (builder/audit_all.py) | — (не перепроверено) |
| 40.3 | Medium | Superblock | поля s_inodes_count/s_free_inodes_count; «s_op: ext4_fill_super, xfs_init» | s_inodes_count — поле дискового ext4_super_block, не VFS super_block; s_op = struct super_operations (alloc_inode, write_inode…), fill_super — не её член | Documentation/filesystems/vfs.rst; fs/dcache.c | — (не перепроверено) |
| 40.4 | Medium | Каталоги | «поиск в каталоге с миллионом файлов — медленный перебор» | ext4 dir_index (HTree)/XFS B+tree дают ~O(log n) lookup; проблемы — readdir/stat-шторм, память dcache, fsck, ls | Documentation/filesystems/vfs.rst; fs/dcache.c | — (не перепроверено) |
| 40.5 | Medium | Perf | «глубокие пути → dcache thrashing, конкуренция блокировок каталогов» | RCU-walk lookup без блокировок; «thrashing» — только при давлении памяти; без источника | Documentation/filesystems/vfs.rst; fs/dcache.c | — (не перепроверено) |
| 40.6 | Low | Ошибки Go | «os.Stat при повреждённом суперблоке вернёт EBADF/EIO; fs.ReadStat» | EBADF — неверный fd; `fs.ReadStat` не существует (есть fs.Stat, FileInfo) | исходники Go (runtime/net/os/syscall), release notes версии | — (не перепроверено) |
| 40.7 | Low | Inode | `i_block[EXT4_DIRECT_BLOCKS]` | i_block[EXT4_N_BLOCKS]; EXT4_NDIR_BLOCKS=12; нет birth time (i_crtime, statx btime) | первоисточник по теме (спецификация/документация) | — (не перепроверено) |
| 40.8 | Low | Q2 | «ctime обновляется при изменении inode номера» | inode-номер не меняется; ctime также обновляется при write | Documentation/filesystems/vfs.rst; fs/dcache.c | — (не перепроверено) |
| 40.9 | Low | dentry | «при unlink dentry удаляется из кэша» | становится negative dentry (кэшируется отсутствие) | Documentation/filesystems/vfs.rst; fs/dcache.c; net/unixsock_posix.go; man 7 unix | — (не перепроверено) |
| 40.10 | Low | Go syscalls | «os — обёртка над openat2, statx» | os.Open — openat, Stat — newfstatat/fstatat; openat2 stdlib не использует (проверить для os.Root в 1.24) | исходники Go (runtime/net/os/syscall), release notes версии | ⚠ проверить |
| 40.11 | Low | Разметка | заголовок «## > [!tip] Собеседование» | сломанная разметка callout внутри заголовка | первоисточник по теме (спецификация/документация) | — (не перепроверено) |

### Статья 41. Журналируемые файловые системы

| № | Приор. | Раздел | Утверждение | Проблема / что проверить | Источник | Статус |
|---|:---:|---|---|---|---|---|
| 41.1 | High | Режимы журналирования | «ext4, XFS, Btrfs поддерживают три режима data=; data=ordered — по умолчанию в ext4 и XFS» | data=ordered/writeback/journal — опции только ext3/ext4; XFS журналирует только метаданные и не имеет data=; Btrfs — COW без журнала (tree-log для fsync); ZFS — ZIL | man 2 fsync; Documentation/filesystems/ext4/; fs/jbd2 | — (не перепроверено) |
| 41.2 | High | Протокол коммита | порядок: журнал → flush → commit record → checkpointing (в пути fsync) → возврат fsync | в jbd2 fsync возвращается после того, как commit-блок надёжен (preflush+FUA); checkpointing выполняется позже асинхронно и в fsync не входит; диаграмма (F до G) неверна; контрольная сумма — CRC32C (journal_checksum v2/v3) | man 2 fsync; Documentation/filesystems/ext4/; fs/jbd2 | — (не перепроверено) |
| 41.3 | Medium | Write barriers | «WRITE BARRIER через libata/nvme» | barrier-примитив удалён в 2.6.37; теперь REQ_PREFLUSH/REQ_FUA; mount-опция barrier=0/nobarrier осталась; «гарантированно разрушит ФС» — только при волатильном кэше без PLP | Intel SDM / AMD APM, Optimization Manual | — (не перепроверено) |
| 41.4 | Medium | Код fdatasync | «исключает лишний Journal Commit» | файл открыт с O_CREATE\|O_TRUNC и растёт → изменяются размер/аллокация → fdatasync тоже требует коммита; выигрыш только при перезаписи preallocated-файла; нет fsync каталога; f.Fd() переводит файл в blocking-режим | man 2 fsync; Documentation/filesystems/ext4/; fs/jbd2 | — (не перепроверено) |
| 41.5 | Medium | omission | — | ext4 fast_commit (5.10), metadata_csum, commit=N (5 с), journal_async_commit; Btrfs/ZFS COW; Go: F_FULLFSYNC на macOS | mm/memory.c (do_wp_page); Documentation/mm/; man 2 fsync; Documentation/filesystems/ext4/; fs/jbd2 | — (не перепроверено) |
| 41.6 | Low | Цифры | fsync «HDD 5–15 мс; NVMe 100–500 мкс» | enterprise NVMe с PLP ≈ 20–100 мкс, consumer без PLP — единицы мс; ст.39: «миллисекунды на SSD» | man 2 fsync; Documentation/filesystems/ext4/; fs/jbd2; NVMe spec; JEDEC/ONFI; документация вендора SSD | — (не перепроверено) |
| 41.7 | Low | Write amplification | «транзакцию дважды» | двойная запись — для метаданных (и всех данных в data=journal); в ordered данные пишутся один раз | man 2 fsync; Documentation/filesystems/ext4/; fs/jbd2 | — (не перепроверено) |
| 41.8 | Low | Interview | «ФС журналирует 4 КБ блок для 50-байтной строки» | в ordered данные не журналируются | man 2 fsync; Documentation/filesystems/ext4/; fs/jbd2 | — (не перепроверено) |
| 41.9 | Low | PHP | «сбрасывать состояние в Redis командой SAVE» | бессмыслица (SAVE — синхронный RDB-снимок) | JEP 444 (virtual threads), JDK/Python/PHP release notes | — (не перепроверено) |

### Статья 42. Буферизация IO и Page Cache

| № | Приор. | Раздел | Утверждение | Проблема / что проверить | Источник | Статус |
|---|:---:|---|---|---|---|---|
| 42.1 | High | Код O_DIRECT | `os.O_DIRECT` | константы в пакете os нет (ст.43 сама это говорит: syscall.O_DIRECT/unix.O_DIRECT) — не компилируется; противоречие между статьями | man 2 open (O_DIRECT); statx(2) | — (не перепроверено) |
| 42.2 | Medium | Read-ahead | «планировщик I/O включает read-ahead» | readahead — часть mm/page cache (read_ahead_kb=128), не I/O scheduler | Documentation/admin-guide/sysctl/vm.rst; mm/filemap.c, mm/page-writeback.c | — (не перепроверено) |
| 42.3 | Medium | dirty ratios | «10% и 20% от свободной RAM» | от available memory (free+reclaimable), см. vm.dirty_*_bytes; throttling начинается раньше (freerun ceiling) | runtime/os_linux.go (newosproc, cloneFlags) | — (не перепроверено) |
| 42.4 | Medium | Примеры СУБД с O_DIRECT | «PostgreSQL, ScyllaDB, RocksDB, Redis» (и ст.43: «PostgreSQL (direct_io), ClickHouse, Redis») | PostgreSQL по умолчанию использует page cache (direct I/O — debug_io_direct, экспериментально с 16/17); Redis O_DIRECT не использует; RocksDB — опция use_direct_reads; ClickHouse — по порогу | man 2 open (O_DIRECT); statx(2) | — (не перепроверено) |
| 42.5 | Medium | Итог 5 | «O_DIRECT и mmap позволяют обойти Page Cache» | mmap отображает сам Page Cache (ст.18) — не обходит | man 2 mmap; mm/mmap.c; Documentation/mm/; man 2 open (O_DIRECT); statx(2) | — (не перепроверено) |
| 42.6 | Medium | omission | — | posix_fadvise/readahead/sync_file_range; /proc/meminfo (Dirty/Writeback/Cached); page cache входит в cgroup memory (working_set в k8s) — важно для логирующих Go-сервисов; fincore/vmtouch | Documentation/admin-guide/sysctl/vm.rst; mm/filemap.c, mm/page-writeback.c; Documentation/admin-guide/cgroup-v2.rst | — (не перепроверено) |
| 42.7 | Low | Under hood | «page cache = массив struct page; ключ устройство+inode+offset» | кэш на файл: address_space(inode)->i_pages (xarray) по смещению; элементы — folio (с 5.16) | Documentation/admin-guide/sysctl/vm.rst; mm/filemap.c, mm/page-writeback.c; Documentation/filesystems/vfs.rst; fs/dcache.c | — (не перепроверено) |
| 42.8 | Low | Диаграмма | «Page Miss ~1–5 мс» | NVMe ≈100 мкс; HDD 5–10 мс | NVMe spec; JEDEC/ONFI; документация вендора SSD | — (не перепроверено) |
| 42.9 | Low | Interview | «fsync прерывает фоновый write-back цикл» | нет | man 2 fsync; Documentation/filesystems/ext4/; fs/jbd2 | — (не перепроверено) |
| 42.10 | Low | Mechanical | «DRAM накопителя» в цепочке копий; PHP «буфер libc» | цепочка искажена; у PHP свои streams (8 КБ), не libc stdio | JEP 444 (virtual threads), JDK/Python/PHP release notes; runtime/os_linux.go (newosproc, cloneFlags) | — (не перепроверено) |

### Статья 43. Direct IO и Zero Copy

| № | Приор. | Раздел | Утверждение | Проблема / что проверить | Источник | Статус |
|---|:---:|---|---|---|---|---|
| 43.1 | High | Код writeDirectIO | «aligned := make([]byte, len+4096); f.Write(aligned[:len(data)])» | не выравнивает адрес (нет смещения до границы) и длина не кратна блоку → EINVAL; «posix_memalign в Go» отсутствует; код не показывает заявленное выравнивание | воспроизвести: go build / go vet | — (не перепроверено) |
| 43.2 | Medium | Direct IO internals | «read_iter → direct_IO → blk_rq_map_user»; «0% CPU» | путь через mapping->a_ops->direct_IO / iomap_dio_rw → bio; blk_rq_map_user — для SG_IO/passthrough; CPU нужен для submit/IRQ | первоисточник по теме (спецификация/документация) | — (не перепроверено) |
| 43.3 | Medium | Выравнивание | «аппаратное требование DMA PCIe: кратность размеру страницы»; bounce buffer | требование — logical block size устройства (512 или 4096) и dma_alignment; при нарушении — EINVAL, а не bounce buffer; с Linux 6.0 есть statx(STATX_DIOALIGN) — не упомянуто | man 2 open (O_DIRECT); statx(2) | — (не перепроверено) |
| 43.4 | Medium | Go sendfile | «fs.go анализирует типы; на других ОС — WriteFile» | решение принимает net.TCPConn.ReadFrom (sendfile/splice); sendfile также на Darwin/FreeBSD/Solaris, TransmitFile на Windows; не работает через TLS, bufio, gzip-middleware | man 2 sendfile/splice; net/tcpsock_posix.go (ReadFrom) | — (не перепроверено) |
| 43.5 | Medium | Corner 1 | «O_DIRECT продлевает ресурс NAND; на HDD — взрывной прирост» | износ определяется FTL/write amplification, O_DIRECT его не снижает; утверждения без источника | man 2 open (O_DIRECT); statx(2); NVMe spec; JEDEC/ONFI; документация вендора SSD | — (не перепроверено) |
| 43.6 | Low | Классический путь | «перезагрузка таблиц страниц при каждом переходе» | syscall не перезагружает CR3 (кроме KPTI) | Documentation/arch/x86/pti.rst; Intel SDM; Intel SDM Vol.3 §4.10 (TLB); Documentation/arch/x86/tlb.rst | — (не перепроверено) |
| 43.7 | Low | tmpfs | «может игнорировать/деградировать» | до 6.6 O_DIRECT на tmpfs → EINVAL | man 2 open (O_DIRECT); statx(2) | — (не перепроверено) |
| 43.8 | Low | «mmap для >2 ГБ» | — | порога 2 ГБ нет | man 2 mmap; mm/mmap.c; Documentation/mm/ | — (не перепроверено) |
| 43.9 | Low | omission | — | copy_file_range (Go ≥1.15), MSG_ZEROCOPY, io_uring fixed buffers, vmsplice; побочный эффект sendfile — изменение файла во время передачи | man 2 sendfile/splice; net/tcpsock_posix.go (ReadFrom) | — (не перепроверено) |

### Статья 44. Диски и устройства хранения

| № | Приор. | Раздел | Утверждение | Проблема / что проверить | Источник | Статус |
|---|:---:|---|---|---|---|---|
| 44.1 | Medium | Код O_DIRECT | «проверяйте выравнивание через os.File.Stat() и syscall.Statfs()» | ни Stat, ни Statfs.Bsize не дают dio-выравнивание: нужны statx(STATX_DIOALIGN, ≥6.0), BLKSSZGET или /sys/block/*/queue/logical_block_size; на tmpfs/overlayfs O_DIRECT может давать EINVAL; Printf-разрыв; (код выравнивания здесь корректен, в отличие от ст.42/43 — несогласованность) | man 2 open (O_DIRECT); statx(2) | — (не перепроверено) |
| 44.2 | Low | Эпиграф | «Свободная парафраза Хэмминга» | вымышленная; Хэмминга — только «The purpose of computing is insight, not numbers» (повтор [8]) | оригинальный источник цитаты | — (не перепроверено) |
| 44.3 | Low | Mermaid | `F["Контроллер …:::process"]`, `Host["…:::system"]` | `:::class` внутри кавычек выводится как текст (см. ст.3/4/15) | Mermaid Live Editor; повторная сборка (builder/audit_all.py) | — (не перепроверено) |
| 44.4 | Low | Шкала времени | NVMe «1–2 дня», HDD «4–9 мес» | при 1 такт=1 с: NVMe 10–100 мкс ≈ 9 ч…4 сут; HDD 5–10 мс ≈ 6–12 мес; ст.35 даёт «NVMe 20 мкс ≈ сутки» — разнобой | NVMe spec; JEDEC/ONFI; документация вендора SSD | — (не перепроверено) |
| 44.5 | Low | Таблица | NVMe «3–7 ГБ/с (Gen4/5)» | Gen5 — до ~14 ГБ/с; «мегабайты DRAM» в SSD — обычно ≈1 ГБ/ТБ (есть DRAM-less) | NVMe spec; JEDEC/ONFI; документация вендора SSD | — (не перепроверено) |
| 44.6 | Low | TRIM | не упомянуты fstrim.timer/discard mount; erase «в 10–20 раз дольше чтения или программирования» | erase ≈ 3–10 мс vs program ≈0.2–1 мс vs read ≈50 мкс | NVMe spec; JEDEC/ONFI; документация вендора SSD; runtime/os_linux.go (newosproc, cloneFlags) | — (не перепроверено) |
| 44.7 | Low | Mechanical | «TLB shootdowns при mmap на медленных устройствах» | не следует из page faults | Intel SDM Vol.3 §4.10 (TLB); Documentation/arch/x86/tlb.rst; man 2 mmap; mm/mmap.c; Documentation/mm/ | — (не перепроверено) |

### Статья 45. Scheduler диска и очередь запросов

| № | Приор. | Раздел | Утверждение | Проблема / что проверить | Источник | Статус |
|---|:---:|---|---|---|---|---|
| 45.1 | Medium | Таблица | mq-deadline «безусловный приоритет чтению» | чтение предпочтительнее, но есть writes_starved (по умолчанию 2) и дедлайны — «безусловного» приоритета нет; kyber — «API-шлюзы» (уровень блочного устройства) | Documentation/block/; block/blk-mq.c | — (не перепроверено) |
| 45.2 | Medium | Gotcha/скрипт | для NVMe-БД рекомендован mq-deadline | типовая практика для NVMe — none (mq-deadline добавляет блокировки); утверждение без измерений; nr_requests на NVMe по умолчанию ≈1023 — «увеличение до 256» его уменьшает; настройки в sysfs не переживают перезагрузку (udev) | Documentation/block/; block/blk-mq.c; NVMe spec; JEDEC/ONFI; документация вендора SSD | — (не перепроверено) |
| 45.3 | Medium | История | «до 4.8 — единая очередь с q->queue_lock» | blk-mq — с 3.13 (2014), NVMe→blk-mq в 3.19, scheduler-фреймворк blk-mq в 4.11, legacy single-queue удалён в 5.0; «80% времени в спин-локе» без источника | Documentation/block/; block/blk-mq.c; NVMe spec; JEDEC/ONFI; документация вендора SSD | — (не перепроверено) |
| 45.4 | Low | HDD vs SSD | «планировщик нужен SSD из-за P/E и write amplification» | I/O scheduler износ NAND не уменьшает | NVMe spec; JEDEC/ONFI; документация вендора SSD | — (не перепроверено) |
| 45.5 | Low | Pipeline | «Merge & Sort» для всех | сортировка есть у mq-deadline/BFQ; у none её нет | Documentation/block/; block/blk-mq.c | — (не перепроверено) |
| 45.6 | Low | io_uring | «подружить с Go», «горутины не блокируют M» | stdlib Go io_uring не использует; сторонние библиотеки, проблемы интеграции с GC/netpoller; io_uring отключён/заблокирован в ряде сред (Docker ≥25 default seccomp, GKE/ChromeOS, Android) | runtime/os_linux.go (newosproc, cloneFlags) | — (не перепроверено) |
| 45.7 | Low | fsync | — | описание REQ_PREFLUSH/REQ_FUA верно (противоречит ст.41 «WRITE BARRIER») | man 2 fsync; Documentation/filesystems/ext4/; fs/jbd2 | — (не перепроверено) |

### Статья 46. RAID, LVM и логические тома

| № | Приор. | Раздел | Утверждение | Проблема / что проверить | Источник | Статус |
|---|:---:|---|---|---|---|---|
| 46.1 | High | Таблица RAID | чтение/запись: RAID5 read «~1×», RAID6 «~1×», RAID10 read «~1×» write «~1×»; RAID0 «tmpfs на SSD» | RAID5/6 читают ≈(N−1)/(N−2)×, RAID10 — до N× на чтении и N/2× на записи; фраза про tmpfs бессмысленна; «RAID6 только для холодных архивов» — гипербола | NVMe spec; JEDEC/ONFI; документация вендора SSD; Documentation/admin-guide/md.rst; Documentation/admin-guide/device-mapper/ | — (не перепроверено) |
| 46.2 | High | Путь I/O (диаграмма и Итог 3) | Page Cache → I/O Scheduler → Device Mapper → RAID → диск | dm-linear и md — bio-based слои: scheduler присоединён к request queue нижнего физического устройства и работает ПОСЛЕ dm/md; у dm-устройств обычно none; «для RAID выбор scheduler критичен» — настраивается на member-дисках | Documentation/admin-guide/sysctl/vm.rst; mm/filemap.c, mm/page-writeback.c; Documentation/admin-guide/md.rst; Documentation/admin-guide/device-mapper/ | — (не перепроверено) |
| 46.3 | High | Код GroupCommitter | notify на КАЖДЫЙ Append → flusher делает flush+fsync немедленно | группировки нет (sync на каждую запись), вызов Append не ждёт durability (не настоящий group commit), mu удерживается на время fsync (стопорит все Append), гонка Close/flusher, Printf сообщает «зафиксированы» до фактического Sync | man 2 fsync; Documentation/filesystems/ext4/; fs/jbd2 | — (не перепроверено) |
| 46.4 | Medium | Write penalty | — | не упомянуты full-stripe write (без RMW), stripe cache, write hole в RAID5/6 (md bitmap/journal), URE при ребилде больших дисков | man 2 fsync; Documentation/filesystems/ext4/; fs/jbd2; Documentation/admin-guide/md.rst; Documentation/admin-guide/device-mapper/ | — (не перепроверено) |
| 46.5 | Medium | Snapshots | «snapshot split», «каждый fsync удваивает нагрузку» | термин выдуман; описан только legacy COW-snapshot (copy-on-first-write chunk); thin-snapshots (dm-thin) работают иначе (break-sharing); не упомянуты инвалидация legacy-снимка при переполнении COW и ошибки I/O при заполнении thin-pool | man 2 fsync; Documentation/filesystems/ext4/; fs/jbd2 | — (не перепроверено) |
| 46.6 | Medium | BBWC gotcha | «если батарея неисправна, данные потеряны» — и в предыдущем абзаце «контроллер переключается в write-through» | противоречие; потеря возможна при политике «Always Write Back»/включённом кэше дисков без PLP, а не при штатном BBU-fallback | Intel SDM / AMD APM, Optimization Manual | — (не перепроверено) |
| 46.7 | Low | omission/CLI | — | megacli устарел (StorCLI/perccli); не упомянуты dm-crypt/dm-cache/dm-integrity, mdadm write-intent bitmap, «RAID ≠ backup», Btrfs/ZFS-RAID | Documentation/admin-guide/md.rst; Documentation/admin-guide/device-mapper/ | — (не перепроверено) |
| 46.8 | Low | рекомендация O_DIRECT для логов | — | выравнивание под stripe width оправдано только для больших последовательных записей | man 2 open (O_DIRECT); statx(2) | — (не перепроверено) |

### Статья 47. Сетевая подсистема ОС

| № | Приор. | Раздел | Утверждение | Проблема / что проверить | Источник | Статус |
|---|:---:|---|---|---|---|---|
| 47.1 | High | somaxconn/Backlog | «net.ListenConfig.Backlog»; «somaxconn по умолчанию 128» | в ListenConfig нет поля Backlog; Go сам берёт backlog из /proc/sys/net/core/somaxconn (maxListenerBacklog); default somaxconn = 4096 с ядра 5.4 (128 — до 5.3) | man 2 listen; Documentation/networking/ip-sysctl.rst; net/ipv4/tcp_input.c | ✔ src |
| 47.2 | High | Interview KeepAlive | «ListenConfig.KeepAlive лишь включает SO_KEEPALIVE; интервалы из sysctl (7200 с); сервер держит мёртвое соединение 2 часа» | с Go 1.13 KeepAlive задаёт TCP_KEEPIDLE и TCP_KEEPINTVL (по умолчанию 15 с, включён по умолчанию у Dialer/Listener); в Go 1.23 добавлен net.KeepAliveConfig (Idle/Interval/Count) | net package docs; Go 1.13/1.23 notes | ✔ src |
| 47.3 | High | Код keepAliveControl | импорт `time` не используется | не компилируется; константы 4/5 в обход syscall.TCP_KEEPIDLE; нет TCP_KEEPCNT | net/dial.go, net/tcpsockopt_posix.go; man 7 tcp; go build / go vet на листинге | — (не перепроверено) |
| 47.4 | Medium | Слои | «NAPI (interrupt coalescing)» | NAPI — режим опроса (polling) для снижения IRQ; interrupt coalescing/moderation — отдельная аппаратная функция NIC | Documentation/networking/napi.rst, skbuff.rst | — (не перепроверено) |
| 47.5 | Medium | п.5 | «в LISTEN пакет помещается в receive_queue» | для LISTEN-сокета SYN→request_sock (SYN queue), ACK→accept queue; receive_queue — только для ESTABLISHED (и backlog при блокировке сокета пользователем) | man 2 listen; Documentation/networking/ip-sysctl.rst; net/ipv4/tcp_input.c | — (не перепроверено) |
| 47.6 | Medium | Gotcha копирование | «до 60% CPU на 40G/100G»; DMA считается «копированием»; «стандартный net Go пока использует recvmsg» | DMA не нагружает CPU; число без источника; не упомянуты TCP_ZEROCOPY_RECEIVE (4.18), MSG_ZEROCOPY, GRO/LRO, RSS/RPS | исходники Go (runtime/net/os/syscall), release notes версии; исходники и Documentation/ ядра, man-страницы (man 2/7) | — (не перепроверено) |
| 47.7 | Medium | Переполнение receive_queue | «ядро молча дропает пакеты, падает окно TCP» | для TCP при заполнении rcvbuf окно сжимается (flow control), дропы — только при превышении лимитов (TCPRcvQDrop); молчаливые дропы характерны для UDP (RcvbufErrors) | исходники и Documentation/ ядра, man-страницы (man 2/7) | — (не перепроверено) |
| 47.8 | Medium | omission | — | nf_conntrack_max (частая причина дропов), RSS/RPS/XPS/IRQ affinity, GRO/GSO/TSO, softnet_stat/ethtool -S, netdev_max_backlog, BBR, SO_REUSEPORT | man 2 sched_setaffinity/mbind; Documentation/admin-guide/mm/numa_memory_policy.rst; Documentation/networking/napi.rst, skbuff.rst | — (не перепроверено) |
| 47.9 | Low | Эпиграф / «80%» | «свободная мысль в духе Bell Labs»; «на 80% определяются ядром» | вымысел/число без источника | исходники и Documentation/ ядра, man-страницы (man 2/7) | — (не перепроверено) |
| 47.10 | Low | Mermaid | `NIC["…:::process 10G…"]`, `L2["…:::process"]` | :::class внутри кавычек (см. выше) | Mermaid Live Editor; повторная сборка (builder/audit_all.py) | — (не перепроверено) |
| 47.11 | Low | Путь пакета п.3 | «функция драйвера net_rx_action; budget 64» | net_rx_action — softirq-обработчик ядра; драйвер даёт ->poll(); budget: netdev_budget=300 на softirq, napi weight=64; не упомянуты GRO и XDP (до аллокации skb); пакетные данные — page_pool/page_frag | man 2 select/poll; fs/select.c; Documentation/networking/napi.rst, skbuff.rst | — (не перепроверено) |
| 47.12 | Low | п.6 | «recvmsg» | Go-TCP читает через read(2); recvmsg/recvfrom — для UDP/UnixConn с OOB | исходники и Documentation/ ядра, man-страницы (man 2/7) | — (не перепроверено) |
| 47.13 | Low | sk_buff | «skb_frag — страницы подкачки» | page fragments (skb_shared_info.frags), не swap | Documentation/networking/napi.rst, skbuff.rst | — (не перепроверено) |
| 47.14 | Low | SO_RCVBUF | схема «×2, затем обрезка rmem_max» | сначала min(val, rmem_max), затем ×2; не упомянуто: SetReadBuffer/SetWriteBuffer отключают TCP buffer autotuning (может ухудшить throughput) | исходники и Documentation/ ядра, man-страницы (man 2/7) | — (не перепроверено) |
| 47.15 | Low | Checksum | «ошибки checksum error в логах Go-сервиса» | Go их не видит: ядро молча дропает (InCsumErrors в /proc/net/snmp) | Documentation/networking/napi.rst, skbuff.rst | — (не перепроверено) |
| 47.16 | Low | netpoll | «runtime.park», «дескрипторы пулятся для кэшей» | gopark; pollcache — аллокатор pollDesc, к L1/L2 отношения не имеет | runtime/netpoll.go, netpoll_epoll.go; man 7 epoll; man 2 open/fcntl; os/file_unix.go | — (не перепроверено) |

### Статья 48. Socket API и жизненный цикл TCP-соединения

| № | Приор. | Раздел | Утверждение | Проблема / что проверить | Источник | Статус |
|---|:---:|---|---|---|---|---|
| 48.1 | High | Код сервера | импорт `fmt` не используется | не компилируется; «graceful shutdown» не ждёт активные conn; `ne.Timeout()` для Accept — неверная проверка (Temporary/EMFILE-backoff; net/http делает сам) | go build / go vet на листинге | — (не перепроверено) |
| 48.2 | Medium | Очереди | `syn_table`, `sk_read_queue`, `sk_rmembuf` | syn_table удалена в 4.4 (request sock хранятся в ehash, reqsk_queue); очередь называется sk_receive_queue (ст.47: receive_queue); sk_rmembuf не существует; sk_rmem_alloc — счётчик, а не очередь | первоисточник по теме (спецификация/документация) | — (не перепроверено) |
| 48.3 | Medium | Gotcha accept queue | «при повторной попытке ECONNREFUSED»; «передают backlog через ListenConfig» | RST только при tcp_abort_on_overflow=1; ListenConfig.Backlog нет; не упомянуто: при заполненной accept queue ядро дропает и НОВЫЕ SYN (ретрансмиты клиента 1/3/7 с) — типичный симптом | man 2 listen; Documentation/networking/ip-sysctl.rst; net/ipv4/tcp_input.c | ✔ src |
| 48.4 | Medium | Под капотом Go | «регистрация fd в epoll после EAGAIN»; `runtime.park`; callback `netpollwake` | регистрация при создании fd; gopark; netpollwake не существует (ep_poll_callback в ядре) — повтор ст.35/36 | runtime/netpoll.go, netpoll_epoll.go; man 7 epoll; runtime/runtime2.go (gobuf); cmd/compile/abi-internal.md | — (не перепроверено) |
| 48.5 | Medium | Interview | «структура poller» | pollDesc с таймерами rt/wt (в остальном описание верно — без timerfd) | runtime/netpoll.go, netpoll_epoll.go; man 7 epoll | — (не перепроверено) |
| 48.6 | Medium | SO_REUSEPORT | «Go по умолчанию включает SO_REUSEADDR и SO_REUSEPORT» (и Итог 3) | по умолчанию только SO_REUSEADDR (для listener); REUSEPORT нужно включать через ListenConfig.Control (ст.50 говорит верно); «аппаратно балансирует» — программно по хэшу | net/sockopt_linux.go, net/tcpsock.go; man 7 tcp/socket | ✔ src |
| 48.7 | Low | Введение | `[[5. Учебник по Go (Основы и синтаксис)]].net` | висячая вики-ссылка, склеенная с «.net» (такого модуля нет) | Mermaid Live Editor; повторная сборка (builder/audit_all.py) | — (не перепроверено) |
| 48.8 | Low | Под капотом | «f_op->socket» | такого поля нет: file_operations socket_file_ops, file->private_data → struct socket | исходники и Documentation/ ядра, man-страницы (man 2/7) | — (не перепроверено) |
| 48.9 | Low | accept() | «таймеры (TCP_TIMEWAIT, DELACK, RTO) инициализируются в accept()» | дочерний сокет создаётся при завершении handshake (tcp_create_openreq_child); accept лишь извлекает | исходники и Documentation/ ядра, man-страницы (man 2/7) | — (не перепроверено) |
| 48.10 | Low | Nagle | — | верно: Go включает TCP_NODELAY по умолчанию (противоречит ст.22 «TCP_NODELAY как оптимизация») | net/sockopt_linux.go, net/tcpsock.go; man 7 tcp/socket | ✔ src |
| 48.11 | Low | TIME_WAIT | — | «2MSL = 60 с в Linux» верно здесь, но ст.50 говорит иначе (см. [50]) | RFC 9293; Documentation/networking/ip-sysctl.rst; include/net/tcp.h | — (не перепроверено) |

### Статья 49. Backlog, SYN Queue и Accept Queue

| № | Приор. | Раздел | Утверждение | Проблема / что проверить | Источник | Статус |
|---|:---:|---|---|---|---|---|
| 49.1 | Medium | Структуры | `struct listen_sock (backlog, qlen, max_qlen)`, `SOCK_LISTEN`, `syn_table` | listen_sock удалён в 4.4 (lockless listener); сейчас request_sock_queue (rskq_accept_head/tail, qlen, rskq_lock), sk_max_ack_backlog, sk_state==TCP_LISTEN | man 2 listen; Documentation/networking/ip-sysctl.rst; net/ipv4/tcp_input.c | — (не перепроверено) |
| 49.2 | Medium | tcp_max_syn_backlog | «лимит SYN Queue» | с 4.4 длина SYN-очереди ограничена listen backlog (min(backlog, somaxconn)); tcp_max_syn_backlog участвует в решении о syncookies и в 3/4-правиле; упрощение | man 2 listen; Documentation/networking/ip-sysctl.rst; net/ipv4/tcp_input.c | — (не перепроверено) |
| 49.3 | Medium | «listen_lock» | «спинлок; M упирается в него» | имя устарело (rskq_lock/lock_sock); после 4.4 SYN-обработка без блокировки listener; «горутины/M упираются» — недоказано | runtime/os_linux.go (newosproc, cloneFlags) | — (не перепроверено) |
| 49.4 | Medium | Gotcha | «backlog через unix.SetsockoptInt(SOL_SOCKET, 1024, 65535) / SO_MAX_CONN» | такой опции нет; backlog задаётся только listen(2); Go сам вызывает listen(fd, somaxconn); пример (REUSEPORT + бессмысленный setsockopt) не демонстрирует тюнинг; корректно: повторный unix.Listen(fd, n) или собственный сокет + net.FileListener | man 2 listen; Documentation/networking/ip-sysctl.rst; net/ipv4/tcp_input.c | ✔ src |
| 49.5 | Medium | Info CAP_NET_ADMIN | «somaxconn — общесистемная переменная» | net.core.somaxconn namespaced (per-netns); в Kubernetes задаётся через pod securityContext.sysctls | man 2 listen; Documentation/networking/ip-sysctl.rst; net/ipv4/tcp_input.c; man 7 capabilities; syscall.SysProcAttr | — (не перепроверено) |
| 49.6 | Medium | «пауза GC → переполнение accept queue» | — | STW Go GC < 1 мс; реальные причины — CPU starvation/throttling, GOMAXPROCS, блокирующая обработка в accept-цикле | man 2 listen; Documentation/networking/ip-sysctl.rst; net/ipv4/tcp_input.c; runtime/mgc.go; go.dev/doc/gc-guide | — (не перепроверено) |
| 49.7 | Low | SYN cookies | — | не сказано об ограничениях (потеря опций TCP, ECN/SACK/WS частично) | man 2 listen; Documentation/networking/ip-sysctl.rst; net/ipv4/tcp_input.c | — (не перепроверено) |
| 49.8 | Low | TCPListener.File() | `tcpListener.File()` в примере | File() делает dup дескриптора (в Go 1.27.1 netFD.dup без SetNonblock(false)); для тюнинга backlog не нужен; побочные эффекты на старых версиях — проверить | man 2 listen; Documentation/networking/ip-sysctl.rst; net/ipv4/tcp_input.c; man 2 open/fcntl; os/file_unix.go | ✔ src |
| 49.9 | Low | Gotcha «тишина» | «use of closed network connection» как ошибка исчерпания fd | эта ошибка — закрытие listener/conn | первоисточник по теме (спецификация/документация) | — (не перепроверено) |
| 49.10 | Low | perf | `perf trace -e accept,connect` «измерит задержку между handshake и accept» | не видит завершение handshake | man perf/vmstat/iostat; B.Gregg «Linux Performance» | — (не перепроверено) |
| 49.11 | Low | omission | — | dmesg «Possible SYN flooding»; nstat TcpExtListenOverflows/ListenDrops/TCPReqQFullDrop; SO_REUSEPORT+BPF; tcp_synack_retries | man 2 listen; Documentation/networking/ip-sysctl.rst; net/ipv4/tcp_input.c; Documentation/bpf/; cilium/ebpf docs; man 2 bpf | — (не перепроверено) |

### Статья 50. TIME_WAIT, CLOSE_WAIT и проблемы сокетов

| № | Приор. | Раздел | Утверждение | Проблема / что проверить | Источник | Статус |
|---|:---:|---|---|---|---|---|
| 50.1 | High | TIME_WAIT длительность | «MSL=60 с, 2MSL=120 с (иногда 60)»; диаграмма «60–120 сек» | в Linux TCP_TIMEWAIT_LEN = 60 с (константа, не 2MSL=120); ст.48 говорит верно — противоречие | RFC 9293; Documentation/networking/ip-sysctl.rst; include/net/tcp.h | — (не перепроверено) |
| 50.2 | Medium | RFC | «RFC 793» | заменён RFC 9293 (2022) | первоисточник по теме (спецификация/документация) | — (не перепроверено) |
| 50.3 | Medium | Под капотом | «struct tcp_time_wait»; «tcp_death_row — глобальная хеш-таблица»; «tcp_tw_recycle()» | реальные: inet_timewait_sock/tcp_timewait_sock в ehash; tcp_death_row — структура-счётчик (tw_count, sysctl_max_tw_buckets); tcp_tw_recycle — sysctl, удалён в 4.12 (NAT-проблемы) | RFC 9293; Documentation/networking/ip-sysctl.rst; include/net/tcp.h | — (не перепроверено) |
| 50.4 | Medium | Port exhaustion | «28k портов, 500 RPS за минуту» | TIME_WAIT уникален по 4-tuple: порт переиспользуем для других dst; предел — на (dst ip:port); не упомянуты tcp_tw_reuse (=2 loopback-only с 4.19), tcp_max_tw_buckets; Go-специфика: http.Transport MaxIdleConnsPerHost по умолчанию = 2 — главная причина churn | RFC 9293; Documentation/networking/ip-sysctl.rst; include/net/tcp.h | — (не перепроверено) |
| 50.5 | Medium | Interview | «CLOSE_WAIT → паника too many open files» | accept вернёт EMFILE (net/http backoff-retry), не паника (повтор [5]) | RFC 9293; Documentation/networking/ip-sysctl.rst; include/net/tcp.h | — (не перепроверено) |
| 50.6 | Medium | CLOSE_WAIT стратегии | п.3: tcp_fin_timeout «ограничит зависшие сессии» | противоречит абзацу выше (tcp_fin_timeout — только FIN-WAIT-2; CLOSE_WAIT таймаута не имеет) | RFC 9293; Documentation/networking/ip-sysctl.rst; include/net/tcp.h | — (не перепроверено) |
| 50.7 | Low | «100% утечка» | — | CLOSE_WAIT бывает и временным (idle conn в пуле до чтения EOF) | RFC 9293; Documentation/networking/ip-sysctl.rst; include/net/tcp.h | — (не перепроверено) |
| 50.8 | Low | SO_REUSEPORT | «устраняет contention listen_lock» | устаревшее имя; недостатки (переразброс при смене набора listener'ов) не упомянуты | net/sockopt_linux.go, net/tcpsock.go; man 7 tcp/socket | — (не перепроверено) |
| 50.9 | Low | ip_local_port_range=1024–65535 | — | пересекается с портами сервисов; использовать ip_local_reserved_ports; тип совета небезопасен | первоисточник по теме (спецификация/документация) | — (не перепроверено) |
| 50.10 | Low | Стратегия «SO_REUSEADDR» | — | не борьба с TIME_WAIT, а разрешение bind при перезапуске | net/sockopt_linux.go, net/tcpsock.go; man 7 tcp/socket | — (не перепроверено) |

### Статья 51. DNS глазами ОС и libc

| № | Приор. | Раздел | Утверждение | Проблема / что проверить | Источник | Статус |
|---|:---:|---|---|---|---|---|
| 51.1 | High | Режимы netdns | «go по умолчанию на linux, darwin, windows»; «experimentalgo» | на darwin при cgo по умолчанию системный резолвер (libSystem); на Windows — системный GetAddrInfoW; режима experimentalgo нет (реальные значения: go, cgo, 1/2 (debug), комбинации «go+1», «cgo+2»); выбор зависит от conf (nsswitch/resolv.conf/env), а не только от CGO_ENABLED | net package doc «Name Resolution» | ✔ src |
| 51.2 | High | Go-резолвер | «параллельный опрос всех nameserver; первый ответивший побеждает» (текст, диаграмма, итог, sequence-комментарий) | pure-Go резолвер перебирает серверы последовательно (attempts × servers, timeout 5 с по умолчанию, rotate опционально); параллельны только A и AAAA; параллельно опрашивает все серверы musl — наоборот | net/dnsclient_unix.go | ✔ src |
| 51.3 | Medium | glibc | «getaddrinfo читает resolv.conf один раз» | современный glibc (≥2.26) перечитывает при смене mtime (res_init не нужен) | net/dnsclient_unix.go, net/conf.go; man 5 resolv.conf; musl release notes; glibc symbol versioning docs; man 7 libc | — (не перепроверено) |
| 51.4 | Medium | Alpine/musl | «musl не поддерживает ndots, требует порядка строк» | реальные проблемы: musl <1.2.4 без TCP-fallback (усечённые ответы), ограничения search-доменов, параллельный опрос; Interview п.2: «CGO_ENABLED=1 → всегда netcgo» неверно (выбор по conf) | net/dnsclient_unix.go, net/conf.go; man 5 resolv.conf; musl release notes | ✔ src |
| 51.5 | Medium | cgo-резолвер | — | не сказано, что cgo-lookup блокирует потоки (лимит 500 одновременных) | исходники Go (runtime/net/os/syscall), release notes версии | — (не перепроверено) |
| 51.6 | Medium | K8s | — | не упомянуты: 5-секундные задержки из-за гонки conntrack при параллельных A/AAAA (single-request-reopen, NodeLocal DNSCache), CoreDNS autopath; search включает ещё и node-домены (больше NXDOMAIN, ×2 из-за AAAA) | Kubernetes docs (kubelet, QoS, CPU Manager) | ✔ src |
| 51.7 | Low | Эпиграф | «старинная пословица» | мем/хайку (≈2016), не пословица | первоисточник по теме (спецификация/документация) | — (не перепроверено) |
| 51.8 | Low | Введение | «Это решало проблемы с утечками памяти в net/http» | бессмыслица | первоисточник по теме (спецификация/документация) | — (не перепроверено) |
| 51.9 | Low | Конвейер | порядок «/etc/hosts → nsswitch» | сначала nsswitch.conf определяет порядок источников (files, dns) | первоисточник по теме (спецификация/документация) | — (не перепроверено) |
| 51.10 | Low | Mechanical | «Page Fault для таблиц маршрутизации»; «/run/systemd/resolve/resolv.conf — Unix Domain Socket»; дубль фразы «Если в Linux настроен» | файл с upstream-серверами, не сокет; stub — 127.0.0.53:53 UDP/TCP; не упомянут Docker DNS 127.0.0.11 | net/dnsclient_unix.go, net/conf.go; man 5 resolv.conf; musl release notes; man systemd.service, sd_listen_fds(3), sd_notify(3) | — (не перепроверено) |
| 51.11 | Low | omission | — | GODEBUG=netdns=go+1 для отладки; EDNS0 (Go шлёт 1232 Б) при TC; Happy Eyeballs | net/dnsclient_unix.go, net/conf.go; man 5 resolv.conf; musl release notes | ✔ src |

### Статья 52. Ограничения ОС. ulimit, cgroups, quotas

| № | Приор. | Раздел | Утверждение | Проблема / что проверить | Источник | Статус |
|---|:---:|---|---|---|---|---|
| 52.1 | High | Interview | «Go определяет память через sysinfo//proc/meminfo хоста, GC ориентировался на 64 ГБ → запускался поздно» | GC-триггер вычисляется от live heap и GOGC, память хоста не используется; OOM в контейнере — следствие рабочего набора, превышающего limit, а не «невидимости» лимита; GOMEMLIMIT — верно, но мотив описан неправильно | runtime/mgc.go; go.dev/doc/gc-guide; man 5 proc; sysstat docs | — (не перепроверено) |
| 52.2 | High | Go runtime + Итог 3 | «Go не распознаёт cgroup без явных GOMEMLIMIT и GOMAXPROCS»; YAML GOMAXPROCS=2 | с Go 1.25 GOMAXPROCS учитывает cgroup CPU limit автоматически (и динамически); GOMEMLIMIT по-прежнему вручную; также «getrlimit <1024 → рискует» — Go ≥1.19 сам поднимает soft NOFILE до hard | Go 1.19 release notes; runtime/debug/garbage.go; Documentation/admin-guide/cgroup-v2.rst | ✔ src |
| 52.3 | Medium | rlimits | «RLIMIT_AS (или maxrss) — виртуальная или физическая память» | RLIMIT_RSS в Linux не действует; AS — только виртуальное пространство | man 2 getrlimit; syscall/rlimit.go | — (не перепроверено) |
| 52.4 | Medium | K8s requests | «requests.memory → memory.low/min» | kubelet по умолчанию memory.min/low не выставляет (MemoryQoS — alpha, выключен); memory requests = scheduling + oom_score_adj; cpu.requests → cpu.weight (не упомянуто) | Kubernetes docs (kubelet, QoS, CPU Manager) | — (не перепроверено) |
| 52.5 | Medium | omission | — | memory.events (oom_kill), memory.stat, cpu.stat nr_throttled, PSI; project quotas (XFS prjquota — ephemeral-storage в k8s) | Documentation/admin-guide/sysctl/vm.rst; mm/vmscan.c, mm/oom_kill.c | — (не перепроверено) |
| 52.6 | Low | Под капотом | «rlim в task_struct»; «ENFILE или ENOSPC (inode)» | rlimits в signal_struct (общие для thread group); ENFILE — системный file-max; ENOSPC для inode — ФС, не таблица fd | kernel/fork.c; man 2 clone/execve/wait; Documentation/filesystems/vfs.rst; fs/dcache.c | — (не перепроверено) |
| 52.7 | Low | cgroups | «v2 — стандарт в ядрах 5.8+» (ст.53: «5.3+») | v2 стабилен с 4.5; дефолт — Fedora 31/Debian 11/Ubuntu 21.10/RHEL 9; цифры расходятся | Documentation/admin-guide/cgroup-v2.rst | — (не перепроверено) |
| 52.8 | Low | v1 vs v2 | «v1 не учитывал page cache» | memcg v1 заряжал page cache; проблема — атрибуция buffered writeback между blkio и memory | Documentation/admin-guide/sysctl/vm.rst; mm/filemap.c, mm/page-writeback.c | — (не перепроверено) |
| 52.9 | Low | pids.max | «netpoller требует новых потоков» | потоки — для блокирующих syscalls/cgo, не netpoller | runtime/netpoll.go, netpoll_epoll.go; man 7 epoll; Documentation/admin-guide/cgroup-v2.rst | — (не перепроверено) |

### Статья 53. Контейнеры под капотом. namespaces и cgroups

| № | Приор. | Раздел | Утверждение | Проблема / что проверить | Источник | Статус |
|---|:---:|---|---|---|---|---|
| 53.1 | High | Gotcha памяти | «аллокатор Go использует mmap и brk»; `runtime.Grow`; «mmap вернёт ENOMEM → fatal error: out of memory или nil deref» | Go не использует brk; runtime.Grow нет; при упоре в memory.max mmap успешен (память выделяется при page fault) → reclaim → cgroup OOM-kill SIGKILL без трейса; ENOMEM от mmap — лишь при RLIMIT_AS/overcommit=2/max_map_count | man 2 mmap; mm/mmap.c; Documentation/mm/; man 2 brk; runtime/mem_linux.go | ✔ src |
| 53.2 | Medium | Namespaces | «7 типов» | в Linux 8: добавлен time namespace (5.6); user ns хранится в cred, а не в nsproxy | man 7 namespaces; man 2 pivot_root | — (не перепроверено) |
| 53.3 | Medium | Цепочка запуска | «pivot_root заменяет корень текущего процесса»; «PID в cgroup.procs в …/cpu.max» | pivot_root меняет root mount namespace; путь/файлы перепутаны; runc создаёт cgroup и размещает процесс раньше, затем mounts/pivot_root/seccomp/caps | Documentation/admin-guide/cgroup-v2.rst; man 7 namespaces; man 2 pivot_root | — (не перепроверено) |
| 53.4 | Medium | Interview п.1 | «docker run без root благодаря USER namespace; UID 0→1000» | по умолчанию Docker userns НЕ использует (root контейнера = root хоста с урезанными capabilities); userns-remap/rootless — опционально, маппинг на subuid-диапазон, не «1000» | man 7 namespaces; man 2 pivot_root; man 2 setuid; syscall/syscall_linux.go | — (не перепроверено) |
| 53.5 | Medium | omission | — | seccomp, capabilities, LSM, overlayfs, OCI/runc/shim, Kata/gVisor (общее ядро = граница доверия), SO_BINDTODEVICE требует CAP_NET_RAW | man 7 capabilities; syscall.SysProcAttr; Documentation/admin-guide/LSM/; SELinux/AppArmor docs; Docker seccomp/AppArmor docs | — (не перепроверено) |
| 53.6 | Low | Вступление | «нет виртуальной памяти, отличной от физической хоста»; «нет гипертрейдинга гостевых ОС»; «0 оверхеда» | бессмыслица; есть оверхед overlayfs/veth/netfilter/seccomp | man 7 namespaces; man 2 pivot_root; Documentation/admin-guide/LSM/; SELinux/AppArmor docs; Docker seccomp/AppArmor docs | — (не перепроверено) |
| 53.7 | Low | cgroups | «v2 стандарт с ядра 5.3+» | см. [52] | Documentation/admin-guide/cgroup-v2.rst | — (не перепроверено) |
| 53.8 | Low | п.3 | «ядро может вернуть EAGAIN при переключении потока (cpu.max)» | throttling не возвращает ошибок | Documentation/admin-guide/cgroup-v2.rst | — (не перепроверено) |
| 53.9 | Low | Код | — | на хосте root-cgroup не содержит memory.current/max → программа молча ничего не выведет; Printf-разрывы | Documentation/admin-guide/cgroup-v2.rst; go build / go vet на листинге | — (не перепроверено) |

### Статья 54. Изоляция процессов в Linux

| № | Приор. | Раздел | Утверждение | Проблема / что проверить | Источник | Статус |
|---|:---:|---|---|---|---|---|
| 54.1 | High | PID 1 в Go | «SIGTERM без Notify будет молча проигнорирован; процесс работает до SIGKILL» | Go-runtime ставит обработчик; без Notify при SIGTERM вызывает dieFromSignal: raise(SIG_DFL) (ядро игнорирует для init), затем exit(128+sig) (в Go 1.27.1: «PID 1 immune to signals … exit(128+sig)») — процесс завершается немедленно (код 143) и без graceful shutdown; «игнорируется» верно для C/Python-программ без обработчика | runtime/signal_unix.go dieFromSignal (✔ прочитано в Go 1.27.1) | ✔ src |
| 54.2 | Medium | Структуры | «struct namespace», Mount→fs_struct, Cgroup→struct cgroup | нет struct namespace (mnt_namespace); fs_struct — root/cwd процесса; для cgroup-ns — cgroup_namespace; time namespace (5.6) не упомянут (8 типов) | Documentation/admin-guide/cgroup-v2.rst; man 7 namespaces; man 2 pivot_root | — (не перепроверено) |
| 54.3 | Medium | Согласованность модуля | §1 говорит: Go 1.25 нативно учитывает cgroup (GODEBUG=containermaxprocs); ст.8, 52, 53 утверждают, что нужен automaxprocs/GOMAXPROCS вручную | противоречие между статьями; в самой ст.54 «до 1.24» верно, но итог 3 «требуется явная настройка» устарел | Documentation/admin-guide/cgroup-v2.rst; runtime/debug.go; runtime/cgroup_linux.go; Go 1.25 release notes | ✔ src |
| 54.4 | Medium | Q2 | «Go аллоцирует через mmap() и brk()»; «libcontainer подписывается на /sys/fs/cgroup/memory/oom.event» | brk Go не использует; события: v1 memory.oom_control+eventfd, v2 memory.events (inotify); «oom.event» нет | man 2 mmap; mm/mmap.c; Documentation/mm/; man 2 brk; runtime/mem_linux.go | ✔ src |
| 54.5 | Low | Эпиграф | — | выдуманный «принцип» | первоисточник по теме (спецификация/документация) | — (не перепроверено) |
| 54.6 | Low | cgroups internals | «sched_tick проверяет квоту», «__alloc_pages сверяется с memory.max» | CFS bandwidth — hrtimer'ы period/slack и учёт в update_curr (throttled_list у cfs_rq); memcg-заряд — mem_cgroup_charge/try_charge при fault/page-cache-add, не в __alloc_pages | Documentation/admin-guide/cgroup-v2.rst | — (не перепроверено) |
| 54.7 | Low | EMFILE/ENOSPC | «исчерпали квоту /proc и /sys контейнера» | бессмыслица; ENOSPC для сокетов/inotify бывает (лимит inotify watches) | man 5 proc; sysstat docs | — (не перепроверено) |
| 54.8 | Low | LaTeX | — | $$ \text{…} $$ с TAB-порчей (системно) | Mermaid Live Editor; повторная сборка (builder/audit_all.py) | — (не перепроверено) |

### Статья 55. Виртуальные машины и гипервизоры

| № | Приор. | Раздел | Утверждение | Проблема / что проверить | Источник | Статус |
|---|:---:|---|---|---|---|---|
| 55.1 | Medium | Диаграмма | QEMU в «Root Mode / Ring 0» | QEMU — пользовательский процесс хоста (Ring 3 host), kvm.ko — ядро; AMD-V использует VMCB, не VMCS | Intel SDM Vol.3 (VMX); Documentation/virt/kvm/; virtio spec | — (не перепроверено) |
| 55.2 | Medium | Код pinning | «привязка потока к ядру 0 — защита от миграции vCPU»; «физическое ядро 0» | гостевой affinity не мешает гипервизору мигрировать vCPU по физическим ядрам (нужен pinning на хосте); CPU 0 — логический vCPU | man 2 sched_setaffinity/mbind; Documentation/admin-guide/mm/numa_memory_policy.rst; Intel SDM Vol.3 (VMX); Documentation/virt/kvm/; virtio spec | — (не перепроверено) |
| 55.3 | Medium | omission | — | steal time (%st) как главный индикатор oversubscription для Go; kvm-clock/clocksource: на Xen/без TSC clock_gettime идёт syscall'ом без vDSO — ломает тезис «time.Now почти бесплатен» (ст.2/23); Firecracker/microVM (ст.4), Nitro, SR-IOV/VFIO, balloon/KSM, confidential VM (SEV/TDX) | man 7 vdso; runtime/vdso_linux.go; firecracker docs/SPECIFICATION.md | — (не перепроверено) |
| 55.4 | Low | Введение | «в 95% случаев контейнер внутри ВМ» | цифра без источника | первоисточник по теме (спецификация/документация) | — (не перепроверено) |
| 55.5 | Low | Interview п.1/4 | «гостевое ядро перехватывает syscall в своей IDT» | SYSCALL идёт через MSR LSTAR, не IDT (повтор [22]) | Intel SDM (SYSCALL/SYSRET); arch/x86/entry/entry_64.S | — (не перепроверено) |
| 55.6 | Low | VM-exit cost | «сотни тактов» | типично ≈1000+ тактов на exit/entry round-trip (зависит от CPU/причины) | runtime/os_linux.go (newosproc, cloneFlags) | — (не перепроверено) |
| 55.7 | Low | Hugepages | «снижает промахи TLB в десятки раз» | гипербола | Intel SDM Vol.3 §4.10 (TLB); Documentation/arch/x86/tlb.rst; Documentation/admin-guide/mm/transhuge.rst, hugetlbpage.rst | — (не перепроверено) |

### Статья 56. Безопасность ОС. Права доступа, users, groups

| № | Приор. | Раздел | Утверждение | Проблема / что проверить | Источник | Статус |
|---|:---:|---|---|---|---|---|
| 56.1 | High | Алгоритм проверки | «шаг 1: если EUID==0 — безусловно разрешено» | в современном ядре обход DAC даёт capability CAP_DAC_OVERRIDE/CAP_DAC_READ_SEARCH (capable()), не «uid==0»; root без этих caps (cap_drop ALL в контейнере) доступ не обходит; также не учтены ACL, immutable/append-only атрибуты, LSM | man 7 capabilities; syscall.SysProcAttr; Documentation/admin-guide/LSM/; SELinux/AppArmor docs; Docker seccomp/AppArmor docs | — (не перепроверено) |
| 56.2 | Medium | Interview | «PCI DSS/SOC2/ISO 27001 категорически запрещают запуск сервисов от root» | требуют least privilege, прямого запрета нет | первоисточник по теме (спецификация/документация) | — (не перепроверено) |
| 56.3 | Low | Права | Sticky: «только владелец файла или root» | также владелец каталога; omission umask (MkdirAll(0750) зависит от umask) | первоисточник по теме (спецификация/документация) | — (не перепроверено) |
| 56.4 | Low | Mechanical | «openat на горячем пути — десятки нс» | порядка 1–2 мкс (syscall+path walk+file alloc) | исходники Go (runtime/net/os/syscall), release notes версии; воспроизводимое измерение (lmbench/perf/fio) или публикация с методикой | — (не перепроверено) |
| 56.5 | Low | Go-код | `info` берётся ДО Chmod, потом проверяется «permissions mismatch» | сравнивается устаревшая информация; Printf-разрыв; /var/run — tmpfs, нужен RuntimeDirectory= | go build / go vet на листинге | — (не перепроверено) |
| 56.6 | Low | Octal | «755 десятичное = 01363 → Sticky и SGID»; `os.ModeSticky = 010000000` | 755₁₀ = 01363₈ → sticky (1), SGID не выставлен; ModeSticky = 1<<20 (0o4000000); 0o10000000 — ModeCharDevice | исходники Go (runtime/net/os/syscall), release notes версии | — (не перепроверено) |
| 56.7 | Low | Go setuid | «в Go нет Setuid; используйте syscall.AllThreadsSyscall … либо x/sys/unix принудительно рассылают всем потокам» | с Go 1.16 syscall.Setuid/Setgid/Setgroups/Setresuid на Linux действуют на все потоки (через AllThreadsSyscall; x/sys/unix.Setuid — тонкая обёртка над syscall.Setuid, т.е. тоже на все потоки); AllThreadsSyscall вручную не нужен (ст.57 использует syscall.Setuid правильно); не упомянут syscall.SysProcAttr.Credential для дочерних процессов | man 2 setuid; syscall/syscall_linux.go | ✔ src |
| 56.8 | Low | Пример sequence | «root читает /etc/shadow как конфиг/ключи» | странный пример (shadow — не секреты приложения) | воспроизвести: go build / go vet | — (не перепроверено) |
| 56.9 | Low | omission | — | net.ipv4.ip_unprivileged_port_start (с 4.11; в Docker ≥20.10 =0 внутри контейнера), no_new_privs, ambient caps, setcap, systemd User=/AmbientCapabilities= | man 7 capabilities; syscall.SysProcAttr; man systemd.service, sd_listen_fds(3), sd_notify(3) | — (не перепроверено) |

### Статья 57. ACL, capabilities и привилегии процессов

| № | Приор. | Раздел | Утверждение | Проблема / что проверить | Источник | Статус |
|---|:---:|---|---|---|---|---|
| 57.1 | High | Gotcha execve | «capabilities не наследуются при os/exec, если не установлен флаг NoSetuid/NoSetgid или Inheritable» | таких флагов в SysProcAttr нет; корректный API — SysProcAttr.AmbientCaps ([]uintptr, Go 1.9+); наследование определяется формулой P'(permitted)=…; для non-root нужны ambient или file caps | kernel/fork.c; man 2 clone/execve/wait; man 7 capabilities; syscall.SysProcAttr | ✔ src |
| 57.2 | Medium | Capabilities | «CAP_DAC_OVERRIDE — аналог chmod для root»; «привязаны к исполняемому файлу, а не к пользователю» | DAC_OVERRIDE — обход проверок rwx; capabilities — атрибут потока/credentials, file caps — лишь способ их получения при exec; формулы permitted/inheritable/effective для файла не объяснены | man 7 capabilities; syscall.SysProcAttr | — (не перепроверено) |
| 57.3 | Medium | Info | «capset/prctl требует cred_guard_mutex → конкуренция у приложений с os.Setuid/os.Setgid» | os.Setuid нет (см. ст.56); cred_guard_mutex — exec/ptrace; утверждение выдумано | man 2 setuid; syscall/syscall_linux.go | — (не перепроверено) |
| 57.4 | Medium | Код drop | «Очищаем effective capabilities … syscall.CAP_CLEAR» | такой константы нет; при смене euid 0→≠0 ядро само сбрасывает caps (если не SECBIT_KEEP_CAPS/ambient); комментарий вводит в заблуждение | man 7 capabilities; syscall.SysProcAttr | — (не перепроверено) |
| 57.5 | Medium | omission | — | как дать Go-бинарнику NET_BIND_SERVICE: setcap cap_net_bind_service=+ep (слетает при пересборке/копировании), K8s securityContext.capabilities.add (для non-root без ambient не действует — известная проблема kubernetes#56374), sysctl ip_unprivileged_port_start, systemd AmbientCapabilities=; no_new_privs/AT_SECURE | man 7 capabilities; syscall.SysProcAttr; man systemd.service, sd_listen_fds(3), sd_notify(3) | — (не перепроверено) |
| 57.6 | Low | ACL | «парсинг ACL при каждом openat; в Go ощущается через os.Stat задержкой» | ACL кэшируется в inode (i_acl); эффект на Go не показан; default ACL (system.posix_acl_default) не упомянут | man 5 acl; Documentation/filesystems/ | — (не перепроверено) |
| 57.7 | Low | Sequence/Diagram | порядок ACL → LSM(security_capable) → EPERM; «errno = -EACCES» | DAC (generic_permission) → capable-обход → LSM hooks; errno положительный; LSM обычно EACCES | Documentation/admin-guide/LSM/; SELinux/AppArmor docs; Docker seccomp/AppArmor docs; man 5 acl; Documentation/filesystems/ | — (не перепроверено) |
| 57.8 | Low | Interview | «setuid даёт UID=0» | euid владельца файла (не обязательно 0); `github.com/capabilities/cap` не существует (реальные: syndtr/gocapability, kernel.org/pub/linux/libs/security/libcap/cap) | man 2 setuid; syscall/syscall_linux.go | — (не перепроверено) |

### Статья 58. SELinux и AppArmor

| № | Приор. | Раздел | Утверждение | Проблема / что проверить | Источник | Статус |
|---|:---:|---|---|---|---|---|
| 58.1 | High | Код dropPrivileges | `unix.CapHeader/CapData`; Capset(0) затем Capset(NET_BIND_SERVICE); «переключаемся на non-root» → `os.Chown(".", 1000, 1000)` | типы — unix.CapUserHeader/CapUserData (v3 требует массив из 2 CapUserData); после обнуления permitted поднять caps нельзя (EPERM); os.Chown меняет владельца текущего каталога, а не UID процесса — нужен syscall.Setuid; пример неработоспособен и вводит в заблуждение | man 2 setuid; syscall/syscall_linux.go; runtime/os_linux.go (newosproc, cloneFlags) | ✔ src |
| 58.2 | High | Gotcha docker-default | «блокирует ~44 syscalls (mount, ptrace) и /proc/sys; чтение /proc/self/status и pprof дадут EACCES» | ~44 syscalls блокирует seccomp-профиль, а не AppArmor; docker-default AppArmor запрещает mount, запись в /proc/sys, ptrace чужих профилей; чтение /proc/self/status и runtime/pprof разрешены; --cap-add=SYS_PTRACE нужен для strace/dlv attach | net/http/pprof/pprof.go; runtime/pprof; man 2 ptrace; strace(1) | — (не перепроверено) |
| 58.3 | Medium | SELinux | «при каждом обращении VFS вызывает getxattr() и сверяет с AVC» | метка читается из xattr один раз при инициализации inode (inode_doinit) и хранится в inode security blob; AVC кэширует решения; Interview «чтение xattr в каждой проверке» — неверно | Documentation/filesystems/vfs.rst; fs/dcache.c; Documentation/admin-guide/LSM/; SELinux/AppArmor docs; Docker seccomp/AppArmor docs | — (не перепроверено) |
| 58.4 | Medium | AppArmor | «стандарт де-факто в Kubernetes» | K8s не привязан к AppArmor; на RHEL/Fedora/OpenShift — SELinux; AppArmor применяется, если включён на хосте (Ubuntu/Debian/SUSE) | Documentation/admin-guide/LSM/; SELinux/AppArmor docs; Docker seccomp/AppArmor docs; Kubernetes docs (kubelet, QoS, CPU Manager) | — (не перепроверено) |
| 58.5 | Medium | Хэш-профиль | «profile /usr/bin/myapp sha256:abc123 { … }» | такого синтаксиса AppArmor нет (привязка по пути/атрибутам xattr/attachment, не по хэшу) — выдумка | Documentation/admin-guide/LSM/; SELinux/AppArmor docs; Docker seccomp/AppArmor docs; man 5 acl; Documentation/filesystems/ | — (не перепроверено) |
| 58.6 | Medium | Graceful shutdown | «SIGTERM и SIGKILL … MAC не влияет на маршрутизацию сигналов» | SIGKILL перехватить нельзя; LSM имеет хук task_kill (SELinux: permission process:signal) — MAC может ограничивать сигналы | man 7 signal; os/signal doc; runtime/signal_unix.go; runtime/os_linux.go (newosproc, cloneFlags) | — (не перепроверено) |
| 58.7 | Medium | omission | — | seccomp; контейнерные SELinux-метки (container_t, MCS, :z/:Z на bind-mount) — частая причина EACCES в Docker/Podman на RHEL; AppArmor в K8s (securityContext.appArmorProfile GA 1.30); Landlock (5.13, go-landlock); audit2allow «не применять вслепую»; SELinux booleans; `sepolicy generate` | Documentation/admin-guide/LSM/; SELinux/AppArmor docs; Docker seccomp/AppArmor docs; man 2 prctl (PR_SET_CHILD_SUBREAPER); Docker/containerd docs | — (не перепроверено) |
| 58.8 | Low | LSM | «~5–10 нс на хук» | оценка без источника; в 6.x хуки через static calls | Documentation/admin-guide/LSM/; SELinux/AppArmor docs; Docker seccomp/AppArmor docs; runtime/os_linux.go (newosproc, cloneFlags) | — (не перепроверено) |
| 58.9 | Low | Профиль | `/var/log/myapp w,` «писать в директорию» | это файл; для каталога `/var/log/myapp/** w,`; нет capability net_bind_service | man 7 capabilities; syscall.SysProcAttr | — (не перепроверено) |
| 58.10 | Low | Interview perf | «Permissive — накладные пренебрежимо малы; Enforcing 10–50 нс» | в permissive продолжается оценка AVC и аудит-логирование (может быть дорого при потоке denials); цифры без источника | man perf/vmstat/iostat; B.Gregg «Linux Performance» | — (не перепроверено) |

### Статья 59. Crash Dump, Core Dump и анализ падений

| № | Приор. | Раздел | Утверждение | Проблема / что проверить | Источник | Статус |
|---|:---:|---|---|---|---|---|
| 59.1 | High | Go и core dump | вся логика: «если рантайм бессилен — ядро делает дамп»; GOTRACEBACK не упомянут | по умолчанию Go даже при фатальных сигналах/`fatal error` печатает трейс и завершается exit(2) без core; core-dump включается GOTRACEBACK=crash (или debug.SetTraceback("crash")), SIGQUIT/SIGABRT тоже exit(2) без него; для живого процесса — gcore; runtime/debug.WriteHeapDump | runtime/extern.go GOTRACEBACK | ✔ src |
| 59.2 | High | Interview: утечки | «dlv core … команда heap» | у Delve нет команды heap; для анализа core Go — golang.org/x/debug/cmd/viewcore (histogram/objects/…); mspan/mcentral вручную разбирать нереально | runtime/mheap.go, runtime/sizeclasses.go, runtime/malloc.go | — (не перепроверено) |
| 59.3 | Medium | Under hood Go | «с Go 1.11 дескрипторы горутин в управляемой куче»; «нет таблицы горутин» | g всегда аллоцировались в куче; есть глобальный runtime.allgs, по которому отладчики находят горутины; версия 1.11 нерелевантна | man 2 open/fcntl; os/file_unix.go; man 5 elf; Documentation/arch/x86/x86_64/mm.rst | ✔ src |
| 59.4 | Medium | core_pattern | `%p %u %s %t %c %h %E` | реальный шаблон systemd: `%P %u %g %s %t %c %h`; core_pattern глобален для хоста (не namespaced) — в K8s дампы контейнеров уходят в handler хоста; не упомянуты coredump_filter, MADV_DONTDUMP (уменьшение размера) | man 5 core; runtime/extern.go (GOTRACEBACK) | — (не перепроверено) |
| 59.5 | Medium | Ловушка 1 | «kernel.core_uses_pid / vm.core_uses_pid=0 (рекомендуется 1)» | параметр kernel.core_uses_pid; vm.core_uses_pid нет; противоречие в самой фразе | первоисточник по теме (спецификация/документация) | — (не перепроверено) |
| 59.6 | Medium | Сжатие | `kernel.core_pattern = \|/usr/bin/bzip2 > /var/crash/core.%e.%p.bz2` | pipe-handler запускается без shell — `>` не сработает; нужен скрипт-обёртка; bzip2 слишком медленный (блокирует завершение процесса), лучше zstd/lz4 | man 5 core; runtime/extern.go (GOTRACEBACK) | — (не перепроверено) |
| 59.7 | Low | Введение | «теряете до 80% информации» | цифра выдумана; «регистры всех физических ядер» — регистры каждого потока | runtime/runtime2.go (gobuf); cmd/compile/abi-internal.md | — (не перепроверено) |
| 59.8 | Low | VMA | «rb-tree и список» | maple tree с 6.1 | man 2 mmap; mm/mmap.c; Documentation/mm/ | — (не перепроверено) |
| 59.9 | Low | Ловушка 3 | «зависание write в сокет → дамп … D-state» | путано: задержка возникает, когда handler/диск/NFS не вычитывают поток | исходники и Documentation/ ядра, man-страницы (man 2/7) | — (не перепроверено) |
| 59.10 | Low | Инструменты | GDB без оговорки | Go-документация: поддержка GDB ограничена, предпочтительнее Delve; для локальных переменных нужна сборка с -gcflags="all=-N -l" | исходники Go (runtime/net/os/syscall), release notes версии | — (не перепроверено) |
| 59.11 | Low | omission | — | сохранение данных при аварии: kernel.core_pipe_limit, `coredumpctl --debugger=dlv`, Docker/K8s ulimit -c | man 2 getrlimit; syscall/rlimit.go; man 5 core; runtime/extern.go (GOTRACEBACK) | — (не перепроверено) |

### Статья 60. perf, top, vmstat, iostat и другие инструменты Linux

| № | Приор. | Раздел | Утверждение | Проблема / что проверить | Источник | Статус |
|---|:---:|---|---|---|---|---|
| 60.1 | High | Gotcha perf+Go | «Исторически perf не мог раскручивать стеки Go из-за сегментированных стеков»; рекомендации «-buildmode=pie», GOEXPERIMENT=strictfipsruntime, GODEBUG=gctrace/asyncpreempt | frame pointers в Go включены на amd64 с 1.7 (arm64 — 1.12) — perf -g (fp) работает; сегментированных стеков с 1.3 нет; перечисленные флаги к раскрутке отношения не имеют; противоречит ст.20 («FP отключён, нужен GOEXPERIMENT=framepointer») | man perf/vmstat/iostat; B.Gregg «Linux Performance»; man 5 elf; Documentation/arch/x86/x86_64/mm.rst | ✔ src |
| 60.2 | Medium | %sy gotcha | «блокирующие сетевые вызовы net/http → частый сон/пробуждение потоков → %sy» | сеть в Go неблокирующая (netpoller); %sy от syscalls/futex/page faults/softirq | man 2 futex; runtime/lock_futex.go, sync/mutex.go; runtime/netpoll.go, netpoll_epoll.go; man 7 epoll | — (не перепроверено) |
| 60.3 | Medium | vmstat | «r > GOMAXPROCS = нехватка CPU», «cs — переход Ring3↔Ring0», «b — мьютексы/каналы», Interview «b высок → диск, сеть или мьютекс» | r сравнивают с числом CPU; syscalls не считаются в cs; b — только D-state (диск/NFS/ядерные ожидания), сетевое ожидание — S-state, не b; рассуждение про GC при si/so=0 не следует из vmstat | runtime/chan.go; man perf/vmstat/iostat; B.Gregg «Linux Performance» | — (не перепроверено) |
| 60.4 | Medium | iostat | «%util >80% — близко к насыщению» | для SSD/NVMe/RAID с параллельными очередями %util некорректен (man iostat); смотреть aqu-sz, r_await/w_await; await разбит на r_await/w_await в новых sysstat | man perf/vmstat/iostat; B.Gregg «Linux Performance» | — (не перепроверено) |
| 60.5 | Medium | «Direct I/O через mmap или io_uring» | — | mmap не обходит Page Cache; Direct I/O = O_DIRECT (повтор [42]) | man 2 mmap; mm/mmap.c; Documentation/mm/; man 2 open (O_DIRECT); statx(2) | — (не перепроверено) |
| 60.6 | Medium | Сценарий 3 | «Lock contention sync.Mutex → высокий %sy и cs сотни тысяч» | slow path Go-мьютекса паркует горутину в userspace; признак — mutex/block profile (pprof) и go tool trace; perf c2c = cache-to-cache (не «Last Cache Miss») | sync/mutex.go, sync/rwmutex.go, runtime/sema.go | — (не перепроверено) |
| 60.7 | Low | top | `top -o %us`; «top использует getrusage()» | у top нет per-process поля %us; значения берутся из /proc/PID/stat; getrusage не используется | man 5 proc; sysstat docs | — (не перепроверено) |
| 60.8 | Low | Сценарий 1 | «GODEBUG=gctrace=1 | grep gcwait»; «замена []byte на mmap» | gctrace пишет в stderr и «gcwait» там нет; совет с mmap сомнителен | — (не перепроверено) |
| 60.9 | Low | Итог/таблица | «не нужно открывать отладочные порты» | net/http/pprof требует HTTP-эндпоинт; не упомянуты runtime/trace, runtime/metrics, GODEBUG=schedtrace, pidstat/mpstat/sar/PSI/ss, kernel.perf_event_paranoid (блокирует perf в контейнерах) | net/http/pprof/pprof.go; runtime/pprof; man perf/vmstat/iostat; B.Gregg «Linux Performance» | — (не перепроверено) |

### Статья 61. eBPF. Современный способ наблюдать за ОС

| № | Приор. | Раздел | Утверждение | Проблема / что проверить | Источник | Статус |
|---|:---:|---|---|---|---|---|
| 61.1 | High | Код | `//go:embed` без import "embed"; `collection.Maps.Lookup("metrics_map").Lookup(&metricsMap)`; неиспользуемые `os`, `time`; busy-loop по Lookup с unbuffered chan; «Duration» из sys_enter_write | не компилируется (Maps — map[string]*ebpf.Map); 100% CPU spin; длительность нельзя получить без пары enter/exit; идиома — bpf2go + ringbuf.Reader, rlimit.RemoveMemlock (<5.11); Printf-разрыв | go build / go vet на листинге | ✔ src |
| 61.2 | Medium | uprobes в Go | «перехват функций Go-бинарника» без оговорок | uretprobe небезопасны для Go (перемещение стека горутин ломает return-адрес; процесс падает) — используют uprobe на каждом RET; аргументы читаются из регистров ABIInternal (1.17+) | Documentation/bpf/; cilium/ebpf docs; man 2 bpf | — (не перепроверено) |
| 61.3 | Medium | Maps/Zero-Copy | «карты проецируются в Go через mmap; чтение без syscalls» | mmap — только для BPF_F_MMAPABLE array-карт (5.5) и ring buffer; hash/per-CPU — через bpf() syscalls (Map.Lookup); пример сам делает Lookup в цикле | man 2 mmap; mm/mmap.c; Documentation/mm/; man 2 sendfile/splice; net/tcpsock_posix.go (ReadFrom) | — (не перепроверено) |
| 61.4 | Medium | Привилегии | CAP_BPF (5.8) или SYS_ADMIN | для трассировки нужен ещё CAP_PERFMON; kernel.unprivileged_bpf_disabled; в k8s/Docker seccomp режет bpf() без SYS_ADMIN | man 7 capabilities; syscall.SysProcAttr | — (не перепроверено) |
| 61.5 | Medium | omission | — | CO-RE/BTF/libbpf, bpftool, bpftrace/BCC one-liners (execsnoop, tcpconnect, biolatency), готовые Go-профилировщики на eBPF (Parca, Pyroscope, Beyla, Tetragon), ограничения по версии ядра | Documentation/bpf/; cilium/ebpf docs; man 2 bpf; Intel/AMD Optimization Manuals (cache coherency) | — (не перепроверено) |
| 61.6 | Low | Введение | «eBPF — extended Berkeley Packet Filter»; «агенты тратят 10–15% CPU» | сейчас не аббревиатура; цифра без источника | Documentation/bpf/; cilium/ebpf docs; man 2 bpf | — (не перепроверено) |
| 61.7 | Low | Verifier | «лучше kprobes и LD_PRELOAD»; ошибка «invalid mem stack»; «#pragma unroll» | eBPF использует kprobes как точку подключения; реальные тексты ошибок иные («stack limit exceeded»); с bounded loops (5.3) и bpf_loop (5.17) unroll не обязателен; «гарантированно не вызывает panic» — были CVE в верификаторе | Documentation/bpf/; cilium/ebpf docs; man 2 bpf; runtime/panic.go; runtime/extern.go (GOTRACEBACK) | — (не перепроверено) |

### Статья 62. Как Go runtime взаимодействует с ОС

| № | Приор. | Раздел | Утверждение | Проблема / что проверить | Источник | Статус |
|---|:---:|---|---|---|---|---|
| 62.1 | High | GOMAXPROCS gotcha | «используйте uber-go/automaxprocs; значение = физические ядра/квоты» | устарело с Go 1.25 (авто-учёт cgroup, динамика); по умолчанию = логические CPU (SMT) | runtime/debug.go; runtime/cgroup_linux.go; Go 1.25 release notes | ✔ src |
| 62.2 | Medium | G-M-P / Hand-off | «M создаются pthread_create», «лишние потоки уничтожаются pthread_exit» | в pure-Go runtime — clone(2) (newosproc); pthread_create — только при cgo; Go не уничтожает простаивающие M (они паркуются), завершается лишь поток после LockOSThread-горутины | runtime/os_linux.go (newosproc, cloneFlags) | ✔ src |
| 62.3 | Medium | Переключение горутин | «10–20 нс» (абзац 1, Итог 2) vs «100–300 нс» (Mechanical) | противоречие в одной статье | исходники Go (runtime/net/os/syscall), release notes версии; воспроизводимое измерение (lmbench/perf/fio) или публикация с методикой | — (не перепроверено) |
| 62.4 | Medium | Under hood P | «число P фиксируется при старте и неизменно»; поля runqsize, syscall | runtime.GOMAXPROCS(n) меняет число P (STW/procresize); с Go 1.25 — автоматически; полей runqsize/syscall нет (status, syscalltick) | runtime/proc.go (runqput, runnext) | — (не перепроверено) |
| 62.5 | Medium | Память | «sysAlloc — гигабайты PROT_NONE при старте»; «коммит через mprotect» | арены 64 МБ резервируются по мере роста (hints); sysMap делает mmap(MAP_FIXED, RW), а не mprotect | man 2 mmap; mm/mmap.c; Documentation/mm/ | ✔ src |
| 62.6 | Medium | Блокирующие вызовы | «entersyscall проверяет g.lockedm» и «немедленно отвязывает P» | P не отдаётся сразу: handoff делает sysmon retake (≥1 тика=20 мкс и условия/10 мс; в Go ≤1.26 это статус _Psyscall, в 1.27 удалён) или entersyscallblock; lockedm к entersyscall отношения не имеет | runtime/proc.go (sysmon, retake, handoffp) | ✔ src |
| 62.7 | Medium | Сигналы | «SIGUSR1/SIGUSR2 … SIGSTKFLT при переполнении стека»; «SIGWINCH обрабатывает stdlib для os.Stdout» | переполнение стека определяется проверкой в newstack без сигналов (SIGSTKFLT в sigtable — _SigThrow, ✔ sigtab_linux_generic.go; SIGUSR1/2 — только _SigNotify); SIGWINCH в sigtable = _SigNotify+_SigIgn (по умолчанию игнорируется, ✔); не упомянуты SIGPROF (профиль), SIGQUIT (дамп), SIGCHLD, SIGPIPE; «SIGURG гарантирует» — async preemption не работает в unsafe-points (nosplit/runtime/cgo) | runtime/stack.go, runtime/proc.go (maxstacksize); man 7 signal; os/signal doc; runtime/signal_unix.go | ✔ src |
| 62.8 | Medium | omission | — | futex — ключевой syscall рантайма (note/runtime.mutex/timers) не показан в статье-интеграции; vDSO (nanotime/walltime), sigaltstack, arch_prctl (TLS), getrandom, sched_getaffinity, SIGURG для GC stack scan; cgo thread model | man 2 futex; runtime/lock_futex.go, sync/mutex.go; man 7 vdso; runtime/vdso_linux.go | — (не перепроверено) |
| 62.9 | Low | g/gopark | «gogo, gopark, goready — ассемблерные в asm_*.s» | в asm — gogo/mcall/morestack; gopark/goready — Go-функции proc.go | cmd/compile/abi-internal.md; go.dev/doc/asm | — (не перепроверено) |
| 62.10 | Low | Gotcha RSS | «Go возвращает лениво; агрессивно — при GOGC=1; Page Cache влияет на RSS» | работает фоновый scavenger с pacing (+GOMEMLIMIT); page cache в RSS процесса не входит (кроме mapped) | Documentation/admin-guide/sysctl/vm.rst; mm/filemap.c, mm/page-writeback.c | — (не перепроверено) |
| 62.11 | Low | Netpoller | «pollCache — кэш для поиска горутин; поллер проверяет netFD.Read/Write» | pollCache — аллокатор pollDesc; netpoll не вызывает Read/Write, лишь netpollready | runtime/netpoll.go, netpoll_epoll.go; man 7 epoll; runtime/mheap.go, runtime/sizeclasses.go, runtime/malloc.go | — (не перепроверено) |
| 62.12 | Low | Mechanical | «горутины в очереди одного P исполняются на одном M и делят L1/L2» | work stealing, смена M↔P; привязка не гарантирована | runtime/os_linux.go (newosproc, cloneFlags) | — (не перепроверено) |
| 62.13 | Low | OOM текст | «fatal error: cannot allocate memory» | фактически «fatal error: out of memory» / «runtime: out of memory: cannot allocate N-byte block» | Documentation/admin-guide/sysctl/vm.rst; mm/vmscan.c, mm/oom_kill.c; runtime/os_linux.go (newosproc, cloneFlags) | — (не перепроверено) |
| 62.14 | Low | Итог 1 | «виртуальная машина пользовательского пространства» | рантайм — не VM (нет байткода) | runtime/os_linux.go (newosproc, cloneFlags) | — (не перепроверено) |

### Статья 63. Итоги раздела. Картина ОС целиком для Go-разработчика

| № | Приор. | Раздел | Утверждение | Проблема / что проверить | Источник | Статус |
|---|:---:|---|---|---|---|---|
| 63.1 | High | Interview close() | «epoll зафиксирует закрытие fd, сгенерирует EPOLLHUP/EPOLLERR; Read получит io.EOF или EBADF» | локальное close() не порождает epoll-события (fd удаляется из epoll); netFD.Close → pollDesc.evict → runtime_pollUnblock будит читателя в userspace; ошибка — net.ErrClosed («use of closed network connection»), не EOF/EBADF | runtime/netpoll.go, netpoll_epoll.go; man 7 epoll | ✔ src |
| 63.2 | High | Таблица Go→ядро | «sync.Mutex → futex»; «Channel → runtime.sema + epoll/futex»; «goroutine → clone(CLONE_VM\|FS\|FILES)»; «runtime.GC → madvise/mprotect»; «Нейгла» | противоречит ст.23/33: sync.Mutex использует runtime sema+gopark (futex — на уровне M); каналы — hchan+lock+gopark, без epoll; clone создаёт M, а не горутину; GC madvise не вызывает (scavenger); «алгоритм Нагла» | man 2 futex; runtime/lock_futex.go, sync/mutex.go; sync/mutex.go, sync/rwmutex.go, runtime/sema.go | ✔ src |
| 63.3 | Medium | Согласованность | «g→g 10–20 нс» (63, 62 п.1, 5, 9) vs «100–300» (62 Mechanical, 9, 5 text) | единый диапазон не выдержан во всём модуле | воспроизводимое измерение (lmbench/perf/fio) или публикация с методикой | — (не перепроверено) |
| 63.4 | Medium | Регистры | «сохраняется rip, rsp, r12–r15» | gobuf: sp, pc, g, ctxt, ret, lr, bp; ABIInternal без callee-saved; R14 — g, R15 — GOT (dynlink) | runtime/runtime2.go (gobuf); cmd/compile/abi-internal.md; cmd/compile/abi-internal.md; go.dev/doc/asm | — (не перепроверено) |
| 63.5 | Medium | Ловушка GOMAXPROCS | «определяет количество потоков ОС (M), выполняющих байткод Go»; «GOMAXPROCS=1 + невытесняемые циклы → очередь» | задаёт число P (M может быть больше, ст.62/Interview); «байткода» в Go нет; с 1.14 tight-loop вытесняется async preemption | runtime/debug.go; runtime/cgroup_linux.go; Go 1.25 release notes; runtime/os_linux.go (newosproc, cloneFlags) | — (не перепроверено) |
| 63.6 | Low | Under hood | «m хранит schedtick» | schedtick в p | первоисточник по теме (спецификация/документация) | — (не перепроверено) |
| 63.7 | Low | Практики | «sync.Pool снижает давление на страничный кэш»; «WaitGroup без context гарантированно приводит к утечке горутин»; «connect — тяжёлый блокирующий syscall» | page cache не при чём; утечки — из-за блокировок/отсутствия отмены, не WaitGroup; connect в Go неблокирующий (netpoll) | sync/pool.go; staticcheck SA6002; go vet copylocks; sync docs | — (не перепроверено) |
| 63.8 | Low | GOMEMLIMIT | «предотвращает уничтожение OOM Killer» | soft limit, не гарантия (ст.17) | Documentation/admin-guide/sysctl/vm.rst; mm/vmscan.c, mm/oom_kill.c; Go 1.19 release notes; runtime/debug/garbage.go | — (не перепроверено) |

---

## 5. Что не вошло / ограничения проверки

* **Сам текст статей не правился**, `sources/` не изменялся; единственный создаваемый файл — этот отчёт.
* Утверждения о ядре Linux/железе/сторонних инструментах основаны на моих знаниях (на момент прогона это Linux 6.x, Go 1.27, K8s 1.3x); интернет-поиск и первоисточники по ним **не открывались**. Строки со статусом «— (не перепроверено)» требуют подтверждения по указанному типу источника, а «⚠ проверить» — те, где я сам не уверен.
* Данные в таблице раздела 2 («числовые расхождения») — это расхождения **между статьями модуля** и с общеизвестными порядками величин; для итогового числа нужен собственный бенчмарк на целевом железе.
* Версии: утверждения про Go сверены с 1.27.1; для более старых версий (например, ≤1.24) часть замечаний (T2: Go 1.25; `_Psyscall`-терминология sysmon — удалена в новых версиях, #64318) иначе формулируется — это отмечено в строках.
* В отчёт сознательно не включены чисто стилистические замечания (юмор, метафоры, эмодзи в заголовках, длина абзацев) и спорные оценки «лучшая практика», если они не искажают факты.
