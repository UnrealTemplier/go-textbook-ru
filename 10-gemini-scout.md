# 🧭 Исследовательский скаут-отчет: Модуль 10. Проектирование API и Сетевые протоколы

> *«Сетевые протоколы и API — это кровеносная система распределенных систем. Любая неточность в контракте, скрытое состояние гонки в лимитере или утечка сокетов на уровне рантайма в высоконагруженном сервисе оборачивается каскадной аварией всего кластера».*  
> — Исследовательский аудит архитектуры бэкенда

---

## 📌 Паспорт модуля и объем проверки

* **Название модуля:** Модуль 10: Проектирование API и Сетевые протоколы
* **Расположение исходных материалов:** `sources/10. Проектирование API и Сетевые протоколы/`
* **Количество статей:** 40
* **Общий объем текста:** ~8 950 строк Markdown
* **Роль и цель:** Первый независимый сквозной проход (First-Pass Fact-Check Research Scout). Широкий поиск потенциально некорректных, устаревших, вводящих в заблуждение, упрощенных, платформенно- и рантайм-зависимых утверждений, скрытых состояний гонки (Race Conditions), утечек ресурсов, расхождений с актуальными RFC и сетевыми спецификациями, а также системных белых пятен (Blind Spots).

---

## 📊 Сводка найденных кандидатов

| Приоритет | Кол-во | Описание характера находок |
|:---:|:---:|---|
| 🔴 **High** | **8** | Полная подмена темы статьи 35 (файл озаглавлен «Chaos testing API.md», но внутри на 100% посвящен Graceful Shutdown; реальный Chaos Engineering отсутствует вовсе); состояние гонки (Broken Double-Checked Locking) в локальном Token Bucket лимитере; фатальный обрыв серверной половины двунаправленного gRPC-стрима при получении `io.EOF` от клиента с воровством сообщений из общего канала; прямое нарушение RFC 9110 / RFC 7232 при проверке `If-None-Match` и пустой ответ `304 Not Modified` без обязательных заголовков; неограниченная утечка памяти (Unbounded Memory Leak) в `sync.Map` и синхронная блокировка флешера Redis в гибридном квотировании; утечка горутин (Goroutine Leak) в `writePump` при обрыве соединения WebSocket; использование устаревшего и отключенного в Go `Subject.CommonName` (CN) вместо SAN в mTLS-аутентификации; риск искажения данных и обрыва JSON из-за использования одиночного `r.Body.Read` в демонстрационном буферном пуле `sync.Pool`. |
| 🟡 **Medium** | **9** | Пропуск обязательного вызова `pr.SetXForwarded()` при ручной мутации заголовков в `httputil.ProxyRequest` (Go 1.20+); систематическое повреждение LaTeX-формул (замена `\t` на байт табуляции `0x09`, что ломает KaTeX); использование нетипизированных примитивных строк в `context.WithValue` вопреки собственным же рекомендациям из соседней статьи; захардкоженная заглушка `lastEventID = 100` в рабочем примере Long Polling; математическая неприменимость SQL Tuple Comparison при разнонаправленной сортировке и уязвимость незашифрованных Base64-курсоров; отсутствие упоминания типов `sint32`/`sint64` и 10-байтового раздувания отрицательных чисел в Protobuf Varint; межмодульная несогласованность стандарта Problem Details (RFC 7807 vs RFC 9457); категоричный совет возвращать `409 Conflict` на конкурентные запросы с ключом идемпотентности вместо кратковременного удержания (Stripe standard); умалчивание о роли Pact Broker в сквозном CI/CD контрактов. |
| 🟢 **Low** | **5** | Абсолютизация требования HATEOAS для практических REST API; требование возврата заголовка `WWW-Authenticate` при ошибке 401 в чисто сервисных JSON API; глобальная регистрация метрик через `promauto` без возможности изоляции тестовых прогонов; риск искажения HTTP-статуса при повторных вызовах `WriteHeader` в кастомном `ResponseWriter`; систематический пропуск проверки ошибки возвращаемого значения `json.NewEncoder(w).Encode(...)`. |

---

## 🧭 Каталог кандидатов на углубленный фактчекинг

---

### Кандидат 1: Полная подмена темы статьи (Chaos Testing vs Graceful Shutdown)
* **article/section:** `35. Chaos testing API.md` (весь документ, строки 1–302)
* **claim:**  
  Файл назван `35. Chaos testing API.md`, в оглавлениях и перекрестных ссылках позиционируется как модуль по Chaos Testing API. Однако внутри статьи:
  - Заголовок: `# Graceful Shutdown и устойчивость API в Go: Искусство уходить красиво`.
  - Содержание: 100% текста посвящено перехвату сигналов `SIGINT`/`SIGTERM` через `signal.NotifyContext`, жизненному циклу подов в Kubernetes (Grace Period, Pod Lifecycle), задержке в `iptables` («The Sleep Hack»), реализации `srv.Shutdown()` и `grpcServer.GracefulStop()`.
  - Термины Chaos Testing, Chaos Engineering, внедрение сбоев (Fault Injection), Toxiproxy, Chaos Mesh, задержки сети, packet drop, network partition не упоминаются ни разу!
* **why it needs checking:** Это критический баг контента и нарушение структуры курса. Читатель, открывающий главу по хаос-тестированию API, получает отличную, но совершенно постороннюю статью о Graceful Shutdown (которая, к тому же, частично дублирует тему завершения работы сервисов из Модуля 9). Реальная дисциплина хаос-тестирования распределенных сетевых интерфейсов осталась полностью нераскрытой.
* **evidence/source needed:** Проверка файла `sources/10. Проектирование API и Сетевые протоколы/35. Chaos testing API.md`; проверка плана учебного модуля и связей со статьями 34 и 36.
* **priority:** 🔴 **High**

---

### Кандидат 2: Состояние гонки (Broken Double-Checked Locking) в локальном Rate Limiter
* **article/section:** `11. Rate limiting в API.md` / `## Ловушка на собеседовании: Утечка памяти в локальном лимитере` (строки 154–167)
* **claim:**  
  ```go
  func getVisitor(ip string) *rate.Limiter {
      mu.RLock()
      limiter, exists := limiters[ip]
      mu.RUnlock()

      if !exists {
          mu.Lock()
          limiter = rate.NewLimiter(1, 3)
          limiters[ip] = limiter
          mu.Unlock()
      }
      return limiter
  }
  ```
  В тексте утверждается, что единственная проблема данного кода — отсутствие вытеснения старых записей (Eviction / Memory Leak).
* **why it needs checking:** В листинге содержится классический антипаттерн **Broken Double-Checked Locking**, порождающий состояние гонки (Race Condition):
  1. Между вызовами `mu.RUnlock()` и последующим `mu.Lock()` блокировка полностью снимается.
  2. Если на сервис одновременно приходят два параллельных HTTP-запроса от одного IP-адреса, обе горутины увидят `!exists == true`.
  3. Обе горутины создадут по новому экземпляру `rate.NewLimiter(1, 3)`.
  4. Первая горутина захватит `mu.Lock()`, запишет лимитер и начнет списывать токены.
  5. Вторая горутина захватит `mu.Lock()` и **безусловно перезапишет** `limiters[ip]` своим новым лимитером со свежими 3 токенами!
  6. Накопленное состояние лимитера сбрасывается, клиент получает незаслуженные дополнительные токены в обход лимита, а предыдущий объект лимитера выбрасывается. Для корректности требуется повторная проверка `limiter, exists = limiters[ip]` под эксклюзивным `mu.Lock()`, либо безусловный захват `mu.Lock()` с самого начала.
* **evidence/source needed:** Документация Go Memory Model; запуск теста с флагом `go test -race` на конкурентный вызов `getVisitor`.
* **priority:** 🔴 **High**

---

### Кандидат 3: Преждевременный обрыв стрима при `io.EOF` и воровство сообщений из канала в gRPC Streaming
* **article/section:** `18. gRPC streaming.md` / `### Двунаправленный стриминг (Bidirectional Streaming)` (строки 97–138)
* **claim:**  
  В методе `SyncChat`:
  ```go
  // Читающая горутина:
  in, err := stream.Recv()
  if err == io.EOF {
      // Клиент закрыл стрим на отправку (полуоткрытое соединение)
      errCh <- nil
      return
  }
  ...
  // Пишущий цикл в основной горутине:
  case err := <-errCh:
      // Читающая горутина завершилась (с ошибкой или штатным io.EOF)
      return err // Возвращает nil!
  ...
  case outMsg := <-s.businessMessageQueue:
      if err := stream.Send(outMsg); err != nil { return err }
  ```
* **why it needs checking:** Здесь присутствуют сразу две грубые ошибки сетевого протокола gRPC:
  1. **Преждевременное закрытие стрима:** Когда клиент вызывает `CloseSend()`, сервер получает `io.EOF`. Это означает полузакрытое соединение (Half-closed stream): клиент больше ничего не шлет, но **ждет оставшиеся ответы от сервера**! Код читателя отправляет `errCh <- nil`, а цикл записи, получив `nil`, делает `return nil`. В `grpc-go` возврат из RPC-хэндлера немедленно отправляет HTTP/2 фрейм с трейлерами (`grpc-status: 0`) и принудительно закрывает серверную сторону потока! Сервер аварийно обрывает отправку сообщений, которые он еще должен был дослать клиенту.
  2. **Воровство сообщений (Competing Consumers):** Поле `s.businessMessageQueue` принадлежит структуре сервера `*server`. Если к чату подключаются 10 пользователей, горутины всех 10 соединений будут конкурировать за вычитывание из одного общего канала `<-s.businessMessageQueue`. Каждое исходящее сообщение получит ровно **один случайный пользователь**, вместо широковещательной рассылки (Broadcast) всем участникам чата.
* **evidence/source needed:** Спецификация gRPC over HTTP/2 (gRPC Protocol RFC); документация `grpc-go` (Handling client EOF in bidirectional streaming); официальные примеры RouteGuide.
* **priority:** 🔴 **High**

---

### Кандидат 4: Нарушение RFC 9110 при проверке `If-None-Match` и пустой ответ `304 Not Modified`
* **article/section:** `12. Caching HTTP.md` / `## Mechanical Sympathy: Ловушка генерации ETag в Go` (строки 134–146)
* **claim:**  
  ```go
  // 2. Сравниваем с заголовком клиента ДО загрузки самих данных
  if r.Header.Get("If-None-Match") == currentETag {
      w.WriteHeader(http.StatusNotModified)
      return // <- Идеально! Ноль аллокаций тяжелых DTO, ноль JOIN-ов в БД.
  }
  // 3. Если ETag не совпал - делаем тяжелую работу
  user := db.GetFullUserWithHeavyJoins(r.Context(), userID)
  w.Header().Set("ETag", currentETag)
  w.Header().Set("Cache-Control", "private, max-age=3600")
  json.NewEncoder(w).Encode(user)
  ```
* **why it needs checking:** Листинг содержит два грубых нарушения стандартов HTTP (RFC 9110 / RFC 7232):
  1. **Примитивное сравнение строк:** Клиент может прислать слабый тег валидации (Weak ETag, например `W/"123"`), маску `*` или список тегов через запятую (`"v1", "v2"`). Сравнение `r.Header.Get("If-None-Match") == currentETag` не распознает слабые теги (которые генерируют многие CDN и браузеры) и wildcard-запросы, из-за чего сервер будет каждый раз выполнять дорогостоящую выборку `db.GetFullUserWithHeavyJoins` и возвращать полный 200 OK.
  2. **Отсутствие обязательных заголовков в ответе 304:** Согласно RFC 9110 (Section 15.4.5 — 304 Not Modified), сервер при генерации статуса 304 **ОБЯЗАН** сформировать заголовки `ETag`, `Cache-Control`, `Vary` и `Date`, которые присутствовали бы в эквивалентном ответе `200 OK`. Код вызывает `w.WriteHeader(http.StatusNotModified)` до установки заголовков `ETag` и `Cache-Control`. В итоге браузер/CDN получает пустой статус без метаданных кэширования и не может обновить TTL валидности записи.
* **evidence/source needed:** RFC 9110 (HTTP Semantics), Section 13.1.2 (If-None-Match) и Section 15.4.5 (304 Not Modified); RFC 7232.
* **priority:** 🔴 **High**

---

### Кандидат 5: Утечка памяти в `sync.Map` и синхронная блокировка флешера Redis в квотировании
* **article/section:** `30. API rate limiting и quotas.md` / `## 6. Идиоматичный Go: Реализация Async Flusher` (строки 144–212)
* **claim:**  
  ```go
  type Manager struct {
      localCounters sync.Map // Ключ: clientID (string), Значение: *uint64
      redisClient   RedisClient
  }
  ...
  func (m *Manager) flushToRedis() {
      m.localCounters.Range(func(key, value interface{}) bool {
          clientID := key.(string)
          counterPtr := value.(*uint64)
          delta := atomic.SwapUint64(counterPtr, 0)
          if delta > 0 {
              ctx, cancel := context.WithTimeout(context.Background(), 2*time.Second)
              if err := m.redisClient.IncrBy(ctx, "quota:"+clientID, int64(delta)); err != nil {
                  atomic.AddUint64(counterPtr, delta)
              }
              cancel()
          }
          return true
      })
  }
  ```
* **why it needs checking:**
  1. **Unbounded Memory Leak:** Поле `localCounters sync.Map` сохраняет указатель на счетчик для каждого уникального `clientID`. В коде **отсутствует механизм удаления (Eviction/Delete)** неактивных клиентов. Для публичного API с миллионами клиентов, токенов или IP-адресов это приводит к непрерывному росту мапы в памяти процесса и падению сервиса по OOM.
  2. **Синхронная блокировка флешера:** В цикле `Range` вызов `m.redisClient.IncrBy` выполняется **последовательно и синхронно** для каждого клиента с таймаутом до 2 секунд. Если активных клиентов 10 000, последовательные сетевые round-trip вызовы заблокируют горутину флешера на десятки секунд. Фоновый таймер `ticker.C` начнет пропускать тики, а актуализация квот в Redis перестанет поспевать за реальным трафиком. Для промышленных решений обязателен батчинг через Redis Pipelining (`redis.Pipelined`).
* **evidence/source needed:** Документация Go `sync.Map` (отсутствие автоматического GC неиспользуемых ключей); спецификация Redis Pipelining.
* **priority:** 🔴 **High**

---

### Кандидат 6: Утечка горутины `writePump` при обрыве соединения WebSocket
* **article/section:** `22. WebSocket.md` / `## Проблема мертвых душ: Ping / Pong и утечки памяти` (строки 138–163)
* **claim:**  
  В функции `readPump`:
  ```go
  func (c *Client) readPump() {
      defer func() {
          c.conn.Close()
      }()
      ...
      for {
          _, message, err := c.conn.ReadMessage()
          if err != nil { break }
      }
  }
  ```
* **why it needs checking:**
  1. Когда клиент внезапно отключается, `readPump` выходит из цикла и выполняет `c.conn.Close()`.
  2. Однако канал `c.send` (созданный в `ServeWS` с буфером 256) **не закрывается**.
  3. Горутина `writePump` ждет сообщений из канала: `message, ok := <-c.send`. Если сообщений для этого клиента больше нет, `writePump` остается навечно заблокированной на чтении из незакрытого канала.
  4. Закрытие `c.conn` прервет `writePump` только в том случае, если в канал кто-то пришлет новое сообщение и `writePump` попытается сделать `conn.WriteMessage`. Но если сообщений нет, горутина зависает в памяти навсегда. На 100 000 отключившихся пользователей сервис накопит 100 000 утекших горутин (Goroutine Leak).
  5. Кроме того, листинг реализации `writePump` в статье вовсе отсутствует, хотя в тексте на него опирается вся архитектурная схема.
* **evidence/source needed:** Официальный эталонный пример Gorilla WebSocket chat (`hub.go`, `client.go`); диагностика утечки горутин через `runtime.NumGoroutine()`.
* **priority:** 🔴 **High**

---

### Кандидат 7: Использование устаревшего и отключенного `Subject.CommonName` вместо SAN в mTLS
* **article/section:** `29. mTLS в сервисах.md` / `## Извлечение идентичности клиента из mTLS-сессии` (строки 126–134)
* **claim:**  
  ```go
  // 3. Извлекаем проверенную криптографическую личность клиента
  if len(r.TLS.PeerCertificates) == 0 {
      http.Error(w, "Client certificate missing", http.StatusUnauthorized)
      return
  }
  clientName := r.TLS.PeerCertificates[0].Subject.CommonName
  log.Printf("Успешный mTLS запрос от доверенного сервиса: %s", clientName)
  ```
* **why it needs checking:**
  1. Поле `CommonName` (CN) для идентификации субъекта сертификата признано устаревшим (deprecated) в RFC 2818 более 20 лет назад.
  2. В Go 1.15 валидация `CommonName` была отключена по умолчанию, а начиная с Go 1.17 флаг обратной совместимости `GODEBUG=x509ignoreCN=0` был полностью удален.
  3. В современных сервисных микросервисных сетях и Zero-Trust архитектурах (SPIFFE/SPIRE, Kubernetes, Istio, HashiCorp Vault) идентичность клиента кодируется исключительно в **SAN (Subject Alternative Name)**:
     - Либо в **URI SAN** (`cert.URIs`) в формате SPIFFE ID: `spiffe://domain/ns/prod/sa/billing-service`.
     - Либо в **DNS SAN** (`cert.DNSNames`).
  4. Сертификаты, сгенерированные современными удостоверяющими центрами (CA), часто вообще оставляют поле `Subject.CommonName` пустым. Обучение извлечению идентичности через `Subject.CommonName` несет ложное представление о безопасности и приведет к падению в реальных продакшен-кластерах.
* **evidence/source needed:** Go 1.15 Release Notes (x509 CommonName deprecation); спецификация SPIFFE ID (X509-SVID); RFC 6125.
* **priority:** 🔴 **High**

---

### Кандидат 8: Искажение данных из-за одиночного `Read` в буферном пуле `sync.Pool`
* **article/section:** `39. API performance.md` / `### Пример эффективного использования sync.Pool` (строки 210–228)
* **claim:**  
  ```go
  func HeavyJSONHandler(w http.ResponseWriter, r *http.Request) {
      bufPtr := bufferPool.Get().(*[]byte)
      buf := *bufPtr
      defer bufferPool.Put(bufPtr)

      // Читаем полезную нагрузку напрямую в переиспользуемый буфер
      n, err := r.Body.Read(buf)
      if err != nil && err != io.EOF {
          http.Error(w, "Read error", http.StatusInternalServerError)
          return
      }

      // Обрабатываем вычитанные байты buf[:n] ...
      w.WriteHeader(http.StatusOK)
  }
  ```
* **why it needs checking:**
  1. **Нарушение контракта `io.Reader`:** Согласно спецификации интерфейса `io.Reader` в Go, метод `Read` не обязан вычитывать весь доступный объем данных за один вызов. Если входящий TCP-пакет пришел частями (например, первый TCP-сегмент MTU размером 1460 байт из общего 10-килобайтного JSON-запроса), одиночный вызов `r.Body.Read(buf)` вернет `n = 1460` и `err = nil`!
  2. Код посчитает `buf[:n]` полным телом запроса, в результате чего хэндлер получит обрезанный невалидный JSON.
  3. Для корректного вычитывания потока данных в буфер фиксированного размера необходимо использовать цикл или функцию `io.ReadFull(r.Body, buf)`, а для произвольного размера — `io.ReadAll(io.LimitReader(r.Body, maxBytes))` с `bytes.Buffer`.
* **evidence/source needed:** Спецификация пакета `io` в стандартной библиотеке Go (`io.Reader` contract); документация `net/http`.
* **priority:** 🔴 **High**

---

### Кандидат 9: Пропуск обязательного вызова `pr.SetXForwarded()` в `httputil.ProxyRequest`
* **article/section:** `25. API Gateway.md` / `## Идиоматичный Go: Реализация API Gateway` (строки 114–130)
* **claim:**  
  ```go
  Rewrite: func(pr *httputil.ProxyRequest) {
      pr.SetURL(targetURL)
      pr.Out.Header.Set("X-Forwarded-Host", pr.In.Host)
      pr.Out.Header.Set("X-Gateway-Auth", "verified")
      if userID, ok := pr.In.Context().Value("user_id").(string); ok {
          pr.Out.Header.Set("X-User-ID", userID)
      }
  }
  ```
* **why it needs checking:**
  1. В теоретической части статьи автор прямо подчеркивает важность безопасной обработки заголовков `X-Forwarded-*` в Go 1.20+ через метод `pr.SetXForwarded()`.
  2. Однако в листинге кода реализации автор забыл вызвать `pr.SetXForwarded()`, ограничившись ручной установкой только `X-Forwarded-Host`.
  3. Метод `pr.SetXForwarded()` критически важен: он корректно дополняет цепочку `X-Forwarded-For` реальным IP клиента (отсекая попытки спуфинга со стороны клиента) и выставляет `X-Forwarded-Proto`. Пропуск этого вызова оставляет upstream-сервисы без информации об исходном IP-клиента и протоколе шифрования.
* **evidence/source needed:** Документация `net/http/httputil.ProxyRequest.SetXForwarded` (Go 1.20+).
* **priority:** 🟡 **Medium**

---

### Кандидат 10: Систематическое повреждение LaTeX-формул (табуляция `0x09` вместо `\t`)
* **article/section:** 
  - `23. Server Sent Events.md` (строка 375: `$	o$` вместо `$\to$`)
  - `24. Long polling.md` (строка 73: `$$50\,000 	imes 20	ext{ КБ}  pprox 1	ext{ ГБ RAM}$$`)
  - `26. BFF pattern.md` (строка 268: `$$	ext{Клиент} \longrightarrow 	ext{BFF} \longrightarrow 	ext{Микросервисы}$$`)
  - `27. Backward compatibility.md` (строка 89: `$$	ext{Header} = (	ext{field\_number} \ll 3) \mid 	ext{wire\_type}$$`)
  - `34. Contract testing.md` (строка 241: `$	o$`)
* **claim:**  
  В формулах KaTeX строковая последовательность `\t` была интерпретирована как литеральный символ табуляции `0x09`, превратив `\text` в `	ext`, `\times` в `	imes`, а `\to` в `	o`.
* **why it needs checking:** Литеральный байт табуляции внутри блоков математики `$ ... $` и `$$ ... $$` приводит к ошибкам парсера KaTeX на фронтенде и отображению поврежденного сырого текста вместо математических формул и стрелок.
* **evidence/source needed:** Проверка исходных файлов через `hexdump -C` или `cat -A`; спецификация KaTeX Math Syntax.
* **priority:** 🟡 **Medium**

---

### Кандидат 11: Использование нетипизированных примитивных строк в `context.WithValue`
* **article/section:** `25. API Gateway.md` (строка 168)
* **claim:**  
  ```go
  ctx := context.WithValue(r.Context(), "user_id", "usr_998877")
  next.ServeHTTP(w, r.WithContext(ctx))
  ```
* **why it needs checking:**
  1. Использование встроенного типа `string` в качестве ключа контекста — общепризнанный антипаттерн в Go, нарушающий рекомендации документации пакета `context` и вызывающий предупреждение линтера `SA1029` (`staticcheck`).
  2. Примечательно, что в статье `28. Security API. Auth, OAuth2.md` (строки 178–189) автор сам подробно и правильно объясняет, почему необходимо использовать неэкспортируемый тип `type contextKey struct{}`, чтобы избежать межпакетных коллизий. Налицо прямая несогласованность стандартов кодирования внутри одного модуля.
* **evidence/source needed:** Документация пакета `context` в стандартной библиотеке Go; правило линтера `staticcheck SA1029`.
* **priority:** 🟡 **Medium**

---

### Кандидат 12: Захардкоженная заглушка `lastEventID = 100` в рабочем примере Long Polling
* **article/section:** `24. Long polling.md` / `## 3. Идиоматичный Go: Реализация Long Polling` (строки 123–127)
* **claim:**  
  ```go
  var lastEventID int64
  if val := r.URL.Query().Get("last_event_id"); val != "" {
      // В реальном коде: strconv.ParseInt
      lastEventID = 100 
  }
  ```
* **why it needs checking:** В обучающем материале приводится якобы готовый для запуска обработчик `LongPollHandler`. Но из-за захардкоженного значения `lastEventID = 100` реальное значение параметра `last_event_id` полностью игнорируется. Если читатель попытается протестировать логику восстановления пропущенных событий, пример поведет себя непредсказуемо. Код должен использовать реальный вызов `lastEventID, _ = strconv.ParseInt(val, 10, 64)`.
* **evidence/source needed:** Проверка листинга в `sources/10. Проектирование API и Сетевые протоколы/24. Long polling.md`.
* **priority:** 🟡 **Medium**

---

### Кандидат 13: Ограниченность Tuple Comparison при разнонаправленной сортировке и уязвимость Base64-курсоров
* **article/section:** `10. Pagination, filtering, sorting.md` / `### 2. Keyset / Cursor Pagination (Выбор Senior-инженера)` (строки 80–88)
* **claim:**  
  В качестве универсального решения для пагинации по не уникальным полям предлагается сравнение кортежей:
  ```sql
  WHERE (price, id) > (100, 452) ORDER BY price ASC, id ASC LIMIT 20;
  ```
  И указывается: «В Go мы кодируем структуру `{"price":100, "id":452}` в JSON и оборачиваем в Base64 — это и есть строка cursor для фронтенда».
* **why it needs checking:**
  1. **Разнонаправленная сортировка:** Синтаксис сравнения кортежей `(col1, col2) > (val1, val2)` в SQL математически работает **только если направления сортировки совпадают** (оба `ASC` или оба `DESC`). Если сортировка разнонаправленная (`ORDER BY price ASC, id DESC`), сравнение кортежей неприменимо — требуется разворачивать условие через булеву логику: `WHERE (price > 100) OR (price = 100 AND id < 452)`.
  2. **Незащищенный Base64-курсор:** Обычный JSON в Base64 не защищен от модификации клиентом. Злоумышленник может менять значения `id` и `price`, организуя перебор записей (ID Enumeration) или обход фильтров. В продакшен API курсоры обязаны подписываться HMAC-токеном или шифроваться.
* **evidence/source needed:** SQL Standard (Row Value Comparison); Use The Index, Luke (Keyset Pagination pitfalls).
* **priority:** 🟡 **Medium**

---

### Кандидат 14: Отсутствие упоминания ZigZag-кодирования и раздувания отрицательных чисел в Protobuf Varint
* **article/section:** `17. Protocol Buffers.md` / `## Wire Types` (строки 50–65)
* **claim:**  
  Утверждается, что тип `Varint` (Wire Type 0) упаковывает числа с алгоритмической сложностью LEB128, сжимая число 1 в 1 байт, а 150 в 2 байта.
* **why it needs checking:**
  1. В статье полностью упущен фундаментальный нюанс бинарного формата Protobuf: стандартное кодирование знаковых чисел `int32` и `int64` через стандартный Varint в дополнительном коде (two's complement) приводит к тому, что любое отрицательное число (например, `-1`) **раздувается до максимальных 10 байт в проводе**!
  2. Именно по этой причине в спецификацию Protobuf были добавлены специальные типы `sint32` и `sint64`, использующие кодирование **ZigZag** (где знаковые числа отображаются на положительные: 0 -> 0, -1 -> 1, 1 -> 2, -2 -> 3). Не упомянуть это в главе про Protobuf Wire Format — серьезный педагогический пробел.
* **evidence/source needed:** Google Protocol Buffers Encoding Documentation (Signed Integers & ZigZag Encoding).
* **priority:** 🟡 **Medium**

---

### Кандидат 15: Межмодульная несогласованность стандарта Problem Details (RFC 7807 vs RFC 9457)
* **article/section:** 
  - `9. Error handling в API.md` (строка 1 и 42)
  - `14. OpenAPI и Swagger.md` (строка 175)
  - `36. Документация API best practices.md` (строки 110, 169)
* **claim:**  
  В статье 9 прямо указано, что комитет IETF официально аннулировал RFC 7807 и заменил его спецификацией **RFC 9457 (Problem Details for HTTP APIs)**. При этом заголовок самой статьи 9 гласит «... От архитектуры до RFC 7807», а в статьях 14 и 36 в качестве актуального стандарта указывается исключительно устаревший RFC 7807.
* **why it needs checking:** Внутреннее противоречие между статьями одного модуля дезориентирует читателя относительно действующего стандарта контракта ошибок в веб-сервисах.
* **evidence/source needed:** IETF RFC 9457 (Obsoletes: 7807); сопоставление текстов статей 9, 14 и 36.
* **priority:** 🟡 **Medium**

---

### Кандидат 16: Односторонний совет возвращать `409 Conflict` на конкурентные Idempotency-запросы
* **article/section:** `13. Idempotency ключи.md` / `## Ловушки и корнер-кейсы` (строки 102–105)
* **claim:**  
  «Что сервер обязан вернуть второму запросу? Худшая ошибка — заблокировать вторую горутину через `time.Sleep` или `sync.Cond` в надежде дождаться, пока первый запрос завершится... Идиоматичный подход: Немедленно завершить обработку и вернуть клиенту статус `409 Conflict` (или `425 Too Early`)».
* **why it needs checking:**
  1. В золотом стандарте индустрии для платежных и транзакционных шлюзов (Stripe Idempotency API Specification, драфт IETF `draft-ietf-httpapi-idempotency-key`) рекомендуется именно **кратковременное удержание (Lock & Wait)** параллельного дублирующего запроса (на 5–15 секунд).
  2. Если первый запрос завершается за 200–300 мс (нормальное время транзакции), удерживаемый второй запрос сразу получает успешный результат `200 OK` с закэшированным телом первого.
  3. Немедленный возврат `409 Conflict` перекладывает всю тяжесть обработки на клиента, заставляя клиентское приложение писать сложную логику повторов с задержками и ухудшая пользовательский опыт. Утверждение, что ожидание — это «худшая ошибка», слишком категорично и односторонне.
* **evidence/source needed:** Stripe API Reference (Idempotent Requests); IETF Draft `draft-ietf-httpapi-idempotency-key-04`.
* **priority:** 🟡 **Medium**

---

### Кандидат 17: Умалчивание о ключевой роли Pact Broker в сквозном контрактном тестировании
* **article/section:** `34. Contract testing.md` / `## 4. Consumer-Driven Contracts в Go: Практика с Pact` (строки 150–254)
* **claim:**  
  Описывается локальная генерация JSON-контрактов потребителем и их локальная верификация поставщиком через `pact-go/v2`.
* **why it needs checking:** В изоляции локальный запуск тестов Pact выглядит простым, но на практике контрактное тестирование в микросервисах не работает без централизованного реестра контрактов — **Pact Broker** и инструмента верификации матриц совместимости `can-i-deploy`. Без упоминания брокера у разработчиков складывается обманчивое впечатление, что файлы пактов нужно вручную копировать между репозиториями сервисов.
* **evidence/source needed:** Pact Documentation (Pact Broker & CI/CD workflow, `can-i-deploy`).
* **priority:** 🟡 **Medium**

---

### Кандидат 18: Абсолютизация требования HATEOAS для практических REST API
* **article/section:** `1. REST. Архитектурный стиль и ограничения.md` / `## Ограничения REST` (строки 80–115)
* **claim:**  
  Утверждается, что если API не поддерживает гипермедиа как двигатель состояния приложения (HATEOAS), его нельзя называть REST API.
* **why it needs checking:** Строго академически по диссертации Роя Филдинга это верно. Однако в современной индустрии 99% сервисов используют модель зрелости Ричардсона 2-го уровня (HTTP-методы + URI ресурсов) без HATEOAS из-за избыточности ссылок в мобильных и SPA-клиентах. Стоит добавить сбалансированную оговорку о разнице между теоретическим REST и индустриальной практикой (Pragmatic REST / HTTP API).
* **evidence/source needed:** Richardson Maturity Model (Martin Fowler); Roy Fielding dissertation (2000).
* **priority:** 🟢 **Low**

---

### Кандидат 19: Обязательность заголовка `WWW-Authenticate` при ошибке 401 в JSON API
* **article/section:** `6. Статусы HTTP.md` / `### 401 Unauthorized` (строки 110–125)
* **claim:**  
  Указывается, что сервер обязан возвращать заголовок `WWW-Authenticate` при ответе `401 Unauthorized`.
* **why it needs checking:** По спецификации RFC 9110 это действительно так. Однако в веб-приложениях с аутентификацией по Bearer-токену возвращение браузерного заголовка `WWW-Authenticate: Basic ...` вызывает нежелательное появление встроенного модального окна логина браузера. В чисто сервисных REST API этот заголовок часто опускают или форматируют как `WWW-Authenticate: Bearer error="invalid_token"`. Полезно уточнить этот практический контекст.
* **evidence/source needed:** RFC 9110 Section 15.5.2; RFC 6750 (OAuth 2.0 Bearer Token Usage).
* **priority:** 🟢 **Low**

---

### Кандидат 20: Глобальная регистрация метрик через `promauto` без возможности изоляции тестов
* **article/section:** `31. API observability.md` / `## 4. Идиоматичный Prometheus Middleware` (строки 128–145)
* **claim:**  
  Метрики регистрируются через глобальные переменные `promauto.NewCounterVec` в дефолтном `prometheus.DefaultRegisterer`.
* **why it needs checking:** Использование глобального регистратора в пакетах усложняет модульное тестирование: повторный вызов инициализации в тестах приводит к панике `duplicate metrics collector registration`. В надежных архитектурах коллекторы регистрируются в кастомном `prometheus.NewRegistry()`, передаваемом через DI.
* **evidence/source needed:** Документация `prometheus/client_golang/prometheus`.
* **priority:** 🟢 **Low**

---

### Кандидат 21: Риск искажения HTTP-статуса при повторных вызовах `WriteHeader`
* **article/section:** `31. API observability.md` / `## 4. Идиоматичный Prometheus Middleware` (строки 147–156)
* **claim:**  
  ```go
  type statusResponseWriter struct {
      http.ResponseWriter
      statusCode int
  }
  func (rw *statusResponseWriter) WriteHeader(code int) {
      rw.statusCode = code
      rw.ResponseWriter.WriteHeader(code)
  }
  ```
* **why it needs checking:** Если хэндлер или сторонний middleware по ошибке вызывает `WriteHeader` несколько раз (например, сначала 200, а затем в блоке ошибки 500), поле `rw.statusCode` перезапишется последним значением, хотя в реальный сетевой сокет ушел первый статус. Для идеальной надежности в `statusResponseWriter` добавляют булев флаг `wroteHeader bool`.
* **evidence/source needed:** Документация `http.ResponseWriter.WriteHeader`.
* **priority:** 🟢 **Low**

---

### Кандидат 22: Систематический пропуск проверки ошибки возвращаемого значения `json.NewEncoder(w).Encode(...)`
* **article/section:** Системно в статьях `10. Pagination, filtering, sorting.md`, `12. Caching HTTP.md`, `24. Long polling.md`
* **claim:**  
  В примерах пишется:
  ```go
  json.NewEncoder(w).Encode(data)
  ```
  без проверки возвращаемой ошибки `error`.
* **why it needs checking:** Хотя в простых примерах это допустимо для краткости, при обрыве соединения клиентом или повреждении структур данных игнорирование ошибки может маскировать сетевые сбои в логах. Рекомендуется сопровождать вызов явным комментарием или логированием.
* **evidence/source needed:** Effective Go; Go standard library guidelines.
* **priority:** 🟢 **Low**

---

## 🔍 Системные белые пятна и архитектурные упущения (Blind Spots)

В ходе анализа выявлены 5 важных системных тем, которые критически важны для проектирования современных сетевых API на Go, но выпали из содержания Модуля 10:

1. **Полное отсутствие методологии Chaos Engineering (подмена темы в статье 35):**  
   Из-за того, что статья 35 полностью посвящена Graceful Shutdown, в модуле не рассмотрены настоящие инструменты тестирования сетевой деградации:
   - Использование **Toxiproxy** (инструмент от Shopify) для симуляции задержек (Latency), джиттера, разрыва соединений (TCP Reset) и ограничения пропускной способности в integration-тестах Go API.
   - Тестирование разделения сети (Network Partition) и сбоев DNS в кластерах через **Chaos Mesh** / **LitmusChaos**.
   - Паттерны устойчивости: Circuit Breaker (`gobreaker`), Retries с Exponential Backoff и Full Jitter в сетевых клиентах.

2. **Уязвимость HTTP/2 Rapid Reset (CVE-2023-44487) и DoS через gRPC/HTTP/2 стримы:**  
   В статьях 16–19 подробно разбираются HTTP/2 и gRPC, однако не упомянута крупнейшая атака на протокол HTTP/2 — **Rapid Reset**. Атакующий непрерывно отправляет поток запросов `HEADERS`, за которым мгновенно следует `RST_STREAM`. В Go это приводило к лавинообразному созданию горутин и мгновенному исчерпанию ресурсов сервера при нулевом сетевом трафике. Важно раскрыть, как рантайм Go (начиная с версий Go 1.21.3 и 1.20.10) защищается от этого через ограничение сброшенных потоков и настройку `MaxConcurrentStreams`.

3. **Утечка TCP-соединений в HTTP-клиентах при отсутствии `io.Copy(io.Discard, resp.Body)`:**  
   В обсуждении сетевых клиентов упущен классический подводный камень механизма HTTP Keep-Alive в Go: если клиент закрывает `resp.Body.Close()` до того, как тело ответа было полностью прочитано до конца (`io.EOF`), нижележащий сетевой транспорт `http.Transport` не может повторно использовать данный TCP-сокет и вынужден разрывать соединение пакетом `RST`. В микросервисных архитектурах это приводит к исчерпанию портов (TIME_WAIT exhaustion) и высокому расходу CPU на постоянные повторные TLS-хэндшейки. Перед закрытием ответа всегда необходимо вызывать `_, _ = io.Copy(io.Discard, resp.Body)`.

4. **Кэширование Preflight-запросов CORS (`Access-Control-Max-Age`):**  
   В статьях о безопасности и производительности API упущена критическая настройка CORS-заголовков. Без заголовка `Access-Control-Max-Age` браузер отправляет предварительный запрос `OPTIONS` (Preflight) перед **каждым** пользовательским запросом `POST`, `PUT`, `DELETE` или запросом с кастомными заголовками, удваивая общую задержку (Latency) для фронтенда и увеличивая нагрузку на сетевой шлюз ровно в 2 раза.

5. **Потоковые ETag для больших объемов данных (Streaming ETag vs In-memory hashing):**  
   В статье 12 подробно разобран антипаттерн вычисления MD5 от всего буфера JSON в памяти, но не показано, как вычислять ETag для динамических тяжелых ресурсов (файлов, отчетов, экспортов данных), где версия в БД отсутствует. В таких сценариях требуется потоковое хэширование через `io.MultiWriter` или генерация составных ETag на базе размера файла и даты модификации (`Content-Length` + `Last-Modified`).

---

## 📋 Итог и рекомендации для следующего этапа проверки

Модуль 10 («Проектирование API и Сетевые протоколы») — фундаментальный и технически зрелый блок энциклопедии. Авторы глубоко понимают многие тонкости сетевого стека Go (нововведения Go 1.20 `httputil.ProxyRequest.Rewrite`, нововведения Go 1.22 в `r.Pattern`, механику `http.MaxBytesReader`, атаку Key Confusion в JWT, нюансы gRPC streaming). 

Тем не менее, обнаружен ряд критических дефектов содержания и практических ошибок в коде:

1. **Критические точки вмешательства:**
   - **Статья 35:** Принять решение о судьбе статьи `35. Chaos testing API.md`: либо переименовать её в соответствии с реальным содержанием («Graceful Shutdown и Pod Lifecycle в Go»), а статью по реальному Chaos Testing написать заново; либо переписать статью 35, включив в неё Toxiproxy, Chaos Mesh и fault-injection тестирование API.
   - **Исправление листингов с состояниями гонки и багами рантайма:** Устранить broken double-checked locking в `11. Rate limiting в API.md`, исправить преждевременный возврат `nil` при `io.EOF` в `18. gRPC streaming.md`, добавить обязательные заголовки при `304 Not Modified` в `12. Caching HTTP.md`, защитить мапу от утечки памяти и добавить Redis Pipeline в `30. API rate limiting и quotas.md`.
   - **Замена устаревшего `Subject.CommonName` на SAN** в `29. mTLS в сервисах.md`.
   - **Исправление единичного `Read` на потоковое чтение** в `39. API performance.md`.
   - **Исправление LaTeX-разметки:** Заменить символы табуляции `0x09` на обратный слэш `\` в формулах KaTeX (`\text`, `\times`, `\to`).

2. **Следующие шаги:**
   - Передать исследовательский бриф инженеру-фактчекеру для точечной сверки и внесения правок в файлы `sources/10. Проектирование API и Сетевые протоколы/`.
   - Синхронизировать терминологию стандартов RFC (RFC 9457 vs RFC 7807) по всем статьям модуля.
   - Дополнить модуль рекомендациями по защите от HTTP/2 Rapid Reset, сбросу тел ответов через `io.Copy(io.Discard, ...)` и кэшированию CORS Preflight.
