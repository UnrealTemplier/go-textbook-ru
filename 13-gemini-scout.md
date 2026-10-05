# 🧭 Исследовательский скаут-отчет: Модуль 13. Очереди, брокеры сообщений и оркестраторы

> *«Асинхронные распределенные системы — это не просто вызов функций через сетевой сокет с задержкой. Это мир, где закон Мерфи возведен в абсолют: сеть разорвется в момент записи, компенсация обгонит транзакцию, воркер упадет между проверкой и списанием, а брокер честно вернет дубликат ровно тогда, когда вы меньше всего этого ждете».*  
> — Исследовательский аудит распределенных архитектур и очередей сообщений

---

## 📌 Паспорт модуля и объем проверки

* **Название модуля:** Модуль 13: Очереди, брокеры сообщений и оркестраторы
* **Расположение исходных материалов:** `sources/13. Очереди, брокеры сообщений и оркестраторы/`
* **Структура модуля:** 7 тематических подразделов:
  1. `01. Фундамент асинхронности` (10 статей)
  2. `02. RabbitMQ` (10 статей)
  3. `03. Kafka` (12 статей)
  4. `04. NATS` (7 статей)
  5. `05. Паттерны и архитектура` (10 статей)
  6. `06. Оркестрация процессов` (7 статей)
  7. `07. Практика` (10 статей)
* **Количество статей:** 66
* **Общий объем текста:** ~20 987 строк Markdown
* **Количество листингов Go:** 169 блоков кода
* **Роль и цель:** Первый независимый сквозной проход (First-Pass Fact-Check Research Scout). Широкий поиск потенциально некорректных, устаревших, вводящих в заблуждение, неполных, версионно-чувствительных, машинно- и рантайм-зависимых утверждений, скрытых состояний гонки (Race Conditions), взаимных блокировок (Deadlocks), утечек ресурсов, расхождений с протоколами и спецификациями (AMQP 0-9-1, Kafka Wire Protocol, NATS, Temporal SDK), а также системных белых пятен (Blind Spots).

---

## 📊 Сводка найденных кандидатов

| Приоритет | Кол-во | Описание характера находок |
|:---:|:---:|---|
| 🔴 **High** | **11** | Некомпилируемый Go-код и синтаксическая ошибка `mu.muUnlock := func() { mu.Unlock() }`; чужой код (Java Kafka Producer/Consumer и Python RabbitMQ) внутри блоков ````go`; состояние гонки (TOCTOU) и ложная идемпотентность в конкурентном юнит-тесте; грубое нарушение потокобезопасности `amqp091-go.Channel` в RPC-клиенте и публикаторе; массовый сброс сообщений в DLQ с `Nack(false)` при штатном Graceful Shutdown из-за отмены родительского контекста; опасный архитектурный миф о применимости Kafka как прямого Event Store для агрегатов без вторичных индексов и условного коммита; потеря денег при нарушении порядка сообщений (Pivot Trap / Out-of-Order Compensation) в хореографической Саге; дедлок в `publishBatchFast` при сбое сетевой записи в RabbitMQ; блокирующий `time.Sleep` в бесконечном цикле DLQ в Kafka, намертво блокирующий остановку сервиса; паника рантайма в Temporal Workflow из-за вызова Activity без обязательных таймаутов; потеря сообщений и утечка горутин в `RunKeyedPool` из-за отсутствия координации оффсетов и синхронизации завершения. |
| 🟡 **Medium** | **10** | Прямое самопротиворечие учебника по поводу неограниченного Fan-Out (`go process()` объявлен ядом в одной статье и рекомендован как эталон в двух соседних); удержание открытой транзакции PostgreSQL во время внешних сетевых вызовов к брокеру в Polling Outbox; обучение исключительно устаревшему (Legacy) API NATS JetStream вместо пакета `jetstream` (Go SDK v1.31+); ложное подтверждение (`Ack`) и потеря задач в Redis-дедупликаторе при падении первого воркера; замалчивание параметра `min.insync.replicas` в гарантиях `acks=all`; попытка сброса батча по уже отмененному контексту при остановке `BatchProcessor`; потеря OTel-декоратора `slog.Handler` при вызове `logger.With` из-за неполного интерфейса; риск вечного цикла ретраев из-за жесткого `val.(int32)`; 100% утилизация CPU (CPU thrashing) при мгновенном `Nack(requeue=true)` в RabbitMQ; 20 битых викиссылок на переименованные файлы. |
| 🟢 **Low** | **4** | Глобальная регистрация метрик через `promauto` без возможности изоляции тестов; чувствительность к регистру заголовков в OpenTelemetry carrier для Kafka; использование `select {}` вместо graceful shutdown в примере воркера Camunda Zeebe; переполнение целочисленного сдвига `uint64(1)<<attempt` при больших значениях `MaxRetries`. |

---

## 🧭 Каталог кандидатов на углубленный фактчекинг

---

### Кандидат 1: Некомпилируемый Go-код и синтаксическая ошибка `mu.muUnlock := func() { mu.Unlock() }`
* **article/section:** `07. Практика/7. Тестирование async систем.md` / `## Тестирование конкурентной обработки` (строки 690–705)
* **claim:**  
  В примере юнит-теста `TestConcurrentProcessing_OrderAndRaces`:
  ```go
  var mu sync.Mutex
  orderPerKey := make(map[string][]int)
  ...
  mu.Lock()
  orderPerKey[j.key] = append(orderPerKey[j.key], j.seq)
  mu.muUnlock := func() { mu.Unlock() }
  mu.muUnlock()
  ```
* **why it needs checking:** Листинг содержит грубую синтаксическую ошибку языка Go, из-за которой код вообще не компилируется компилятором `gc`:
  1. В Go оператор краткого объявления переменной `:=` требует слева идентификаторы новых переменных. Конструкция вида `x.y := expr` (селектор поля на левой стороне `:=`) запрещена грамматикой спецификации языка Go (`non-name mu.muUnlock on left side of :=`).
  2. Тип `sync.Mutex` из стандартной библиотеки не имеет поля или метода `muUnlock` (`type "sync".Mutex has no field or method muUnlock`).
  3. Это очевидный артефакт незавершенного редактирования или генерации кода, разрушающий доверие читателя к академическому качеству книги.
* **evidence/source needed:** Спецификация языка Go (The Go Programming Language Specification — Short variable declarations); запуск `go vet` или `go build` на фрагменте.
* **priority:** 🔴 **High**

---

### Кандидат 2: Чужой код (Java Kafka Client и Python RabbitMQ) внутри блоков ````go`
* **article/section:** 
  - `04. NATS/3. Subject based routing.md` (строки 237–241, 252–255)
  - `04. NATS/6. NATS vs Kafka vs RabbitMQ.md` (строки 144–155, 335–342)
* **claim:**  
  В статье `04. NATS/3`:
  ```go
  // Kafka style (flat)
  producer.send(new ProducerRecord<>("orders_new", data));
  producer.send(new ProducerRecord<>("orders_completed", data));
  ```
  ```go
  // RabbitMQ (упрощенно)
  channel.publish(exchange="amq.topic", routingKey="orders.new", body=data);
  ```
  В статье `04. NATS/6`:
  ```go
  // Kafka: Партиционированный стриминг
  producer.send(new ProducerRecord<>("orders", "partition-key", orderData))

  consumer.subscribe(Collections.singletonList("orders"))
  for {
      records := consumer.poll(Duration.ofMillis(100))
      for record := range records {
          processOrder(record.value())
      }
  }
  ```
* **why it needs checking:** 
  1. Блоки кода помечены тегом языка ````go`, однако содержат синтаксис **Java** (`new ProducerRecord<>`, `Collections.singletonList`, `Duration.ofMillis`) и **Python** (именованные параметры вызова `exchange=...`, `routingKey=...`).
  2. Во втором фрагменте конструкции Java скомбинированы с циклом Go `for record := range records`, порождая синтаксический гибрид, не валидный ни в одном существующем языке программирования.
  3. В учебнике по бэкенду на Go сравнение обязано приводиться на Go-клиентах (`twmb/franz-go`, `IBM/sarama`, `rabbitmq/amqp091-go`), либо чужие языки должны явно помечаться своими идентификаторами (`java`, `python`).
* **evidence/source needed:** Парсер Markdown и компилятор Go; проверка файлов `04. NATS/3. Subject based routing.md` и `04. NATS/6. NATS vs Kafka vs RabbitMQ.md`.
* **priority:** 🔴 **High**

---

### Кандидат 3: Ложная идемпотентность и Time-of-Check to Time-of-Use (TOCTOU) в конкурентном тесте
* **article/section:** `07. Практика/7. Тестирование async систем.md` / `## Unit-тестирование обработчиков сообщений` (строки 100–140) и `## Тестирование идемпотентности обработчика` (строки 270–310)
* **claim:**  
  Обработчик:
  ```go
  // 1. Проверка идемпотентности
  alreadyProcessed, err := h.repo.HasEvent(ctx, msg.EventID)
  if alreadyProcessed { return nil }

  // 2. Списание и фиксация события
  if err := h.repo.UpdateBalance(ctx, msg.UserID, -msg.Amount); err != nil { return err }
  if err := h.repo.RecordEvent(ctx, msg.EventID); err != nil { return err }
  ```
  И тест к нему:
  ```go
  func TestPaymentHandler_Idempotency_Concurrent(t *testing.T) {
      mockRepo := newMockOrderRepo()
      mockRepo.balances["usr-vip"] = 1000.0
      h := NewPaymentHandler(mockRepo)
      msg := PaymentMessage{EventID: "tx-duplicate-999", UserID: "usr-vip", Amount: 100.0}

      const goroutines = 10
      var wg sync.WaitGroup
      wg.Add(goroutines)
      for i := 0; i < goroutines; i++ {
          go func() {
              defer wg.Done()
              _ = h.HandlePayment(context.Background(), msg)
          }()
      }
      wg.Wait()

      // Инвариант: списание 100.0 должно произойти строго 1 раз! Баланс обязан стать 900.0, а не 0.0
      assert.Equal(t, 900.0, mockRepo.balances["usr-vip"])
  }
  ```
* **why it needs checking:** Листинг содержит фундаментальную ошибку конкурентности (Check-Then-Act / TOCTOU), разрушающую саму идею урока:
  1. Операции `HasEvent`, `UpdateBalance` и `RecordEvent` не объединены в транзакцию базы данных или распределенный мьютекс.
  2. Когда 10 параллельных горутин вызывают `HandlePayment`, все 10 горутин одновременно вызывают `HasEvent` ДО того, как хотя бы одна из них вызовет `RecordEvent`.
  3. Все 10 горутин получают `alreadyProcessed == false`, и каждая списывает по 100.0! Баланс становится `0.0` вместо `900.0`!
  4. При проверке этого теста в изолированном скрипте тест детерминированно падает с ошибкой: `Final balance: 0 (expected 900.00)`. Обучать инженеров паттерну конкурентной идемпотентности на коде, который сам по себе является уязвимым к гонке состояний, недопустимо.
* **evidence/source needed:** Выполнение тестовой программы в Go; проверка концепции Check-Then-Act в Go Memory Model.
* **priority:** 🔴 **High**

---

### Кандидат 4: Нарушение потокобезопасности `amqp091-go.Channel` в RPC-клиенте и Publisher
* **article/section:** 
  - `02. RabbitMQ/6. Routing patterns.md` / `### Идиоматичный Go-код промышленного RPC-клиента` (строки 270–340)
  - `07. Практика/1. Работа с очередями в Go.md` / `## Работа с RabbitMQ в Go` (строки 130–185)
* **claim:**  
  В статье `02. RabbitMQ/6`:
  ```go
  // RPCClient реализует потокобезопасный мультиплексированный клиент RPC
  type RPCClient struct {
      ch       *amqp.Channel
      replyQ   string
      requests sync.Map // map[string]chan []byte
  }
  func (c *RPCClient) Call(ctx context.Context, targetQueue string, payload []byte) ([]byte, error) {
      ...
      err := c.ch.PublishWithContext(ctx, "", targetQueue, false, false, ...)
  }
  ```
  В статье `07. Практика/1`:
  ```go
  type RabbitPublisher struct {
      conn    *amqp.Connection
      channel *amqp.Channel
  }
  func (p *RabbitPublisher) Publish(ctx context.Context, exchange, routingKey string, body []byte) error {
      err := p.channel.PublishWithContext(ctx, exchange, routingKey, false, false, ...)
  }
  ```
* **why it needs checking:** 
  1. В коде утверждается, что клиент является «потокобезопасным мультиплексированным клиентом RPC».
  2. Однако согласно официальной спецификации AMQP 0-9-1 и официальной документации библиотеки `github.com/rabbitmq/amqp091-go`: **`*amqp.Channel` НЕ является потокобезопасным!** («Channel instances are not thread-safe. You cannot use a single Channel from multiple goroutines concurrently to publish or consume»).
  3. Конкурентные вызовы `PublishWithContext` на одном и том же `amqp.Channel` приводят к перемешиванию бинарных AMQP-фреймов в общем сетевом буфере сокета, возникновению фатальных исключений протокола (`channel exception 504: channel-error`) и принудительному закрытию соединения со стороны сервера RabbitMQ.
  4. Для обеспечения реальной потокобезопасности требуется либо защищать вызовы `PublishWithContext` с помощью `sync.Mutex`, либо использовать пул каналов (Channel Pool), либо выделять отдельный канал на каждую горутину-воркер.
* **evidence/source needed:** Официальная документация `rabbitmq/amqp091-go` (Package documentation — Concurrency: Channels are not safe for concurrent use); RabbitMQ Go Client Guide.
* **priority:** 🔴 **High**

---

### Кандидат 5: Массовый сброс сообщений в DLQ с `Nack(false)` при отмене контекста во время Graceful Shutdown
* **article/section:** 
  - `07. Практика/3. Параллелизм обработки сообщений.md` (строки 145–165)
  - `02. RabbitMQ/4. Acknowledgements и delivery guarantees.md` (строки 210–235)
* **claim:**  
  В воркере:
  ```go
  func (c *Consumer) worker(ctx context.Context, id int, jobs <-chan Message) {
      for msg := range jobs {
          msgCtx, cancel := context.WithTimeout(ctx, 5*time.Second)

          if err := c.handler(msgCtx, msg); err != nil {
              c.logger.Error("Ошибка обработки воркером", "worker_id", id, "err", err)
              _ = msg.Nack(false) // Ошибка: отправляем в DLQ или логируем
          } else {
              _ = msg.Ack()
          }
          cancel()
      }
  }
  ```
* **why it needs checking:** В коде заложена катастрофическая ловушка жизненного цикла контекстов:
  1. Параметр `ctx` — это корневой контекст приложения, связанный с сигналами `SIGTERM` / `SIGINT`.
  2. При получении сигнала остановки `ctx` переходит в отмененное состояние (`ctx.Err() == context.Canceled`).
  3. Воркеры продолжают вычитывать сообщения, оставшиеся в буфере канала `jobs` (до `workerCount` сообщений), и вызывают `context.WithTimeout(ctx, 5*time.Second)`.
  4. Поскольку родительский `ctx` **уже отменен**, дочерний `msgCtx` оказывается **мгновенно отмененным в момент создания**!
  5. Любой запрос к БД или HTTP внутри `c.handler(msgCtx, msg)` немедленно завершается с ошибкой `context.Canceled`.
  6. Воркер попадает в ветку `err != nil` и отправляет брокеру `msg.Nack(false)` (`requeue=false`).
  7. **Результат:** При каждом плановом перезапуске пода в Kubernetes все in-flight сообщения, находившиеся в буфере воркеров, принудительно сбрасываются в DLQ или удаляются как поврежденные, хотя данные были абсолютно валидны! Для изоляции контекста задачи от сигнала завершения в Go 1.21+ применяется `context.WithoutCancel(ctx)`.
* **evidence/source needed:** Документация Go `context.WithTimeout` и `context.WithoutCancel`; поведение RabbitMQ при `basic.nack(requeue=false)`.
* **priority:** 🔴 **High**

---

### Кандидат 6: Архитектурный миф о применимости Kafka как прямого Event Store для агрегатов
* **article/section:** `05. Паттерны и архитектура/4. Event sourcing и брокеры.md` / `## Брокер как База Данных (Идеальный Match)` (строки 50–90, 220–250)
* **claim:**  
  > «Если задать параметры топика: `retention.bytes = -1`, `retention.ms = -1`, то топик Kafka де-факто превращается в высоконадежную, персистентную СУБД. При этом использование ID агрегата (например, `account_id`) в качестве ключа партиционирования (Partition Key) гарантирует, что все события конкретного банковского счета попадут в одну и ту же партицию, обеспечивая абсолютный порядок чтения и записи».  
  Диаграмма показывает прямой цикл:
  `Клиент -> Сервис: POST /accounts/42/withdraw`  
  `Сервис -> Kafka: Чтение истории событий (account_id = 42)`  
  `Сервис: Регидратация NewAccountFromHistory()`  
  `Сервис -> Kafka: Append: MoneyWithdrawn (ОДНА АТОМАРНАЯ ЗАПИСЬ!)`
* **why it needs checking:** Это широко известное в индустрии опасное заблуждение (антипаттерн «Kafka is NOT an Event Store», подробно разобранный автором концепции Event Sourcing Грегом Янгом и инженерами Confluent):
  1. **Отсутствие вторичных индексов по ключу:** В партицию Kafka пишутся события тысяч разных аккаунтов. Чтобы восстановить состояние `account_id = 42`, сервис не может сделать `SELECT WHERE account_id = 42`. Ему придется вычитать **всю партицию от оффсета 0 до конца** (миллионы чужих событий), отфильтровав их на клиенте.
  2. **Отсутствие условного коммита (Optimistic Concurrency Control / Expected Version):** В Event Store критически важно гарантировать, что новое событие записывается только поверх строго ожидаемой версии агрегата (`expectedVersion = 2`). Kafka **не поддерживает условную запись в партицию по ключу**. Если два параллельных запроса прочитают версию 2 и отправят события в Kafka, оба события успешно запишутся, и инвариант агрегата (баланс счета) будет необратимо поврежден.
  3. В реальных архитектурах Event Store строится на реляционных СУБД (PostgreSQL с таблицей `events` и ограничением `UNIQUE(aggregate_id, version)`) или EventStoreDB, а Kafka используется как шина публикации через Outbox/CDC.
* **evidence/source needed:** Доклады и статьи Greg Young («Why Event Sourcing is not just Kafka»); статьи Confluent («Event Sourcing with Kafka»); архитектурные требования к Event Store.
* **priority:** 🔴 **High**

---

### Кандидат 7: Потеря денег при нарушении порядка сообщений (Pivot Trap / Out-of-Order Compensation) в Саге
* **article/section:** `05. Паттерны и архитектура/8. Saga через брокеры.md` / `## Практика на Go: Обработка компенсаций` (строки 185–215)
* **claim:**  
  В обработчике сбоя склада:
  ```go
  res, err := tx.ExecContext(ctx, `
      UPDATE payments SET status = 'REFUNDED' 
      WHERE saga_id = $1 AND status = 'COMPLETED'
  `, event.SagaID)
  ...
  rows, err := res.RowsAffected()
  if rows == 0 {
      // Ловушка гонки: компенсация пришла раньше прямого списания, 
      // либо это повторный дубликат уже отмененной транзакции
      h.logger.WarnContext(ctx, "Платеж не найден в статусе COMPLETED или уже возвращен", "saga_id", event.SagaID)
      return nil // Отправляем Ack брокеру во избежание бесконечного цикла
  }
  ```
* **why it needs checking:** Автор сам указывает в комментарии, что «компенсация пришла раньше прямого списания», но предлагает фатально ошибочное решение:
  1. Из-за сетевых задержек или ребалансировки партиций событие `InventoryFailed` может прибыть в платежный сервис **раньше**, чем завершится прямое списание средств `ProcessPayment`.
  2. Хэндлер видит `rows == 0`, логирует предупреждение и возвращает `nil` (Ack брокеру). Сообщение о компенсации удаляется из очереди навсегда!
  3. Спустя 50 мс прибывает задержанное прямое списание. Оно успешно списывает деньги с карты клиента и ставит статус `COMPLETED`.
  4. Поскольку компенсация уже подтверждена и забыта, сервис больше никогда не попытается вернуть деньги. Клиент остался без товара и без денег!
  5. Для корректной обработки out-of-order компенсаций требуется создание упреждающей записи отмены (`INSERT INTO payments (saga_id, status) VALUES ($1, 'CANCELLED') ON CONFLICT...`), которая заблокирует выполнение прямого платежа при его последующем приходе.
* **evidence/source needed:** Шаблоны распределенных саг (Chris Richardson, «Microservices Patterns» — Handling Out-of-Order Messages in Sagas); семантика идемпотентного отката.
* **priority:** 🔴 **High**

---

### Кандидат 8: Дедлок в `publishBatchFast` при сбое сетевой записи в RabbitMQ
* **article/section:** `02. RabbitMQ/10. Производительность и tuning RabbitMQ.md` / `### Publisher: Батчинг и Асинхронные Confirms` (строки 160–225)
* **claim:**  
  ```go
  func publishBatchFast(ctx context.Context, ch *amqp.Channel, exchange, routingKey string, messages [][]byte) error {
      ...
      confirms := ch.NotifyPublish(make(chan amqp.Confirmation, len(messages)))
      var wg sync.WaitGroup
      wg.Add(1)

      go func() {
          defer wg.Done()
          received := 0
          for c := range confirms {
              received++
              if received == len(messages) {
                  return // Получили ответы на всю пачку
              }
          }
      }()

      for _, payload := range messages {
          err := ch.PublishWithContext(ctx, ...)
          if err != nil {
              log.Printf("Ошибка записи в TCP-сокет: %v", err)
          }
      }

      wg.Wait()
      ...
  }
  ```
* **why it needs checking:** Листинг содержит гарантированный Deadlock при любых частичных сетевых ошибках:
  1. Если отправка 10-го сообщения из 100 упадет с ошибкой (таймаут контекста, разрыв TCP-сокета или закрытие канала), цикл просто выведет лог и пойдет дальше.
  2. В брокер попадет только 9 сообщений. Брокер сгенерирует ровно 9 подтверждений.
  3. Фоновая горутина ожидает строго `received == len(messages)` (100). Поскольку оставшиеся подтверждения никогда не придут, условие никогда не выполнится, горутина никогда не выйдет, `wg.Done()` не вызовется, а вызывающая горутина намертво зависнет в `wg.Wait()`.
  4. Кроме того, повторный вызов `ch.NotifyPublish` на каждом вызове функции регистрирует все новые каналы слушателей в объекте `Channel`, что ведет к утечке памяти и расщеплению потока подтверждений.
* **evidence/source needed:** Документация `amqp091-go.Channel.NotifyPublish`; тестирование поведения при имитации ошибки записи.
* **priority:** 🔴 **High**

---

### Кандидат 9: Блокирующий `time.Sleep` в бесконечном цикле DLQ в Kafka, намертво вешающий завершение сервиса
* **article/section:** `07. Практика/6. Handling poison messages.md` / `## Практика для Kafka: Ручное управление DLQ` (строки 270–295)
* **claim:**  
  ```go
  if errors.Is(err, ErrFatalPoisonPill) {
      // Блокирующий цикл гарантированной доставки яда в DLQ
      for {
          dlqErr := w.producer.ProduceSync(ctx, "dlq-topic", msg.Key, msg.Value, err.Error())
          if dlqErr == nil {
              w.consumer.Commit(msg)
              return
          }
          // Если записать в DLQ не удалось, ждем и повторяем: данные терять нельзя
          time.Sleep(2 * time.Second)
      }
  }
  ```
* **why it needs checking:** 
  1. Вызов `time.Sleep(2 * time.Second)` полностью игнорирует отмену контекста `ctx.Done()`.
  2. Если во время попытки записи в DLQ приходит сигнал `SIGTERM`, контекст `ctx` отменяется. В результате `ProduceSync(ctx, ...)` будет мгновенно падать с ошибкой `context.Canceled` на каждой итерации.
  3. Метод входит в **бесконечный неуправляемый цикл**, усыпляя горутину на 2 секунды и снова получая `context.Canceled`. Сервис невозможно завершить штатно — Kubernetes будет ждать окончания `terminationGracePeriodSeconds` и принудительно убьет процесс сигналом `SIGKILL`.
  4. Вместо `time.Sleep` любой повтор обязан использовать `select { case <-ctx.Done(): return ... case <-time.After(...): }`.
* **evidence/source needed:** Руководства по идиоматичному Go (Effective Go — Concurrency and cancellation); Kubernetes Pod Termination Lifecycle.
* **priority:** 🔴 **High**

---

### Кандидат 10: Паника рантайма в Temporal Workflow из-за отсутствия `workflow.ActivityOptions`
* **article/section:** `06. Оркестрация процессов/5. Retry и compensation logic.md` / `### Идиоматичная Saga в Temporal (Go)` (строки 150–205)
* **claim:**  
  ```go
  func TourBookingWorkflow(ctx workflow.Context, req TourRequest) (err error) {
      ...
      // --- ШАГ 1: Бронирование отеля ---
      var hotelBookingID string
      err = workflow.ExecuteActivity(ctx, BookHotelActivity, req.HotelID).Get(ctx, &hotelBookingID)
  ```
* **why it needs checking:** 
  1. В сигнатуру функции передается базовый `ctx workflow.Context`. В коде функции контекст **нигде не оборачивается** через `workflow.WithActivityOptions(ctx, options)`.
  2. Согласно правилам Temporal Go SDK, запуск `workflow.ExecuteActivity` на контексте, в котором не задан хотя бы один из таймаутов (`StartToCloseTimeout` или `ScheduleToCloseTimeout`), является фатальной ошибкой: рантайм Temporal немедленно паникует с сообщением `missing activity options: both ScheduleToCloseTimeout and StartToCloseTimeout are not set`.
  3. Точно такая же ошибка допущена в блоке компенсаций: `disconnectedCtx, _ := workflow.NewDisconnectedContext(ctx)` создается без опций Activity, и любая компенсирующая операция точно так же упадет при вызове `ExecuteActivity(disconnectedCtx, ...)`.
* **evidence/source needed:** Документация Temporal Go SDK (Activity Options & Execution Timeouts); исходный код `go.temporal.io/sdk/internal/internal_workflow.go`.
* **priority:** 🔴 **High**

---

### Кандидат 11: Потеря contiguous оффсетов Kafka и утечка горутин в `RunKeyedPool`
* **article/section:** `07. Практика/3. Параллелизм обработки сообщений.md` / `### Паттерн: Key-based Worker Pool` (строки 260–310)
* **claim:**  
  ```go
  func (c *Consumer) RunKeyedPool(ctx context.Context, workerCount int) error {
      workerChannels := make([]chan KeyedMessage, workerCount)
      for i := 0; i < workerCount; i++ {
          workerChannels[i] = make(chan KeyedMessage, 100)
          go c.keyedWorker(ctx, i, workerChannels[i])
      }
      for {
          select {
          case <-ctx.Done():
              for _, ch := range workerChannels { close(ch) }
              return nil
          case msg, ok := <-c.brokerMessages:
              if !ok { return nil }
              ...
              select {
              case workerChannels[workerID] <- msg:
              case <-ctx.Done(): return nil
              }
          }
      }
  }
  ```
* **why it needs checking:** 
  1. **Утечка горутин (Goroutine Leak):** В функции отсутствует `sync.WaitGroup`. При срабатывании `case <-ctx.Done()` каналы закрываются и функция мгновенно возвращает `nil`. Фоновые горутины `keyedWorker` обрываются посреди выполнения задач. А при `if !ok { return nil }` каналы не закрываются вовсе — все воркеры остаются вечно висеть на `range jobs`.
  2. **Потеря оффсетов Kafka (Watermark Violation):** Автор рекомендует этот паттерн для распараллеливания одной партиции Kafka. Однако оффсеты в Kafka монотонны и кумулятивны! Если Воркер 1 обрабатывает сообщение с оффсетом 10 долго (10 секунд), а Воркер 2 обработал оффсет 11 мгновенно (1 мс) и закоммитил оффсет 11 в Kafka, то при аварии сервиса на 5-й секунде оффсет 10 **никогда не будет перечитан** — данные аккаунта потеряны! Для безопасного шардирования партиции Kafka консьюмер обязан поддерживать непрерывный учет минимального незакоммиченного смещения (Contiguous Watermark Tracker).
* **evidence/source needed:** Архитектура фиксации оффсетов Kafka; Go Concurrency patterns (Graceful Worker Pool Shutdown).
* **priority:** 🔴 **High**

---

### Кандидат 12: Прямое самопротиворечие учебника по поводу неограниченного Fan-Out (`go process()`)
* **article/section:** 
  - `07. Практика/3. Параллелизм обработки сообщений.md` (строки 35–55)
  - `07. Практика/2. Консьюмеры и graceful shutdown.md` (строка 130)
  - `03. Kafka/12. Производительность Kafka.md` (строки 198–210)
* **claim:**  
  - В статье 3:  
    `subgraph AntiPattern["Антипаттерн: Неограниченный Fan-Out"]`  
    «Первое искушение начинающего Go-разработчика: Будем писать go process(msg) на каждое пришедшее сообщение! В продакшене этот наивный подход гарантированно приводит к отказу сервиса... Неограниченный Fan-Out — архитектурный яд».
  - В статье 2 (Консьюмеры и graceful shutdown):  
    В качестве эталонного производственного консьюмера дается код:
    ```go
    case msg, ok := <-messagesCh:
        wg.Add(1)
        go func(m Message) {
            defer wg.Done()
            c.handleSingleMessage(msgCtx, m)
        }(msg)
    ```
  - В статье 12 (Производительность Kafka):  
    «**Критический паттерн для Go:** не обрабатывайте сообщения синхронно внутри цикла Poll. Выгружайте их в worker-пул или горутины, немедленно возвращаясь к Poll»:
    ```go
    fetches.EachRecord(func(record *kgo.Record) {
        wg.Add(1)
        go func(r *kgo.Record) {
            defer wg.Done()
            process(r)
        }(record)
    })
    ```
* **why it needs checking:** Прямое противоречие внутри одного учебного модуля. В одной статье автор справедливо громит неограниченный Fan-Out как опаснейший антипаттерн, приводящий к OOM и поломке Backpressure, а в двух соседних статьях подает его как эталонный производственный код. Студент получает диаметрально противоположные указания.
* **evidence/source needed:** Сверка текстов статей `07. Практика/3`, `07. Практика/2` и `03. Kafka/12`.
* **priority:** 🟡 **Medium**

---

### Кандидат 13: Удержание открытой транзакции СУБД во время сетевых вызовов в Polling Outbox
* **article/section:** `05. Паттерны и архитектура/6. Outbox pattern.md` / `### Подход 1: Polling Publisher` (строки 185–215)
* **claim:**  
  ```sql
  -- Эталонный запрос конкурентного Polling Relay в PostgreSQL:
  BEGIN;

  WITH cte AS (
      SELECT id FROM outbox
      WHERE status = 'pending'
      ORDER BY created_at ASC
      LIMIT 100
      FOR UPDATE SKIP LOCKED
  )
  UPDATE outbox SET status = 'processing'
  WHERE id IN (SELECT id FROM cte)
  RETURNING id, topic, payload;

  -- 1. Полученные строки отправляются в брокер Kafka/RabbitMQ в коде Go
  -- 2. При подтверждении успешной отправки от брокера:
  DELETE FROM outbox WHERE id IN (...);

  COMMIT;
  ```
* **why it needs checking:** Листинг предлагает опасный антипаттерн интеграции баз данных и сети:
  1. Транзакция PostgreSQL открывается (`BEGIN`), захватывает блокировки строк, и пока в коде Go выполняются синхронные сетевые вызовы к брокеру (которые могут занимать секунды при задержках или ретраях), транзакция удерживается открытой.
  2. Это приводит к блокировке слотов соединений в пуле СУБД (`pgxpool` / `sql.DB`), а также замораживает транзакционный горизонт (`Oldest Xmin`), препятствуя работе PostgreSQL Autovacuum и вызывая разрастание мертвых строк (Table Bloat).
  3. Вдобавок, бессмысленно делать `UPDATE ... SET status = 'processing'`, если через мгновение в той же самой транзакции вызывается `DELETE FROM outbox WHERE id IN (...)`.
  4. Промышленный Polling Relay обязан разбивать процесс на две транзакции: первая переводит статус в `processing` и немедленно делает `COMMIT`, после чего код публикует сообщения в брокер, и отдельной короткой транзакцией удаляет отправленные строки.
* **evidence/source needed:** Документация PostgreSQL (Concurrency Control and autovacuum bloat); статьи Vlad Mihalcea («Never keep database connections open during network calls»).
* **priority:** 🟡 **Medium**

---

### Кандидат 14: Обучение устаревшему (Legacy) API NATS JetStream вместо нового пакета `jetstream`
* **article/section:** Подраздел `04. NATS` (системно во всех статьях, особенно `5. JetStream. Persistence и stream processing.md`)
* **claim:**  
  Во всех статьях используется синтаксис:
  ```go
  js, err := nc.JetStream()
  js.Publish("orders.new", data)
  js.Subscribe("orders.*", handler)
  js.PullSubscribe("orders.*", "durable")
  js.AddStream(&nats.StreamConfig{...})
  ```
* **why it needs checking:** 
  1. Начиная с версии `github.com/nats-io/nats.go` v1.31.0 (2023–2024 гг.), архитекторы NATS полностью переработали работу с JetStream, выделив ее в новый пакет `jetstream` (`import "github.com/nats-io/nats.go/jetstream"`).
  2. Старый интерфейс `nats.JetStreamContext` (`nc.JetStream()`) официально объявлен **Legacy**. Все новые возможности (упрощенный Pull-консьюмер, `CreateOrUpdateStream`, потоковые итераторы сообщений `Fetch`/`Next`, расширенные фильтры) поддерживаются только в новом API:
     ```go
     js, err := jetstream.New(nc)
     stream, err := js.CreateOrUpdateStream(ctx, jetstream.StreamConfig{...})
     cons, err := stream.CreateOrUpdateConsumer(ctx, jetstream.ConsumerConfig{...})
     ```
  3. Обучение инженеров в 2026 году исключительно легаси-интерфейсу создает технологический долг.
* **evidence/source needed:** Документация NATS.go (JetStream Migration Guide: Legacy vs JetStream Package); репозиторий `nats-io/nats.go`.
* **priority:** 🟡 **Medium**

---

### Кандидат 15: Ложное подтверждение (`Ack`) и потеря задач в Redis-дедупликаторе
* **article/section:** `07. Практика/4. Idempotent handlers.md` / `### 2. Отдельное хранилище идемпотентности (Redis / Memcached)` (строки 180–210)
* **claim:**  
  ```go
  func (h *SMSHandler) HandleSendSMS(ctx context.Context, idempKey string, phone, text string) error {
      redisKey := "idemp:" + idempKey

      // 1. Атомарная попытка захвата ключа
      set, err := h.redisClient.SetNX(ctx, redisKey, "processing", 1*time.Hour).Result()
      if err != nil { return fmt.Errorf("redis setnx error: %w", err) }
      if !set {
          // Ключ уже существует: операция либо выполняется параллельно, либо уже завершена
          return nil // Пропускаем дубликат
      }
      ...
  }
  ```
* **why it needs checking:** 
  1. Если два воркера получают копии одного сообщения почти одновременно: Воркер 1 успешно захватывает ключ со статусом `processing`.
  2. Воркер 2 пытается сделать `SetNX`, получает `!set`, считает сообщение успешно выполненным и делает `return nil`! Консьюмер отправляет брокеру `Ack`!
  3. Если в этот момент Воркер 1 падает (OOM, сбой питания, паника), ключ зависает, но сообщение **уже подтверждено брокеру Воркером 2**! Задача потеряна навсегда, SMS клиенту отправлено не будет.
  4. При статусе `processing` параллельный обработчик не имеет права сразу возвращать `Ack`. Он должен либо подождать завершения первого воркера, либо вернуть транзиентную ошибку (`Nack` с `requeue=true` или повтор через backoff).
* **evidence/source needed:** Паттерн Distributed Idempotency Lock; Stripe Engineering Blog («Idempotency and concurrency»).
* **priority:** 🟡 **Medium**

---

### Кандидат 16: Замалчивание роли `min.insync.replicas` в гарантиях `acks=all`
* **article/section:** `01. Фундамент асинхронности/7. Message durability и persistence.md` / `## 4. Подход Kafka: Диск как фундамент` (строки 120–160)
* **claim:**  
  > «`acks=all` (или `acks=-1`): Лидер принимает сообщение, реплицирует его по сети на все активные реплики из списка ISR (In-Sync Replicas)... Все In-Sync Replicas (ISR) подтвердили! Leader шлет успешный Ack продюсеру! Репликация в Page Cache трех независимых машин по сети оказывается надежнее и на порядки быстрее, чем локальный вызов `fsync`...»
* **why it needs checking:** 
  1. Автор создает у читателя опасную иллюзию, будто `acks=all` сам по себе гарантирует запись на 3 машины.
  2. В архитектуре Kafka `acks=all` означает ожидание подтверждения от всех реплик, находящихся в текущем списке ISR. Если 2 реплики из 3 отстали или упали, в ISR остается **только один брокер — сам лидер**!
  3. Если на брокере не настроен параметр `min.insync.replicas = 2` (по умолчанию в ванильной Kafka он равен `1`!), продюсер с `acks=all` успешно запишет данные **в единственный узел**! При падении этого узла данные будут безвозвратно утеряны. Описание `acks=all` без упоминания `min.insync.replicas` педагогически неполно и опасно.
* **evidence/source needed:** Документация Apache Kafka (Producer Configs: `acks`, Topic/Broker Configs: `min.insync.replicas`); Confluent Kafka Reliability Guide.
* **priority:** 🟡 **Medium**

---

### Кандидат 17: Попытка сброса батча по уже отмененному контексту при остановке `BatchProcessor`
* **article/section:** `07. Практика/5. Batch processing сообщений.md` / `## 1. Архитектура BatchProcessor` (строки 120–135)
* **claim:**  
  ```go
  func (p *BatchProcessor) Run(ctx context.Context, ch <-chan Message) error {
      ...
      for {
          select {
          case <-ctx.Done():
              // При получении сигнала SIGTERM сбрасываем остатки частично заполненного батча!
              if len(batch) > 0 {
                  if err := p.process(ctx, batch); err != nil {
                      return fmt.Errorf("flush on shutdown failed: %w", err)
                  }
              }
              return nil
  ```
* **why it needs checking:** 
  1. В ветке `case <-ctx.Done():` код пытается сбросить оставшиеся сообщения, вызывая `p.process(ctx, batch)`.
  2. Однако в качестве первого аргумента передается тот самый `ctx`, который **только что был отменен**!
  3. Если функция `p.process` выполняет операции с СУБД (`db.ExecContext(ctx, ...)`), база данных немедленно прервет операцию с ошибкой `context canceled`. Сброс сорвется, и `Run` вернет ошибку, оставив сообщения несохраненными. Для сброса на фазе graceful shutdown требуется передавать отдельный контекст с дедлайном (например, `context.WithoutCancel(ctx)` с таймаутом).
* **evidence/source needed:** Документация Go 1.21 `context.WithoutCancel`; шаблоны безопасного дренажа очередей.
* **priority:** 🟡 **Medium**

---

### Кандидат 18: Потеря OTel-декоратора `slog.Handler` при вызове `logger.With` из-за неполного интерфейса
* **article/section:** `07. Практика/8. Observability очередей.md` / `### Идиоматичный Slog-адаптер для трассировки` (строки 380–415)
* **claim:**  
  ```go
  type TraceContextHandler struct {
      slog.Handler
  }
  func NewTraceJSONHandler() *TraceContextHandler {
      baseHandler := slog.NewJSONHandler(os.Stdout, &slog.HandlerOptions{Level: slog.LevelInfo})
      return &TraceContextHandler{Handler: baseHandler}
  }
  func (h *TraceContextHandler) Handle(ctx context.Context, r slog.Record) error {
      ...
      return h.Handler.Handle(ctx, r)
  }
  ```
* **why it needs checking:** Листинг содержит классическую тонкую ошибку декорирования `slog.Handler`:
  1. Структура `TraceContextHandler` встраивает `slog.Handler`, но переопределяет **только метод `Handle`**.
  2. Методы `WithAttrs` и `WithGroup` остаются не переопределенными.
  3. Если в коде консьюмера кто-то создаст дочерний логгер: `subLogger := logger.With("worker_id", id)`, вызов `WithAttrs` сработает на встроенном `baseHandler` (`*slog.JSONHandler`) и вернет чистый JSONHandler без обертки `TraceContextHandler`!
  4. Во всех логах дочернего логгера поля `trace_id` и `span_id` перестанут появляться. Для полноценного декоратора `slog.Handler` методы `WithAttrs` и `WithGroup` обязаны возвращать `&TraceContextHandler{Handler: h.Handler.WithAttrs(...)}`.
* **evidence/source needed:** Документация Go `log/slog` (Writing a handler wrapper); Go standard library issues.
* **priority:** 🟡 **Medium**

---

### Кандидат 19: Риск вечного цикла ретраев из-за хрупкого type assertion `val.(int32)`
* **article/section:** `02. RabbitMQ/8. Retry patterns в RabbitMQ.md` / `## Реализация Exponential Backoff на Go` (строки 180–210)
* **claim:**  
  ```go
  var retryCount int32 = 0
  if d.Headers != nil {
      if val, ok := d.Headers["x-retry-count"]; ok {
          if count, ok := val.(int32); ok {
              retryCount = count
          }
      }
  }
  ```
* **why it needs checking:** 
  1. В библиотеке `rabbitmq/amqp091-go` при декодировании бинарных фреймов таблицы AMQP заголовки целых чисел в зависимости от типа фрейма и версии брокера могут распаковываться как `int32`, `int64` или `int`.
  2. Если значение заголовка распаковано как `int64` (или `int`), проверка `count, ok := val.(int32)` тихо вернет `ok == false`.
  3. Переменная `retryCount` останется равной `0`.
  4. Условие `retryCount >= MaxRetries` никогда не выполнится, и упавшее сообщение будет **вечно ретраиться с первой задержкой**, перегружая брокер и базу данных. Необходимо использовать универсальный парсер чисел (типовой свитч по `int`, `int32`, `int64`).
* **evidence/source needed:** Реализация декодера AMQP-типов в `rabbitmq/amqp091-go`; поведение `amqp.Table` при десериализации.
* **priority:** 🟡 **Medium**

---

### Кандидат 20: 100% утилизация CPU (CPU thrashing) при мгновенном `Nack(requeue=true)` в RabbitMQ
* **article/section:** `07. Практика/6. Handling poison messages.md` / `## Практика для RabbitMQ: Nack и DLX` (строки 190–210)
* **claim:**  
  ```go
  if errors.Is(err, ErrFatalPoisonPill) {
      _ = d.Nack(false, false)
  } else {
      // ВРЕМЕННАЯ ОШИБКА (Transient Error):
      // requeue=true возвращает сообщение в очередь для повторной попытки.
      w.logger.Info("Временный сбой, возвращаем сообщение в очередь", "err", err)
      _ = d.Nack(false, true)
  }
  ```
* **why it needs checking:** 
  1. В RabbitMQ протокол `Basic.Nack` с `requeue=true` возвращает сообщение не в хвост, а **в голову (Head) очереди**.
  2. Тот же самый консьюмер в следующую миллисекунду немедленно снова вычитывает ровно то же самое сообщение.
  3. Если внешняя база данных упала на 1 минуту, консьюмер войдет в жесточайший цикл: вычитка -> ошибка подключения -> мгновенный `Nack(requeue=true)` -> повторная вычитка. Это порождает миллионы пустых циклов в секунду, утилизируя 100% CPU Go-воркера и брокера RabbitMQ.
  4. Возврат в очередь без паузы или без перенаправления в очередь задержки (Wait Queue / TTL / Delayed Exchange) является антипаттерном.
* **evidence/source needed:** Документация RabbitMQ (Negative Acknowledgements and Requeueing); RabbitMQ Performance Gotchas.
* **priority:** 🟡 **Medium**

---

### Кандидат 21: Системная проблема: 20 сломанных викиссылок (Broken Wikilinks)
* **article/section:** Системно в файлах `03. Kafka/1`, `03. Kafka/11`, `04. NATS/1`, `04. NATS/3`, `04. NATS/6`, `04. NATS/7`, `05. Паттерны и архитектура/1`, `05. Паттерны и архитектура/10`, `05. Паттерны и архитектура/4`
* **claim:**  
  В тексте присутствуют ссылки:
  - `[[1. Apache Kafka. Архитектура и концепции]]` (реальный файл: `1. Kafka. Архитектура и модель log based системы.md`)
  - `[[2. Exchanges, queues и bindings]]` (в репозитории темы разбиты на `2. Exchanges...` и `3. Queues и bindings.md`)
  - `[[1. RabbitMQ. Архитектура и основные концепции]]` (реальный файл: `1. RabbitMQ. Архитектура и концепции.md`)
  - `[[3. Kafka Producer и Consumer. Гарантии доставки]]` (реальный файл: `3. Producer и consumer.md`)
  - `[[05. Паттерны и архитектура/1. Pub Sub]]` (содержит путь, нарушая формат викиссылок генератора SSG)
  - `[[06. Оркестрация процессов/1. Что такое workflow orchestration]]` (содержит путь)
  - `[[14. Алгоритмы консенсуса. Raft]]` (ссылка на сторонний модуль без точного совпадения имени файла)
* **why it needs checking:** Нарушение связности графа знаний энциклопедии. Генератор статического сайта не может сопоставить битые имена файлов, что оставляет читателя с неработающими ссылками.
* **evidence/source needed:** Скрипт проверки викиссылок `builder/scanner.py`.
* **priority:** 🟡 **Medium**

---

### Кандидат 22: Глобальная регистрация метрик через `promauto` без возможности изоляции тестов
* **article/section:** `07. Практика/8. Observability очередей.md` (строки 270–305), `07. Практика/9. Мониторинг lag и throughput.md` (строки 185–220)
* **claim:**  
  Метрики регистрируются через глобальные пакетные переменные:
  ```go
  var EventsPublishedTotal = promauto.NewCounterVec(...)
  var EventsConsumedTotal = promauto.NewCounterVec(...)
  ```
* **why it needs checking:** В крупных сервисах и при параллельном тестировании (`go test -race -parallel`) создание метрик в глобальном реестре Prometheus `DefaultRegisterer` приводит к панике при повторной регистрации, невозможности сбросить состояние счетчиков между тестами и затрудняет внедрение зависимостей. Рекомендуется передавать кастомный `*prometheus.Registry` через конструктор структуры сервиса.
* **evidence/source needed:** Документация `prometheus/client_golang` (Best Practices for Unit Testing with Metrics).
* **priority:** 🟢 **Low**

---

### Кандидат 23: Чувствительность к регистру ключей заголовков в OpenTelemetry carrier
* **article/section:** `05. Паттерны и архитектура/10. Distributed tracing в async системах.md` (строки 190–215)
* **claim:**  
  ```go
  func (c kafkaExtractCarrier) Get(key string) string {
      for _, h := range c.headers {
          if string(h.Key) == key {
              return string(h.Value)
          }
      }
      return ""
  }
  ```
* **why it needs checking:** Сравнение `string(h.Key) == key` чувствительно к регистру символов. Если продюсер на Java, .NET или Python передаст заголовок в формате `Traceparent` или `TRACEPARENT`, точная проверка провалится, и трассировка разорвется. Идиоматично использовать регистронезависимое сравнение `strings.EqualFold(string(h.Key), key)`.
* **evidence/source needed:** Спецификация W3C TraceContext; OpenTelemetry Go TextMapCarrier conventions.
* **priority:** 🟢 **Low**

---

### Кандидат 24: Использование `select {}` вместо graceful shutdown в воркере Camunda Zeebe
* **article/section:** `06. Оркестрация процессов/7. Альтернативы. Zeebe, Airflow.md` (строка 95)
* **claim:**  
  ```go
  log.Println("Zeebe Job Worker успешно запущен, ожидание задач...")
  select {} // Блокировка основного потока
  ```
* **why it needs checking:** Использование пустого `select {}` блокирует горутину навечно без перехвата сигналов ОС (`SIGTERM`/`SIGINT`). Операторы `defer client.Close()` и `defer jobWorker.Close()` никогда не выполнятся при остановке контейнера.
* **evidence/source needed:** Go standard library (Signal handling in main); Zeebe Go Client best practices.
* **priority:** 🟢 **Low**

---

### Кандидат 25: Переполнение целочисленного сдвига `uint64(1)<<attempt` при больших `MaxRetries`
* **article/section:** `01. Фундамент асинхронности/9. Retry стратегии и exponential backoff.md` (строки 150–160)
* **claim:**  
  ```go
  expo := float64(cfg.BaseDelay) * float64(uint64(1)<<attempt)
  if expo > float64(cfg.MaxDelay) { expo = float64(cfg.MaxDelay) }
  ```
* **why it needs checking:** В Go сдвиг беззнакового целого `1 << attempt` при `attempt >= 64` приводит к переполнению и обращению результата в `0`! Если пользователь сконфигурирует `MaxRetries = 100`, начиная с 64-й попытки задержка внезапно сбросится в 0 миллисекунд вместо `MaxDelay`. Необходимо ограничивать `attempt` перед операцией сдвига.
* **evidence/source needed:** Спецификация Go (Integer overflow and bitwise shift operators).
* **priority:** 🟢 **Low**

---

## 🔍 Системные белые пятна и архитектурные упущения (Blind Spots)

В ходе анализа выявлены 4 важные системные темы, которые критически важны для проектирования современных очередей и распределенных брокеров на Go, но выпали из содержания Модуля 13:

1. **Ребалансировка Consumer Group в Kafka: Stop-the-World vs Incremental Cooperative Rebalancing:**  
   В подразделе по Kafka упоминается Cooperative Sticky Rebalance, но совершенно отсутствует практический Go-код обработки хуков ребалансировки (`OnPartitionsRevoked`, `OnPartitionsAssigned`, `OnPartitionsLost`). В распределенных системах именно во время ребалансировки происходит львиная доля аварий: сервис обязан успеть сбросить локальные буферы и закоммитить оффсеты ДО того, как брокер передаст партицию другому поду.
2. **Проблема разрастания мертвых строк (PostgreSQL Table Bloat) в паттернах Outbox и Inbox:**  
   В статьях подробно описаны паттерны Transactional Outbox и Inbox, однако не раскрыта главная эксплуатационная беда этих паттернов в реляционных базах — MVCC Bloat. Высокочастотные `INSERT`, `UPDATE` и `DELETE` тысяч записей в секунду приводят к раздуванию таблиц и индексов до сотен гигабайт, перегрузке диска и отказу базы. Необходимо показать, как настраивать агрессивный `autovacuum` на уровне конкретных таблиц (`autovacuum_vacuum_scale_factor = 0.01`) или применять ежедневное партиционирование таблиц с мгновенным `DROP TABLE`.
3. **Kafka Tombstones и специфика Log Compaction:**  
   В статье по Retention и Compaction лишь вскользь упомянуты tombstone-сообщения. В продакшене начинающие разработчики часто сталкиваются с тем, что отправка пустого тела сообщения (`value = nil`) удаляет ключ из компактифицированного топика, но этот маркер продолжает жить в логе ровно `delete.retention.ms`. Без понимания этой механики консьюмеры, читающие компактифицированный топик с нуля, неожиданно получают панику на `nil`-указателях в поле полезной нагрузки.
4. **Безопасный параллелизм вычитки Kafka: Алгоритм скользящего окна (Contiguous Offset Watermark Tracker):**  
   Параллельная обработка сообщений из одной партиции с помощью Worker Pool — самый частый вопрос на собеседованиях уровня Lead/Principal. В модуле показан шардированный пул по ключам, но не объяснено, как коммитить оффсеты: если сообщение 10 еще обрабатывается, а сообщение 15 уже завершено, коммитить 15 нельзя. Требуется раскрыть алгоритм учета минимального непрерывного подтвержденного смещения (sliding window ack tracker).

---

## 📋 Итог и рекомендации для следующего этапа проверки

Модуль 13 («Очереди, брокеры сообщений и оркестраторы») — один из самых масштабных, фундаментальных и глубоких блоков всей энциклопедии (66 статей, ~21 000 строк). Авторы глубоко понимают многие тонкости современных систем (KRaft mode в Kafka, Raft WAL в Quorum Queues RabbitMQ, Durable Execution в Temporal, zero-alloc Avro-сериализатор `hamba/avro`).

Тем не менее, в модуле выявлен ряд критических дефектов кода и архитектурных концепций:

1. **Критические точки вмешательства:**
   - **Исправление синтаксической ошибки в Go:** Исправить некомпилируемый листинг `mu.muUnlock := func() { mu.Unlock() }` в `07. Практика/7. Тестирование async систем.md`.
   - **Удаление чужеродного кода (Java/Python):** Переписать примеры публикации и подписки в `04. NATS/3` и `04. NATS/6` на чистый идиоматичный Go (`franz-go` и `amqp091-go`).
   - **Устранение состояния гонки в тесте идемпотентности:** Заменить разрозненные вызовы `HasEvent`/`UpdateBalance` на атомарную операцию в единой транзакции в `07. Практика/7. Тестирование async систем.md`.
   - **Обеспечение потокобезопасности `amqp091-go.Channel`:** Добавить мьютексы или пул каналов в примерах RPC-клиента и Publisher в RabbitMQ.
   - **Защита Graceful Shutdown от сброса сообщений в DLQ:** Использовать `context.WithoutCancel` для предотвращения ложного `Nack(false)` на остатках очереди во время остановки.
   - **Коррекция архитектурного позиционирования Kafka:** Дополнить статью по Event Sourcing объяснением, почему чистая Kafka без вторичных индексов и OCC не может заменять специализированный Event Store.
   - **Предотвращение зависаний и дедлоков:** Устранить дедлок в `publishBatchFast` и заменить блокирующий `time.Sleep` на выборку с контекстом в цикле DLQ.
   - **Добавление таймаутов Activity в Temporal Saga:** Добавить `workflow.WithActivityOptions` с `StartToCloseTimeout` в код саги `TourBookingWorkflow`.
   - **Модернизация API NATS:** Обновить примеры JetStream на современный пакет `github.com/nats-io/nats.go/jetstream`.
   - **Исправление битых викиссылок:** Актуализировать 20 перекрестных ссылок `[[...]]`.

2. **Следующие шаги:**
   - Передать сформированный исследовательский бриф инженеру-фактчекеру для точечной сверки и внесения правок в файлы `sources/13. Очереди, брокеры сообщений и оркестраторы/`.
   - Провести полную пересборку проекта (`python3 builder/build_all.py --all`) и контрольный QA-аудит (`python3 builder/audit_all.py`) после применения исправлений.
