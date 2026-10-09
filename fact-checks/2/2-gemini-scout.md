# 🕵️‍♂️ Исследовательский бриф первичного фактчекинга (Scout Brief): Модуль 2 «Устройство и работа ОС»

> **Роль:** First-pass fact-check research scout.  
> **Цель:** Широкий и независимый анализ всех 63 статей Модуля 2 на предмет потенциально некорректных, устаревших, вводящих в заблуждение, упрощенных, неполных, версионно-чувствительных, машинно-зависимых или педагогически рискованных утверждений, ошибок в листингах кода, а также скрытых технических белых пятен (blind spots).  
> **Целевой артефакт:** `2-gemini-scout.md`

---

## 📌 Паспорт модуля и обзор охвата

* **Директория:** `sources/2. Устройство и работа ОС/`
* **Количество статей:** 63 (от фундаментальной природы процессов, форков, потоков и планировщиков ядра CFS/EEVDF до виртуальной памяти, сигналов, подсистем IPC, сокетов, netpoller, VFS, cgroups v1/v2, Linux Security и архитектурного моста между рантаймом Go и ядром ОС).
* **Суммарный объем:** ~15 676 строк Markdown.
* **Листинги кода:** 79 фрагментов на Go (включая работу с низкоуровневыми пакетами `syscall`, `golang.org/x/sys/unix`, `unsafe`, работу с сетью, файловыми дескрипторами и сигналами).
* **Технический стек:** Ядро Linux (от 3.x/4.x до 6.6+ EEVDF), Go (от 1.14 до 1.27.1), POSIX/glibc, x86-64 / ARM64, systemd, cgroups v1/v2, eBPF, namespaces.

---

## 🧭 Каталог кандидатов на углубленный фактчекинг

---

### Кандидат 1: Вымышленные системные вызовы Go для работы с Shared Memory (`ShmOpen`, `ShmUnlink`)
* **article/section:** `32. Разделяемая память (Shared Memory). POSIX и System V shm.md` / `## 4. Практика на Go: Работа с POSIX Shared Memory`
* **claim:** Листинг демонстрирует создание и управление сегментом разделяемой памяти через прямой пакет `syscall`:
  ```go
  fd, err := syscall.ShmOpen("/my_shared_seg", os.O_CREAT|os.O_RDWR, 0666)
  err = syscall.ShmSetSize(fd, 4096)
  defer syscall.ShmUnlink("/my_shared_seg")
  ```
* **why it needs checking:** Функций `syscall.ShmOpen`, `syscall.ShmSetSize` и `syscall.ShmUnlink` **не существует** ни в стандартном пакете `syscall`, ни в расширенном пакете `golang.org/x/sys/unix`. В ОС Linux `shm_open(3)` и `shm_unlink(3)` не являются системными вызовами ядра — это библиотечные обертки `glibc` (`librt`), которые под капотом создают именованные файлы в псевдофайловой системе `tmpfs`, смонтированной в `/dev/shm`. Системного вызова `shmsetsize` в Linux также не существует (размер файла меняется стандартным вызовом `ftruncate(2)`). Данный код гарантированно не компилируется в Go (`undefined: syscall.ShmOpen`). Каноничный способ работы с POSIX Shared Memory в чистом Go без cgo — прямое открытие псевдофайла:
  ```go
  file, err := os.OpenFile("/dev/shm/my_shared_seg", os.O_CREATE|os.O_RDWR, 0666)
  err = file.Truncate(4096)
  ```
* **evidence/source needed:** Документация пакета `syscall` и `golang.org/x/sys/unix`; `man 3 shm_open`; `man 2 ftruncate`.
* **priority:** **High**

---

### Кандидат 2: Несуществующая опция сокета `1024` и нерабочая настройка Backlog
* **article/section:** `49. Backlog, SYN Queue и Accept Queue.md` / `## 5. Практика: Управление Backlog в Go`
* **claim:** Листинг пытается динамически изменить размер очереди `listen` backlog скомпилированного листенера через `setsockopt`:
  ```go
  file, _ := tcpListener.File()
  _ = unix.SetsockoptInt(int(file.Fd()), unix.SOL_SOCKET, 1024, 65535)
  ```
* **why it needs checking:** 
  1. В ядре Linux константы опции сокета с номером `1024` на уровне `SOL_SOCKET` не существует.
  2. Размер backlog очереди `listen(2)` никогда не настраивается через `setsockopt`. В Linux backlog передается вторым аргументом непосредственно в системный вызов `listen(int sockfd, int backlog)`.
  3. В стандартной библиотеке Go размер backlog вычисляется при вызове `net.Listen` неявно внутри `src/net/sock_linux.go` путем чтения лимита ядра из `/proc/sys/net/core/somaxconn` (функция `maxListenerBacklog()`).
  4. Вызов `tcpListener.File()` дублирует файловый дескриптор через `dup(2)` и переводит сокет в блокирующий режим, что ломает интеграцию с Go Netpoller.
* **evidence/source needed:** `src/net/sock_linux.go` (`func maxListenerBacklog()`), `include/uapi/asm-generic/socket.h`, `man 2 listen`, `man 2 setsockopt`.
* **priority:** **High**

---

### Кандидат 3: Нерабочее «выравнивание» буфера для `O_DIRECT` и гарантированный `EINVAL`
* **article/section:** `43. Прямой ввод-вывод (Direct IO) и Zero Copy.md` / `## 3. Direct IO в Go: Как обойти кэш страниц`
* **claim:** В листинге утверждается, что срез выравнивается под требования Direct I/O путем добавления 4096 байт:
  ```go
  aligned := make([]byte, len(data)+4096)
  copy(aligned, data)
  n, err := f.Write(aligned[:len(data)])
  ```
* **why it needs checking:** 
  1. Вызов `make([]byte, ...)` аллоцирует память через рантайм-аллокатор Go (`mcache`), который выравнивает адреса только по границам классов размеров (8, 16, 32, 64 байт), но **никогда не гарантирует выравнивание базового адреса по границе страницы 4096 байт**.
  2. Флаг `O_DIRECT` в ядре Linux требует жесткого выравнивания как самого указателя буфера в памяти, так и смещения в файле, а также длины передаваемого буфера кратно размеру сектора диска (512 или 4096 байт). Передача среза `aligned[:len(data)]` произвольной длины гарантированно завершится системной ошибкой `EINVAL`.
  3. Для честного `O_DIRECT` в Go требуется либо аллокация через `unix.Mmap` / `posix_memalign`, либо вычисление смещения указателя с помощью `uintptr(unsafe.Pointer(&buf[0])) % 4096`, а длина записи должна быть строго кратна размеру сектора.
* **evidence/source needed:** `man 2 open` (раздел `O_DIRECT`); Linux Kernel Block Layer Architecture; `src/runtime/malloc.go`.
* **priority:** **High**

---

### Кандидат 4: Внутреннее противоречие: `EPOLLET` против `EPOLLONESHOT` в Netpoller Go
* **article/section:** `38. Как netpoller Go использует epoll, kqueue, IOCP.md` / `## Внутренности Netpoller` vs `## Резюме`
* **claim:** 
  - В разделах 2 и 3 (§ 116, 122) подробно и верно доказано, что Go netpoller работает исключительно в режиме Edge-Triggered (`EPOLLET`) и сознательно **не использует** `EPOLLONESHOT`, чтобы избежать лишних системных вызовов `epoll_ctl(EPOLL_CTL_MOD)`.
  - Однако в финальном резюме (пункт 2, строка 190) утверждается прямо противоположное:  
    *«2. Edge-Triggered vs Level-Triggered: Go использует Edge-Triggered (EPOLLET в Linux, EV_CLEAR в BSD) для снижения числа пробуждений. Флаги EPOLLONESHOT и EV_ONESHOT гарантируют точечный контроль за событиями, исключая гонки между потоками-планировщиками.»*
* **why it needs checking:** Прямое противоречие внутри одного документа. В исходном коде рантайма Go (`src/runtime/netpoll_epoll.go`) регистрация дескриптора производится строго с флагами `_EPOLLET | _EPOLLIN | _EPOLLOUT | _EPOLLRDHUP`. Флаг `EPOLLONESHOT` никогда не устанавливается, так как рантайм защищает состояние готовности горутины собственными атомиками в структуре `pollDesc` (`rg`, `wg`), исключая накладные расходы `EPOLL_CTL_MOD`.
* **evidence/source needed:** `src/runtime/netpoll_epoll.go` (`func netpollopen(fd uintptr, pd *pollDesc) int32`).
* **priority:** **High**

---

### Кандидат 5: Вымышленная архитектура сигналов: `sigwaitinfo` на одном потоке
* **article/section:** `28. Сигналы в Linux. Архитектура и надежная доставка.md` / `## 3. Go Runtime и сигналы: Модель обработки`
* **claim:** Утверждается, что Go при старте процесса блокирует все сигналы на всех потоках маской `rt_sigprocmask` и запускает одну специальную горутину, которая синхронно ожидает сигналы через вызов `sigwaitinfo(2)` или `sigtimedwait(2)`.
* **why it needs checking:** Это грубое искажение реальной модели обработки сигналов в Go:
  1. Синхронные сигналы исключений процессора (`SIGSEGV`, `SIGBUS`, `SIGFPE`) не могут быть заблокированы и не могут быть получены через `sigwaitinfo` на другом потоке — ядро посылает их ровно тому потоку OS (`M`), который выполнил недопустимую инструкцию.
  2. Асинхронные сигналы вытеснения (`SIGURG`, с Go 1.14) должны доставляться конкретному потоку `M` для вызова `runtime.asyncPreempt`.
  3. В действительности Go регистрирует глобальный обработчик сигналов через `rt_sigaction` с функцией `runtime.sigtramp` (написанной на ассемблере) с флагом `SA_ONSTACK`. Каждый поток `M` имеет свой альтернативный стек сигналов (`gsignal`), выделенный через `sigaltstack(2)`.
  4. Сигналы ядра перехватываются на том потоке, куда они прилетели, и только пользовательские сигналы (пакет `os/signal`) отправляются через канал нотификации горутине-диспетчеру.
* **evidence/source needed:** `src/runtime/os_linux.go`, `src/runtime/signal_unix.go`, `src/runtime/sys_linux_amd64.s` (`TEXT runtime·sigtramp(SB)`).
* **priority:** **High**

---

### Кандидат 6: Ложное утверждение о ненадежности и переупорядочивании дейтаграмм в UDS (`SOCK_DGRAM`)
* **article/section:** `27. Unix Domain Socket (UDS). Локальный IPC.md` / `## 1. Архитектура Unix Domain Sockets`
* **claim:** *"SOCK_DGRAM — ненадежный, сообщения могут теряться или приходить вне порядка (аналог UDP), но границы сообщений сохраняются."*
* **why it needs checking:** В ОС Linux сокеты домена UNIX (`AF_UNIX` / `AF_LOCAL`) типа `SOCK_DGRAM` работают целиком в оперативной памяти ядра через кольцевые буферы сокетов (`sk_buff`).
  1. Согласно `man 7 unix`: *"Unix domain datagram sockets are reliable and don't reorder datagrams"*.
  2. Они **гарантированно сохраняют порядок** отправки (FIFO) и **никогда не теряют сообщения** в пути. Если буфер сокета получателя полон, операция `send(2)` либо блокируется, либо немедленно возвращает ошибку `EAGAIN`/`ENOBUFS` (сообщение не выбрасывается ядром молча, как в сетевом UDP).
  3. Называть доменные дейтаграммы «ненадежными» — критическая фактологическая ошибка.
* **evidence/source needed:** `man 7 unix` (раздел "Socket types: SOCK_DGRAM"); Linux Kernel networking code `net/unix/af_unix.c`.
* **priority:** **High**

---

### Кандидат 7: Искажение механизма роста стека в Go: `mmap`, `madvise` и `SIGSEGV`
* **article/section:** `21. Переполнение стека (Stack Overflow). Защитные страницы, сегментированные стеки.md` / `## 4. Стек в Go: От сегментов к копированию`
* **claim:** Статья утверждает, что:
  1. Функция `newstack` аллоцирует новую память вызовом `mmap` и освобождает старый стек системным вызовом `madvise(MADV_DONTNEED)`.
  2. Копирование старого стека в новый происходит *«только если в старом стеке остались жизненно важные данные»*.
  3. Переполнение стека в Go детектируется защитной страницей (Guard Page) ядра через сигнал `SIGSEGV`, который перехватывается рантаймом.
* **why it needs checking:** 
  1. Выделение памяти под стеки горутин в Go (от 2 КБ до 32 КБ) происходит **без системных вызовов** из локального пула потока `mcache.stackcache` или глобального пула `stackpool`, и только для огромных стеков (>32 КБ) используется `stackLarge`. Никаких вызовов `mmap` и тем более `madvise(MADV_DONTNEED)` на каждый рост стека не происходит.
  2. При росте стек горутины копируется **всегда целиком** (`copystack`), так как все стековые фреймы активных функций содержат адреса возврата, локальные переменные и аргументы.
  3. В Go для горутин **нет защитных страниц ядра (Guard Pages)**. Проверка переполнения стека выполняется чисто программно компилятором: в прологе каждой функции вставляются инструкции сравнения текущего указателя стека `SP` со значением `g.stackguard0`. Если `SP < stackguard0`, вызывается функция `runtime.morestack`. Сигнал `SIGSEGV` не генерируется и ядро в этом не участвует.
* **evidence/source needed:** `src/runtime/stack.go` (`func newstack()`, `func copystack()`, `func stackalloc()`); Go Compiler ABI specification.
* **priority:** **High**

---

### Кандидат 8: Утверждение о работе `ltrace` без `ptrace` через `LD_PRELOAD`
* **article/section:** `24. strace, ltrace. Как устроена трассировка сисколлов и вызовов библиотек.md` / `## 3. ltrace: Трассировка динамических библиотек`
* **claim:** *"ltrace... в отличие от strace, он не требует прав на ptrace и работает практически полностью в user-space через механизм LD_PRELOAD."*
* **why it needs checking:** `ltrace` в операционной системе Linux фундаментально основан на системном вызове `ptrace(2)`.
  1. `ltrace` аттачится к целевому процессу через `ptrace(PTRACE_ATTACH)` или запускает его через `ptrace(PTRACE_TRACEME)`.
  2. Для перехвата вызовов динамических библиотек `ltrace` парсит таблицу PLT (Procedure Linkage Table) в ELF-файле процесса и с помощью `ptrace(PTRACE_POKETEXT)` заменяет инструкции входа в PLT на инструкцию программной точки останова (`INT 3` на x86/x86-64, опкод `0xCC`).
  3. Без разрешенного системного вызова `ptrace` (например, в Docker-контейнере без `--cap-add=SYS_PTRACE`) утилита `ltrace` аварийно завершается с ошибкой `ptrace: Operation not permitted`.
  4. Механизм `LD_PRELOAD` используется альтернативными инструментами (такими как `latrace`), но не классическим `ltrace`.
* **evidence/source needed:** `man 1 ltrace`; исходный код `ltrace` (`sysdeps/linux-gnu/trace.c`, `ptrace.c`).
* **priority:** **High**

---

### Кандидат 9: Неверный дефолтный резолвер для Darwin/macOS и фиктивный флаг `experimentalgo`
* **article/section:** `51. DNS глазами ОС. resolv.conf, NSS, libc getaddrinfo.md` / `## 4. Go Resolver: netgo против cgo`
* **claim:** 
  1. В сводной таблице платформ указано, что на macOS (Darwin) дефолтным резолвером является чистый Go-резолвер (`netgo`).
  2. В тексте заявляется о существовании отладочного режима `GODEBUG=netdns=experimentalgo`.
* **why it needs checking:** 
  1. В исходном коде Go (`src/net/conf.go`, функция `hostLookupOrder`) для платформ Darwin (macOS), iOS и Android жестко прописано использование системного резолвера через cgo:  
     *«Darwin and iOS always use the cgo resolver because the OS requires it for mDNS and VPN integration»*. Чистый Go-резолвер на macOS запускается только если сборка выполнена с тегом `netgo` или при полном отключении cgo (`CGO_ENABLED=0`).
  2. Значения `experimentalgo` в парсере `GODEBUG=netdns` никогда не существовало в кодовой базе Go (поддерживаются флаги вида `1`, `2`, `cgo`, `go`).
* **evidence/source needed:** `src/net/conf.go`, `src/net/net.go`, документация пакета `net`.
* **priority:** **High**

---

### Кандидат 10: Неэффективный `syscall.Setuid` в многопоточном Go и вымышленный `CAP_CLEAR`
* **article/section:** `57. Безопасность ядра. ACL, capabilities, namespaces, setuid.md` / `## 3. Практика: Сброс привилегий в Go`
* **claim:** Листинг сброса привилегий использует:
  ```go
  if err := syscall.Setuid(1000); err != nil { ... }
  ```
  и ссылается на очистку capabilities через `syscall.CAP_CLEAR`.
* **why it needs checking:** 
  1. В ядре Linux системный вызов `setuid(2)` изменяет UID **только для вызывающего потока ядра (kernel task / OS thread)**. В языке Go рантайм создает множество потоков ОС (`M`), и горутины произвольно мигрируют между ними. Вызов `syscall.Setuid` переключит UID только одного текущего потока `M`, оставив все остальные потоки процесса с привилегиями `root`, что создает катастрофическую дыру в безопасности.
  2. Начиная с Go 1.16 для изменения учетных данных процесса на всех потоках ядра был добавлен специальный механизм `syscall.AllThreadsSyscall(syscall.SYS_SETUID, ...)` (ранее для этого требовался cgo и библиотека glibc, реализующая POSIX-сигнальный трюк `NPTL`).
  3. Константы `syscall.CAP_CLEAR` не существует в Go.
* **evidence/source needed:** Go Issue #1435; Release Notes Go 1.16 (`syscall.AllThreadsSyscall`); `man 2 setuid` (Linux differences).
* **priority:** **High**

---

### Кандидат 11: Устаревшее безальтернативное утверждение об игнорировании cgroup CPU квот в Go
* **article/section:** `8. Процессы, потоки, волокна...md`, `52. Архитектура cgroups...md`, `54. cgroups v1 vs v2...md`, `62. Go runtime и системные ресурсы...md`
* **claim:** Статьи категорически утверждают, что Go не понимает ограничения CPU в контейнерах cgroups, всегда выставляет `GOMAXPROCS` по числу физических ядер хоста и требует обязательного ручного подключения внешней библиотеки `go.uber.org/automaxprocs`.
* **why it needs checking:** Начиная с релиза **Go 1.25** рантайм получил нативную поддержку автоматического распознавания лимитов CPU из cgroups v1 и v2 (`internal/runtime/cgroup`, флаг `GODEBUG=containermaxprocs=1`). Go теперь автоматически ограничивает значение `runtime.GOMAXPROCS` квотой контейнера без использования сторонних библиотек. Текст статей отражает состояние мира до Go 1.25.
* **evidence/source needed:** Go 1.25 Release Notes; Go Issue #33803; исходный код `src/internal/runtime/cgroup/cgroup.go` в Go 1.25+.
* **priority:** **High**

---

### Кандидат 12: Жесткая константа `TCP_TIMEWAIT_LEN` (60 секунд) в Linux vs теоретические 2MSL (120 с)
* **article/section:** `50. Состояние TIME_WAIT. Зачем оно нужно и как с ним жить.md` / `## 1. Анатомия TIME_WAIT: Зачем ждать 2MSL`
* **claim:** Утверждается, что состояние `TIME_WAIT` в Linux длится 2MSL, что строго составляет 120 секунд (2 минуты), и это время можно гибко настраивать системными параметрами.
* **why it needs checking:** В теории RFC 793 значение MSL принимается равным 60 секундам (2MSL = 120 с). Однако в сетевом стеке ядра Linux длительность `TIME_WAIT` захардкожена константой в заголовочном файле ядра:
  ```c
  #define TCP_TIMEWAIT_LEN (60*HZ) /* how long to wait to destroy TIME-WAIT state, about 60 seconds */
  ```
  В Linux сокет находится в `TIME_WAIT` **ровно 60 секунд**, и это значение невозможно изменить через `sysctl` без модификации и перекомпиляции ядра. Кроме того, важно отметить, что опция `tcp_tw_recycle` была полностью удалена из ядра начиная с Linux 4.12 из-за проблем с NAT.
* **evidence/source needed:** Ядро Linux: `include/net/tcp.h` (`TCP_TIMEWAIT_LEN`); RFC 793; `man 7 tcp`.
* **priority:** **Medium**

---

### Кандидат 13: Статус спящего потока в `futex` (`TASK_INTERRUPTIBLE` vs `TASK_UNINTERRUPTIBLE`)
* **article/section:** `33. Примитивы синхронизации ядра. Mutex, RWLock, Семафоры, Futex.md` / `## 4. Futex (Fast Userspace Mutex)`
* **claim:** Заявляется, что поток, засыпающий на вызове `futex(FUTEX_WAIT)`, переводится планировщиком ядра в состояние глубокого сна `TASK_UNINTERRUPTIBLE` (статус `D` в выводе `ps`), игнорируя любые сигналы.
* **why it needs checking:** В коде ядра Linux (`kernel/futex/waitwake.c`) системный вызов `futex` при ожидании устанавливает состояние задачи как `TASK_INTERRUPTIBLE`:
  ```c
  set_current_state(TASK_INTERRUPTIBLE);
  ```
  Поток, ждущий на `futex`, находится в состоянии прерываемого сна (статус `S`, а не `D`). При поступлении сигнала системный вызов прерывается с ошибкой `EINTR` (или перезапускается через `ERESTARTSYS`). Состояние `TASK_UNINTERRUPTIBLE` (`D`) используется для ожиданий ввода-вывода диска или блокировок страниц, а не пользовательских фьютексов.
* **evidence/source needed:** Исходный код ядра Linux `kernel/futex/waitwake.c`; `man 2 futex`.
* **priority:** **Medium**

---

### Кандидат 14: Недопустимость сокета в качестве источника для `sendfile(2)`
* **article/section:** `43. Прямой ввод-вывод (Direct IO) и Zero Copy.md` / `## 4. Zero Copy: splice, sendfile, vmsplice`
* **claim:** Статья заявляет, что системный вызов `sendfile` позволяет перекачивать данные напрямую как «из файла в сокет», так и «из сетевого сокета в файл» без участия пользователей.
* **why it needs checking:** Согласно документации ядра Linux `man 2 sendfile`:
  *«The in_fd argument must correspond to a file which supports mmap-like operations (i.e., it cannot be a socket)»*.
  Системный вызов `sendfile` в Linux **никогда не может читать из сокета**. В качестве `in_fd` допускается только файловый дескриптор с поддержкой mmap (регулярный файл). Для перекачки данных из сокета в сокет или из сокета в файл ядро предоставляет системный вызов `splice(2)` через промежуточный pipe, но не `sendfile`.
* **evidence/source needed:** `man 2 sendfile`; `man 2 splice`.
* **priority:** **Medium**

---

### Кандидат 15: Ошибка компиляции сигнатуры `syscall.Pipe2`
* **article/section:** `26. Pipe и FIFO. Межпроцессное взаимодействие через псевдофайлы.md` / `## 4. Практика на Go: Низкоуровневая работа с Pipe`
* **claim:** В листинге вызов создания неблокирующего пайпа записан как:
  ```go
  fds, err := syscall.Pipe2(syscall.O_NONBLOCK)
  ```
* **why it needs checking:** Сигнатура функции `Pipe2` в стандартном пакете Go `syscall` (а также в `golang.org/x/sys/unix`):
  ```go
  func Pipe2(p []int, flags int) (err error)
  ```
  Функция принимает уже выделенный срез `p []int` (длиной минимум 2 элемента) первым аргументом и возвращает **только одну ошибку `error`**. Запись `fds, err := syscall.Pipe2(...)` приведет к ошибке компиляции: *«assignment mismatch: 2 variables but syscall.Pipe2 returns 1 value»*.
* **evidence/source needed:** Документация пакета `syscall` (`func Pipe2(p []int, flags int) error`).
* **priority:** **Medium**

---

### Кандидат 16: Ошибка компиляции `os.O_DIRECT`
* **article/section:** `42. Буферизация ввода-вывода (IO). Page Cache, Dirty Pages, Sync.md` / `## Практика: Обход кэша`
* **claim:** В листинге код открывает файл с флагом прямого ввода-вывода через стандартный пакет `os`:
  ```go
  f, err := os.OpenFile("log.dat", os.O_CREATE|os.O_WRONLY|os.O_DIRECT, 0644)
  ```
* **why it needs checking:** Константа `O_DIRECT` **отсутствует в стандартном пакете `os`** языка Go (пакет `os` содержит только кроссплатформенные флаги `O_RDONLY`, `O_WRONLY`, `O_RDWR`, `O_APPEND`, `O_CREATE`, `O_EXCL`, `O_SYNC`, `O_TRUNC`). Константа `O_DIRECT` является Linux-специфичной и объявлена исключительно в пакете `syscall` или `golang.org/x/sys/unix`. Данный код не компилируется.
* **evidence/source needed:** `src/os/file.go`; `src/syscall/zerrors_linux_amd64.go`.
* **priority:** **Medium**

---

### Кандидат 17: Некорректное приведение `stat_t.Mode` к `os.FileMode`
* **article/section:** `40. Устройство файловых систем. Inode, Dentry, Блоки данных.md` / `## Чтение Inode в Go`
* **claim:** Код выполняет каст низкоуровневого поля структуры ядра к типу `os.FileMode`:
  ```go
  var stat syscall.Stat_t
  syscall.Stat(path, &stat)
  mode := os.FileMode(stat.Mode)
  if mode.IsDir() { ... }
  ```
* **why it needs checking:** В языке Go тип `os.FileMode` использует собственную битовую маску, где биты типов файлов (`ModeDir`, `ModeSymlink`, `ModeDevice`) намеренно вынесены компилятором в **старшие 12 бит** 32-битного числа (например, `ModeDir = 1 << 31`), чтобы младшие 9 бит соответствовали стандартным POSIX-правам `rwxrwxrwx`. В POSIX структуре `Stat_t.Mode` флаг `S_IFDIR` находится в 14–15 битах (`0040000`). Прямое приведение `os.FileMode(stat.Mode)` приводит к тому, что метод `mode.IsDir()` всегда вернет `false`! Для корректной проверки нужно либо использовать побитовое И с системной маской `(stat.Mode & syscall.S_IFMT) == syscall.S_IFDIR`, либо использовать высокоуровневый `os.Stat`.
* **evidence/source needed:** `src/os/types.go` (определение констант `FileMode` и реализация `func (m FileMode) IsDir() bool`); `man 7 inode`.
* **priority:** **Medium**

---

### Кандидат 18: Противоречие в аллокациях памяти Go (`brk` vs `mmap`) и пропуск Time Namespace
* **article/section:** `53. Что такое контейнер на самом деле. Ликбез без магии.md` / `## 2. Изоляция: Анатомия Namespaces` & `## Память рантайма`
* **claim:** 
  1. В тексте утверждается, что рантайм Go управляет кучей через системные вызовы `brk` и `mmap`.
  2. При перечислении изолирующих пространств имен (Namespaces) Linux перечисляются только 7 классических неймспейсов.
* **why it needs checking:** 
  1. Утверждение о `brk` противоречит статьям 15 и 62 данного же модуля, где совершенно справедливо указано, что Go аллокатор работает **исключительно** через `mmap(MAP_ANONYMOUS)` и вообще не использует `brk/sbrk` во избежание фрагментации адресного пространства и конфликтов с динамическими библиотеками.
  2. Начиная с ядра Linux 5.6 (2020 год) в ядро добавлено 8-е пространство имен: **Time Namespace** (`CLONE_NEWTIME`), которое позволяет изолировать значения часов `CLOCK_MONOTONIC` и `CLOCK_BOOTTIME` для контейнеров (критично для миграции контейнеров checkpoint/restore в CRIU).
* **evidence/source needed:** `src/runtime/mem_linux.go` (`func sysAllocOS()`); `man 7 time_namespaces`; `man 7 namespaces`.
* **priority:** **Medium**

---

### Кандидат 19: Утверждение об использовании `pthread_create` / `pthread_exit` рантаймом Go в Linux
* **article/section:** `62. Go runtime и системные ресурсы ОС. Взаимодействие шедулера и ядра.md` / `## 2. Управление потоками: M и клонирование ядра`
* **claim:** Статья заявляет, что рантайм Go при необходимости создания нового рабочего потока `M` вызывает библиотечную функцию `pthread_create`, а при завершении потока — `pthread_exit`.
* **why it needs checking:** В операционной системе Linux чистый исполняемый файл Go компилируется со статической линковкой без зависимости от библиотеки `libpthread` (glibc).
  1. Go порождает новые потоки выполнения ОС напрямую через сырой системный вызов ядра `clone(2)` (`flags = CLONE_VM | CLONE_FS | CLONE_FILES | CLONE_SIGHAND | CLONE_THREAD | CLONE_SYSVSEM`), реализованный на чистом ассемблере в функции `runtime.clone`.
  2. Завершение потока выполняется прямым системным вызовом ядра `exit(2)`, а не `pthread_exit`.
  3. Библиотека `libpthread` используется рантаймом Go исключительно при сборке с включенным cgo (`CGO_ENABLED=1`), о чем необходимо явно предупредить читателя.
* **evidence/source needed:** `src/runtime/sys_linux_amd64.s` (`TEXT runtime·clone(SB)`); `src/runtime/os_linux.go` (`func newosproc(mp *m)`).
* **priority:** **Medium**

---

### Кандидат 20: Синтаксическая поломка строковых литералов с переводом строк во множестве статей
* **article/section:** Статьи 4, 11, 16, 24, 27, 30, 42, 57 и др. (более 10 статей)
* **claim:** В листингах кода часто встречается форматированный вывод, оформленный в виде:
  ```go
  fmt.Printf("Status: %s\n
  PID: %d\n", status, pid)
  ```
* **why it needs checking:** В синтаксисе языка Go строковые литералы в двойных кавычках (`"..."`) не могут содержать неэкранированных переводов строк. Подобный перенос строки компилятор Go бракует фатальной ошибкой `newline in string`. Для многострочных строк в Go требуются либо обратные кавычки (raw string literals `` `...` ``), либо конкатенация строк через оператор `+`. В модуле обнаружено множество подобных фрагментов, ломающих компиляцию при копировании примеров читателями.
* **evidence/source needed:** Спецификация языка Go (String literals); вывод компилятора `go build`.
* **priority:** **Low**

---

### Кандидат 21: Эволюция планировщика ядра: CFS против EEVDF в Linux 6.6+
* **article/section:** `7. Планировщик Linux CFS и EEVDF. Принципы справедливости.md` / `## 4. Переход к EEVDF: Что изменилось в Linux 6.6`
* **claim:** Описывается замена CFS на EEVDF (Earliest Eligible Virtual Deadline First), но не указаны ключевые изменения в интерфейсе тюнинга ядра: удаление параметров `sched_latency_ns` и `sched_min_granularity_ns`.
* **why it needs checking:** При миграции на EEVDF в Linux 6.6 классические параметры настройки задержек в `/sys/kernel/debug/sched/` и `/proc/sys/kernel/` были полностью удалены. Вместо них был введен единый квант времени `sched_base_slice_ns`, а также механизм флагов чувствительности к задержкам (`latency sensitive`). Инженеры, настраивающие серверы по старым руководствам для CFS, столкнутся с ошибками отсутствия файлов в `sysfs`.
* **evidence/source needed:** Документация ядра Linux: *EEVDF Scheduler* (commit `86146c21e3f`); `Documentation/scheduler/sched-eevdf.rst`.
* **priority:** **Low**

---

### Кандидат 22: Тонкости разделения файловой позиции (`f_pos`) при `dup` против повторного `open`
* **article/section:** `30. Файловые дескрипторы и таблица открытых файлов ядра.md` / `## 3. Системная таблица файлов (Open File Table)`
* **claim:** Объясняется, что файловый дескриптор указывает на запись в открытой таблице файлов ядра, где хранится смещение `f_pos`.
* **why it needs checking:** Пояснение корректно, однако педагогически крайне важно явно подчеркнуть контраст между вызовами:
  1. `dup(fd)` (или `fork`) копирует файловый дескриптор в рамках одной и той же записи `struct file`, поэтому смещение `f_pos` является общим (чтение из одного дескриптора сдвигает позицию для другого).
  2. Два независимых вызова `open("/path", ...)` создают две разные структуры `struct file` с независимыми смещениями `f_pos`, даже если они указывают на один и тот же `inode`.
  Без этого акцента у читателей возникает путаница при параллельной записи из разных горутин или процессов.
* **evidence/source needed:** `man 2 dup`; `man 2 open`; Robert Love: *Linux System Programming* (Chapter 2).
* **priority:** **Low**

---

## 📊 Сводная таблица кандидатов по приоритетам

| Приоритет | № | Статья / Раздел | Ключевая претензия | Источник / Референс |
|:---:|:---:|---|---|---|
| 🔴 **High** | 1 | `32. Shared Memory` / Практика Go | Вымышленные сисколлы Go: `syscall.ShmOpen`, `ShmSetSize`, `ShmUnlink` | `man 3 shm_open` / Go `syscall` |
| 🔴 **High** | 2 | `49. Backlog & Queues` / Настройка | Опция `1024` и настройка backlog через `setsockopt` вместо `listen(2)` | `src/net/sock_linux.go` / `man 2 listen` |
| 🔴 **High** | 3 | `43. Direct IO` / Практика Go | Псевдовыравнивание через `make([]byte)` гарантирует `EINVAL` в ядре | `man 2 open` (`O_DIRECT`) / Linux VFS |
| 🔴 **High** | 4 | `38. Netpoller` / Резюме vs Текст | Внутреннее противоречие: в тексте `EPOLLET`, а в резюме `EPOLLONESHOT` | `src/runtime/netpoll_epoll.go` |
| 🔴 **High** | 5 | `28. Сигналы` / Модель Go | Вымышленная модель: `sigwaitinfo` на потоке вместо `sigtramp` и `gsignal` | `src/runtime/signal_unix.go` |
| 🔴 **High** | 6 | `27. UDS` / Архитектура | Ложное утверждение о ненадежности и потере порядка в UDS `SOCK_DGRAM` | `man 7 unix` ("reliable, in-order") |
| 🔴 **High** | 7 | `21. Stack Overflow` / Стек Go | Утверждения о `mmap`/`madvise` на каждый рост стека и `SIGSEGV` с Guard Page | `src/runtime/stack.go` |
| 🔴 **High** | 8 | `24. strace, ltrace` / ltrace | Ложное утверждение, что `ltrace` не требует `ptrace` и работает на `LD_PRELOAD` | `man 1 ltrace` / исходники `ltrace` |
| 🔴 **High** | 9 | `51. DNS в ОС` / cgo vs netgo | Ошибочный дефолт для macOS (там `cgo`, а не `netgo`) и фиктивный `experimentalgo` | `src/net/conf.go` |
| 🔴 **High** | 10 | `57. Безопасность` / setuid в Go | `syscall.Setuid` меняет UID только одного потока M; пропуск `AllThreadsSyscall` | `syscall.AllThreadsSyscall` / Issue #1435 |
| 🔴 **High** | 11 | `8, 52, 54, 62` / cgroups & Go | Устаревшее утверждение: с Go 1.25 квоты cgroups v1/v2 поддерживаются нативно | Go 1.25 Release Notes / Issue #33803 |
| 🟡 **Medium** | 12 | `50. TIME_WAIT` / Длительность | В Linux время `TIME_WAIT` жестко зашито как 60 с (`TCP_TIMEWAIT_LEN`), а не 120 с | `include/net/tcp.h` (`TCP_TIMEWAIT_LEN`) |
| 🟡 **Medium** | 13 | `33. Примитивы ядра` / Futex | Ожидание на `futex` переводит поток в `TASK_INTERRUPTIBLE`, а не `TASK_UNINTERRUPTIBLE` | `kernel/futex/waitwake.c` |
| 🟡 **Medium** | 14 | `43. Direct IO` / sendfile | Системный вызов `sendfile` принципиально не может читать из сетевого сокета | `man 2 sendfile` |
| 🟡 **Medium** | 15 | `26. Pipe и FIFO` / Pipe2 | Ошибка сигнатуры `syscall.Pipe2`: функция принимает срез дескрипторов | Go `syscall.Pipe2` docs |
| 🟡 **Medium** | 16 | `42. Буферизация IO` / O_DIRECT | Константы `os.O_DIRECT` не существует в стандартном пакете `os` | `src/os/file.go` |
| 🟡 **Medium** | 17 | `40. Устройство ФС` / Inode | Некорректный каст `os.FileMode(stat.Mode)`: метод `IsDir()` всегда возвращает `false` | `src/os/types.go` |
| 🟡 **Medium** | 18 | `53. Контейнеры` / Память и NS | Противоречие по поводу вызовов `brk` в Go и пропуск Time Namespace (`CLONE_NEWTIME`) | `src/runtime/mem_linux.go` / `man 7 namespaces` |
| 🟡 **Medium** | 19 | `62. Go runtime` / Потоки OS | В Linux Go создает потоки через чистый сисколл `clone`, а не `pthread_create` | `src/runtime/sys_linux_amd64.s` |
| 🟢 **Low** | 20 | Множество статей / Листинги | Синтаксические ошибки компилятора: неэкранированные переводы строк в строках `"..."` | Go Spec (String literals) |
| 🟢 **Low** | 21 | `7. Планировщик` / EEVDF | Удаление параметров тюнинга `sched_latency_ns` при переходе на EEVDF в 6.6+ | Linux Kernel EEVDF docs |
| 🟢 **Low** | 22 | `30. Дескрипторы` / f_pos | Педагогический контраст разделения позиции смещения: `dup` vs повторный `open` | Robert Love: Linux System Programming |

---

## 🎯 Стратегические рекомендации для последующей редактуры

1. **Исправление некомпилируемых примеров системного программирования в Go:**
   - Полностью заменить вымышленные вызовы `syscall.ShmOpen` в статье 32 на каноничное открытие файла в `/dev/shm` через `os.OpenFile` с последующим `Truncate` и `mmap`.
   - Заменить нерабочий код `setsockopt(..., 1024, ...)` в статье 49 на объяснение расчета backlog рантаймом Go из `/proc/sys/net/core/somaxconn`.
   - Исправить сигнатуры системных вызовов в примерах (`syscall.Pipe2`, перенос `O_DIRECT` в `golang.org/x/sys/unix`).
   - Устранить поломки форматированных строк с переводом строк внутри кавычек (`newline in string`) во всех 10+ статьях модуля.
2. **Синхронизация описания подсистем рантайма Go с реальной кодовой базой:**
   - **Стеки (§ 21):** Убрать миф о выделении памяти под стеки через `mmap` при каждом росте и детектировании переполнения через `SIGSEGV` с Guard Page. Четко описать работу `mcache.stackcache`, функцию `copystack` и компиляторную проверку `SP < g.stackguard0`.
   - **Сигналы (§ 28):** Заменить концепцию «одного потока с `sigwaitinfo`» на реальную архитектуру Go: ассемблерный трамплин `runtime.sigtramp`, альтернативный стек `gsignal` на каждом `M` через `sigaltstack` и перехват аппаратных исключений и `SIGURG`.
   - **Netpoller (§ 38):** Устранить противоречие в резюме статьи 38, убрав упоминание `EPOLLONESHOT` и подтвердив бескомпромиссное использование `EPOLLET`.
3. **Безопасность и многопоточность в Linux (§ 57):**
   - Категорически акцентировать внимание на опасности вызова `syscall.Setuid` в Go из-за смены UID только на одном потоке OS (`M`). Добавить подробный разбор механизма `syscall.AllThreadsSyscall` (Go 1.16+).
4. **Актуализация контейнерной среды и cgroups (§ 8, 52, 54, 62):**
   - Обновить информацию о связке Go и контейнеров с учетом релиза Go 1.25: зафиксировать, что Go научился автоматически определять квоты cgroups v1/v2 из коробки через `internal/runtime/cgroup`.
5. **Точность сетевых и IPC гарантий ядра Linux (§ 27, 43, 50):**
   - Снять с UDS `SOCK_DGRAM` ярлык «ненадежного аналога UDP»: подтвердить 100% надежность и сохранение порядка ядром Linux.
   - Скорректировать длительность `TIME_WAIT` для Linux: указать жесткую константу `TCP_TIMEWAIT_LEN = 60s`.
   - Уточнить ограничения `sendfile(2)`, исключив утверждение о возможности чтения из сокета.
