# 🧭 Исследовательский скаут-отчет: Модуль 14. Распределенные системы на Go

> *«Распределенная система — это система, в которой сбой компьютера, о существовании которого вы даже не подозревали, может сделать ваш собственный компьютер непригодным для использования».*  
> — Лесли Лэмпорт

---

## 📌 Паспорт модуля и объем проверки

* **Название модуля:** Модуль 14: Распределенные системы на Go
* **Расположение исходных материалов:** `sources/14. Распределенные системы на Go/`
* **Количество статей:** 74 статьи в 10 тематических разделах:
  1. `01. Основы` (8 статей)
  2. `02. Консенсус` (8 статей)
  3. `03. Данные и согласованность` (8 статей)
  4. `04. Микросервисы` (10 статей)
  5. `05. Надежность` (8 статей)
  6. `06. Сеть` (6 статей)
  7. `07. Kubernetes и деплой` (8 статей)
  8. `08. Практика` (10 статей)
  9. `09. Паттерны` (7 статей)
  10. `10. Итог` (1 статья)
* **Общий объем текста:** ~19 976 строк Markdown
* **Роль и цель:** Первый независимый сквозной проход (First-Pass Fact-Check Research Scout). Широкий поиск потенциально некорректных, устаревших, вводящих в заблуждение, упрощенных, платформенно- и рантайм-зависимых утверждений, состояний гонки (Race Conditions), взаимных блокировок (Deadlocks), утечек дескрипторов сокетов и памяти, нарушений контрактов стандартной библиотеки Go, а также системных архитектурных белых пятен (Blind Spots).

---

## 📊 Сводка найденных кандидатов

| Приоритет | Кол-во | Описание характера находок |
|:---:|:---:|---|
| 🔴 **High** | **10** | Состояние гонки (Race Condition / TOCTOU) в примере реализации идемпотентности, приводящее к двойным списаниям; некомпилируемый листинг `func RegisterRoutes(mux *http.NewServeMux)` (использование функции-конструктора в качестве типа); гарантированный взаимный дедлок (Lock Inversion AB-BA) при двустороннем слиянии `GCounter.Merge`; грубое нарушение правил Go `copylocks` при копировании структуры, содержащей `sync.RWMutex`, по значению в `ResolveConflicts`; логический баг и риск паники `index out of range` в оркестраторе саги при получении дубликатов сообщений с фиктивной компенсацией fire-and-forget; систематическая утечка сокетов и дескрипторов TCP в шлюзе `aggregateHandler` при любых не-200 ответах бэкенда; математически неверный расчет кворума синхронной репликации в `StrongServer`, ломающий гарантии в 2-нодовых кластерах; тихая потеря до 99 логов из батча и до 1024 из канала при завершении контекста в `AsyncHandler` с нарушением контракта `slog.Handler`; логический баг пропуска отставших реплик при одинаковых метках времени в `ReadWithRepair`; превращение 1-миллисекундного сбоя базы данных в 100-миллисекундное зависание по таймауту в примере ликвидации утечки горутин. |
| 🟡 **Medium** | **12** | Использование устаревшего и отключенного поля `Subject.CommonName` (CN) вместо SAN в mTLS-авторизации; опасная рекомендация передавать контекст входящего запроса `r.Context()` в фоновую горутину `go sendEmailNotification(ctx, ...)` без отвязки через `context.WithoutCancel`; ложный миф о наличии встроенного DNS-кэширования в стандартном пакете Go `net`; безусловный `return true` в валидаторе `IsTransient`, делающий любые фатальные клиентские ошибки повторяемыми, и использование deprecated метода `netErr.Temporary()`; утечка секретов в открытом виде при логировании `SecretString` через `log/slog` из-за отсутствия интерфейса `slog.LogValuer`; синхронная блокировка воркера в шейпере `PacedSender`, обрушивающая пропускную способность; незафиксированный статус ошибки в спанах OpenTelemetry (`span.RecordError` без `span.SetStatus`); потеря событий `fsnotify` при подписке на симлинк ConfigMap из-за привязки inotify к inode; лексикографическое сравнение строковых представлений LSN базы данных, ломающее гарантию Read-Your-Writes; устаревший `httputil.ReverseProxy.Director` (вместо `Rewrite`) с риском двойных слэшей и некорректным `Host`; опасное удаление чужого распределенного лока `redisClient.Del` без проверки значения через Lua-скрипт; использование типа `float64` для хранения денег и баланса в Event Sourcing с риском накопления погрешностей IEEE 754. |
| 🟢 **Low** | **6** | Отмена контекста записи на отстающие узлы при наборе кворума $W$, искусственно деградирующая итоговый фактор репликации; использование `http.Get` без таймаутов и пропуск `ErrTooManyRequests` в клиенте Circuit Breaker; устаревший `atomic.Value` с ручным кастом типов вместо `atomic.Pointer[T]` и миф о чтении за 1 такт CPU через `LOCK CMPXCHG`; использование `r.RemoteAddr` с сырым портом в качестве ключа rate limiter; ошибочное утверждение о сложности поиска $O(\log n)$ в односвязном дереве `context.Context`; рекомендация проверки readiness probe через прямой `PingContext` к БД без упоминания риска каскадного отключения всех реплик. |

---

## 🧭 Каталог кандидатов на углубленный фактчекинг

---

### Кандидат 1: Состояние гонки (Race Condition / TOCTOU) в примере реализации идемпотентности
* **article/section:** `09. Паттерны/7. Anti patterns микросервисов.md` / `## 6. Неидемпотентные мутации (Missing Idempotency)` (строки 197–228)
* **claim:**  
  ```go
  func (s *PaymentService) Charge(ctx context.Context, req ChargeRequest, idempotencyKey string) error {
      // 1. Проверяем в Redis, обрабатывали ли мы данный Idempotency-Key
      exists, err := s.cache.Get(ctx, idempotencyKey)
      if err == nil && exists != "" {
          return nil
      }

      // 2. Выполняем финансовую проводку в базе данных
      err = s.db.Withdraw(ctx, req.UserID, req.Amount)
      if err != nil {
          return fmt.Errorf("transaction failed: %w", err)
      }

      // 3. Атомарно сохраняем ключ с разумным TTL (например, 24 часа)
      _ = s.cache.Set(ctx, idempotencyKey, "processed", 24*time.Hour)
      return nil
  }
  ```
  В тексте листинг подается как образцовое «Инженерное решение» проблемы повторных списаний средств.
* **why it needs checking:** В коде содержится классическое состояние гонки **Time-of-Check to Time-of-Use (TOCTOU)**:
  1. Если два одинаковых запроса приходят одновременно (двойной клик пользователя, агрессивный ретрай мобильного клиента или service mesh), обе горутины параллельно вызывают `s.cache.Get(ctx, idempotencyKey)`.
  2. Для обеих горутин ключ еще не записан в Redis (`exists == ""`).
  3. Обе горутины параллельно вызывают `s.db.Withdraw(ctx, req.UserID, req.Amount)`!
  4. Со счета клиента **дважды списываются деньги**.
  5. После этого обе горутины вызывают `s.cache.Set(...)`.
  Идемпотентность полностью разрушена. Для обеспечения гарантий ключ идемпотентности обязан атомарно резервироваться **ДО** бизнес-операции (через `SET key "processing" NX EX 60` в Redis, либо через уникальный констрейнт `INSERT INTO idempotency_keys` в одной транзакции с бизнес-логикой).
* **evidence/source needed:** Martin Fowler: Patterns of Distributed Systems (Idempotent Receiver); Stripe Engineering: Designing robust and predictable APIs with idempotency; Redis Documentation: `SET key value [NX|XX] [GET] [EX seconds]`.
* **priority:** 🔴 **High**

---

### Кандидат 2: Некомпилируемый листинг регистрации маршрутов (`http.NewServeMux` как тип)
* **article/section:** `08. Практика/4. CI_CD для микросервисов.md` / `### Healthchecks (Liveness и Readiness)` (строка 234)
* **claim:**  
  ```go
  // RegisterRoutes настраивает маршруты healthcheck
  func (c *Checker) RegisterRoutes(mux *http.NewServeMux) {
      // Liveness: проверяет только факт того, что сервер живет и не завис в deadlock
      mux.HandleFunc("GET /healthz", func(w http.ResponseWriter, r *http.Request) {
  ...
  ```
* **why it needs checking:** Функция `http.NewServeMux` в стандартной библиотеке Go является функцией-конструктором (`func NewServeMux() *ServeMux`), а не типом данных. Попытка скомпилировать этот код завершится фатальной ошибкой компилятора:  
  `http.NewServeMux is not a type`.  
  Корректный тип аргумента — `*http.ServeMux`. Это прямая синтаксическая ошибка в учебном материале.
* **evidence/source needed:** Документация пакета `net/http` (`go doc net/http.NewServeMux`, `go doc net/http.ServeMux`).
* **priority:** 🔴 **High**

---

### Кандидат 3: Гарантированный взаимный дедлок (AB-BA Deadlock) в методе слияния `GCounter.Merge`
* **article/section:** `03. Данные и согласованность/7. CRDT.md` / `### Реализация G-Counter на Go` (строки 185–199)
* **claim:**  
  ```go
  // Merge выполняет операцию слияния полурешетки (LUB / Join)
  func (c *GCounter) Merge(other *GCounter) {
      c.mu.Lock()
      defer c.mu.Unlock()

      other.mu.RLock()
      defer other.mu.RUnlock()

      for node, remoteVal := range other.state {
          if currentVal, exists := c.state[node]; !exists || remoteVal > currentVal {
              c.state[node] = remoteVal
          }
      }
  }
  ```
* **why it needs checking:** В коде заложен классический дедлок из-за инверсии порядка захвата блокировок (Lock Ordering Inversion):
  1. Пусть узел $A$ и узел $B$ синхронизируются по протоколу Gossip или HTTP в параллельных горутинах.
  2. Горутина 1 вызывает `nodeA.Merge(nodeB)`: захватывает `nodeA.mu.Lock()` и пытается взять `nodeB.mu.RLock()`.
  3. Горутина 2 одновременно вызывает `nodeB.Merge(nodeA)`: захватывает `nodeB.mu.Lock()` и пытается взять `nodeA.mu.RLock()`.
  4. Горутина 1 ждет освобождения блокировки $B$, а Горутина 2 ждет освобождения блокировки $A$.
  5. Процесс намертво зависает в дедлоке.
  Для безопасного слияния метод `Merge` должен либо принимать изолированный снимок состояния `otherState map[string]int64` (который уже возвращается методом `other.StateCopy()`), либо захватывать блокировки в строго детерминированном глобальном порядке (например, сравнивая строковые `nodeID`).
* **evidence/source needed:** Go Memory Model; обнаружение дедлоков в тестах через `go test -race` и анализ дампов горутин.
* **priority:** 🔴 **High**

---

### Кандидат 4: Нарушение правил Go `copylocks` при копировании структуры с мьютексом по значению
* **article/section:** `03. Данные и согласованность/6. Conflict resolution.md` / `### Пример: Слияние корзины покупателя` (строки 76–119)
* **claim:**  
  ```go
  type Cart struct {
      Items  []string
      VClock vclock.VectorClock
  }

  func ResolveConflicts(siblings []Cart) Cart {
      ...
      mergedVClock := vclock.New("app-resolver")
      for _, s := range siblings {
          ...
          mergedVClock.Merge(s.VClock.Clone())
      }

      result := Cart{
          VClock: *mergedVClock,
          Items:  make([]string, 0, len(finalItems)),
      }
      ...
      return result
  }
  ```
* **why it needs checking:** Структура `vclock.VectorClock`, объявленная в статье [[5. Vector clocks]] (строка 148), содержит поле `mu sync.RWMutex`:
  ```go
  type VectorClock struct {
      mu     sync.RWMutex
      nodeID string
      vc     map[string]uint64
  }
  ```
  В языке Go структуры, содержащие `sync.Mutex` или `sync.RWMutex`, **категорически запрещено копировать по значению**, так как внутреннее состояние мьютекса оказывается размноженным.  
  В приведенном коде копирование происходит многократно:
  1. В сигнатуре `func ResolveConflicts(siblings []Cart) Cart` (передача и возврат по значению);
  2. В цикле `for _, s := range siblings` (копирование каждого элемента слайса);
  3. В строке `VClock: *mergedVClock` (разыменование указателя с копированием внутреннего `sync.RWMutex`).
  Стандартный линтер Go (`go vet`) завершается с ошибкой: `copylocks: assignment copies lock value to result: myproject/vclock.VectorClock contains sync.RWMutex`.
* **evidence/source needed:** Документация Go: `go vet` copylocks check; `sync.Mutex` documentation ("A Mutex must not be copied after first use").
* **priority:** 🔴 **High**

---

### Кандидат 5: Логический сбой автомата саги и паника `index out of range` при дубликатах сообщений
* **article/section:** `09. Паттерны/1. Saga pattern.md` / `### Обработчик шагов (упрощенно)` (строки 234–286)
* **claim:**  
  ```go
  func (o *Orchestrator) HandleReply(reply SagaReply) {
      saga, err := o.repo.GetSaga(reply.SagaID)
      ...
      if reply.Success {
          saga.Steps[saga.CurrentStep].Status = StatusCompleted
          saga.CurrentStep++

          if saga.CurrentStep == len(saga.Steps) {
              saga.Status = StatusCompleted
              ...
              return
          }
          o.executeStep(saga, saga.CurrentStep)
      } else {
          saga.Status = StatusCompensating
          o.compensate(saga)
      }
      ...
  }

  func (o *Orchestrator) compensate(saga *SagaInstance) {
      for i := saga.CurrentStep - 1; i >= 0; i-- {
          step := &saga.Steps[i]
          if step.Status == StatusCompleted && step.Compensate {
              o.sendCompensateCommand(saga.ID, *step)
          }
      }
      saga.Status = StatusFailed
  }
  ```
* **why it needs checking:** В архитектуре оркестратора заложены две критические ошибки:
  1. **Игнорирование номера шага в ответе:** Структура `SagaReply` содержит поле `Step int`, однако функция `HandleReply` **вообще не проверяет**, совпадает ли `reply.Step` с `saga.CurrentStep`! Если из брокера (Kafka/RabbitMQ с гарантией at-least-once) придет дубликат ответа от шага 0 в момент, когда сага уже находится на шаге 1, код по ошибке применит его к шагу 1 (`saga.Steps[1].Status = StatusCompleted`) и инкрементирует `CurrentStep`. Если же сага уже завершена, обращение `saga.Steps[saga.CurrentStep]` вызовет панику `runtime error: index out of range`!
  2. **Иллюзорная компенсация (Fire-and-Forget):** Функция `compensate` отправляет команды отката асинхронно в цикле и **немедленно объявляет сагу проваленной** (`saga.Status = StatusFailed`). Если компенсирующая транзакция потеряется в сети или упадет, оркестратор никогда об этом не узнает. В надежных сагах компенсация представляет собой полноценный зеркальный конечный автомат с ожиданием подтверждений от каждого компенсирующего шага.
* **evidence/source needed:** Chris Richardson: Microservices Patterns (Chapter 4: Managing transactions with sagas); Temporal.io documentation: Saga orchestration and compensation guarantees.
* **priority:** 🔴 **High**

---

### Кандидат 6: Утечка соединений и сокетов (Socket Leak) в Gateway `aggregateHandler` при не-200 ответах
* **article/section:** `09. Паттерны/4. API Gateway.md` / `### Паттерн Aggregator: спасение от Network Chattiness` (строки 284–312)
* **claim:**  
  ```go
  // Параллельный запрос 1: User Service
  wg.Add(1)
  go func() {
      defer wg.Done()
      client := http.Client{Timeout: 1 * time.Second}
      resp, err := client.Get("http://user-service/profile")
      if err == nil && resp.StatusCode == http.StatusOK {
          defer resp.Body.Close()
          body, _ := io.ReadAll(resp.Body)
          userDataChan <- body
          return
      }
      userDataChan <- []byte("{}")
  }()
  ```
* **why it needs checking:** Если удаленный сервис возвращает статус, отличный от 200 OK (например, `404 Not Found`, `500 Internal Server Error`, `502 Bad Gateway`):
  1. `err == nil`, но `resp.StatusCode == http.StatusOK` ложно;
  2. Блок `if` пропускается целиком;
  3. Вызов `defer resp.Body.Close()` **не регистрируется и не выполняется**!
  4. Тело ответа остается невычитанным, соединение не возвращается в пул `http.Transport`, а низкоуровневый дескриптор сокета ОС зависает навсегда.
  При деградации нижележащего сервиса шлюз за считанные секунды исчерпает лимит файловых дескрипторов (`too many open files`) и упадет. Кроме того, создание нового экземпляра `http.Client` внутри каждой горутины запроса создает бессмысленную нагрузку на аллокатор памяти и игнорирует контекст входящего запроса `r.Context()`.
* **evidence/source needed:** Go `net/http` documentation for `Client.Do` and `Response.Body.Close`; Staticcheck check `SA5001`.
* **priority:** 🔴 **High**

---

### Кандидат 7: Ошибочная формула кворума синхронной репликации в `StrongServer`
* **article/section:** `03. Данные и согласованность/2. Strong vs eventual consistency.md` / `### Строгий подход (Synchronous Replication)` (строки 167–180)
* **claim:**  
  ```go
  // ШАГ 3: Блокирующее ожидание сбора Кворума большинства
  acks := 1 // Учитываем собственный подтвержденный голос
  quorum := (len(s.replicas) / 2) + 1

  for acks < quorum {
      select {
      case <-ackCh:
          acks++
      case <-ctx.Done():
          return fmt.Errorf("таймаут сбора кворума: %w", ctx.Err())
      }
  }
  return nil
  ```
* **why it needs checking:** В формуле расчета кворума допущена грубая ошибка: размер кластера вычисляется исключительно из количества реплик `len(s.replicas)`, а не из общего числа узлов кластера $N = 1 + 	ext{len}(	ext{replicas})$:
  - Рассмотрим классический кластер из **двух узлов** (1 Мастер + 1 Реплика, $N=2$). Строгое большинство для двух узлов — это $2$ подтверждения (оба узла).
  - Что рассчитывает код: `len(s.replicas) == 1`.  
    `quorum := (1 / 2) + 1` $	o$ в целочисленной арифметике Go: `0 + 1 = 1`.
  - Мастер инициализирует `acks := 1` (свой голос).
  - Проверяется условие цикла: `acks < quorum` $	o$ `1 < 1` — **условие ложно!**
  - Цикл ожидания реплик **не выполняется вовсе**!
  - Мастер записывает данные локально и мгновенно возвращает клиенту успех, вообще не дожидаясь ответа от единственной реплики! Заявленная «строгая синхронная репликация» вырождается в неконсистентную асинхронную запись.
  Корректная формула: `totalNodes := len(s.replicas) + 1; quorum := (totalNodes / 2) + 1`.
* **evidence/source needed:** Математическое определение строгого большинства: $\lfloor N/2 floor + 1$; Raft Consensus Algorithm Specification.
* **priority:** 🔴 **High**

---

### Кандидат 8: Тихая потеря логов при остановке и нарушение контракта `slog.Handler` в `AsyncHandler`
* **article/section:** `08. Практика/5. Логирование в распределенных системах.md` / `### Асинхронное логирование (Zero-Alloc Flush)` (строки 214–292)
* **claim:**  
  ```go
  func (h *AsyncHandler) Handle(ctx context.Context, r slog.Record) error {
      payload := map[string]any{
          "time":  r.Time.Format(time.RFC3339Nano),
          "level": r.Level.String(),
          "msg":   r.Message,
      }
      if val := ctx.Value("trace_id"); val != nil {
          payload["trace_id"] = val
      }
      ...
  }

  func (h *AsyncHandler) WithAttrs(attrs []slog.Attr) slog.Handler { return h }
  func (h *AsyncHandler) WithGroup(name string) slog.Handler        { return h }
  ```
  А в фоновом цикле записи:
  ```go
  case <-ctx.Done():
      close(h.done)
      return
  ```
* **why it needs checking:** В реализации присутствуют три критических бага:
  1. **Тихая потеря логов при остановке (Silent Data Loss):** При отмене `ctx.Done()` горутина мгновенно закрывает канал `h.done` и завершает работу. Все записи, накопленные в текущем срезе `batch` (до 99 сообщений!), а также все сообщения, стоящие в очереди буферизованного канала `h.logCh` (до 1024 записей!), **бесследно выбрасываются и никогда не записываются на диск**. Самые важные предсмертные логи сервиса теряются. Требуется процедура сброса остатка (drain).
  2. **Нарушение контракта `slog.Handler`:** Методы `WithAttrs` и `WithGroup` обязаны возвращать **новый** изолированный обработчик с примененными атрибутами. Возврат `return h` приводит к тому, что любые атрибуты, добавленные через `logger.With(...)`, полностью игнорируются!
  3. **Игнорирование атрибутов записи `r.Attrs`:** Метод `Handle` сериализует только время, уровень и сообщение, полностью игнорируя пользовательские поля, переданные в `slog.Info("msg", "user_id", 123)`.
* **evidence/source needed:** Документация пакета Go `log/slog` (Handler interface contract, `slog.HandlerWithOptions`); Uber Zap buffer flush guidelines.
* **priority:** 🔴 **High**

---

### Кандидат 9: Алгоритмический дефект пропуска отставших реплик в `ReadWithRepair`
* **article/section:** `03. Данные и согласованность/3. Read repair.md` / `## Идиоматичный Go: Read Repair с таймаутами` (строки 131–141)
* **claim:**  
  ```go
  if resp.Timestamp > latestData.Timestamp {
      // Нашли более свежие данные: все ранее виденные узлы объявляются отставшими
      if latestData.Timestamp > 0 {
          staleNodes = append(staleNodes, latestData.NodeID)
      }
      latestData = resp
  } else if resp.Timestamp < latestData.Timestamp {
      // Текущий ответ отстал от лидера
      staleNodes = append(staleNodes, resp.NodeID)
  }
  ```
* **why it needs checking:** Алгоритм инкрементального поиска отстающих узлов ошибочен при получении ответов с одинаковыми таймстемпами:
  - Допустим, опрашиваются 3 реплики: Узел 1, Узел 2, Узел 3.
  - Порядок прихода сетевых ответов:
    1. Узел 1 отвечает со старым значением: $ts = 10$. `latestData` становится Узел 1 ($ts=10$). `staleNodes = []`.
    2. Узел 2 отвечает со старым значением: $ts = 10$. Условие `>` ложно ($10 > 10$ — false), условие `<` ложно ($10 < 10$ — false). Ни одна ветка не срабатывает! Узел 2 **не добавляется в `staleNodes`**.
    3. Узел 3 отвечает со свежим значением: $ts = 20$. Срабатывает ветка `>`. В `staleNodes` добавляется `latestData.NodeID` (Узел 1). `latestData` становится Узел 3 ($ts=20$).
  - Итог: в `staleNodes` попал только Узел 1. **Узел 2 остался отставшим, но ремонт для него никогда не запустится!**
  Корректный подход: сохранять все ответы в срез или мапу, после чего одним проходом найти максимальный $ts_{\max}$ и отправить в ремонт все узлы с $ts < ts_{\max}$.
* **evidence/source needed:** Cassandra Read Repair internals; Dynamo paper (Amazon, Section 4.4).
* **priority:** 🔴 **High**

---

### Кандидат 10: Превращение мгновенного сбоя в 100-мс зависание в примере исправления утечки горутин
* **article/section:** `08. Практика/9. Production incidents.md` / `### Инцидент 1: Утечка горутин` (строки 270–289)
* **claim:**  
  ```go
  func handlerWithCtx(w http.ResponseWriter, r *http.Request) {
      ctx, cancel := context.WithTimeout(r.Context(), 100*time.Millisecond)
      defer cancel()

      ch := make(chan string, 1)
      go func() {
          data, err := fetchDataWithContext(ctx)
          if err == nil {
              ch <- data
          }
      }()

      select {
      case data := <-ch:
          fmt.Fprint(w, data)
      case <-ctx.Done():
          http.Error(w, "timeout", http.StatusGatewayTimeout)
      }
  }
  ```
  Позиционируется как «Долгосрочное системное исправление» инцидента.
* **why it needs checking:** Если фоновая функция `fetchDataWithContext` завершается мгновенной ошибкой (например, база данных разорвала TCP-соединение через 1 мс или вернула ошибку валидации):
  1. `err == nil` ложно. В канал `ch` ничего не отправляется!
  2. Горутина хэндлера зависает в блоке `select`.
  3. Поскольку канал пуст, хэндлер сидит в ожидании все 100 миллисекунд таймаута!
  4. По истечении 100 мс срабатывает `<-ctx.Done()`, и клиенту возвращается ложный статус `504 Gateway Timeout` с текстом `"timeout"`!
  Мгновенный отказ бэкенда маскируется под таймаут, вызывая 100-кратный рост задержки (Latency Penalty) на ровном месте. Канал обязан передавать структуру с ошибкой `struct { data string; err error }`, чтобы при любой ошибке хэндлер реагировал мгновенно.
* **evidence/source needed:** Идиомы Go Concurrency (Errgroup / Result Channel); Dave Cheney: Concurrency Made Easy.
* **priority:** 🔴 **High**

---

### Кандидат 11: Использование устаревшего и отключенного поля `Subject.CommonName` (CN) в mTLS
* **article/section:** `06. Сеть/3. mTLS.md` / `### Серверная часть` (строки 121–127)
* **claim:**  
  ```go
  if len(r.TLS.PeerCertificates) > 0 {
      clientCert := r.TLS.PeerCertificates[0]
      clientIdentity := clientCert.Subject.CommonName
      w.Write([]byte("Успешная mTLS авторизация: " + clientIdentity))
      return
  }
  ```
* **why it needs checking:** Использование `Subject.CommonName` (CN) для идентификации хостов и сервисов в X.509 сертификатах официально объявлено **deprecated в RFC 6125 и RFC 5280**.  
  В стандартной библиотеке Go начиная с версии 1.15 верификация по CommonName отключена по умолчанию, а флаг обратной совместимости `GODEBUG=x509ignoreCN=0` был полностью удален в Go 1.17. В современных распределенных архитектурах (Service Mesh Istio, SPIFFE/SPIRE, Linkerd) цифровая личность микросервиса передается исключительно через **SAN (Subject Alternative Name)** в виде URI (`spiffe://cluster.local/ns/prod/sa/payment-service`) или DNS (`clientCert.URIs` / `clientCert.DNSNames`).
* **evidence/source needed:** RFC 6125 (Section 2.3); Go 1.15 / 1.17 Release Notes (`x509ignoreCN`); SPIFFE Identity and X.509 Standards.
* **priority:** 🟡 **Medium**

---

### Кандидат 12: Опасная рекомендация передачи контекста запроса в асинхронную горутину
* **article/section:** `08. Практика/7. Correlation ID.md` / `## Ловушки и частые ошибки` (строки 269–282)
* **claim:**  
  ```go
  // ❌ ОШИБКА: контекст потерян!
  go sendEmailNotification(orderData)

  // ✅ ПРАВИЛЬНО: сквозная передача
  go sendEmailNotification(ctx, orderData)
  ```
* **why it needs checking:** Если переменная `ctx` получена из входящего HTTP-запроса (`r.Context()`), то при завершении HTTP-хендлера стандартный сервер Go **немедленно отменяет контекст запроса** (`context.Canceled`).  
  Фоновая горутина `sendEmailNotification(ctx, orderData)`, попытавшись выполнить сетевой вызов к SMTP-серверу или запись в БД с этим контекстом, немедленно упадет с ошибкой `context canceled`!  
  В Go 1.21+ для решения этой проблемы внедрена специальная функция **`context.WithoutCancel(ctx)`**, которая сохраняет все значения контекста (TraceID, CorrelationID, UserID), но отвязывает его от жизненного цикла завершившегося HTTP-запроса. Без указания этого нюанса рекомендация в учебнике приводит к отказу фоновых задач.
* **evidence/source needed:** Go 1.21 Release Notes (`context.WithoutCancel`); документация `net/http.Request.Context()`.
* **priority:** 🟡 **Medium**

---

### Кандидат 13: Ложный миф о наличии встроенного DNS-кэширования в стандартном пакете Go `net`
* **article/section:** `04. Микросервисы/8. Service discovery.md` / `> [!info] Под капотом: Ротация и DNS Caching в Go` (строка 192)
* **claim:**  
  *«По умолчанию резолвер в стандартном пакете Go `net` кэширует DNS-ответы операционной системы. Если ваше приложение обращается к соседнему сервису через имя хоста, убедитесь, что вы не удерживаете постоянный TCP-коннект к одному-единственному поду вечно...»*
* **why it needs checking:** Это популярное, но технически абсолютно неверное утверждение:
  1. В стандартной библиотеке Go (`net.Resolver`) **никогда не было и нет встроенного DNS-кэша**. Каждый вызов `LookupHost` / `DialContext` выполняет полноценный сетевой DNS-запрос к системным серверам (если в ОС не запущен внешний кэширующий демон вроде `systemd-resolved` или `nscd`).
  2. Проблема залипания трафика на одном IP-адресе в Go вызвана исключительно **механизмом Keep-Alive в `http.Transport`**: однажды открытое TCP-соединение переиспользуется для сотен последующих HTTP-запросов, из-за чего повторный DNS-резолвинг просто не вызывается.
* **evidence/source needed:** Исходный код `src/net/lookup.go` и `src/net/dnsclient_unix.go`; Go Issue #24796.
* **priority:** 🟡 **Medium**

---

### Кандидат 14: Использование deprecated `netErr.Temporary()` и безусловный повтор любых ошибок в Retry
* **article/section:** `05. Надежность/2. Retry и backoff.md` / `### Реализация на современном Go` (строки 148–162)
* **claim:**  
  ```go
  func IsTransient(err error) bool {
      if err == nil {
          return false
      }

      var netErr net.Error
      if errors.As(err, &netErr) && (netErr.Timeout() || netErr.Temporary()) {
          return true
      }

      // Дополнительно: здесь проверяются HTTP 502 Bad Gateway, 503, 504
      return true
  }
  ```
* **why it needs checking:** Здесь присутствуют сразу две ошибки:
  1. **Deprecated API:** Метод `netErr.Temporary()` объявлен **устаревшим (deprecated)** еще в версии Go 1.18. Официальная документация Go прямо указывает: *"Temporary is deprecated. Most network errors were never meant to be temporary, and callers that check Temporary usually intend to check Timeout instead."* Линтер `staticcheck` выдает предупреждение `SA1019`.
  2. **Безусловный `return true`:** В конце функции написано `return true`. Это означает, что **любая** ошибка приложения (например, `400 Bad Request`, `401 Unauthorized`, `404 Not Found`, `422 Unprocessable Entity`, ошибка парсинга JSON или нарушение уникального ключа в БД) будет признана «временной» и будет бессмысленно повторяться максимальное число раз, увеличивая нагрузку на сервисы!
* **evidence/source needed:** Go standard library `net.Error` documentation; Staticcheck `SA1019`.
* **priority:** 🟡 **Medium**

---

### Кандидат 15: Утечка паролей в открытом виде при логировании `SecretString` через `log/slog`
* **article/section:** `04. Микросервисы/10. Secrets management.md` / `### Маскирование секретов в коде Go` (строки 141–173)
* **claim:**  
  ```go
  type SecretString string

  func (s SecretString) String() string {
      return "****"
  }

  func (s SecretString) MarshalJSON() ([]byte, error) {
      return json.Marshal("****")
  }
  ```
  В тексте утверждается, что данный тип надежно маскирует значение «при любых выводах в консоль».
* **why it needs checking:** В современном Go 1.21+ стандартом структурированного логирования стал пакет `log/slog`.
  1. Если передать переменную типа `SecretString` в логгер: `slog.Info("config loaded", "password", cfg.Password)`, функция `slog` по умолчанию **не вызывает метод `String()`** для пользовательских строковых типов! Для защиты в `slog` требуется реализация интерфейса `slog.LogValuer`:
     ```go
     func (s SecretString) LogValue() slog.Value {
         return slog.StringValue("****")
     }
     ```
     Без этого секретный пароль будет напечатан в JSON-логи в абсолютно открытом виде!
  2. Форматирование `fmt.Printf("%#v
", cfg)` обходит метод `.String()` и также печатает реальное содержимое строки.
* **evidence/source needed:** Документация Go `log/slog.LogValuer`; Go issue #59145.
* **priority:** 🟡 **Medium**

---

### Кандидат 16: Синхронная блокировка воркера в шейпере `PacedSender`
* **article/section:** `06. Сеть/5. Traffic shaping.md` / `### Реализация Paced Sender на Go` (строки 137–145)
* **claim:**  
  ```go
  case task := <-s.tasks:
      select {
      case <-s.ticker.C:
          task()
      case <-ctx.Done():
          return
      }
  ```
* **why it needs checking:** Воркер шейпера выполняет переданную функцию `task()` синхронно прямо в теле цикла чтения тикера.  
  Если переданная задача выполняет сетевой запрос длительностью 50 мс, а шейпер настроен на 100 RPS (интервал 10 мс):
  1. Воркер зависает на выполнении первой задачи на 50 мс.
  2. В течение этих 50 мс входящие задачи не вычитываются из `s.tasks`, очередь переполняется, и `Submit` начинает аварийно сбрасывать задачи с ошибкой `bucket is full`.
  3. Реальная пропускная способность коллапсирует со 100 RPS до 20 RPS ($1 / 50	ext{ms}$).
  Шейпер обязан либо запускать задачу в отдельной горутине (`go task()`), либо использовать алгоритм Token Bucket (`rate.Limiter.Wait`), контролирующий только факт отправки, а не время ожидания ответа.
* **evidence/source needed:** Паттерны Rate Limiting и Traffic Pacing на Go; документация `golang.org/x/time/rate`.
* **priority:** 🟡 **Medium**

---

### Кандидат 17: Отсутствие вызова `span.SetStatus` при ошибке в спане OpenTelemetry
* **article/section:** `07. Kubernetes и деплой/7. Observability в Kubernetes.md` / `## 3. Распределенный трейсинг (Tracing)` (строки 334–337)
* **claim:**  
  ```go
  if err := executeDatabaseQuery(ctx); err != nil {
      span.RecordError(err)
      http.Error(w, err.Error(), http.StatusInternalServerError)
      return
  }
  ```
* **why it needs checking:** В спецификации OpenTelemetry метод `span.RecordError(err)` **не переводит статус спана в состояние ошибки**. Он лишь добавляет событие (Event) типа "exception" в метаданные спана.  
  В результате в интерфейсах систем визуализации (Jaeger, Grafana Tempo, Datadog) такой спан будет по-прежнему отображаться как **успешный (зеленый)**!  
  Для корректного отображения сбоя в трейсинге необходимо явно вызывать:  
  `span.SetStatus(codes.Error, err.Error())` (из пакета `go.opentelemetry.io/otel/codes`). Примечательно, что в соседней статье [[6. Distributed tracing]] (строка 139) эта строчка присутствует, что подчеркивает рассинхронизацию между статьями.
* **evidence/source needed:** OpenTelemetry Go SDK Specification: `Span.RecordError` vs `Span.SetStatus`; OpenTelemetry Trace API RFC.
* **priority:** 🟡 **Medium**

---

### Кандидат 18: Потеря событий `fsnotify` из-за привязки inotify к inode при ротации ConfigMap
* **article/section:** `07. Kubernetes и деплой/4. ConfigMap и Secret.md` / `#### Чтение «на горячую» в Go: Hot-Reload без блокировок` (строки 243–288)
* **claim:**  
  ```go
  // Подписываемся на родительскую директорию или сам файл
  if err := watcher.Add(filepath); err != nil { ... }
  ...
  if event.Has(fsnotify.Remove) || event.Has(fsnotify.Chmod) || event.Has(fsnotify.Write) {
      if err := loadConfig(filepath); err != nil { ... }
      _ = watcher.Add(filepath)
  }
  ```
* **why it needs checking:** В Linux подсистема `inotify` регистрирует наблюдение не за текстовой строкой пути, а за конкретным **`inode` файла**.  
  Когда `kubelet` обновляет смонтированный ConfigMap, он создает новый каталог `..2026_...` и атомарно подменяет симлинк `..data`.  
  Если Go-код подписывается на сам файл конфигурации (`/etc/config/config.json`), старый `inode` удаляется, дескриптор `inotify` в ядре аннулируется, а попытка мгновенного повторного вызова `loadConfig(filepath)` в момент события `Remove` может натолкнуться на временное отсутствие файла (`ENOENT`).  
  Надежная практика мониторинга томов Kubernetes (используемая в Viper и client-go) — подписываться на **родительскую директорию** (`filepath.Dir(filepath)`) и отслеживать события создания/подмены ссылки `..data`.
* **evidence/source needed:** Kubernetes Documentation: Mounted ConfigMaps Volume Update Mechanics; Viper Issue #284 (`fsnotify k8s configmap symlink`).
* **priority:** 🟡 **Medium**

---

### Кандидат 19: Лексикографическое сравнение строковых представлений LSN в модели Read-Your-Writes
* **article/section:** `03. Данные и согласованность/1. Consistency модели.md` / `#### Как реализовать Read Your Writes в Go` (строки 197–201)
* **claim:**  
  ```go
  type ConsistencyToken string
  ...
  replicaLSN := r.replicaDB.CurrentReplicationLSN(ctx)

  // Если реплика отстает от ревизии клиента — читаем с Мастера!
  if replicaLSN < minToken {
      return r.masterDB.QueryUser(ctx, userID)
  }
  ```
* **why it needs checking:** Тип `ConsistencyToken` объявлен как примитивная строка `string`. Оператор `<` в Go выполняет **побайтовое лексикографическое сравнение строк**:
  - В PostgreSQL LSN имеет шестнадцатеричный формат `X/Y` (например, `"16/B374D848"`), либо возвращается как целочисленный 64-битный счетчик байтов журнала WAL.
  - Лексикографическое сравнение строковых чисел дает ложные результаты: например, строка `"100"` лексикографически МЕНЬШЕ строки `"20"` (`"100" < "20"` — истинно!), а шестнадцатеричные смещения разной длины сравниваются некорректно.
  В результате запросы пользователей будут непредсказуемо уходить на отстающие реплики либо перегружать мастер-узел. Токены LSN обязаны парситься и сравниваться как беззнаковые 64-битные целые числа (`uint64`).
* **evidence/source needed:** PostgreSQL Documentation: `pg_lsn` Type and WAL positions; Martin Kleppmann: Designing Data-Intensive Applications (Chapter 5, Read-Your-Writes consistency).
* **priority:** 🟡 **Medium**

---

### Кандидат 20: Устаревший `httputil.ReverseProxy.Director` и риск появления двойных слэшей
* **article/section:** `09. Паттерны/4. API Gateway.md` / `### Настройка ReverseProxy в Go` (строки 208–224)
* **claim:**  
  ```go
  func NewCustomProxy(targetURL *url.URL) *httputil.ReverseProxy {
      proxy := &httputil.ReverseProxy{
          Director: func(req *http.Request) {
              req.URL.Scheme = targetURL.Scheme
              req.URL.Host = targetURL.Host
              req.URL.Path = targetURL.Path + req.URL.Path
              ...
              req.Header.Del("Authorization")
          },
      }
      return proxy
  }
  ```
* **why it needs checking:** 
  1. **Устаревший API:** Начиная с Go 1.20 поле `Director` в `httputil.ReverseProxy` объявлено устаревшим в пользу поля **`Rewrite`** (`func(*httputil.ProxyRequest)`). Старый `Director` не очищал hop-by-hop заголовки, не управлял `X-Forwarded-*` заголовками и создавал риски безопасности (Header Injection).
  2. **Опасная конкатенация путей:** Простое сложение строк `targetURL.Path + req.URL.Path` порождает двойной слэш `//` (например, если `targetURL.Path == "/api/"`, а `req.URL.Path == "/users"`, итоговый путь станет `"/api//users"`), что приводит к ошибкам 404 на бэкендах.
  3. **Неизменный `Host`:** В HTTP/1.1 сервер Go отправляет исходный заголовок `Host` клиента, если он явно не перезаписан в `req.Host = targetURL.Host`, что ломает маршрутизацию на виртуальных хостах бэкенда.
* **evidence/source needed:** Go 1.20 Release Notes (`httputil.ReverseProxy.Rewrite`); `httputil.ProxyRequest` documentation.
* **priority:** 🟡 **Medium**

---

### Кандидат 21: Опасное удаление чужого распределенного лока `redisClient.Del` без Lua-скрипта
* **article/section:** `02. Консенсус/7. Distributed locks.md` / `## Наивный подход: Redis и SETNX` (строки 48–51)
* **claim:**  
  ```go
  // Освобождаем лок в конце работы
  defer func() {
      // Внимание: освобождать нужно через Lua-скрипт, проверяя lockValue!
      redisClient.Del(ctx, lockKey)
  }()
  ```
* **why it needs checking:** Хотя в комментарии сделано устное предупреждение, в теле рабочего Go-кода написан прямой вызов `redisClient.Del(ctx, lockKey)`.  
  Если воркер испытал паузу GC или сетевую задержку, превысившую TTL блокировки (10 секунд):
  1. Redis удаляет ключ по таймауту;
  2. Другой воркер захватывает этот лок;
  3. Первый воркер просыпается и в блоке `defer` выполняет `redisClient.Del(ctx, lockKey)`;
  4. Первый воркер **удаляет чужой лок второго воркера**!
  Давать в учебном материале заведомо аварийный код вызова `Del` (даже с комментарием) педагогически опасно. Следует сразу демонстрировать канонический атомарный 3-строчный Lua-скрипт проверки значения.
* **evidence/source needed:** Redis Distributed Locks Specification (Redlock algorithm by antirez); Martin Kleppmann: How to do distributed locking.
* **priority:** 🟡 **Medium**

---

### Кандидат 22: Использование типа `float64` для финансовых балансов в Event Sourcing
* **article/section:** `09. Паттерны/3. Event sourcing.md` / `## 2. Реализация агрегата на Go` (строки 126, 141, 151)
* **claim:**  
  ```go
  type Account struct {
      ID      string
      Balance float64
      Version int
      ...
  }

  func (a *Account) Deposit(amount float64) error { ... }
  func (a *Account) Withdraw(amount float64) error { ... }
  ```
* **why it needs checking:** Использование чисел с плавающей точкой (`float64`) для денежных сумм и балансов банковских счетов — грубейшая ошибка в финансовом и учетном домене.  
  Из-за особенностей представления чисел в стандарте IEEE 754 операции сложения и вычитания дробей накапливают систематическую погрешность (классический пример `0.1 + 0.2 = 0.30000000000000004`). При воспроизведении сотен транзакций из журнала событий баланс неизбежно «поплывет» на доли копейки, вызывая расхождение финансовых отчетов.  
  Для денег в Go строго обязательно использовать либо целочисленные копейки/центы (`int64`), либо библиотеки работы с фиксированной точностью (например, `shopspring/decimal`).
* **evidence/source needed:** IEEE 754 Floating-Point Standard; Enterprise Software Design Guidelines for Financial Data Types.
* **priority:** 🟡 **Medium**

---

### Кандидат 23: Отмена контекста записи на не-кворумные узлы в `WriteWithQuorum`
* **article/section:** `03. Данные и согласованность/4. Quorum.md` / `## Реализация Quorum Write на Go` (строки 145–147)
* **claim:**  
  ```go
  quorumCtx, cancel := context.WithCancel(ctx)
  defer cancel()
  ...
  if acks >= W {
      return nil // defer cancel() моментально погасит медленные запросы
  }
  ```
* **why it needs checking:** При кворумном чтении (Quorum Read) досрочная отмена контекста медленных запросов оправдана: достаточно получить данные от кворума.  
  Однако при **кворумной записи (Quorum Write)** в системах типа Dynamo/Cassandra запись рассылается на все $N$ узлов (Replication Factor). Набрав кворум $W$, координатор отвечает клиенту успехом, но фоновая репликация на оставшиеся $N - W$ узлов **обязана продолжаться**, чтобы поддерживать полноту репликации в кластере.  
  Если координатор принудительно отменяет запись через `defer cancel()`, отстающие узлы прерывают транзакцию, и кластер стабильно остается в частично рассинхронизированном состоянии, перекладывая всю тяжесть на механизмы Read Repair.
* **evidence/source needed:** Werner Vogels et al.: Dynamo: Amazon's Highly Available Key-value Store; Apache Cassandra Write Path Architecture.
* **priority:** 🟢 **Low**

---

### Кандидат 24: Использование `http.Get` без таймаута и пропуск ошибки `ErrTooManyRequests` в Circuit Breaker
* **article/section:** `05. Надежность/1. Circuit breaker.md` / `### Правильный подход: Атомарные операции` (строки 171–193)
* **claim:**  
  ```go
  body, err := breaker.Execute(func() (interface{}, error) {
      resp, err := http.Get(url)
      ...
  })
  if errors.Is(err, gobreaker.ErrOpenState) { ... }
  ```
* **why it needs checking:**
  1. Вызов `http.Get(url)` использует глобальный `http.DefaultClient`, у которого отсутствует таймаут. Если целевой сервер зависнет при открытии TCP-сокета, горутина внутри предохранителя зависнет навсегда.
  2. Проверка ошибок обрабатывает только `gobreaker.ErrOpenState`. Однако в состоянии `Half-Open` библиотека `gobreaker` при превышении квоты пробных запросов (`MaxRequests`) возвращает ошибку `gobreaker.ErrTooManyRequests`, которая в данном коде не перехватывается как ошибка предохранителя.
* **evidence/source needed:** Документация библиотеки `github.com/sony/gobreaker` (переменные ошибок `ErrOpenState`, `ErrTooManyRequests`).
* **priority:** 🟢 **Low**

---

### Кандидат 25: Устаревший `atomic.Value` и сомнительное утверждение о `LOCK CMPXCHG`
* **article/section:** `04. Микросервисы/9. Configuration management.md` / `> [!info] Под капотом: Lock-free чтение с atomic.Value` (строки 111, 138–142)
* **claim:**  
  *«Использование atomic.Value позволяет реализовать паттерн Copy-on-Write: фоновая горутина обновляет указатель на новую структуру за одну атомарную процессорную инструкцию LOCK CMPXCHG, а рабочие горутины читают данные без блокировок... Get возвращает актуальный снимок конфигурации за 1 такт процессора без мьютексов»*.
* **why it needs checking:**
  1. Начиная с Go 1.19 в стандартной библиотеке появился строго типизированный дженерик-тип **`atomic.Pointer[T]`**, который избавляет от необходимости использовать `atomic.Value` и ручные приведения типов `.(*AppConfig)`.
  2. Инструкция `LOCK CMPXCHG` на архитектуре x86 является дорогой операцией блокировки шины/кэш-линии (занимает от 15 до 40 тактов процессора, а не «1 такт»). Чтение через `atomic.Value.Load()` также выполняет цикл проверок типа в runtime и распаковку `iface`, поэтому утверждение об «1 такте» является преувеличением.
* **evidence/source needed:** Go 1.19 Release Notes (`sync/atomic.Pointer`); исходный код `src/sync/atomic/value.go`.
* **priority:** 🟢 **Low**

---

### Кандидат 26: Использование сырого `r.RemoteAddr` с портом в качестве ключа Rate Limiting
* **article/section:** `06. Сеть/6. Rate limiting.md` / `### Паттерн Token Bucket на чистом Go` (строка 143)
* **claim:**  
  ```go
  ip := r.RemoteAddr // Упрощенно. В реальности нужно парсить X-Forwarded-For
  m.mu.Lock()
  c, exists := m.clients[ip]
  ```
* **why it needs checking:** В стандартной библиотеке Go поле `r.RemoteAddr` всегда содержит адрес в формате `"IP:Port"` (например, `"192.168.1.50:54321"`).  
  Поскольку браузеры и HTTP-клиенты для каждого нового TCP-соединения открывают новый случайный эфемерный порт (`54321`, `54322`, `54323`), использование сырого `r.RemoteAddr`:
  - Создает в хэш-таблице `m.clients` отдельный лимитер на каждое новое соединение одного и того же клиента;
  - Полностью нивелирует защитный эффект лимитера;
  - Приводит к неконтролируемому разрастанию памяти мапы.
  Перед использованием адрес обязан очищаться через `net.SplitHostPort(r.RemoteAddr)`.
* **evidence/source needed:** Документация Go: `net/http.Request.RemoteAddr`; `net.SplitHostPort`.
* **priority:** 🟢 **Low**

---

### Кандидат 27: Ошибочное утверждение о сложности поиска $O(\log n)$ в односвязном дереве `context.Context`
* **article/section:** `08. Практика/6. Distributed tracing.md` / `### Механическое сочувствие (Mechanical Sympathy)` (строка 108)
* **claim:**  
  *«Иммутабельный context.Context представляет собой связанное дерево... Извлечение метаданных требует обхода связного списка за O(log n) или O(1) шагов...»*
* **why it needs checking:** Цепочка контекстов `context.valueCtx` в стандартной библиотеке Go устроена как классический **односвязный список** (каждый узел хранит указатель только на своего родителя). Поиск ключа через метод `Value(key)` выполняется простым линейным проходом вверх по цепочке от дочернего контекста к корню.  
  Временная сложность такого поиска строго линейна — **$O(N)$**, где $N$ — глубина вложенности вызовов `WithValue`. Никакого логарифмического дерева $O(\log n)$ там нет (что, кстати, совершенно верно описано в соседней статье [[7. Correlation ID]], строка 226).
* **evidence/source needed:** Исходный код `src/context/context.go` (`valueCtx.Value`).
* **priority:** 🟢 **Low**

---

### Кандидат 28: Проверка Readiness Probe через прямой пинг зависимостей без защиты от каскадного сбоя
* **article/section:** `08. Практика/4. CI_CD для микросервисов.md` / `### Healthchecks (Liveness и Readiness)` (строки 246–251)
* **claim:**  
  ```go
  // Readiness: глубокая проверка готовности обслуживать клиентов
  mux.HandleFunc("GET /readyz", func(w http.ResponseWriter, r *http.Request) {
      ...
      // Проверяем жива ли база данных!
      if err := c.db.PingContext(ctx); err != nil {
          http.Error(w, "Database unavailable", http.StatusServiceUnavailable)
          return
      }
      ...
  ```
  В тексте утверждается: *«Проверка readiness обязана валидировать работоспособность критических зависимостей (база данных, кэш, брокеры сообщений)»*.
* **why it needs checking:** В архитектуре надежности распределенных систем привязка Readiness Probe всех реплик к централизованной базе данных считается опасным антипаттерном каскадного отказа (Cascading Failure):
  - При кратковременном спайке нагрузки на PostgreSQL или временном сетевом лаге `PingContext` начинает отваливаться по таймауту;
  - Kubernetes объявляет **все 100 подов сервиса неready одновременно**;
  - Трафик к сервису полностью отключается;
  - Одновременно сотни подов продолжают долбить несчастную базу проверочными пингами каждые несколько секунд, препятствуя ее восстановлению.
  Рекомендацию необходимо сопровождать важной оговоркой: готовность пода должна отражать способность самого инстанса принимать трафик, а проверка внешних зависимостей должна быть защищена Circuit Breaker или агрегироваться умными балансировщиками.
* **evidence/source needed:** Google SRE Book: Addressing Cascading Failures; Kubernetes Best Practices: Pod Probes and Health Checks.
* **priority:** 🟢 **Low**

---

## 🔍 Системные белые пятна и архитектурные упущения (Blind Spots)

В ходе широкого анализа содержания Модуля 14 выявлены 5 важнейших системных тем, которые критически необходимы Senior-разработчику для проектирования современных распределенных систем на Go, но остались за рамками модуля:

1. **Отсутствие конкретной реализации Transactional Outbox Pattern:**  
   Паттерн Outbox неоднократно упоминается в статьях о Сагах и распределенных транзакциях как спасительный инструмент для обеспечения надежной отправки сообщений в брокер (Dual-Write Problem). Однако во всем модуле отсутствует конкретный Go-листинг его реализации:
   - Сохранение бизнес-сущности и события в таблицу `outbox` в рамках единой транзакции `*sql.Tx`;
   - Надежное вычитывание пачек событий фоновым поллером с использованием `SELECT ... FOR UPDATE SKIP LOCKED` (чтобы избежать блокировок между репликами воркеров);
   - Альтернатива на базе Change Data Capture (CDC / Debezium) поверх журнала WAL Postgres.

2. **Паттерн дедупликации Singleflight (`golang.org/x/sync/singleflight`):**  
   В статьях о надежности и кэшировании подробно обсуждается катастрофа «стада бизонов» (Thundering Herd) и прогрев кэшей. Однако в модуле не рассмотрен главный инструмент экосистемы Go для борьбы с этой проблемой — пакет `singleflight.Group`. Он позволяет схлопывать тысячи параллельных запросов за одним и тем же ключом в единственный сетевой поход к базе данных, спасая бэкенд от мгновенного краха.

3. **Фаза Pre-Vote в Raft (борьба с дестабилизацией от изолированных узлов):**  
   В статье [[2. Raft. Основы]] подробно разобран сценарий однонаправленного разрыва сети (когда изолированный узел накручивает Терм и сбивает Лидера). Однако авторы не раскрыли каноническое инженерное решение этой проблемы — **Pre-Vote Protocol** (внедренный в диссертации Диего Онгаро в 2014 году и являющийся неотъемлемой частью `etcd/raft`). Прежде чем увеличивать реальный Терм, кандидат обязан опросить кворум: считают ли они текущего лидера мертвым.

4. **Специфика балансировки gRPC-трафика в Kubernetes (L4 vs L7):**  
   Микросервисы на Go повсеместно используют gRPC для межсервисного взаимодействия. Однако в статьях о Kubernetes упущен фундаментальный подводный камень: стандартный `kube-proxy` и `ClusterIP Service` работают на транспортном уровне **L4 (TCP)**. Поскольку HTTP/2 удерживает одно постоянное TCP-соединение, **100% RPC-запросов уходят в один-единственный под**, вызывая катастрофический перекос нагрузки. Необходимо раскрыть решения: headless services с client-side балансировкой (`round_robin`) либо L7-проксирование через Envoy / Service Mesh.

5. **Очистка и компактизация логов консенсуса (Log Compaction & Snapshotting):**  
   В статьях о Raft подробно описана репликация логов, но обойдена вниманием проблема бесконечного роста журнала WAL. Без механизма периодического создания слепков состояния (Snapshotting) и безопасного отсечения старых записей (`compact`) диск сервера неизбежно переполнится, а восстановление узла из лога займет часы.

---

## 📋 Итог и рекомендации для следующего этапа проверки

Модуль 14 («Распределенные системы на Go») представляет собой масштабный, концептуально насыщенный и фундаментальный труд. Авторы проделали впечатляющую работу по систематизации огромного пласта знаний: от физики кремниевых кварцевых резонаторов и математики Лэмпорта до практических манифестов Kubernetes и паттернов надежности.

Тем не менее, статус «первого прохода» выявил ряд критических ошибок реализации, состояний гонки и устаревших практик, которые требуют обязательного исправления:

1. **Первоочередные точки вмешательства:**
   - **Устранение синтаксической ошибки компиляции:** Исправить `mux *http.NewServeMux` на `mux *http.ServeMux` в `08. Практика/4. CI_CD для микросервисов.md`.
   - **Устранение состояния гонки в идемпотентности:** Заменить уязвимый паттерн Check-Then-Act в `09. Паттерны/7. Anti patterns микросервисов.md` на атомарный `SETNX` до вызова `Withdraw`.
   - **Ликвидация мертвого дедлока в CRDT:** Переписать `GCounter.Merge` в `03. Данные и согласованность/7. CRDT.md`, исключив одновременный встречный захват мьютексов двух объектов.
   - **Устранение нарушения `copylocks`:** Передавать `Cart` и `VectorClock` по указателю в `03. Данные и согласованность/6. Conflict resolution.md`.
   - **Защита автомата саги от паник и дубликатов:** Добавить проверку `reply.Step == saga.CurrentStep` в `09. Паттерны/1. Saga pattern.md`.
   - **Устранение утечки сокетов в Gateway:** Гарантировать вызов `resp.Body.Close()` при любых статус-кодах в `09. Паттерны/4. API Gateway.md`.
   - **Исправление формулы кворума синхронной репликации:** Скорректировать расчет $N = 	ext{len}(	ext{replicas}) + 1$ в `03. Данные и согласованность/2. Strong vs eventual consistency.md`.
   - **Защита от потери логов при Shutdown:** Добавить процедуру сброса буфера (drain) и исправить контракт методов `WithAttrs/WithGroup` в `08. Практика/5. Логирование в распределенных системах.md`.

2. **Модернизация версионно-чувствительного кода:**
   - Заменить использование устаревшего `Subject.CommonName` на SAN в `06. Сеть/3. mTLS.md`.
   - Добавить рекомендацию `context.WithoutCancel` для асинхронных задач в `08. Практика/7. Correlation ID.md`.
   - Заменить deprecated `httputil.ReverseProxy.Director` на `Rewrite` в `09. Паттерны/4. API Gateway.md`.
   - Добавить реализацию `slog.LogValuer` для безопасного логирования паролей в `04. Микросервисы/10. Secrets management.md`.
   - Добавить обязательный вызов `span.SetStatus` в `07. Kubernetes и деплой/7. Observability в Kubernetes.md`.

3. **Следующие шаги:**
   - Передать сформированный исследовательский бриф инженеру-фактчекеру для точечной сверки и внесения исправлений в файлы `sources/14. Распределенные системы на Go/`.
   - Дополнить модуль практическими примерами паттерна Transactional Outbox и дедупликации `singleflight`.
