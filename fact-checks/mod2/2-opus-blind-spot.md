# Blind-spot ревью · Модуль 2 «Устройство и работа ОС»

> **Роль:** blind-spot researcher (Opus).
> **Вход:** `sources/2. Устройство и работа ОС/` (63 статьи, прочитаны целиком заново) и `2-opus-judge.md` (Master Fact-Check Brief).
> **Задача:** найти только важные проблемы, которых нет в брифе. Чтобы не повторяться, каждый кандидат сверялся не только с текстом брифа, но и со строками `2-sonnet-alt.md` и `2-gemini-scout.md`, на которые бриф ссылается по номерам.

---

## 0. Методика и уровень доказательности

- Утверждения о Go сверены с исходниками локального **go1.27.1 linux/amd64** (`/usr/local/go/src`) и `golang.org/x/sys v0.46.0`. Пути и строки указаны в каждом пункте.
- Четыре находки подтверждены **экспериментом** (программы в scratchpad, Go 1.27.1, Linux 7.2). Они помечены **[эксперимент]**.
- Утверждения о ядре Linux, systemd и SELinux по первоисточникам не проверялись. Для них указан решающий источник.
- Номера строк даны по текущим файлам в `sources/`.

### Сводка

| ID | Статьи | Суть | Приоритет | Меняет вывод брифа? |
|---|---|---|:---:|---|
| B-1 | 49 | `TCPListener.File().Fd()` переводит слушающий сокет в блокирующий режим; `Close`/`Shutdown` зависает | **High** | да: R4, R10, K3 |
| B-2 | 2 | Блокирующий `RawSyscall` подвешивает stop-the-world и всю программу, а не «только P+M» | **High** | да: 2.9 |
| B-3 | 47 | Хук `Control` из ответа на Interview не действует: принятые соединения получают keepalive 15/15 | **High** | дополняет J-H12 |
| B-4 | 57, 58 | `capset`/`PR_CAP_AMBIENT` действуют на один поток; в Go привилегии остаются у остальных M | **High** | дополняет J-H15 |
| B-5 | 28 | Async preemption (`SIGURG`) приносит `EINTR` в «сырые» syscall; тезис «в Go это абстрагировано» неверен | Medium | — |
| B-6 | 16, 6 | `CLONE_VFORK` замораживает только вызывающий поток, а не процесс | Medium | — |
| B-7 | 18, 22, 23, 42, 43 | Page fault на mmap-файле невидим для планировщика Go: M блокируется вместе с P | Medium | — |
| B-8 | 22, 35 | `O_NONBLOCK` не действует на обычные файлы | Medium | — |
| B-9 | 35, 38 | Go не «вычитывает сокет до EAGAIN»; корректность ET обеспечивает `pollDesc` | Medium | — |
| B-10 | 52, 53 | Неверный мотив запаса под `GOMEMLIMIT`: стеки и метаданные рантайма входят в лимит | Medium | — |
| B-11 | 51 | Кастомный `Resolver.Dial` ломает TCP-fallback (усечённый ответ без ошибки) и не отменяет `search`/`ndots` | Medium | — |
| B-12 | 48 | `SetReadDeadline` один раз на соединение — абсолютный срок, а не idle-таймаут | Medium | — |
| B-13 | 52, 5, 2 | Неудачный `clone` для нового M в Go — фатальная ошибка процесса, а не мягкий `EAGAIN`; `RLIMIT_NPROC` — на UID хоста | Medium | — |
| B-14 | 21 (19, 20) | В контейнере бесконечная рекурсия кончается OOM-kill раньше, чем `stack overflow` | Medium | — |
| B-15 | 42, 46, 39, 41 | «Идиоматичные» листинги глотают ошибки `Flush`/`Sync`/`Close` | Medium | дополняет J-H21 |
| B-16 – B-29 | разные | Мелкие пропуски и неточные формулировки | Low | — |

---

## 1. Находки, которые меняют выводы брифа

### B-1. `TCPListener.File()` + `file.Fd()` делает слушающий сокет блокирующим; `ln.Close()` и `server.Shutdown()` зависают (ст. 49, строки 182–191) · High

- **Статья / раздел:** ст. 49, «Взаимодействие Go runtime с очередями», листинг, шаг 2 «Альтернативный низкоуровневый путь через TCPListener и raw fd».
- **Утверждение:** `file, err := tcpListener.File(); … unix.SetsockoptInt(int(file.Fd()), …)` подано как безопасная «демонстрация работы с дескриптором».
- **Почему важно:**
  - Бриф отклонил G2 п.4 (R4, R10, K3) на том основании, что `File()` не переводит сокет в блокирующий режим. Само по себе это верно, но листинг статьи следом вызывает **`file.Fd()`**, а этот вызов режим меняет.
  - `net` создаёт файл через `newUnixFile` с флагом `nonblock`. `(*os.File).fd()` для такого файла вызывает `pfd.SetBlocking()`.
  - `dup` разделяет open file description, а `O_NONBLOCK` — флаг именно этого описания. Поэтому **исходный listener тоже становится блокирующим**.
  - Последствия:
    1. `Accept` занимает поток ОС.
    2. `ln.Close()` ждёт, пока завершится висящий `accept(2)`, то есть до следующего входящего соединения.
    3. `server.Shutdown()` в том же листинге висит по той же причине.
  - Если фактчекер последует R4/R10, он закрепит в тексте ложную безопасность этого паттерна.
- **[эксперимент]** Go 1.27.1: `nonblock before: true` → после `File()` + `Fd()` → `nonblock after: false`; `ln.Close()` при заблокированном `Accept` не вернулся за 2 с.
- **Улики / источники:**
  - `os/file_unix.go:70–85` (`fd()` → `f.pfd.SetBlocking()`);
  - комментарий к `net_newUnixFile` в `os/file_unix.go` («a nonblocking network connection will become blocking if code calls the Fd method»);
  - `net/fd_unix.go:170–180` (`dup` → `newUnixFile`);
  - документация `(*os.File).Fd` («SetDeadline methods will stop working»);
  - man 2 fcntl (`F_SETFL` действует на open file description).
- **Что предложить в правке:** использовать `ln.(*net.TCPListener).SyscallConn()` + `RawConn.Control`. Если нужен дескриптор, вызывать `Fd()` только на копии, которая не делит open file description с работающим listener, и помнить, что он станет блокирующим.
- **Приоритет: High.**

### B-2. `RawSyscall` с блокирующим вызовом подвешивает **всю** программу на ближайшей сборке мусора (ст. 2, строки 142–146; Interview п.1, строка 183) · High

- **Статья / раздел:** ст. 2, Gotcha «Syscall vs RawSyscall».
- **Утверждение статьи:** «вы намертво заморозите системный тред M вместе с P, и все горутины в этой очереди встанут намертво».
- **Позиция брифа (S 2.9, Medium):** «другие P могут украсть горутины из local runq; блокируется только P + M».
- **Почему важно:** статья недоговаривает, а предложенная брифом правка вносит ошибку.
  - Горутина в `RawSyscall` остаётся в `_Grunning`, P — в `_Prunning`, `entersyscall` не вызывается.
  - `syscall.RawSyscall` помечен `//go:nosplit`, а внутри зовёт ассемблерный `internal/runtime/syscall/linux.Syscall6`. Для такого PC `isAsyncSafePoint` возвращает false, поэтому `SIGURG` не может вытеснить горутину. После обработчика сигнала (`SA_RESTART`) syscall просто перезапускается.
  - `stopTheWorld` (GC, `GOMAXPROCS(n)`, `ReadMemStats`, профилирование) ждёт остановки всех P бесконечно. **Встаёт весь процесс**, а не одна очередь.
  - Это реальная причина правила «RawSyscall нельзя для блокирующих вызовов» (документация `x/sys/unix`).
- **[эксперимент]** Go 1.27.1: горутина делает `syscall.RawSyscall(SYS_READ)` на пустом pipe, затем вызывается `runtime.GC()` — процесс висит (`timeout 6` → exit 124). Контроль с `syscall.Syscall` — GC возвращается за 0,6 мс.
- **Улики / источники:** `syscall/syscall_linux.go:51–68`; `runtime/preempt.go` (`isAsyncSafePoint`: ветка `FuncFlagAsm` → false); `runtime/proc.go` (`stopTheWorldWithSema`, ожидание `sched.stopwait`).
- **Рекомендация фактчекеру:** не принимать правку S 2.9 в предложенном виде. Формулировка: «M блокируется вместе с P; другие P украдут горутины из очереди, но первый же stop-the-world (GC, `runtime.GOMAXPROCS`, `ReadMemStats`) остановит весь процесс навсегда».
- **Приоритет: High.**

### B-3. Хук `Control` из ответа на Interview не меняет keepalive у принятых соединений (ст. 47, строки 253–310) · High

- **Статья / раздел:** ст. 47, Interview про `net.ListenConfig{KeepAlive}` и листинг `keepAliveControl`.
- **Утверждение:** чтобы задать свои `TCP_KEEPIDLE`/`TCP_KEEPINTVL`, «воспользуйтесь хуком `Control` в `net.ListenConfig` … до вызова `listen()`».
- **Почему важно:** бриф (J-H12) ловит устаревшее описание дефолтов и неиспользуемый импорт. Но даже после исправления компиляции рецепт не работает.
  - Для каждого принятого соединения `TCPListener.accept` вызывает `newTCPConn(fd, ln.lc.KeepAlive, ln.lc.KeepAliveConfig, …)`.
  - При `KeepAlive == 0` это включает keepalive с дефолтами Go (idle 15 с, interval 15 с, count 9) и перезаписывает значения, которые сокет унаследовал от listener.
  - Читатель уверен, что получил 30/10, а в продакшене работает 15/15.
- **[эксперимент]** Go 1.27.1: `Control` ставит на listener `KEEPIDLE=30`, `KEEPINTVL=10`; у принятого соединения `getsockopt` возвращает `KEEPIDLE=15 KEEPINTVL=15`.
- **Улики / источники:** `net/tcpsock_posix.go:158–164`, `net/tcpsock.go:289–308` (`newTCPConn` → `SetKeepAliveConfig`); документация `net.ListenConfig.KeepAlive` / `KeepAliveConfig` (Go 1.23).
- **Правильные варианты для правки:** `net.ListenConfig{KeepAliveConfig: net.KeepAliveConfig{Enable: true, Idle: 30*time.Second, Interval: 10*time.Second, Count: …}}` (Go ≥ 1.23) или `SetKeepAliveConfig` на каждом принятом `*TCPConn`. Вариант `KeepAlive: -1` + `Control` полагается на наследование опций accepted-сокетом в Linux (`tcp_create_openreq_child`); его надо проверить отдельно.
- **Приоритет: High.**

### B-4. Сброс capabilities через `unix.Capset` в Go действует только на один поток ОС (ст. 58, строки 233–253; ст. 57, строки 111–118 и Gotcha 240–242) · High

- **Статья / раздел:** ст. 58, `dropPrivileges()`; ст. 57, «Иерархия и хранение», Gotcha про `execve`.
- **Утверждение:** `unix.Capset(...)` «убирает все capabilities» процесса и «оставляет только `CAP_NET_BIND_SERVICE`»; capabilities описаны как свойство процесса.
- **Почему важно:** бриф (J-H15) ловит `unix.CapHeader`, невозможность поднять права после обнуления и `os.Chown`. Но он пропускает главное.
  - `capset(2)` и `prctl(PR_CAP_AMBIENT…)` меняют credentials **только вызывающего потока**.
  - `unix.Capset` — это `RawSyscall(SYS_CAPSET)`, без рассылки по потокам. Go-процесс многопоточен: остальные M сохраняют полный набор.
  - Горутины мигрируют между M, поэтому код после «сброса» может исполняться на потоке с полными правами. Это та же проблема, что `setuid` до Go 1.16, только для capabilities, и здесь `syscall` её не решает.
  - Для учебника по безопасности это опасная формулировка.
- **Улики / источники:**
  - `golang.org/x/sys@v0.46.0/unix/zsyscall_linux.go:524–530` (`Capset` = `RawSyscall`);
  - man 2 capset, man 7 capabilities («per-thread attributes»);
  - документация `syscall.AllThreadsSyscall` (и `ENOTSUP` при cgo, J-H15);
  - `kernel.org/pub/linux/libs/security/libcap/cap` + `psx` (рассылка на все потоки);
  - systemd `CapabilityBoundingSet=`/`AmbientCapabilities=`, Kubernetes `securityContext.capabilities.drop` (права задаются до `execve`).
- **Приоритет: High.**

---

## 2. Medium

### B-5. Async preemption приносит `EINTR` в «сырые» системные вызовы (ст. 28, строки 178–181; связано со ст. 2, 22, 41, 44, 45) · Medium

- **Утверждение (28:180):** «В Go это абстрагировано: netpoller и стандартная библиотека автоматически перезапускают syscall…».
- **Почему важно:**
  - С Go 1.14 рантайм постоянно шлёт потокам `SIGURG`. Stdlib оборачивает вызовы в `ignoringEINTR`, а прямые вызовы через `syscall` и `x/sys/unix` этого не делают. Именно такие вызовы модуль массово показывает: `syscall.Fdatasync`, `unix.Mmap`, `unix.Capset`, `syscall.Setpriority`, `unix.SchedSetaffinity`, `Statfs`.
  - Обработчики Go ставятся с `SA_RESTART`, но часть вызовов не перезапускается никогда: `epoll_wait`, `nanosleep`, `futex` с таймаутом, `poll`/`select`, `recv` с `SO_RCVTIMEO` (man 7 signal, «Interruption of system calls»). C-код под cgo тоже видит `EINTR`.
  - Go 1.14 release notes прямо требуют обрабатывать `EINTR` в таких программах.
  - Бриф упоминает `SIGURG` только как «шум в strace» (24.10, 28.8).
- **Источники:** Go 1.14 release notes (раздел Runtime, async preemption, `EINTR`); `internal/poll/fd_posix.go` (`ignoringEINTR`); `runtime/signal_unix.go` (`setsig` с `_SA_RESTART`); man 7 signal.
- **Приоритет: Medium.**

### B-6. `CLONE_VFORK` приостанавливает только вызывающий поток, а не процесс (ст. 16, строки 108–111 и 160–162; ст. 6, строка 202) · Medium

- **Утверждение (16:111):** «Флаг `CLONE_VFORK` замораживает родительский процесс до тех пор, пока потомок не вызовет `execve()`, полностью исключая дублирование страниц и гарантируя защиту от deadlock».
- **Почему важно:**
  - По man 2 vfork (NOTES) в многопоточном процессе приостанавливается **только вызывающий поток**. Остальные M Go-процесса (GC-воркеры, sysmon, другие горутины) продолжают работать и пишут в ту же память, которую через `CLONE_VM` видит потомок.
  - Именно поэтому `forkAndExecInChild` написан как `nosplit`-код без аллокаций, а Go держит `syscall.ForkLock` для `CLOEXEC`.
  - «Гарантия от deadlock» следует не из заморозки процесса, а из того, что потомок не трогает рантайм. Бриф разбирает COW в ст. 16 (J-H23), но не эту модель.
- **Источники:** man 2 vfork (NOTES), man 2 clone (`CLONE_VFORK`); `syscall/exec_linux.go` (комментарии к `forkAndExecInChild1`), `syscall/exec_unix.go` (`ForkLock`).
- **Приоритет: Medium.**

### B-7. Page fault на mmap-отображении невидим для планировщика Go (ст. 18 целиком; ст. 22:134; ст. 23:120 и 136; ст. 42 «mmap»; ст. 43 `mapLargeFile`) · Medium

- **Утверждение:** mmap подаётся как универсально выгодная замена `read` («чтение работает как доступ к RAM», «альтернатив mmap нет»). О поведении в Go не говорится ничего.
- **Почему важно:**
  - Major fault на файловой странице ждёт диска, но происходит в user-коде: горутина в `_Grunning`, P в `_Prunning`. `retake` отбирает P только у потока в syscall, поэтому P простаивает вместе с M.
  - При небольшом `GOMAXPROCS` (контейнеры) случайный доступ к холодному mmap-файлу останавливает обработку всех горутин этого P и задерживает stop-the-world.
  - Этим mmap принципиально отличается от `pread`, где работает hand-off. Бриф затрагивает механизм только в ст. 13 (13.3, swap, Interview); статьи, которые продвигают mmap как инструмент для Go, этого предупреждения не содержат.
- **Источники:** `runtime/proc.go` (`retake`: условие `s == _Psyscall`/`syscallsp`); man 2 mmap; обсуждения в Go issue tracker о mmap и планировщике (bbolt, `golang/go` «mmap page faults block P»), подобрать конкретный номер.
- **Приоритет: Medium.**

### B-8. `O_NONBLOCK` не действует на обычные файлы (ст. 22, строка 149; ст. 35, строки 96–131) · Medium

- **Утверждение (22:149):** «Blocking: read/write/accept без `O_NONBLOCK`. Non-blocking: с флагом `O_NONBLOCK` или через epoll/kqueue»; ст. 35 подаёт неблокирующий режим как универсальное свойство I/O.
- **Почему важно:**
  - Для регулярных файлов и блочных устройств Linux игнорирует `O_NONBLOCK` (man 2 open): `read` при промахе page cache всё равно спит.
  - Это ключ к пониманию, почему дисковый I/O в Go всегда занимает поток M, почему epoll отвергает регулярные файлы (`EPERM`) и зачем нужны io_uring или пул потоков.
  - Ст. 38:128 говорит верно, так что внутри модуля есть противоречие. Бриф отмечает только «epoll и обычные файлы» (36.9, Low), не сам `O_NONBLOCK`.
- **Источники:** man 2 open (`O_NONBLOCK`: «has no effect for regular files and block devices»); man 7 epoll; `os/file_unix.go` (`newFile`: `kindOpenFile` → `pfd.Init` → `epoll_ctl` даёт `EPERM` → файл не pollable).
- **Приоритет: Medium.**

### B-9. Go не «вычитывает сокет до EAGAIN» (ст. 35, строки 243–246; ст. 38, строка 124; ст. 36, Go-раздел) · Medium

- **Утверждение (35:246, 38:124):** «Сетевой поллер рантайма и `netFD` обязаны в цикле вычитывать все доступные байты до получения `EAGAIN`, иначе оставшиеся байты застрянут…».
- **Почему важно:**
  - `poll.FD.Read` делает **один** `read(2)` и возвращает сколько есть. Паркуется он только при `EAGAIN`.
  - Edge-triggered корректен потому, что готовность запоминается в `pollDesc` (`rg`/`wg`, `pdReady`), а не потому, что кто-то дочитывает сокет. Следующий `Read` просто снова зовёт `read(2)`.
  - Классический контракт ET из C-мира ошибочно приписан Go. Читатель делает неверные выводы: будто частичное чтение в Go опасно, будто нужен цикл «до EAGAIN», будто `bufio` «теряет» уведомления.
  - Бриф разбирает ONESHOT и момент регистрации (J-H7), но не это.
- **Источники:** `internal/poll/fd_unix.go` (`(*FD).Read`: цикл `for { n, err := ignoringEINTRIO(syscall.Read…); if err == EAGAIN && pollable { waitRead; continue } … return }`); `runtime/netpoll.go` (`pollDesc`, `netpollblock`, `pdReady`).
- **Приоритет: Medium.**

### B-10. Неверное обоснование запаса под `GOMEMLIMIT` (ст. 52, строки 202–203 и 229–234; ст. 53, строка 234) · Medium

- **Утверждение (52:203):** «Оставшиеся 15–20% резервируются под стек горутин, метаданные рантайма и Page Cache»; 52:234: «запас жизненно необходим ядру для размещения стеков горутин, … метаданных рантайма и накладных расходов сборщика мусора».
- **Почему важно:**
  - По документации `SetMemoryLimit` лимит «includes all memory mapped, managed, and not released by the Go runtime». Стеки горутин и метаданные GC **уже внутри** лимита.
  - Запас нужен для памяти вне рантайма: cgo/C-аллокации, отображения бинарника и mmap-файлов (bbolt, ст. 18), а также page cache, tmpfs и сокетные буферы, которые memcg учитывает в `memory.current`.
  - Неверная модель ведёт к неверному расчёту: например, сервис с большим mmap-индексом получит OOM-kill при «правильном» запасе 15%. Бриф говорит, что `GOMEMLIMIT` мягкий (17.5, 63.8), но не про состав лимита.
- **Источники:** `runtime/debug/garbage.go:181–195`; go.dev/doc/gc-guide («Memory limit»); `Documentation/admin-guide/cgroup-v2.rst` (что учитывается в `memory.current`).
- **Приоритет: Medium.**

### B-11. Кастомный `net.Resolver` из листинга ломает TCP-fallback и не обходит `search`/`ndots` (ст. 51, строки 143–184) · Medium

- **Утверждение:** резолвер с `PreferGo: true` и `Dial`, который всегда возвращает `DialContext(ctx, "udp", "1.1.1.1:53")`, подан как «защита от сбоев системного `/etc/resolv.conf`».
- **Почему важно:**
  1. **Усечённые ответы:** `Dial` игнорирует аргумент `network`. Когда ответ приходит с флагом TC, Go повторяет запрос по `"tcp"`, получает снова UDP-соединение (`PacketConn`) и возвращает усечённый ответ **без ошибки**.
  2. **`search`/`ndots` продолжают работать:** список имён по-прежнему строится из `resolv.conf`. В поде Kubernetes на 1.1.1.1 уйдут запросы `example.com.default.svc.cluster.local` и подобные (лишние NXDOMAIN, задержки), а внутрикластерные имена не разрешатся вообще.
  3. **Подмена адреса:** `Dial` подменяет любой `address`, включая адреса из `resolv.conf`. Это надо явно оговорить.
- **Источники:** `net/dnsclient_unix.go:169–216` (`exchange`: выбор `PacketConn` против stream и ветка `h.Truncated && network == "udp"`); `net/dnsclient_unix.go` (`nameList`); документация `net.Resolver.Dial`.
- **Приоритет: Medium.**

### B-12. `SetReadDeadline` — абсолютный срок, а не idle-таймаут (ст. 48, строки 243–267) · Medium

- **Утверждение:** в `handleConn` дедлайны выставлены один раз «для защиты от медленных клиентов (Slowloris атаки)», дальше идёт цикл эхо-чтения.
- **Почему важно:**
  - В Go deadline — абсолютный момент времени, действующий на все будущие операции. Любое, даже активное соединение будет разорвано через 30 с после подключения.
  - Защиты от Slowloris это тоже не даёт: медленный клиент укладывается в 30 с.
  - Документация `net.Conn` прямо предписывает для idle-таймаута продлевать дедлайн после каждого успешного `Read`/`Write`. Бриф упоминает дедлайны только как пропуск (38.10).
- **Источники:** документация `net.Conn.SetDeadline` («An idle timeout can be implemented by repeatedly extending the deadline…»); `net/http.Server` (`ReadHeaderTimeout`, `IdleTimeout`) как пример разделения таймаутов.
- **Приоритет: Medium.**

### B-13. Неудачное создание потока в Go фатально; `RLIMIT_NPROC` считается по UID хоста (ст. 52, строка 147; ст. 5, строка 294; ст. 2, строка 179) · Medium

- **Утверждение (52:147):** «При исчерпании лимита [`pids.max`] системный вызов `clone()` вернёт ошибку ядра `EAGAIN`»; 5:294 описывает `RLIMIT_NPROC` как лимит «процессов и потоков пользователя» без оговорок.
- **Почему важно:**
  1. **Фатальность:** для рантайма Go `EAGAIN` от `clone` при создании M — не мягкая ошибка. `newosproc` печатает «runtime: failed to create new OS thread (have N already; errno=11)», подсказку «may need to increase max user processes (ulimit -u)» и вызывает `throw("newosproc")`. Падает весь процесс.
  2. **Масштаб лимита:** `RLIMIT_NPROC` считается по **real UID на всём хосте**, если нет user namespace. Контейнеры, запущенные под одним UID (1000, 65534), исчерпывают лимит друг за друга.
  3. **Пропуск:** статьи не связывают это с лавиной блокирующих syscall (ст. 2, 62) — типичным путём к краху. В брифе этого нет.
- **Источники:** `runtime/os_linux.go:190–200`; man 2 setrlimit (`RLIMIT_NPROC`: «number of extant process (or, more precisely on Linux, threads) for the real user ID»); `Documentation/admin-guide/cgroup-v2.rst` (pids).
- **Приоритет: Medium.**

### B-14. В контейнере бесконечная рекурсия заканчивается OOM-kill, а не `stack overflow` (ст. 21, раздел «Когда Go всё же падает»; ст. 19 и 20, строки про лимит 1 ГБ) · Medium

- **Утверждение:** при переполнении стека «произойдёт `fatal error: stack overflow`» и выведется диагностика (ст. 20:155, 19:229, 21:126–134).
- **Почему важно:**
  - Стек удваивается до 512 МиБ: следующий шаг 1 ГиБ уже больше `maxstacksize = 1e9`, и тогда срабатывает `throw`. Последнее копирование 256 → 512 МиБ на время требует около 768 МиБ.
  - В типичном поде с `memory.max` 512 МиБ – 1 ГиБ процесс получит `SIGKILL` от cgroup OOM **до** сообщения рантайма, без единой строки трейса. Диагностика «смотрите fatal error» в контейнере не работает.
  - Практическое следствие: в контейнерах ставить `debug.SetMaxStack`. Бриф разбирает механизм роста стека (J-H2), но не это следствие.
- **Источники:** `runtime/stack.go` (`newstack`: проверка `newsize > maxstacksize`, `copystack`); `runtime/proc.go:164–166`; документация `runtime/debug.SetMaxStack`.
- **Приоритет: Medium** (зависит от окружения).

### B-15. «Идиоматичные» листинги глотают ошибки `Flush`/`Sync`/`Close` (ст. 42, строки 140–156; ст. 46, строки 316–325; ст. 39, строки 143–147; ст. 41, строки 161–165) · Medium

- **Утверждения:**
  - ст. 42: `defer w.Flush()` с комментарием «принудительный сброс остатка буфера»;
  - ст. 46: `_ = gc.writer.Flush(); _ = gc.file.Sync()` в «групповом коммите WAL»;
  - ст. 39, 41: `defer f.Close()` после записи, которая должна быть durable.
- **Почему важно:**
  - Ошибка отложенного `Flush` (`ENOSPC`, `EDQUOT`, `EIO`) теряется: функция возвращает `nil`, а данные не записаны.
  - В `GroupCommitter` проглоченный `fsync` с `EIO` после fsyncgate означает, что страницы уже помечены чистыми. Вызывающий считает данные зафиксированными, а повтор не поможет.
  - Ошибки отложенной записи (NFS, квоты) могут прийти только из `close(2)` (man 2 close).
  - Модуль сам называет эти паттерны production-ready и посвящает статьи 39–41 durability. Бриф разбирает другие дефекты `GroupCommitter` (J-H21) и fsyncgate (39.8), но не отброшенные ошибки в коде.
- **Источники:** документация `bufio.Writer` (ошибка «липкая» и возвращается из `Flush`); man 2 close (NOTES: «Not checking the return value of close() is a common but nevertheless serious programming error»); man 2 fsync; PostgreSQL wiki «Fsync Errors».
- **Приоритет: Medium.**

---

## 3. Low

| ID | Ст. / строки | Утверждение | Почему важно | Источник |
|---|---|---|---|---|
| B-16 | 6:47–50 | «Если бы создание процесса было одним монолитным вызовом, ядру пришлось бы копировать все страницы сразу» | Причинность перевёрнута: spawn-модель (`CreateProcess`, `posix_spawn`) не копирует ничего; COW придуман, чтобы удешевить именно `fork` | Baumann et al., «A fork() in the road» (HotOS 2019); man 3 posix_spawn |
| B-17 | 6:114 | «Для статически скомпилированных программ (большинства Go-бинарников) управление передаётся на `_start`» | Точка входа Go — `_rt0_amd64_linux` (ст. 1:57 говорит верно, внутреннее противоречие). При cgo-сборке с `net`/`os/user` бинарник динамический и стартует через `ld.so` | `runtime/rt0_linux_amd64.s`; `readelf -l` (PT_INTERP) |
| B-18 | 9:136 | Pipeline stalls: «в `top` нагрузка может отображаться как умеренная (CPU 50%)» | Такты в stall-е для ОС — занятый CPU; `top` покажет полную загрузку. Видны stall-ы только через IPC (`perf stat`), иначе вывод для диагностики неверный | man perf-stat; B. Gregg, «Linux Performance» (CPU utilization vs IPC) |
| B-19 | 36:294 | «Go регистрирует события с `EPOLLRDHUP`, позволяя мгновенно узнавать о закрытии TCP-соединения клиентом без пробного `read`» | В Go RDHUP только будит ожидающих; API о закрытии пира не сообщает без `Read` (`io.EOF`). Простаивающее соединение без висящего `Read` ничего не узнает (поэтому `net/http` держит фоновое чтение) | `runtime/netpoll_epoll.go` (обработка `EPOLLRDHUP`); `net/http/server.go` (`backgroundRead`) |
| B-20 | 2:95 | Бинарник без cgo в `scratch` «запустится без единой системной библиотеки» | Запустится, но HTTPS упадёт без CA-бандла (`x509: certificate signed by unknown authority`), `time.LoadLocation` — без tzdata, `os/user` — без `/etc/passwd`. Частая практическая ловушка | `crypto/x509` (`root_linux.go`), `time/tzdata`, `os/user` |
| B-21 | 8:146–155 | Описание `LockOSThread` | Пропущено: если горутина завершится, не вызвав `UnlockOSThread`, поток уничтожается (Go ≥1.10). На этом держится паттерн `setns`; новые M создаются через template thread, чтобы не наследовать состояние | документация `runtime.LockOSThread`; Go 1.10 release notes; `runtime/proc.go` (`templateThread`) |
| B-22 | 29:15 | «Запускается с `&` или через `nohup` … Если вы закроете терминал, … фоновый процесс умрёт» | `nohup` как раз игнорирует `SIGHUP`; ставить его в один ряд с `&` неверно | man 1 nohup |
| B-23 | 58:217 | Бинарник, скопированный через `scp` или собранный `go build`, получит `user_home_t` | Новый файл наследует контекст каталога назначения (в `/usr/local/bin` — `bin_t`). Типичная ловушка — `mv` из `$HOME`, который сохраняет метку | Red Hat SELinux Guide («Maintaining SELinux Labels»: cp vs mv) |
| B-24 | 63:213–214 | «Используйте `x/sys/unix` и `syscall.SetNonblock` — это позволяет одному потоку обслуживать тысячи соединений» | Неблокирующий fd вне netpoller даёт `EAGAIN` и busy-loop (ст. 35 сама предупреждает). Правильно — `os.NewFile` / `net.FileConn` / `RawConn.Read` с интеграцией в netpoller | `os/file_unix.go` (`newFile`, `kindNonBlock`); документация `syscall.RawConn` |
| B-25 | 1:76–78 | `GOMAXPROCS > N_CPU` → «тяжёлая пробуксовка (thrashing)», «львиная доля тактов на context switch» | Простаивающие P не жгут CPU. Реальная цена — больше dedicated GC-воркеров (25% от P), spinning M и сгоревшая CFS-квота. «Thrashing» — термин из подкачки | `runtime/mgcpacer.go` (`gcBackgroundUtilization`); `runtime/proc.go` (spinning M) |
| B-26 | 41:204 | «При падении PHP-FPM воркера данные [после `file_put_contents`] могут потеряться» | Данные, отданные `write()`, переживают крах процесса (они в page cache); теряются при потере питания или краше ядра. Реальная ловушка для Go другая: `log.Fatal`/`os.Exit` пропускают отложенный `w.Flush()` (связано с B-15) | man 2 write; документация `os.Exit` |
| B-27 | 12:166–168 | «Ядро изначально маппит все анонимные страницы на одну Zero Page … реальная аллокация при первой записи (Copy-On-Write)» | Изначально PTE нет вовсе; zero page подставляется только при fault на чтение, при fault на запись страница выделяется сразу | `mm/memory.c` (`do_anonymous_page`) |
| B-28 | 30:121–124 | Socket activation даёт «zero-downtime деплой: новый процесс получает [сокет], старый завершается после `SIGUSR1`» | `systemctl restart` сначала останавливает старый процесс, потом запускает новый; соединения ждут в backlog. Перекрытие инстансов требует шаблонных юнитов или FD store (`FileDescriptorStoreMax=`) | man systemd.socket, systemd.service (`FileDescriptorStoreMax`) |
| B-29 | 48:327 | Итог: «настройка глубины очереди `SO_BACKLOG`» | Опции сокета `SO_BACKLOG` в Linux нет (в J-H5 указан только `SO_MAX_CONN` в ст. 49); backlog задаётся только аргументом `listen(2)` | `include/uapi/asm-generic/socket.h`; man 2 listen |

---

## 4. Замечания для следующего шага конвейера

1. **B-1 и B-2 противоречат решениям брифа** (R4, R10, K3 и правке S 2.9). При исправлении статей 2 и 49 опираться на эти пункты, а не на § 8 брифа.
2. **B-3 и B-4 делают рекомендованные исправления J-H12 и J-H15 неполными.** Код, который просто начнёт компилироваться, всё равно будет делать не то, что обещает текст.
3. **B-7, B-8, B-9 и B-13** — одна тема: где граница между сетевым I/O, который Go мультиплексирует, и всем остальным, что держит поток M. Её стоит согласовать сквозной правкой статей 22, 35, 38, 52 и 62, как это сделано в брифе для C-HANDOFF.
4. **B-15** дополняет кластер C-COMPILE: в «компилирующихся» листингах тоже есть смысловые дефекты, которые `go vet` не ловит (`errcheck` поймает).
5. Программы для экспериментов B-1, B-2, B-3 лежат в scratchpad сессии (`fdtest`, `rawtest`, `katest`). Их легко воспроизвести за минуту на любом `go ≥ 1.23`.
