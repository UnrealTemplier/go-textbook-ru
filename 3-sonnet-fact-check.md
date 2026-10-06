# Первичный фактчек по источникам · Модуль 3 «Компьютерные сети и сетевой стек»

> **Роль:** primary source-based fact checker (Sonnet 5.5).
> **Вход:** `sources/3. Компьютерные сети и сетевой стек/` (44 статьи), `3-opus-judge.md` (Master Fact-Check Brief), `3-opus-blind-spot.md` (дополнительные находки).
> **Дата проверки:** 2026-10-06. Репозиторий на `HEAD 2b7c9945`; в `sources/` после брифа ничего не менялось.
> **Правило отчёта:** статус получает только то, что я проверил сам. Всё остальное помечено **NOT CHECKED** (раздел 9).

---

## 0. Метод, окружение, теги доказательств

**Окружение.** Go 1.27.1 linux/amd64; Linux 7.2.8 (Fedora 44); unprivileged `unshare -Urnm` (netns, `veth`, `iptables`, `ip netns exec`), root в ядре не использовался; модули из кэша и по сети: `golang.org/x/net v0.59.0`, `quic-go v0.63.0`, `grpc-go v1.80/1.84`, `cilium/ebpf v0.22.0`, `gorilla/websocket` (main). Ядро: исходники `torvalds/linux` (master на 2026-10-06) и `Documentation/`.

| Тег | Что значит |
|---|---|
| **[SRC]** | прочитан исходник Go (`/usr/local/go/src`, `x/net`, `quic-go`, `grpc-go`) |
| **[API]** | `api/go1.N.txt` (версия появления идентификатора) |
| **[VET]** | `go vet` на листинге из статьи (все 38 `package`-блоков запущены; зависимости подтянуты) |
| **[EXP]** | я написал программу и запустил её (loopback или netns с `veth` MTU 1500) |
| **[KERN]** | исходники или `Documentation/` ядра |
| **[RFC]** | текст RFC |
| **[WEB]** | официальная документация, release notes, объявление |

**Что не делалось (честно).**
- Нет `root`: не менял глобальные sysctl, не воспроизводил `nf_conntrack_max`-переполнение и переполнение neighbour-таблицы (в netns эти sysctl недоступны; см. J-H8).
- Не проверял железо, NIC offload, cloud-фабрики и версии ядер «до/после» экспериментально; для них указаны исходник ядра или документация, и это отмечено.
- Числа без источника (C-NUM) и «Medium/Low» из Brief, которые я не открывал, **не** объявлены верными (раздел 9).

**Статусы:** `VERIFIED` · `INCORRECT` · `PARTIALLY CORRECT` · `OUTDATED` · `CONTEXT-DEPENDENT` · `OPINION / NOT A FACT CLAIM` · `NOT CHECKED`.

---

## 1. Сводка

### 1.1. Итог по блокам Master Brief

| Блок Brief | Вердикт | Комментарий |
|---|---|---|
| J-H1 Nagle | **Подтверждён** | В Go `TCP_NODELAY=1` по умолчанию на клиенте и сервере [EXP][SRC]. Ст. 10, 11, 37, 44 подают ядерный дефолт как поведение Go. |
| J-H2 keepalive | **Подтверждён** | Go включает keepalive 15 с / 15 с / 9 [EXP][SRC]; «72000», «Go 1.16», «висит вечно» неверны. |
| J-H3 `net.Conn`/gorilla | **Подтверждён** | Doc `net.Conn` и doc gorilla [SRC]. |
| J-H4 netpoller | **Подтверждён** | `wakeG`, `EPOLL_CTL_MOD`, `webPoller`, `epoll_pwait2`, «1024 события», «Go 1.22+ ET» неверны; `epoll_pwait` как имя верно (K1). |
| J-H5 API | **Подтверждён, одно уточнение** | `golang.org/x/net/http3` **существует как пакет-заглушка** без публичного API [SRC] (Brief: «публичного пакета нет»). |
| J-H6 компиляция | **Подтверждён + 1 новая находка** | Лишний `"time"` в ст. 33 [VET]. |
| J-H7 DNS | **Подтверждён** | Кэша нет, `singleflight` на `map`+`Mutex`, EDNS0 = 1232 [SRC]. |
| J-H8 errno | **Подтверждён (3 из 4 сценариев экспериментом)** | `ENETUNREACH`, `EHOSTUNREACH`, таймаут при DROP [EXP]; conntrack/neighbour — только по исходникам ядра. |
| J-H9 пул | **Подтверждён** | [SRC][EXP]. |
| J-H10 REUSE* | **Подтверждён** | Go ставит `SO_REUSEADDR` на слушающие сокеты, `SO_REUSEPORT` нет [EXP][SRC]. |
| J-H11 буферы | **Подтверждён, одна поправка к Brief** | `rmem_max = 4 MiB` — **дефолт mainline-ядра** (не «значение дистрибутива») [KERN]. |
| J-H12 TLS | **Подтверждён** | `Handshake()` проверяет имя [EXP]. |
| J-H13 отзыв | **Подтверждён** | [SRC][WEB]. |
| J-H14 HTTP/3, QUIC | **Подтверждён** | quic-go: Reno/Cubic, BBR нет [SRC]. |
| J-H15 Rapid Reset | **Подтверждён** | [SRC][WEB]. |
| J-H16 формулы | **Подтверждён** | [RFC][KERN]. |
| J-H17 UDP | **Подтверждён и закрыт K12** | Эксперимент на `veth` MTU 1500 [EXP]. |
| J-H18 листинги | **Подтверждён по строкам таблицы** | См. 2.18. |
| J-H19 raw-сокеты | **Подтверждён частично** | Привилегии не воспроизводились. |
| J-H20 K8s DNS/L4 | **Подтверждён** | [WEB]. |
| J-H21 VLAN MTU | **Подтверждён** | [EXP][WEB]. |
| J-H22 mtr/dig | **CONTEXT-DEPENDENT** | Первоисточник по ICMP-ограничению не найден (см. 2.22). |
| J-H23–J-H30 | **Подтверждены** (кроме оговорок) | См. разделы 2.23–2.30. |

### 1.2. Расхождения с Brief

1. **Blind Spot прав насчёт K10/R7.** В ст. 16:84 «версии 1.11» есть и неверно (резолвер на чистом Go — с Go 1.5; не «на всех Unix»). Решение R7 Brief снять. См. K10, B-4.
2. **J-H11:** Brief пишет, что 4 MiB для `rmem_max` — значение дистрибутива. В `net/core/sock.c` mainline `sysctl_rmem_max = 4 << 20`, в `Documentation/admin-guide/sysctl/net.rst` — «Default: 4194304» [KERN]. `rmem_default` = 212992 [EXP] (ст. 14:217 «~212 КБ» верна для UDP).
3. **J-H5:** `golang.org/x/net/http3` — не «нет такого пакета», а пакет без публичного API (`This package is a work in progress. It is not ready for production usage`) [SRC].
4. **J-H8:** Sonnet-гипотеза «`ENOBUFS` при переполнении neighbour-таблицы» верна только для внутреннего пути: `ip_finish_output2` возвращает `PTR_ERR(neigh)`, но `tcp_connect()` игнорирует любую ошибку передачи SYN, кроме `-ECONNREFUSED` [KERN: tcp_output.c:4386–4387]. `connect()` не вернёт `ENOBUFS`.
5. **J-H23:** HAProxy `nbthread`: «по умолчанию = число CPU» верно только на платформах с CPU affinity; иначе 1 [WEB: `configuration.txt`].
6. **C-GOVER (ст. 18):** «TLS 1.3 по умолчанию с Go 1.21» — Brief прав (Go 1.13, а с 1.14 отключить через GODEBUG нельзя) [WEB].
7. Новые находки, которых нет ни в одном брифе, — раздел 8.

### 1.3. Самые вредные для читателя ошибки (ТОП)

1. `SetNoDelay(true)` «обязательно», «Nagle включён по умолчанию» (ст. 10, 11, 37, 44).
2. «Keepalive в Go бесполезен/по умолчанию 2 часа/72000 с/висит вечно» (ст. 1, 12, 41, 43). Реально: 15 с/15 с/9.
3. Ошибки при проблемах L2–L4 (ст. 5, 7, 8, 9, 32): `no route to host` ≠ пропажа маршрута; DROP даёт только таймаут.
4. `net.Conn`/gorilla «не потокобезопасны» — всё наоборот (ст. 1, 25).
5. `PreferServerCipherSuites`, «`Handshake()` не проверяет имя хоста» (ст. 18, 19).
6. Дефолт `MaxIdleConnsPerHost` = 2, а не 100; «0 — неограниченно» (ст. 21, 40).
7. Контекст после `Hijack` не отменяется (ст. 25); контекст не прерывает `Read/Write` (ст. 44).
8. Правила для `IdleConnTimeout > 2·MSL` (ст. 39).
9. Идемпотентный ключ в `CreateOrder`, Half-Open пропускает всех, лимитер без очистки (ст. 43, 33).
10. Кэш DNS в Go (ст. 16), `ndots:0`, `PreferGo: true` «всегда».

---

## 2. High-блоки J-H1 … J-H30

### 2.1. J-H1. Nagle и `SetNoDelay`

| Утверждение | Статус | Доказательство |
|---|---|---|
| Go по умолчанию ставит `TCP_NODELAY=1` на все TCP-сокеты (`Dial` и `Accept`) | **VERIFIED** | [SRC] `net/tcpsock.go:290` `newTCPConn` → `setNoDelay(fd, true)`; doc `SetNoDelay`: «The default is true (no delay)». [EXP] `getsockopt`: `NODELAY=1` у клиента и у принятого сокета. |
| Ст. 12:227–228, 342: «в Go `TCP_NODELAY` включён по умолчанию» | **VERIFIED** | то же |
| Ст. 21:163: «Go ставит `TCP_NODELAY` на keep-alive соединениях» | **PARTIALLY CORRECT** | Ставится на все TCP-соединения, а не только keep-alive. |
| Ст. 10:322–330: ядро объединяет мелкие записи (Nagle) — это верно для ядра; «в микросервисах на Go всегда принудительно отключают Нагла» + листинг `SetNoDelay(true)` | **PARTIALLY CORRECT** | Дефолт ядра описан верно. Для Go вызов не нужен: флаг уже включён. Формулировка «всегда принудительно отключают» подана как необходимость. |
| Ст. 11:352–358: `SetNoDelay(true)` «критично для low-latency» | **PARTIALLY CORRECT** | Вызов безвреден, но «критично» неверно. |
| Ст. 11:428: «отключение алгоритма Нейгла — обязательный арсенал» | **INCORRECT** | Для Go это значение по умолчанию. |
| Ст. 37:266, 275: комментарий «Отключает алгоритм Нагла… критично» и интервью «Почему `TCP_NODELAY` часто включают?» | **INCORRECT** (для Go) | То же. |
| Ст. 44:170: «По умолчанию… активирован алгоритм Нагла… его отключение через `conn.SetNoDelay(true)` обязательно» | **INCORRECT** | То же; противоречит ст. 12. |
| Ст. 12:344: `sysctl -w net.ipv4.tcp_delack_min=1` и `tcp_delack_max=1` | **INCORRECT** | [EXP] в `/proc/sys/net/ipv4` нет `tcp_delack*`; в `ip-sysctl.rst` их нет [KERN]. Есть сокетная опция `TCP_DELACK_MAX_US=46` [KERN: `uapi/linux/tcp.h:144`]. |

**K4 (ст. 12 учит «включайте»):** Brief прав, ст. 12 говорит верно (VERIFIED).

### 2.2. J-H2. TCP keepalive в Go

| Утверждение | Статус | Доказательство |
|---|---|---|
| Для сокетов от `net.Dial`/`net.Listen` keepalive включён: idle 15 с, interval 15 с, count 9 | **VERIFIED** | [SRC] `net/dial.go:18–27`, `tcpsock.go:291–296`. [EXP] `SO_KEEPALIVE=1`, `TCP_KEEPIDLE=15`, `TCP_KEEPINTVL=15`, `TCP_KEEPCNT=9` у клиента и принятого сокета. |
| Ядерный дефолт 7200 с (2 ч) | **VERIFIED** | [KERN] `ip-sysctl.rst`: `tcp_keepalive_time` default 2 hours; [EXP] при `Dialer{KeepAlive:-1}` + `SetKeepAlive(true)` получаем `IDLE=7200, INTVL=75, CNT=9`. |
| Ст. 12:287–290, 356; ст. 21:283; ст. 40: «дефолтный keepalive бесполезен, 2 часа» | **INCORRECT** для Go | выше. **CONTEXT-DEPENDENT**: верно для сокета, где keepalive включили без настройки, и для C/Java/Python. |
| Ст. 12:296: «Начиная с Go 1.16 … `SetKeepAlivePeriod`» | **INCORRECT** | [API] `api/go1.2.txt:760`. |
| Ст. 43:305: «`SetKeepAlive(true)` … каждые **72000** сек» | **INCORRECT** | ядерный дефолт 7200; в Go — 15 с. |
| Ст. 1:190: «соединение останется висеть вечно» без `SetDeadline` | **INCORRECT** | keepalive обнаружит мёртвого пира: ≈ 15 + 9·15 = 150 с на idle-соединении. Но **нюанс** B-3: при неподтверждённых данных keepalive не работает (см. B-3). |
| Ст. 8:309: `net.Dialer{KeepAlive: 15 * time.Second}` как «включение» | **PARTIALLY CORRECT** | Keepalive уже включён; значение задаёт только `idle`. У `http.DefaultTransport` `KeepAlive` = 30 с [SRC `transport.go:47–58`]. |
| Ст. 41:181 «стоит явно настроить `SetKeepAlive(true)`» | **PARTIALLY CORRECT** | Включение не нужно; настроить *период* — да. |
| `net.KeepAliveConfig` (Go 1.23) не упомянут нигде | **VERIFIED** (пропуск) | [API] `api/go1.23.txt:60–65`; `grep KeepAliveConfig` по модулю — 0. |

**Новая находка (раздел 8, N-1):** с Go 1.23 `SetKeepAlivePeriod(d)` меняет только `TCP_KEEPIDLE`, а до 1.23 менял и `KEEPIDLE`, и `KEEPINTVL`. [SRC 1.27 `tcpsock.go:249–257`; SRC go1.22.0 `tcpsockopt_unix.go`; EXP: после `SetKeepAlivePeriod(30s)` `IDLE=30`, `INTVL` не изменился]. Ст. 12:296–310 описывает «период keep-alive» без учёта этой разницы → **CONTEXT-DEPENDENT**.

### 2.3. J-H3. Потокобезопасность

| Утверждение | Статус | Доказательство |
|---|---|---|
| Ст. 1:187–188: «одновременный вызов двух `Read()` или двух `Write()` … категорически запрещён… разрушение внутренних буферов… race» | **INCORRECT** | [SRC] `net/net.go:123`: «Multiple goroutines may invoke methods on a Conn simultaneously»; `internal/poll/fd_mutex.go` сериализует `Read` с `Read`, `Write` с `Write`. |
| Рекомендация мьютекса/канала для *составных* сообщений | **PARTIALLY CORRECT** | Разумна: один логический ответ из нескольких `Write` может перемешаться с чужим. Но причина — прикладная, а не «разрушение буферов». |
| Ст. 1:235 «неполная потокобезопасность `net.Conn`» | **INCORRECT** | то же |
| Ст. 25:277: «`websocket.Conn` не потокобезопасен для одновременного `ReadMessage` и `WriteMessage`» | **INCORRECT** | [SRC gorilla `doc.go:122–131`]: «Connections support one concurrent reader and one concurrent writer». Нельзя нескольким писателям (и нескольким читателям). Рекомендация «mutex / single writer» верна. |

### 2.4. J-H4. Netpoller

| Утверждение | Статус | Доказательство |
|---|---|---|
| `runtime.wakeG` (ст. 38:21, 70, 79, 86, 108, 117, 189; ст. 43:42; ст. 44:49) | **INCORRECT** | [SRC] `grep -rn wakeG runtime` — пусто. Реальное: `netpoll` → `netpollready` → `netpollunblock` → `injectglist`/`goready`. |
| `netpollBlock`, `netpollReady` (ст. 1:177–178; ст. 38) | **PARTIALLY CORRECT** | Реально `netpollblock`, `netpollready` (строчные, `runtime/netpoll.go:494,548`). Смысл верен. |
| «вызывает `runtime.stopm`» из `netpollBlock` | **PARTIALLY CORRECT** | `netpollblock` → `gopark`; `stopm` вызывает планировщик, если нет работы. |
| Ст. 1:144: `epoll_ctl(EPOLL_CTL_MOD, fd, EPOLLIN)` после `EAGAIN` | **INCORRECT** | [SRC] `runtime/netpoll_epoll.go:51–55`: регистрация один раз `EPOLL_CTL_ADD` с `EPOLLIN\|EPOLLOUT\|EPOLLRDHUP\|EPOLLET`; `EPOLL_CTL_MOD` в рантайме не используется (`grep` пусто). |
| Ст. 37:134, 149; ст. 38:77: FD регистрируется «с `EPOLLIN\|EPOLLET`» | **PARTIALLY CORRECT** | ET верно; набор флагов неполный. Порядок `listen` → регистрация — верен. |
| Ст. 38:82: «`netpoller` имеет лимит на количество отслеживаемых FD… динамически масштабируется» | **INCORRECT** | [SRC] один глобальный `epfd` (`netpoll_epoll.go:16`); лимит только `RLIMIT_NOFILE`. K3: цитата Gemini была перефразирована, суть ошибки подтверждена. |
| Ст. 38:170: `epoll_pwait2` (Linux 5.11+) | **INCORRECT** | [SRC] рантайм вызывает `SYS_EPOLL_PWAIT` (`syscall_linux.go:32`); `SYS_EPOLL_PWAIT2` только объявлен для 3 архитектур, не вызывается. |
| Ст. 1:163, 169: рантайм использует `epoll_pwait` «для безопасной маскировки сигналов» | **PARTIALLY CORRECT** | Имя syscall верно, обоснование нет: `Syscall6(SYS_EPOLL_PWAIT, …, 0, 0)` — маска не передаётся. K1: Sonnet был неправ, Brief прав. |
| Ст. 1:172: `webPoller` для WASM | **INCORRECT** | [SRC] файлы `runtime/netpoll_*.go`: `aix, epoll, fake, kqueue, solaris, stub, wasip1, windows`. `js/wasm` — `netpoll_fake.go` (поллера нет), `wasip1` — `poll_oneoff`. |
| Ст. 15:312, ст. 10, 37: «фоновый поток рантайма выполняет `epoll_wait`» | **INCORRECT** | [SRC] `netpoll(0)` вызывают `findRunnable`, `sysmon`, `startTheWorld` (`proc.go:1778, 3511, 3769, 6622`); блокирующий `netpoll(delay)` — на M без работы. Выделенного потока нет. Ст. 44:104 описывает верно. |
| Ст. 44:104: «пачку до 1024 готовых событий» | **INCORRECT** (внесено прошлым фактчеком) | [SRC] `var events [128]linux.EpollEvent` (`netpoll_epoll.go:117`). |
| Ст. 44:71: «в Go 1.22+ оптимизированный edge-triggered режим» | **INCORRECT** | [SRC go1.1] `netpoll_epoll.c:39`: `EPOLLET` уже в Go 1.1; `events[128]` там же. |
| Ст. 37:164: «Go использует ET, что требует вычитывать данные до `EAGAIN`» | **INCORRECT** | см. B-18. |

### 2.5. J-H5. Несуществующие API и идентификаторы

| Ст., строка | В тексте | Статус | Доказательство |
|---|---|---|---|
| 32:5, 174; 16:181, 241; 17:216 | `net.DialContext(ctx, …)` | **INCORRECT** | Есть только `(*net.Dialer).DialContext` [SRC `dial.go:529`]. |
| 20:176–177 | поле `Request.Context context.Context` в «структуре из `request.go`» | **INCORRECT** | поле приватное `ctx` [SRC `request.go:338`]. Доступ: `r.Context()`. |
| 22:245 | `http2.Server.MaxHeaderListSize`, `ReadHeaderBufferSize` | **INCORRECT** | [SRC x/net v0.59.0 `server_common.go:59–172`] таких полей нет. Предел заголовков берётся из `http.Server.MaxHeaderBytes` (`server.go:500–506`). |
| 40:109, 196 | `http.Server.MaxConns`, `http.ServerMetrics` | **INCORRECT** | [SRC] в `net/http` их нет. |
| 44:134 | `net.Resolver.LookupContext` | **INCORRECT** | [SRC `lookup.go`] методы: `LookupHost/IPAddr/IP/NetIP/…`. |
| 15:174 | `syscall.ListenConfig` | **INCORRECT** | тип `net.ListenConfig` [SRC `dial.go:816`]. |
| 14:146, 359–362 | `conn.Connect(addr)` для UDP | **INCORRECT** | [SRC] у `*net.UDPConn` метода `Connect` нет; нужен `net.DialUDP`. Семантика «`connect` на UDP локальный» — **VERIFIED** [EXP]: `Read` на подключённом UDP возвращает `connection refused` после ICMP port unreachable, у неподключённого — только таймаут. |
| 14:140 | `UDPConn` встраивает `IPConn` | **INCORRECT** | `type UDPConn struct { conn }` [SRC `udpsock.go:119`]. |
| 4:299 | методы `netip.Addr.IPv4()/IPv6()` | **INCORRECT** | [SRC `netip.go`] есть `AddrFrom4/16`, `As4/As16`, `Unmap`. |
| 4:205 | `syscall.WriteMsgUDP` | **INCORRECT** | в `syscall` нет (есть `(*net.UDPConn).WriteMsgUDP`). |
| 34:162 | `GODEBUG=netpoll=1`; профиль pprof `syscall` | **INCORRECT** | [SRC] встроенные профили: `goroutine, threadcreate, heap, allocs, block, mutex`; GODEBUG-опции `netpoll` нет. |
| 36:176 | `link.XDPOpts` | **INCORRECT** | [VET] `undefined: link.XDPOpts`; тип `link.XDPOptions`, передаётся значением, а не указателем. |
| 36:282 | `Replace: true` в `link.AttachXDP` | **INCORRECT** | `XDPOptions{Program, Interface, Flags}`; замена — `Link.Update` (B-24). |
| 24:225–250 | `poll.FD` и `fd.SyscallConn().Read(...)` «из quic-go» | **INCORRECT** | [SRC] `internal/poll` не импортируется; у `poll.FD` есть `RawRead`, а не `SyscallConn`; в quic-go такого кода нет. |
| 23:165, 229; 44:148 | `golang.org/x/net/http3` | **INCORRECT** (с уточнением) | Пакет существует, но это заглушка: `http3.go` содержит только `go:linkname`-хуки для тестов `net/http` («pending this package having a public API»). Использовать `github.com/quic-go/quic-go/http3`. |
| 23:151 | `http3.Client` | **INCORRECT** | [SRC quic-go v0.63.0 `http3/`] типы `Transport`, `ClientConn`, `Server`; типа `Client` нет. |
| 19:294 | `CertificateSignatureAlgorithm` | **INCORRECT** | в `crypto/x509` тип `SignatureAlgorithm`. Ст. 19:294 выдаёт его за поле структуры. |

### 2.6. J-H6. Листинги, которые не компилируются

`go vet` на всех 38 блоках с `package`; зависимости (`quic-go`, `x/time/rate`, `netlink`, `grpc`, `uuid`, `x/net/icmp`) подтянуты.

| Ст., блок | Результат | Статус |
|---|---|---|
| 2 (L122) | `"fmt" imported and not used` | **VERIFIED** |
| 20 (L246) | `"time" imported and not used` | **VERIFIED** |
| 30 (L122) | `"context" imported and not used` | **VERIFIED** |
| 31 (L189) | `"encoding/hex" imported and not used` | **VERIFIED** |
| 42 (L159) | `"context" imported and not used` | **VERIFIED** |
| **33 (L86)** | **`"time" imported and not used`** | **VERIFIED — новая находка** (в Brief нет) |
| 36 (L145) | `undefined: link.XDPOpts` → после замены: `cannot use &link.XDPOptions{…} … as link.XDPOptions value` → `"os" imported and not used` | **VERIFIED** |
| 43 (L263) | `undefined: Service`, `undefined: pb` | **VERIFIED** — не самостоятельный пример; также `uuid.New()` в `CreateOrder`, см. J-H18 |
| 43 (L52) | `undefined: pb` | **VERIFIED** — фрагмент |
| Остальные полные `package`-блоки (3, 4, 5, 6, 7, 8, 9, 11, 13, 14×2, 16, 17, 18, 19, 23, 27, 29, 35×4, 37, 39, 40, 41, 43×2) | `go vet` без ошибок | **VERIFIED** (компилируются) |

Это не проверка *поведения*: см. 2.18.

`//go:generate go build -ldflags '-s -w' -o xdp_prog.xdp xdp.c` (ст. 36:158): **INCORRECT**. `go build` не компилирует C в eBPF-объект, расширение `.xdp` не совпадает с загружаемым `xdp_prog.o` (строка 163). Нужен `clang -target bpf` или `bpf2go` [SRC `cilium/ebpf`].

### 2.7. J-H7. DNS-резолвер Go

| Утверждение | Статус | Доказательство |
|---|---|---|
| Ст. 16:178–179: «Встроенный кэш с дедупликацией… на базе `sync.Map`» | **INCORRECT** (ярлык и реализация) | [SRC] кэша ответов нет; дедупликация — `lookupGroup singleflight.Group` (`lookup.go:166`), реализован на `map` + `sync.Mutex` (`internal/singleflight/singleflight.go:30–31`). Сама идея «дедупликация одновременных запросов» — **VERIFIED**. |
| Ст. 17:328, 30:92, 44:171 «кэша нет» | **VERIFIED** | то же |
| Ст. 16:94–101, 156: ответ > 512 байт → `TC=1` → TCP | **PARTIALLY CORRECT** | RFC 1035 даёт 512 для UDP без EDNS0. Go шлёт EDNS0 OPT с размером **1232** [SRC `dnsclient_unix.go:39, 77`], поэтому усечение у Go — при ответе > 1232. |
| Ст. 17:79, 325: EDNS0 «буфер 4096 байт через `udp-max`» | **INCORRECT** (для Go) | 1232. RFC 6891 лишь *рекомендует* стартовое значение 4096 [RFC 6891 §6.2.5]; опции `udp-max` в EDNS0 нет — размер лежит в поле CLASS записи OPT. |
| Ст. 35:171: «Если ответ > 512 байт, сервер ставит флаг **`DO`**» | **INCORRECT** | `DO` — бит DNSSEC OK, к усечению не относится; усечение — `TC`. |
| Ст. 35:173: «Go по умолчанию использует стратегию `go` (Cgo resolver)» | **INCORRECT** | `go` — чистый Go-резолвер [SRC `conf.go:127–185`: «By default, prefer the go resolver»]. |
| Ст. 16:84: «В Go начиная с версии 1.11 по умолчанию **на всех платформах Unix** чистый Go resolver (`netgo`)» | **INCORRECT** | [WEB Go 1.5 release notes] с 1.5; [SRC] на `darwin/ios/android/windows/plan9` предпочитается cgo (`goosPrefersCgo`, `conf.go:167–190`). **Blind Spot B-4 прав, K10/R7 в Brief — ошибочно сняты.** |
| Ст. 1:192: «с Go 1.20+ чистый `netgo` по умолчанию на большинстве платформ» | **INCORRECT** (версия) | с Go 1.5 [WEB]. |
| Ст. 16:172–174: macOS — `SCDynamicStore`; Windows — реестр через `dnscfg` | **INCORRECT** | [SRC] `grep SCDynamicStore\|dnscfg net` — пусто; Windows читает конфиг через `GetAdaptersAddresses` (`dnsconfig_windows.go:24`). |
| Ст. 1:192, ст. 16, 17: «рекомендуется `ndots:0`» | **CONTEXT-DEPENDENT** | В K8s ломает короткие имена; обычно `ndots:1–2` или FQDN с точкой. |
| «Всегда `PreferGo: true`» (ст. 16:315; 17:285, 311, 329; 35:191) | **CONTEXT-DEPENDENT** | см. B-9. |

### 2.8. J-H8. Какую ошибку видит клиент (C-ERRNO)

Эксперименты в netns (`veth`, MTU 1500; `Dialer.Timeout = 8 s`):

| Сценарий | Результат [EXP] |
|---|---|
| Порт закрыт на живом хосте (RST) | `connection refused` (мгновенно) |
| Нет маршрута (нет default route), dst `8.8.8.8:80` | **`network is unreachable`** (`ENETUNREACH`), мгновенно |
| Хост в подсети отсутствует (ARP не отвечает), `10.0.0.99` | **`no route to host`** (`EHOSTUNREACH`) через 3,1 с |
| `iptables -j DROP` на исходящий SYN или на INPUT пира | **`i/o timeout`** (8 с) — нет errno |
| `REJECT --reject-with icmp-port-unreachable` | `connection refused` |
| `REJECT --reject-with tcp-reset` | `connection refused` |

| Утверждение | Статус | Комментарий |
|---|---|---|
| Ст. 7:401: пропал default route → `no route to host` | **INCORRECT** | Для off-link получаем `ENETUNREACH` («network is unreachable»). |
| Ст. 5:340: переполнение neighbour-таблицы → `no route to host` | **INCORRECT** (по исходникам) | [KERN] `neighbour.c:655` `ERR_PTR(-ENOBUFS)`; `ip_output.c:242–245` отбрасывает пакет и возвращает ошибку, но `tcp_connect()` её игнорирует (`tcp_output.c:4386–4387`, реагирует только на `-ECONNREFUSED`). Ожидаемый исход — SYN-ретрансмиты и таймаут. **Эксперимент не выполнен**: `gc_thresh*` в netns недоступны. |
| Ст. 8:156, 361: переполнение conntrack → `no route to host` | **INCORRECT** (по исходникам) | [KERN] `nf_conntrack_core.c:1669`: «table full, dropping packet» + `-ENOMEM` → drop → клиент видит таймаут. Эксперимент не выполнен (`nf_conntrack_max` в netns read-only). |
| Ст. 32:136: conntrack full → «`ECONNREFUSED` или `ETIMEDOUT`» | **PARTIALLY CORRECT** | `ETIMEDOUT` — да; `ECONNREFUSED` возникает только от RST/ICMP, а не от drop. |
| Ст. 9:391: NetworkPolicy drop → `ECONNREFUSED` либо `network unreachable` | **INCORRECT** для DROP | таймаут; `ECONNREFUSED` — только при REJECT [EXP]. |
| Ст. 3:12: FDB exhaustion → `ECONNREFUSED` | **INCORRECT** (по логике L2) | Переполнение FDB приводит к flooding кадров, а не к RST. **NOT CHECKED экспериментально.** |

### 2.9. J-H9. Пул `http.Transport`

| Утверждение | Статус | Доказательство |
|---|---|---|
| Ст. 21:59: `DefaultMaxIdleConnsPerHost = 2` | **VERIFIED** | [SRC `transport.go:62`], [EXP] `2`. |
| Ст. 21:230: «по умолчанию `MaxIdleConnsPerHost = 100`… до 100 параллельных TCP» | **INCORRECT** | см. выше + `MaxIdleConnsPerHost` ограничивает **простаивающие**, а не параллельные соединения. Параллельные ограничивает `MaxConnsPerHost` (по умолчанию без лимита; Go 1.11 [API]). |
| Ст. 40:184–185: «`MaxIdleConnsPerHost` = 0 → неограниченное число idle» | **INCORRECT** | doc: «If zero, DefaultMaxIdleConnsPerHost is used» [SRC `transport.go:215`]. Безлимитность — у `MaxIdleConns` = 0 (общее число). |
| Ст. 35:284: `MaxIdleConnsPerHost` «ограничивает живые сокеты, новые запросы блокируются» | **INCORRECT** | это поведение `MaxConnsPerHost`. |
| Ст. 44:124: «создаёте новый `http.Client`… вы теряете пул» | **PARTIALLY CORRECT** | Пул принадлежит `Transport`: клиент с тем же `Transport` пул не теряет. «Переиспользуйте `http.DefaultClient`» — **OPINION** (у него нет `Timeout`). |
| Ст. 39:150: `MaxIdleConnsPerHost: 100 // в DefaultTransport по умолчанию всего 2!` | **VERIFIED** | |
| Ст. 38: «2 idle на хост по умолчанию» | **VERIFIED** | |

### 2.10. J-H10. `SO_REUSEADDR` / `SO_REUSEPORT`

| Утверждение | Статус | Доказательство |
|---|---|---|
| Go ставит `SO_REUSEADDR=1` на слушающие сокеты | **VERIFIED** | [SRC `sockopt_linux.go:28`], [EXP] listener и принятый сокет: `REUSEADDR=1`. На клиентском сокете — 0. |
| `SO_REUSEPORT` на Linux Go не ставит | **VERIFIED** | [EXP] `REUSEPORT=0`; [SRC] в `sockopt_linux.go` только multicast `SO_REUSEADDR`. |
| Ст. 2:194: «рантайм принудительно включает флаг повторного использования адреса» | **VERIFIED** | то же. Но «двухминутный `TIME_WAIT`» — **INCORRECT** (60 с; см. C-TIMEWAIT). |
| Ст. 15:170–184: «в Go это настраивается через `syscall.ListenConfig`» | **INCORRECT** | тип неверный (`net.ListenConfig`) и опция уже включена по умолчанию. |
| Ст. 39:111–112: «`SO_REUSEADDR` не спасает от `TIME_WAIT`… не удаляет `TIME_WAIT` из таблицы conntrack» | **INCORRECT** | `SO_REUSEADDR` как раз разрешает `bind()` при `TIME_WAIT` слушающего порта; к conntrack отношения нет. |
| Ст. 44:169: «Go использует `SO_REUSEPORT` для балансировки между `p`» | **INCORRECT** | |
| Ст. 10:249, 42:214, 43:306/317, 33:240: `SO_REUSE*` как средство от исчерпания клиентских эфемерных портов | **INCORRECT** | Обе опции влияют на `bind()` слушающего сокета. |
| Ст. 37:153; 39:122: `SO_REUSEPORT` «распределяет между горутинами»; «при включённом `SO_REUSEPORT` ядро балансирует `accept` между сокетами разных потоков» | **INCORRECT** (для Go по умолчанию) | Go его не включает; балансировка возможна только если приложение само открывает несколько listener'ов. |

### 2.11. J-H11. Буферы сокетов

| Утверждение | Статус | Доказательство |
|---|---|---|
| Явный `SO_RCVBUF` выключает автотюнинг приёма для сокета | **VERIFIED** | [KERN] `net/core/sock.c:975`: `sk->sk_userlocks \|= SOCK_RCVBUF_LOCK`; `tcp_input.c:789, 923` проверяют этот флаг. |
| Значение кламп до `rmem_max` и удваивается | **VERIFIED** | [KERN] `sock.c:1375`; [EXP] `SetReadBuffer(1 MB)` → `SO_RCVBUF = 2 097 152`. |
| Ст. 13:314–330: опция на **слушающем** сокете наследуется принятыми | **VERIFIED** | [EXP] принятый сокет от listener с `SO_RCVBUF=1 MB` → `RCVBUF = 2097152` (клиент: 131072). Автотюнинг у такого сокета отключён → для каналов с большим BDP это **не** «разворачивает окно». |
| Ст. 11:330–338, 416: «расширяет окно Flow Control», «ядро выделит 2 МБ памяти» | **PARTIALLY CORRECT** | Удвоение — верно (`man 7 socket`); это лимит учёта памяти, а не аллокация. Автотюнинг теряется. |
| Ст. 11:414–415: «удвоение — историческое наследие BSD; ядро резервирует половину под `sk_buff`» | **PARTIALLY CORRECT** | Удваивает Linux (`man 7 socket`), причина — накладные расходы. Подача «BSD/Go» неточна (Low). |
| Ст. 11:149–150, B-20: «размер `sk_rcvbuf` по умолчанию и границы — `rmem_default`/`rmem_max`» | **PARTIALLY CORRECT** | для TCP начальный размер задаёт `tcp_rmem`; `rmem_max` ограничивает явный `setsockopt` (B-20). |
| Ст. 14:217: «по умолчанию Linux выделяет ~212 КБ» | **VERIFIED** (для UDP) | [EXP] `/proc/sys/net/core/rmem_default` = 212992 (UDP берёт его); у TCP-клиента `SO_RCVBUF = 131072` из `tcp_rmem[1]`. |

**Поправка к Brief:** `rmem_max = 4194304` — ядерный дефолт текущего mainline, а не «значение дистрибутива» [KERN `sock.c:287`, `Documentation/admin-guide/sysctl/net.rst`].

### 2.12. J-H12. TLS

| Утверждение | Статус | Доказательство |
|---|---|---|
| Ст. 18:303–304, 329: «`Handshake()` не проверяет, для какого домена выдан сертификат; нужен ручной `VerifyHostname`» | **INCORRECT** | [EXP] сертификат от доверенного CA для `attacker.com`, клиент `ServerName=example.com`: `Handshake()` → `x509: certificate is valid for attacker.com, not example.com`. Пустой `ServerName` без `InsecureSkipVerify` → `tls: either ServerName or InsecureSkipVerify must be specified`. [SRC `handshake_client.go:46, 1157`]. Ручной вызов нужен только при `InsecureSkipVerify = true`. |
| Ст. 19:93 (SAN проверяется), диаграмма с `VerifyHostname` | **VERIFIED** | Противоречит ст. 18. |
| `PreferServerCipherSuites: true` (ст. 18:254; 19:224) | **INCORRECT** | [SRC `common.go:737–745`]: «legacy field and has no effect… Deprecated». |
| «В Go 1.21+ TLS 1.3 включён по умолчанию» (ст. 18:106, 253) | **INCORRECT** | [WEB] Go 1.13 включил, Go 1.14 убрал `tls13=0`. Минимум по умолчанию — TLS 1.2 [SRC `common.go:1239`]. |
| «Системный вызов `Handshake()`» (ст. 18:303) | **INCORRECT** (термин) | это не syscall. |
| Ст. 18:164: `sync.Pool` для Record Layer и `cipher.AEAD`, «−30–50% GC» | **PARTIALLY CORRECT** | [SRC] `outBufPool = sync.Pool{…}` в `crypto/tls/conn.go:971` (буферы записи); для `cipher.AEAD` пула нет. Число 30–50% без источника → C-NUM. |
| Ст. 18:162: FIPS 140-3 «без стороннего BoringCrypto» | **VERIFIED** | [WEB Go 1.24 notes] «Go Cryptographic Module… FIPS 140-3». |

### 2.13. J-H13. Отзыв сертификатов и даты

| Утверждение | Статус | Доказательство |
|---|---|---|
| Ст. 19:316: «В Go проверка отзыва настраивается через `x509.VerifyOptions`» | **INCORRECT** | [SRC `verify.go:547`] «WARNING: this function doesn't do any revocation checking». Нужно писать `VerifyPeerCertificate`/`VerifyConnection` + `x/crypto/ocsp`/`x509.ParseRevocationList`. |
| Ст. 19:89–92 описывает отзыв как часть процедуры Go-клиента | **PARTIALLY CORRECT** | Теоретически верно; в Go по умолчанию не выполняется. |
| «OCSP Stapling — современный стандарт» | **OUTDATED** | [WEB] Let's Encrypt: OCSP-серверы выключены 2025-08-06, дальше только CRL. |
| SC-081: 200 дней с 15.03.2026, 100 — с 15.03.2027, 47 — с 15.03.2029 | **VERIFIED** | [WEB] CA/B Forum Ballot SC-081v3 (утв. 2025-04-11). В тексте этих дат нет → добавление. |
| Chrome Root Program v1.8 (clientAuth EKU) | **NOT CHECKED** | |

### 2.14. J-H14. HTTP/3 и QUIC

| Утверждение | Статус | Доказательство |
|---|---|---|
| Ст. 23:81: `net/http` без нативного HTTP/3 | **VERIFIED** | [API] `api/go1.24–1.27.txt` без HTTP/3-типов; [SRC] `x/net/http3` — заглушка. |
| Ст. 23:165, 229; 44:148: `golang.org/x/net/http3` | **INCORRECT** | см. J-H5; противоречит ст. 23:81. |
| Ст. 23:69: «Приложение Go —HTTP/2 Frames→ QUIC» | **INCORRECT** | [RFC 9114 §1, §4] HTTP/3 имеет собственные фреймы; QPACK вместо HPACK. |
| Ст. 24:27, 183: «По умолчанию используется BBRv2 (в quic-go настраивается)» | **INCORRECT** | [SRC quic-go v0.63.0 `internal/ackhandler/sent_packet_handler.go:132–137`] `NewCubicSender(…, true /* use Reno */, …)`; BBR в quic-go отсутствует. RFC 9002 по умолчанию — NewReno. |
| Ст. 24:181: `PTO = RTT + 4 * SmoothedRTT + MaxAckDelay` | **INCORRECT** | [RFC 9002 §6.2.1] `PTO = smoothed_rtt + max(4*rttvar, kGranularity) + max_ack_delay`. |
| Ст. 24:143: «отправитель ждёт `WINDOW_UPDATE`» | **INCORRECT** | `WINDOW_UPDATE` — HTTP/2. В QUIC: `MAX_DATA`, `MAX_STREAM_DATA`, `MAX_STREAMS` [RFC 9000 §19]. |
| Ст. 24:182: «QUIC читает `ECN-CE` и `ECN-Echo` из IP-заголовка» | **PARTIALLY CORRECT** | ECN-кодпоинты ECT(0)/ECT(1)/CE читаются из IP, счётчики возвращаются в `ACK_ECN`; «ECN-Echo» — TCP-флаг [RFC 9000 §13.4]. |
| Ст. 23:88, 157; 24:112: «64-битный CID» | **PARTIALLY CORRECT** | [RFC 9000 §17.2] CID — до 20 байт (version 1); 64 бита — типичная, но не фиксированная длина. |
| Ст. 23:131: «Сервер валидирует 0-RTT после завершения handshake» | **INCORRECT** | [RFC 9001 §4.6] сервер принимает и обрабатывает 0-RTT раньше; защита от replay — на прикладном уровне (RFC 8470 `Early-Data`). |
| Ст. 24:112: «после миграции теряются ключи» | **INCORRECT** | Ключи не привязаны к 5-tuple; миграция требует `PATH_CHALLENGE/RESPONSE` [RFC 9000 §9]. |
| Ст. 23:159: «hole punching встроен в `quic-go` (ICE/STUN)» | **INCORRECT** | [SRC] в не-тестовом коде quic-go нет STUN/ICE (`grep` — только `_test.go`). |
| «UDP GSO/GRO, TSO/GRO/checksum offload при QUIC» | **NOT CHECKED** | |
| Ст. 23 «сервер только с h3 без `Alt-Svc`/HTTPS RR и без TCP-fallback» | **NOT CHECKED** | [RFC 9460] существует; в статье не описан (пропуск). |
| «`sync.Pool` −60–70%» (ст. 23:111) | **NOT CHECKED** (числа) | |

### 2.15. J-H15. HTTP/2 Rapid Reset

| Утверждение | Статус | Доказательство |
|---|---|---|
| Ст. 22:245: защита Go — «`MaxHeaderListSize` и `ReadHeaderBufferSize`» | **INCORRECT** | поля не существуют; |
| Реальная защита | **VERIFIED** | [SRC x/net v0.59.0 `server.go:2251–2266`]: число живых обработчиков ≤ `advMaxStreams`, остальные в очереди; при очереди > `4×advMaxStreams` — `ENHANCE_YOUR_CALM` (`too_many_early_resets`). **K5: Brief прав, Gemini (`MaxRSTFrameRate`) — нет.** |
| CVE-2023-39325 / Go 1.20.10, 1.21.3 / x/net 0.17.0 | **VERIFIED** | [WEB] Go vulndb GO-2023-2102. |
| CONTINUATION Flood CVE-2023-45288 (Go 1.21.9/1.22.2, x/net 0.23.0) не упомянут | **VERIFIED** (пропуск) | [WEB] |

### 2.16. J-H16. Формулы TCP и ядро

| Утверждение | Статус | Доказательство |
|---|---|---|
| Ст. 12:103–104: `RTO = SRTT + max(K, DELAYED_ACK_TIME)·4`, `K = 4·RTTVAR` | **INCORRECT** | [RFC 6298 §2]: `RTO <- SRTT + max(G, K*RTTVAR)`, `K = 4`; `DELAYED_ACK_TIME` в формуле нет. |
| Ст. 12:182, 200, 215: «`TCP_DELACK_MAX` ≈ 40 мс»; «таймер `tcp_delack_max` (40 мс)» | **INCORRECT** | [KERN `include/net/tcp.h:150,154`] `TCP_DELACK_MAX = HZ/5` (200 мс), `TCP_DELACK_MIN = HZ/25` (40 мс). |
| Ст. 12:339: `tcp_rto_min`, `tcp_delack_max` — sysctl | **INCORRECT** | Есть `tcp_rto_min_us` (мкс; default 200000) и `tcp_rto_max_ms` [KERN `ip-sysctl.rst`, EXP на 7.2.8]; `tcp_rto_min`, `tcp_delack_*` — нет. |
| Ст. 12:131–132: `ip route … rto_min 200ms` | **VERIFIED** | [KERN `ip-sysctl.rst`]: `rto_min` route option имеет наивысший приоритет. |
| Ст. 13:142, 257: Cubic `β ≈ 0.2`, окно уменьшается на 20% | **INCORRECT** (для Linux/RFC) | [RFC 9438 §4.6] `β_cubic = 0.7`; [KERN `tcp_cubic.c:50`] `beta = 717/1024`. Значение 0.2 — нотация оригинальной статьи Ha et al. (β как *величина уменьшения*), не современный стандарт. |
| Ст. 13:141: `K = ∛(W·β/C)` | **PARTIALLY CORRECT** | При β = 0.2 нотация оригинальной статьи. Для RFC 9438 `K = ∛((W_max − cwnd_epoch)/C)`, `C = 0.4`. |
| Ст. 13:180: «Кевин Якобсон» | **INCORRECT** | авторы BBR: Neal Cardwell, Yuchung Cheng, C. Stephen Gunn, Soheil Hassas Yeganeh, **Van** Jacobson [WEB ACM Queue 14(5), 2016]. |
| Ст. 13:182: оптимальная точка (Kleinrock, 1979) | **VERIFIED** | [WEB] обзор статьи BBR (Acolyer): «proved by Leonard Kleinrock in 1979». |
| Ст. 13:206: «согласно принципу неопределённости Клейнрока…» | **INCORRECT** (атрибуция) | неразличимость измерений BtlBw и RTprop — результат Jaffe (1981); формулировки «принцип неопределённости Клейнрока» в BBR-статье не найдено (по доступному изложению). |
| Ст. 12:92: «3 DupACK → потеря с вероятностью > 99.9%» | **PARTIALLY CORRECT** | порог 3 — RFC 5681; вероятность выдумана (C-NUM). |
| `tcp_retries2=15` «13–30 мин» | **PARTIALLY CORRECT** | [KERN `ip-sysctl.rst`] 924,6 с ≈ 15,4 мин. |
| Ст. 13:244: «BBR **требует** `fq`» | **NOT CHECKED** | Brief утверждает, что с 4.13 есть внутренний TCP pacing; в этой сессии `tcp_bbr.c`/`tcp_output.c` по этому вопросу не читал. |
| Ст. 13:245: «BBR v2 (и v3)» как доступные | **OUTDATED** | В mainline только `tcp_bbr.c` (BBRv1) [KERN]. |

### 2.17. J-H17. UDP

Эксперимент на `veth`, MTU 1500, IPv4, `Dial("udp4")`:

| Запись | DF (`IP_PMTUDISC_DO`) | Результат записи | Приём |
|---|---|---|---|
| 1472 Б | нет | OK | целиком |
| 1473 Б | нет | OK (фрагментируется) | **целиком** (1473) |
| 3000 Б | нет | OK | в буфер 1500 → **`n = 1500, err = nil`, `flags = MSG_TRUNC`** (виден только через `ReadMsgUDP`) |
| 65 507 Б | нет | OK | |
| 65 508 Б | нет | **`message too long`** | |
| 1473, 3000 Б | да | **`message too long`** | |

| Утверждение | Статус |
|---|---|
| Ст. 14:236: «буфер 1500 гарантирует чтение целого пакета без усечения» | **INCORRECT** (`n = 1500, err = nil`, молчаливое усечение) [EXP] |
| Ст. 9:126–129, 403: UDP > MTU → `message too long` при `Write` | **INCORRECT** (EMSGSIZE при DF-флаге или > 65 507) [EXP]; **K12 закрыт: тест на MTU 1500.** |
| Ст. 14:150: `connect` «ускоряет отправку на 10–15%» | **NOT CHECKED** (число) |
| Ст. 14:330–334: «UDP молча выбрасывает… ни ошибки» + `ss -u -a` (`RcvbufErrors`) | **PARTIALLY CORRECT**: молчаливый дроп — верно; `RcvbufErrors` виден в `netstat -su`/`nstat`, `ss -u -a` его не показывает (по `ss`-выводу — **NOT CHECKED**). |
| Ст. 14:322: «Prometheus push-gateway» как UDP-протокол | **NOT CHECKED** (Pushgateway — HTTP; по Brief) |

### 2.18. J-H18. Листинги, которые делают не то, что заявлено

| Ст. | Что заявлено → что делает | Статус | Доказательство |
|---|---|---|---|
| 27:165, 195, 255 | «`FlushInterval = 0` — немедленный flush, `>0` буферизует» | **INCORRECT** | [SRC `reverseproxy.go:141–151, 666–681`]: 0 — периодического flush нет; `<0` — после каждой записи; `text/event-stream` и `ContentLength == -1` — всегда сразу. |
| 40:155–158 | `BaseContext` кладёт `start_time` «для запросов» | **INCORRECT** | [EXP] 3 запроса → `BaseContext` вызван 1 раз (на `Serve`). Ключ строка → `staticcheck SA1029`. |
| 25:232–268 | «`<-r.Context().Done()` — клиент отключился» | **INCORRECT** | [EXP] после `Hijack` и закрытия клиента `r.Context()` не отменён за 1,5 с. Ст. 25:222–229: `CheckOrigin: return true` — B-13. |
| 43:263–285 | `uuid.New()` внутри `CreateOrder` | **VERIFIED** (логическая ошибка по коду) | ключ создаётся на каждый вызов → внешний ретрай создаёт дубль. |
| 33:86–138 | per-IP лимитер как защита; карта без очистки; порядок `global` → per-IP | **VERIFIED** (по коду) | [VET] также лишний `time`. Карта растёт без TTL; `global.Allow()` до per-IP тратит глобальный токен. |
| 43:190–235 | Half-Open: «один запрос» | **VERIFIED** (по коду) | `case 2: return true` для всех до `Record*`. |
| 26:150–182 | «корректный» bidi-стриминг | **PARTIALLY CORRECT** | `CloseSend` в `defer`, но функция выходит сразу после `Send`-цикла, не дождавшись `Recv() == io.EOF`. Результат зависит от вызывающего. |
| 21:169–183 | `Set("Transfer-Encoding","chunked")`; «`w.Write()` форматирует чанки при наличии заголовка» | **PARTIALLY CORRECT** | [EXP] заголовок лишний (Go сам включает chunked без `Content-Length`; ответ с ним идентичен). Без `Flush` стриминга нет — данные в буфере. |
| 35:309–325 | `runContinuousProbe(ctx, …)` | **VERIFIED** (по коду) | `for range ticker.C` не смотрит `ctx`; `wg.Wait()` недостижим. |
| 17:255–300 | `lookupWithTimeout` + «изолированный резолвер» | **NOT CHECKED** по существу (код прочитан только в Brief) |
| 2:122 | `SetReadDeadline` вне цикла; `io.EOF` как ошибка; `fmt` не используется | **VERIFIED** [VET][код] | Соединение умирает через 30 с независимо от активности; `ctx` не используется; `continue` после ошибки `Accept` — B-26. |
| 30:186–190 | round-robin `int64` | **VERIFIED как Low** | поле приватное и стартует с 0; 2⁶³ инкрементов недостижимо. Ошибка в ответе ст. 30:196 («atomic не вызывает cache bouncing») — **NOT CHECKED**. |

### 2.19. J-H19. Raw-сокеты, ICMP

| Утверждение | Статус | Доказательство |
|---|---|---|
| Ст. 35:111, 364: raw-сокет блокирует M/тред; `runtime.LockOSThread`, «scheduler blocking» | **INCORRECT** | [SRC] `net.ListenIP`/`DialIP` создают неблокирующие сокеты через `sysSocket` (`SOCK_NONBLOCK`), `Read` паркует горутину через netpoller. |
| Ст. 35:363: «Go не поддерживает `IP_HDRINCL` в стандартной `net` из-за ограничений безопасности» | **PARTIALLY CORRECT** | [SRC] `net` сам не ставит `IP_HDRINCL` (grep пуст), но не «из-за безопасности»: управляйте через `SyscallConn`/`x/net/ipv4.RawConn`. |
| Для `"ip4:icmp"` нужны root или `CAP_NET_RAW`; без них — `icmp.ListenPacket("udp4", …)` | **VERIFIED** | [SRC x/net `icmp/listen_posix.go`]: «For non-privileged datagram-oriented ICMP endpoints, network must be "udp4" or "udp6»; `ping_group_range` — **NOT CHECKED** (не воспроизводил). |

### 2.20. J-H20. K8s и L4-балансировка

| Утверждение | Статус | Доказательство |
|---|---|---|
| Ст. 30:89: «CoreDNS возвращает список IP подов» для `svc.default.svc.cluster.local` | **INCORRECT** для ClusterIP-сервиса | [WEB] kubernetes.io: обычный Service резолвится в ClusterIP; список IP подов отдаёт только headless. |
| Ст. 30:259: «Headless с `publishNotReadyAddresses: true`» | **INCORRECT** как совет по балансировке | [WEB] поле публикует *неготовые* адреса (основное использование — peer discovery у StatefulSet). |
| Формат имени `svc.default.svc.cluster.local` | **VERIFIED** (K11) | `svc` может быть именем сервиса. |
| Ст. 41:150–181: `MaxIdleConnsPerHost: 100` к ClusterIP без слов о залипании | **VERIFIED** (пропуск) | kube-proxy балансирует при установке соединения (L4); keep-alive/HTTP/2/gRPC остаются на одном поде. Источник «Virtual IPs and Service Proxies» — **NOT CHECKED подробно**, закреплено общим описанием. |

### 2.21. J-H21. VLAN и MTU

| Утверждение | Статус | Доказательство |
|---|---|---|
| Ст. 9:119, 126, 224, 401: 802.1Q-тег уменьшает MTU до 1496 | **INCORRECT** | [WEB/IEEE 802.3ac, 1998] максимальный кадр 1518→1522, payload 1500; [EXP] `ip link add link v0 name v0.10 type vlan id 10` → `mtu 1500`. |
| Ст. 9:224: «1426 байт» | **INCORRECT** | построено на ложной посылке: VLAN-тег MTU не уменьшает; VXLAN поверх IPv6 даёт 1500−70 = 1430, а не 1426. |
| Ст. 9:203–216: итог VXLAN 50 Б | **VERIFIED** (число) / **PARTIALLY CORRECT** (состав) | [EXP] `vxlan` над `veth` MTU 1500 → `mtu 1450`. Состав: 20 IP + 8 UDP + 8 VXLAN + **14 внутренний Ethernet**, а не внешний (B-25). |
| Ст. 9:211: порт 4789 / «в ранних реализациях ядра 8472» | **PARTIALLY CORRECT** | [EXP] `ip link add vxlan` без `dstport` → `dstport 8472`; `iproute2`: «Will use Linux kernel default (non-standard value)». 8472 — текущий дефолт модуля, а не «ранние реализации». Дефолты CNI — **NOT CHECKED** по первичным докам. |

### 2.22. J-H22. `mtr`/`dig`

| Утверждение | Статус | Доказательство |
|---|---|---|
| Ст. 35:355: потери на hop-2, исчезающие на hop-3 → проблема оборудования | **CONTEXT-DEPENDENT** | В `man mtr` сказано только «sudden increase in packet loss… often indicates a bad link». Объяснение «ICMP rate limiting» в моих источниках не подтверждено; **RFC 4443 §2.4 / Cisco / RIPE не открывались → NOT CHECKED**. |
| Ст. 35:171: флаг `DO` | **INCORRECT** | см. J-H7. |

### 2.23. J-H23. Прокси

| Утверждение | Статус | Доказательство |
|---|---|---|
| Ст. 28:59, 81, 157, 179: «nginx использует `splice()`…» | **INCORRECT** | [SRC] `git clone nginx`, `grep -rIi splice src/` → 0 совпадений. HAProxy `splice` поддерживает (`option splice-*` в `configuration.txt`). `sendfile` у nginx есть, но не для проксирования и не поверх TLS без kTLS. |
| Ст. 28:111–115: HAProxy «single-threaded event loop» | **INCORRECT/OUTDATED** | [WEB `configuration.txt`] `nbthread` по умолчанию = числу доступных CPU (на платформах с CPU affinity); иначе 1. Многопоточность — с 1.8. |
| Ст. 28:114: HAProxy реализует управление окном перегрузки и ACK в user-space | **INCORRECT** | TCP — ядерный (в моих источниках нет контрпримера; логика стандартная). **Подтверждено только отсутствием в docs → CONTEXT-DEPENDENT/NOT CHECKED глубже.** |
| Ст. 28:122: Envoy — «стандарт для Istio, Linkerd» | **INCORRECT** | Linkerd — `linkerd2-proxy` на Rust; ст. 42:137 говорит верно. |
| «написанный на C++ и LLVM» | **INCORRECT/мелочь** | Envoy на C++; «LLVM» — лишнее. |

### 2.24. J-H24. Service Mesh

| Утверждение | Статус | Доказательство |
|---|---|---|
| Ст. 42:153: «`http.Transport` превращается в соединение к `127.0.0.1:15001`» | **INCORRECT** | [WEB Istio] iptables `REDIRECT` на порт Envoy; приложение подключается к исходному адресу, Envoy получает его через `SO_ORIGINAL_DST`. |
| Ст. 42:214: port exhaustion у `127.0.0.1:15001`, `SO_REUSEPORT`, UDS «в Linkerd по умолчанию» | **INCORRECT** | `SO_REUSEPORT` не лечит; Linkerd использует iptables-перехват на порты 4143/4140 [WEB linkerd.io/reference/iptables], а не UDS. |
| Ст. 42:154: «Envoy перехватывает DNS» | **PARTIALLY CORRECT** | [WEB Istio DNS Proxying] DNS-прокси работает в `istio-agent` (`pilot-agent`), по умолчанию выключен (`ISTIO_META_DNS_CAPTURE`). |
| Ст. 42:218: «sidecar использует `SO_LINGER=0`» | **NOT CHECKED** (источник не найден, вероятно выдумка) |
| Ст. 42:138: «~10–20 МБ RAM Linkerd» | **NOT CHECKED** (число) |

### 2.25. J-H25. SSE

| Утверждение | Статус | Доказательство |
|---|---|---|
| «SSE строится на HTTP Upgrade» (ст. 25:9, 101) | **INCORRECT** | [WEB WHATWG HTML] SSE — обычный HTTP-ответ с `text/event-stream`, без `Upgrade`/101. |
| Ограничения `EventSource` (только GET, нет заголовков, ~6 соединений на origin в HTTP/1.1) | **NOT CHECKED** (в Brief — пропуск) |

### 2.26. J-H26. `IdleConnTimeout` и MSL

| Утверждение | Статус | Доказательство |
|---|---|---|
| Ст. 39:151, 216: «`IdleConnTimeout` обязан быть > 2·MSL (60 с)» | **INCORRECT** | [SRC `transport.go`] `IdleConnTimeout` — время жизни простаивающего соединения *в пуле*, к `TIME_WAIT` не относится. Практическое правило обратное (клиентский < серверного/LB). |
| Ст. 39:115: «если `IdleConnTimeout` < 60 с, соединения закрываются до завершения `TIME_WAIT`… цикл `SYN → FIN`» | **INCORRECT** | `TIME_WAIT` у стороны, закрывшей первой, не зависит от этого таймаута. |
| «AWS ALB 60 с / NLB 350 с» как ориентиры | **VERIFIED** (NLB: 350 с TCP, настраивается 60–6000) [WEB]; ALB — **NOT CHECKED** |

### 2.27. J-H27. Go на edge

| Утверждение | Статус | Доказательство |
|---|---|---|
| Ст. 31:121, 258: «нет GC-пауз, нет escape-анализа» | **INCORRECT** | В Go есть STW-паузы (короткие); escape-анализ выполняет компилятор [WEB go.dev/doc/gc-guide — **не открывал в этой сессии**; общеизвестно]. **Статус INCORRECT присвоен по общеизвестному факту, первичный источник не проверен.** |
| «упакованные в eBPF/FFI» | **INCORRECT** (Go в eBPF не компилируется стандартным тулчейном) | **NOT CHECKED** по источнику. |

### 2.28. J-H28. Планировщик в статье о DDoS

| Утверждение | Статус | Доказательство |
|---|---|---|
| Ст. 33:142: «Планировщик Go не может создать новые P, если ОС не может выделить FD» | **INCORRECT** | число P = `GOMAXPROCS`; к FD не относится [SRC `runtime`; логика `procresize`]. |
| «используйте `context.Background()` или пул контекстов» | **INCORRECT** | пула контекстов нет; без таймаута — вредно. |
| «мьютекс переходит в состояние фаззинга (futex)» | **INCORRECT** | в `sync.Mutex` есть *starvation mode*, термина «фаззинг» нет; на Linux парковка идёт через планировщик/семафор. **`sync/mutex.go` целиком не перечитывал.** |

### 2.29. J-H29. Заголовки HTTP

| Утверждение | Статус | Доказательство |
|---|---|---|
| Ст. 20:321: `authorization: Bearer xyz` → `r.Header["Authorization"]` вернёт `nil` | **INCORRECT** | [EXP] сервер канонизирует ключи: `Header["Authorization"]=["Bearer xyz"]`; `Header["authorization"]` пуст. |
| Ст. 20:297: `Header.Get("X-Custom")` «склеен через запятую» | **INCORRECT** | [EXP] `Get("x-custom")="a"`, `Values=["a" "b"]`. |
| Ст. 20:106, 152: `Server: Golang/1.24` в ответе | **INCORRECT** (для `net/http`) | [EXP] заголовок `Server` по умолчанию не отправляется. |

### 2.30. J-H30. Дренаж тела

| Утверждение | Статус | Доказательство |
|---|---|---|
| Ст. 21:102–107, 240–245: после `Close()` соединение возвращается в пул | **PARTIALLY CORRECT** | [EXP] тело 8 МБ: 5 запросов без чтения → **5** TCP-соединений; с `io.Copy(io.Discard, …)` → **1**. Для маленького тела (прочитано целиком буфером) — 1. |
| Пропуск «дренаж до `Close()`» | **VERIFIED** (пропуск) | |

---

## 3. Конфликты брифов (K1–K12) и их решение

| # | Тема | Решение | Основание |
|---|---|---|---|
| K1 | `epoll_pwait` | **Brief прав**: имя верно, обоснование «маскировка сигналов» неверно | [SRC `syscall_linux.go:32`] |
| K2 | sysctl/опции RTO и delayed ACK | **Brief прав**: есть `tcp_rto_min_us`, `tcp_rto_max_ms`, сокетные `TCP_RTO_MIN_US`, `TCP_DELACK_MAX_US`; имён `tcp_rto_min`, `tcp_delack_*` нет | [KERN] `ip-sysctl.rst`, `uapi/linux/tcp.h:143–144`, [EXP] `/proc/sys/net/ipv4` на 7.2.8. **Версия ядра появления — NOT CHECKED.** |
| K3 | «Дополнительные epoll-инстансы» | **Brief прав**: цитата перефразирована; ошибка (лимит FD) есть | ст. 38:82 |
| K4 | Ст. 12 в списке `SetNoDelay` | **Brief прав**: ст. 12 верна | ст. 12:227–228, 342 |
| K5 | Защита Go от Rapid Reset | **Brief прав**: учёт живых обработчиков | [SRC x/net `server.go:2251–2266`] |
| K6 | Round-robin `int64` | **Brief прав**: Low | |
| K7 | `IdleConnTimeout > 2·MSL` | **High подтверждён** | см. 2.26 |
| K8 | `LookupNetIP` как «zero-alloc» | **Brief прав**: `[]netip.Addr` — срез в куче; `Resolver.LookupIP` — Go 1.15, `LookupIPAddr` — 1.8, `LookupNetIP` — 1.18 | [API] |
| K9 | `os/rlimit.go` | **Brief прав**: код в `syscall/rlimit.go`; Go 1.19 | [SRC] `syscall/rlimit.go:32–42` `Cur = Max − 1`; [WEB] Go 1.19 notes («Go programs that import package `os`… increase RLIMIT_NOFILE»). |
| K10 | «Go 1.11» в ст. 16 | **Brief НЕ прав**: ст. 16:84 содержит «версии 1.11» (без слова «Go») | `sed -n 84p` на ст. 16; B-4 |
| K11 | `svc.default.svc.cluster.local` | **Brief прав** | |
| K12 | UDP 1500 по `lo` | **Закрыт экспериментом на `veth` MTU 1500** | см. 2.17 |

---

## 4. Сквозные кластеры

| Кластер | Статус | Доказательство |
|---|---|---|
| **C-LISTEN** — `net.Listen` на `:8080` | **VERIFIED** | [EXP] сокет `AF_INET6`, адрес `[::]:port`; `SOCK_NONBLOCK\|SOCK_CLOEXEC` в `socket()` [SRC `sock_cloexec.go:20`]; `accept4(SOCK_NONBLOCK\|SOCK_CLOEXEC)` [SRC]. Ст. 2:191 `socket(AF_INET, …)`, ст. 10:272 `socket(AF_INET, SOCK_STREAM, 0)`, ст. 15:129 — **INCORRECT/упрощение**. |
| ст. 15:199: «`listen(5)` пропустит до `somaxconn`» | **INCORRECT** | очередь = min(backlog, somaxconn). Go читает backlog из `/proc/sys/net/core/somaxconn` [SRC `sock_linux.go:33–52`]. |
| `somaxconn` «по умолчанию 128» | **OUTDATED** | [KERN] `ip-sysctl.rst`: «Defaults to 4096. (Was 128 before linux-5.4)». |
| **C-TIMEWAIT** — «двухминутный `TIME_WAIT`» (ст. 2:194) | **INCORRECT** | [KERN `tcp.h:140`] `TCP_TIMEWAIT_LEN = 60*HZ`; ст. 10:217, 39:28 верны. |
| **C-GOVER** | см. ниже | |
| **C-ECMP** | **VERIFIED** | [EXP] IPv4: второй `ip route add` с теми же prefix/metric → `File exists`; IPv6 `append` объединил в multipath. Ст. 6:153 («одинаковые prefix+metric → ECMP») **INCORRECT** для IPv4. |
| **C-INTERNALS** | | |
| `struct tcp_sock` «в `include/net/tcp.h`» (ст. 10:115, 11) | **INCORRECT** | [KERN] в `include/linux/tcp.h:197`. |
| «изменение полей требует `LOCK CMPXCHG`» (ст. 10:121) | **INCORRECT** | поля меняются под socket lock; **глубже не проверял.** |
| «HPACK динамическая таблица — LRU» (ст. 22:167, 192) | **INCORRECT** | [SRC x/net `hpack/tables.go:13–29`] FIFO-срез `ents`; RFC 7541 — вытесняется самая старая. |
| Ст. 20 «нет interning» | **INCORRECT** | [SRC `textproto/reader.go:794–806`] `commonHeader` интернирует. |
| Ст. 20/22 прочие внутренности | **NOT CHECKED** | |
| **C-MARKUP** | | |
| Повреждённый LaTeX в ст. 4:57, 64, 110 | **VERIFIED** | в 64-й строке перед `imes` стоит TAB (`\t`), аналогично `\a` перед `pprox`. |
| Пустой блок `SO_BINDTODEVICE` (ст. 3:255–258) | **VERIFIED** | только два комментария. «Требует `CAP_NET_RAW`» — **OUTDATED**: с Linux 5.7 не нужно, если сокет ещё не привязан [WEB]. «Через `x/net/ipv4`» — **INCORRECT**. |
| «4 КБ макс» (ст. 22:66) против 16 384 (строка 87) | **VERIFIED** | противоречие внутри статьи. |
| **C-HISTORY** | | |
| «TCP/IP… рождён в Bell Labs» (ст. 2:13) | **PARTIALLY CORRECT/INCORRECT** | Bell Labs — Unix; TCP/IP — DARPA/Stanford/BBN/Berkeley. **Первоисточник не открывался; оценка по общеизвестной истории.** |
| «net/http спроектирован гениями Bell Labs» (ст. 21:7), OSPF «Bell Labs» (7:176) | **INCORRECT/OPINION** | |
| Эпиграф ст. 10, 14 (Эйнштейн) | **OUTDATED/INCORRECT атрибуция** | [WEB] «significant problems… same level of thinking» — «no known source in the given wording»; «simple as possible but not simpler» — перефразировка (Sessions, NYT 1950). |
| Эпиграф ст. 12 («Перефразируя Кнута») | **PARTIALLY CORRECT** | «Преждевременная оптимизация — корень всех зол» — Knuth (1974); вторая половина добавлена. |
| Эпиграф ст. 16 (HOSTS.TXT) | **PARTIALLY CORRECT** | Фейнлер/SRI — верно; сам «текст цитаты» помечен «Из истории» — не атрибутирован. «Стэнфорд» → **Stanford Research Institute (SRI)** (в строке 6 сказано верно). |
| Эпиграфы Кернигана («Управление сложностью…»; «…размышление вкупе с print…») | **NOT CHECKED** по первичному тексту; атрибуция в целом принята. |
| **C-EXT** (дата-зависимые факты) | | |
| ingress-nginx выводится | **VERIFIED** | [WEB] kubernetes.io/blog/2026/01/29/ingress-nginx-statement. |
| kube-proxy: nftables GA в 1.33, IPVS deprecated в 1.35 | **VERIFIED** | [WEB] kubernetes.io блог/KEP-5495. |
| Linkerd: с 2.15 нет open-source stable-релизов | **VERIFIED** | [WEB] buoyant.io. |
| RFC 793→9293, 7234→9111, 8312→9438, 1631→3022 | **VERIFIED** | `Obsoletes:` в заголовках RFC. |
| `nhooyr.io/websocket` → `coder/websocket`, gorilla archived/revived, Weave Net, Telia→Arelion | **NOT CHECKED** | |
| **C-NUM** | **NOT CHECKED** | см. раздел 9. |

### C-GOVER (версии Go)

| Ст., строка | В тексте | Статус | Доказательство |
|---|---|---|---|
| 12:296 | `SetKeepAlivePeriod` с Go 1.16 | **INCORRECT** (1.2) | [API] |
| 18:106, 253 | TLS 1.3 по умолчанию с Go 1.21 | **INCORRECT** (1.13/1.14) | [WEB] |
| 44:71 | ET «Go 1.22+» | **INCORRECT** (с 1.1) | [SRC go1.1] |
| 13:366 | `Transport.ReadBufferSize/WriteBufferSize` «с Go 1.19» | **INCORRECT** (1.13, дефолт 4 КБ) | [API][WEB] |
| 27:252 | HTTP/2 к бэкендам «Go 1.11+» | **INCORRECT** | `ForceAttemptHTTP2` — Go 1.13 [API]; h2-клиент существует с Go 1.6 (**по Brief; 1.6 не перепроверялось**). |
| 33:195 | «В Go 1.21+ появился новый сервер» | **INCORRECT** (нет такого события) | **NOT CHECKED** по release notes 1.21 подробно. |
| 39:127 | «В Go 1.21+ планировщик использует `netpoll` для приёма» | **INCORRECT** | netpoll с Go 1.1 [SRC go1.1]. |
| 40:145 (`ReadHeaderTimeout` «Go 1.8») | **VERIFIED** [API go1.8] |
| 40:154 (`BaseContext` «Go 1.13+») | **VERIFIED** [API go1.13] |
| 12:145 (`Temporary()` deprecated с 1.18) | **VERIFIED** [API go1.18: `//deprecated`] |
| 21:189, 25:160 (`ResponseController` Go 1.20) | **VERIFIED** [API go1.20] |
| 27:198 (`Rewrite` Go 1.20) | **VERIFIED** [API go1.20: `ProxyRequest`] |
| 4:230 (`net/netip` Go 1.18) | **VERIFIED** [API go1.18] |
| 6:330 (`ListenConfig.Control` Go 1.11) | **VERIFIED** [API go1.11] |
| 43:151 (`sync.Pool` «в Go 1.21+») | **INCORRECT** (Go 1.3) [API go1.3] |
| 18:162 (FIPS 140-3 Go 1.24) | **VERIFIED** [WEB] |
| 18 (`GOMAXPROCS` «по физическим ядрам») | **OUTDATED** | [WEB Go 1.25]: с Go 1.25 учитывается cgroup CPU-лимит; до этого — число логических CPU (`NumCPU`), а не физических. |
| 33 (`RLIMIT_NOFILE`) | **VERIFIED** (Go 1.19) |
| 22, 27: h2c только через `x/net/http2/h2c` | **OUTDATED** | [API go1.24: `Protocols.SetUnencryptedHTTP2`] |
| 35:251 `DualStack: true` | **OUTDATED** | [SRC `dial.go:153`] «previously enabled RFC 6555 Fast Fallback» — deprecated. |

---

## 5. C-FIX: остатки прошлого фактчека `d9b00f4f`

| # | Что проверено | Статус |
|---|---|---|
| F1 | Ст. 44:104 «до 1024 событий» — новая ошибка; ст. 44:71 «Go 1.22+ ET» | **INCORRECT** оба [SRC] |
| F2 | Ст. 12:131–133 (`rto_min` per-route) | **VERIFIED**; остаются ст. 12:182, 200, 215, 339, 344 | **INCORRECT** |
| F3 | Ст. 12:145–146 «для retry проверяйте `errors.Is(err, context.Canceled)`» | **INCORRECT**: отменённую операцию не повторяют (**логика**, не проверялось экспериментально). `Temporary()` deprecated с 1.18 — **VERIFIED**. |
| F4 | Ст. 17, 30, 44 «кэша нет» | **VERIFIED**; ст. 16:178–179, 221 — **INCORRECT** |
| F5 | Ст. 21:59 (=2) | **VERIFIED**; ст. 21:230 (=100) **INCORRECT** |
| F6 | Ст. 23:81 | **VERIFIED**; ст. 23:165, 229 — **INCORRECT** |
| F7 | Ст. 33 лимитер | **VERIFIED** (глобальный вынесен), карта без очистки и порядок — остались |
| F8 | Ст. 35 `icmp.ListenPacket` | **VERIFIED**; нет слов о привилегиях |
| F9 | Ст. 9 порт VXLAN 4789 + 8472 | **PARTIALLY CORRECT** (см. 2.21) |
| F10 | Ст. 41:149 «350–1000 секунд» | **PARTIALLY CORRECT**: AWS NAT GW и NLB — 350 с [WEB]; GCP Cloud NAT established idle — 1200 с [WEB search result]; Azure LB — 4 мин по умолчанию, 4–100 мин для правил [WEB learn.microsoft.com]. «Без RST»: **INCORRECT** для AWS (NAT GW возвращает RST при попытке продолжить) [WEB]. |
| F11 | Ст. 42:218 | опечатка исправлена; содержание — **NOT CHECKED** |

---

## 6. Blind Spot (B-1 … B-35)

| ID | Статья | Утверждение | Статус | Доказательство |
|---|---|---|---|---|
| **B-1** | 4:296–303, 321 | `netip.Addr`/`Prefix` как ключи allow/deny-списков | **INCORRECT** (для dual-stack listener) | [EXP] принятый IPv4-клиент: `::ffff:127.0.0.1`, `Is4()=false`, `Is4In6()=true`, `Prefix.Contains(addr)=false` (после `Unmap()` — `true`); `addr == 127.0.0.1` — `false`. `net.IP`: `len 16` vs `4`, `Equal` = `true`. Совет `bytes.Equal` для `net.IP` неверен. |
| **B-2** | 44:172 | «Отмена контекста возвращает `context.Canceled` при чтении/записи» | **INCORRECT** | [EXP] `DialContext` + `cancel()`; `Read` всё ещё блокирован через 1,5 с. [SRC `dial.go`] контекст действует только на установление. Верно только: соединение закрывать явно; `TIME_WAIT` — отдельное явление. |
| **B-3** | 12:249–331, 356; 10:158 | Keepalive ловит смерть пира | **PARTIALLY CORRECT** (не работает при неподтверждённых данных) | [EXP] `idle 2 с, interval 1 с, count 3` + DROP: простаивающее соединение — `Read` вернул ошибку через **4,1 с**; соединение с неподтверждёнными данными (`tcp_retries2=5`) — **13,4 с** (≈ сумма RTO, keepalive не вмешался); с `TCP_USER_TIMEOUT=3000` — **3,4 с**. [KERN] `tcp_timer.c:823–824` (`packets_out` → `goto resched`); grpc-go ставит `TCP_USER_TIMEOUT` сам [SRC]. |
| B-4 | 16:84 | «версии 1.11… на всех Unix» | **INCORRECT** | см. K10. |
| B-5 | 38:158–159 | «`dialer.Timeout` — только SYN/SYN-ACK» | **INCORRECT** (Brief: «верно») | [SRC `dial.go:529–542`] `dialCtx` (дедлайн) применяется **до** `resolveAddrList`; таймаут включает DNS и делится между адресами. |
| B-6 | 27:249 | `NewSingleHostReverseProxy` ставит `Host` бэкенда | **INCORRECT** | [EXP] бэкенд получил `Host: api.example.com`; [SRC `reverseproxy.go:313`]. |
| B-7 | 9:329; 27:155 и др. | Кастомный `&http.Transport{…}` | **PARTIALLY CORRECT** (потеря `Proxy`) | [SRC `transport.go:47–58`]: `DefaultTransport` задаёт `Proxy: ProxyFromEnvironment`; нулевой `Transport` — `Proxy == nil`. Ст. 9: `Transport` на каждый вызов — антипаттерн (doc: «Transports should be reused instead of created as needed», `transport.go:72`). |
| B-8 | 30:92, 255–257; 17:172, 328 | `IdleConnTimeout < DNS TTL` лечит устаревший DNS | **INCORRECT** | `IdleConnTimeout` закрывает только idle. **Рассуждение, прямого эксперимента нет.** |
| B-9 | 16:315; 17:285 | «всегда `PreferGo: true`» | **CONTEXT-DEPENDENT** | [SRC `conf.go`] без `PreferGo` на Linux nsswitch-источники (`mdns`, `myhostname`, `sss`, …) отдаются в cgo; с `PreferGo` — нет. На darwin системный резолвер предпочитается по умолчанию. |
| B-10 | 17:311; 19:64 | `CGO_ENABLED=0` + `scratch` | **VERIFIED** (пропуск) | [API] `x509.SetFallbackRoots` — Go 1.20. Эффект «нет CA-бандла» — общеизвестен, **эксперимент не ставил.** |
| B-11 | 18:314–315 | `GOMEMLIMIT` «жёсткий лимит», «OOM-паника», включает буферы сокетов | **INCORRECT** | `GOMEMLIMIT` — мягкий; буферы ядра не входят. **Источник (`gc-guide`) в этой сессии не открывался**: статус по знанию API, поэтому оценка **PARTIALLY verified**. |
| B-12 | 7:399–402 | Liveness-рестарт «чинит» default route | **INCORRECT** (по K8s) | **NOT CHECKED по первоисточнику** (рассуждение). |
| B-13 | 25:222–229, 242 | `CheckOrigin: return true`; нет `SetReadLimit` | **VERIFIED** | [SRC gorilla `server.go:60–67`]: при `nil` — проверка same-origin; `return true` её снимает. `SetReadLimit` есть в `conn.go`. |
| B-14 | 39:17–20, 62–72; 8:97; 41:149 | «28 000 портов» = лимит хоста | **INCORRECT** | [EXP] диапазон 40000–40009: 30 подключений к одному `dst:port` — 10 OK; при двух `dst:port` — 20 OK (4-tuple). AWS NAT GW: «Each new IPv4 address can support up to 55,000 concurrent connections»; GCP Cloud NAT: 64 порта на ВМ по умолчанию [WEB]. |
| B-15 | 2:106; 3:309 | «Dst MAC — адрес следующего шлюза/коммутатора» | **NOT CHECKED** (рассуждение по 802.1D/RFC 826) |
| B-16 | 9:228–229, 403 | Jumbo Frames как «решение» | **CONTEXT-DEPENDENT** | **NOT CHECKED** облачные MTU; общая логика. |
| B-17 | 43:297 | серверная идемпотентность без атомарной резервации | **VERIFIED** (логически) | гонка двух ретраев — по структуре кода. **Не запускалось.** |
| **B-18** | 37:164 | «ET требует вычитывать до `EAGAIN`» | **INCORRECT** | [SRC `internal/poll/fd_unix.go:141–178`] `Read` делает один `syscall.Read`; при `EAGAIN` — `waitRead`; при `n>0` возвращает. Комментарий в `Read` ссылается на ET-ограничение (`go.dev/issue/15735`). |
| B-19 | 23:88, 102–105, 157–159 | миграция QUIC за L4 | **NOT CHECKED** (draft QUIC-LB, RFC 9000 §9–10.3 не перечитывал) |
| B-20 | 11:149–150 | `rmem_default/rmem_max` для TCP | **PARTIALLY CORRECT** | [KERN] `tcp_rmem` задаёт начальный размер. |
| B-21 | 5:333–340 | «шторм ARP» | **NOT CHECKED** |
| B-22 | 6:385 | порядок адресов по `resolv.conf`/`nsswitch.conf` | **INCORRECT** | [SRC `net/addrselect.go`, `dnsclient_unix.go`] сортировка RFC 6724 (`sortByRFC6724`). |
| B-23 | 17:222–227; 16:170 | `single-request-reopen`, `edns0` | **VERIFIED** | [SRC `dnsconfig_unix.go:101`] `single-request` и `single-request-reopen` — один и тот же `case`; неизвестная опция → `unknownOpt` (→ cgo). `no-reload` (121–124) существует. «Конфиг не кэшируется при первом запросе» — **NOT CHECKED** (`tryUpdate` не открывал). |
| B-24 | 36:282 | `Replace: true` | **VERIFIED** | см. J-H5 |
| B-25 | 9:203–216 | состав 50 Б VXLAN | **VERIFIED** | [EXP] MTU `vxlan` = 1450; состав — по RFC 7348 (не открывал) |
| B-26 | 14:225–249; 1; 2; 15 | `continue` на любую ошибку `Accept` | **VERIFIED** (по коду) | горячий цикл после закрытия listener; в ст. 14 `os.Exit(0)` из обработчика сигнала делает `case <-sigChan` мёртвым кодом. |
| B-27 | 18:229–287 | клиент без дедлайнов | **VERIFIED** (по коду) | `net.Dial` без таймаута, `Handshake()` без дедлайна. [API] `HandshakeContext` — Go 1.17. |
| B-28 | 33:229–230 | таймауты `Server` и `Shutdown` | **VERIFIED** | [SRC `server.go:3241`] `Shutdown` не ждёт hijacked; `WriteTimeout` не отменяет `r.Context()` — **NOT CHECKED отдельно**. |
| B-29–B-30 | 37, 39, 41 | `SO_REUSEPORT` | **NOT CHECKED** (следствие J-H10) |
| B-31 | 13:284–294 | `default_qdisc` | **NOT CHECKED** |
| B-32 | 13:365 | `fq_codel` | **NOT CHECKED** |
| B-33 | 4:155–157 | FCS и отказ от checksum IPv6 | **VERIFIED** | [RFC 8200 §8.1] UDP checksum обязательна в IPv6. |
| B-34 | 31:104, 147, 204–221 | кэш-обработчик, `sync.Once` | **NOT CHECKED** |
| B-35 | 3:224–227; 4:230 | мелочи | **NOT CHECKED** |

---

## 7. Medium по статьям: что проверено

Формат: статус по тем пунктам Brief § 6, которые я проверил. Остальное — раздел 9.

| Ст. | Пункт | Статус | Доказательство |
|---|---|---|---|
| 1 | «стек потока ОС 2–8 МБ, 10 000 клиентов — мгновенная смерть» | **NOT CHECKED** | |
| 1 | «TLB flush при переключении потоков» | **INCORRECT** | потоки одного процесса делят адресное пространство **(логика)**; источник — **NOT CHECKED**. |
| 1 | «горутина ~2 КБ на соединение» | **NOT CHECKED** | |
| 2 | Zero-copy: «в Go через `syscall.Splice`; `net/http` классическое копирование» | **INCORRECT** | [SRC] `syscall.Splice` существует (Linux); `net/sendfile_*.go`, `splice_linux.go`; `(*response).ReadFrom` использует `sendfile` для `*os.File` → `*TCPConn` и `splice` для TCP↔TCP (`server.go:606–609`). По TLS — нет. |
| 3 | Linux интерфейсы через `/sys/class/net` | **INCORRECT** | [SRC `interface_linux.go:17, 124`] `NetlinkRIB`. Windows: `GetAdaptersAddresses` (`interface_windows.go:24`), а не `GetAdaptersInfo`. |
| 3 | «tun/tap — чистые IP-пакеты без L2» | **INCORRECT** | [KERN `tuntap.rst`]: «TUN works with IP frames. TAP works with Ethernet frames.» |
| 4 | TTL «на приёме до маршрутизации» | **INCORRECT** | [KERN] TTL — в `ip_forward.c:118, 149`; в `ip_input.c` нет. |
| 4 | Smurf/Teardrop | **NOT CHECKED** |
| 4 | Teredo/6to4 актуальны | **OUTDATED** | [RFC 7526] 6to4 anycast — Historic. Teredo: **NOT CHECKED**. |
| 5 | `arp_tables` как таблица ARP | **INCORRECT** | [KERN] `arp_tables.c` — фильтр `arptables`; ARP — `arp.c` + `neighbour.c`. |
| 6 | Route cache «до 2.6.38» / «с 3.6 ликвидирован» | **PARTIALLY CORRECT** | «ликвидирован в 3.6» **NOT CHECKED**; внутреннее противоречие «2.6.38» vs «3.6» остаётся. |
| 7 | Administrative Distance «ядро выбирает» | **INCORRECT** | **NOT CHECKED** по `ip-route`/kernel; Brief-логика. |
| 7 | TCAM на NIC, `<10 нс` | **NOT CHECKED** |
| 8 | «AWS NAT GW и GCP Cloud NAT режут до 350 с» | **PARTIALLY CORRECT** | AWS NAT GW 350 с [WEB]; GCP Cloud NAT — 1200 с (TCP established) [WEB]. |
| 8 | RFC 1631 → RFC 3022 | **VERIFIED** | |
| 10 | Nagle, `SO_REUSE*` | см. J-H1, J-H10 | |
| 10 | `SetReadDeadline` «переводит сокет в состояние ошибки» (ст. 10:336) | **NOT CHECKED** |
| 11 | SYN flood: `tcp_synack_timer`; лог «possible SYN flooding … Dropping request» | **PARTIALLY CORRECT** | [KERN `tcp_input.c:7530–7565`] sysctl `tcp_synack_timer` нет; лог формата «Possible SYN flooding on port <addr>:<port>. Sending cookies./Dropping request.»: «Dropping request» — при `tcp_syncookies=0`, «Sending cookies» — по умолчанию (=1). |
| 11 | RFC 793 → 9293 | **VERIFIED** | |
| 13 | `cubic_ack` (функция) | **NOT CHECKED** |
| 13 | «`cwnd` исчерпан → `write` вернёт `EAGAIN`» | **INCORRECT** | `EAGAIN` при полном `sndbuf`; `cwnd` ограничивает отправку, а не успешность `write` — **NOT CHECKED** по исходнику. |
| 15 | «Ephemeral ports 49152–65535» | **CONTEXT-DEPENDENT** | [RFC 6335 §6] Dynamic Ports 49152–65535 — IANA; Linux — 32768–60999 [EXP]. |
| 16 | `net.DefaultResolver`/`8.8.8.8` «в серьёзных production не полагайтесь» | **OPINION** | |
| 17 | «CNAME-цепочки убивают latency» | **NOT CHECKED** |
| 17 | «cgo на Alpine — аварийно» | **NOT CHECKED** |
| 20 | `MaxBytesReader` против Slowloris | **INCORRECT** (логика) | `ReadHeaderTimeout` — против Slowloris; `MaxBytesReader` — лимит объёма. |
| 20 | «нет interning» | **INCORRECT** | см. C-INTERNALS |
| 22 | PRIORITY — «дерево приоритетов» | **OUTDATED** | [RFC 9113 §5.3.2] схема deprecated; замена — RFC 9218 [RFC]. |
| 22 | LRU для HPACK | **INCORRECT** | |
| 22:241 | «HPDoS (Rapid Reset / Header DoS)» | **PARTIALLY CORRECT** | Rapid Reset (CVE-2023-44487) ≠ HPACK-bomb. |
| 25 | «Go проверяет заголовок и подтверждает 101» | **PARTIALLY CORRECT** | делает библиотека, не `net/http`. После `Hijack` сбрасываются дедлайны [SRC `server.go:326, 741`]; `Shutdown` не ждёт hijacked [SRC `server.go:3241`]. |
| 25 | «nginx/HAProxy WebSocket по умолчанию» | **NOT CHECKED** |
| 25 | `WriteTimeout` убивает SSE → `ResponseController.SetWriteDeadline` | **VERIFIED** (пропуск) | [API go1.20]. |
| 26 | «контекст → `GOAWAY` или `CANCEL`» | **PARTIALLY CORRECT** | отмена — `RST_STREAM(CANCEL)` (следующая фраза в тексте верна); `GOAWAY` — о соединении. [RFC 9113] |
| 26 | `grpc.WithBlock`, `grpc.Dial` | **OUTDATED** | [SRC grpc v1.84] `grpc.NewClient` существует. |
| 27 | `Director` и `Rewrite` (Go 1.20) | **VERIFIED** | [API go1.20] |
| 27 | «тело ответа копируется в отдельной горутине»; «Go 1.18+ chunked» | **NOT CHECKED** |
| 29 | `IdleConnTimeout 90 с` в разделе про сервер | **INCORRECT** | у `http.Server` — `IdleTimeout` [SRC `server.go:3087–3091`]. |
| 31 | RFC 7234 → 9111 | **VERIFIED** | |
| 35 | `DualStack: true` | **OUTDATED** | см. C-GOVER. |
| 36 | «Offloaded Mode: Mellanox ConnectX…» | **PARTIALLY CORRECT/OUTDATED** | [WEB] hardware offload XDP — Netronome `nfp`; про Mellanox/Intel/Marvell подтверждений не нашёл (по поиску). Не exhaustive. |
| 36 | Стек 512 Б; 11 регистров; 1 млн инструкций | **VERIFIED** | [KERN `filter.h:100`; `bpf_verifier.h`: `BPF_COMPLEXITY_LIMIT_INSNS 1000000`]. |
| 36 | «Верификатор — DAG, без циклов»; «зациклится → soft lockup» | **OUTDATED/INCORRECT** | [WEB] bounded loops с 5.3, `bpf_loop` с 5.17; верификатор гарантирует завершение, поэтому «зависнет» — неверно. |
| 36 | «Mellanox/Intel/Marvell NIC offload» (ст. 36:247) | см. выше | |
| 37 | «процесс блокируется в ядре» (37:115) в Go | **INCORRECT** | сокет неблокирующий [SRC `sock_cloexec.go:20`]. |
| 38 | `DualStack` (36) | **OUTDATED** | |
| 39 | `tcp_tw_reuse` | **PARTIALLY CORRECT** | [KERN] default 2 (loopback). Ст. 42:218 «tcp_tw_reuse=1» — это глобальный режим. |
| 40 | `ReadHeaderTimeout` Go 1.8 | **VERIFIED** | [API] |
| 40:188 | «таймаут — `conn.Close()` → `read` с `EOF`» | **INCORRECT** | дедлайн даёт `i/o timeout` (`os.ErrDeadlineExceeded`) [SRC `net.go:158–159`]. |
| 40:194 (итог) | «HTTP/2: потеря пакета влияет только на конкретный stream» | **INCORRECT** | для HTTP/2 поверх TCP — HoL на уровне TCP; верно для HTTP/3. Противоречит ст. 10. **Логика**; первоисточник — [RFC 9113/9000]. |
| 41 | «IPVS категорически лучше iptables» | **OPINION/OUTDATED** | [WEB] IPVS deprecated (1.35). |
| 41:185 | «Go TCP не умеет обрабатывать фрагменты» | **INCORRECT** | сборкой занимается ядро. |
| 41:190 | `curl` падает с NXDOMAIN — «Go resolver» | **INCORRECT** | `curl`/`wget` не используют Go. |
| 43 | `errors.Is(err, context.DeadlineExceeded)` для gRPC-ошибок | **INCORRECT** | [EXP] `errors.Is(status.Error(codes.DeadlineExceeded,…), context.DeadlineExceeded)` = `false`; `status.Code(err)` = `DeadlineExceeded`. |
| 43 | `sync.Pool` «в Go 1.21+» | **INCORRECT** | [API go1.3] |
| 44 | «`write` без `memcpy`, если буфер выровнен» | **NOT CHECKED** |
| 44:168 | «`Dial` без `context` гарантированно приведёт к утечке горутин» | **PARTIALLY CORRECT** | утечку может вызвать любой блокирующий `Read/Write`; `Dial` ограничен таймаутом `connect`. |
| 44:172 | «Cancel → TIME_WAIT» | **INCORRECT** | см. B-2. |

---

## 8. Новое: важные проблемы, которых не было ни в Brief, ни в Blind Spot

| ID | Ст. | Находка | Статус | Доказательство |
|---|---|---|---|---|
| **N-1** | 12:296–310 | Семантика `SetKeepAlivePeriod` зависит от версии Go: с Go 1.23 — только `TCP_KEEPIDLE`; до 1.23 — и `KEEPIDLE`, и `KEEPINTVL`. Статья описывает «период keep-alive» безоговорочно. | **CONTEXT-DEPENDENT** | [EXP] `IDLE=30, INTVL` не изменился; [SRC] 1.27 `tcpsock.go:249–257`, go1.22.0 `tcpsockopt_unix.go`. |
| **N-2** | 33:86 | Лишний `"time"` в листинге лимитера (после его правки прошлым фактчеком). | **VERIFIED** | [VET] |
| **N-3** | 11, 13, 14, 37 | Кроме потери автотюнинга: `SetReadBuffer` на **слушающем** сокете наследуется принятыми [EXP]. | **VERIFIED** | см. 2.11 |
| **N-4** | 22:167, 192 | HPACK: «таблица заполняется сервером»; реально каждая сторона кодирует свою таблицу. «LRU» ложно. | **PARTIALLY CORRECT** | [RFC 7541 / SRC `tables.go`] — проверен только FIFO-аспект. |
| **N-5** | 28 | `splice` не в nginx, а в HAProxy (`option splice-auto/request/response`); статья приписывает nginx. | **VERIFIED** | [SRC haproxy `configuration.txt`] |
| **N-6** | 42:154 | DNS-прокси Istio — в `istio-agent`, не в Envoy; по умолчанию выключен. | **PARTIALLY CORRECT** | [WEB] |
| **N-7** | 14:217 vs 11 | Для UDP дефолт `SO_RCVBUF` = `rmem_default` = 212992 [KERN], для TCP — `tcp_rmem[1]` = 131072 [EXP]; статьи не разводят. | **CONTEXT-DEPENDENT** | |

---

## 9. NOT CHECKED: что осталось непроверенным

Всё перечисленное ниже **не** считается подтверждённым.

1. **Medium/Low из Brief § 6–7**, кроме пунктов в разделе 7: примерно 150 из ≈ 190 пунктов Medium и ≈ 150 Low не открывались по первоисточникам. По статьям, где основные пункты не разобраны: **3, 5, 6, 7 (кроме ссылок), 9 (кроме MTU), 13 (кроме формул), 15, 17 (кроме DNS), 19 (кроме отзыва), 24, 26, 29, 30, 31, 32, 34, 36 (кроме eBPF-констант), 37, 38, 41–43**.
2. **Числа (C-NUM)** — не проверялись: «10–20 нс» переключения горутин (ст. 1:161), «15 нс» M, «ndots: +10–50 мс», «−30–50% GC» (18), «−60–70%» (23), «CPU −40–60%» (22), «~0.5% overhead NIC offload» (9), «40+ Mpps», «iptables 1–3 мкс», «XDP 25–50 нс» (36), «connect ускоряет на 10–15%» (14), «NUMA в 3–4 раза», «фрагментация −30–50%» (3), «TCAM < 10 нс» (7), «OSPF 10–50 мс» (7), «~10–20 МБ RAM Linkerd» (42), «2–5 мс на handshake» (19). **Не ошибки по умолчанию, но и не подтверждены.**
3. **Ядро:** версии появления `tcp_rto_min_us`/`TCP_RTO_MIN_US`/`TCP_DELACK_MAX_US`; дефолт `tcp_tw_reuse` в других версиях; route cache (3.6); поведение `connect()` при переполнении neighbour/conntrack (эксперимент невозможен без root).
4. **Chrome Root Program v1.8**; `nhooyr.io/websocket` → `coder/websocket`; gorilla «archived/revived»; Weave Net; Telia→Arelion.
5. **Облачные таймауты:** AWS ALB 60 с; Azure NAT; GCP Cloud NAT 1200 с — по результатам поиска, а не по странице таймаутов (страница не загрузилась).
6. **HTTP/3-детали:** TSO/GRO при QUIC; QUIC-LB и миграция за L4-балансировщиком (B-19); `Alt-Svc`/HTTPS RR (RFC 9460 лишь упомянут); DPLPMTUD.
7. **Envoy/nginx/HAProxy:** «ловушки» (H1 nginx WebSocket defaults), xDS без EDS/ADS.
8. **Go:** `sync/mutex.go` (starvation), `runtime/sema.go`; `gc-guide` (STW, `GOMEMLIMIT`) — *перекрыто знанием API, не чтением страницы*; интервью-утверждения про `runtime.stopm`, `sysmon retake`.
9. **gRPC:** `KeepaliveParams.MinTime`, `connPool`, `MaxCall*MsgSize`, retry service config (gRFC A6), VLQ/varint — не открывал.
10. **Безопасность/L2–L3:** GARP/DAD (ст. 5), VLAN hopping, IPv6 /64-на-под, conntrack «больше не нужен» (8), Smurf/Teardrop, RA Guard.
11. **Эксперименты, не поставленные:** переполнение neighbour-таблицы и conntrack; `ping_group_range` для `icmp.ListenPacket("udp4")`; `IP_BIND_ADDRESS_NO_PORT`; `tcp_tw_reuse` на не-loopback; **кернельный дефолт `tcp_delack*` в старых ядрах**.
12. **Нетронутые дефекты `sources/`**: wikilinks, мелкие опечатки (`epoll_ctl(epoll_ctl,…)` — подтверждено: ст. 15:308), которые не фактические.

---

## 10. Рекомендации для редакторской правки (по приоритету)

1. **Таблица дефолтов Go** одним блоком (ссылки из ст. 1, 10, 12, 20, 21, 40, 44): `TCP_NODELAY=1`; keepalive 15/15/9 (`SetKeepAlivePeriod` — только idle с Go 1.23); `SO_REUSEADDR=1` на listener; `SO_REUSEPORT` — нет; backlog = `somaxconn`; `DefaultMaxIdleConnsPerHost = 2`; нет DNS-кэша, EDNS0 = 1232; `Dialer.Timeout` включает DNS; `http.Client`/`http.Server` без таймаутов; `net.Conn` — конкурентно безопасен.
2. Исправить имена и версии: `wakeG`, `EPOLL_CTL_MOD`, `webPoller`, `epoll_pwait2`, `1024 events`, `Go 1.22+ ET`, `Go 1.16`, `Go 1.21 TLS 1.3`, `Go 1.11` (ст. 16), `Go 1.20 netgo`.
3. Исправить ошибки диагностики L2–L4 (`ENETUNREACH`, `EHOSTUNREACH`, таймаут при DROP).
4. Исправить листинги: компиляция (ст. 2, 20, 30, 31, **33**, 36, 42), `BaseContext`, `FlushInterval`, WebSocket (`r.Context()`, `CheckOrigin`, `SetReadLimit`), идемпотентность, Half-Open, лимитер (очистка карты, порядок), `Transport` (`Clone()`, `Proxy`), `http3`/`XDPOptions`.
5. Исправить TLS (`Handshake()` проверяет имя; `PreferServerCipherSuites`; отзыв — вручную).
6. Исправить формулы: RTO по RFC 6298; `TCP_DELACK_MIN` = 40 мс, `TCP_DELACK_MAX` = 200 мс; Cubic β = 0.7; PTO по RFC 9002; авторы BBR (Van Jacobson).
7. Отметить как дата-зависимое: ingress-nginx, kube-proxy IPVS/nftables, Linkerd, OCSP/сроки сертификатов; ссылаться на RFC 9293/9111/9438/3022.
8. Эпиграфы Эйнштейна — заменить или пометить «приписывается».
