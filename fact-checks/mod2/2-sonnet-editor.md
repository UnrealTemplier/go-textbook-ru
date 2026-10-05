# Final Technical Editor · Модуль 2 «Устройство и работа ОС»

> **Роль:** финальный технический редактор (Sonnet 5.5).
> **Вход:** оригинальные статьи `sources/2. Устройство и работа ОС/` (63 файла) и `2-sonnet-fact-check.md`. Файла `2-sonnet-arbiter.md` не существует, поэтому работа велась только по фактчеку.
> **Дата правки:** 2026-10-05.
> **Результат:** исправления внесены прямо в исходные файлы модуля (структура и имена файлов сохранены). Изменено 60 из 63 статей; не тронуты 45, 46, 55: по ним фактчек не нашёл подтверждённых ошибок.

---

## 1. Правила, по которым шла правка

1. Правились только утверждения со статусом `INCORRECT`, `PARTIALLY CORRECT`, `OUTDATED`, `CONTEXT-DEPENDENT`, а также `VERIFIED`-находки, которые прямо противоречат тексту статьи (например, правильная формулировка в одной статье и неверная в другой).
2. `NOT CHECKED` и `OPINION / NOT A FACT CLAIM` не трактовались как факты и **не правились** (список в § 5). То же относится к предложениям брифов (Gemini, Opus), которые фактчек не подтвердил.
3. Структура статей, учебные цели, метафоры, примеры и интонация автора сохранены. Переписывались только абзацы, где ошибка в самой посылке. Новых технических утверждений без опоры на фактчек не добавлялось; там, где потребовалась новая формулировка, она ограничена тем, что фактчек доказал **[L]/[E]/[R]**.
4. Правки Mermaid, сделанные раньше (`1598e5d8`, `8a4bfb2e`, `a8d34615`), не трогались.
5. `dist/` не пересобирался и не коммитился: сборка ушла в scratch-каталог, чтобы прогнать аудит. Коммит не создавался (по правилу § 0 `AGENTS.md`).

## 2. Сводка по классам правок

| Класс | Что исправлено | Статьи |
|---|---|---|
| Рантайм Go: стек горутин | рост стека идёт из пулов рантайма, без `mmap`/`madvise`; лимит стека — `maxstacksize`, а не `ulimit -v`; переполнение — `fatal error` (`throw`, код 2), не паника и не `SIGSEGV`; нет `gostacksplit`, `gostartcall` не про рост стека; профиля `pprof/stack` нет; `//go:nosplit` не защита от рекурсии; OOM-kill раньше `stack overflow` в контейнере | 19, 20, 21 |
| Рантайм Go: блокировки и каналы | `sync.Mutex`, каналы и `RWMutex` паркуют горутину (`gopark`, семафоры) **без** `futex`; `futex` — для сна потоков `M` и внутренних локов рантайма; netpoller каналами не пользуется | 1, 3, 22, 23, 24, 33, 34, 62, 63 |
| Netpoller | fd регистрируется в epoll один раз при создании сокета, а не после `EAGAIN`; нет `EPOLLONESHOT`; `read` один, а не «до `EAGAIN`»; несуществующие `wakeG`, `netpollLock`, `type netpoller`, имена файлов `netpoll_*.go`; локальный `close()` → «use of closed network connection», а не `EPOLLHUP`/`io.EOF` | 35, 36, 37, 38, 63 |
| Сигналы | нет `sigwaitinfo`; буфер канала `signal` задаёт вызывающий код; `NotifyContext` — Go 1.16; `SIGPIPE` (fd 1/2 завершают, остальные дают `EPIPE`); `EINTR` не полностью скрыт | 28 |
| Привилегии и capabilities | `syscall.Setuid/Setgid` уже рассылаются всем потокам (`AllThreadsSyscall` напрямую не нужен, при cgo даёт `ENOTSUP`); `unix.Capset` действует на один поток; `CapUserHeader/CapUserData`, массив из двух структур; `AmbientCaps`; нет `CAP_CLEAR`, `NoSetuid`, `github.com/capabilities/cap`; 44 вызова блокирует seccomp, а не AppArmor | 56, 57, 58 |
| Контейнеры и cgroup | `GOMAXPROCS` и cgroup (Go 1.25+, зависит от `go` в `go.mod`); `NumCPU` — логические CPU; Go в PID 1 **не** игнорирует `SIGTERM` (код 143); при `memory.max` — `SIGKILL` (137) без диагностики, `ENOMEM` бывает от `mmap` только в других случаях; нет `brk` для кучи на 64 бит; `GOMEMLIMIT` включает стеки и метаданные рантайма; namespaces — 8 (есть `TIME`) | 1, 8, 52, 53, 54 |
| Сеть и сокеты | нет `ListenConfig.Backlog` и `SO_MAX_CONN`/`SO_BACKLOG`; backlog берётся из `somaxconn` (128 → 4096 с ядра 5.4); `File().Fd()` делает сокет блокирующим; `KeepAlive: 30s` выставляет `TCP_KEEPIDLE=30`, хук `Control` на принятых соединениях не работает; `TIME_WAIT` = 60 с (не 120); `tcp_fin_timeout` — про `FIN_WAIT_2`; RFC 9293; `tcp_tw_recycle` удалён в 4.12; по умолчанию Go ставит только `SO_REUSEADDR`; `ECONNREFUSED` лишь при `tcp_abort_on_overflow=1`; DNS: опрос серверов последовательный, `experimentalgo` нет, дефолт зависит от ОС, при `TC` TCP-запрос делает резолвер | 1, 47, 48, 49, 50, 51 |
| Память | возврат памяти делает scavenger, а не `sysmon`, отображение сохраняется; `HeapInuse ≥ HeapAlloc`; `sync.Pool` и `badPattern`/`goodPattern`; false sharing (классы размеров 24, 48, 80…); `debug.MemoryLimit` нет, есть `SetMemoryLimit(-1)`; `pagealloc=1`, `MHeapMap_SpanInUse`, `gcresidency` нет; 5-уровневая адресация — порядка 64 ПБ; CoW не через `PTE_SOFT_DIRTY`; `CLONE_VFORK` приостанавливает вызывающий поток; page fault не отнимает `P` | 11, 12, 13, 14, 15, 16, 17, 19 |
| Процессы и `os/exec` | `cmd.Wait` блокирует поток `M` (hand-off), а не только горутину; нет `runtime.forkExec`; `forkAndExecInChild` — Go (`nosplit`), не ассемблер; `retake`: условия отбора `P`; `daemonize()` без защиты от рекурсии, `SysProcAttr.Setsid`; `Type=simple` — после `fork()`; `LimitNOFILE` — rlimit; Go ≥ 1.19 сам поднимает soft `RLIMIT_NOFILE`; нет `go-systemd/sdnotify` (есть `daemon`) | 5, 6, 22, 29, 30, 52, 62 |
| Файлы и IO | нет `os.O_DIRECT` (есть `syscall.O_DIRECT`); выравнивание буфера; `EINVAL` зависит от ФС; режимы `data=` только у ext4; checkpointing не часть `fsync`; нет `syscall.ShmOpen`, `/dev/zero` не годится для IPC; `os.FileMode(Stat_t.Mode)` неверно; `UNIX SOCK_DGRAM` на Linux надёжен; `Pipe2`, `os.NewFile(uintptr)`; гонка `runWithPipe`; `FileListener` вместо `FileConn`; `net/http`/`sendfile` | 25, 26, 27, 31, 32, 40, 41, 42, 43 |
| Диагностика | `ltrace` работает через `ptrace` (и не через `LD_PRELOAD`); `epoll_pwait(-1)` и `futex` — не признаки багов; core dump в Go требует `GOTRACEBACK=crash`; `kernel.core_uses_pid`; у Delve нет `heap`; `GODEBUG=asyncpreempt=1`, `pprof -goroutine` нет; детектор deadlock не зависит от `GOMAXPROCS` и молчит при cgo; frame pointer включён всегда | 20, 24, 34, 59, 60 |
| Числа | DRAM ~70–100 нс (не 20–30); переключение горутин порядка 100–150 нс (не 10–20); syscall без KPTI ~60–80 нс; 50 000 RPS × 20 syscall — 10–50 % одного ядра; KPTI только на CPU с Meltdown; верхние оценки переключения потоков — с косвенными потерями; Firecracker — не более 125 мс | 2, 4, 8, 9, 11, 23, 35, 38, 62, 63 |
| Разное | регистры аргументов `syscall` (`RDI, RSI, RDX, R10, R8, R9`); `arch/x86/boot/header.S`, `compressed/head_64.S`; `fs/futex.c` → `kernel/futex/`; `TASK_INTERRUPTIBLE` у `FUTEX_WAIT`; spinlock на UP; `RWMutex` не голодит писателей; IOCP — пул создаёт приложение; `gobuf = {sp, pc, bp, g, ctxt}`; `perf`/сегментированные стеки; приоритеты RT (`sched_rt_runtime_us` зависит от дистрибутива) | 3, 4, 5, 9, 10, 23, 33, 34, 37, 60, 63 |
| Код листингов | строковые литералы, разорванные реальным переводом строки (исправлено 34 места в 16 статьях); неиспользуемые импорты (`log`, `fmt`, `unsafe`, `bytes`, `path/filepath`, `os`, `time`); `Madvise` с тремя аргументами; `Pipe2([]int{0,1}, …)`; `ForkExec` возвращает два значения; несуществующие `unix.CapHeader/CapData`, `Mmsghdr`, `http.NewServer`, `cilium/ebpf Maps.Lookup`; `//go:embed` без `import _ "embed"` | 5, 6, 7, 10, 12, 13, 14, 16, 17, 18, 19, 25, 26, 27, 29, 30, 31, 32, 39, 40, 41, 42, 43, 44, 47, 48, 49, 51, 53, 56, 57, 58, 61 |
| Разметка | потерянные `\t` в формулах KaTeX (14 строк) вернулись в `\to`, `\text`, `\times` | 12, 13, 14, 15, 17, 18, 54 |

## 3. Подробный перечень по статьям

Формат: **статья** — что изменилось (ссылки на пункты фактчека в скобках).

- **1** — «монолитный статический ELF» уточнён (cgo → динамический); `channel` не использует netpoller; `brk` заменён на `mmap`; `SO_REUSEPORT` не включается по умолчанию; `N_CPU` — логические CPU (J-H3, J-H4, C-BRK, C-SOCKDEF, 1.3, 1.5).
- **2** — KPTI оговорен (`CR3` — только на CPU с Meltdown); цена syscall; расчёт «50 % мощности» исправлен на 10–50 % одного ядра; `RawSyscall` возвращает `Errno`, а не `uintptr(-1)`; блокирующий `RawSyscall` подвешивает весь процесс на ближайшем STW (J-H30, B-2, 2.8, 2.9).
- **3** — `futex` в `sync.Mutex`; `getcpu` заменён на `sched_getaffinity` (J-H3, 3.3).
- **4** — `head.S` → `header.S` / `compressed/head_64.S`; Firecracker — не более 125 мс, а не «5 мс» (J-H5, 4.13).
- **5** — `cmd.Wait` и поток `M`; `runtime.forkExec`; диаграмма регистров горутины; предупреждение про soft `RLIMIT_NOFILE` в Go ≥ 1.19; листинг (импорты, литералы) (J-H16, C-GOBUF, C-NOFILE).
- **6** — `forkAndExecInChild` не на ассемблере; `Wait` и hand-off; листинг (J-H16, 6.5).
- **8** — `NumCPU`, `automaxprocs` с оговоркой про Go 1.25; DRAM ~70–100 нс (J-H4, J-H25).
- **9** — `gobuf` вместо «14 регистров»; `sched_gomaxprocs` убран; оговорка о прямой и косвенной стоимости (C-GOBUF, J-H5, C-NUM).
- **10** — RT-throttling зависит от дистрибутива (J-H26).
- **11** — DRAM-задержки; `cpuset.sched_load_balance`/`mems_hardwall` (только cgroup v1); `gcresidency` убран (J-H25, J-H5).
- **12** — 5-уровневая адресация (~64 ПБ); `Madvise` (J-H6, 12.2).
- **13** — `pagealloc=1` → `disablethp`; `MHeapMap_SpanInUse`; лишний `unsafe`; Interview Q2: page fault не отнимает `P` (J-H5, J-H24).
- **14** — `badPattern`/`goodPattern` (аллокации, `sync.Pool` с `*[]byte`); `netpoller` и каналы (J-H24).
- **15** — false sharing и размерные классы (J-H24).
- **16** — `PTE_SOFT_DIRTY`; `CLONE_VFORK`; `Madvise(DONTFORK)`; противоречие CoW/`os/exec` (J-H23, B-6).
- **17** — `debug.SetMemoryLimit(-1)` вместо `MemoryLimit()` (J-H5).
- **18** — лишний/недостающий импорт, литералы (J-H6).
- **19** — scavenger и `sysmon`; `HeapInuse`; рост стека; таблица `brk`/`mmap`; лимит стека (J-H2, J-H24).
- **20** — frame pointer включён всегда; `fatal error` ≠ паника (J-H19, J-H2).
- **21** — рост стека без `mmap`/`madvise`; `gostacksplit`, `gostartcall`; лимит `maxstacksize`; не `SIGSEGV`; нет профиля `stack`; `nosplit`; OOM-kill (J-H2, B-14).
- **22** — hand-off и `retake`; строка про `futex` в таблице собеседований (C-HANDOFF, J-H3).
- **23** — `futex`; регистры `syscall`; `.s` вместо `.go`; Interview Q3; оценка тактов (J-H3, J-H27, 23.5).
- **24** — `ltrace`/`ptrace`/`LD_PRELOAD`; диагностика `epoll_pwait(-1)` и `futex` (J-H9).
- **25** — `os.NewFile(uintptr(…))` (J-H5).
- **26** — `Pipe2`; `runWithPipe` (гонка, лишний `log`); таблица «автозакрытие пайпов» (J-H16).
- **27** — `SOCK_DGRAM` надёжен; пример передачи FD переписан на `UnixRights` + `WriteMsgUnix`/`ReadMsgUnix` (J-H8).
- **28** — `sigwaitinfo`, буфер, `NotifyContext`, `SIGPIPE`, `EINTR` (J-H1, B-5, 28.4, 28.6).
- **29** — `daemonize()` (защита от рекурсии, `Setsid`, два значения `ForkExec`); `http.NewServer`; `Type=simple`; `sdnotify` → `daemon` (J-H16).
- **30** — `FileListener` вместо `FileConn`; `LimitNOFILE` — rlimit (J-H16, C-NOFILE).
- **31** — `/dev/zero` как IPC → `/dev/shm`; лишний `unsafe` (J-H17).
- **32** — `syscall.ShmOpen` → `os.OpenFile("/dev/shm/…")` + `Truncate` (J-H5, J-H17).
- **33** — spinlock на UP; `TASK_INTERRUPTIBLE`; `kernel/futex/`; `golang.org/x/sync/semaphore` (J-H22, J-H5).
- **34** — `futex` в `sync.Mutex`; детектор deadlock; `acquireWithTimeout` на `TryLock`; `RWMutex`; `pprof` и `asyncpreempt`; `TryLock` публичен (J-H22, N-2).
- **35** — fd регистрируется один раз; «читать до `EAGAIN»; стоимость переключения (J-H7, B-9).
- **36** — диаграмма и список этапов netpoller; `wakeG` → `netpollready`/`goready` (J-H7, J-H5).
- **37** — IOCP; имена файлов; `netpollLink` → `operation` (J-H28, J-H5).
- **38** — `pollDesc` вместо `type netpoller`; `netpollLock`; `EPOLLONESHOT`; edge-triggered; число для переключения (J-H5, J-H7, 38.2).
- **39** — литерал (J-H6).
- **40** — `os.FileMode(Stat_t.Mode)`; `fs.ReadStat`; литералы (J-H16, K6, 40.6).
- **41** — `data=` только у ext4; checkpointing (J-H21).
- **42** — `os.O_DIRECT` → `syscall.O_DIRECT`; `EINVAL` (J-H14).
- **43** — `writeDirectIO` (выравнивание через `Mmap`); `EINVAL`; `sendfile`/`fs.go` (J-H14, 43.4).
- **44** — литералы (J-H6).
- **47** — `Backlog`; `KeepAlive`; пример на `KeepAliveConfig`; `somaxconn` (J-H11, J-H12, B-3, N-3).
- **48** — `ECONNREFUSED`; `Backlog`; `SO_REUSEPORT`; `SO_BACKLOG` (J-H11, C-SOCKDEF, B-29).
- **49** — `SO_MAX_CONN`; `File().Fd()` (блокирующий режим); пример про `backlog` (J-H5, K3, B-1).
- **50** — `TIME_WAIT` 60 с; `tcp_tw_recycle`; `tcp_fin_timeout`; RFC 9293 (J-H13, 50.2).
- **51** — дефолтный резолвер; `experimentalgo`; последовательный опрос; `TC` (J-H10).
- **52** — `NOFILE`; `GOMEMLIMIT`; `clone` для `M`; GC и cgroup; `GOMAXPROCS` (J-H4, B-10, B-13).
- **53** — 8 namespaces; `brk`; `ENOMEM`/`SIGKILL` (K8, J-H18).
- **54** — `GOMAXPROCS` (Go 1.25); PID 1; `brk` (J-H4, J-H18, K5).
- **56** — `AllThreadsSyscall` → `syscall.Setuid/Setgid`; литералы (J-H15, K1).
- **57** — `os.Setuid` → `syscall.Setuid`; `Capset` на один поток; `CAP_CLEAR`; `AmbientCaps`; `capabilities/cap` (J-H15, B-4).
- **58** — `dropPrivileges`: `CapUserHeader/CapUserData`, массив из двух; seccomp (J-H15, N-4, 58.2).
- **59** — `GOTRACEBACK=crash`; `heap` у Delve; `kernel.core_uses_pid` (J-H20).
- **60** — сегментированные стеки; `asyncpreempt` (J-H19, J-H5).
- **61** — листинг eBPF (`embed`, `Maps`, опрос с паузой, счётчик вместо длительности) (J-H31).
- **62** — `gopark` — Go; hand-off; `pthread_create` / `clone`; стоимость переключения (J-H24, 62.9, C-HANDOFF, C-NUM).
- **63** — таблица «Go → ядро» (`goroutine`, `Channel`, `sync.Mutex`, `runtime.GC`); `gobuf`; `GOMAXPROCS`; `close()`/`EPOLLHUP`; диаграмма (J-H29, J-H3, J-H7).
- **7** — только литералы в листингах (J-H6).
- **45, 46, 55** — по фактчеку правок не требовалось.

## 4. Проверка после правок

- **Строковые литералы:** `go/scanner` по всем 78 go-блокам модуля (включая блоки внутри цитат `> ```go`) — 0 ошибок.
- **Компиляция:** все 46 программ `package main` проходят `go vet` (go1.27.1, `golang.org/x/sys v0.46.0`, `cilium/ebpf v0.22.0`). Исключение — блоки 29 (№3) и 30 (№2): они используют `github.com/coreos/go-systemd/v22/daemon`, которого нет в локальном кэше модулей, поэтому проверены только синтаксически.
- **Аудит сайта:** полная сборка в scratch-каталог + `python3 builder/audit_all.py`: ошибок имён файлов 0, битых ссылок 0, анкоров 0, ошибок и предупреждений Mermaid 0 (рантайм-разбор: не разобрано 0 из 2486).
- Репозиторный `dist/` не пересобирался (см. § 1, п. 5).

## 5. Что сознательно не менялось

- **`NOT CHECKED` (≈259 Medium, ≈280 Low):** микроархитектурные задержки (TLB, L1–L3, NVMe), структуры ядра (`tcp_death_row`, `struct tcp_time_wait`, `fs/namei.c`, jbd2, XFS-журнал, `dm`/`md`), удалённый доступ NUMA, `MPOL_BIND`, auto-NUMA, EEVDF-детали, `LimitNOFILE` в Docker, `requests.memory ↔ memory.min`, поведение Java, PHP-FPM, Python, `O_DIRECT` и «ресурс ячеек NAND», `net.Conn` как `io.ReaderAt`, «в Go нет аналога `popen`», история `adaptivestackstart` и THP в 1.21.x, `MADV_DONTFORK` на невыровненном срезе, `CLONE_VFORK`/`LockOSThread` и т. п. Любое такое утверждение оставлено как есть и **не считается проверенным**.
- **`OPINION`:** эпиграфы и атрибуции, терминология «context switch» и «mode switch».
- **`VERIFIED`-места** (не менялись): `somaxconn` 128→4096 в ст. 49, `MaxIdleConnsPerHost = 2`, `RLIMIT_RSS`, `ModeSticky`, `SO_RCVBUF ×2`, абстрактные UDS, финализатор `*os.File`, `Go + TCP_NODELAY` (ст. 63, пометка судьи ложноположительная), `Type=notify` в целом.
- **Mermaid и разметка**, уже исправленные коммитами `1598e5d8`, `8a4bfb2e`, `a8d34615`, не менялись; в рамках текущих правок скорректированы лишь диаграммы, смысл которых противоречил исправленному тексту (ст. 21, 36, 41, 63).

## 6. Остаточные риски и замечания

1. **Ошибки брифов, не перенесённые в текст:** пометка судьи о «алгоритме Нейгла» в ст. 63 (формулировка верна), `automaxprocs` в ст. 62 (его там нет), `fs/futex.c` как «историческое имя» (такого файла никогда не было), «`EINVAL` гарантирован при `O_DIRECT`» (зависит от ФС).
2. **Версии Go, не проверенные по release notes:** в статьях 19 и 20 остались формулировки «непрерывные стеки с Go 1.4» и «2 КБ с 1.4» (`NOT CHECKED`); я их не менял.
3. **Эксперименты воспроизведены на go1.27.1 / Linux 7.2.8 / Intel Core i9-12900K.** Числа, взятые из замеров (140 нс, 60–80 нс, 70–100 нс), в тексте оговорены как порядок величины; на другом железе они будут другими.
4. **`GOMAXPROCS` / cgroup:** формулировки привязаны к языковой версии `go` в `go.mod` (поведение `containermaxprocs` с Go 1.25), это проверено запуском.
5. **Листинги** в ст. 27 (`WriteMsgUnix`/`ReadMsgUnix`) и ст. 29 (`daemon.SdNotify`) — фрагменты; в ст. 29 и 30 использована библиотека `go-systemd/v22/daemon`, API которой я сверял по сообщению фактчека (§ J-H5), а не по локальным исходникам.
