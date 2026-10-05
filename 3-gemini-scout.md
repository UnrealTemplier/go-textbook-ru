# 🕵️‍♂️ Исследовательский бриф первичного фактчекинга (Scout Brief): Модуль 3 «Компьютерные сети и сетевой стек»

> **Роль:** First-pass fact-check research scout.  
> **Цель:** Широкий и независимый анализ всех 44 статей Модуля 3 на предмет потенциально некорректных, устаревших, вводящих в заблуждение, упрощенных, неполных, версионно-чувствительных, машинно-зависимых или педагогически рискованных утверждений, критических багов и ошибок компиляции в листингах кода, а также архитектурных белых пятен (blind spots).  
> **Целевой артефакт:** `3-gemini-scout.md`

---

## 📌 Паспорт модуля и обзор охвата

* **Директория:** `sources/3. Компьютерные сети и сетевой стек/`
* **Количество статей:** 44 (от физического канального уровня L2, Ethernet, ARP и IP-маршрутизации до детального устройства TCP, алгоритмов перегрузки Reno/Cubic/BBR, HTTP/1.1, HTTP/2, QUIC/HTTP-3, TLS 1.3, сетевого стека Linux, `netpoller`, Kubernetes CNI, Service Mesh и сетевых паттернов распределенных систем).
* **Суммарный объем:** ~13 205 строк Markdown.
* **Листинги кода:** 84 блока на Go (включая сокетное программирование `net`, `net/http`, `net/netip`, `crypto/tls`, `golang.org/x/net`, `golang.org/x/sys/unix`, `quic-go`, gRPC и eBPF).
* **Технический стек:** Сетевой стек ядра Linux (NAPI, softirq, `sk_buff`, TCP/IP, netfilter/iptables, IPVS, eBPF/XDP), сетевая подсистема рантайма Go (1.14–1.27, `netpoller`, non-blocking I/O, epoll/kqueue/IOCP, `gopark`/`goready`), сетевые протоколы RFC (IPv4, IPv6, ARP, NDP, TCP, UDP, QUIC, TLS 1.3, HTTP/1.1–HTTP/3, BGP, VXLAN).

---

## 🧭 Каталог кандидатов на углубленный фактчекинг

---

### Кандидат 1: Вызов несуществующей функции `net.DialContext` (Compile Error)
* **article/section:** `32. Firewall, iptables, nftables и базовая фильтрация трафика.md` / `## Go-разработчик и Firewall: Практика` (Блоки кода 1 и 2)
* **claim:** Листинг предлагает выполнять подключение с контекстом через вызов функции пакета:
  ```go
  conn, err := net.DialContext(ctx, "tcp", "db.internal:5432")
  ```
* **why it needs checking:** В стандартном пакете `net` функции верхнего уровня `net.DialContext` **не существует**. Пакет экспортирует только `net.Dial(network, address)` и `net.DialTimeout(network, address, timeout)`. Для использования контекста необходимо инстанциировать структуру `net.Dialer`:
  ```go
  d := net.Dialer{}
  conn, err := d.DialContext(ctx, "tcp", "db.internal:5432")
  // либо (&net.Dialer{}).DialContext(...)
  ```
  Код в статье гарантированно не скомпилируется (`undefined: net.DialContext`). Ошибка продублирована дважды в одном файле.
* **evidence/source needed:** Go Documentation: `package net` (`src/net/dial.go`); вывод `go build / go vet`.
* **priority:** **High**

---

### Кандидат 2: Неиспользуемые импорты в листингах, ломающие компиляцию Go (`fmt`, `encoding/hex`, `context`)
* **article/section:** 
  1. `2. Модели OSI и TCP IP...md` (Блок 1, строка 5: `"fmt"`)
  2. `31. CDN, Edge и кеширование HTTP.md` (Блок 1, строка 6: `"encoding/hex"`)
  3. `42. Service Mesh. Istio, Linkerd, sidecar proxy.md` (Блок 1, строка 4: `"context"`)
* **claim:** В полностью оформленных примерах `package main` импортируются пакеты `fmt`, `encoding/hex`, `context`, которые нигде не вызываются в теле функций.
* **why it needs checking:** В языке Go неиспользуемый импорт (`imported and not used`) является фатальной ошибкой компилятора (`go build`) и линтера (`go vet`). Например, в статье 31 хэш форматируется через `%x` в `fmt.Sprintf`, из-за чего импорт `encoding/hex` остался рудиментом. Читатель, копирующий эти примеры в IDE или терминал, получает отказ в компиляции.
* **evidence/source needed:** The Go Programming Language Specification (Import declarations); проверка через `go vet / go build`.
* **priority:** **High**

---

### Кандидат 3: Скрытая уязвимость OOM (Memory Leak DoS) в реализации Rate Limiter против DDoS
* **article/section:** `33. DDoS, Rate Limiting и базовая защита сетевых сервисов.md` / `## 3. Rate Limiting на практике: Go-реализация`
* **claim:** Реализация лимитера `Limiter` хранит индивидуальные ограничения клиентов в хэш-таблице:
  ```go
  type Limiter struct {
      ...
      mu       sync.RWMutex
      limiters map[string]*rate.Limiter
  }
  func (rl *Limiter) Allow(ip string) bool {
      ...
      if !exists {
          rl.mu.Lock()
          if lim, exists = rl.limiters[ip]; !exists {
              lim = rate.NewLimiter(rl.perIPLimit, rl.perIPBurst)
              rl.limiters[ip] = lim
          }
          rl.mu.Unlock()
      }
      return lim.Allow()
  }
  ```
* **why it needs checking:** В карте `rl.limiters` **полностью отсутствует логика очистки, эвикшена (eviction), TTL или LRU**. В статье этот лимитер преподносится как инструмент защиты от DDoS-атак. При реальной сетевой атаке (ботнет, спуфинг IP-адресов или перебор подсетей IPv6) атакующий генерирует запросы с миллионов уникальных IP-адресов. Сервер создаст миллионы структур `rate.Limiter` в куче, которые никогда не будут удалены сборщиком мусора, что приведет к мгновенному исчерпанию оперативной памяти и падению процесса через OOM Killer. Лимитер защиты от DoS сам по себе является уязвимостью отказа в обслуживании.
* **evidence/source needed:** OWASP Denial of Service Cheat Sheet; исходный код `golang.org/x/time/rate`; лучшие практики создания rate limiter с TTL кэшем (например, `hashicorp/golang-lru`).
* **priority:** **High**

---

### Кандидат 4: Паника рантайма из-за отрицательного остатка от деления в Round-Robin балансировщике (`eps[idx%len]`)
* **article/section:** `30. Service Discovery и балансировка в микросервисах.md` / `## 2. Клиентская балансировка: Архитектура и паттерны`
* **claim:** Выбор следующего адреса сервиса реализован через атомарный инкремент знакового `int64`:
  ```go
  idx := atomic.AddInt64(&b.currentIndex, 1)
  return eps[idx%int64(len(eps))], nil
  ```
* **why it needs checking:** В Go оператор взятия остатка `%` для знаковых целых чисел сохраняет знак делимого. Если `a < 0`, то `a % b <= 0` (например, `-5 % 3 == -2`). Поле `currentIndex` имеет знаковый тип `int64`. Когда счетчик достигнет `math.MaxInt64`, следующий инкремент переполнит его в `math.MinInt64` (отрицательное число). Также при некорректной инициализации со значением `-1` вычисление `idx%len` даст отрицательный индекс, и обращение `eps[-1]` приведет к немедленной панике рантайма: `panic: runtime error: index out of range [-1]`. В Go для lock-free round-robin счетчик обязан быть беззнаковым (`uint64`), либо нормализоваться битовой маской `int(idx & 0x7FFFFFFFFFFFFFFF) % len(eps)`.
* **evidence/source needed:** The Go Language Specification (Arithmetic operators: Integer overflow, Remainder `%`); тест переполнения `atomic.AddInt64`.
* **priority:** **High**

---

### Кандидат 5: Логический сбой Half-Open в Circuit Breaker (Thundering Herd вместо единичного зонда)
* **article/section:** `43. Сетевые паттерны распределенных систем.md` / `## 3. Circuit Breaker (Пакет resilience)`
* **claim:** В методе `Allow()` переход в состояние Half-Open описан следующим образом:
  ```go
  case 1: // Open
      if time.Since(cb.lastFailTime) > cb.resetTimeout {
          cb.state = 2 // Half-Open
          return true
      }
      return false
  case 2: // Half-Open
      return true // Разрешаем один запрос для проверки
  ```
* **why it needs checking:** Комментарий утверждает: *«Разрешаем один запрос для проверки»*. Однако в коде состояние 2 (`Half-Open`) безусловно возвращает `true` для **каждого** последующего вызова `Allow()`, пока кто-то не вызовет `RecordSuccess()` или `RecordFailure()`. Если сервис находится под высокой нагрузкой (например, 5 000 rps), то после истечения `resetTimeout` все 5 000 входящих запросов одновременно получат `true` и обрушатся на едва восстанавливающийся зависимый сервис (классический Thundering Herd). В каноническом паттерне Circuit Breaker (Martin Fowler / Sony gobreaker) в состоянии Half-Open разрешается строго ограниченное число пробных запросов (обычно ровно 1), а все параллельные вызовы немедленно отклоняются.
* **evidence/source needed:** Martin Fowler: *CircuitBreaker*; исходный код `github.com/sony/gobreaker` (переменная `counts.requests`).
* **priority:** **High**

---

### Кандидат 6: Утечка горутины и соединений в WebSocket-обработчике из-за `r.Context().Done()`
* **article/section:** `25. WebSocket, SSE и долгоживущие соединения.md` / `## WebSocket: Двунаправленный полнодуплексный протокол`
* **claim:** В листинге `wsHandler` горутина чтения при ошибке или разрыве сокета просто завершает работу (`break`), а основной цикл ожидает сигнала отмены контекста `r.Context().Done()`:
  ```go
  go func() {
      for {
          _, msg, err := conn.ReadMessage()
          if err != nil { break }
      }
  }()
  for {
      select {
      case <-r.Context().Done():
          conn.WriteMessage(...)
          return
      case <-ticker.C:
          conn.WriteMessage(websocket.PingMessage, nil)
      }
  }
  ```
* **why it needs checking:** После выполнения `upgrader.Upgrade(w, r, nil)` базовое TCP-соединение переходит в режим `Hijack`. Сервер `net/http` снимает с себя управление дескриптором. Во многих конфигурациях и старых версиях рантайма `r.Context()` после Hijack **не отменяется** при обрыве TCP-соединения клиентом. Единственный надежный способ узнать о разрыве соединения — это ошибка системного чтения из `conn.ReadMessage()`. Однако горутина чтения при ошибке молча завершается, не закрывая контекст и не отправляя сигнал в управляющий канал. Основной цикл зависает в `ticker.C` навсегда (или до ошибки записи ping), продолжая удерживать ресурсы и вызывая утечку памяти.
* **evidence/source needed:** Документация `gorilla/websocket` (раздел "Control Messages and Concurrency"); issue `golang/go` о жизненном цикле `r.Context()` после Hijack.
* **priority:** **High**

---

### Кандидат 7: Несуществующая функция рантайма `runtime.wakeG` и миф о создании множественных epoll-инстансов в `netpoller`
* **article/section:** `38. Как Go работает с сетью. net, net_http, netpoller, epoll.md` / `## netpoller под капотом` и `## Планирование горутин при IO: gopark и wakeG`
* **claim:** 
  1. `netpoller имеет лимит на количество отслеживаемых FD. В современных версиях Go он динамически масштабируется через создание дополнительных epoll-инстансов при превышении порога.`
  2. `Ядро будит поток, netpoller извлекает pollDesc, определяет связанную горутину rg и вызывает runtime.wakeG.`
* **why it needs checking:** 
  1. В исходном коде рантайма Go (`src/runtime/netpoll_epoll.go`) объявлен ровно **один** глобальный файловый дескриптор epoll: `var epfd int32 = -1`. В Linux системный вызов `epoll_create1` вызывается ровно один раз при старте рантайма. Ядро Linux не имеет искусственного лимита на число дескрипторов в epoll (оно ограничено только `RLIMIT_NOFILE` и системной памятью ядра). Go никогда не создавал и не создает дополнительных epoll-инстансов.
  2. Функции `runtime.wakeG` в кодовой базе Go **не существует**. Для возвращения горутины из ожидания I/O в очередь выполнения рантайм использует каноническую внутреннюю функцию `goready(gp, traceskip)` или `injectglist(&toRun)`. Публикация вымышленных имен внутренних функций рантайма вводит читателей в заблуждение при профилировании и чтении трейсов.
* **evidence/source needed:** `src/runtime/netpoll_epoll.go`; `src/runtime/proc.go` (`func goready`); поиск по дереву `src/runtime/` по ключевому слову `wakeG`.
* **priority:** **High**

---

### Кандидат 8: Нерабочая директива сборки eBPF C-кода через `go build`
* **article/section:** `36. eBPF и XDP для анализа и ускорения сетевого трафика.md` / `## 3. Пишем свой XDP-фильтр на C и Go`
* **claim:** В начале Go-файла указана генерационная директива:
  ```go
  //go:generate go build -ldflags '-s -w' -o xdp_prog.xdp xdp.c
  ```
* **why it needs checking:** Компилятор Go (`go build`) категорически не умеет компилировать Си-файлы в байт-код eBPF ELF. Утилита `go build` предназначена исключительно для компиляции исходных текстов Go (или CGO для пользовательского пространства хоста). Байт-код eBPF компилируется специализированным бекендом LLVM/Clang:
  ```bash
  clang -target bpf -O2 -c xdp.c -o xdp_prog.o
  ```
  либо через кодогенератор `cilium/bpf2go`. Директива в листинге синтаксически ошибочна и вызовет сбой `go generate`.
* **evidence/source needed:** Руководство Cilium eBPF Go Library (`bpf2go`); Linux Kernel eBPF Documentation.
* **priority:** **High**

---

### Кандидат 9: Осиротевшая фоновая горутина в двунаправленном gRPC-стриминге (отсутствие `waitc`)
* **article/section:** `26. gRPC, Protocol Buffers и сетевые особенности RPC.md` / `## 3. Сетевые особенности gRPC под капотом`
* **claim:** Листинг позиционируется как *«Пример корректной работы с двунаправленным стримингом»*:
  ```go
  stream, err := client.Chat(ctx)
  ...
  defer stream.CloseSend()
  go func() {
      for {
          resp, err := stream.Recv()
          if err == io.EOF { return }
          if err != nil { return }
      }
  }()
  for _, msg := range messages {
      if err := stream.Send(msg); err != nil { return err }
  }
  ```
* **why it needs checking:** Как только цикл `stream.Send` завершается, функция выходит из области видимости, выполняет `defer stream.CloseSend()` и немедленно завершается. При этом фоновая горутина `stream.Recv()` остается брошенной (orphaned). Если сервер отправляет ответные сообщения после обработки всех входящих или с небольшой задержкой, вызывающий код завершится раньше, контекст будет сброшен, а ответы сервера будут потеряны. В каноничном паттерне gRPC Go всегда создается канал ожидания `waitc := make(chan struct{})`, и вызывающая функция обязана блокироваться на `<-waitc` до тех пор, пока `stream.Recv()` не вернет `io.EOF`.
* **evidence/source needed:** Официальная документация gRPC Go: *gRPC Basics – Go* (раздел Bidirectional streaming RPC); репозиторий `grpc/grpc-go/examples/route_guide`.
* **priority:** **High**

---

### Кандидат 10: Ручная установка `SO_RCVBUF` / `SO_SNDBUF` отключает Linux TCP Window Auto-Tuning
* **article/section:** `13. Congestion Algorithms. Reno, Cubic, BBR.md` / `## Тюнинг BBR и буферов ядра в Go`
* **claim:** Автор рекомендует вручную форсировать размер буферов сокета до 1 МБ через системные вызовы в Go как способ повысить пропускную способность:
  ```go
  syscall.SetsockoptInt(int(fd), syscall.SOL_SOCKET, syscall.SO_RCVBUF, 1024*1024)
  syscall.SetsockoptInt(int(fd), syscall.SOL_SOCKET, syscall.SO_SNDBUF, 1024*1024)
  ```
* **why it needs checking:** В сетевом стеке ядра Linux при явной установке `SO_RCVBUF` через `setsockopt` (или метод Go `SetReadBuffer`) ядро **навсегда отключает динамический автотюнинг TCP-окна** (`tcp_moderate_rcvbuf`) для этого сокета. На современных серверах параметры `net.ipv4.tcp_rmem` позволяют окну приема автоматически масштабироваться до 6–16+ МБ при высоком BDP. Принудительная фиксация буфера на 1 МБ жестко ограничивает окно и катастрофически **деградирует** производительность на 10G/40G/100G каналах с высоким RTT. Настройка буферов вручную рекомендуется только при четком понимании ограничений памяти, а в общем случае автотюнинг ядра справляется значительно эффективнее.
* **evidence/source needed:** `man 7 tcp` (секция `SO_RCVBUF`); Linux Kernel Documentation: *TCP Window Auto-Tuning*; Cloudflare Blog: *Tuning TCP receive buffers*.
* **priority:** **High**

---

### Кандидат 11: Укоренившийся миф о включенном алгоритме Нейгла (Nagle) по умолчанию в Go
* **article/section:** `10. TCP...md`, `11. TCP Handshake...md`, `12. TCP Retransmission...md`
* **claim:** На протяжении трех статей автор рекомендует вручную вызывать `tcpConn.SetNoDelay(true)` на каждом принятом соединении:
  ```go
  // Отключение алгоритма Нейгла: немедленная отправка пакетов
  _ = tcpConn.SetNoDelay(true)
  ```
  описывая это как критически важную оптимизацию для снижения сетевых задержек (low-latency RPC).
* **why it needs checking:** В стандартной библиотеке Go алгоритм Нейгла **отключен по умолчанию** (`TCP_NODELAY = 1`) для абсолютно всех TCP-соединений, создаваемых через `net.Dial`, `net.Listen` и `net/http`, начиная с Go 1.0. Функция `newTCPConn` в файле `src/net/tcpsock.go` первой строкой безусловно выполняет:
  ```go
  setNoDelay(fd, true)
  ```
  Разработчику в Go вообще не нужно вызывать `SetNoDelay(true)`. Напротив, вызывать `SetNoDelay(false)` приходится лишь в редких случаях передачи массивных непрерывных потоков данных (bulk transfer) для экономии заголовков. Подача этого метода как обязательной оптимизации формирует ложное понимание сетевых дефолтов Go.
* **evidence/source needed:** `src/net/tcpsock.go` (`func newTCPConn`); документация метода `net.TCPConn.SetNoDelay`.
* **priority:** **High**

---

### Кандидат 12: Подмена времени входящего запроса при использовании `BaseContext` в `http.Server`
* **article/section:** `40. Head of Line Blocking, Slowloris и деградация под нагрузкой.md` / `## Борьба с деградацией в Go`
* **claim:** Листинг настраивает защиту и контекст сервера следующим образом:
  ```go
  BaseContext: func(listener net.Listener) context.Context {
      ctx := context.Background()
      return context.WithValue(ctx, "start_time", time.Now())
  },
  ```
* **why it needs checking:** Функция `BaseContext` в `http.Server` вызывается **ровно один раз** в момент вызова `server.Serve(listener)`. В результате все миллионы запросов, которые сервер обработает за недели или месяцы работы, получат в качестве `"start_time"` неизменную метку времени старта самого сервера! Для привязки данных к конкретному физическому соединению используется поле `ConnContext: func(ctx context.Context, c net.Conn) context.Context`, а для засечения времени обработки каждого запроса — классический HTTP Middleware. Листинг демонстрирует критический смысловой баг.
* **evidence/source needed:** Go Documentation: `http.Server.BaseContext` vs `http.Server.ConnContext` (`src/net/http/server.go`).
* **priority:** **High**

---

### Кандидат 13: Игнорирование сервером заголовка `Transfer-Encoding: chunked` и блокировка буфера без Flush
* **article/section:** `21. HTTP 1.1 под капотом. Keep Alive, Chunked Encoding, Pipelining.md` / `## Chunked Transfer Encoding`
* **claim:** Листинг функции `streamChunked`:
  ```go
  func streamChunked(w http.ResponseWriter, data <-chan []byte) {
      w.Header().Set("Transfer-Encoding", "chunked")
      w.Header().Set("Content-Type", "application/octet-stream")
      // w.Write() автоматически форматирует чанки при наличии заголовка
      for chunk := range data {
          _, err := w.Write(chunk)
  ```
* **why it needs checking:** 
  1. В стандартном сервере `net/http` ручная установка заголовка `Transfer-Encoding` принудительно удаляется рантаймом (`delHeader("Transfer-Encoding")`). Сервер Go автоматически включает chunked encoding, если размер `Content-Length` неизвестен заранее, и отключает его, если размер передан. Утверждение, что `w.Write()` чанкует данные *из-за наличия этого заголовка*, не соответствует механике `net/http`.
  2. Без явного вызова `http.NewResponseController(w).Flush()` (или `w.(http.Flusher).Flush()`) данные не уйдут мгновенно клиенту — они останутся в буфере `bufio.Writer` (по умолчанию 4 КБ) до полного накопления или завершения хэндлера.
* **evidence/source needed:** `src/net/http/server.go` (`func (cw *chunkWriter) writeHeader`); документация `http.ResponseWriter` и `http.Flusher`.
* **priority:** **High**

---

### Кандидат 14: Устаревшее недействующее поле `PreferServerCipherSuites` и избыточная проверка `VerifyHostname`
* **article/section:** 
  1. `18. TLS и HTTPS. Шифрование поверх TCP.md` / `## Реализация безопасного TLS-клиента на Go`
  2. `19. Сертификаты, PKI, mTLS и процесс TLS Handshake.md` / `## 3. mTLS на практике: Реализация на Go`
* **claim:** В конфигурации TLS-клиента и сервера жестко задается:
  ```go
  cfg := &tls.Config{
      MinVersion: tls.VersionTLS13,
      PreferServerCipherSuites: true,
  }
  ...
  // 5. Критически важная проверка: валидация имени хоста (Hostname Verification)
  if err := tlsConn.VerifyHostname("example.com"); err != nil { ... }
  ```
* **why it needs checking:** 
  1. В стандартной библиотеке Go поле `PreferServerCipherSuites` официально объявлено устаревшим (`legacy field and has no effect`) и полностью игнорируется рантаймом. Более того, в протоколе TLS 1.3 концепция серверного порядка наборов шифров упразднена спецификацией RFC 8446.
  2. В клиенте Go вызов `tlsConn.Handshake()` **уже автоматически валидирует сертификат и доменное имя** относительно поля `cfg.ServerName`. Преподносить последующий ручной вызов `tlsConn.VerifyHostname(...)` как «критически важную проверку» вредно: читатели решат, что по умолчанию Go не сверяет имя хоста и пропускает MITM-атаки, что в корне неверно.
* **evidence/source needed:** `src/crypto/tls/common.go` (`Config.PreferServerCipherSuites`); RFC 8446; `src/crypto/tls/handshake_client.go`.
* **priority:** **Medium**

---

### Кандидат 15: Архаичный паттерн DNS-запроса через горутину вместо современного zero-alloc API `LookupNetIP`
* **article/section:** `17. DNS под капотом. Record Types, TTL, Recursive Resolver, кеширование.md` / `## DNS в Go: netgo vs cgo`
* **claim:** Листинг `lookupWithTimeout` запускает функцию `net.LookupIP(host)` в отдельной горутине с `select` по каналу и контексту:
  ```go
  go func() {
      ips, err := net.LookupIP(host)
      ch <- result{ips, err}
  }()
  ```
* **why it needs checking:** Это устаревший антипаттерн времен Go 1.6:
  1. Начиная с Go 1.8 метод `resolver.LookupIP(ctx, "ip4", host)` принимает контекст напрямую и сам корректно прерывает системные операции при таймауте.
  2. Начиная с Go 1.18 в Go появился zero-alloc метод `resolver.LookupNetIP(ctx, "ip", host)`, возвращающий компактные неизменяемые структуры `netip.Addr` без аллокаций срезов в куче.
  3. В приведенном коде при срабатывании таймаута контекста брошенная горутина с `net.LookupIP(host)` продолжает висеть в памяти ядра до завершения сетевого вызова.
* **evidence/source needed:** Go 1.18 Release Notes (`net.Resolver.LookupNetIP`); `src/net/lookup.go`.
* **priority:** **Medium**

---

### Кандидат 16: Несуществующее публичное поле `Request.Context` в `http.Request`
* **article/section:** `20. HTTP 1.1. Структура запроса и ответа.md` / `## 3. Как Go представляет HTTP-запрос под капотом`
* **claim:** В листинге анатомии структуры `http.Request` указано экспортируемое поле:
  ```go
  type Request struct {
      ...
      Host    string
      Context context.Context // Контекст горутины для отмены и таймаутов
  }
  ```
* **why it needs checking:** В пакете `net/http` поле контекста является строго приватным: `ctx context.Context`. Прямое обращение `r.Context` вызовет ошибку компиляции. Доступ к контексту запроса в Go осуществляется исключительно через публичный метод-геттер `r.Context()` и конструкторы клонирования `r.WithContext(ctx)` или `r.Clone(ctx)`.
* **evidence/source needed:** `src/net/http/request.go` (структура `type Request struct`).
* **priority:** **Medium**

---

### Кандидат 17: Использование устаревшего флага `Dialer.DualStack` (Deprecated c Go 1.12)
* **article/section:** 
  1. `35. Диагностика сети. ping, traceroute, dig, curl, mtr.md` (Блок 4)
  2. `38. Как Go работает с сетью. net, net_http, netpoller, epoll.md` (Блок 1)
* **claim:** Листинги конфигурируют сетевой диалер с параметром:
  ```go
  dialer := net.Dialer{
      Timeout:   5 * time.Second,
      KeepAlive: 30 * time.Second,
      DualStack: true,
  }
  ```
* **why it needs checking:** Поле `DualStack` в структуре `net.Dialer` официально объявлено устаревшим начиная с версии Go 1.12: *«Deprecated: DualStack is deprecated and has no effect. Fast Fallback (Happy Eyeballs) is enabled by default»*. Указание этого флага в современном учебнике по Go засоряет код недействующими параметрами.
* **evidence/source needed:** `src/net/dial.go` (`type Dialer struct`); Go 1.12 Release Notes.
* **priority:** **Low**

---

### Кандидат 18: Полностью пустой блок кода для `SO_BINDTODEVICE`
* **article/section:** `3. Ethernet, MAC-адреса и локальные сети.md` / `### Привязка к конкретному интерфейсу (Socket Options)`
* **claim:** Блок кода, озаглавленный как *«В Linux это достигается установкой низкоуровневой опции сокета SO_BINDTODEVICE через системные вызовы пакета syscall»*, содержит только:
  ```go
  // Привязка сокета к физическому интерфейсу eth0 через SO_BINDTODEVICE
  // Требует привилегии CAP_NET_RAW в ядре Linux
  ```
* **why it needs checking:** Исполняемый код в блоке отсутствует вовсе. Разработчик не видит реального механизма привязки (через `net.ListenConfig.Control` и системный вызов `unix.BindToDevice` или `setsockopt`). Это очевидный артефакт верстки/недописанный фрагмент.
* **evidence/source needed:** Просмотр файла `sources/3. Компьютерные сети и сетевой стек/3. Ethernet, MAC-адреса и локальные сети.md` (строка 75).
* **priority:** **Medium**

---

### Кандидат 19: Использование приватных типов рантайма `internal/poll.FD` в псевдокоде QUIC
* **article/section:** `24. Deep Dive в QUIC. Пакеты, Stream, Loss Recovery.md` / `## Практика: Оптимизация буферов UDP в Go (sync.Pool)`
* **claim:** В сигнатуре функции указан тип `poll.FD`, а затем вызывается псевдометод `fd.SyscallConn().Read(...)`:
  ```go
  func (c *connection) readLoop(fd *poll.FD) error {
      ...
      n, _, err := fd.SyscallConn().Read(func(fd uintptr) error {
          return readUDP(fd, buf)
      })
  }
  ```
* **why it needs checking:** Пакет `internal/poll` является внутренним пакетом рантайма Go и заблокирован компилятором для внешнего импорта (`use of internal package not allowed`). В реальной библиотеке `quic-go` сетевые операции производятся над абстракциями `net.PacketConn` / `net.UDPConn` с использованием оптимизаций GSO/GRO через пакет `golang.org/x/net/ipv4`. Кроме того, у `poll.FD` нет метода `SyscallConn()`. Псевдокод запутывает читателя компиляторно невозможными конструкциями.
* **evidence/source needed:** Go Spec (Internal packages); исходный код библиотеки `quic-go` (файл `packet_handler_map.go`).
* **priority:** **Low**

---

### Кандидат 20: Архитектурная слепая зона: Дисбаланс нагрузки в Kubernetes ClusterIP из-за HTTP Keep-Alive
* **article/section:** `41. Kubernetes Networking. CNI, Pod Network, Service, Ingress.md` / `## Go-клиент в Kubernetes: Сетевые грабли`
* **claim:** Листинг `createK8sOptimizedClient` рекомендует агрессивный пул соединений:
  ```go
  MaxIdleConnsPerHost: 100,
  IdleConnTimeout:     90 * time.Second,
  ```
* **why it needs checking:** В Kubernetes механизм ClusterIP работает на уровне ядра через L4 NAT (`iptables` или `IPVS`). Балансировка происходит **исключительно в момент TCP-рукопожатия (SYN)**. Если Go-клиент устанавливает долгоживущие Keep-Alive соединения к домену сервиса (`http://my-service:8080`), ядро перенаправляет TCP-сессию на один конкретный под. Все последующие тысячи HTTP-запросов уходят в этот единственный под. Если Deployment масштабируется с 1 до 10 реплик, новые поды получают 0% трафика, а один захлебывается. В учебнике для Senior Go-разработчиков это критический пробел: необходимо осветить решения (gRPC client-side balancing, headless services, ограничение максимального времени жизни соединения `MaxConnDuration` или использование L7 Envoy/Ingress).
* **evidence/source needed:** Kubernetes Documentation: *Services – Virtual IPs and Service Proxies*; блог Kubernetes: *Why Ingress is needed for HTTP load balancing*.
* **priority:** **Medium**

---

### Кандидат 21: Риск скрытого усечения датаграмм (Silent Truncation) буфером 1500 байт в UDP
* **article/section:** `14. UDP. Когда ненадежный транспорт лучше TCP.md` / `## Go и UDP: Низкоуровневая работа с net.UDPConn`
* **claim:** Листинг утверждает: *«Буфер 1500 байт (стандартный Ethernet MTU) гарантирует чтение целого пакета без усечения: buf := make([]byte, 1500)»*.
* **why it needs checking:** Это утверждение опасно:
  1. В приведенном примере сервер слушает локальный интерфейс `127.0.0.1`. На loopback-интерфейсе Linux (`lo`) размер MTU по умолчанию составляет **65 536 байт**, а не 1500! Клиент на том же хосте может отправить датаграмму размером до 65 507 байт.
  2. В сетях ЦОД стандартной практикой являются Jumbo Frames (MTU 9000).
  3. В UDP, если буфер приложения меньше входящей датаграммы, ядро Linux считывает указанные байты, а **весь остаток пакета безвозвратно отбрасывает (Drop)**! Гарантировать отсутствие усечения может только буфер максимального теоретического размера UDP-полезной нагрузки ($65535 - 20 - 8 = 65507$ байт) или буфер, согласованный с протокольным форматом сообщений.
* **evidence/source needed:** RFC 768 (UDP); `man 7 udp`; вывод `ip link show lo` (mtu 65536).
* **priority:** **Medium**

---

### Кандидат 22: Игнорирование канонического API `net.KeepAliveConfig` (Go 1.23+)
* **article/section:** `11. TCP...md`, `12. TCP Retransmission...md`, `38. Как Go работает с сетью...md`, `39. TIME_WAIT...md`
* **claim:** Во всех статьях для настройки TCP Keep-Alive приводится только устаревший метод `SetKeepAlivePeriod(time.Duration)`.
* **why it needs checking:** В Go 1.23 был представлен долгожданный полноценный кроссплатформенный API:
  ```go
  conn.SetKeepAliveConfig(net.KeepAliveConfig{
      Enable:   true,
      Idle:     15 * time.Second,
      Interval: 5 * time.Second,
      Count:    3,
  })
  ```
  Метод `SetKeepAlivePeriod` не позволял раздельно настраивать время простоя до первого зонда (`TCP_KEEPIDLE`), интервал повторов (`TCP_KEEPINTVL`) и число проверок (`TCP_KEEPCNT`), вынуждая инженеров прибегать к небезопасным системным вызовам `setsockopt`. В учебнике с таймлайном 2026 года отсутствие `KeepAliveConfig` является заметным версионным упущением.
* **evidence/source needed:** Go 1.23 Release Notes (`net.KeepAliveConfig`, `net.Dialer.KeepAliveConfig`).
* **priority:** **Medium**

---

### Кандидат 23: Неверное понимание механизма защиты от атаки HTTP/2 Rapid Reset (CVE-2023-44487)
* **article/section:** `22. HTTP 2. Multiplexing, Frames, HPACK.md` / `> [!warning] Ловушка / Gotcha: HPDoS (HTTP/2 Rapid Reset)`
* **claim:** *«В Go защита: обязательное обновление рантайма, а также жесткая настройка параметров http2.Server.MaxHeaderListSize и http2.Server.ReadHeaderBufferSize, ограничивающих аппетиты сервера.»*
* **why it needs checking:** Атака HTTP/2 Rapid Reset заключалась в том, что клиент отправлял микроскопические *валидные* фреймы `HEADERS` и тут же сбрасывал поток фреймом `RST_STREAM`. Размеры заголовков укладывались в стандартные минимумы, поэтому ограничение `MaxHeaderListSize` и `ReadHeaderBufferSize` **не защищало от этой уязвимости**. Настоящий патч в Go (выпущенный в Go 1.21.3 и 1.20.10) внедрил внутренний рейт-лимитер кадров сброса потока (`MaxRSTFrameRate` / скользящее окно обработки RST), при превышении которого соединение принудительно разрывается фреймом `GOAWAY`.
* **evidence/source needed:** Go Security Advisory: *CVE-2023-44487 and CVE-2023-39325*; коммит в `golang.org/x/net/http2` от 10 октября 2023 г.
* **priority:** **Medium**

---

### Кандидат 24: Пропуск аппаратной многоочередности (RSS/RPS/RFS) в глубоком обзоре сетевого стека Linux
* **article/section:** `37. Сетевой стек Linux под капотом.md`
* **claim:** Статья заявляет глубокий разбор сетевого конвейера Linux от сетевой карты до приложения, но полностью обходит стороной многоочередные адаптеры (Multi-queue NIC) и балансировку прерываний.
* **why it needs checking:** В современных серверах 10G/25G/100G ключевой причиной неравномерной утилизации CPU и роста задержек является обработка всех сетевых прерываний одним ядром процессора (100% softirq на CPU0). Понимание аппаратного Receive Side Scaling (RSS), а также программных механизмов RPS/RFS в ядре Linux — обязательная фундаментальная тема при профилировании сетевого бэкенда. В статье термины RSS и multi-queue не упоминаются ни разу.
* **evidence/source needed:** Linux Kernel Documentation: *Scaling in the Linux Networking Stack (RSS, RPS, RFS)*; `ethtool -l eth0`.
* **priority:** **Low**

---

### Кандидат 25: Некорректное обоснование правила `IdleConnTimeout > 2*MSL` в пуле HTTP-соединений
* **article/section:** `39. TIME_WAIT, Port Exhaustion и другие проблемы TCP-сервисов.md` / `## Борьба с Port Exhaustion в Go-сервисах`
* **claim:** Листинг содержит комментарий:
  ```go
  IdleConnTimeout: 90 * time.Second, // Должен быть > 2 * MSL (60s)
  ```
* **why it needs checking:** Таймаут `IdleConnTimeout` в `http.Transport` определяет время удержания бездействующего соединения в пуле клиента Go до его закрытия. Он не имеет никакой математической или физической связи с интервалом `2*MSL` (TIME_WAIT). Напротив, ключевое золотое правило настройки `IdleConnTimeout` — он **обязан быть меньше, чем keepalive-таймаут апстрима или балансировщика** (например, если у Nginx `keepalive_timeout 65s` или у AWS ALB `idle_timeout 60s`, то у Go-клиента должно быть 50–55 секунд). Если у клиента таймаут больше, клиент попытается отправить запрос в сокет, который апстрим уже закрыл, что вызовет гонку и ошибку `EOF / connection reset by peer`.
* **evidence/source needed:** AWS ALB Documentation: *Connection Idle Timeout*; Simon Eskildsen: *The architecture of high throughput HTTP clients*.
* **priority:** **Low**

---

### Кандидат 26: Бесконечный цикл с недостижимым `wg.Wait()` в утилите диагностики
* **article/section:** `35. Диагностика сети. ping, traceroute, dig, curl, mtr.md` / `## Автоматизация сетевой диагностики на Go`
* **claim:** В функции `runContinuousProbe`:
  ```go
  func runContinuousProbe(ctx context.Context, dest string, interval time.Duration) {
      ticker := time.NewTicker(interval)
      defer ticker.Stop()
      var wg sync.WaitGroup
      for range ticker.C {
          wg.Add(1)
          go func() { ... }()
      }
      wg.Wait()
  }
  ```
* **why it needs checking:** Конструкция `for range ticker.C` никогда не прерывается сама по себе и не проверяет `ctx.Done()`. Строка `wg.Wait()` за пределами цикла является мертвым кодом (dead code), который никогда не исполнится. При отмене контекста функция продолжит бесконечно спавнить горутины, пока процесс не завершится принудительно.
* **evidence/source needed:** Go Documentation: `time.Ticker`; проверка логики отмены циклов по контексту.
* **priority:** **Low**

---

### Кандидат 27: Опущение необходимости прав суперпользователя / `CAP_NET_RAW` для ICMP Echo
* **article/section:** `35. Диагностика сети. ping, traceroute, dig, curl, mtr.md` / `## Реализация Ping на Go (ICMP Echo Request)`
* **claim:** Листинг открывает ICMP-сокет вызовом:
  ```go
  conn, err := icmp.ListenPacket("ip4:icmp", "0.0.0.0")
  ```
  без каких-либо комментариев о правах доступа.
* **why it needs checking:** В ОС Linux открытие сырого сокета `"ip4:icmp"` требует привилегий `root` либо наличия у исполняемого файла capabilities `CAP_NET_RAW` (`setcap cap_net_raw+ep`). При запуске от обычного непривилегированного пользователя код упадет с ошибкой `socket: operation not permitted`. Для работы без root в Linux требуется использовать `"udp4"` сокет с системной настройкой `net.ipv4.ping_group_range`. Умолчание об этом приводит к гарантированному сбою при воспроизведении примера студентами.
* **evidence/source needed:** `man 7 raw`; документация пакета `golang.org/x/net/icmp`.
* **priority:** **Medium**

---

### Кандидат 28: Генерация нового UUID внутри вызываемого метода, нарушающая идемпотентность
* **article/section:** `43. Сетевые паттерны распределенных систем.md` / `## 4. Идемпотентность и Deduplication`
* **claim:** В листинге клиента генерация ключа идемпотентности происходит внутри самого метода выполнения запроса:
  ```go
  func (s *Service) CreateOrder(ctx context.Context, req *OrderReq) error {
      idempKey := uuid.New().String()
      ...
      resp, err := s.grpcClient.CreateOrder(ctx, &pb.CreateOrderRequest{
          Order:          req,
          IdempotencyKey: idempKey,
      })
  ```
* **why it needs checking:** Суть паттерна Idempotency Key заключается в том, что при сетевом сбое (таймаут, разрыв соединения) вызывающая сторона **повторяет тот же самый запрос с тем же самым ключом идемпотентности**, чтобы сервер распознал дубликат. Если генерировать `uuid.New()` внутри метода `CreateOrder` при каждом его вызове, то любой внешний ретрай создаст совершенно новый заказ, полностью дискредитируя смысл защиты от дубликатов. Ключ идемпотентности должен либо формироваться детерминированно из бизнес-сущности (детерминированный UUID/хэш), либо передаваться в метод извне.
* **evidence/source needed:** Stripe API Documentation: *Idempotent Requests*; IETF Draft: *The Idempotency-Key HTTP Header Field*.
* **priority:** **Low**

---

## 📊 Сводная таблица кандидатов по приоритетам

| Приоритет | № | Статья / Раздел | Ключевая претензия | Источник / Референс |
|:---:|:---:|---|---|---|
| 🔴 **High** | 1 | `32. Firewall...` / Практика | Несуществующая функция `net.DialContext` (Compile Error) | `src/net/dial.go` |
| 🔴 **High** | 2 | `2. OSI`, `31. CDN`, `42. Service Mesh` | Неиспользуемые импорты `fmt`, `encoding/hex`, `context` (Compile Error) | Go Language Spec |
| 🔴 **High** | 3 | `33. DDoS...` / Rate Limiter | Фатальная утечка памяти (OOM DoS) из-за неограниченной мапы `limiters` | OWASP DoS Guidelines |
| 🔴 **High** | 4 | `30. Service Discovery...` / Балансировка | Паника рантайма из-за отрицательного остатка `eps[idx%len]` при wrap-around | Go Spec (Arithmetic operators) |
| 🔴 **High** | 5 | `43. Паттерны...` / Circuit Breaker | Thundering Herd в Half-Open: все запросы получают `true` без ограничений | Martin Fowler / sony/gobreaker |
| 🔴 **High** | 6 | `25. WebSocket...` / Upgrader | Утечка горутины: `r.Context()` не завершается после Hijack при ошибке чтения | `gorilla/websocket` docs |
| 🔴 **High** | 7 | `38. Go и сеть` / netpoller | Вымышленная функция `runtime.wakeG` и миф о создании множественных epoll | `src/runtime/netpoll_epoll.go` |
| 🔴 **High** | 8 | `36. eBPF & XDP` / Фильтр | Фиктивная директива сборки eBPF C-кода через `go build` | Cilium `bpf2go` / Clang |
| 🔴 **High** | 9 | `26. gRPC...` / Стриминг | Потеря ответов и зомби-горутина в gRPC duplex stream без канала `waitc` | gRPC Go Reference |
| 🔴 **High** | 10 | `13. Congestion...` / BBR | Ручная установка `SO_RCVBUF` навсегда отключает TCP auto-tuning в Linux | `man 7 tcp` (`SO_RCVBUF`) |
| 🔴 **High** | 11 | `10. TCP`, `11. Handshake`, `12. Nagle` | Алгоритм Нагла в Go выключен по умолчанию: `SetNoDelay(true)` избыточен | `src/net/tcpsock.go` |
| 🔴 **High** | 12 | `40. HoL Blocking...` / Slowloris | Баг `BaseContext`: `start_time` фиксируется один раз при старте сервера | `src/net/http/server.go` |
| 🔴 **High** | 13 | `21. HTTP 1.1...` / Chunked | `net/http` удаляет `Transfer-Encoding: chunked`; чанки виснут без `Flush()` | `src/net/http/server.go` |
| 🟡 **Medium** | 14 | `18. TLS`, `19. Сертификаты` | Устаревший `PreferServerCipherSuites` и избыточный `VerifyHostname` | `src/crypto/tls/common.go` |
| 🟡 **Medium** | 15 | `17. DNS под капотом` / netgo | Архаичный паттерн запроса DNS через горутину вместо `LookupNetIP` | Go 1.18 Release Notes |
| 🟡 **Medium** | 16 | `20. HTTP 1.1` / Request | Ошибочно объявлено экспортируемое поле `Context` вместо `ctx` | `src/net/http/request.go` |
| 🟡 **Medium** | 17 | `3. Ethernet...` / SO_BINDTODEVICE | Пустой блок кода вместо реального примера сокетной опции | `sources/.../3. Ethernet.md` |
| 🟡 **Medium** | 18 | `41. Kubernetes...` / Keep-Alive | Срыв балансировки K8s ClusterIP из-за HTTP Keep-Alive (трафик на 1 под) | K8s Documentation |
| 🟡 **Medium** | 19 | `14. UDP...` / Буферы | Иллюзия безопасности буфера 1500 байт: усечение пакетов на `lo` и Jumbo | RFC 768 / `ip link show lo` |
| 🟡 **Medium** | 20 | `11. Handshake`, `12. KeepAlive` | Пропуск современного API `net.KeepAliveConfig` из Go 1.23+ | Go 1.23 Release Notes |
| 🟡 **Medium** | 21 | `22. HTTP 2...` / Rapid Reset | Неверное объяснение защиты от CVE-2023-44487 (нужен rate limit RST) | Go Advisory CVE-2023-44487 |
| 🟡 **Medium** | 22 | `35. Диагностика` / Raw ICMP | Опущена необходимость `CAP_NET_RAW` / root для `ip4:icmp` | `man 7 raw` |
| 🟢 **Low** | 23 | `35. Диагностика`, `38. Go и сеть` | Устаревшее недействующее поле `Dialer.DualStack` (deprecated с Go 1.12) | Go 1.12 Release Notes |
| 🟢 **Low** | 24 | `24. Deep Dive QUIC` / sync.Pool | Несуществующий импорт `internal/poll` и метод `SyscallConn` | Go Spec (Internal packages) |
| 🟢 **Low** | 25 | `37. Linux стек` / Драйверы | Полный пропуск аппаратной многоочередности сетевых карт (RSS/RPS/RFS) | Linux Scaling doc |
| 🟢 **Low** | 26 | `39. TIME_WAIT...` / Keep-Alive | Ложная привязка `IdleConnTimeout > 2*MSL` вместо согласования с апстримом | AWS ALB Architecture |
| 🟢 **Low** | 27 | `35. Диагностика` / Ping runner | Бесконечный цикл тикера без проверки контекста с недостижимым `wg.Wait()` | Go Ticker docs |
| 🟢 **Low** | 28 | `43. Паттерны...` / Идемпотентность | Локальная генерация нового UUID, ломающая семантику ретраев | Stripe Idempotency Guide |

---

## 🎯 Стратегические рекомендации для последующей редактуры

1. **Устранить ошибки компиляции в коде примеров (§ 2, 31, 32, 42):**
   - Заменить несуществующий вызов `net.DialContext(ctx, ...)` на `(&net.Dialer{}).DialContext(ctx, ...)`.
   - Очистить код от неиспользуемых импортов (`fmt`, `encoding/hex`, `context`).
2. **Исправить критические логические баги в алгоритмических сниппетах (§ 25, 26, 30, 33, 40, 43):**
   - Добавить эвикшен/TTL в per-IP `RateLimiter`, чтобы исключить уязвимость OOM DoS.
   - Сделать счетчик round-robin беззнаковым `uint64` во избежание паники при переполнении.
   - Ограничить Half-Open в Circuit Breaker единичным зондирующим запросом.
   - Добавить канал `waitc` в пример двунаправленного gRPC-стриминга.
   - Заменить `BaseContext` на middleware/`ConnContext` для замера времени запросов.
3. **Синхронизировать терминологию рантайма Go с реальностью кодовой базы (§ 38):**
   - Устранить вымышленное имя `runtime.wakeG`, описав реальную механику `goready` и `injectglist`.
   - Удалить ошибочное утверждение о масштабировании `netpoller` через создание нескольких инстансов `epoll`.
4. **Развенчать мифы сетевого стека Go и ядра Linux (§ 10, 11, 12, 13, 21):**
   - Четко зафиксировать, что `TCP_NODELAY` (отключение Нагла) в Go включено **по умолчанию** с версии 1.0.
   - Предупредить о рисках явного вызова `SO_RCVBUF`, отключающего Linux window auto-tuning.
   - Пояснить, что установка заголовка `Transfer-Encoding: chunked` в Go игнорируется и удаляется рантаймом.
5. **Актуализировать сетевые API под современный стек Go 1.18–1.24+ (§ 15, 17, 20, 22):**
   - Внедрить `net.KeepAliveConfig` из Go 1.23 для управления TCP Keep-Alive.
   - Продвигать `net/netip` и `resolver.LookupNetIP` взамен тяжелого `net.IP`.
   - Удалить устаревшие поля `DualStack` и `PreferServerCipherSuites`.
6. **Осветить реальные инфраструктурные грабли Kubernetes (§ 41):**
   - Добавить подробное объяснение проблемы залипания HTTP Keep-Alive соединений на один под при балансировке через ClusterIP (iptables/IPVS) и пути её решения на бэкенде.
