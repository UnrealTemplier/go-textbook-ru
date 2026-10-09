# Модуль 3 «Компьютерные сети и сетевой стек» — независимый фактчек (Sonnet, вторая линия)

Дата: 2026-10-05. Объём: все 44 статьи `sources/3. Компьютерные сети и сетевой стек/` прочитаны целиком. Бриф другого исследователя не использовался и не открывался.

## 0. Как читать отчёт

Формат каждой находки: **раздел → утверждение → проблема → источник/как проверить → приоритет**.

- **H** — фактическая ошибка, которая приведёт читателя к неверному коду, неверной диагностике или неверной модели системы; либо противоречие внутри модуля по ключевому факту.
- **M** — неточность, устаревшее, вводящее в заблуждение упрощение, неработающий/небезопасный пример кода, важное упущение.
- **L** — мелкая неточность, цифра без источника, терминология. Стилистика не включалась.

Метки достоверности: **[✔ src]** — проверено по исходникам Go 1.27.1 (`/usr/local/go/src`); **[✔ exp]** — проверено запуском на Linux 7.2 / Go 1.27.1; **[✔ web]** — проверено поиском (дата 2026-10); **[RFC]** — следует из стандарта; **[проверить]** — вывод по знанию предметной области, нужен источник перед правкой текста.

### 0.1. Что проверено механически (журнал верификации)

| Проверка | Результат |
|---|---|
| `runtime/netpoll_epoll.go`: размер массива событий | `[128]EpollEvent` (в ст.44: «до 1024») [✔ src] |
| `netpollopen`: флаги epoll | `EPOLLIN\|EPOLLOUT\|EPOLLRDHUP\|EPOLLET`, один раз при открытии fd; вызов `EpollWait` (не `epoll_pwait`/`pwait2`) [✔ src] |
| Имена в рантайме | `wakeG` отсутствует; есть `netpollready → netpollgoready → goready`, `netpollblock`; `stopm` в netpoll.go нет [✔ src] |
| TCP_NODELAY по умолчанию | `setNoDelay(fd, true)` в `newTCPConn`; на Dial и Accept `TCP_NODELAY=1` [✔ src, ✔ exp] |
| TCP keepalive по умолчанию | `SO_KEEPALIVE=1`, `TCP_KEEPIDLE=15`, `TCP_KEEPINTVL=15`, `TCP_KEEPCNT=9` на клиентском и принятом соединении [✔ src, ✔ exp] |
| Слушающий сокет `net.Listen("tcp", ":0")` | `AF_INET6`, `IPV6_V6ONLY=0`, `SO_REUSEADDR=1` выставлены автоматически [✔ exp] |
| Backlog | Go читает `/proc/sys/net/core/somaxconn` (на тестовой машине 4096, а не 128) [✔ src, ✔ exp] |
| `net.UDPConn.Connect` | метода нет (есть `SyscallConn`, `ReadMsgUDP`, `WriteMsgUDP`…) [✔ src] |
| UDP: буфер 1500, датаграмма 3000 по `lo` | `ReadFromUDP` вернул n=1500, err=nil — тихое усечение [✔ exp] |
| UDP: запись 1500 байт по `lo` | ошибки `message too long` нет [✔ exp] |
| `http.DefaultMaxIdleConnsPerHost` | `= 2`; `MaxIdleConnsPerHost==0` → 2; `DefaultTransport`: `KeepAlive: 30s`, `MaxIdleConns 100`, `IdleConnTimeout 90s` [✔ src] |
| `http.Server.MaxConns`, `http.ServerMetrics`, `Resolver.LookupContext` | не существуют [✔ src] |
| Канонизация заголовков на сервере | клиент прислал `authorization:` → `r.Header["Authorization"]` находит значение, `r.Header["authorization"]` — пусто [✔ exp] |
| `Hijack` | вызывает `rwc.SetDeadline(zero)` и `abortPendingRead`; `r.Context()` не отменяется при закрытии клиентом (ждали 1,5 с) [✔ src, ✔ exp] |
| `Request` | поле контекста приватное (`ctx`), экспортируемого `Context` нет [✔ src] |
| `ReverseProxy.FlushInterval` | 0 — периодического flush нет; <0 — flush после каждой записи; для стриминга/`ContentLength==-1` — всегда сразу [✔ src] |
| `net.Conn` | «Multiple goroutines may invoke methods on a Conn simultaneously» [✔ src] |
| `Dialer.DualStack` | deprecated («Fast Fallback is enabled by default») [✔ src] |
| `crypto/tls` | при `InsecureSkipVerify=false` hostname проверяется внутри handshake (`DNSName: ServerName`); без ServerName — ошибка; `PreferServerCipherSuites` — Deprecated/ignored; default min TLS 1.2 (если `MinVersion==0`); X25519MLKEM768 по умолчанию с 1.24; 0-RTT только в QUIC-хуках; `KeyLogWriter` есть [✔ src] |
| `x509.Verify` | «doesn't do any revocation checking» [✔ src] |
| `net/netip.Addr` | `struct{addr uint128; z unique.Handle[addrDetail]}`, `Sizeof=24`; методов `IPv4()/IPv6()` нет (`AddrFrom4`, `Unmap`) [✔ src, ✔ exp] |
| DNS-клиент Go | `maxDNSPacketSize = 1232` (EDNS0); кэша ответов нет; `lookupGroup singleflight.Group` [✔ src] |
| Выбор резолвера | по умолчанию «cgo если можно», но на Unix анализируются `resolv.conf`/`nsswitch.conf`; Go-резолвер при распознанной конфигурации, cgo при неизвестном/спецформатах; на darwin `preferCgo` [✔ src] |
| `syscall.Splice` | **существует** на linux/amd64 и arm64 (в первых заметках я ошибочно считал, что его нет — исправлено ниже) [✔ src] |
| `net.ListenIP/DialIP` | raw IP-сокеты есть в stdlib [✔ src] |
| `net/http`: `Protocols`/`UnencryptedHTTP2` | есть (h2c без x/net); HTTP/3 — только внутренние хуки для `x/net/internal/http3`, публичного http3 в Go 1.27.1 нет [✔ src] |
| `GODEBUG` | опции `netpoll` нет (`http2debug`, `http2client`, `http2server` есть) [✔ src] |
| Рантайм | `GOMAXPROCS` учитывает cgroup (`runtime/cgroup_linux.go`) [✔ src] |
| Параметры ядра тестовой машины | `tcp_tw_reuse=2`, `ip_local_port_range=32768 60999` [✔ exp] |
| ingress-nginx | объявлен выводимым из поддержки (март 2026), рекомендация — Gateway API [✔ web] |
| kube-proxy IPVS | deprecated с Kubernetes 1.35, nftables GA в 1.33 [✔ web] |
| Linkerd | с версии 2.15 (2024) Buoyant не публикует open-source stable-релизы (edge + BEL) [✔ web] |
| CA/B SC-081 | 200 дней с 15.03.2026, 100 — с 15.03.2027, 47 — с 15.03.2029 [✔ web] |
| Let's Encrypt OCSP | отключён 06.08.2025, только CRL [✔ web] |
| Chrome Root Program v1.8 | clientAuth EKU: новые sub-CA serverAuth-only с 15.06.2026, листовые — с 15.03.2027 [✔ web] |

Источники (web): kubernetes.io/blog/2026/01/29/ingress-nginx-statement/, letsencrypt.org/2025/08/06/ocsp-service-has-reached-end-of-life, linkerd.io/2024/02/21/announcing-linkerd-2.15/, encryptionconsulting.com/chromes-root-program-policy-v1-8/, bex.co/blog/2026/07/12/kubernetes-135-ipvs-nftables-kube-proxy-migration.

---

## 1. Системные (сквозные) находки — исправлять в первую очередь

Эти ошибки повторяются в нескольких статьях и/или противоречат друг другу внутри модуля. Правка одного места без остальных оставит противоречие.

| ID | Тема | Где встречается | Что неверно | Источник | Приор. |
|---|---|---|---|---|---|
| X1 | **TCP_NODELAY в Go включён по умолчанию** | Ст.10, 11, 37, 44 учат, что Nagle «включён по умолчанию, вызывайте SetNoDelay(true)»; Ст.12, 21 говорят верно | Противоречие внутри модуля; примеры `SetNoDelay(true)` избыточны, «40 мс-ад» в Go воспроизводится только при `SetNoDelay(false)` или у клиентов на других языках | `net/tcpsock.go: setNoDelay(fd,true)`; эксперимент `TCP_NODELAY=1` [✔ src, ✔ exp] | **H** |
| X2 | **TCP keepalive в Go включён по умолчанию (15 с)** | Ст.2 («вечно висит»), 8, 10, 11, 12 («дефолт бесполезен, SetKeepAlive(true) — включение»), 35, 41, 43 («72000 сек») | Для Dial/Listen keepalive уже включён: idle=interval=15 с, count=9 (Linux default). В `DefaultTransport` — 30 с. Нигде не сказано; «2 часа» относится к ядерному дефолту для сокетов без Go | `net/dial.go`; эксперимент [✔ src, ✔ exp] | **H** |
| X3 | **`SO_REUSEADDR` Go ставит сам** | Ст.15 (интервью «включите через syscall.ListenConfig»), 39, 43, 11 | Совет делать то, что рантайм уже делает; `syscall.ListenConfig` не существует (`net.ListenConfig`). Ст.2 корректна | `net/sockopt_linux.go`, эксперимент `SO_REUSEADDR=1` [✔ src, ✔ exp] | **H** |
| X4 | **Дефолты пула `http.Transport`** | Ст.21: «MaxIdleConnsPerHost по умолчанию 100»; Ст.40: «0 → неограниченно»; Ст.21/38/44/30: «=2» | `DefaultMaxIdleConnsPerHost=2`, 0 → 2. Ограничивает только idle, а не одновременные соединения (для этого `MaxConnsPerHost`) | `net/http/transport.go` [✔ src] | **H** |
| X5 | **DNS в Go: кэш, резолвер по умолчанию** | Ст.16 («встроенный кэш на sync.Map»), Ст.1 («Go 1.20+»), Ст.16 («Go 1.11»), Ст.35 («стратегия go = cgo»); Ст.17/44 верно: «кэша нет» | Кэша нет, есть singleflight; EDNS0 1232 вместо «512». Резолвер: pure Go при распознанной конфигурации на Linux; cgo на darwin/при неизвестном; привязка к версиям (1.11/1.20) произвольна | `net/lookup.go`, `net/conf.go`, `net/dnsclient_unix.go` [✔ src] | **H** |
| X6 | **Какая ошибка видна клиенту при проблемах L3/L4** | Ст.5 («neighbour overflow → no route to host»), 7 («нет default route → no route to host»), 8 («conntrack full → no route to host»), 32 («→ ECONNREFUSED или ETIMEDOUT»), 9 (NetworkPolicy → `network unreachable`) | Разные errno перепутаны: нет маршрута → `ENETUNREACH` («network is unreachable»); `EHOSTUNREACH` — ARP-fail/ICMP; тихий DROP (conntrack full, DROP-правило) → только таймаут/`ETIMEDOUT`; `ECONNREFUSED` — RST/ICMP port unreachable; переполнение neighbour-таблицы → `ENOBUFS` | `ip-sysctl`, `connect(2)`, ядро `__neigh_create` [проверить воспроизведением] | **H** |
| X7 | **Как Go-рантайм работает с epoll** | Ст.1 (EPOLL_CTL_MOD на каждый read; `epoll_pwait`; `webPoller`), 38 (`epoll_ctl ADD` после EAGAIN; `epoll_pwait2`; `wakeG`; лимит fd), 37/15/44 («фоновый поток poller»), 43, 44 | Реальность: fd регистрируется один раз при открытии (ET, IN\|OUT\|RDHUP); `EpollWait`; нет выделенного потока (netpoll вызывают `findRunnable`/`sysmon`); имён `wakeG`/`netpollReady` нет | `runtime/netpoll_epoll.go`, `netpoll.go` [✔ src] | **H** |
| X8 | **Ловушка `net.Conn` «не потокобезопасен» vs gorilla/websocket** | Ст.1 (net.Conn «нельзя два Read/Write») и Ст.25 («Conn не потокобезопасен для Read и Write одновременно») | Для `net.Conn` — документированно безопасно (fdMutex сериализует). Для gorilla — наоборот: один читатель + один писатель параллельно разрешены, нельзя несколько писателей | doc `net.Conn` [✔ src]; gorilla docs [проверить] | **H** |
| X9 | **ECMP хэш «по 5-tuple» и «одинаковые маршруты → ECMP»** | Ст.6, 7, 9 | В Linux IPv4 ECMP — один маршрут с несколькими nexthop; дубль → `EEXIST`. Политика хэша по умолчанию — L3 (`fib_multipath_hash_policy=0`) | `ip-sysctl.rst`, `ip-route(8)` [проверить] | **M** |
| X10 | **Выдуманные цифры/параметры** | «10–20 нс», «99.9% 3 DupACK», «+500–1000 мс ndots», «снижение GC 30–50% / 60–70%», «CPU −40–60%», «~0.5% overhead», «40+ Mpps», «sysctl tcp_delack_min/max», `GODEBUG=netpoll=1`, `epoll_pwait2`, `ServerMetrics` | Источников нет; часть параметров не существует | см. по статьям | **M/H** |
| X11 | **Устаревшее/зависящее от даты** | OCSP (19), срок сертификатов (19), clientAuth EKU (19), kube-proxy IPVS (41), ingress-nginx (28/41), Linkerd (42), Weave (41), nhooyr→coder (25), RFC 7234/793 (31/11), Go 1.19 (RLIMIT_NOFILE), Go 1.25 (GOMAXPROCS cgroup), Go 1.24 (PQ-KEX, h2c Protocols) | Нужна «актуальность на дату» в тексте | [✔ web], [✔ src] | **M** |
| X12 | **Wikilinks/кросс-ссылки с неверным адресатом** | Ст.4 (MSS → ст.21/22; PMTUD → ст.39), Ст.7 (CNI → ст.8), Ст.10 (следующая «Handshake, Teardown и флаги» ≠ реальная ст.11), Ст.36→37 обещает qdisc/NAPI — не раскрыто | Навигация ведёт не туда | сверить заголовки | **L** |
| X13 | **Нет сквозного разбора gRPC/HTTP2 + L4-балансировка** | Ст.26, 29, 30 | Главная эксплуатационная ловушка (один долгоживущий connection → дисбаланс; решения headless+`dns:///`+round_robin, xDS, mesh) не описана ни в одной статье | gRPC docs «load balancing» [проверить] | **M** |
| X14 | **Выдуманные внутренности «из исходников»** | Ст.18 (поля `tls.Conn`), 22 (`http2.conn`, `streamMap`, `hpack.Entry`), 24 (`poll.FD` в «quic-go»), 38, 23 | Код/структуры помечены как фрагменты из реализации, но не соответствуют ей | `crypto/tls/conn.go` и др. [✔ src] | **M** |

Правки по приоритету: X1–X8 → затем X6/X9 → X10–X14.

---

## 2. Находки по статьям

Формат строки: **приоритет — раздел — «утверждение» → проблема. Источник.**

### Блок 1. L1–L3 и основы (ст.1–9)

#### Ст.1. Обзор раздела
- **H — «Ловушка 1: net.Conn не потокобезопасен»** → неверно (см. X8). Одновременные `Read`/`Write` и даже несколько `Write` сериализуются `fdMutex`; Write целиком атомарен относительно другого Write. Проблема только прикладная (интерливинг сообщений из нескольких `Write`). Источник: doc `net.Conn` [✔ src].
- **M — sequence diagram: `epoll_ctl(EPOLL_CTL_MOD, fd, EPOLLIN)` после EAGAIN** → см. X7: регистрация один раз, ET, IN\|OUT\|RDHUP; MOD на чтение нет. Противоречит ст.2/15/37. [✔ src]
- **M — «epoll_pwait для безопасной маскировки сигналов», «группирует epoll_wait и kqueue»** → runtime вызывает `EpollWait`; фраза бессмысленна. [✔ src]
- **M — «netpoll для WASM — webPoller»** → такого нет; для wasip1 `netpoll_wasip1.go` (poll_oneoff), для js/wasm сетевого поллера нет; не упомянуты AIX (pollset), Solaris (event ports). Проверить `runtime/netpoll_*.go` [✔ src, список файлов — сверить].
- **L — `netpollInit/netpollReady/netpollBlock`, «netpollBlock вызывает runtime.stopm»** → имена lowercase (`netpollinit/netpollready/netpollblock`); `stopm` из netpoll не вызывается. [✔ src]
- **M — Ловушка 3: «Go 1.20+ netgo по умолчанию на большинстве платформ»; «ndots:0 рекомендуется»** → см. X5. Число лишних запросов зависит от `search` (k8s: 3 суффикса ×(A+AAAA)); рекомендация обычно `ndots:1–2`, FQDN с точкой, NodeLocal DNSCache. cgo-резолвер: getaddrinfo в отдельных потоках (лимит 500). [✔ src]
- **M — Ловушка 2: «без таймаутов соединение висит вечно»** → keepalive (X2) обнаружит мёртвого пира за ≈ 15+9·15 с (Go 1.23: `KeepAliveConfig`). SetDeadline по-прежнему нужен для прикладного idle. [✔ exp]
- **M — «стек потока ОС 2–8 МБ, 10 000 клиентов — мгновенная смерть»** → это виртуальная память (резидентно десятки КБ); NPTL держит 10k+ потоков; Java default Xss = 1 МБ (таблица: «от 2 МБ»), ст.2 пишет «1–8 МБ». Источник: `ulimit -s`, JVM `-Xss`.
- **L — «M освобождается за 15 нс», «переключение горутин 10–20 нс»** → точные числа без источника; типично ≈ 50–200 нс (Gosched/chan ping-pong). Проверить `go test -bench` на целевом железе.
- **L — «TLB flush при переключении потоков»** → для потоков одного процесса адресное пространство то же (flush при смене процесса; PCID смягчает).
- **L — hand-off при блокирующем syscall «моментально»** → P забирается sysmon'ом (retake ~20 мкс–10 мс); лимит потоков `SetMaxThreads` = 10000 → `fatal: thread exhaustion`, а не «лавинообразное падение». [✔ src runtime, проверить]
- **L — BGP/OSPF на L3** → BGP работает поверх TCP/179, OSPF — IP proto 89. **L — «горутина ~2 КБ»** → с Go 1.19 начальный стек адаптивный; на соединение net/http уходит ≫2 КБ (bufio 4+4 КБ, conn).

#### Ст.2. OSI и TCP/IP
- **H — chain `net.Listen`: `socket(AF_INET, SOCK_STREAM, IPPROTO_TCP)`, O_NONBLOCK после** → для `":8080"` создаётся `AF_INET6` dual-stack (`V6ONLY=0`), `SOCK_NONBLOCK|SOCK_CLOEXEC` передаются в `socket()`; backlog = `somaxconn`. [✔ exp, ✔ src] Повторяется на диаграммах ст.8, 15, 37 (`bind 0.0.0.0`).
- **M — «SO_REUSEADDR … двухминутный TIME_WAIT»** → в Linux TIME_WAIT=60 с (`TCP_TIMEWAIT_LEN`); 2 мин — RFC-значение. Ст.10/39 говорят 60 с. [RFC 793/9293, kernel]
- **M — «Zero-Copy: через syscall.Splice; net/http по умолчанию классическое копирование»** → `syscall.Splice` есть (amd64/arm64), но Go сам применяет `sendfile` (io.Copy `*os.File→*TCPConn`, и `http.ServeContent` по plain TCP через `response.ReadFrom`) и `splice` (TCPConn↔TCPConn/UnixConn); по TLS — нет. [✔ src `net/sendfile*.go`, `splice_linux.go`, `server.go:response.ReadFrom`]
- **M — код сервера: `SetReadDeadline` вне цикла** → соединение умирает через 30 с независимо от активности; `io.EOF` логируется как ошибка; `ctx` не используется (комментарий про graceful shutdown вводит в заблуждение); «под капотом вызывается системный вызов net.Listen» — `net.Listen` не syscall.
- **M — «TCP/IP рождён в Bell Labs, DARPA и Berkeley»** → Bell Labs ни при чём (Cerf/Kahn: Stanford/DARPA, BBN; Berkeley — реализация BSD/sockets). Источник: RFC 675/793, история Интернета.
- **L — 5-й уровень OSI = `context`; «валидирует TTL на приёме»** → `context` не session layer; TTL проверяет форвардер (локальная доставка TTL не проверяет). **L — TCP-заголовок «20 байт»** → 20 минимум, практично 32 (timestamps), SYN до 60. **L — «softirq → steal time»** → steal — метрика гипервизора. **L — «O(1) на соединение»** — некорректная нотация. **L — «1000–5000 тактов» смешивает syscall (~100–300 тактов, с KPTI больше) и context switch.**

#### Ст.3. Ethernet
- **M — «Go читает интерфейсы из /sys/class/net/ (или Netlink); Windows — GetAdaptersInfo»** → Linux — netlink (`interface_linux.go`, `NetlinkRIB`); Windows — `GetAdaptersAddresses`. Ст.9 пишет верно («netlink») — противоречие. [✔ src, проверить `interface_windows.go`]
- **M — «tun/tap … чистые IP-пакеты без L2»** → TAP — L2 с MAC; TUN — L3. **M — «GRO и GSO объединяют мелкие кадры в 64 КБ» (подано как checksum offload)** → GRO — приём (coalesce), GSO — передача (отложенная сегментация, обратное направление); TSO/LRO/BIG TCP (>64 КБ) не разведены.
- **M — «io_uring — kernel-bypass»** → не bypass: асинхронный syscall-интерфейс.
- **L — MAC `02:xx:xx:xx:xx:xx` для veth/docker** → `eth_random_addr` ставит только local-бит, первый октет — любой вида `xxxxxx10`; Docker — `02:42:ac:…` из IP. **L — NUMA «в 3–4 раза»** → типично ≈1,3–2×; нужен источник. **L — `SO_BINDTODEVICE` требует CAP_NET_RAW; через x/net/ipv4** → с Linux 5.7 не требует, если сокет ещё не привязан; в x/net/ipv4 такой опции нет (идиома — `ListenConfig.Control` + `unix.SetsockoptString`); раздел содержит только комментарий вместо кода. **L — «ECONNREFUSED из-за FDB exhaustion»** → ECONNREFUSED — RST (L4). **L — «фрагментация при MTU 1450 → −30–50%»** — без источника; VXLAN 50 Б для IPv4 underlay (70 для IPv6). **L — VLAN: кадр 1522, payload 1500 — не упомянуто. «DNS-имена интерфейсов» — бессмыслица.**

#### Ст.4. IP
- **M — Linux receive path (диаграмма/список): TTL декрементируется/проверяется на приёме до маршрутизации; netfilter PREROUTING после route lookup** → TTL проверяют/декрементируют в `ip_forward`; `NF_INET_PRE_ROUTING` выполняется ДО routing decision (ст.32 нарисована верно — противоречие). Источник: `net/ipv4/ip_input.c`, `ip_forward.c`.
- **M — «опции IP → cache line split TCP-портов»** → опции IP выравниваются до 4 байт; выравнивание определяется `NET_IP_ALIGN`/sk_buff, а не опциями; «20 байт + начало TCP в одной кэш-линии гарантированно» неверно.
- **M — «Smurf эксплуатировал баги сборки фрагментов»** → Smurf — ICMP echo на broadcast (амплификация). Фрагментационные: Teardrop, Ping of Death.
- **M — `netip.Addr` «хранит [4]byte или [16]byte»; методы `IPv4()/IPv6()/Unmap()` за O(1)** → `uint128 + unique.Handle` (24 байта), IPv4 хранится как `::ffff:`; `IPv4()/IPv6()` нет (`AddrFrom4/16`, `As4/As16`, `Unmap`); «zero-alloc» нарушается для IPv6 zone. [✔ src, ✔ exp]
- **M — `WriteMsgUDP/syscall.WriteMsgUDP с MSG_MORE… взаимодействует с адаптером напрямую`** → `syscall.WriteMsgUDP` не существует; `MSG_MORE` — corking; к NIC/`bufio` отношения нет. **M — Teredo/6to4 как актуальные** → deprecated (RFC 7526)/вымерли; актуальны 6rd, NAT64/464XLAT, DS-Lite. **M — «маршрутизаторы вынуждены фрагментировать»** → в IPv6 маршрутизаторы не фрагментируют (PMTUD, ICMPv6 PTB, min MTU 1280); в IPv4 при DF — drop + ICMP.
- **L — «TTL никогда не измерялся в секундах»** → RFC 791 определяет секунды, на практике хопы (RFC 1812). **L — LaTeX повреждён escape-последовательностями** (`pprox`, `	imes`) в трёх формулах. **L — wikilinks** (X12). **L — «IPv4 исчерпан в 2011»** — пул IANA; RIPE 2012, ARIN 2015.

#### Ст.5. ARP/NDP
- **M — «IPv4 использует таблицы arp_tables»** → `arp_tables` — фильтр arptables; ARP — `net/ipv4/arp.c` + `net/core/neighbour.c`; NDP — `net/ipv6/ndisc.c`.
- **M — «x/net/ipv4,ipv6 дают интерфейс к RTM_GETNEIGH»; «getifaddrs для таблицы соседей»** → x/net/ipv4/ipv6 — опции сокетов/multicast; netlink — `x/sys/unix`, `vishvananda/netlink`; `getifaddrs` — адреса интерфейсов.
- **M — «neighbor table overflow → fatal error; Dial падает с no route to host»** → X6: это printk-warning, `connect` получает `ENOBUFS`; `EHOSTUNREACH` — при FAILED. Пороги даны только для IPv4 (`net.ipv6.neigh.default.gc_thresh*` пропущены; дефолты 128/512/1024 не названы).
- **M — «connect(): ядро переводит горутину в ожидание ARP; завершается после ARP»** → Go делает non-blocking connect (`EINPROGRESS`); SYN ждёт в `arp_queue`; `Dial` возвращается после TCP-handshake; ядро о горутинах не знает; `syscall.Conn` — интерфейс, не «дескриптор».
- **M — GARP «обнаружение конфликтов IP»; «коммутаторы обновляют IP→MAC»** → для DAD IPv4 — ARP Probe (RFC 5227); коммутатор хранит MAC→порт; VRRP — виртуальный MAC `00:00:5E:00:01:VRID`, меняется порт.
- **L — `gc_stale_time`, `delay_first_probe_time`, «NDP Guard» (стандартный термин — RA Guard, RFC 6105), `arp_ignore/arp_announce/arp_accept/rp_filter` не упомянуты.**

#### Ст.6. Маршрутизация
- **M — «одинаковые prefix+metric → ECMP по 5-tuple»** → X9. **M — route cache «до 2.6.38 … с 3.6 ликвидирован»** → внутреннее противоречие (удалён в 3.6); «горутины читают FIB без локов» — про ядро.
- **L — два default с metric 100/200 «при падении переключится»** → только при исчезновении маршрута (carrier loss); при живом линке нужен мониторинг/BFD. **L — асимметрия: «клиент шлёт RST»** → типично rp_filter/uRPF; клиент RST на корректный SYN-ACK не шлёт. **L — пример `10.0.1.50/32 via 127.0.0.1 dev lo`** нереалистичен; `ip rule`/таблицы `local,main,default` не описаны. **L — «32 итерации» vs LC-trie; «BGP full view > 950k»** — IPv4 уже >1,0M. **L — `SO_BINDTODEVICE`: CAP_NET_RAW до 5.7; `IP_TRANSPARENT` требует CAP_NET_ADMIN/TPROXY/ip rule; нет кода FREEBIND/TRANSPARENT.**

#### Ст.7. RIP/OSPF/BGP
- **H — интервью: «пропал default route → `connect: no route to host`»** → X6: `ENETUNREACH` («network is unreachable»). 
- **M — «OSPF сходится за 10–50 мс без потери TCP»** → типично сотни мс–секунды (SPF/LSA throttle, hello/dead 10/40 с без BFD); 10–50 мс — BFD+tuning/IP-FRR; пакеты теряются, TCP переживает ретрансмитами.
- **M — «ядро выбирает по Administrative Distance»** → в ядре Linux AD нет (metric/proto); AD — Cisco-понятие (FRR/zebra, BIRD — preference).
- **M — «tc/iproute2 делегируют правила в TCAM NIC; TCAM <10 нс; SmartNIC LPM»** → FIB-TCAM — в ASIC коммутатора (Linux switchdev, флаг `offload`); tc-flower offload — flow-правила, не FIB. **M — «группируйте IP в CIDR, чтобы fib_trie был в L1 и net.Dial быстрее»** → один lookup на connect, потом `sk_dst_cache`; на хосте десятки маршрутов — совет бессмысленен.
- **M — интервью: `SO_BINDTODEVICE через unix.Bind / netlink`** → это `setsockopt`. **M — «в поде `ip route` покажет loopback 127.0.0.1/8 и 169.254.169.254/32»** → 127/8 в таблице `local`; 169.254.169.254 не универсален (Calico: default via 169.254.1.1).
- **L — Telia→Arelion (2022); «OSPF — подход Bell Labs»; метрика RIP connected=1 (RFC 2453), диаграмма внутренне непоследовательна; OSPF cost при reference-bw 100 Mbps — ловушка «все ≥100M = 1»; нет IS-IS/EIGRP/DR-BDR/areas/RFC 7938/RPKI; «Calico/Cilium построены на BGP» — BGP опционален (Cilium по умолчанию VXLAN/Geneve); GoBGP/MetalLB не упомянуты.**

#### Ст.8. NAT
- **H — «conntrack full → `dial tcp: connect: no route to host`», «DROP с пометкой NO ROUTE»** → X6: тихий drop → `i/o timeout` (SYN-ретрансмиты до ≈127 с, `tcp_syn_retries=6`); «poller ждёт бесконечно» — нет. Для локального UDP — `EPERM`.
- **M — IPv6: «каждому поду /64»; «conntrack больше не нужен»; «port exhaustion растворяется»** → под получает /128 из node-podCIDR /64; stateful firewall и kube-proxy используют conntrack; исчерпание определяется 4-tuple и снимается только множеством src-адресов; для IPv4-интернета нужны NAT64/egress-only gateway.
- **M — «AWS NAT GW и GCP Cloud NAT режут до 350 с»** → 350 с — AWS (при последующем пакете шлёт RST); GCP Cloud NAT — по умолчанию 1200 с. 
- **L — RFC 1631 (obsoleted RFC 3022), CGNAT/RFC 6598; «ISP гарантированно отбрасывают RFC 1918»; «Linux выбирает порт 12345» (сначала сохраняет исходный); checksum обновляется инкрементально; IMDSv2; `bind 0.0.0.0` (на деле `[::]`), «маска 0.0.0.0»; `netip.IsPrivate` включает ULA; `net.Dialer{KeepAlive:15s}` — «включение» (дефолт уже 15 с).**

#### Ст.9. VLAN/VXLAN
- **H — «тег 802.1Q уменьшает MTU до 1496; кадр 1518→1522; ОС должна снизить MTU»** → 802.3ac (1998) допускает 1522; `eth0.10` на Linux имеет MTU 1500. Далее «1426» строится на ошибке. [RFC/IEEE 802.3ac]
- **M — «UDP 1500 байт → `message too long` при Write»** → безусловно неверно: EMSGSIZE только при DF (`IP_PMTUDISC_DO`) или >65507; по умолчанию фрагментация. [✔ exp: запись по `lo` без ошибки]
- **M — «inter-VLAN routing идёт через CPU/ядро, +мкс»** → L3-коммутатор маршрутизирует в ASIC; CPU — исключения. **M — «dev физически не может попасть в prod на L2»** → VLAN hopping (DTP, double tagging, native VLAN). **M — интервью: «UDP исключает дедлоки в сетевом стеке ядра»** → выдумка. **M — «NetworkPolicy drop → ECONNREFUSED/network unreachable; sidecar → 503»** → X6; Envoy RBAC deny → 403.
- **L — «MTU-black hole → рост TIME_WAIT»** (на деле ESTABLISHED+ретрансмиты); «NIC offload ~0.5% CPU»; «8472 — ранние реализации» (текущий дефолт ядра/Flannel/Cilium; Calico — 4789); `flannel.1` — виртуальное vxlan-устройство, не физический интерфейс; ст.9 «netlink» vs ст.3 «sysfs» (X14).

### Блок 2. Транспорт TCP/UDP, порты (ст.10–15)

#### Ст.10. TCP
- **H — Nagle/NODELAY** → X1 (код `SetNoDelay(true)` избыточен).
- **M — «SO_REUSEADDR/SO_REUSEPORT решают port exhaustion клиента»** → относятся к `bind()` сервера; для исходящих — `tcp_tw_reuse` (default 2, 1 — глобально), диапазон портов, `IP_BIND_ADDRESS_NO_PORT`, несколько src-IP, пулы; `tcp_tw_recycle` удалён в 4.12 (не упомянуто).
- **M — «изменение snd_una/… требует LOCK CMPXCHG»; «tcp_sock в include/net/tcp.h»** → поля меняются под socket lock; структура в `include/linux/tcp.h`.
- **M — «фоновый тред netpoller в epoll_wait»** → X7. **L — «9 бит флагов» vs 8 на схеме (NS historic, RFC 8311); SetReadDeadline «переводит сокет в состояние ошибки» (можно продлить); «no duplicates благодаря cumulative ACK» (по seq); ссылка на ст.11 не соответствует; X2.**

#### Ст.11. Handshake/Flow/Congestion
- **H — `SetReadBuffer(1 МБ)` «расширяет окно Flow Control»** → `SO_RCVBUF/SO_SNDBUF` отключают autotuning (`tcp_rmem/tcp_wmem`) и клампятся `rmem_max/wmem_max`; «Window = Buffer − Used» неверно (объявляется часть, `tcp_adv_win_scale`/`scaling_ratio`). [ip-sysctl]
- **M — «клиент пишет быстрее сервера → ECONNRESET»** → при живом пире Linux ждёт бесконечно (persist timer); без ответа — `ETIMEDOUT`; нужен `SetWriteDeadline`.
- **M — SYN flood: «tcp_synack_timer»; лог «possible SYN flooding … Dropping request»** → такого sysctl нет (`tcp_synack_retries`, `tcp_max_syn_backlog`); актуальный лог «…Sending cookies. Check SNMP counters.»; ограничения SYN cookies, accept-queue overflow (`ListenOverflows/Drops`, `tcp_abort_on_overflow`) не раскрыты.
- **L — RFC 793 → RFC 9293; «удвоение буфера — BSD/Go»** (удваивает Linux, `socket(7)`); `conn.(*net.TCPConn)` без проверки; «persist timer 5–60 с» (RTO→120 с); tcp_sock в `net/tcp.h` (X14); Reno vs CUBIC/PRR.

#### Ст.12. Retransmission/Keepalive/Nagle/Delayed ACK
- **H — `RTO = SRTT + max(K, DELAYED_ACK_TIME)×4`, K=4·RTTVAR** → RFC 6298: `RTO = SRTT + max(G, 4·RTTVAR)`; Linux ≈ SRTT+4·RTTVAR, min 200 мс. [RFC 6298]
- **H — «TCP_DELACK_MAX≈40 мс», `sysctl tcp_delack_min/max`, `tcp_rto_min` (sysctl), `TCP_RTO_MIN` как опция сокета** → в mainline таких sysctl нет; `TCP_DELACK_MIN=40 мс`, `TCP_DELACK_MAX=200 мс`, ATO адаптивный, quickack; `rto_min` — per-route (`ip route … rto_min`), у сокета — `TCP_USER_TIMEOUT` (не упомянут). [kernel `include/net/tcp.h`, `ip-route(8)`]
- **H — «дефолтный keepalive бесполезен… SetKeepAlive(true)… с Go 1.16 SetKeepAlivePeriod»** → X2; `SetKeepAlivePeriod` с Go 1.2; ставит и IDLE, и INTVL, но не CNT; `KeepAliveConfig` — Go 1.23. [✔ src]
- **M — «3 DupACK ⇒ >99.9% потеря»** → число выдумано; Linux — SACK + RACK-TLP (RFC 8985), adaptive reordering, PRR (RFC 6937), TLP/F-RTO не упомянуты. **M — `tcp_retries2=15` «13–30 мин»** → ≈ 924,6 с (≈15 мин). **M — совет `errors.Is(err, context.Canceled)` для retry** → отмена не повторяется. 
- **L — «четыре условия Nagle», TCP_CORK/autocorking; противоречие со ст.10/11; NAT-таймауты 5–15 мин (AWS 350 с, GCP 1200 с, Azure 4 мин); SO_REUSEPORT/BINDTODEVICE в разделе про пулы — не связаны.**

#### Ст.13. Reno/Cubic/BBR
- **H — Cubic: «β≈0.2, окно −20%, сохраняет 80%», `K=∛(W·β/C)`** → RFC 8312/9438: β_cubic=0.7 (cwnd→70%), `K=∛(W_max(1−β)/C)`, C=0.4; Linux `BETA=717/1024`. TCP-friendly region, fast convergence, HyStart не упомянуты; RFC 8312 obsoleted RFC 9438. [RFC 9438]
- **M — «BBR требует fq»; «BBR v2/v3 в таблице/sysctl»** → с 4.13 есть внутренний TCP pacing (fq желателен); в mainline только BBRv1. **M — авторы «…Кевин Якобсон»** → Van Jacobson; «принцип неопределённости Клейнрока» — нет такого. 
- **M — «cwnd исчерпан → write(2) возвращает EAGAIN»** → EAGAIN при полном sndbuf; `EPOLLOUT` зависит от `sk_stream_wspace`, не от cwnd. **M — «BBR: нулевая чувствительность к потерям; P99 в разы; Cubic 1–2 с в трансконтинентальных»** → BBRv1 игнорирует потери (высокий retransmit при мелких буферах, несправедлив к Cubic); внутри ДЦ смысла нет (DCTCP/ECN).
- **L — `cubic_ack` (в ядре `bictcp_*`); `ReadBufferSize/WriteBufferSize` у Transport — Go 1.13, не 1.19; ECN/DCTCP/`ss -ti` не упомянуты.**

#### Ст.14. UDP
- **H — `conn.Connect(addr)` на UDP-сокете** → у `UDPConn` нет `Connect` (`DialUDP`). [✔ src]
- **H — «буфер 1500 гарантирует чтение целого пакета»** → датаграмма до 65507 Б; молча усекается, `ReadFromUDP` err=nil (флаги `MSG_TRUNC` теряются; нужен `ReadMsgUDP`). [✔ exp]
- **M — `SetReadBuffer(4 МБ)` «критично»** → клампится `rmem_max` (по умолчанию 212992 → ≈416 КБ); нужен sysctl или `SO_RCVBUFFORCE` (CAP_NET_ADMIN); проверять через getsockopt.
- **M — «Prometheus Pushgateway — UDP»** → HTTP/TCP; DTLS как пример надёжности — ретрансмитит только handshake.
- **L — «connect ускоряет на 10–15%»; `struct udp_sock` в `include/linux/udp.h`; Go не считает checksum (ядро/NIC); STW GC «долгая пауза»; опущены SO_REUSEPORT, recvmmsg/sendmmsg (`ipv4.PacketConn.ReadBatch`), UDP GSO/GRO, IP_PKTINFO, amplification/spoofing (ст.33); цитаты Эйнштейна/Кнута апокрифичны/не дословны.**

#### Ст.15. Порты, сокеты
- **H — интервью: «SO_REUSEADDR через `syscall.ListenConfig`»** → X3.
- **H — backlog: «listen(5) — ядро пропустит до somaxconn»; «somaxconn по умолчанию 128»; `listen(backlog=128)` в диаграмме** → очередь = min(backlog, somaxconn); дефолт 128 до 5.4, с 5.4 — 4096 (на тестовой машине 4096); Go читает somaxconn. [✔ src, ✔ exp]
- **M — «эфемерные порты 49152–65535»** → рекомендация IANA; Linux — 32768–60999 (ст.10/39 верно). **M — `bind 0.0.0.0` vs dual-stack в той же статье** (X7/ст.2). **M — «фоновый поток epoll_wait»; опечатка `epoll_ctl(epoll_ctl,…)`**.
- **L — `sk_send_queue` (в ядре `sk_write_queue` + `tcp_rtx_queue`); `close()` с непрочитанными данными шлёт RST; идиома `SetLinger(0)`; `ip_unprivileged_port_start`.**

### Блок 3. DNS, TLS, PKI (ст.16–19)

#### Ст.16. DNS
- **H — «встроенный кэш (sync.Map)»; интервью «Go использует DNS Caching»** → X5: кэша нет, есть `singleflight`. Ст.17 корректна.
- **H — «UDP-ответ ≤512 байт, TC при >512»** → EDNS0 (RFC 6891), Go шлёт OPT с 1232; TC по размеру EDNS; DNSSEC-ответы >512 штатно; RFC 7766. [✔ src `dnsclient_unix.go`]
- **H — «macOS — SCDynamicStore; Windows — реестр через dnscfg»** → Unix: `resolv.conf` (перечитывается ≈ раз в 5 с); macOS по умолчанию cgo/системный; Windows — Win32 API. [✔ src `conf.go`, проверить `lookup_windows.go`]
- **M — «Go 1.11 по умолчанию pure-Go на всех Unix»** → X5. **M — интервью «DialContext висит дольше дедлайна»** → объяснение размытое; реально — таймауты `resolv.conf` (timeout×attempts×серверы×search×A+AAAA). **M — пример: захардкожен `8.8.8.8:53`, «никогда не используйте DefaultResolver»** → ломает split-horizon/CoreDNS/air-gap. **M — ndots: «+10–50 мс»** → цифра без источника; не названы 5-секундные таймауты из-за UDP-conntrack race, NodeLocal DNSCache, `single-request`.
- **L — «0 RTT» UDP; Route 53 «рекурсивный»; нет RCODE/AD/CD; `grpc.Dial` (passthrough) vs `NewClient` (dns); HOSTS.TXT — SRI-NIC (Фейнлер), цитата вымышленная.**

#### Ст.17. DNS под капотом
- **H — противоречия с ст.16 (кэш; 512 vs EDNS)** → привести к ст.17 + 1232 (не 4096).
- **M — Dial всегда `"udp"`** → ломает TC-fallback (рантайм вызывает Dial с `network="tcp"`); использовать параметр. **M — «CNAME-цепочки убивают latency»** → цепочку разворачивает рекурсор; клиент — один round-trip, задержка на cache miss. **M — «cgo на Alpine аварийно/утечки»** → собирается; не запускается бинарник из glibc-сборки; реальная разница musl (search/ndots, TCP-fallback <1.2.4); distroless/base содержит glibc. **M — ndots `api` → 5 запросов** → при 3 search `api.default.svc…` разрешается с первого раза; пример ст.16 корректнее.
- **L — «13 anycast-узлов»** (13 идентичностей, >1500 инстансов); порядок QTYPE/QCLASS; «MX сортирует резолвер»; нет SOA/CAA/DNSKEY/SVCB-HTTPS (RFC 9460), negative caching (RFC 2308), serve-stale (RFC 8767); `lookupWithTimeout` течёт горутиной.

#### Ст.18. TLS
- **H — интервью: «Handshake не проверяет домен; нужен VerifyHostname»** → при `InsecureSkipVerify=false` имя проверяется в handshake; без ServerName — ошибка. [✔ src] Ручной VerifyHostname нужен лишь при `InsecureSkipVerify`.
- **H — «Go 1.21+: TLS 1.3 по умолчанию»** → TLS 1.3 — с Go 1.13; min=TLS 1.2 (клиент 1.18, сервер 1.22). [✔ src] Не упомянуты X25519MLKEM768 (по умолчанию с 1.24), ECH, отсутствие 0-RTT поверх TCP, тикеты и ротация ключей.
- **M — внутренности `tls.Conn` (`handshakeStatus`, `rd.buf` кольцевой, `gcmCipher`)** → реально `isHandshakeComplete atomic.Bool`, `rawInput/input/hand`, halfConn `in/out`. [✔ src] «sync.Pool −30–50% GC» без источника. **M — `PreferServerCipherSuites:true`** → ignored. **M — «Close нужен, иначе fd зависнет навсегда»** → у netFD есть finalizer (недетерминированно). 
- **L — «GOMAXPROCS по физическим ядрам»** → Go ≥1.25 cgroup-aware [✔ src]; SNI открыт без ECH; TLS 1.2 resumption/False Start; сравнения с PHP/Java декоративны.

#### Ст.19. PKI, mTLS
- **H — «валидация включает CRL/OCSP»; «отзыв — через x509.VerifyOptions»** → `x509.Verify` отзыв не проверяет [✔ src]; нужно `VerifyPeerCertificate` + `x/crypto/ocsp`, `x509.ParseRevocationList`.
- **H — OCSP stapling как стандарт; пропущены сроки/EKU** → Let's Encrypt выключил OCSP (06.08.2025), SC-081 (200/100/47 дней), Chrome v1.8 (clientAuth EKU) [✔ web] — для mTLS с публичными CA критично.
- **M — «при CGO_ENABLED=1 крипто делегируется системным библиотекам»** → нет (только BoringCrypto/FIPS-сборки). **M — «ClientSessionCache → 0-RTT/1-RTT без асимметрии»** → Go не поддерживает 0-RTT; PSK_DHE оставляет ECDHE; «2–5 мс на handshake» завышено.
- **L — `PreferServerCipherSuites`; один Config как клиентский и серверный; тип `CertificateSignatureAlgorithm` выдуман; `openssl x509 -text` не проверяет цепочку (нужен `openssl verify`/`s_client`); путь trust store только Debian-like; SPIFFE/SPIRE и ротация не раскрыты.**

### Блок 4. HTTP/1.1, HTTP/2, QUIC, потоки (ст.20–26)

#### Ст.20. HTTP/1.1
- **H — интервью: «`authorization:` → `r.Header["Authorization"]` вернёт nil»** → наоборот: сервер канонизирует входящие ключи; промахивается обращение по неканоническому ключу. [✔ exp]
- **M — «`Header.Get` вернёт значение, склеенное запятой»** → вернёт первое, без склейки. **M — поле `Request.Context`** → экспортируемого нет (приватное `ctx`). **M — «MaxBytesReader — защита от Slowloris»** → лимит объёма; Slowloris — `ReadHeaderTimeout`. **M — «пул горутин; Request на connection»** → горутина на соединение, Request на запрос. **M — «нет interning; парсер — FSM»** → textproto интернирует частые ключи, `ReadMIMEHeader` — одна аллокация; не FSM.
- **L — фрагмент в Request-URI; формы request-target; CL+TE (smuggling); `Server:` не отправляется net/http по умолчанию; JSON через `Fprintf("%s")` без экранирования; RFC 2068/2616 история.**

#### Ст.21. HTTP/1.1 под капотом
- **H — «MaxIdleConnsPerHost по умолчанию 100 … 100 параллельных соединений»; интервью «открывает до 100»** → X4. 
- **H — «Close() возвращает соединение в пул»** → только если тело вычитано до EOF; иначе соединение закрывается (doc `Response.Body`). Главная ловушка клиента не описана.
- **M — `Set("Transfer-Encoding","chunked")` «автоформатирует»** → не нужно; Go выбирает chunked сам (нет CL и >2 КБ буфера или Flush); в h2 заголовок недопустим. **M — «Nagle 200–400 мс; NODELAY на keep-alive»** → X1. **M — «TCP keepalive 2 часа»** → X2; гонка закрытия idle (EOF), `IdleConnTimeout` клиента < keepalive сервера/LB.
- **L — `Max-Forwards`; chunked для WebSocket; `Content-MD5`; «Bell Labs»; pipelining в Go (сервер обрабатывает последовательно).**

#### Ст.22. HTTP/2
- **H — Rapid Reset: «защита — MaxHeaderListSize, ReadHeaderBufferSize»** → не митигируют; фикс — патч (Go 1.20.10/1.21.3, x/net 0.17.0, учёт живых обработчиков); не упомянут CONTINUATION Flood (CVE-2023-45288).
- **M — внутренности `http2.conn/framer/streamMap/hpack.Entry`; «динамическая таблица — список с LRU»** → `serverConn`, `Framer`, `streams map`; таблица — слайс, FIFO. **M — «PRIORITY — дерево приоритетов»** → deprecated в RFC 9113 (→ RFC 9218). **M — «h2c через x/net/http2/h2c; h2 только с TLS»** → Go 1.24+: `Protocols.UnencryptedHTTP2` [✔ src]; кастомный `DialContext/TLSClientConfig` отключает авто-h2 (нужен `ForceAttemptHTTP2`).
- **L — «Length 24 бита — 4 КБ» (16 КБ); чётные stream ID шлёт сервер; ALPN в EncryptedExtensions; «−40–60% CPU».**

#### Ст.23. HTTP/3 и QUIC
- **H — «`golang.org/x/net/http3`»** → публичного пакета нет (в Go 1.27.1 — внутренние хуки `x/net/internal/http3`); `quic-go/http3`. [✔ src]
- **H — «quic-go: Cubic и BBR; по умолчанию BBRv2» (ст.24)** → у quic-go публично CUBIC/NewReno; BBR — [проверить по `quic-go/internal/congestion`]; в RFC 9002 по умолчанию NewReno.
- **H — «HTTP/2-фреймы по QUIC-streams»; нет QPACK** → HTTP/3 имеет собственные фреймы (RFC 9114) и QPACK (RFC 9204).
- **H — сервер только h3 без Alt-Svc/HTTPS RR/TCP-fallback** → браузеры узнают о h3 из `Alt-Svc`/RFC 9460.
- **M — «0-RTT: сервер валидирует после handshake»** → сервер обрабатывает сразу (replay). **M — «CID 64 бита»; миграция** → 0–20 байт, PATH_CHALLENGE/RESPONSE, NEW_CONNECTION_ID; QUIC-LB. **M — «hole punching встроен в quic-go (ICE/STUN)»** → нет. **M — «CC только sysctl»** → `TCP_CONGESTION` per-socket (противоречит ст.12). **M — PMTU/фрагментация** → DF, Initial ≥1200, DPLPMTUD (RFC 8899).
- **L — выдуманные числа/метрики (`sync.Pool −60–70%`, «2–5 мкс», `http3_server_round_trip_duration_seconds`), `MSG_DONTWAIT`, `http3.Client`.**

#### Ст.24. Deep dive QUIC
- **H — «PTO = RTT + 4·SmoothedRTT + MaxAckDelay»** → RFC 9002: `smoothed_rtt + max(4·rttvar, kGranularity) + max_ack_delay`, backoff.
- **H — «теряем TSO/GRO/checksum offload»; «TCP BBR обучен на роутерах»** → UDP GSO (4.18)/GRO (5.0) используются реализациями; UDP checksum offload работает.
- **H — «ждёт WINDOW_UPDATE»** → в QUIC `MAX_DATA/MAX_STREAM_DATA/MAX_STREAMS/*_BLOCKED`.
- **M — ASCII Long/Short Header** (`0xQUIC`; в short нет Length; DCID без длины) → RFC 9000 §17. **M — «ACK кодирует потерянные»; «ECN-Echo»** → ACK ranges — полученные; ECT/CE + ACK_ECN. **M — «после миграции теряются ключи»** → нет. **M — код `poll.FD` «из quic-go»; буферы 32 КБ–1 МБ** → не из quic-go (≤≈1452 Б). **M — «Gen0 GC», `asyncpreemptoff` «на критичных путях»** → у Go GC нет поколений; опция процессная.
- **L — Stream ID биты; ACK Frequency — draft; верно: новый PN, PN spaces, kPacketThreshold=3.**

#### Ст.25. WebSocket/SSE
- **H — «ReadMessage+WriteMessage параллельно небезопасны»** → X8.
- **H — код: `r.Context().Done()` «клиент отключился»** → после Hijack ctx не отменяется [✔ exp]; нужны `SetReadDeadline`+`PongHandler` либо завершение по ошибке читателя.
- **H — «SSE строится на HTTP Upgrade»** → обычный HTTP-ответ; нет лимита 6 соединений HTTP/1.1, ограничений EventSource (GET, без заголовков).
- **M — «Go проверяет заголовок и подтверждает 101»** → библиотека; после Hijack сбрасываются дедлайны [✔ src], `Shutdown` не ждёт hijacked, h2 без Hijacker. **M — «nginx WebSocket настроен по умолчанию»** → нужны `proxy_http_version 1.1`, `Upgrade/Connection`, `proxy_read_timeout`. **M — «rmem_max → соединение разорвётся»** → нет (zero window). **M — `WriteTimeout` убивает SSE** → `ResponseController.SetWriteDeadline`.
- **L — CVE-2011-7008 не подтверждён; сервер MUST NOT маскировать; «32-битная длина»; nhooyr→coder; gorilla (2022 архив/2023 возрождена); Redis Pub/Sub at-most-once.**

#### Ст.26. gRPC
- **H — «context → GOAWAY или CANCEL фреймы»** → `RST_STREAM(CANCEL)`; дедлайн — `grpc-timeout`, не упомянут; `te: trailers`, Trailers-Only.
- **H — «MaxCall{Recv,Send}MsgSize — flow control»; «WithInitialConnWindowSize → несколько соединений»** → лимиты размера (4 МБ); окна — `InitialWindowSize/InitialConnWindowSize`, BDP-estimator.
- **M — «connPool; KeepaliveParams с MinTime»** → нет connPool; `MinTime` — серверный `EnforcementPolicy` (GOAWAY too_many_pings). **M — «собственный `net/http2`»** → `internal/transport` на `x/net/http2`. **M — «VLQ»; «zero-allocation»; «reflection в Java/C#»** → base-128 varint (LEB128), zigzag; protobuf-go — table-driven. **M — «TLS по умолчанию»; `WithBlock` deprecated** → `grpc.NewClient`.
- **L — метрики `_total`; proto3/optional/Editions; X13.**

### Блок 5. Прокси, балансировка, CDN, защита (ст.27–33)

#### Ст.27. Прокси
- **H — «FlushInterval=0 — немедленный flush; >0 буферизует»** → перевёрнуто [✔ src] (0 — нет периодического; <0 — после каждой записи; стриминг — сразу).
- **M — «тело ответа в отдельной горутине»; «Go 1.18+ chunked»** → в одной горутине (отдельные — для upgrade/`maxLatencyWriter`); стриминг всегда. **M — «Go 1.11+ h2 к бэкендам; HOL устранён»** → h2 клиент с 1.6, только https; кастомный dial отключает; TCP HOL остаётся. **M — интервью про MaxIdleConnsPerHost** → причина — малое значение (X4). **M — XFF/Forwarded, hop-by-hop, PROXY protocol, smuggling, ретраи не упомянуты.**
- **L — «Nginx — C++/Rust»; «Lua/WSI»; `ReadHeaderTimeout` у ReverseProxy.**

#### Ст.28. nginx/Envoy/HAProxy
- **H — «nginx использует sendfile и splice»; «splice для aio и tcp_nopush»** → splice в nginx нет; sendfile не при TLS (кроме kTLS) и не при проксировании.
- **H — «HAProxy: один поток; TCP-логика в user-space (окно перегрузки, ACK)»** → многопоточен с 1.8, `nbthread`=CPU; TCP — ядерный.
- **M — «Envoy — стандарт для Istio, Linkerd»** → Linkerd — свой Rust-прокси (ст.42 верно). **M — xDS без EDS/ADS.** **M — «port exhaustion у Go-клиента»** → у nginx→upstream; `keepalive`, `proxy_http_version 1.1`.
- **L — `open_file_cache`; Pingora/Caddy/Traefik; ingress-nginx EOL; QAT/Nitro.**

#### Ст.29. Балансировка
- **M — Gotcha про LC и keep-alive** → логика перевёрнута (проблема — долгоживущие соединения); `least_request`/P2C. **M — graceful shutdown без preStop/задержки endpoints; «broken pipe и panic»** → panic не будет. **M — «IdleConnTimeout 90 с» в серверном разделе** → `IdleTimeout`. **L — «L4 не умеет TLS-termination»; DSR/PROXY/IPVS/Maglev не упомянуты; X13.**

#### Ст.30. Service Discovery
- **H — «ExternalIPs или headless с `publishNotReadyAddresses:true`»** → вредный совет (неготовые поды в DNS).
- **H — «svc.default.svc.cluster.local возвращает список IP подов»** → формат `<svc>.<ns>.svc.cluster.local`; ClusterIP → один VIP; список — только headless; вся история «TTL DNS меняет IP» относится к headless/Consul; TTL CoreDNS ≈30 с.
- **M — «TCP state mismatch… use of closed network connection»; «connection refused 80%»; `ErrConnectionClosed`** → выдумано. **M — код `NewResolver` «контроль TTL»**; `ServiceBalancer` «lock-free» при RLock+копии. **L — «cache stampede»; P2C; SRV; EndpointSlices.**

#### Ст.31. CDN/Edge
- **H — «Go на edge: нет GC-пауз/escape-анализа; упаковка в eBPF/FFI»** → у Go есть GC; escape-анализ — компиляторный; реально TinyGo/wasip1.
- **M — «anycast → наименее загруженный»** → ближайший по BGP. **M — «RFC 7234»** → RFC 9111; RFC 9213, Cache-Status, immutable. **M — `inm == etag`** (списки, weak, `*`); 304 без Cache-Control/Vary. **M — «Vary: Authorization»** → private/no-store. **M — нет инвалидации (purge, surrogate keys, shield).**
- **L — `write-through`; TFO; `http2.Transport` в клиенте (авто); xxhash «SIMD».**

#### Ст.32. Firewall
- **H — «conntrack full → ECONNREFUSED или ETIMEDOUT»** → X6 (только таймаут).
- **M — `INPUT ACCEPT 22,80; DROP`** → ломает исходящие соединения хоста (нет ESTABLISHED,RELATED и `lo`). **M — nftables-команды** → `nft add rule ip filter input ip saddr @whitelist accept`; CIDR требует `flags interval`. **M — интервью «telnet работает, Go нет → conntrack»** → логическое противоречие (IPv6/DNS/proxy env/uid-owner). **M — «Cilium генерирует nftables»; iptables-nft** → Cilium — eBPF.
- **L — «iptables через netlink» (setsockopt); «nftables близок к BPF»; Docker DNAT/DOCKER-USER; AWS NACL; `err == context.DeadlineExceeded`.**

#### Ст.33. DDoS/Rate limiting
- **H — «P не создаются при нехватке FD»; «пул контекстов»; «STW чаще»** → неверно (X10).
- **M — «10 000 slow-conn гарантированно убьют память»** → ≈100 МБ; противоречит ст.1/2; Go ≥1.19 поднимает RLIMIT_NOFILE (`os/rlimit.go`) [проверить файл]. **M — limiter: `global.Allow()` до per-IP** → выжигает глобальный бюджет. **M — «Sliding Window Counter — ложные срабатывания на границе»** → это Fixed Window. **M — `MaxHeaderBytes` «защита от Slowloris»; «новый сервер в Go 1.21».**
- **L — SYN cookies при «включении»; «фаззинг мьютекса»; EADDRNOTAVAIL vs EADDRINUSE.**

### Блок 6. Наблюдаемость, ядро, Go (ст.34–38)

#### Ст.34. tcpdump/ss
- **H — `GODEBUG=netpoll=1`; pprof «syscall»** → не существуют [✔ src]. 
- **M — Wireshark без дешифровки** → `SSLKEYLOGFILE`/`KeyLogWriter`; снятие трафика подов (`nsenter`, `kubectl debug`). **M — `-n` «обязателен»; `--snapshot-len` кольцо; `tcptrace` — eBPF** → при `-w` резолва нет; кольцо — `-B/-C/-W`. **M — «ss O(1)», «ss показывает QUIC», «iowait»; `ss … | grep <pid>` без `-p`.** **M — «ESTABLISHED, tcpdump пуст → TIME_WAIT»** → чаще idle keep-alive.

#### Ст.35. ping/traceroute/dig/curl/mtr
- **H — mtr: «потери на hop-2, исчезают на hop-3 → проблема провайдера»** → ICMP rate-limiting; значимы сохраняющиеся потери.
- **H — dig: «>512 байт → флаг DO»; «Go по умолчанию go (cgo)»** → DO — DNSSEC OK; TC — усечение; go=pure Go.
- **H — «net не поддерживает raw; raw блокирует M; LockOSThread; netpoller не работает с raw; IP_HDRINCL запрещён»** → `net.ListenIP/DialIP` есть [✔ src], работают через netpoller; `ipv4.RawConn` — IP_HDRINCL; `icmp.ListenPacket("udp4")` — без привилегий.
- **M — `pingHost`** читает первый ICMP без проверки ID/Seq и без RTT; `runContinuousProbe`; traceroute-фрагмент (`SetControlMessage` не ставит TTL; `Fd()` нет); `curl -w` не показан; `MaxIdleConnsPerHost` «блокирует»; `DualStack` deprecated; eBPF «без CAP_NET_RAW» (нужны CAP_BPF/NET_ADMIN).

#### Ст.36. eBPF/XDP
- **H — «Mellanox ConnectX поддерживает XDP offload»** → offload — в основном Netronome (nfp).
- **M — код cilium/ebpf** (`go build xdp.c`; `link.XDPOpts`; `Lookup([]byte)`; `import "os"`; `Replace:true`) → bpf2go/clang; `link.XDPOptions`; тип ключа карты; `link.Update`. **M — «TC после маршрутизации»** → ingress раньше netfilter. **M — числа таблицы (iptables 1–3 мкс; XDP 25–50 нс; 40+ Mpps)** без источника. **M — DAG «без циклов» vs «зациклится → soft lockup»** → bounded loops с 5.3, `bpf_loop` 5.17.
- **L — `vmlinux.h` не нужен на целевой машине; BTF с 5.2; нет привилегий (CAP_BPF 5.8), версий ядра, AF_XDP, uprobes на Go.**

#### Ст.37. Сетевой стек Linux
- **H — «если данных нет, процесс блокируется в ядре» (про Go)** → противоречит модели (non-blocking+epoll).
- **M — sysctl-комментарии перепутаны** (`tcp_max_syn_backlog` ≠ лимит соединений; `ip_local_port_range` ≠ REUSEPORT; `tcp_tw_reuse` не уменьшает TIME_WAIT; нижняя граница 1024 пересекается с портами сервисов). **M — `SetNoDelay(true)` как тюнинг** → X1; `SetReadBuffer` → autotuning. **M — «выделенные потоки poller»** → X7.
- **L — `kmalloc-256/512`; `cb[]` и retransmit; `sk_backlog`; не раскрыты NAPI/RSS/RPS/qdisc/BQL, обещанные во введении.**

#### Ст.38. Go и сеть
- **H — «epoll_pwait2 (5.11+) для наносекундных таймаутов без timerfd»** → не используется [✔ src].
- **H — `wakeG`, «SetReadDeadline → epoll_ctl», регистрация после EAGAIN** → X7; дедлайны — таймеры pollDesc.
- **M — «лимит fd в netpoller»; «утечка при SetDeadline»; `http2.Priority`; «STW чаще»; «5–10 тыс. потоков»; `DualStack`.** Верно: 2 idle/host, `client.Timeout` vs `dialer.Timeout`.

### Блок 7. Эксплуатация, K8s, mesh, паттерны (ст.39–44)

#### Ст.39. TIME_WAIT
- **H — «IdleConnTimeout обязан быть >60 с (>2·MSL)»; «короткий idle → SYN→FIN цикл»** → TIME_WAIT от idle-таймаута не зависит.
- **H — интервью «почему SO_REUSEADDR не спасает при рестарте»** → спасает (X3); conntrack к bind не относится.
- **M — «bind: address already in use» как симптом клиента** → `EADDRNOTAVAIL`; лимит per 4-tuple. **M — не упомянуты `tcp_tw_reuse` default 2, `tcp_tw_recycle`, conntrack time_wait=120 с, `IP_BIND_ADDRESS_NO_PORT`, `tcp_migrate_req`.**
- **L — `tcp_max_tw_buckets`; `tcp_time_wait_hash`; `ip_local_reserved_ports`.**

#### Ст.40. HoL/Slowloris
- **H — «`MaxIdleConnsPerHost=0` → неограниченно»** → X4. **H — `http.ServerMetrics`; `http.Server.MaxConns`** → не существуют [✔ src].
- **M — итог «HTTP/2: потеря влияет только на stream»** → противоречит тексту; верно для HTTP/3. **M — «клиент отвалится по ОС-таймауту 2+ часа»** → живой Slowloris-клиент; X2. **M — «блокированные в netpoll горутины создают M»** → нет.
- **L — дедлайн = runtime-таймер; `BaseContext` со строковым ключом; slow-read/RUDY/zero-window.**

#### Ст.41. K8s Networking
- **M — «два режима kube-proxy: iptables, IPVS; IPVS категорически лучше»** → IPVS deprecated (1.35), nftables GA (1.33) [✔ web]. **M — «ClusterIP не на интерфейсе»** → в IPVS — на `kube-ipvs0`; «iptables O(N) на каждый пакет» — на первый; «перейти на ipvs решит conntrack» противоречиво. **M — Ingress без Gateway API/ingress-nginx EOL; Weave** [✔ web]. **M — интервью «curl NXDOMAIN, wget работает — Go resolver»** → curl/wget не Go. **M — «Go не умеет фрагментацию/CUBIC в Go»** → ядро.
- **L — цифры Cilium; veth «копирует»; netns «1–2 КБ»; таймауты NLB/GCP/Azure; NetworkPolicy, `externalTrafficPolicy`, NodeLocal DNSCache.**

#### Ст.42. Service Mesh
- **H — «Go dial'ит 127.0.0.1:15001»; «port exhaustion на 15001; Linkerd UDS»** → REDIRECT прозрачен (`SO_ORIGINAL_DST`).
- **H — противоречие со ст.28 (Linkerd/Envoy)**; xDS в Linkerd нет; `linkerd-controller` устарел.
- **M — Ambient = eBPF** → ztunnel+waypoint; Tetragon/Kube-OVN/OTel — не mesh; proxyless gRPC (xDS) не упомянут. **M — «обход прокси через явный IP»** → иначе; Istio CNI, native sidecar (K8s 1.33 GA), startup race, protocol sniffing. **M — «каскадные таймауты»** → retry amplification; L7-LB gRPC как причина внедрения. **M — «sidecar SO_LINGER=0»** → выдумка.
- **L — порты Linkerd (4143 inbound/4140 outbound); «нет динамических аллокаций»; hot restart; смена модели поставки Linkerd [✔ web].**

#### Ст.43. Сетевые паттерны
- **H — `idempKey := uuid.New()` внутри CreateOrder** → новый ключ на каждый вызов — идемпотентность теряется; ключ один на операцию, переиспользуется в ретраях.
- **M — `errors.Is(err, context.DeadlineExceeded)` для gRPC** → `status.Code`. **M — «gRPC без retry; grpc-go/retry»** → есть service-config retry (A6); middleware — сторонний. **M — NATS-код** → неограниченные горутины, `context.Background()`, нет errgroup. **M — Half-Open «один запрос»** → пропускает все. **M — `SetKeepAlive … 72000 сек`** → 7200; X2/X3.
- **L — не раскрыты bulkhead, load shedding, hedging, deadline propagation, saga/outbox; `wakeG`.**

#### Ст.44. Итоги
- **H — «SO_REUSEPORT: Go использует для баланса между P»** → не включается по умолчанию. **H — NODELAY (X1). H — «http3.Transport в современном Go»** → не std.
- **M — Zero-copy «без memcpy если буфер выровнен»** → write всегда копирует (кроме MSG_ZEROCOPY); `net.Buffers`. **M — «до 1024 событий», «Go 1.22+ ET», `wakeG`** → 128/давно/нет [✔ src]. **M — `Resolver.LookupContext`** → нет. **M — «новый http.Client теряет пул»; DefaultClient** → пул у Transport; нет Timeout. **M — «потеря пакетов → -EAGAIN/0 байт; use of closed network connection»** → потери невидимы; `i/o timeout`/`ETIMEDOUT`.
- **L — «Cancel → TIME_WAIT»; «Dial без ctx → гарантированная утечка»; «переключение таблиц страниц при syscall».**

---

## 3. Важные упущения (не ошибки, но пробелы относительно заявленного охвата)

| Тема | Где нужна | Что добавить | Приор. |
|---|---|---|---|
| Дренаж тела ответа до `Close()` | ст.21 | `io.Copy(io.Discard, resp.Body)` для reuse | **H** |
| Дефолтные таймауты Go (`http.Client` без Timeout, `Server` без таймаутов) | ст.20, 21, 40 | таблица дефолтов | **M** |
| ECN/DCTCP, `ss -ti`, `nstat` | ст.13, 34 | диагностика CC | **M** |
| Заголовки `Forwarded`/XFF, PROXY protocol, smuggling | ст.27–29 | модель доверия к IP клиента | **M** |
| Alt-Svc/HTTPS RR, fallback с UDP/443 | ст.23 | как клиент находит h3 | **M** |
| `externalTrafficPolicy`, EndpointSlices, Gateway API, NetworkPolicy | ст.41 | современный K8s-стек | **M** |
| Native sidecar, Ambient, proxyless gRPC | ст.42 | выбор архитектуры mesh | **M** |
| Docker/DNAT и INPUT-правила | ст.32 | `DOCKER-USER` | **M** |
| Привилегии/версии для eBPF (CAP_BPF, 5.x) | ст.36 | матрица требований | **M** |
| Интеграция `RawConn.Read/Write` с netpoller | ст.38 | как кооперировать syscall с poller | **L** |

## 4. Рекомендованный порядок правок

1. X1–X8 (сквозные H): единая «таблица дефолтов Go net/http/TCP» (NODELAY=1, keepalive 15 с, REUSEADDR, backlog=somaxconn, `DefaultMaxIdleConnsPerHost=2`, dual-stack, нет DNS-кэша, EDNS0 1232) и ссылки на неё из ст.1, 2, 8, 10–12, 15, 21, 37–40, 43, 44.
2. H-ошибки в кодовых примерах, которые читатель скопирует: ст.14 (`Connect`, буфер 1500), 19 (`VerifyHostname` советы), 25 (`r.Context` после Hijack, thread-safety), 27 (`FlushInterval`), 30 (`publishNotReadyAddresses`), 32 (iptables/nft), 36 (cilium/ebpf), 43 (idempotency key).
3. Формулы и параметры: RTO (12), PTO (24), Cubic β (13), delack (12), TCP-флаги, sysctl-комментарии (37).
4. Актуализация: сертификаты/PKI (19), K8s (41), mesh (42), ingress-nginx (28/41).
5. Привязка версий Go в тексте к проверенным фактам (1.13 TLS1.3, 1.19 RLIMIT, 1.20 ResponseController, 1.23 KeepAliveConfig, 1.24 h2c/PQ, 1.25 cgroup GOMAXPROCS).

Ограничения: не проверялись по первоисточнику (помечены [проверить]) — конкретные поля ядра/`quic-go`, gorilla-доки, поведение `ss`/`mtr` на реальном железе, CVE-идентификаторы WebSocket. Эксперименты выполнялись на loopback без реальной сети.
