# Master Fact-Check Brief · Модуль 3 «Компьютерные сети и сетевой стек»

> **Роль:** senior research judge (Opus).
> **Входные данные:**
> - `sources/3. Компьютерные сети и сетевой стек/` — 44 статьи, 13 205 строк, 80 блоков ```go (38 полных `package`, 42 фрагмента). Модуль уже проходил один фактчек: коммит `d9b00f4f docs(factcheck): correct module 3 technical claims` (2026-09-25), см. § 6.
> - `3-gemini-scout.md` — 28 кандидатов (13 High, 9 Medium, 6 Low).
> - `3-sonnet-alt.md` — 14 сквозных тем (X1–X14), ≈ 330 строк по статьям, 10 пропусков, журнал механической проверки.
> - Инструкция фактчекера: `4. Sonnet Fact Check` (статусы VERIFIED / INCORRECT / PARTIALLY CORRECT / OUTDATED / CONTEXT-DEPENDENT / OPINION / NOT CHECKED).
>
> **Адресат:** следующий шаг конвейера — первичный фактчек по источникам (`3-sonnet-fact-check.md`) и, если будет, `3-opus-blind-spot.md`.

---

## 0. Как пользоваться этим брифом

1. **Это не вердикт.** Бриф говорит, *что* проверить, *почему* и *каким источником это решается*. Статус каждому утверждению присваивает фактчекер.
2. **Улики судьи.** Часть пунктов я сверил сам; такие места помечены **[улика судьи]** с путём к файлу и строкой. Что использовалось:
   - тулчейн **go1.27.1 linux/amd64** (`/usr/local/go/src`, `/usr/local/go/api/go1.*.txt` — для версий появления API);
   - `golang.org/x/net v0.59.0` (http2), `github.com/cilium/ebpf v0.22.0`, `golang.org/x/sys v0.46.0` из локального кэша модулей;
   - извлечение всех 80 Go-блоков модуля; `gofmt -e` для всех полных `package`-блоков и `go vet` для тех, чьи зависимости есть в кэше (§ 2, J-H6);
   - ядро машины судьи **Linux 7.2.8 (Fedora 44)**: `/proc/sys/net/...`, `/usr/include/linux/tcp.h`;
   - `grep` по тексту статей: каждая находка обоих брифов прослежена до строки (номера строк в брифе — по текущему `HEAD`).

   Улики судьи — сильная подсказка, но не замена проверки. Тулчейн показывает поведение только 1.27.1, границы версий («с Go 1.xx») нужно подтверждать по release notes или `api/go1.xx.txt`. Утверждения о ядре, RFC, железе, K8s, Envoy/nginx/HAProxy, quic-go, gRPC судья **не** проверял по первоисточникам, если это не оговорено явно; для них указан решающий источник.
3. **Gemini.** Номера статей у Gemini верны, но цитаты местами пересказаны своими словами (G7: в тексте **нет** слов про «дополнительные epoll-инстансы»). Нумерация в сводной таблице Gemini (строки 486–517) **не совпадает** с нумерацией «Кандидат N» в теле. В этом брифе `G#` всегда означает номер «Кандидат N» из тела отчёта.
4. **Sonnet.** Покрытие на порядок шире. Механические проверки по исходникам Go в основном подтвердились, но есть одно ложное срабатывание (`epoll_pwait`, § 3, K1) и одно устаревшее утверждение о ядре (sysctl/опции RTO и delayed ACK, § 3, K2). Строки у Sonnet без номеров; здесь номера добавлены там, где судья их нашёл.
5. **Происхождение находок:** `G#` — кандидат Gemini; `S:X#` — сквозная тема Sonnet; `S n` — строка Sonnet по статье n; `J` — добавлено судьёй.
6. **Типы находок:** **ФАКТ** — фактическая ошибка; **КОД** — пример не компилируется или делает не то, что заявлено; **API** — несуществующий идентификатор, поле, флаг; **УСТАР.** — устарело; **ДОПУЩ.** — скрытое допущение (версия, ОС, дистрибутив); **ПРОТИВ.** — противоречие внутри статьи или между статьями; **ЧИСЛО** — цифра без источника; **УПРОЩ.** — допустимое учебное упрощение, нужна разве что оговорка; **МНЕНИЕ** — оценка, поданная как факт; **ПРОПУСК** — важное упущение, не ошибка; **РАЗМЕТКА** — дефект рендеринга.
7. **Порядок работы фактчекера:** § 2 (High) → § 3 (конфликты и ложные срабатывания) → § 4 (кластеры) → § 5 (C-FIX: остатки прошлого фактчека) → § 6 (Medium по статьям) → § 7 (Low) → § 9 (пропуски). Пункты § 8 («Отклонено/понижено») перепроверять не нужно, если не появятся новые улики.

---

## 1. Сводка

| Категория | Кол-во | Комментарий |
|---|:---:|---|
| High-блоки (после слияния) | 30 | объединяют ≈ 140 строк обоих брифов |
| Конфликты и ложные срабатывания брифов | 12 | у каждого — решающая улика |
| Сквозные кластеры | 14 | одна проблема в нескольких статьях |
| Остатки прошлого фактчека `d9b00f4f` (C-FIX) | 11 мест | правка сделана частично или сама внесла ошибку |
| Medium (после слияния) | ≈ 190 | § 6, по статьям |
| Low | ≈ 150 | § 7, компактно |
| Отклонено или понижено | 9 | § 8 |
| Находки судьи (`J`), которых нет ни в одном брифе | ≈ 15 | помечены `J` |

**Общая картина.**
- **Gemini** дал узкий список (28), почти целиком про код. 26 из 28 подтверждаются текстом. Уникально у Gemini (у Sonnet нет или есть лишь намёк): G2 (часть статей), G3 (неограниченный рост карты лимитеров — OOM), G4, G5 подробно, G8, G9 (gRPC bidi), G10 (SO_RCVBUF в ст. 13), G12 (`BaseContext`), G13 (chunked без Flush), G15, G17 (ст. 38), G20, G22 (`KeepAliveConfig`), G24 (RSS/RPS), G26, G27.
- **Sonnet** покрыл модуль целиком и проверял по исходникам и экспериментами. Все Go-утверждения Sonnet, которые я перепроверил, подтвердились, кроме K1 (`epoll_pwait`). Слабости Sonnet: несколько неверно указанных статей (X5 «Go 1.11» в ст. 16), путь к коду rlimit (`os/rlimit.go` не существует, верно `syscall/rlimit.go`) и устаревшая формулировка о ядре (K2).
- Модуль уже **прошёл фактчек `d9b00f4f`**, но правка была точечной: рядом с исправленными строками остались старые формулировки, а одна правка внесла новую ошибку («до 1024 событий», § 5). Отсюда много внутренних противоречий.

**Главные изменения приоритетов:**
- **G4 понижен с High до Low.** Переполнение `int64` наступит после 2⁶³ инкрементов (≈ 292 года при 10⁹ вызовов/с). «Инициализация в −1» в коде невозможна: поле не экспортируется и стартует с 0. Совет `uint64` уместен как гигиена, не как баг. Вместо этого в том же листинге судья нашёл реальную ошибку в ответе на собеседование (J, § 6, ст. 30).
- **G25 повышен с Low до High** (вместе с S 39): правило «`IdleConnTimeout` > 2·MSL» повторено в итогах ст. 39 как закон.
- **G23 (Rapid Reset) повышен с Medium до High** и уточнён: поля `http2.Server.MaxHeaderListSize` и `ReadHeaderBufferSize` **не существуют** (J). Механизм защиты у Gemini описан неверно, у Sonnet — верно (§ 3, K5).
- **G16, G14 повышены с Medium до High:** несуществующее поле API и вредный совет по безопасности TLS.
- **G7 подтверждён, но цитата исправлена** (§ 3, K3).
- **G11: ст. 12 исключена** из списка ошибочных — она как раз говорит верно (§ 3, K4).
- **Sonnet High понижены до Medium:** S 16 «встроенный кэш» (поведение описано верно, неверны ярлык и реализация), S 36 «Mellanox XDP offload», S 26 «GOAWAY или CANCEL», S 37 «процесс блокируется в ядре», S 2 «цепочка `net.Listen`», S 28 «nginx splice» оставлен High только в части HAProxy.
- **Новый кластер C-FIX** (§ 5): прошлый фактчек оставил противоречия в ст. 12, 16, 21, 23, 44 и внёс неверную цифру в ст. 44.

---

## 2. High: проверить в первую очередь

### J-H1. «Нагл в Go включён по умолчанию, вызывайте `SetNoDelay(true)`» (ст. 10, 11, 37, 44 против ст. 12, 21) · ФАКТ + ПРОТИВ.
*Источники: G11, S:X1, S 10, S 11, S 37, S 44.*
- **Утверждения:**
  - ст. 10, строки 318–330: «По умолчанию ядро Linux объединяет мелкие порции… В микросервисах на Go всегда принудительно отключают Нагла» + листинг `SetNoDelay(true)`;
  - ст. 11, строки 352–358 и 428: `SetNoDelay(true)` как «критично для low-latency», итог «отключение алгоритма Нейгла — обязательный арсенал»;
  - ст. 37, строки 266 и 275: `conn.SetNoDelay(true) // критично для low-latency`;
  - ст. 44, строка 170: «По умолчанию в сетевом стеке активирован алгоритм Нагла… его отключение через `conn.SetNoDelay(true)` обязательно».
- **Противоречит:** ст. 12, строки 226–243 и 342 («В Go флаг `TCP_NODELAY` включен по умолчанию»), ст. 21, строка 163.
- **[улика судьи]** `net/tcpsock.go:290` — `newTCPConn` первой строкой вызывает `setNoDelay(fd, true)`; путь используется и для `Dial`, и для `Accept`. Sonnet подтвердил экспериментом (`TCP_NODELAY=1`).
- **Уточнение к Gemini:** G11 включает ст. 12 в список ошибочных. Это неверно: ст. 12 — единственное место, где сказано правильно (§ 3, K4).
- **Что решить фактчекеру:** для ядра (C, Python, Java) дефолт «Нагл включён» верен; для Go — нет. Проверить, что ст. 10/11/37/44 не подают ядерный дефолт как поведение Go.
- **Решающий источник:** `src/net/tcpsock.go` (`newTCPConn`), doc `(*TCPConn).SetNoDelay` («The default is true (no delay)»).
- **Приоритет: High.**

### J-H2. TCP keepalive в Go: «дефолт 2 часа бесполезен», «`SetKeepAlive(true)` — включение», «72000 сек», «с Go 1.16» (ст. 1, 8, 11, 12, 21, 40, 41, 43) · ФАКТ + УСТАР. + ПРОПУСК
*Источники: S:X2, S 12, S 43, S 1, S 8, S 40, S 41, G22.*
- **Утверждения:**
  - ст. 12, строки 286–291 и 356: «Дефолтный TCP Keep-Alive абсолютно бесполезен», «Дефолтный таймаут в 2 часа бесполезен… Требуется явное уменьшение периода через `SetKeepAlivePeriod`»;
  - ст. 12, строка 298: «Начиная с релиза Go 1.16… `SetKeepAlivePeriod`»;
  - ст. 43, строка 305: «`SetKeepAlive(true)` отправляет TCP-пакеты каждые **72000** сек»;
  - ст. 11, строки 342–349; ст. 41, строка 181; ст. 21, строка 283 («обычно 2 часа»); ст. 1, строка 190 («соединение останется висеть вечно»); ст. 40 («клиент отвалится по ОС-таймауту 2+ часа»); ст. 8 (`net.Dialer{KeepAlive:15s}` как «включение»).
- **Почему проверять:** для соединений, созданных через `net.Dial`/`net.Listen`, Go **уже** включает keepalive: idle = 15 с, interval = 15 с, count = 9. «7200 с» — ядерный дефолт для сокетов, где keepalive включили без настройки. `SetKeepAlivePeriod` существует с Go 1.2, а не 1.16. «72000» — опечатка (7200). `net.KeepAliveConfig` (Go 1.23) в модуле не упомянут ни разу (G22).
- **[улика судьи]** `net/dial.go:18–27` (`defaultTCPKeepAliveIdle = 15s`, `defaultTCPKeepAliveInterval = 15s`, `defaultTCPKeepAliveCount = 9`); `net/tcpsock.go:291–296` (keepalive включается, если не отключён явно); `api/go1.2.txt` — `SetKeepAlivePeriod`; `api/go1.23.txt` — `KeepAliveConfig`, `SetKeepAliveConfig`, `Dialer.KeepAliveConfig`. `grep KeepAliveConfig` по модулю — 0 совпадений.
- **Нюанс для текста:** «мёртвый пир обнаружится за ≈ 15 + 9·15 = 150 с» (Sonnet) — проверить по `KeepAliveConfig` doc: при `Interval == 0` и `Count == 0` используются 15 с и 9.
- **Решающий источник:** `src/net/dial.go`, `src/net/tcpsock.go`, `src/net/tcpsockopt_*.go`; Go 1.23 Release Notes; `api/go1.2.txt`.
- **Приоритет: High.**

### J-H3. Потокобезопасность `net.Conn` и `gorilla/websocket.Conn` (ст. 1, 25) · ФАКТ
*Источники: S:X8, S 1, S 25.*
- **Утверждения:**
  - ст. 1, строки 187–188: «одновременный вызов двух `Read()` или двух `Write()` из разных горутин категорически запрещен! Это приведет к разрушению внутренних буферов… Race Conditions»; строка 235 — «учитывайте неполную потокобезопасность `net.Conn`»;
  - ст. 25, строки 275–277: «`websocket.Conn` не является потокобезопасным для одновременного вызова `ReadMessage` и `WriteMessage`».
- **Почему проверять:** для `net.Conn` всё ровно наоборот: документация разрешает конкурентные вызовы, `fdMutex` сериализует `Read` с `Read` и `Write` с `Write`, а один `Write` пишет весь буфер целиком. Опасность прикладная: перемешивание логических сообщений, собранных из нескольких `Write`. У gorilla — тоже наоборот: допустимы один читатель и один писатель одновременно; нельзя нескольких писателей (или нескольких читателей).
- **[улика судьи]** `net/net.go:123`: «Multiple goroutines may invoke methods on a Conn simultaneously.»
- **Решающий источник:** doc `net.Conn`; `internal/poll/fd_mutex.go`; gorilla/websocket README и godoc, раздел «Concurrency» («Connections support one concurrent reader and one concurrent writer»).
- **Приоритет: High.**

### J-H4. Внутренности netpoller: `wakeG`, `netpollReady`, `EPOLL_CTL_MOD`, регистрация «после EAGAIN», «лимит FD», `epoll_pwait2`, `webPoller`, «фоновый поток», «1024 события», «Go 1.22+ ET» (ст. 1, 10, 15, 25, 34, 37, 38, 43, 44) · ФАКТ + API + ПРОТИВ. (часть — C-FIX)
*Источники: G7, S:X7, S 1, S 10, S 15, S 37, S 38, S 44.*
- **Утверждения и строки:**
  - `runtime.wakeG`: ст. 38, строки 21, 70, 79, 86, 108, 117, 189; ст. 43, строка 42; ст. 44, строка 49;
  - `netpollReady`/`netpollBlock`/«вызывает `runtime.stopm`»: ст. 1, строка 177; ст. 38, строки 21, 70;
  - `epoll_ctl(EPOLL_CTL_MOD, fd, EPOLLIN)` после EAGAIN: ст. 1, строка 144; «FD регистрируется… с событием `EPOLLIN | EPOLLET`»: ст. 37, строки 134, 149; ст. 38, строка 77;
  - «`netpoller` имеет лимит на количество отслеживаемых FD… динамически масштабируется»: ст. 38, строка 82;
  - `epoll_pwait2` (Linux 5.11+) «для наносекундных таймаутов»: ст. 38, строка 170;
  - «использует `epoll_pwait` для безопасной маскировки сигналов»: ст. 1, строки 163, 169;
  - `webPoller` для WASM: ст. 1, строка 172;
  - «Фоновый поток рантайма… выполняющий `epoll_wait`»: ст. 15, строка 312; ст. 10 и 37 (Sonnet);
  - «пачку до 1024 готовых событий»: ст. 44, строка 104 (**внесено прошлым фактчеком**, § 5);
  - «в современных версиях Go 1.22+ оптимизированный edge-triggered режим»: ст. 44, строка 71.
- **[улика судьи]**
  - `runtime/netpoll_epoll.go:16` — один глобальный `epfd`; `:51,54` — регистрация **один раз** с `EPOLLIN|EPOLLOUT|EPOLLRDHUP|EPOLLET`; `:117` — `var events [128]linux.EpollEvent`; `:119` — `linux.EpollWait(...)`.
  - `internal/runtime/syscall/linux/syscall_linux.go:32` — `EpollWait` реализован как `Syscall6(SYS_EPOLL_PWAIT, epfd, ev, maxev, waitms, 0, 0)`, т. е. **`epoll_pwait` с нулевой маской сигналов**. Значит, имя системного вызова в ст. 1 **верно**, а обоснование («для безопасной маскировки сигналов») — нет: маска не передаётся (§ 3, K1).
  - `grep -rn wakeG /usr/local/go/src/runtime` — пусто. Реальная цепочка: `netpoll` → `netpollready` → `netpollunblock` → список `gList` → `injectglist`; парковка — `netpollblock` → `gopark`.
  - Файлы `runtime/netpoll_*.go`: `aix`, `epoll`, `fake` (`js && wasm` — заглушка, поллера нет), `kqueue`, `solaris`, `stub`, `wasip1`, `windows`. Никакого `webPoller` нет.
  - `proc.go:1778, 3511` — `netpoll(0)` вызывают `findRunnable`/`sysmon`/`startTheWorld`; выделенного потока поллера нет.
- **Уточнение к Gemini (G7, п. 1):** в ст. 38 нет слов о «создании дополнительных epoll-инстансов». Там сказано «имеет лимит… динамически масштабируется» — ошибка есть, но формулировку надо цитировать по тексту (§ 3, K3).
- **Решающий источник:** `src/runtime/netpoll.go`, `netpoll_epoll.go`, `proc.go` (`findRunnable`, `sysmon`); `internal/runtime/syscall/linux/syscall_linux.go`; для ET-режима и его давности — `git log -S EPOLLET -- src/runtime/netpoll_epoll.go`.
- **Приоритет: High.**

### J-H5. Несуществующие API, поля и идентификаторы (кластер C-API) · API
*Источники: G1, G16, G19, S 4, S 14, S 15, S 20, S 22, S 23, S 34, S 36, S 40, S 44, J.*

| Ст., строка | В тексте | Реальность | Улика |
|---|---|---|---|
| 32: 5, 174 | `net.DialContext(ctx, …)` | функции нет; есть `(*net.Dialer).DialContext` | G1; doc `net` |
| 20: 176 | поле `Request.Context context.Context` в «упрощённой структуре из `src/net/http/request.go`» | поле приватное `ctx`; доступ — `r.Context()`, `r.WithContext`, `r.Clone` | G16, S 20; `net/http/request.go` |
| 22: 245 | `http2.Server.MaxHeaderListSize`, `http2.Server.ReadHeaderBufferSize` | **у `http2.Server` таких полей нет** | **J**: [улика судьи] `x/net@v0.59.0/http2/server_common.go:52` — поля: `MaxHandlers, MaxConcurrentStreams, MaxDecoderHeaderTableSize, MaxEncoderHeaderTableSize, MaxReadFrameSize, PermitProhibitedCipherSuites, IdleTimeout, ReadIdleTimeout, PingTimeout, WriteByteTimeout, MaxUploadBufferPerConnection, MaxUploadBufferPerStream, NewWriteScheduler, CountError` |
| 40: 109, 196 | `http.Server.MaxConns`, `http.ServerMetrics` | не существуют | S 40 (✔ src) |
| 44: 134 | `net.Resolver.LookupContext` | не существует | S 44 |
| 15: 174 | `syscall.ListenConfig` | это `net.ListenConfig` | S 15 |
| 14: 146, 359–361 | `conn.Connect(addr)` у UDP-сокета | у `*net.UDPConn` метода `Connect` нет; «подключённый» UDP — `net.DialUDP` | S 14 (✔ src) |
| 14: 140 | «`net.UDPConn` встраивает универсальный `net.IPConn`» | `type UDPConn struct { conn }` | **J**: [улика судьи] `net/udpsock.go` |
| 4: 299 | методы `netip.Addr` `IPv4()`, `IPv6()` | нет; есть `AddrFrom4/16`, `As4/As16`, `Unmap`, `Is4/Is6` | S 4 |
| 4: 205 | `syscall.WriteMsgUDP` с `MSG_MORE` | `syscall.WriteMsgUDP` не существует (есть `(*net.UDPConn).WriteMsgUDP`) | S 4 |
| 34: 162 | `GODEBUG=netpoll=1`; профиль pprof «`syscall`» | нет такой опции GODEBUG; стандартного профиля `syscall` нет | S 34 |
| 36: 158–170 | `link.XDPOpts`, `&link.XDPOpts{…}` | `link.XDPOptions`, передаётся **значением** | S 36 + **J**: [улика судьи] `go vet` с `cilium/ebpf v0.22.0`: `undefined: link.XDPOpts`; после замены — `cannot use &link.XDPOptions{…} … as link.XDPOptions value`; затем `"os" imported and not used` |
| 24: 229–250 | `fd *poll.FD`, `fd.Read()` без аргументов, `fd.SyscallConn().Read(…)` «из quic-go» | `internal/poll` нельзя импортировать; у `poll.FD` нет `SyscallConn`; в quic-go такого кода нет | G19, S 24 |
| 23: 165, 229; 44: 148 | `golang.org/x/net/http3`, `http3.Transport` «в современном Go» | публичного пакета нет; использовать `github.com/quic-go/quic-go/http3` (C-FIX: ст. 23, строка 81 уже говорит верно) | S 23, S 44 |
| 23: 151 | `http3.Client` | проверить по godoc quic-go/http3 (там `Transport`, ранее `RoundTripper`) | S 23 |
| 19 | тип `CertificateSignatureAlgorithm` | выдуман (Sonnet); проверить по `crypto/x509` (`SignatureAlgorithm`) | S 19 |
| 1: 177; 38 | `netpollBlock`, `netpollReady`, `runtime.wakeG` | см. J-H4 | G7, S 1, S 38 |

- **Решающий источник:** `go doc` соответствующих пакетов в Go 1.27.1; `go vet` после копирования листинга.
- **Приоритет: High.**

### J-H6. Код, который не компилируется (кластер C-COMPILE) · КОД
*Источники: G1, G2, G8, S 36, J.*
- **[улика судьи]** `gofmt -e` — синтаксических ошибок в 38 полных листингах нет. `go vet` (std, `x/sys`, `x/net`, `cilium/ebpf`):

| Ст. | Строка блока | Ошибка | Кто нашёл |
|---|---|---|---|
| 2 | блок с 122 | `"fmt" imported and not used` | G2 |
| 20 | блок с 246 | `"time" imported and not used` | **J** |
| 30 | блок с 122 | `"context" imported and not used` | **J** |
| 31 | блок с 189 | `"encoding/hex" imported and not used` | G2 |
| 42 | блок с 159 | `"context" imported and not used` | G2 |
| 36 | блок с 145 | `link.XDPOpts`, указатель вместо значения, `"os"` не используется | S 36 + **J** |
| 32 | 5, 174 | `net.DialContext` (фрагменты) | G1 |

- `//go:generate go build -ldflags '-s -w' -o xdp_prog.xdp xdp.c` (ст. 36, строка 158): `go build` не компилирует C в eBPF; к тому же генерируется `xdp_prog.xdp`, а загружается `xdp_prog.o` (строка 162). Нужен `clang -target bpf` или `bpf2go` (G8, S 36).
- **Не проверено судьёй** (нет модулей в кэше): ст. 7 (`vishvananda/netlink`), 23 (`quic-go`), 33 (`x/time/rate`), 43 (gRPC `pb`, NATS, `uuid` — фрагменты со ссылками на неопределённые `Service`, `pb`). Фактчекеру — `go vet` с `GOFLAGS=-mod=mod` при доступе к сети.
- 42 блока — фрагменты без `package`; их корректность проверяется по смыслу (кластер C-LOGIC, J-H18).
- **Решающий источник:** `go vet` на Go 1.27.1.
- **Приоритет: High.**

### J-H7. DNS-резолвер Go: «кэш», 512 байт, EDNS0, выбор резолвера, флаг `DO` (ст. 1, 16, 17, 35, 44) · ФАКТ + ПРОТИВ. (часть — C-FIX)
*Источники: S:X5, S 1, S 16, S 17, S 35, G15.*
- **Утверждения:**
  - ст. 16, строки 178–179: «**Встроенный кэш с дедупликацией** (DNS Caching with Deduplication): …потокобезопасный механизм на базе **`sync.Map`**»; строка 221 (интервью) — «Go использует механизм DNS Caching with Deduplication»;
  - ст. 16, строки 94–101, 156, 325: «ответ > 512 байт → TC=1, повтор по TCP»; ст. 17, строка 325: «EDNS0… расширяя буфер до 4096 байт через опцию `udp-max`»;
  - ст. 35, строка 171: «Если ответ > 512 байт, сервер ставит флаг **`DO`** (EDNS0)»;
  - ст. 35, строка 173: «Go по умолчанию использует стратегию `go` (**Cgo resolver**), которая делегирует резолвинг libc»;
  - ст. 1, строка 192: «начиная с Go 1.20+ чистый `netgo` по умолчанию на большинстве платформ»; «рекомендуется `ndots:0`»;
  - ст. 16, строки 172–174: «macOS — `SCDynamicStore`; Windows — реестр через `dnscfg`».
- **Почему проверять:**
  1. Кэша ответов в Go нет. Есть дедупликация одновременных запросов (`singleflight`), и она построена на `map` + мьютекс, не на `sync.Map`. Сам механизм дедупликации в интервью ст. 16 описан **верно**; неверны ярлык «кэш» и `sync.Map`. Ст. 17 (строка 328), 30 (строка 92) и 44 (строка 171) говорят «кэша нет» — внутреннее противоречие.
  2. Go шлёт EDNS0 OPT с размером 1232, а не 512 и не 4096. `DO` — бит «DNSSEC OK», к усечению отношения не имеет. Усечение — флаг `TC`.
  3. Ст. 35, строка 173 перевёрнута: стратегия `go` — это pure-Go резолвер, не cgo.
  4. Выбор резолвера не привязан к «Go 1.20». На Linux по умолчанию предпочитается Go-резолвер; cgo — при `LOCALDOMAIN`/`RES_OPTIONS`/`HOSTALIASES`, нераспознанном `nsswitch.conf` и т. п. На darwin/ios, windows, plan9, android предпочитается системный резолвер.
- **[улика судьи]** `net/lookup.go:166` — `lookupGroup singleflight.Group`; `net/dnsclient_unix.go:39` — `maxDNSPacketSize = 1232`, `:77` — `SetEDNS0(maxDNSPacketSize, …)`; `net/conf.go:127–185` — «By default, prefer the go resolver», `goosPrefersCgo()` для `windows, plan9, darwin, ios, android`.
- **Совет ст. 1 `ndots:0`:** проверить — в K8s это ломает короткие имена сервисов; обычная рекомендация — `ndots:1–2` или FQDN с точкой (S 1). Это CONTEXT-DEPENDENT, а не факт.
- **Решающий источник:** `src/net/conf.go`, `lookup.go`, `dnsclient_unix.go`, `internal/singleflight`; RFC 6891; RFC 3225 (бит DO); doc `net` («Name Resolution»).
- **Приоритет: High** (ст. 35:171/173, EDNS); **Medium** (ярлык «кэш» в ст. 16).

### J-H8. Какую ошибку видит клиент при проблемах L2–L4 (ст. 3, 5, 7, 8, 9, 32) · ФАКТ (кластер C-ERRNO)
*Источники: S:X6, S 5, S 7, S 8, S 9, S 32.*
- **Утверждения:**
  - ст. 5, строка 340: переполнение таблицы соседей → «все вызовы `net.Dial()` падают с `no route to host`»;
  - ст. 7, строка 401: пропал default route → `dial tcp: connect: no route to host`;
  - ст. 8, строки 156 и 361: переполнение conntrack → «тихое отбрасывание пакетов с ошибками `no route to host`»;
  - ст. 32, строка 136: conntrack full → «`ECONNREFUSED` или `ETIMEDOUT`»;
  - ст. 9, строка 391: NetworkPolicy drop → `ECONNREFUSED` либо `network unreachable`;
  - ст. 3, строка 12: FDB exhaustion → `ECONNREFUSED`.
- **Почему проверять:** нет маршрута → `ENETUNREACH` («network is unreachable»); неудача ARP/NDP → `EHOSTUNREACH` («no route to host»); тихий DROP (conntrack full, DROP-правило) → только таймаут (SYN-ретрансмиты, `tcp_syn_retries`); `ECONNREFUSED` — только RST или ICMP port unreachable. Для переполнения таблицы соседей Sonnet предлагает `ENOBUFS` — это **не проверено**: в `tcp_connect()` ошибки передачи SYN, кроме `-ECONNREFUSED`, игнорируются, так что `connect` может закончиться таймаутом. Нужен эксперимент.
- **Решающий источник:** воспроизведение в network namespace (`ip netns`, `ip route del default`, `iptables -j DROP`, `nf_conntrack_max=…`, `gc_thresh3=…`); `man 2 connect`; `net/ipv4/tcp_output.c` (`tcp_connect`), `net/core/neighbour.c`.
- **Приоритет: High** (неверная диагностика в продакшене).

### J-H9. Дефолты пула `http.Transport` (ст. 21, 27, 35, 40, 44) · ФАКТ + ПРОТИВ. (часть — C-FIX)
*Источники: S:X4, S 21, S 27, S 35, S 40, S 44.*
- **Утверждения:**
  - ст. 21, строка 230: «по умолчанию `MaxIdleConnsPerHost = 100`… клиент держит до 100 параллельных TCP» — противоречит строке 59 той же статьи (уже исправленной: «= 2»);
  - ст. 40, строки 184–185: «Если `MaxIdleConnsPerHost` установлен в 0 или не задан — Go создаст неограниченное количество idle-соединений»;
  - ст. 35, строка 284: «`MaxIdleConnsPerHost` ограничивает количество живых сокетов… новые запросы блокируются до появления свободного сокета» — это поведение `MaxConnsPerHost`;
  - ст. 44, строка 124: «Если вы создаете новый `http.Client`… вы теряете пул… переиспользуйте `http.DefaultClient`».
- **[улика судьи]** `net/http/transport.go:62` — `DefaultMaxIdleConnsPerHost = 2`; комментарий у поля: «If zero, DefaultMaxIdleConnsPerHost is used».
- **Почему проверять:** `MaxIdleConnsPerHost` ограничивает только **простаивающие** соединения; одновременные не ограничены, пока не задан `MaxConnsPerHost` (Go 1.11). Пул живёт в `Transport`, а не в `Client`: новый `Client` с тем же `Transport` (или `DefaultTransport`) пул не теряет. `http.DefaultClient` не имеет `Timeout` — советовать его в продакшене спорно.
- **Решающий источник:** `src/net/http/transport.go`, doc `Transport.MaxIdleConnsPerHost`, `MaxConnsPerHost`, `Client`.
- **Приоритет: High.**

### J-H10. `SO_REUSEADDR` / `SO_REUSEPORT`: что делает Go, что решает ядро (ст. 2, 10, 15, 33, 37, 39, 42, 43, 44) · ФАКТ (кластер C-REUSE)
*Источники: S:X3, S 10, S 15, S 39, S 42, S 43, S 44.*
- **Утверждения:**
  - ст. 15, строки 170–184: «В Go это настраивается через `syscall.ListenConfig`» — совет делать то, что рантайм уже делает (и неверное имя пакета);
  - ст. 39, строки 111–112: «Почему `SO_REUSEADDR` не спасает от `TIME_WAIT` при перезапуске? …не удаляет `TIME_WAIT` из таблицы conntrack»;
  - ст. 44, строка 169: «`SO_REUSEPORT`… Go использует это для балансировки входящих соединений между логическими процессорами `p`»;
  - ст. 10, строка 249; ст. 42, строка 214; ст. 43, строки 306, 317; ст. 33, строка 240: `SO_REUSEADDR`/`SO_REUSEPORT` как средство от исчерпания **клиентских** эфемерных портов;
  - ст. 37, строка 153: `SO_REUSEPORT` «для распределения нагрузки между горутинами»;
  - ст. 39, строка 122: «рантайм Go последовательно выполняет `sysSocket -> bind -> listen`. При включенном `SO_REUSEPORT` ядро балансирует…».
- **[улика судьи]** `net/sockopt_linux.go:28,34` — Go сам ставит `SO_REUSEADDR=1` на слушающие (и multicast) сокеты. `SO_REUSEPORT` на Linux Go **не ставит** (есть только в `sockopt_bsd.go:56` и `sockopt_aix.go:38` для multicast UDP).
- **Почему проверять:** `SO_REUSEADDR` как раз и решает проблему рестарта сервера при `TIME_WAIT`, к conntrack это не относится. Обе опции влияют на `bind()` слушающего сокета; исчерпание клиентских портов лечат пулы, `tcp_tw_reuse` (на ядре судьи = 2), диапазон портов, `IP_BIND_ADDRESS_NO_PORT`, несколько исходных IP.
- **Решающий источник:** `src/net/sockopt_linux.go`, `sock_posix.go`; `man 7 socket`; `Documentation/networking/ip-sysctl.rst` (`tcp_tw_reuse`).
- **Приоритет: High.**

### J-H11. Буферы сокетов и автотюнинг окна (ст. 11, 13, 14, 25, 37) · ФАКТ + КОД (кластер C-SOCKBUF)
*Источники: G10, S 11, S 13, S 14, S 25, S 37.*
- **Утверждения:**
  - ст. 13, строки 314–330: `SO_RCVBUF`/`SO_SNDBUF` = 1 МБ через `ListenConfig.Control`, «позволяет приемнику разворачивать Receive Window»;
  - ст. 11, строки 330–338: `SetReadBuffer(1 МБ)` «расширяет окно Flow Control»; строка 416: «ядро выделит **2 МБ** оперативной памяти… передавайте половину»;
  - ст. 14, строки 218, 333: `SetReadBuffer(4 МБ)` «критично»; ст. 37, строки 267–268: `SetReadBuffer(1<<20)`, `SetWriteBuffer(1<<20)`;
  - ст. 25, раздел «TCP и Kernel Buffers»: «`rmem_max`… соединение разорвётся» (Sonnet).
- **Почему проверять:**
  1. Явный `SO_RCVBUF`/`SO_SNDBUF` выключает автотюнинг (`tcp_moderate_rcvbuf`, `SOCK_RCVBUF_LOCK`) для этого сокета; на каналах с большим BDP это скорее ухудшает, чем улучшает. В ст. 13 опция ставится на **слушающий** сокет — проверить, что принятые сокеты наследуют размер и флаг блокировки.
  2. Значение ограничивается `net.core.rmem_max`/`wmem_max` (без `SO_RCVBUFFORCE` и `CAP_NET_ADMIN`) и удваивается ядром. «Ядро выделит 2 МБ памяти» — это лимит учёта, а не аллокация.
  3. Автотюнинг на машине судьи может поднять окно до `tcp_rmem[2]` = 32 МиБ.
- **[улика судьи]** `/proc/sys/net/core/rmem_max` = 4194304, `/proc/sys/net/ipv4/tcp_rmem` = `4096 131072 33554432`, `tcp_moderate_rcvbuf` присутствует. Внимание: 4 МиБ — значение **дистрибутива/настройки** Fedora 44, а не ядерный дефолт. Sonnet называет 212992 — это ядерный дефолт; фактчекеру сверить формулировку «по умолчанию» с `ip-sysctl.rst`.
- **Решающий источник:** `man 7 tcp` (`SO_RCVBUF`), `man 7 socket` (удвоение, `rmem_max`), `Documentation/networking/ip-sysctl.rst` (`tcp_moderate_rcvbuf`, `tcp_rmem`), `net/core/sock.c` (`sock_setsockopt`, `SOCK_RCVBUF_LOCK`), `net/ipv4/inet_connection_sock.c` / `sk_clone_lock` (наследование).
- **Приоритет: High.**

### J-H12. TLS-клиент: «Handshake не проверяет имя хоста», `PreferServerCipherSuites`, «TLS 1.3 по умолчанию с Go 1.21» (ст. 18, 19) · ФАКТ + УСТАР. + ПРОТИВ.
*Источники: G14, S 18, S 19.*
- **Утверждения:**
  - ст. 18, строки 280–284 и 301–304: «Критически важная проверка: `VerifyHostname`»; интервью — «`Handshake()` на низком уровне `tls.Client` **не проверяет**, для какого домена выдан сертификат»; строка 329 — «всегда проводите валидацию… через `VerifyHostname`»;
  - ст. 19, строка 119 (диаграмма: «проверка VerifyHostname»), строки 94–95: «Сопоставление доменного имени: проверяется SAN» — **ст. 19 противоречит интервью ст. 18**;
  - ст. 18, строка 254 и ст. 19, строка 224: `PreferServerCipherSuites: true`;
  - ст. 18, строки 106 и 253: «В Go 1.21+ TLS 1.3 включен по умолчанию».
- **Почему проверять:** при `InsecureSkipVerify == false` клиент проверяет и цепочку, и имя (`ServerName`) внутри handshake; без `ServerName` handshake завершается ошибкой. Ручной `VerifyHostname` нужен только при `InsecureSkipVerify` с собственной проверкой. TLS 1.3 доступен по умолчанию с Go 1.13 (до 1.14 — с возможностью отключить через GODEBUG); минимальная версия по умолчанию — TLS 1.2. Также «Системный вызов `Handshake()`» (ст. 18, строка 303) — это не системный вызов (J, мелочь).
- **[улика судьи]** `crypto/tls/common.go:737–745` — «PreferServerCipherSuites is a legacy field and has no effect… Deprecated: PreferServerCipherSuites is ignored»; `common.go:1239` — правило минимальной версии TLS 1.2 при `MinVersion == 0`.
- **Решающий источник:** `src/crypto/tls/handshake_client.go` (`verifyServerCertificate`, `VerifyOptions.DNSName: c.config.ServerName`); doc `Config.InsecureSkipVerify`; Go 1.13 и 1.14 Release Notes (TLS 1.3); RFC 8446 §4.1.1 (порядок шифров в 1.3).
- **Приоритет: High.**

### J-H13. Отзыв сертификатов и датированные факты PKI (ст. 19) · ФАКТ + УСТАР.
*Источники: S 19.*
- **Утверждения:** ст. 19, строки 89–92 — отзыв (CRL/OCSP, OCSP Stapling) описан как часть процедуры верификации, которую выполняет «Go-клиент»; строка 316 — «В Go проверка [отзыва] настраивается через `x509.VerifyOptions`».
- **[улика судьи]** `crypto/x509/verify.go:547` — «WARNING: this function doesn't do any revocation checking».
- **Почему проверять:** проверку отзыва в Go нужно писать самому (`VerifyPeerCertificate`/`VerifyConnection` + `x/crypto/ocsp` или `x509.ParseRevocationList`). Датированные факты (Sonnet, [✔ web], судья **не** проверял): Let's Encrypt отключил OCSP 06.08.2025; CA/B Forum SC-081 — 200 дней с 15.03.2026, 100 — с 15.03.2027, 47 — с 15.03.2029; Chrome Root Program v1.8 — clientAuth EKU. Для статьи 2026 года «OCSP Stapling — современный стандарт» устарело.
- **Решающий источник:** `crypto/x509/verify.go`; letsencrypt.org/2025/08/06/ocsp-service-has-reached-end-of-life; cabforum.org (Ballot SC-081v3); Chrome Root Program Policy v1.8.
- **Приоритет: High** (отзыв), **Medium** (даты).

### J-H14. HTTP/3 и QUIC: пакеты, фреймы, формулы, congestion control (ст. 23, 24, 44) · ФАКТ + API + ПРОТИВ. (часть — C-FIX)
*Источники: S 23, S 24, S 44, G19.*
- **Утверждения:**
  - `golang.org/x/net/http3` как путь к HTTP/3: ст. 23, строки 165, 229 — **противоречит** строке 81 той же статьи (исправлено в `d9b00f4f`); ст. 44, строка 148;
  - ст. 23, строка 69: «Приложение Go —HTTP/2 Frames→ QUIC Layer»; QPACK не упомянут;
  - ст. 24, строка 183: «Congestion Control: по умолчанию используется **BBRv2** (в quic-go настраивается)»; строка 27 (диаграмма) — то же;
  - ст. 24, строка 181: `PTO = RTT + 4 * SmoothedRTT + MaxAckDelay`;
  - ст. 24, строка 143: «отправитель должен ждать `WINDOW_UPDATE`»;
  - ст. 24 (Sonnet): «при QUIC теряем TSO/GRO/checksum offload»; ст. 23: сервер только с h3 без `Alt-Svc`/HTTPS RR и без TCP-fallback; «0-RTT: сервер валидирует после handshake»; «hole punching встроен в quic-go»; «CID 64 бита».
- **Почему проверять:** HTTP/3 имеет собственные фреймы (RFC 9114) и QPACK (RFC 9204), фреймы HTTP/2 по QUIC не ходят. RFC 9002 §6.2.1: `PTO = smoothed_rtt + max(4·rttvar, kGranularity) + max_ack_delay`. В QUIC управление потоком — `MAX_DATA`, `MAX_STREAM_DATA`, `MAX_STREAMS`, `*_BLOCKED`. Дефолтный CC в RFC 9002 — NewReno-подобный; в quic-go — проверить по коду. UDP GSO (Linux 4.18) и GRO (5.0) используются реализациями QUIC. Браузер узнаёт о h3 из `Alt-Svc` или DNS HTTPS RR (RFC 9460). CID — от 0 до 20 байт.
- **Решающий источник:** RFC 9000 (§17 заголовки, §19 фреймы), RFC 9002, RFC 9114, RFC 9204, RFC 9460; `github.com/quic-go/quic-go/internal/congestion` (какие алгоритмы есть и какой по умолчанию); `src/net/http` Go 1.27.1 (есть ли публичный HTTP/3 — Sonnet: только внутренние хуки).
- **Приоритет: High.**

### J-H15. HTTP/2 Rapid Reset: чем Go защищается на самом деле (ст. 22, строка 245) · ФАКТ + API
*Источники: G23, S 22, J.*
- **Утверждение:** «В Go защита: обязательное обновление рантайма, а также жесткая настройка параметров `http2.Server.MaxHeaderListSize` и `http2.Server.ReadHeaderBufferSize`».
- **[улика судьи]**
  - Полей нет (см. J-H5).
  - `x/net@v0.59.0/http2/server.go:2251–2266` — `scheduleHandler`: число одновременно работающих обработчиков ограничено `advMaxStreams`, остальные ставятся в очередь; если очередь больше `4 × advMaxStreams`, соединение закрывается с `ENHANCE_YOUR_CALM` (`too_many_early_resets`).
- **Конфликт брифов:** Gemini описывает фикс как «внутренний рейт-лимитер кадров сброса потока (`MaxRSTFrameRate` / скользящее окно)». В исходнике этого нет. Sonnet («учёт живых обработчиков») совпадает с кодом (§ 3, K5).
- **Также проверить:** версии с исправлением (Go 1.20.10 / 1.21.3, `x/net` v0.17.0, CVE-2023-39325 для Go и CVE-2023-44487 как общий); отсутствие упоминания CONTINUATION Flood (CVE-2023-45288, Go 1.21.9/1.22.2) — ПРОПУСК.
- **Решающий источник:** Go security announcement (golang-announce, 2023-10-10); `x/net/http2/server.go`; go.dev/issue/63417.
- **Приоритет: High.**

### J-H16. Формулы TCP и параметры ядра: RTO, delayed ACK, Cubic β (ст. 12, 13) · ФАКТ + ПРОТИВ. (часть — C-FIX)
*Источники: S 12, S 13, J.*
- **Утверждения:**
  - ст. 12, строки 104–105: `RTO = SRTT + max(K, DELAYED_ACK_TIME) × 4`, где `K = 4 × RTTVAR`;
  - ст. 12, строка 182: «в ядре Linux константа `TCP_DELACK_MAX` составляет около **40 мс**»; строки 200, 215: «таймер `tcp_delack_max` (40 мс)»; строка 339: `sysctl`-параметры `tcp_rto_min`, `tcp_delack_max`; строка 344: `sysctl -w net.ipv4.tcp_delack_min=1` и `tcp_delack_max=1`;
  - ст. 13, строки 142 и 257: Cubic «β ≈ 0.2, окно уменьшается на 20%, сохраняя 80%»; формула `K = ∛(W·β/C)` (Sonnet);
  - ст. 13, строка 180: авторы BBR «…**Кевин** Якобсон»; строка 206: «принцип неопределенности Клейнрока».
- **Почему проверять:** RFC 6298: `RTO = SRTT + max(G, K·RTTVAR)`, K = 4. В ядре `TCP_DELACK_MIN` = HZ/25 (40 мс), `TCP_DELACK_MAX` = HZ/5 (200 мс) — в тексте имена перепутаны. Cubic: β_cubic = 0.7 (окно → 70%), `K = ∛(W_max·(1−β)/C)`, C = 0.4 (RFC 8312 → RFC 9438; в Linux `beta = 717/1024`). Ван Якобсон (Van Jacobson). «Принцип неопределённости» у Клейнрока — проверить; скорее это метафора авторов BBR.
- **Конфликт с Sonnet:** Sonnet пишет «в mainline таких sysctl нет; `rto_min` — per-route; у сокета — только `TCP_USER_TIMEOUT`». **Это устарело** (§ 3, K2). [улика судьи] на ядре 7.2.8 есть `/proc/sys/net/ipv4/tcp_rto_min_us` (= 200000) и `tcp_rto_max_ms`; в `/usr/include/linux/tcp.h:143–144` — опции сокета `TCP_RTO_MIN_US` (45) и `TCP_DELACK_MAX_US` (46). Sysctl-имён `tcp_rto_min`, `tcp_delack_min`, `tcp_delack_max` по-прежнему нет — в этом Sonnet прав.
- **Решающий источник:** RFC 6298, RFC 9438; `include/net/tcp.h` (константы); `Documentation/networking/ip-sysctl.rst` (`tcp_rto_min_us` — с какой версии ядра); `include/uapi/linux/tcp.h` и changelog ядра (`TCP_RTO_MIN_US`, `TCP_DELACK_MAX_US` — с какой версии); `net/ipv4/tcp_cubic.c`; статья BBR (ACM Queue, 2016) — список авторов.
- **Приоритет: High.**

### J-H17. Статья 14 (UDP): усечение датаграмм, `Connect`, `SetReadBuffer`; ст. 9: «`message too long` при `Write`» · ФАКТ + API + КОД
*Источники: G21, S 14, S 9, J.*
- **Утверждения:**
  - ст. 14: «Буфер 1500 байт (стандартный Ethernet MTU) гарантирует чтение целого пакета без усечения»;
  - ст. 14, строки 140, 146, 359–361: `UDPConn` встраивает `IPConn`; `conn.Connect(addr)` (см. J-H5);
  - ст. 14, строка 150: `connect` «ускоряет отправку на 10–15%» — ЧИСЛО;
  - ст. 9, строки 126–129, 403: UDP > MTU → `message too long` при вызове `Write`.
- **Почему проверять:** датаграмма UDP бывает до 65 507 байт (IPv4), на `lo` MTU 65 536. Если буфер меньше, ядро молча отбрасывает хвост, а `ReadFromUDP` возвращает `n = len(buf)`, `err = nil`; флаг `MSG_TRUNC` виден только через `ReadMsgUDP`. `EMSGSIZE` возвращается при `IP_PMTUDISC_DO` (DF) или размере > 65 507, иначе датаграмма фрагментируется.
- **Улики:** эксперимент Sonnet: датаграмма 3000 байт, буфер 1500 → `n=1500, err=nil`. **Оговорка судьи:** эксперимент Sonnet с записью 1500 байт выполнен по `lo` (MTU 65 536), поэтому он **не доказывает** поведение на интерфейсе с MTU 1500. Нужен повтор на veth с MTU 1500 и с `IP_PMTUDISC_DO`.
- **Решающий источник:** `man 7 udp`, `man 7 ip` (`IP_MTU_DISCOVER`), `src/net/udpsock.go`, `udpsock_posix.go`; эксперимент в netns.
- **Приоритет: High.**

### J-H18. Листинги, которые делают не то, что заявлено (кластер C-LOGIC) · КОД
*Источники: G3, G5, G6, G9, G12, G13, G26, G28, S 25, S 27, S 33, S 35, S 43.*

| Ст., строки | Что заявлено | Что делает код | Источник | Приор. |
|---|---|---|---|---|
| 27: 165, 195, 255 | «`FlushInterval = 0` включает немедленный flush; `> 0` буферизует до таймаута» | ровно наоборот: 0 — без периодического flush; < 0 — после каждой записи; для SSE и `ContentLength == -1` — всегда сразу | S 27; **[улика судьи]** `net/http/httputil/reverseproxy.go:141–151, 666–681` | **High** |
| 40: 155–158 | `BaseContext` кладёт `start_time` «для запросов» | `BaseContext` вызывается **один раз** на `Serve(listener)`: у всех запросов одно время старта сервера; ключ — строка (`go vet`/staticcheck SA1029) | G12, S 40; **[улика судьи]** `net/http/server.go:3541` | **High** |
| 25: 232–268 | «`<-r.Context().Done()` — клиент отключился» в WebSocket-хендлере | после `Hijack` контекст запроса не отменяется при разрыве клиента, пока хендлер работает; читатель при ошибке молча выходит; писатель узнаёт о разрыве только по ошибке ping | G6, S 25 (✔ exp: ждали 1,5 с) | **High** |
| 43: 263–285 | ключ идемпотентности `uuid.New()` внутри `CreateOrder` | новый ключ на каждый вызов — внешний ретрай создаёт дубль; ключ должен создаваться один раз на бизнес-операцию | G28, S 43; Stripe «Idempotent Requests», IETF draft Idempotency-Key | **High** |
| 33: 86–138 | per-IP лимитер как защита от DDoS | карта `limiters` растёт без очистки (миллионы IP / IPv6 → OOM); `global.Allow()` вызывается **до** per-IP, так что отклонённые per-IP запросы тратят глобальный бюджет | G3 (OOM), S 33 (порядок); прошлый фактчек правил этот листинг (§ 5) | **High** |
| 43: 190–235 | Half-Open: «Разрешаем один запрос для проверки» | `case 2` возвращает `true` для **всех** запросов до первого `Record*` | G5, S 43; Fowler «CircuitBreaker», `sony/gobreaker` (`MaxRequests`) | Medium |
| 26: 150–180 | «Пример корректной работы с двунаправленным стримингом» | функция выходит после цикла `Send`, не дожидаясь `Recv() == io.EOF`; ответы теряются, если вызывающий отменит `ctx` | G9; gRPC «Basics — Go», `route_guide` (`waitc`) | Medium |
| 21: 169–183 | `Set("Transfer-Encoding","chunked")`; «`w.Write()` автоматически форматирует чанки при наличии заголовка» | заголовок лишний: Go сам удаляет его и включает chunked, если нет `Content-Length`; без `Flush` данные сидят в буфере — для «стриминга» это главное | G13, S 21; **[улика судьи]** `net/http/server.go:1509–1538` (`delHeader("Transfer-Encoding")`, `te == "chunked"`) | Medium |
| 35: 309–322 | `runContinuousProbe(ctx, …)` | `for range ticker.C` не смотрит на `ctx`; `wg.Wait()` недостижим | G26, S 35 | Medium |
| 35: 49–… и pingOnce | ICMP ping | читается первый пришедший ICMP без проверки ID/Seq; `ID: 0`; ошибки `ResolveIPAddr`/`Marshal` игнорируются; нужны root/`CAP_NET_RAW` (см. J-H19) | S 35, G27 | Medium |
| 17: 255–300 | `lookupWithTimeout` + «изолированный резолвер» | функция зовёт `net.LookupIP` (глобальный резолвер), а созданный в `main` резолвер используется отдельно; горутина висит до конца lookup; `Dial` жёстко шлёт `"udp"` — fallback на TCP при `TC` ломается | G15, S 17 | Medium |
| 2: блок с 122 | сервер с graceful shutdown | `SetReadDeadline` вне цикла: соединение умирает через 30 с независимо от активности; `io.EOF` логируется как ошибка; `ctx` не используется (Sonnet) | S 2 | Medium |
| 30: 186–190 | lock-free round-robin на `int64` | переполнение теоретически возможно, практически — через сотни лет (§ 8, G4) | G4 | Low |

- **Решающий источник:** doc и исходники соответствующих пакетов; для каждого листинга — минимальный прогон.
- **Приоритет:** см. столбец.

### J-H19. Raw-сокеты, ICMP и привилегии (ст. 35) · ФАКТ + API
*Источники: S 35, G27.*
- **Утверждения:** ст. 35, строка 111: «Сырые сокеты блокируют системный тред (M) до завершения `sendto`/`recvfrom`… без `runtime.LockOSThread`… scheduler blocking»; строки 363–364: «Go не поддерживает `IP_HDRINCL` в стандартной `net` из-за ограничений безопасности»; «если пакет не приходит, тред (M) блокируется в ядре». Листинги `icmp.ListenPacket("ip4:icmp", …)` без слов о правах.
- **Почему проверять:** в stdlib есть `net.ListenIP`/`net.DialIP`, и они работают через netpoller, как обычные сокеты. `golang.org/x/net/ipv4.RawConn` даёт `IP_HDRINCL`. Для `"ip4:icmp"` нужны root или `CAP_NET_RAW`; без них на Linux работает `icmp.ListenPacket("udp4", …)` при подходящем `net.ipv4.ping_group_range`.
- **Решающий источник:** `src/net/iprawsock.go`, `iprawsock_posix.go`; godoc `x/net/icmp` (`ListenPacket` — про «udp4»), `x/net/ipv4` (`RawConn`); `man 7 raw`, `man 7 icmp` (`ping_group_range`).
- **Приоритет: High.**

### J-H20. Kubernetes Service Discovery и L4-балансировка долгоживущих соединений (ст. 26, 29, 30, 41) · ФАКТ + ПРОПУСК
*Источники: S 30, S:X13, G20.*
- **Утверждения:**
  - ст. 30, строка 89: «При запросе `svc.default.svc.cluster.local` CoreDNS возвращает список IP подов»;
  - ст. 30, строка 259: совет «использовать `ExternalIPs` или Headless Services с `publishNotReadyAddresses: true`»;
  - ст. 41, строки 150–181: клиент с `MaxIdleConnsPerHost: 100` к ClusterIP — без слов о залипании (G20).
- **Почему проверять:** ClusterIP-сервис в DNS — **один VIP**; список подов отдаёт только headless-сервис. `publishNotReadyAddresses: true` публикует **неготовые** поды — для балансировки это вредно. kube-proxy балансирует на уровне L4 при установлении соединения; долгоживущие HTTP keep-alive и особенно HTTP/2/gRPC остаются на одном поде (решения: headless + `dns:///` + `round_robin`, xDS, mesh, ограничение жизни соединения). Ни одна статья этого не объясняет (S:X13, G20).
- **Уточнение к Sonnet:** формат имени `svc.default.svc.cluster.local` сам по себе допустим (`svc` может быть именем сервиса). Ошибка — в «списке IP подов», не в формате.
- **Решающий источник:** kubernetes.io «DNS for Services and Pods», «Service» (headless, `publishNotReadyAddresses`), «Virtual IPs and Service Proxies»; grpc.io «Load Balancing in gRPC».
- **Приоритет: High.**

### J-H21. VLAN: «тег 802.1Q уменьшает MTU до 1496» (ст. 9, строки 119, 126, 224, 401) · ФАКТ
*Источники: S 9.*
- **Почему проверять:** IEEE 802.3ac (1998) увеличил максимальный кадр до 1522 байт, чтобы тег не съедал payload; VLAN-интерфейс `eth0.10` в Linux по умолчанию имеет MTU 1500. Расчёт «1426 байт» в строке 224 построен на этой ошибке.
- **Решающий источник:** IEEE 802.3ac / 802.1Q; `ip link add link eth0 name eth0.10 type vlan id 10 && ip link show eth0.10`.
- **Приоритет: High.**

### J-H22. Диагностика: `mtr` и `dig` (ст. 35) · ФАКТ
*Источники: S 35.*
- **Утверждения:** строка 355 — «потери на hop-2 исчезают на hop-3 → проблема на сетевом оборудовании [провайдера]»; строка 171 — «> 512 байт → флаг `DO`» (см. J-H7).
- **Почему проверять:** потери только на промежуточном хопе, которые не продолжаются дальше, — обычно ICMP rate limiting на control plane маршрутизатора. Значимы потери, которые сохраняются до конечного узла.
- **Решающий источник:** `man mtr`; RIPE NCC / Cisco «Understanding mtr / traceroute»; RFC 4443 §2.4 (rate limiting ICMPv6), RFC 1812.
- **Приоритет: High.**

### J-H23. Прокси: nginx `splice`, HAProxy «однопоточный» и «TCP в user-space», Envoy в Linkerd (ст. 28) · ФАКТ + ПРОТИВ.
*Источники: S 28, S 42.*
- **Утверждения:** ст. 28, строки 59, 81, 157, 179: «`nginx` использует `sendfile()` и `splice()`… `splice` для `aio` и `tcp_nopush`»; строки 111–115: HAProxy — «single-threaded event loop», «Один основной поток», «реализует часть логики TCP в user-space (управление окном перегрузки, ACK)»; строка 122: Envoy — «стандарт для Service Mesh (Istio, **Linkerd**)», «написанный на C++ и LLVM».
- **Почему проверять:** в nginx нет `splice` (есть `sendfile`, и тот не работает поверх TLS без kTLS и при проксировании). HAProxy многопоточен с 1.8, `nbthread` по умолчанию равен числу CPU (с 2.x); TCP — ядерный. Linkerd использует свой прокси на Rust (`linkerd2-proxy`) — ст. 42, строки 138–145 говорят об этом верно, отсюда противоречие.
- **Решающий источник:** nginx docs (`sendfile`, `aio`, `tcp_nopush`) и исходники (`grep splice`); HAProxy Configuration Manual (`nbthread`), release notes 1.8 / 2.0; linkerd.io architecture.
- **Приоритет: High.**

### J-H24. Service Mesh: «Go dial'ит `127.0.0.1:15001`», port exhaustion на sidecar (ст. 42) · ФАКТ
*Источники: S 42.*
- **Утверждения:** строки 153, 157, 214: «Вызов `http.Transport` превращается в соединение к `127.0.0.1:15001`», «Если Go-приложение открывает много соединений к `127.0.0.1:15001`, ephemeral port pool может исчерпаться… `SO_REUSEPORT`… UDS (в Linkerd…)»; интервью строка 218 про `SO_LINGER=0` у sidecar.
- **Почему проверять:** при `REDIRECT` приложение подключается к исходному адресу назначения; ядро перенаправляет соединение, Envoy узнаёт адрес через `SO_ORIGINAL_DST`. Для приложения это прозрачно. «sidecar использует `SO_LINGER=0`» — без источника (S 42: «выдумка»).
- **Решающий источник:** Istio docs «Traffic interception» / `istio-iptables`; Envoy `original_dst` listener filter; `iptables-extensions(8)` (REDIRECT).
- **Приоритет: High.**

### J-H25. «SSE строится на HTTP Upgrade» (ст. 25, строки 9, 101) · ФАКТ
*Источники: S 25.*
- **Почему проверять:** SSE — обычный ответ `text/event-stream` на GET, без `Upgrade` и без `101`. Не упомянуты ограничения EventSource (только GET, нельзя задать заголовки) и лимит ≈ 6 соединений на origin в HTTP/1.1.
- **Решающий источник:** WHATWG HTML Living Standard, раздел «Server-sent events».
- **Приоритет: High.**

### J-H26. «`IdleConnTimeout` обязан быть > 2·MSL (60 с)» (ст. 39, строки 151, 216) · ФАКТ
*Источники: G25, S 39.*
- **Почему проверять:** idle-таймаут пула клиента не связан с `TIME_WAIT`. Практическое правило противоположное: `IdleConnTimeout` клиента должен быть **меньше** keep-alive таймаута сервера или балансировщика, иначе клиент пишет в уже закрытое соединение (EOF / reset). Итог ст. 39 (строка 216) превращает ошибку в правило.
- **Решающий источник:** doc `http.Transport.IdleConnTimeout`; AWS ALB «Connection idle timeout»; nginx `keepalive_timeout`; go.dev/issue про гонку закрытия idle-соединений (найти).
- **Приоритет: High** (повышен с Low у Gemini).

### J-H27. «Go на edge: нет GC-пауз, нет escape-анализа; упаковка в eBPF/FFI» (ст. 31, строки 121–122, 258) · ФАКТ
*Источники: S 31.*
- **Почему проверять:** у Go есть сборщик мусора с паузами STW (короткими, но есть); escape-анализ выполняет компилятор. Go не «упаковывается в eBPF». Для edge реально используют TinyGo или `GOOS=wasip1`.
- **Решающий источник:** go.dev/doc/gc-guide; `go build -gcflags=-m`; TinyGo docs.
- **Приоритет: High.**

### J-H28. Модель планировщика в статье о DDoS (ст. 33, строки 142, 225–227) · ФАКТ
*Источники: S 33.*
- **Утверждения:** «Планировщик Go не может создать новые P, если ОС не может выделить файловые дескрипторы»; «используйте `context.Background()` или **пул контекстов**»; «мьютекс переходит в состояние фаззинга (futex)».
- **Почему проверять:** число P задаётся `GOMAXPROCS` и с файловыми дескрипторами не связано. Пула контекстов в Go нет, и `context.Background()` вместо таймаута — вредный совет. «Фаззинг» — видимо, искажённое «starvation mode»; проверить `sync/mutex.go` и `runtime/sema.go` (на Linux парковка горутины идёт через планировщик, а не напрямую через futex).
- **Решающий источник:** `src/runtime/proc.go` (`procresize`), `src/sync/mutex.go`, `src/runtime/sema.go`.
- **Приоритет: High.**

### J-H29. Заголовки HTTP: канонизация и `Header.Get` (ст. 20, строки 297, 321) · ФАКТ
*Источники: S 20.*
- **Утверждения:** строка 321 — «Если клиент прислал `authorization: Bearer xyz`, прямой доступ `r.Header["Authorization"]` вернет `nil`»; строка 297 — «`r.Header.Get("X-Custom")` вернёт только первое значение, **склеенное через запятую**».
- **Почему проверять:** сервер канонизирует ключи входящих заголовков, поэтому `r.Header["Authorization"]` найдёт значение, а `r.Header["authorization"]` — нет (Sonnet, ✔ exp). `Header.Get` возвращает первое значение без склейки.
- **Решающий источник:** doc `http.Header.Get`, `textproto.MIMEHeader.Get`, `net/textproto/reader.go` (`ReadMIMEHeader`, канонизация); эксперимент.
- **Приоритет: High.**

### J-H30. Ответ клиента после `resp.Body.Close()`: соединение возвращается в пул «всегда» (ст. 21, строки 102–107, 240–245) · ФАКТ + ПРОПУСК
*Источники: S 21, S:§3 (пропуск «дренаж тела»).*
- **Почему проверять:** соединение возвращается в пул, только если тело вычитано до EOF; иначе `Close` закрывает соединение. Главная ловушка клиента (`io.Copy(io.Discard, resp.Body)` перед `Close`) в модуле не описана. Описание таймера idle («netpoller пробуждает горутину-управляющую») тоже стоит сверить: в `transport.go` это `time.AfterFunc` → `closeConnIfStillIdle`.
- **Решающий источник:** doc `http.Response.Body`, `http.Client.Do`; `src/net/http/transport.go` (`bodyEOFSignal`, `earlyCloseFn`, `tryPutIdleConn`, `closeConnIfStillIdle`).
- **Приоритет: High.**

---

## 3. Конфликты между брифами, ложные срабатывания и решающие улики

| # | Тема | Gemini | Sonnet | Решающая улика | Вывод судьи |
|---|---|---|---|---|---|
| K1 | `epoll_pwait` в рантайме (ст. 1, строки 163, 169; ст. 15, строка 312) | — | «runtime вызывает `EpollWait` (не `epoll_pwait`/`pwait2`)»; «фраза бессмысленна» | **[улика судьи]** `internal/runtime/syscall/linux/syscall_linux.go:32` — `Syscall6(SYS_EPOLL_PWAIT, …, 0, 0)` | Sonnet частично ошибся: системный вызов **именно `epoll_pwait`**, но с нулевой маской, поэтому обоснование «для маскировки сигналов» в ст. 1 неверно. `epoll_pwait2` действительно не используется (ст. 38:170 — ошибка). |
| K2 | sysctl и опции сокета для RTO и delayed ACK (ст. 12) | — | «в mainline таких sysctl нет; `rto_min` — per-route; у сокета — `TCP_USER_TIMEOUT`» | **[улика судьи]** ядро 7.2.8: `/proc/sys/net/ipv4/tcp_rto_min_us`, `tcp_rto_max_ms`; `/usr/include/linux/tcp.h:143–144` — `TCP_RTO_MIN_US`, `TCP_DELACK_MAX_US` | Sonnet прав про имена `tcp_rto_min`/`tcp_delack_min`/`tcp_delack_max` (их нет), но **устарел** про «нет ни sysctl, ни опции сокета»: в современных ядрах такие ручки есть, в микросекундах. Фактчекеру — установить версии ядра по `ip-sysctl.rst` и changelog. |
| K3 | Netpoller «масштабируется дополнительными epoll-инстансами» (ст. 38, строка 82) | цитата с «дополнительных epoll-инстансов» | «лимит fd в netpoller» | `grep` по ст. 38: строка 82 — «имеет лимит на количество отслеживаемых FD… динамически масштабируется» | Ошибка в тексте есть (лимита у netpoller нет, epfd один), но Gemini приписал тексту слова, которых там нет. Цитировать по строке 82. |
| K4 | Где учат «включайте `SetNoDelay(true)`» | ст. 10, 11, **12** | ст. 10, 11, 37, 44; ст. 12, 21 верны | ст. 12, строки 226–228, 342 | Gemini неверно включил ст. 12. Список: 10, 11, 37, 44. |
| K5 | Механизм защиты Go от Rapid Reset (ст. 22) | «рейт-лимитер RST (`MaxRSTFrameRate`, скользящее окно)» | «учёт живых обработчиков» | **[улика судьи]** `x/net/http2/server.go:2251–2266` | Прав Sonnet. Плюс поля из статьи не существуют (J). |
| K6 | Приоритет round-robin на `int64` (ст. 30) | High: паника при переполнении или «инициализации −1» | — | поле приватное, стартует с 0; 2⁶³ инкрементов недостижимы | Понижено до Low (§ 8). |
| K7 | Приоритет `IdleConnTimeout > 2·MSL` (ст. 39) | Low | High | строка 216 — правило вынесено в итоги | High. |
| K8 | `LookupNetIP` как «zero-alloc» замена (G15) | «zero-alloc метод… без аллокаций срезов в куче»; `Resolver.LookupIP(ctx, …)` «с Go 1.8» | — | `LookupNetIP` возвращает `[]netip.Addr` (срез в куче); **[улика судьи]** `api/go1.8.txt` — `Resolver.LookupIPAddr`; `api/go1.15.txt` — `Resolver.LookupIP`; `api/go1.18.txt` — `LookupNetIP` | Претензия к листингу ст. 17 верна (горутина + `select` не нужны, резолвер принимает `ctx`), но аргументы Gemini завышены: «zero-alloc» неверно, версия 1.8 — для `LookupIPAddr`, не `LookupIP`. |
| K9 | Путь к коду, поднимающему `RLIMIT_NOFILE` (ст. 33) | — | «`os/rlimit.go` [проверить файл]» | **[улика судьи]** `os/rlimit.go` не существует; код в `syscall/rlimit.go` (`init`, `Cur = Max − 1`) | Утверждение Sonnet верно, источник — `syscall/rlimit.go`; версия — Go 1.19 (проверить по release notes). |
| K10 | DNS «Go 1.11» в ст. 16 | — | X5: «Ст.16 («Go 1.11»)» | `grep "Go 1.11"`: только ст. 6, строка 330 (`ListenConfig.Control`, это верно — Go 1.11) | В ст. 16 «Go 1.11» нет (удалено `d9b00f4f`). Пункт X5 в этой части снять. |
| K11 | `svc.default.svc.cluster.local` (ст. 30) | — | «формат `<svc>.<ns>.svc.cluster.local`» | `svc` может быть именем сервиса | Формат допустим; ошибка — в «списке IP подов» для ClusterIP (J-H20). |
| K12 | Эксперимент UDP 1500 по `lo` (ст. 9) | — | «✔ exp: запись по `lo` без ошибки» | MTU `lo` = 65 536 | Эксперимент не опровергает утверждение для MTU 1500. Вывод Sonnet, скорее всего, верен (EMSGSIZE только при DF), но улику надо заменить экспериментом на veth с MTU 1500. |

---

## 4. Сквозные кластеры (одна проблема в нескольких статьях)

Кластеры, полностью разобранные в § 2, здесь только названы: **C-NODELAY** (J-H1), **C-KEEPALIVE** (J-H2), **C-NETPOLL** (J-H4), **C-API** (J-H5), **C-COMPILE** (J-H6), **C-DNS** (J-H7), **C-ERRNO** (J-H8), **C-POOL** (J-H9), **C-REUSE** (J-H10), **C-SOCKBUF** (J-H11), **C-LOGIC** (J-H18).

### C-LISTEN. Цепочка `net.Listen`/`Dial` на уровне системных вызовов · ФАКТ + ПРОТИВ.
*Источники: S 2, S 8, S 15, S 37, S 39.*
- ст. 2: `socket(AF_INET, SOCK_STREAM, IPPROTO_TCP)`, `O_NONBLOCK` ставится после; «под капотом вызывается системный вызов `net.Listen`»; ст. 8, 15, 37 — диаграммы с `bind 0.0.0.0`; ст. 39, строка 122 — `sysSocket -> bind -> listen`; ст. 15, строка 199 — «`listen(5)`: ядро пропустит до `somaxconn`», «somaxconn по умолчанию 128»; ст. 4, строка 164 описывает dual-stack верно.
- **Почему проверять:** для `":8080"` на Linux с IPv6 создаётся `AF_INET6` с `IPV6_V6ONLY=0`, флаги `SOCK_NONBLOCK|SOCK_CLOEXEC` передаются прямо в `socket()`. Очередь = min(backlog, somaxconn); Go сам передаёт backlog, прочитанный из `/proc/sys/net/core/somaxconn`. Дефолт `somaxconn` — 4096 с Linux 5.4 (до этого 128). **[улика судьи]** на машине судьи `somaxconn` = 4096.
- **Решающий источник:** `strace -f -e trace=network` на минимальном сервере; `src/net/sock_posix.go`, `sock_linux.go` (`maxListenerBacklog`), `ipsock_posix.go` (`favoriteAddrFamily`); коммит ядра 5.4 о `SOMAXCONN`.
- **Приоритет: Medium** (ст. 15:199 — High: прямо неверное правило про backlog).

### C-TIMEWAIT. Длительность и природа `TIME_WAIT` · ФАКТ + ПРОТИВ.
*Источники: S 2, S 34, S 39, S 44.*
- ст. 2, строка 194: «двухминутного таймаута сокетов в `TIME_WAIT`» — против ст. 10:217, 39:28, 39:214, 44:121 (60 с). ст. 44: «Cancel → TIME_WAIT»; ст. 34: «ESTABLISHED, tcpdump пуст → TIME_WAIT»; ст. 39: «bind: address already in use как симптом клиента» (у клиента — `EADDRNOTAVAIL`, «cannot assign requested address»).
- **Решающий источник:** `include/net/tcp.h` (`TCP_TIMEWAIT_LEN`), RFC 9293.
- **Приоритет: Medium.**

### C-GOVER. Версии Go, привязанные наугад · УСТАР.
*Источники: S:X11, S 12, S 13, S 18, S 27, S 33, S 44, J.*

| Ст., строка | В тексте | Проверить | Улика |
|---|---|---|---|
| 12: 298 | `SetKeepAlivePeriod` «с Go 1.16» | Go 1.2 | **[улика судьи]** `api/go1.2.txt` |
| 18: 106, 253 | TLS 1.3 по умолчанию «с Go 1.21» | Go 1.13/1.14 | release notes |
| 44: 71 | ET-режим «Go 1.22+» | ET давно | `git log` по `netpoll_epoll.go` |
| 13 | `Transport.ReadBufferSize/WriteBufferSize` «Go 1.19» | Go 1.13 | **[улика судьи]** `api/go1.13.txt` |
| 27: 252 | HTTP/2 к бэкендам «Go 1.11+» | h2-клиент с Go 1.6; `ForceAttemptHTTP2` — Go 1.13 | **[улика судьи]** `api/go1.13.txt` |
| 33: 195 | «В Go 1.21+ появился новый сервер» | нет такого события | release notes |
| 39: 127 | «В Go 1.21+ планировщик использует `netpoll` для асинхронного приема» | netpoll в accept с ранних версий | — |
| 40: 145 | `ReadHeaderTimeout` «Go 1.8» | верно | **[улика судьи]** `api/go1.8.txt` |
| 12: 135 | `Temporary()` deprecated «с Go 1.18» | верно | release notes 1.18 |
| 18 | `GOMAXPROCS` «по физическим ядрам» | Go ≥ 1.25 учитывает cgroup | release notes 1.25 |
| 33 | `RLIMIT_NOFILE` | Go 1.19 поднимает soft limit | `syscall/rlimit.go` |
| 22, 27 | h2c только через `x/net/http2/h2c` | Go 1.24: `Protocols.SetUnencryptedHTTP2` | **[улика судьи]** `api/go1.24.txt` |

- **Приоритет: Medium** (каждая по отдельности).

### C-EXT. Устаревшие факты о внешних системах (дата-зависимые) · УСТАР.
*Источники: S:X11, S 19, S 25, S 28, S 41, S 42.*
- ingress-nginx выводится из поддержки (объявлено, окончание — март 2026), рекомендация — Gateway API (ст. 28, 41); kube-proxy: режим nftables GA в 1.33, IPVS deprecated в 1.35 (ст. 41: «два режима, IPVS категорически лучше»); Linkerd: с 2.15 нет open-source stable-релизов (ст. 42); Weave Net прекращён (ст. 41); `nhooyr.io/websocket` → `github.com/coder/websocket`, gorilla архивировалась в 2022 и возродилась в 2023 (ст. 25); OCSP/сроки сертификатов (ст. 19, J-H13); RFC 7234 → RFC 9111 (ст. 31), RFC 793 → RFC 9293 (ст. 11), RFC 8312 → RFC 9438 (ст. 13), RFC 1631 → RFC 3022 (ст. 8); Telia Carrier → Arelion (ст. 7).
- **Судья не проверял.** Источники у Sonnet: kubernetes.io/blog/2026/01/29/ingress-nginx-statement/, linkerd.io/2024/02/21/announcing-linkerd-2.15/, Kubernetes 1.33/1.35 release notes.
- **Указание:** в тексте фиксировать «актуально на дату».
- **Приоритет: Medium.**

### C-ECMP. ECMP в Linux · ФАКТ
*Источники: S:X9, S 6, S 7, S 9.*
- «одинаковые prefix+metric → ECMP по 5-tuple» (ст. 6); в Linux IPv4 ECMP — один маршрут с несколькими `nexthop`; второй такой же маршрут → `EEXIST` (для IPv6 — «append» объединяет). Политика хэша по умолчанию — L3 (`fib_multipath_hash_policy = 0`).
- **Решающий источник:** `ip-route(8)`, `ip-sysctl.rst` (`fib_multipath_hash_policy`).
- **Приоритет: Medium.**

### C-INTERNALS. «Фрагменты из исходников», которые не совпадают с исходниками · ФАКТ
*Источники: S:X14, S 10, S 11, S 18, S 22, S 24, G19.*
- ст. 18: поля `tls.Conn` (`handshakeStatus`, кольцевой `rd.buf`, `gcmCipher`) — реально `isHandshakeComplete atomic.Bool`, `rawInput`, `input`, `hand`, `halfConn in/out`; ст. 22: `http2.conn`, `framer`, `streamMap`, `hpack.Entry`, «динамическая таблица — LRU» — реально `serverConn`, `Framer`, `streams map`, таблица — FIFO-срез; ст. 24: `poll.FD` «из quic-go»; ст. 10, 11: `struct tcp_sock` «в `include/net/tcp.h`» — она в `include/linux/tcp.h`; ст. 10, строка 121: «изменение полей требует `LOCK CMPXCHG`» — поля меняются под socket lock; ст. 20: «нет interning; парсер — FSM».
- **Решающий источник:** `src/crypto/tls/conn.go`, `x/net/http2/server.go`, `x/net/http2/hpack/tables.go`, `src/net/textproto/reader.go`; `include/linux/tcp.h`.
- **Приоритет: Medium.**

### C-NUM. Числа без источника · ЧИСЛО
*Источники: S:X10, S по статьям.*
- «переключение горутин 10–20 нс», «M освобождается за 15 нс» (ст. 1: 161, 234); «3 DupACK ⇒ >99.9% потеря» (ст. 12: 92); «ndots: +10–50 мс» (ст. 16); «+500–1000 мс ndots»; «снижение GC 30–50%» (ст. 18), «60–70%» (ст. 23: 111); «CPU −40–60%» (ст. 22); «~0.5% overhead» NIC offload (ст. 9); «40+ Mpps», «iptables 1–3 мкс», «XDP 25–50 нс» (ст. 36); «connect ускоряет на 10–15%» (ст. 14: 150); «NUMA в 3–4 раза» (ст. 3); «фрагментация −30–50%» (ст. 3); «TCAM < 10 нс» (ст. 7: 290); «OSPF сходится за 10–50 мс» (ст. 7); «~10–20 МБ RAM Linkerd» (ст. 42: 138); «2–5 мс на handshake» (ст. 19); `tcp_retries2=15` «13–30 мин» (≈ 924,6 с; ст. 12).
- **Указание:** для каждого числа — источник или пометка «оценка автора / зависит от железа». Это не ошибки по умолчанию: часть чисел — правдоподобные порядки.
- **Приоритет: Medium/Low.**

### C-HISTORY. История и атрибуции · ФАКТ / МНЕНИЕ
*Источники: S 2, S 7, S 13, S 14, S 16, S 21.*
- «TCP/IP рождён в Bell Labs» (ст. 2, строка 13), «`net/http` спроектирован гениями Bell Labs» (ст. 21, строка 7), «OSPF исповедует подход Bell Labs» (ст. 7, строка 176) — к TCP/IP и OSPF Bell Labs отношения не имеет (Cerf/Kahn, DARPA, BBN, Stanford; реализация сокетов — Berkeley). «Кевин Якобсон» (ст. 13). Апокрифические цитаты Эйнштейна/Кнута (ст. 14), выдуманная цитата про HOSTS.TXT (ст. 16). Эпиграфы — по § 11.3 AGENTS.md переведены на русский; фактчекеру проверить атрибуцию, а не язык.
- **Приоритет: Medium** (Bell Labs как происхождение TCP/IP), Low (остальное).

### C-MARKUP. Разметка и навигация · РАЗМЕТКА (не факт)
*Источники: S:X12, S 4, J.*
- Повреждённый LaTeX в ст. 4, строки 57, 64, 110: `\approx` и `\times` превратились в управляющие символы (`pprox`, `	imes`) — экранирование `\a` и `\t`.
- Пустой блок кода `SO_BINDTODEVICE` в ст. 3, строки 255–258 (G18): только два комментария вместо кода; плюс «требует `CAP_NET_RAW`» (с Linux 5.7 не требуется, если сокет ещё не привязан — S 3) и «через `golang.org/x/net/ipv4`» (такой опции там нет).
- Wikilinks с неверным адресатом: ст. 4 (MSS → ст. 21/22, PMTUD → ст. 39), ст. 7 (CNI → ст. 8), ст. 10 (анонс следующей статьи не совпадает с реальной ст. 11), ст. 36 → 37 обещает qdisc/NAPI, но ст. 37 их не раскрывает.
- Диаграмма ст. 22, строка 66 («4 КБ макс») противоречит тексту строки 87 (16 384 байт).
- **Указание:** это задача редактора, не фактчекера; но пустой блок кода и LaTeX надо исправить.
- **Приоритет: Medium** (пустой блок, LaTeX), Low (wikilinks).

---

## 5. Остатки прошлого фактчека `d9b00f4f` (C-FIX): проверить только остаток

Прошлый фактчек правил точечно. Ниже — места, где исправленная строка соседствует со старой, или где сама правка внесла ошибку.

| # | Ст. | Что исправлено в `d9b00f4f` | Что осталось или появилось | Действие |
|---|---|---|---|---|
| F1 | 44 | «пул тредов 1024» → «считывая за один вызов пачку **до 1024** готовых событий» (строка 104) | **Новая ошибка:** массив событий — 128 (`netpoll_epoll.go:117`). Ст. 44, строка 71 — «Go 1.22+ ET» | исправить число, сверить версию |
| F2 | 12 | `sysctl tcp_rto_min` → `ip route … rto_min` (строки 130–133) | строка 339 — `tcp_rto_min` как sysctl; строки 182, 200, 215, 344 — `tcp_delack_max`/`tcp_delack_min`; «`TCP_DELACK_MAX` ≈ 40 мс» (это `TCP_DELACK_MIN`) | J-H16 |
| F3 | 12 | `Temporary()` заменён комментарием (строки 134–136) | новый совет «для retry-логики проверяйте… `errors.Is(err, context.Canceled)`» — отменённую операцию не повторяют | исправить совет |
| F4 | 16, 17, 30, 44 | «Go кэширует DNS» → «не кэширует» в ст. 17, 30, 44 | ст. 16, строки 178–179 и 221 — «Встроенный кэш с дедупликацией… `sync.Map`» | J-H7 |
| F5 | 21 | строка 59: «`MaxIdleConnsPerHost` по умолчанию… = 2» | строка 230 той же статьи: «по умолчанию `MaxIdleConnsPerHost = 100`» | J-H9 |
| F6 | 23 | строка 81: «нативной поддержки HTTP/3 нет… стандарт — `quic-go/http3`» | строки 165 и 229: «`golang.org/x/net/http3`» | J-H14 |
| F7 | 33 | лимитер: глобальный лимит вынесен из карты | карта без очистки; порядок `global` → per-IP | J-H18 |
| F8 | 35 | `icmp.ListenNetwork` → `icmp.ListenPacket`, буфер чтения | нет слов о `CAP_NET_RAW`; ID/Seq не проверяются; `runContinuousProbe` без `ctx` | J-H18, J-H19 |
| F9 | 9 | порт VXLAN 4785 → 4789; «в ранних реализациях ядра… 8472» | 8472 — не «ранние реализации», а текущий дефолт модуля `vxlan` (параметр `udp_port`) и Flannel/Cilium; Calico — 4789 (S 9). Проверить по `drivers/net/vxlan/vxlan_core.c` | Medium |
| F10 | 41 | строка 149: про keep-alive в пуле | «AWS NLB, GCP Cloud NAT, Azure LB… через **350–1000** секунд» — AWS NLB 350 с; GCP Cloud NAT established — 1200 с; Azure LB — 4 мин по умолчанию (S 8, S 12, S 41). Проверить по документации провайдеров | Medium |
| F11 | 42 | опечатка «proxi» → «прокси» в интервью (строка 218) | содержание ответа (`SO_LINGER=0` у sidecar) не проверялось | J-H24 |

Также проверить, что исправления `d9b00f4f` в ст. 1/2/38 (неблокирующий режим через `SOCK_NONBLOCK`/`fcntl`) не противоречат ст. 38, строка 47 («`O_NONBLOCK` (или `FIONBIO` на Windows)») — формулировки близки, это скорее согласовано.

---

## 6. Medium по статьям (слитый перечень)

Формат: **утверждение (строка, если найдена)** → что проверить · тип · источник. Пункты, уже разобранные в § 2–5, здесь даны ссылкой.

### Ст. 1. Обзор раздела
- Ловушка 1 (`net.Conn`) → J-H3. Ловушка 2 «висит вечно» (строка 190) → J-H2 (keepalive 15 с; `SetDeadline` нужен для прикладного idle). Ловушка 3 (строка 192) → J-H7; там же `ndots:0` (CONTEXT-DEPENDENT).
- `EPOLL_CTL_MOD` (144), `epoll_pwait` (163, 169), `webPoller` (172), `netpollBlock … runtime.stopm` (177) → J-H4.
- «стек потока ОС 2–8 МБ, 10 000 клиентов — мгновенная смерть» (строки 96, 161) → это виртуальная память; NPTL держит 10k+ потоков; Java `-Xss` по умолчанию 1 МБ; ст. 2 пишет «1–8 МБ» · ФАКТ + ПРОТИВ. · `ulimit -s`, JVM docs.
- «горутина ~2 КБ» на соединение → на соединение `net/http` уходит заметно больше (bufio 4+4 КБ, структуры conn); начальный стек с Go 1.19 адаптивный · УПРОЩ.

### Ст. 2. OSI и TCP/IP
- Цепочка `net.Listen` → C-LISTEN. «двухминутный TIME_WAIT» (194) → C-TIMEWAIT.
- «Zero-Copy: через `syscall.Splice`; `net/http` по умолчанию классическое копирование» (237–238 и далее) → Go сам применяет `sendfile` (`io.Copy` из `*os.File` в `*TCPConn`, `http.ServeContent` по plain TCP через `response.ReadFrom`) и `splice` (TCP↔TCP/Unix); по TLS — нет · ФАКТ · `src/net/sendfile_linux.go`, `splice_linux.go`, `net/http/server.go` (`(*response).ReadFrom`).
- Листинг сервера (блок с 122) → J-H18 + неиспользуемый `fmt` (J-H6).
- «TCP/IP рождён в Bell Labs» (13) → C-HISTORY.
- Таблица OSI: 5-й уровень = `context` (19) · МНЕНИЕ/УПРОЩ.

### Ст. 3. Ethernet
- «Go читает интерфейсы из `/sys/class/net/` (или Netlink); Windows — `GetAdaptersInfo`» (197) → Linux — только netlink, Windows — `GetAdaptersAddresses`; ст. 9 пишет верно · ФАКТ + ПРОТИВ. · **[улика судьи]** `net/interface_linux.go:17,124` (`NetlinkRIB`), `interface_windows.go:24`.
- «tun/tap — чистые IP-пакеты без L2» → TAP — L2 с MAC, TUN — L3 · ФАКТ.
- «GRO и GSO объединяют мелкие кадры в 64 КБ» (подано как checksum offload; 325) → GRO — приём, GSO — отправка; TSO/LRO/BIG TCP не разведены · ФАКТ.
- «io_uring — kernel-bypass» (8 или 325) → io_uring — асинхронный интерфейс ядра, не bypass · ФАКТ.
- Пустой блок `SO_BINDTODEVICE` (255–258) → C-MARKUP; G18.
- «ECONNREFUSED из-за FDB exhaustion» (12) → C-ERRNO.

### Ст. 4. IP
- Путь приёма: «TTL проверяется/декрементируется на приёме до маршрутизации; PREROUTING после route lookup» → TTL — в `ip_forward`; `NF_INET_PRE_ROUTING` — до routing decision; ст. 32 рисует верно · ФАКТ + ПРОТИВ. · `net/ipv4/ip_input.c`, `ip_forward.c`.
- «опции IP → cache line split TCP-портов» → выравнивание определяется `NET_IP_ALIGN`/`sk_buff` · ФАКТ.
- «Smurf или Teardrop эксплуатировали баги сборки фрагментов» (213) → Smurf — амплификация ICMP на broadcast; фрагментационные — Teardrop, Ping of Death · ФАКТ.
- `netip.Addr` «хранит `[4]byte` или `[16]byte`», `IPv4()/IPv6()` (299), «zero-alloc» → `uint128` + `unique.Handle` (24 байта); методов нет; zone ломает zero-alloc · ФАКТ + API · **[улика судьи]** `net/netip/netip.go:53,56`.
- `syscall.WriteMsgUDP … MSG_MORE` (205) → J-H5.
- Teredo/6to4 как актуальные (166) → 6to4 deprecated (RFC 7526), Teredo вымер; актуальны 6rd, NAT64/464XLAT, DS-Lite · УСТАР.
- «маршрутизаторы вынуждены фрагментировать» → в IPv6 маршрутизаторы не фрагментируют (PMTUD, ICMPv6 PTB, min MTU 1280); в IPv4 при DF — drop + ICMP · ФАКТ.
- LaTeX (57, 64, 110) → C-MARKUP.

### Ст. 5. ARP и NDP
- «IPv4 использует таблицы `arp_tables`» (369) → `arp_tables` — фильтр arptables; ARP — `net/ipv4/arp.c` + `net/core/neighbour.c` · ФАКТ.
- «`x/net/ipv4`, `ipv6` дают интерфейс к `RTM_GETNEIGH`»; «`getifaddrs` для таблицы соседей» → это `x/sys/unix`/`vishvananda/netlink`; `getifaddrs` — адреса интерфейсов · API.
- Переполнение neighbour-таблицы (340) → C-ERRNO; пороги даны только для IPv4, `net.ipv6.neigh.default.gc_thresh*` и дефолты 128/512/1024 не названы · ПРОПУСК.
- «`connect()`: ядро переводит горутину в ожидание ARP» → Go делает non-blocking connect (`EINPROGRESS`), SYN ждёт в `arp_queue`; ядро о горутинах не знает · ФАКТ.
- GARP «обнаружение конфликтов IP»; «коммутаторы обновляют IP→MAC» → DAD в IPv4 — ARP Probe (RFC 5227); коммутатор хранит MAC→порт; VRRP — виртуальный MAC · ФАКТ.

### Ст. 6. Маршрутизация
- ECMP → C-ECMP.
- Route cache «до 2.6.38» (300) и «с 3.6 ликвидирован» (302) → кэш удалён в 3.6; «до 2.6.38» противоречит · ПРОТИВ. · LWN «The IPv4 routing cache removal».
- «горутины читают FIB без локов» → про ядро (RCU), не про горутины · ФАКТ.

### Ст. 7. RIP, OSPF, BGP
- Интервью «пропал default route → no route to host» (401) → C-ERRNO.
- «OSPF сходится за 10–50 мс без потери TCP» → типично сотни мс — секунды (SPF/LSA throttle, hello/dead 10/40 с без BFD) · ЧИСЛО.
- «ядро выбирает по Administrative Distance» (104) → в ядре Linux AD нет (metric/protocol); AD — понятие Cisco, в FRR — distance, в BIRD — preference · ФАКТ.
- «tc/iproute2 делегируют правила в TCAM NIC; TCAM < 10 нс; SmartNIC LPM» (288–303) → FIB-TCAM — в ASIC коммутатора (switchdev, флаг `offload`); tc-flower offload — flow-правила · ФАКТ.
- «группируйте IP в CIDR, чтобы `fib_trie` был в L1 и `net.Dial` быстрее» (415) → один lookup на connect, далее `sk_dst_cache` · МНЕНИЕ/ФАКТ.
- Интервью: `SO_BINDTODEVICE` «через `unix.Bind` / netlink» → это `setsockopt` · API.
- «в поде `ip route` покажет 127.0.0.1/8 и 169.254.169.254/32» → 127/8 в таблице `local`; 169.254.169.254 не универсален · ФАКТ.
- «Calico/Cilium построены на BGP» (12) → BGP опционален; Cilium по умолчанию VXLAN/Geneve · ФАКТ.

### Ст. 8. NAT
- conntrack full → `no route to host` (156, 361) → C-ERRNO.
- IPv6: «каждому поду /64», «conntrack больше не нужен», «port exhaustion растворяется» (319, 364) → под получает /128 из podCIDR /64 ноды; stateful firewall и kube-proxy используют conntrack; исчерпание — по 4-tuple · ФАКТ.
- «AWS NAT GW и GCP Cloud NAT режут до 350 с» (97) → 350 с — AWS NAT GW; GCP Cloud NAT established — 1200 с · ФАКТ · AWS/GCP docs.

### Ст. 9. VLAN и VXLAN
- 1496 → J-H21. `message too long` → J-H17.
- «inter-VLAN routing идёт через CPU/ядро» → L3-коммутатор маршрутизирует в ASIC · ФАКТ.
- «dev физически не может попасть в prod на L2» → VLAN hopping (DTP, double tagging) · ФАКТ.
- Интервью «UDP исключает дедлоки в сетевом стеке ядра» → источника нет · ФАКТ (проверить).
- NetworkPolicy drop → `ECONNREFUSED`/`network unreachable` (391); «sidecar → 503» → C-ERRNO; Envoy RBAC deny → 403 · ФАКТ.
- 8472 → § 5, F9.

### Ст. 10. TCP
- Nagle → J-H1. Keepalive → J-H2. `SO_REUSEADDR/SO_REUSEPORT` против port exhaustion (249) → J-H10; `tcp_tw_recycle` удалён в 4.12 — не упомянут.
- «изменение `snd_una`… требует `LOCK CMPXCHG`» (121); «`tcp_sock` в `include/net/tcp.h`» (115) → C-INTERNALS.
- «фоновый тред netpoller в `epoll_wait`» → J-H4.
- `SetReadDeadline` «переводит сокет в состояние ошибки» (336) → дедлайн можно продлить; соединение остаётся рабочим · ФАКТ · doc `net.Conn.SetDeadline`.

### Ст. 11. Handshake, Flow Control, Congestion
- `SetReadBuffer(1 МБ)` «расширяет окно»; «Window = Buffer − Used»; удвоение (330–338, 416) → J-H11; объявляемое окно — часть буфера (`tcp_adv_win_scale`, `scaling_ratio`).
- «клиент пишет быстрее сервера → `ECONNRESET`» → при живом пире ядро ждёт (persist timer); без ответа — `ETIMEDOUT`; нужен `SetWriteDeadline` · ФАКТ.
- SYN flood: «`tcp_synack_timer`», лог «possible SYN flooding … Dropping request» (84–87) → такого sysctl нет (`tcp_synack_retries`, `tcp_max_syn_backlog`); актуальный лог «…Sending cookies. Check SNMP counters.» · ФАКТ · `net/ipv4/tcp_input.c` (`tcp_syn_flood_action`).
- `somaxconn = 65535` (308) как рецепт → C-LISTEN.
- Листинг (342–358): `conn.(*net.TCPConn)` без проверки, а ниже — с проверкой · КОД (мелочь).

### Ст. 12. Retransmission, Keep-Alive, Nagle, Delayed ACK
- RTO, delayed ACK, sysctl → J-H16, § 5 F2. Keepalive → J-H2. `errors.Is(err, context.Canceled)` для retry → § 5 F3.
- «3 DupACK ⇒ >99.9% потеря» (92) → C-NUM; не упомянуты SACK, RACK-TLP (RFC 8985), PRR (RFC 6937), F-RTO · ФАКТ/ПРОПУСК.
- `tcp_retries2=15` «13–30 мин» → ≈ 924,6 с · ЧИСЛО · `ip-sysctl.rst`.
- «Четыре условия Нагла» (167–171) → п. 3 «буфер отправки полностью свободен» и п. 4 сформулированы неточно (RFC 896 / RFC 1122 §4.2.3.4) · УПРОЩ.
- NAT-таймауты «5–15 минут» (289) → AWS 350 с, GCP 1200 с, Azure 4 мин · ЧИСЛО.

### Ст. 13. Reno, Cubic, BBR
- Cubic β, BBR авторы, «принцип неопределённости» → J-H16. SO_RCVBUF в листинге → J-H11 (G10).
- «BBR требует `fq`» → с 4.13 есть внутренний TCP pacing; `fq` желателен · ФАКТ.
- «BBR v2/v3» как доступные (245) → в mainline только BBRv1 · УСТАР./ФАКТ · `net/ipv4/tcp_bbr.c`.
- «cwnd исчерпан → `write(2)` возвращает `EAGAIN`» (353, 376) → `EAGAIN` при полном sndbuf; `EPOLLOUT` зависит от `sk_stream_wspace`, не от cwnd · ФАКТ.
- «BBR: нулевая чувствительность к потерям; P99 в разы; Cubic 1–2 с на трансконтинентальных» → BBRv1 игнорирует потери до порога, несправедлив к Cubic; в ДЦ — DCTCP/ECN · ЧИСЛО/МНЕНИЕ.
- `cubic_ack` → в ядре `bictcp_*` · API (ядро).

### Ст. 14. UDP
- → J-H17, J-H5. `SetReadBuffer(4 МБ)` (218, 333) → J-H11.
- «Prometheus push-gateway» как UDP-протокол (322) → Pushgateway работает по HTTP/TCP; DTLS ретрансмитит только handshake · ФАКТ.

### Ст. 15. Порты и сокеты
- Интервью `SO_REUSEADDR` через `syscall.ListenConfig` (170–184) → J-H10, J-H5.
- backlog/somaxconn (196–208) → C-LISTEN (High).
- «Ephemeral ports 49152–65535» (21) → рекомендация IANA; Linux — 32768–60999 (ст. 10, 39 пишут верно) · ПРОТИВ.
- «Фоновый поток… `epoll_wait`» (312) → J-H4; опечатка `epoll_ctl(epoll_ctl,…)` (Sonnet) · РАЗМЕТКА.
- `close()` с непрочитанными данными шлёт RST — не упомянуто; `SetLinger(0)` вместо `SetsockoptLinger` (375–382) · ПРОПУСК/API.

### Ст. 16. DNS
- Кэш, 512, macOS/Windows → J-H7.
- Интервью «`DialContext` висит дольше дедлайна» (241–245) → объяснение размытое; реально — `timeout × attempts × серверы × search × (A+AAAA)` из `resolv.conf` · ФАКТ · `net/dnsclient_unix.go`, `dnsconfig_unix.go`.
- «В серьёзных production никогда не полагайтесь на `net.DefaultResolver`» (250) + захардкоженный `8.8.8.8:53` → ломает split-horizon, CoreDNS, air-gap · МНЕНИЕ, вредный совет.
- ndots «+10–50 мс» → C-NUM; не названы 5-секундные таймауты из-за гонки UDP в conntrack, NodeLocal DNSCache, `single-request` · ПРОПУСК.

### Ст. 17. DNS под капотом
- Противоречия со ст. 16 → J-H7, § 5 F4. Листинг → J-H18 (G15).
- «CNAME-цепочки убивают latency» → цепочку разворачивает рекурсор; клиенту — один round-trip · ФАКТ.
- «cgo на Alpine — аварийно/утечки» → собирается; не запускается бинарник, собранный под glibc; реальные отличия musl (search/ndots, TCP-fallback до musl 1.2.4) · ФАКТ.
- ndots: «`api` → 5 запросов» → при 3 search-доменах `api.default.svc…` находится с первого раза; пример ст. 16 точнее · ФАКТ.
- «Кэширование… на базе `sync.Map`» (246) — это совет, не утверждение о stdlib; ок.

### Ст. 18. TLS
- → J-H12. Внутренности `tls.Conn` → C-INTERNALS.
- «`sync.Pool` для Record Layer и `cipher.AEAD`… снизило нагрузку на GC 30–50%» (164) → C-NUM; проверить, используется ли `sync.Pool` в `crypto/tls` · ФАКТ.
- «`Close` нужен, иначе fd зависнет навсегда» → у `netFD` есть финализатор (недетерминированно) · УПРОЩ.
- `GOMAXPROCS` «по физическим ядрам» → C-GOVER.
- Не упомянуты: X25519MLKEM768 по умолчанию (Go 1.24), ECH, отсутствие 0-RTT поверх TCP · ПРОПУСК.

### Ст. 19. PKI, mTLS
- → J-H12, J-H13.
- «при `CGO_ENABLED=1` крипто делегируется системным библиотекам» → нет (только BoringCrypto/FIPS-сборки) · ФАКТ.
- «`ClientSessionCache` → 0-RTT/1-RTT без асимметрии» → Go не поддерживает 0-RTT в TLS поверх TCP; PSK-DHE оставляет ECDHE · ФАКТ.
- «2–5 мс на handshake» → C-NUM.
- `openssl x509 -text` как проверка цепочки → нужен `openssl verify` или `s_client -verify_return_error` · ФАКТ.

### Ст. 20. HTTP/1.1
- → J-H29, J-H5 (`Request.Context`), J-H6 (`time`).
- «`MaxBytesReader` — защита от Slowloris» → лимит объёма; против Slowloris — `ReadHeaderTimeout` · ФАКТ.
- «пул горутин; `Request` на connection» → горутина на соединение, `Request` на запрос · ФАКТ.
- «нет interning; парсер — FSM» → `textproto` интернирует частые ключи (`commonHeader`), `ReadMIMEHeader` — одна аллокация · ФАКТ.
- `Server: Golang/1.24` в примере ответа (106, 152) → `net/http` не отправляет `Server` по умолчанию · ФАКТ.
- Пример с `r.Context().Done()` (260) — проверить, что это не после Hijack.

### Ст. 21. HTTP/1.1 под капотом
- → J-H9, J-H18 (chunked), J-H30, § 5 F5.
- «Nagle 200–400 мс; Go ставит `TCP_NODELAY` на keep-alive соединениях» (163) → NODELAY ставится на все TCP-соединения · УПРОЩ.
- «TCP keepalive — 2 часа» (283) → J-H2; гонка закрытия idle (EOF): `IdleConnTimeout` клиента < keep-alive сервера/LB → J-H26.
- Pipelining: «Go никогда не поддерживал его полноценно» (230) → сервер обрабатывает конвейер последовательно; клиент — нет · УПРОЩ.

### Ст. 22. HTTP/2
- → J-H15, J-H5. Внутренности → C-INTERNALS.
- «PRIORITY — дерево приоритетов» → схема deprecated в RFC 9113, замена — RFC 9218 · УСТАР.
- «h2c через `x/net/http2/h2c`; h2 только с TLS» → Go 1.24+: `Protocols.SetUnencryptedHTTP2`; кастомный `DialContext`/`TLSClientConfig` отключает авто-h2 (нужен `ForceAttemptHTTP2`) · УСТАР.
- Диаграмма «4 КБ макс» (66) → C-MARKUP.
- Чётные stream ID инициирует сервер (push); ALPN в TLS 1.3 — в EncryptedExtensions · проверить формулировки · Low.

### Ст. 23. HTTP/3 и QUIC
- → J-H14, § 5 F6.
- «0-RTT: сервер валидирует после handshake» (131, 151) → сервер обрабатывает 0-RTT данные сразу; защита от replay — на прикладном уровне · ФАКТ · RFC 9001 §4.6, RFC 8470.
- «CID 64 бита»; миграция без PATH_CHALLENGE/RESPONSE → CID 0–20 байт · ФАКТ · RFC 9000 §5.1, §9.
- «hole punching встроен в quic-go (ICE/STUN)» → нет · ФАКТ.
- «CC настраивается только через sysctl» → `TCP_CONGESTION` per-socket (противоречит ст. 12) · ФАКТ.
- PMTU/фрагментация → DF, Initial ≥ 1200, DPLPMTUD (RFC 8899) · ПРОПУСК.
- `sync.Pool` «−60–70%» (111), «2–5 мкс», метрика `http3_server_round_trip_duration_seconds`, `MSG_DONTWAIT` → C-NUM / выдумано.

### Ст. 24. Deep Dive QUIC
- → J-H14, J-H5 (`poll.FD`).
- ASCII Long/Short Header (`0xQUIC`; в short нет Length; DCID без длины) → RFC 9000 §17 · ФАКТ.
- «ACK кодирует потерянные»; «ECN-Echo» → ACK ranges перечисляют полученные; ECN — ECT/CE + ACK_ECN · ФАКТ.
- «после миграции теряются ключи» → нет · ФАКТ.
- Буферы «32 КБ – 1 МБ» в quic-go → пакеты ≤ ≈ 1452 Б (буферы под MTU) · ФАКТ.
- «Gen0 GC», `asyncpreemptoff=1` «только для критических путей» (274) → у Go GC нет поколений; GODEBUG — на процесс целиком · ФАКТ.
- Интервью: `ackHandler`, `retransmissionBuffer`, `retransmitPacket` (294) — сверить имена с quic-go · API.

### Ст. 25. WebSocket и SSE
- → J-H3 (gorilla), J-H18 (ctx после Hijack), J-H25 (SSE).
- «Go проверяет заголовок и подтверждает 101» → это делает библиотека; после Hijack сбрасываются дедлайны; `Shutdown` не ждёт hijacked-соединения; в HTTP/2 нет `Hijacker` · ФАКТ · **[улика Sonnet]** `server.go` (`Hijack` → `SetDeadline(zero)`).
- «nginx/HAProxy WebSocket настроены по умолчанию» (321) → в nginx нужны `proxy_http_version 1.1`, `Upgrade`/`Connection`, `proxy_read_timeout` · ФАКТ.
- «`rmem_max` → соединение разорвётся» → нет, zero window · ФАКТ.
- `WriteTimeout` убивает SSE → `ResponseController.SetWriteDeadline` (Go 1.20) · ПРОПУСК.
- «Регистры и L1/L2 не инвалидируются при переключении контекста» (286) → МНЕНИЕ/УПРОЩ.

### Ст. 26. gRPC
- «Контекст транслируется в HTTP/2 фреймы `GOAWAY` или `CANCEL`» (150–151) → отмена — `RST_STREAM(CANCEL)`; дедлайн передаётся заголовком `grpc-timeout`; `GOAWAY` — про соединение · ФАКТ (понижено до Medium: следующая фраза в тексте говорит про `RST_STREAM`).
- «`MaxCall{Recv,Send}MsgSize` — flow control»; «`WithInitialConnWindowSize` → несколько соединений» → это лимиты размера сообщения (4 МБ на приём); окна — `InitialWindowSize/InitialConnWindowSize`, BDP-estimator · ФАКТ.
- «`connPool`; `KeepaliveParams` с `MinTime`» (225) → `connPool` нет; `MinTime` — серверный `EnforcementPolicy` (GOAWAY `too_many_pings`) · API.
- «собственный `net/http2`» → `internal/transport` на `x/net/http2` (Framer, hpack) · ФАКТ.
- «VLQ»; «zero-allocation»; «reflection в Java/C#» → varint (base-128), zigzag для `sint`; protobuf-go — table-driven · ФАКТ.
- «TLS по умолчанию»; `WithBlock` → deprecated; `grpc.NewClient` · УСТАР.
- bidi-листинг → J-H18 (G9).
- Пропуск L4-балансировки → J-H20.

### Ст. 27. Прокси
- `FlushInterval` → J-H18.
- «тело ответа в отдельной горутине»; «Go 1.18+ chunked» → в той же горутине (отдельные — для upgrade и `maxLatencyWriter`); стриминг всегда · ФАКТ.
- «Go 1.11+ автоматически h2 к бэкендам… устраняет HOL» (252) → h2-клиент с Go 1.6, только по https; кастомный dial отключает; TCP HOL остаётся · ФАКТ + C-GOVER.
- Интервью «`MaxIdleConnsPerHost` — причина деградации» (237) → причина — малое значение по умолчанию (J-H9).
- `Director` и `Rewrite` (198): «в Go 1.20+ добавлен `Rewrite`» — верно, **[улика судьи]** `api/go1.20.txt`.
- Не упомянуты XFF/`Forwarded`, hop-by-hop, PROXY protocol, smuggling, ретраи · ПРОПУСК.

### Ст. 28. nginx, Envoy, HAProxy
- → J-H23.
- «Envoy — стандарт для Istio, Linkerd» (122) → J-H23; «написан на C++ и LLVM» — LLVM тут ни при чём · ФАКТ.
- xDS без EDS/ADS · ПРОПУСК. «Port exhaustion у Go-клиента» → у nginx→upstream; `keepalive`, `proxy_http_version 1.1` · ФАКТ.

### Ст. 29. Балансировка
- Gotcha про Least Connections и keep-alive → логика перевёрнута (проблема — долгоживущие соединения); `least_request`/P2C · ФАКТ.
- Graceful shutdown без preStop и задержки удаления endpoints; «broken pipe и panic» → panic не будет · ФАКТ.
- «`IdleConnTimeout` 90 с» в разделе про сервер (145) → для сервера — `IdleTimeout` · API.

### Ст. 30. Service Discovery
- → J-H20, J-H6 (`context`).
- «TCP state mismatch… use of closed network connection»; «connection refused 80%»; `ErrConnectionClosed` → выдумано (Sonnet) · ФАКТ.
- Код `NewResolver` «контроль TTL»; `ServiceBalancer` «lock-free» при `RLock` + копировании среза на каждый вызов · ФАКТ/МНЕНИЕ.
- **J:** интервью (строка 196): «атомарные операции… работают за несколько тактов CPU и **не вызывают** переключения контекста или блокировку кэш-линий (cache line bouncing) при низкой конкуренции. Mutex включается только при реальном конфликте» → `atomic.AddInt64` — `LOCK XADD`, при конкуренции кэш-линия так же «скачет» между ядрами; «Mutex включается только при конфликте» — бессмысленная формулировка (fast path `sync.Mutex` — тоже один CAS) · ФАКТ · Intel SDM (LOCK prefix), `src/sync/mutex.go`.

### Ст. 31. CDN и Edge
- → J-H27, J-H6 (`encoding/hex`).
- «anycast → наименее загруженный» → ближайший по BGP · ФАКТ.
- RFC 7234 → RFC 9111; не упомянуты RFC 9213 (Targeted Cache-Control), `Cache-Status`, `immutable` · УСТАР.
- `inm == etag` → `If-None-Match` — список, weak ETag, `*`; 304 без `Cache-Control`/`Vary` · КОД.
- «`Vary: Authorization`» → для приватных ответов — `private`/`no-store` · ФАКТ.
- Инвалидация (purge, surrogate keys, shield) · ПРОПУСК.

### Ст. 32. Firewall
- → J-H5 (`net.DialContext`), C-ERRNO.
- `INPUT ACCEPT 22,80; DROP` → ломает ответы на исходящие соединения хоста (нет `ESTABLISHED,RELATED` и `lo`) · КОД.
- nftables-команды (117 и рядом) → проверить синтаксис: `nft add rule ip filter input ip saddr @whitelist accept`; CIDR в set требует `flags interval` · КОД.
- Интервью «telnet работает, Go нет → conntrack» → логическая натяжка (IPv6 vs IPv4, DNS, proxy env, uid-owner) · ФАКТ.
- «Cilium генерирует nftables» → Cilium — eBPF · ФАКТ.

### Ст. 33. DDoS и Rate Limiting
- → J-H18 (лимитер), J-H28.
- «10 000 slow-conn гарантированно убьют память» → ≈ 100 МБ; противоречит ст. 1/2; Go ≥ 1.19 поднимает soft `RLIMIT_NOFILE` (§ 3, K9) · ФАКТ + ЧИСЛО.
- «`ulimit -n` по умолчанию 1024 в Docker» (225) → в Docker обычно наследуется от `dockerd`/containerd (часто 1048576); проверить · ФАКТ.
- «Sliding Window Counter — ложные срабатывания на границе» → это свойство Fixed Window · ФАКТ.
- `MaxHeaderBytes` «защита от Slowloris» → J-H… (см. ст. 20) · ФАКТ.
- «`sync.Mutex` хуже `atomic`… syscall `futex`» (239) → J-H28.

### Ст. 34. tcpdump, ss
- `GODEBUG=netpoll=1`, профиль `syscall` (162) → J-H5.
- Wireshark без расшифровки TLS → `SSLKEYLOGFILE`/`tls.Config.KeyLogWriter`; снятие трафика подов (`nsenter`, `kubectl debug`) · ПРОПУСК.
- «`-n` обязателен»; «`--snapshot-len` — кольцо»; «`tcptrace` — eBPF» → при `-w` резолва нет; кольцо — `-C/-W/-G`; tcptrace — анализатор pcap · ФАКТ.
- «ss O(1)», «ss показывает QUIC», «iowait»; `ss … | grep <pid>` без `-p` · ФАКТ.
- «ESTABLISHED, tcpdump пуст → TIME_WAIT» → чаще idle keep-alive · ФАКТ.
- Строки 116–117: `send-q` в `LISTEN` = backlog — верно; `recv-q` «аналог `SO_RCVBUF`» — неточно · УПРОЩ.

### Ст. 35. ping, traceroute, dig, curl, mtr
- → J-H19, J-H22, J-H7 (dig), J-H18 (листинги), J-H9 (строка 284).
- traceroute-фрагмент: `SetControlMessage` не ставит TTL (нужен `SetTTL`); у `icmp.PacketConn` нет `Fd()` · API.
- `DualStack: true` (251) → deprecated, «Fast Fallback is enabled by default» · УСТАР. (G17, низкий вес).
- eBPF «без `CAP_NET_RAW`» → нужны `CAP_BPF` + `CAP_NET_ADMIN`/`CAP_PERFMON` · ФАКТ.

### Ст. 36. eBPF и XDP
- → J-H5, J-H6 (листинг, `go:generate`).
- «Offloaded Mode: Mellanox ConnectX, Netronome» (133, 247) → аппаратный XDP offload в mainline — практически только Netronome `nfp`; mlx5 — native mode · ФАКТ (понижено с High: периферийно) · `Documentation/networking/` (XDP), список драйверов с `XDP_FLAGS_HW_MODE`.
- `Lookup([]byte("drop_count"), &count)` → тип ключа должен совпадать с объявленным в карте (обычно `uint32`) · КОД.
- «TC после маршрутизации» → TC ingress раньше netfilter и routing · ФАКТ.
- «Размер стека жёстко ограничен 512 байтами» (61) — верно; «DAG без циклов» vs «зациклится → soft lockup» → bounded loops с 5.3, `bpf_loop` с 5.17 · ПРОТИВ./УСТАР.
- Таблица чисел (iptables 1–3 мкс, XDP 25–50 нс, 40+ Mpps) → C-NUM.
- Требования (`CAP_BPF` с 5.8, BTF с 5.2, версии ядра) · ПРОПУСК.

### Ст. 37. Сетевой стек Linux
- → J-H1 (`SetNoDelay`), J-H11 (буферы), J-H4 (поток poller), J-H10 (строка 153).
- «Если данные еще не пришли в `sk_receive_queue`, **процесс блокируется в ядре**» (115) — сказано про Go → противоречит модели non-blocking + netpoller · ФАКТ (понижено с High: одно предложение, рядом верное описание).
- sysctl-комментарии (227–231): `tcp_max_syn_backlog` — не лимит соединений; `ip_local_port_range` не связан с `SO_REUSEPORT`; `tcp_tw_reuse` не уменьшает `TIME_WAIT`; диапазон от 1024 пересекается с портами сервисов (`ip_local_reserved_ports`) · ФАКТ.
- `kmalloc-256/512` для `sk_buff`; `cb[]` и retransmit; `sk_backlog` · Low.
- NAPI/RSS/RPS/RFS/qdisc/BQL обещаны во введении, но не раскрыты (G24, S 37) · ПРОПУСК.

### Ст. 38. Go и сеть
- → J-H4, C-GOVER (`DualStack` в строке 36).
- «утечка при `SetDeadline`»; `http2.Priority`; «STW чаще»; «5–10 тыс. потоков» → проверить формулировки (S 38) · ФАКТ.
- Верно (подтверждено Sonnet): 2 idle на хост по умолчанию; разница `client.Timeout` и `dialer.Timeout`.

### Ст. 39. TIME_WAIT и Port Exhaustion
- → J-H26, J-H10, C-TIMEWAIT.
- Не упомянуты: `tcp_tw_reuse` по умолчанию 2 (только loopback), удаление `tcp_tw_recycle` (4.12), conntrack `time_wait` = 120 с, `IP_BIND_ADDRESS_NO_PORT`, `tcp_migrate_req` · ПРОПУСК.

### Ст. 40. HoL и Slowloris
- → J-H5 (`ServerMetrics`, `MaxConns`), J-H9 (строка 185), J-H18 (`BaseContext`).
- Итог (194): «HTTP/2: потеря пакета влияет только на конкретный stream» → для HTTP/2 поверх TCP неверно, противоречит ст. 10 и 23; верно для HTTP/3 · ФАКТ + ПРОТИВ. (уровень **High** по содержанию; оставлено здесь, т. к. одно предложение в итогах).
- «клиент отвалится по ОС-таймауту 2+ часа» → J-H2; Slowloris-клиент живой · ФАКТ.
- «блокированные в netpoll горутины создают M» → нет · ФАКТ.
- «Когда таймаут срабатывает, `http.Server` вызывает `conn.Close()`, что генерирует событие `read` с ошибкой `EOF`» (188) → дедлайн реализован таймером рантайма, ошибка — `i/o timeout` (`os.ErrDeadlineExceeded`) · ФАКТ.

### Ст. 41. Kubernetes Networking
- → J-H20, C-EXT, § 5 F10.
- «ClusterIP не на интерфейсе» → в IPVS-режиме VIP на `kube-ipvs0`; «iptables O(N) на каждый пакет» → на первый пакет соединения (дальше conntrack) · ФАКТ.
- Интервью «curl NXDOMAIN, wget работает — Go resolver» → curl и wget не используют Go · ФАКТ.
- «Go TCP не умеет эффективно обрабатывать фрагментированные пакеты… CUBIC в Go» (185–186) → сборкой фрагментов и CC занимается ядро · ФАКТ.
- `SetKeepAlive(true)` + `SetKeepAlivePeriod()` «стоит явно настроить» (181) → J-H2.

### Ст. 42. Service Mesh
- → J-H24, J-H23 (противоречие со ст. 28), J-H6 (`context`).
- xDS в Linkerd нет; `linkerd-controller` устарел · ФАКТ.
- «Ambient = eBPF» → ztunnel + waypoint; Tetragon/Kube-OVN/OTel — не mesh; proxyless gRPC (xDS) не упомянут · ФАКТ/ПРОПУСК.
- «обход прокси через явный IP» → перехват iptables не зависит от того, имя это или IP · ФАКТ.
- Не упомянуты: Istio CNI, native sidecar (K8s 1.33 GA — проверить), гонка старта, protocol sniffing · ПРОПУСК.
- «каскадные таймауты» → точнее retry amplification · МНЕНИЕ.

### Ст. 43. Сетевые паттерны
- → J-H18 (CB, idempotency), J-H2 (72000), J-H10 (306, 317), J-H4 (`wakeG`, 42).
- `errors.Is(err, context.DeadlineExceeded)` для ошибок gRPC → нужен `status.Code(err) == codes.DeadlineExceeded` · API.
- «gRPC без retry; `grpc-go/retry`» → встроенный retry через service config (gRFC A6); middleware — сторонний · ФАКТ.
- NATS-листинг: неограниченные горутины, `context.Background()`, нет errgroup · КОД.
- Интервью (строка 151) про `sub.SetPendingLimits` и `sync.Pool` «в Go 1.21+» → `sync.Pool` существует с Go 1.3 · C-GOVER.

### Ст. 44. Итоги
- → J-H1 (170), J-H4 (49, 71, 104), J-H5 (`LookupContext` 134, `http3.Transport` 148), J-H9 (124), J-H10 (169), § 5 F1.
- «Zero-copy без memcpy, если буфер выровнен» → `write` всегда копирует (кроме `MSG_ZEROCOPY`); `net.Buffers` → `writev` · ФАКТ.
- «`Dial` в цикле без `context.Context` гарантированно приведет к утечке горутин» (168) → `Dial` без ctx ограничен ОС-таймаутом connect; «гарантированно» — преувеличение · ФАКТ.
- «Cancel → TIME_WAIT» (172) → `TIME_WAIT` возникает у стороны, закрывшей первой, независимо от ctx · ФАКТ.
- Интервью (162): «Go получает `-EAGAIN` или 0 байт при потере пакетов; `use of closed network connection`» → потери невидимы приложению; видны как задержка, `i/o timeout` или `ETIMEDOUT` · ФАКТ.
- «переключение таблиц страниц при syscall» → при syscall адресное пространство не меняется (KPTI — оговорка) · ФАКТ.

---

## 7. Low (компактно, по статьям)

- **Ст. 1:** BGP поверх TCP/179, OSPF — IP proto 89; «TLB flush при переключении потоков» (потоки одного процесса делят адресное пространство); hand-off при блокирующем syscall не «моментальный» (sysmon retake ≈ 20 мкс – 10 мс); лимит потоков `SetMaxThreads` = 10000 → `fatal: thread exhaustion`.
- **Ст. 2:** TCP-заголовок «20 байт» (минимум; с timestamps 32, SYN до 60); «softirq → steal time» (steal — метрика гипервизора); «O(1) на соединение»; «1000–5000 тактов» смешивает syscall и context switch; «валидирует TTL на приёме».
- **Ст. 3:** MAC `02:xx…` для veth (`eth_random_addr` ставит только local-бит; Docker — `02:42:…`); VXLAN 50 Б для IPv4-underlay (70 для IPv6); VLAN-кадр 1522; «DNS-имена интерфейсов».
- **Ст. 4:** «TTL никогда не измерялся в секундах» (RFC 791 — секунды, на практике хопы, RFC 1812); «IPv4 исчерпан в 2011» (пул IANA; RIPE 2012, ARIN 2015); wikilinks.
- **Ст. 5:** `gc_stale_time`, `delay_first_probe_time`; «NDP Guard» (стандартно — RA Guard, RFC 6105); не упомянуты `arp_ignore/arp_announce/arp_accept/rp_filter`.
- **Ст. 6:** два default с metric 100/200 переключаются только при исчезновении маршрута (carrier loss), при живом линке нужен мониторинг/BFD (229); асимметрия → обычно `rp_filter`, клиент RST на корректный SYN-ACK не шлёт; пример `10.0.1.50/32 via 127.0.0.1 dev lo` нереалистичен; `ip rule`, таблицы `local/main/default`; «32 итерации» vs LC-trie; BGP full view IPv4 уже > 1,0 млн; `IP_TRANSPARENT` требует `CAP_NET_ADMIN` + TPROXY.
- **Ст. 7:** Telia → Arelion (2022); метрика RIP connected = 1 (RFC 2453), диаграмма 154–160 непоследовательна; OSPF reference-bandwidth 100 Мбит/с; нет IS-IS/EIGRP/areas/RFC 7938/RPKI; GoBGP, MetalLB.
- **Ст. 8:** RFC 1631 → RFC 3022; CGNAT/RFC 6598; «ISP гарантированно отбрасывают RFC 1918» (32); «Linux выбирает порт 12345» (сначала пытается сохранить исходный); checksum обновляется инкрементально; IMDSv2; `bind 0.0.0.0` (на деле `[::]`); `netip.Addr.IsPrivate` включает ULA (fc00::/7); `Dialer{KeepAlive:15s}` — не «включение».
- **Ст. 9:** «MTU black hole → рост TIME_WAIT» (на деле ESTABLISHED + ретрансмиты); NIC offload «~0.5% CPU»; `flannel.1` — виртуальное устройство.
- **Ст. 10:** «9 бит флагов» vs 8 на схеме (NS — historic, RFC 8311); «no duplicates благодаря cumulative ACK» (по seq); анонс следующей статьи.
- **Ст. 11:** RFC 793 → RFC 9293; «удвоение буфера — BSD/Go» (удваивает Linux, `socket(7)`); «persist timer 5–60 с»; Reno vs CUBIC/PRR.
- **Ст. 12:** NAT-таймауты провайдеров; `SO_REUSEPORT/BINDTODEVICE` в разделе про пулы (345); TCP_CORK/autocorking не упомянуты.
- **Ст. 13:** ECN/DCTCP/`ss -ti` не упомянуты; цифра «32 Кбит/с → 40 бит/с» (23) — проверить по Jacobson 1988.
- **Ст. 14:** `struct udp_sock` в `include/linux/udp.h`; Go не считает checksum (ядро/NIC); «STW GC — долгая пауза» (328); опущены SO_REUSEPORT для UDP, `recvmmsg/sendmmsg` (`ipv4.PacketConn.ReadBatch`), UDP GSO/GRO, `IP_PKTINFO`, amplification; цитаты Эйнштейна/Кнута.
- **Ст. 15:** `sk_send_queue` (в ядре `sk_write_queue` + `tcp_rtx_queue`); `ip_unprivileged_port_start`; «Registered ports не требуют root».
- **Ст. 16:** «0 RTT» у UDP; Route 53 назван рекурсивным (это авторитетный DNS; рекурсивный — Route 53 Resolver); нет RCODE/AD/CD; `grpc.Dial` (passthrough) vs `NewClient` (dns); HOSTS.TXT — SRI-NIC, цитата.
- **Ст. 17:** «13 anycast-узлов» (13 идентичностей, > 1500 инстансов); порядок QTYPE/QCLASS; «MX сортирует резолвер»; нет SOA/CAA/DNSKEY/SVCB-HTTPS (RFC 9460), negative caching (RFC 2308), serve-stale (RFC 8767).
- **Ст. 18:** SNI открыт без ECH; TLS 1.2 resumption/False Start; сравнения с PHP/Java (29) декоративны; «Системный вызов `Handshake()`» (303, J).
- **Ст. 19:** один `tls.Config` как клиентский и серверный; путь trust store только Debian-like; SPIFFE/SPIRE и ротация не раскрыты.
- **Ст. 20:** фрагмент в Request-URI; формы request-target; CL+TE (smuggling); JSON через `Fprintf("%s")` без экранирования; RFC 2068/2616 → RFC 9110/9112.
- **Ст. 21:** `Max-Forwards`; chunked «для WebSocket»; `Content-MD5` (удалён в RFC 7231); «Bell Labs» (7).
- **Ст. 22:** чётные stream ID; ALPN в EncryptedExtensions; «−40–60% CPU».
- **Ст. 24:** Stream ID биты; ACK Frequency — draft. Верно (Sonnet): новый PN при ретрансмите, PN spaces, `kPacketThreshold = 3`.
- **Ст. 25:** CVE-2011-7008 не подтверждён; сервер не маскирует фреймы (MUST NOT); «32-битная длина» (на деле 7/16/64 бита); Redis Pub/Sub — at-most-once.
- **Ст. 26:** метрики с `_total`; proto3 `optional`/Editions.
- **Ст. 27:** «Nginx — C++/Rust»; «Lua/WSI»; `ReadHeaderTimeout` у `ReverseProxy`.
- **Ст. 28:** `open_file_cache`; Pingora/Caddy/Traefik; QAT/Nitro.
- **Ст. 29:** «L4 не умеет TLS-termination»; DSR/PROXY/IPVS/Maglev не упомянуты.
- **Ст. 30:** «cache stampede»; P2C; SRV; EndpointSlices; G4 (round-robin `int64`).
- **Ст. 31:** `write-through`; TFO; `http2.Transport` в клиенте (авто); xxhash «SIMD».
- **Ст. 32:** «iptables через netlink» (iptables-legacy — `setsockopt`); «nftables близок к BPF»; Docker DNAT/`DOCKER-USER`; AWS NACL; `err == context.DeadlineExceeded` вместо `errors.Is`.
- **Ст. 33:** SYN cookies «включение»; «фаззинг мьютекса»; `EADDRNOTAVAIL` vs `EADDRINUSE` (240).
- **Ст. 36:** `vmlinux.h` не нужен на целевой машине; AF_XDP, uprobes на Go.
- **Ст. 37:** `kmalloc-256/512`; `cb[]` и retransmit; `sk_backlog`; флаги `EPOLLIN|EPOLLET` без `EPOLLOUT|EPOLLRDHUP` (134, 149; J).
- **Ст. 39:** `tcp_max_tw_buckets`; `tcp_time_wait_hash`; `ip_local_reserved_ports`.
- **Ст. 40:** строковый ключ в `context.WithValue`; slow-read/RUDY/zero-window не упомянуты.
- **Ст. 41:** цифры Cilium; veth «копирует»; netns «1–2 КБ»; таймауты NLB/GCP/Azure; `externalTrafficPolicy`, NodeLocal DNSCache.
- **Ст. 42:** порты Linkerd (4143 inbound / 4140 outbound); «нет динамических аллокаций»; hot restart.
- **Ст. 43:** bulkhead, load shedding, hedging, deadline propagation, saga/outbox не раскрыты.

---

## 8. Отклонено или понижено

| # | Находка | Источник | Решение | Улика |
|---|---|---|---|---|
| R1 | Паника round-robin на `int64` (ст. 30) | G4 | понижено High → Low | 2⁶³ инкрементов недостижимы; поле стартует с 0; сценарий «−1» невозможен |
| R2 | «Runtime вызывает не `epoll_pwait`» (ст. 1) | S:X7, S 1 | отклонено в части имени системного вызова | `syscall_linux.go:32` — `SYS_EPOLL_PWAIT` (K1) |
| R3 | «Netpoller создаёт дополнительные epoll-инстансы» как цитата | G7 п. 1 | цитата отклонена, суть (лимит FD) сохранена | ст. 38:82 (K3) |
| R4 | Ст. 12 учит `SetNoDelay(true)` как обязательное | G11 | отклонено для ст. 12 | ст. 12:226–228, 342 (K4) |
| R5 | `LookupNetIP` «zero-alloc», `Resolver.LookupIP` «с Go 1.8» | G15 | аргументы отклонены, претензия к листингу сохранена | `api/go1.15.txt`, `go1.18.txt` (K8) |
| R6 | «`MaxRSTFrameRate`» как фикс Rapid Reset | G23 | отклонено | `x/net/http2/server.go:2251–2266` (K5) |
| R7 | «В ст. 16 — Go 1.11» | S:X5 | отклонено | grep (K10) |
| R8 | «Нет sysctl/опций сокета для RTO_min и delayed ACK» | S 12 | понижено до «имена в тексте неверны» | ядро 7.2.8 (K2) |
| R9 | «Формат `svc.default.svc.cluster.local` неверен» | S 30 | отклонено | K11 |

---

## 9. Важные пропуски (кандидаты на добавление, не ошибки)

| Тема | Где | Что добавить | Источник находки | Приор. |
|---|---|---|---|---|
| Дренаж тела ответа до `Close()` | ст. 21 | `io.Copy(io.Discard, resp.Body)` для переиспользования соединения | S §3 | **High** |
| L4-балансировка долгоживущих соединений (HTTP keep-alive, gRPC/HTTP2) | ст. 26, 29, 30, 41 | ClusterIP/kube-proxy балансируют на SYN; headless + `round_robin`, xDS, mesh, ограничение жизни соединения | G20, S:X13 | **High** |
| `net.KeepAliveConfig` (Go 1.23) | ст. 11, 12, 38, 39 | раздельная настройка idle/interval/count | G22 | Medium |
| Таблица дефолтов Go (NODELAY, keepalive 15 с, REUSEADDR, backlog = somaxconn, `DefaultMaxIdleConnsPerHost = 2`, dual-stack, нет DNS-кэша, EDNS0 1232, нет таймаутов у `http.Client`/`http.Server`) | ст. 1, 20, 21, 40, 44 | одна таблица со ссылками из статей | S §4 | Medium |
| RSS/RPS/RFS, multi-queue NIC, qdisc/BQL | ст. 37 | обещано во введении | G24, S 37 | Medium |
| ECN/DCTCP, `ss -ti`, `nstat` | ст. 13, 34 | диагностика congestion control | S §3 | Medium |
| `Forwarded`/XFF, PROXY protocol, smuggling | ст. 27–29 | модель доверия к IP клиента | S §3 | Medium |
| Alt-Svc / HTTPS RR, fallback при блокировке UDP/443 | ст. 23 | как клиент находит h3 | S §3 | Medium |
| `externalTrafficPolicy`, EndpointSlices, Gateway API, NetworkPolicy | ст. 41 | современный K8s-стек | S §3 | Medium |
| Native sidecar, Ambient, proxyless gRPC | ст. 42 | выбор архитектуры mesh | S §3 | Medium |
| Docker/DNAT и `DOCKER-USER` | ст. 32 | почему INPUT-правила не защищают контейнеры | S §3 | Medium |
| Привилегии и версии ядра для eBPF | ст. 36 | `CAP_BPF` (5.8), BTF, bounded loops | S §3 | Medium |
| CONTINUATION Flood (CVE-2023-45288) | ст. 22 | вторая крупная атака на HTTP/2 | S 22 | Medium |
| Интеграция `RawConn.Read/Write` с netpoller | ст. 38 | как кооперировать свой syscall с поллером | S §3 | Low |

---

## 10. Рекомендации фактчекеру

1. **Начните с того, что проверяется механически** — это быстро и надёжно:
   - `go vet` для всех полных листингов (J-H6), включая те, которым нужны `quic-go`, `x/time/rate`, gRPC, NATS, `uuid` (судья их не проверил);
   - `go doc` для каждой строки таблицы J-H5;
   - `api/go1.*.txt` для таблицы C-GOVER;
   - `grep` по `/usr/local/go/src/runtime` и `src/net` для J-H4, J-H7, J-H9, J-H10.
2. **Затем эксперименты** (network namespace, loopback недостаточно):
   - errno при отсутствии маршрута, неудаче ARP, DROP, переполнении conntrack и таблицы соседей (J-H8);
   - UDP: усечение и `EMSGSIZE` на veth с MTU 1500, с `IP_PMTUDISC_DO` и без (J-H17, K12);
   - наследование `SO_RCVBUF` принятыми сокетами и фактический размер после клампа (J-H11);
   - `r.Context()` после Hijack, `Header` и канонизация (J-H18, J-H29) — повторить эксперименты Sonnet.
3. **Ядро:** версии `tcp_rto_min_us`, `TCP_RTO_MIN_US`, `TCP_DELACK_MAX_US` (K2); `TCP_DELACK_MIN/MAX`; дефолт `somaxconn` 4096 с 5.4; дефолт порта VXLAN (`vxlan_core.c`); `rmem_max` — отличать ядерный дефолт от значения дистрибутива.
4. **RFC и стандарты:** 6298 (RTO), 9438 (CUBIC), 9000/9002/9114/9204 (QUIC, HTTP/3), 6891 (EDNS0), 3225 (бит DO), 9293 (TCP), 9111 (HTTP caching), 9113/9218 (HTTP/2 priority), IEEE 802.3ac (VLAN).
5. **Дата-зависимые факты** (C-EXT, J-H13) проверяйте по первоисточникам с датой и фиксируйте в тексте «на дату».
6. **Не путайте ядро и Go.** Многие ошибки модуля — ядерный дефолт, выданный за поведение Go (Nagle, keepalive, `SO_REUSEADDR`, backlog). Для каждого такого утверждения указывайте в вердикте обе стороны: «в ядре по умолчанию X, в Go — Y».
7. **C-FIX (§ 5):** при правке одного места проверяйте всю статью и связанные статьи по `grep` — прошлый фактчек оставил противоречия именно так.
8. **Отмечайте NOT CHECKED** для всего, что не удалось проверить: это особенно вероятно для quic-go, Envoy/HAProxy/nginx, облачных таймаутов и чисел из C-NUM.
