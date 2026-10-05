# 🧭 Исследовательский скаут-отчет: Модуль 11. Архитектура и System Design

> *«В распределенных системах любая архитектурная иллюзия — будь то вера в непогрешимость сети, синхронность репликации или надежность наивного ретрая — неизбежно материализуется в виде каскадного отказа, исчерпания пулов соединений и безвозвратной потери клиентских данных».*  
> — Исследовательский аудит архитектуры бэкенда и распределенных систем

---

## 📌 Паспорт модуля и объем проверки

* **Название модуля:** Модуль 11: Архитектура и System Design
* **Расположение исходных материалов:** `sources/11. Архитектура и System Design/`
* **Количество статей:** 54
* **Общий объем текста:** 19 334 строки Markdown
* **Количество блоков Go-кода:** 208
* **Роль и цель:** Первый независимый сквозной проход (First-Pass Fact-Check Research Scout). Глубокий и всесторонний аудит архитектурных концепций, контрактов распределенных систем, моделей консистентности, алгоритмов отказоустойчивости, реализаций паттернов на языке Go, сетевого поведения рантайма (G-M-P, Netpoller, GC, cgroups), а также выявление скрытых состояний гонки (Data Races), утечек ресурсов, математических ошибок, расхождений со спецификациями (RFC, W3C, AMQP, Kafka, Redis) и системных архитектурных пробелов (Blind Spots).

---

## 📊 Сводка найденных кандидатов

| Приоритет | Кол-во | Описание характера находок |
|:---:|:---:|---|
| 🔴 **High** | **12** | **Критические дефекты кода и архитектурные сбои:** Преждевременная отмена контекста запроса в оборонительном комплексе `CallWithResilience` (`defer cancel()`), блокирующая чтение тела ответа `resp.Body`; фатальное повреждение семантики смещений в `segmentio/kafka-go` (`reader.ReadMessage` автоматически коммитит оффсеты вопреки заверениям в тексте о ручном контроле); гарантированная постоянная утечка горутин (Goroutine Leak) в `WorkerPool` (приватный недоступный канал); тихая потеря данных (Silent Data Loss) при переполнении буфера в `WriteBehindCache`; гонка со сбросом устаревших данных (Stale Overwrite) в асинхронном Cache-Aside; вечная блокировка идемпотентного ключа в статусе `IN_PROGRESS` при аварии ноды и фиктивная транзакционность; молчаливое игнорирование сбоев компенсирующих транзакций в оркестраторе Saga; паника рантайма из-за отрицательного индекса слайса (`index out of range`) на 32-битных платформах в `ShardRouter.GetShard`; состояние гонки (Data Race) и паника `concurrent map read and map write` в AP-профиле `localMem`; конкурентное использование непотокобезопасного `amqp.Channel` и устаревший заброшенный драйвер `streadway/amqp`; фатальное падение Lua-скрипта в Redis при холодном ключе (`attempt to compare nil with number`); сервер mTLS полностью забывает загрузить собственный сертификат и ключ (`NewTLSServer`). |
| 🟡 **Medium** | **10** | **Алгоритмические несоответствия, утечки и искажения рендеринга:** Систематическое повреждение математических формул KaTeX из-за разыменования управляющих символов (`\approx` $\to$ `\x07`, `\beta` $\to$ `\x08`, `\forall` $\to$ `\x0c`, `\frac` $\to$ `\x0c`, `\text`/`\to`/`\times` $\to$ `0x09` tab); взрыв кардинальности (Cardinality Explosion) в Prometheus из-за сырого `r.URL.Path`; каскадный срыв сотен горутин при отмене контекста первого инициатора в `singleflight.Do`; подмена алгоритма Fixed Window Counter под видом «скользящего окна» (Sliding Window); неограниченная утечка памяти в внутрипроцессном Pub/Sub (`Subscribe` без `Unsubscribe`); мертвая ветка `<-r.Context().Done()` в неблокирующем `select` с `default`; использование опасного `time.After` в обработчике вопреки предупреждению через 50 строк; потеря аналитики при выборе HTTP 301 vs 302 в URL Shortener; содержательное дублирование кейсов в каталоге System Design (News Feed vs Twitter, Ozon vs E-commerce); последовательный блокирующий вызов коммита без таймаута в координаторе 2PC. |
| 🟢 **Low** | **5** | **Косметические дефекты, устаревшие SDK и деградация контрактов:** Использование устаревших API `grpc.DialContext` и `otlptracegrpc.WithInsecure()`; случайный H1-заголовок статьи 50 из-за bash-комментария; пропуск обязательного заголовка `WWW-Authenticate` при ошибке 401; обрыв конвейера данных без закрытия выходного канала в `RunPipeline`; необновление версии агрегата `order.Version` в памяти после `EventStore.Save`. |

---

## 🧭 Каталог кандидатов на углубленный фактчекинг

---

### Кандидат 1: Преждевременная отмена контекста ломает вычитывание `resp.Body` в оборонительном комплексе `CallWithResilience`
* **article/section:** `36. Circuit Breaker, Retry, Timeout и Backoff.md` / `### Интеграция четырёх механизмов` (строки 145–195)
* **claim:**  
  Функция `CallWithResilience` объединяет Circuit Breaker, Exponential Backoff и таймаут попытки:
  ```go
  retryErr := backoff.Retry(func() error {
      // 3. Уровень 3: Жесткий Timeout на одну конкретную попытку
      attemptCtx, cancel := context.WithTimeout(ctx, 400*time.Millisecond)
      defer cancel()

      req, _ := http.NewRequestWithContext(attemptCtx, http.MethodGet, url, nil)
      r, e := client.Do(req)
      if e != nil {
          return e
      }
      if r.StatusCode >= 500 {
          r.Body.Close()
          return fmt.Errorf("server 5xx error: %d", r.StatusCode)
      }
      resp = r
      return nil
  }, backoff.WithContext(expBackoff, ctx))
  ```
* **why it needs checking:**  
  В коде допущена классическая ошибка управления жизненным циклом контекста в Go `net/http`:
  1. **Отмена контекста до чтения тела ответа:** При успешном выполнении запроса замыкание `backoff.Retry` присваивает `resp = r` и завершается (`return nil`). В этот момент **немедленно срабатывает `defer cancel()`**, который отменяет `attemptCtx`.
  2. Согласно спецификации Go `net/http`, контекст запроса управляет всем жизненным циклом сетевой транзакции, включая чтение потока тела ответа (`resp.Body`). 
  3. Когда вызывающий код получает `*http.Response` и пытается прочитать данные через `io.ReadAll(resp.Body)` или `json.NewDecoder(resp.Body).Decode(...)`, сетевое соединение разрывается транспортом, и операция завершается фатальной ошибкой **`context canceled`**. Код в продакшене не сможет прочитать ни один успешный ответ, размер которого превышает размер первичного сетевого буфера заголовков.
  4. **Архитектурный антипаттерн вложенности CB и Retry:** Оборачивание ретраев внутрь вызова `cb.Execute(...)` скрывает промежуточные сбои от Circuit Breaker (серия из 4 сбоев и 1 успеха воспринимается автоматом как чистый 100% успех). Кроме того, в состоянии `Half-Open` автомат обязан пропустить ровно одну пробную попытку, а не затяжную серию повторов на 2 секунды.
* **evidence/source needed:** Документация пакета `net/http` (`http.Request.Context`, `http.Response.Body`); проверка отмены контекста при потоковом чтении ответа.
* **priority:** 🔴 **High**

---

### Кандидат 2: Фатальное повреждение семантики смещений в Kafka (`reader.ReadMessage` автоматически коммитит оффсет)
* **article/section:** `22. Pub Sub, Queue, Stream модели.md` / `### Stream в Go` (строки 198–218)
* **claim:**  
  Демонстрируется цикл чтения из Kafka с утверждением о ручном контроле коммитов при сбоях:
  ```go
  func consumePartition(ctx context.Context, reader *kafka.Reader, handler func(msg kafka.Message) error) {
      for {
          msg, err := reader.ReadMessage(ctx)
          if err != nil {
              log.Printf("read stream error: %v", err)
              break
          }
          if err := handler(msg); err != nil {
              log.Printf("processing failed: %v", err)
              // При ошибке мы НЕ коммитим offset!
              // Мы можем повторить обработку или направить в DLQ.
              continue
          }
          // Атомарно фиксируем прогресс чтения
          if err := reader.CommitMessages(ctx, msg); err != nil {
              log.Printf("commit failed: %v", err)
          }
      }
  }
  ```
* **why it needs checking:**  
  Это грубейшая ошибка использования библиотеки `segmentio/kafka-go`:
  1. Метод `reader.ReadMessage(ctx)` является высокоуровневой оберткой, которая **под капотом автоматически фиксирует смещение (auto-commit)** сразу после вычитывания сообщения:
     > *«ReadMessage reads and return the next message from the r. The method calls FetchMessage and CommitMessages internally».*
  2. Когда `handler(msg)` возвращает ошибку, и код выполняет `continue` со словами *«При ошибке мы НЕ коммитим offset!»*, смещение **уже зафиксировано в брокере Kafka** вызовом `ReadMessage`!
  3. Сообщение безвозвратно теряется для консьюмер-группы: при перезапуске сервиса или следующей итерации Kafka никогда больше не отдаст это ошибочное сообщение.
  4. Более того, при успешной обработке строка `reader.CommitMessages(ctx, msg)` выполняет **повторный избыточный коммит** уже зафиксированного оффсета. Для реализации ручного коммита после обработки автор обязан был использовать метод **`reader.FetchMessage(ctx)`**, а не `ReadMessage`.
* **evidence/source needed:** Исходный код и официальная документация `github.com/segmentio/kafka-go` (`Reader.ReadMessage` vs `Reader.FetchMessage`).
* **priority:** 🔴 **High**

---

### Кандидат 3: Гарантированная постоянная утечка горутин (Goroutine Leak) в `WorkerPool`
* **article/section:** `6. Вертикальное и горизонтальное масштабирование.md` / `#### Worker Pool для CPU-bound задач` (строки 158–168)
* **claim:**  
  Приводится реализация пула горутин для калибровки под `GOMAXPROCS`:
  ```go
  func WorkerPool(numWorkers int) {
      jobs := make(chan Job, numWorkers*2)
      for i := 0; i < numWorkers; i++ {
          go func() {
              for job := range jobs {
                  Process(job)
              }
          }()
      }
  }
  ```
* **why it needs checking:**  
  Листинг содержит грубейший дефект, делающий функцию абсолютно неработоспособной:
  1. Канал `jobs` создается как локальная переменная внутри `WorkerPool`.
  2. Функция `WorkerPool` **не принимает канал извне и не возвращает его наружу**.
  3. Горутины запускаются и входят в цикл `for job := range jobs`.
  4. Функция `WorkerPool` немедленно завершается. Локальная переменная `jobs` теряется.
  5. Ни один внешний компонент физически не способен отправить ни единой задачи в этот канал или закрыть его (`close(jobs)`).
  6. Все `numWorkers` горутин навечно повисают в состоянии `_Gwaiting` в памяти процесса Go. Это 100% гарантированная пожизненная утечка горутин, которая не выполняет полезной работы и вводит читателя в заблуждение.
* **evidence/source needed:** Анализ кода `sources/11. Архитектура и System Design/6. Вертикальное и горизонтальное масштабирование.md`.
* **priority:** 🔴 **High**

---

### Кандидат 4: Тихая потеря данных (Silent Data Loss) при переполнении буфера в `WriteBehindCache`
* **article/section:** `28. Кэширование. Cache Aside, Write Through, Write Back.md` / `##### Реализация Write-Behind в Go:` (строки 344–391)
* **claim:**  
  Реализация метода `Write` в асинхронном кэше со сбросом в БД:
  ```go
  func (c *WriteBehindCache) Write(ctx context.Context, key string, val any) error {
      // 1. Быстрая запись в Redis
      if err := c.client.Set(ctx, key, val, 24*time.Hour).Err(); err != nil {
          return err
      }

      // 2. Отправка в буфер асинхронного сброса
      select {
      case c.writes <- writeOp{key: key, value: val}:
          return nil
      default:
          // Буфер переполнен: защита от утечки памяти
          log.Printf("ALERT: Write-Behind буфер переполнен для ключа %s!", key)
          return nil
      }
  }
  ```
* **why it needs checking:**  
  В критическом компоненте персистентности замаскирована катастрофическая уязвимость потери данных:
  1. При переполнении буфера `c.writes` код попадает в ветку `default:` и возвращает **`return nil` (успех)**!
  2. Вызывающий клиент уверен, что операция записи прошла успешно и данные сохранены. Однако запись была сделана **только в Redis с TTL 24 часа**, а в очередь сброса в постоянную реляционную базу данных она **никогда не попадет**.
  3. Через 24 часа (или при аварийном рестарте пода Redis) эти данные исчезнут навсегда без единого следа в базе данных. Выдавать `nil` на сброшенную мимо постоянного хранилища запись — фатальный антипаттерн. В таких случаях архитектура обязана либо возвращать ошибку (например, `ErrBackpressureExceeded`), либо блокироваться с ожиданием слота, либо аварийно синхронно писать напрямую в СУБД.
  4. **Потеря буфера при Graceful Shutdown:** В методе `Start(ctx context.Context)` при наступлении `<-ctx.Done()` воркер сбрасывает текущий накопленный срез `batch`, но **игнорирует оставшиеся элементы в канале `c.writes`** (до `bufferSize` записей!), просто выходя из функции через `return`. Все сообщения, находящиеся в очереди канала, выбрасываются.
* **evidence/source needed:** Анализ исходного кода и принципов проектирования Write-Behind хранилищ.
* **priority:** 🔴 **High**

---

### Кандидат 5: Гонка со сбросом устаревших данных (Stale Overwrite) в асинхронном Cache-Aside
* **article/section:** `28. Кэширование. Cache Aside, Write Through, Write Back.md` / `##### Реализация Cache-Aside в Go:` (строки 133–152)
* **claim:**  
  ```go
  // 2. Промах кэша: загружаем из БД
  user, err := s.loadFromDB(ctx, id)
  if err != nil {
      return nil, err
  }

  // 3. Сохраняем в кэш (асинхронно или с коротким таймаутом)
  go func() {
      setCtx, cancel := context.WithTimeout(context.Background(), 500*time.Millisecond)
      defer cancel()

      data, marshalErr := json.Marshal(user)
      if marshalErr == nil {
          _ = s.cache.Set(setCtx, cacheKey, data, 5*time.Minute).Err()
      }
  }()
  ```
* **why it needs checking:**  
  Асинхронная запись в кэш через неконтролируемую горутину порождает тяжелейшее состояние гонки:
  1. **Сценарий рассинхронизации:** Горутина A получает промах кэша и читает из базы старую версию профиля пользователя (имя «Иван»).
  2. Горутина B выполняет `UpdateUser`, обновляет имя на «Петр», успешно коммитит транзакцию в БД и вызывает `cache.Del(ctx, cacheKey)`. Кэш чист.
  3. Неконтролируемая фоновая `go func()` горутины A просыпается *после* завершения работы горутины B и выполняет `cache.Set(..., "Иван", 5*time.Minute)`.
  4. В кэш Redis записываются **устаревшие данные**, которые останутся там на 5 минут! Любой последующий читатель будет получать старое значение («Иван»), хотя в базе данных уже сохранен «Петр».
  5. Кроме того, запуск неконтролируемой горутины `go func()` на каждый промах кэша при Cache Stampede мгновенно создает тысячи горутин, атакующих Redis параллельными сериализациями и сокетами.
* **evidence/source needed:** Исследования Martin Kleppmann о Cache-Aside race conditions; документация Redis Cache Patterns.
* **priority:** 🔴 **High**

---

### Кандидат 6: Вечная блокировка идемпотентного ключа в статусе `IN_PROGRESS` при падении ноды
* **article/section:** `27. Idempotency и exactly once семантика.md` / `#### 1. Идемпотентный обработчик на Go (Idempotency Key Pattern)` (строки 124–188)
* **claim:**  
  Обработчик резервирует ключ через `INSERT ... ON CONFLICT DO NOTHING` с указанием времени `locked_until`:
  ```go
  lockedUntil := time.Now().Add(10 * time.Second)
  query := `
      INSERT INTO idempotency_keys (key, status, locked_until)
      VALUES ($1, 'IN_PROGRESS', $2)
      ON CONFLICT (key) DO NOTHING
  `
  res, err := h.db.ExecContext(ctx, query, key, lockedUntil)
  // ...
  if rowsAffected == 0 {
      var rec IdempotencyRecord
      err := h.db.QueryRowContext(ctx, 
          `SELECT status, response_code, response_body FROM idempotency_keys WHERE key = $1`, 
          key,
      ).Scan(&rec.Status, &rec.ResponseCode, &rec.ResponseBody)
      // ...
      if rec.Status == "IN_PROGRESS" {
          w.Header().Set("Retry-After", "2")
          http.Error(w, "concurrent request in progress", http.StatusConflict) // 409 Conflict
          return
      }
      // ...
  }
  ```
* **why it needs checking:**  
  В логике блокировок присутствует системная дыра:
  1. В таблицу записывается поле `locked_until = NOW() + 10s`. Однако в блоке обработки конфликта (`rowsAffected == 0`) поле `locked_until` **вообще не запрашивается из БД и никак не проверяется**!
  2. Если рабочий инстанс сервиса аварийно завершился (OOM, panic, сбой ноды Kubernetes) во время выполнения `executeBusinessLogic`, статус записи в БД останется `'IN_PROGRESS'`.
  3. Любой последующий повторный запрос клиента (через 15 секунд, час или день) получит `rowsAffected == 0`, вычитает статус `'IN_PROGRESS'` и **навечно будет получать `409 Conflict`**. Запрос никогда не сможет быть повторен или завершен!
  4. Поле `locked_until` оказалось бесполезным бутафорским реквизитом. Для корректности запрос вставки обязан перехватывать истекшие блокировки, например: `INSERT ... ON CONFLICT (key) DO UPDATE SET status = 'IN_PROGRESS', locked_until = $2 WHERE idempotency_keys.status = 'IN_PROGRESS' AND idempotency_keys.locked_until < NOW()`.
  5. **Иллюзия транзакционности:** В блоке `[!info] Под капотом` прямо под листингом автор утверждает: *«В PostgreSQL это реализуется через INSERT INTO idempotency_keys ... в пределах одной локальной транзакции с бизнес-операцией»*. Но в самом коде функции транзакция `BeginTx` отсутствует вовсе — выполняются три разрозненных независимых вызова `h.db.ExecContext`!
* **evidence/source needed:** Документация паттерна Stripe Idempotency; архитектурные соглашения IETF Idempotency-Key HTTP Header Field.
* **priority:** 🔴 **High**

---

### Кандидат 7: Молчаливое игнорирование сбоев компенсирующих транзакций в оркестраторе Saga
* **article/section:** `26. Saga Pattern. Оркестрация и хореография.md` / `##### Реализация оркестратора на Go` (строки 306–344)
* **claim:**  
  При сбое шага 3 (списание средств) оркестратор запускает откат:
  ```go
  err = o.paymentSvc.Charge(ctx, orderID, cmd.Amount)
  if err != nil {
      log.Printf("[Orchestrator] Оплата отклонена. Запуск каскада компенсаций в обратном порядке...")
      saga.Status = "COMPENSATING"
      _ = o.sagaStore.Update(ctx, saga)

      // Компенсация в строгом обратном порядке:
      _ = o.inventorySvc.Release(ctx, orderID) // Компенсация шага 2
      _ = o.orderSvc.Cancel(ctx, orderID)      // Компенсация шага 1

      saga.Status = "FAILED"
      _ = o.sagaStore.Update(ctx, saga)
      return fmt.Errorf("payment charge failed: %w", err)
  }
  ```
* **why it needs checking:**  
  Здесь нарушено фундаментальное правило распределенной саги:
  1. Вызовы компенсирующих действий `Release` и `Cancel` обернуты в пустой идентификатор **`_ =`**, их ошибки **полностью проигнорированы**.
  2. Если сервис склада или сервис заказов временно недоступен (сетевой таймаут, 500 ошибка), компенсация молча проваливается, статус саги переводится в `FAILED`, и процесс завершается.
  3. В результате товары на складе остаются заблокированными навечно, либо заказ остается открытым. В теории распределенных транзакций **компенсация не имеет права просто «упасть»** — оркестратор обязан ретраить компенсации до победного конца (через Outbox/DLQ), либо переводить сагу в критический аварийный статус `COMPENSATION_FAILED` для ручного вмешательства инженера.
  4. **Потеря экземпляра саги при сбое:** Метод `o.sagaStore.Save(ctx, saga)` вызывается только *после* успешного завершения `o.orderSvc.Create(ctx, cmd)`. Если оркестратор упадет ровно между созданием заказа и сохранением саги в БД, заказ в `orderSvc` останется жить вечно, а восстановитель `ResumePendingSagas` о нем даже не узнает.
* **evidence/source needed:** Классическая статья Garcia-Molina & Salem (1987) «Sagas»; спецификации Temporal.io / Cadence по обработке сбоев компенсаций.
* **priority:** 🔴 **High**

---

### Кандидат 8: Паника рантайма из-за отрицательного индекса слайса (`index out of range`) на 32-битных платформах в `ShardRouter`
* **article/section:** `31. Partitioning и Sharding.md` / `### Реализация в Go: маршрутизация на уровне приложения` (строки 138–150)
* **claim:**  
  ```go
  func (r *ShardRouter) GetShard(key string) *sql.DB {
      h := r.hash(key) // uint32 от crc32.ChecksumIEEE
      idx := int(h) % len(r.shards)
      return r.shards[idx]
  }
  ```
* **why it needs checking:**  
  Классическая платформенно-зависимая ловушка целочисленного переполнения в Go:
  1. Метод `r.hash(key)` возвращает `uint32`.
  2. На 32-битных платформах (`GOARCH=386`, `arm`, `mips`) базовый тип `int` является 32-битным знаковым целым числом (`int32`).
  3. Если хэш-сумма превышает `0x7FFFFFFF` (например, `0x80000001` = 2 147 483 649), приведение `int(h)` интерпретирует старший бит как знаковый, превращая число в **отрицательное** (`-2 147 483 647`).
  4. В Go операция остатка от деления отрицательного числа на положительное дает **отрицательный результат** (например, `-2147483647 % 4 == -3`).
  5. Индексация `r.shards[-3]` приводит к моментальной фатальной панике: **`panic: runtime error: index out of range [-3]`** и падению всего сервиса!
  6. Безопасное каноническое вычисление обязано брать модуль до преобразования в знаковый тип: `idx := int(h % uint32(len(r.shards)))`.
* **evidence/source needed:** Спецификация языка Go (Numeric types, Integer overflow, Modulo operator); верификация на 32-битной архитектуре.
* **priority:** 🔴 **High**

---

### Кандидат 9: Состояние гонки (Data Race) и паника `concurrent map read and map write` в AP-профиле `localMem`
* **article/section:** `30. CAP теорема и реальные компромиссы.md` / `#### 2. Реализация AP-подхода с плавной деградацией (Fallback)` (строки 194–221)
* **claim:**  
  ```go
  type APProfileService struct {
      primaryDB *redis.Client // Основное хранилище
      localMem  map[string]*Profile
  }
  // ...
  func (s *APProfileService) GetProfile(ctx context.Context, id string) (*Profile, error) {
      val, err := s.primaryDB.Get(ctx, "profile:"+id).Result()
      if err == nil {
          return &Profile{ID: id, Bio: val, Stale: false}, nil
      }

      // 2. В случае сетевого сбоя: отдаём устаревшие данные (Fallback)
      if cached, ok := s.localMem[id]; ok {
          log.Printf("WARN: основная база недоступна; отдаем устаревшие данные для профиля %s", id)
          cached.Stale = true
          return cached, nil // Доступность сохранена ценой согласованности!
      }
      return nil, fmt.Errorf("profile completely unavailable: %w", err)
  }
  ```
* **why it needs checking:**  
  В коде присутствуют сразу две грубые ошибки конкурентности:
  1. Поле `localMem` объявлено как стандартная несинхронизированная карта Go `map[string]*Profile` без `sync.RWMutex` или `sync.Map`. Если параллельно с чтением фоновый воркер будет наполнять эту карту, рантайм Go немедленно выбросит фатальную неперехватываемую панику: **`fatal error: concurrent map read and map write`**.
  2. Даже при чисто параллельном чтении строка `cached.Stale = true` мутирует общее поле структуры по разделяемому указателю `*Profile` из десятков параллельных горутин-обработчиков HTTP-запросов. Это классический **Data Race**, выявляемый детектором `go test -race`.
* **evidence/source needed:** Спецификация The Go Memory Model; запуск `go run -race`.
* **priority:** 🔴 **High**

---

### Кандидат 10: Конкурентное использование непотокобезопасного `amqp.Channel` и устаревший драйвер `streadway/amqp`
* **article/section:** `22. Pub Sub, Queue, Stream модели.md` / `### Queue в Go` (строки 129–158)
* **claim:**  
  ```go
  import "github.com/streadway/amqp"

  func startWorkers(ctx context.Context, channel *amqp.Channel, queueName string, workers int, handler func(msg amqp.Delivery)) {
      for i := 0; i < workers; i++ {
          go func(workerID int) {
              deliveries, err := channel.Consume(queueName, "", false, false, false, false, nil)
              // ...
              for {
                  select {
                  case <-ctx.Done(): return
                  case msg, ok := <-deliveries:
                      handler(msg)
                      _ = msg.Ack(false)
                  }
              }
          }(i)
      }
  }
  ```
* **why it needs checking:**  
  1. **Нарушение потокобезопасности `amqp.Channel`:** В цикле `for i := 0; i < workers` каждая горутина вызывает `channel.Consume(...)` на **одном и том же экземпляре `*amqp.Channel`**. Согласно официальной документации AMQP-клиентов для Go:
     > *«It is not safe to use Channel concurrently across multiple goroutines»*.  
     Параллельный вызов `Consume` и параллельные `msg.Ack` на одном канале вызывают повреждение внутренних структур кадров AMQP и аварийное закрытие сокета брокером. Правильный паттерн: либо вызывать `Consume` один раз и раздавать сообщения из возвращенного канала `<-chan amqp.Delivery` пулу воркеров, либо открывать отдельный `amqp.Channel` на каждую горутину.
  2. **Заброшенная библиотека:** Пакет `github.com/streadway/amqp` официально заброшен и не поддерживается с 2021 года. Официальным современным преемником от команды RabbitMQ является **`github.com/rabbitmq/amqp091-go`**.
* **evidence/source needed:** Документация `github.com/rabbitmq/amqp091-go` и репозитория `streadway/amqp`.
* **priority:** 🔴 **High**

---

### Кандидат 11: Падение Lua-скрипта в Redis при отсутствии ключа (`attempt to compare nil with number`)
* **article/section:** `52. Разбор типичных System Design задач.md` / `### 10. Интернет-магазин (High-Load E-commerce)` (строки 553–563)
* **claim:**  
  В качестве эталонного решения проблемы race condition при списании остатков товара предлагается атомарный Lua-скрипт:
  ```lua
  local stock = redis.call('GET', KEYS[1])
  if tonumber(stock) > 0 then
      redis.call('DECR', KEYS[1])
      return 1
  else
      return 0
  end
  ```
* **why it needs checking:**  
  В скрипте содержится критический баг обработки краевого случая в движке Lua Redis:
  1. Если товар еще не был прогрет в кэше или ключ был вытеснен по политике памяти LRU, команда `redis.call('GET', KEYS[1])` возвращает `false` (в контексте Redis Lua).
  2. Функция `tonumber(false)` возвращает **`nil`**.
  3. Выражение `if nil > 0` в языке Lua является синтаксически некорректным и немедленно выбрасывает рантайм-ошибку интерпретатора:  
     **`ERR Error running script: @user_script:2: attempt to compare nil with number`**.
  4. Вместо безопасного возврата кода 0 запрос в продакшене падает с внутренней ошибкой драйвера Redis. Скрипт обязан проверять: `local stock = redis.call('GET', KEYS[1]); if stock and tonumber(stock) > 0 then ...`.
* **evidence/source needed:** Документация Redis Programmability & Lua scripting; выполнение скрипта в `redis-cli --eval`.
* **priority:** 🔴 **High**

---

### Кандидат 12: Сервер mTLS забывает загрузить собственный сертификат и ключ (`NewTLSServer`)
* **article/section:** `45. Zero Trust и сетевые границы.md` / `#### 1. Сервер с требованием клиентского сертификата` (строки 100–126)
* **claim:**  
  ```go
  func NewTLSServer(certFile, keyFile, caCertFile string) (*http.Server, error) {
      caCert, err := os.ReadFile(caCertFile)
      if err != nil { return nil, err }

      caCertPool := x509.NewCertPool()
      caCertPool.AppendCertsFromPEM(caCert)

      tlsConfig := &tls.Config{
          ClientAuth: tls.RequireAndVerifyClientCert,
          ClientCAs:  caCertPool,
          MinVersion: tls.VersionTLS13,
      }

      return &http.Server{
          Addr:      ":8443",
          TLSConfig: tlsConfig,
      }, nil
  }
  ```
* **why it needs checking:**  
  Функция принимает параметры `certFile` и `keyFile`, но **вообще не использует их**:
  1. Сервер не загружает ключевую пару через `tls.LoadX509KeyPair(certFile, keyFile)` и не наполняет срез `tlsConfig.Certificates`.
  2. Если запустить такой сервер через `server.ListenAndServeTLS("", "")`, вызов упадет с ошибкой **`tls: no certificates configured`**.
  3. Если же запустить его через `server.ListenAndServe()`, он поднимется по открытому незашифрованному протоколу HTTP на порту 8443, полностью обесценив архитектуру Zero Trust. В листинге клиента ниже (`NewTLSClient`) сертификат загружается безупречно, что делает пропуск на стороне сервера досадным дефектом.
* **evidence/source needed:** Исходный код пакета `crypto/tls` (`tls.Config.Certificates`).
* **priority:** 🔴 **High**

---

### Кандидат 13: Систематическое повреждение математических формул KaTeX из-за разыменования управляющих символов
* **article/section:** Множественные статьи Модуля 11:
  - `25. Distributed Transactions. 2PC и проблемы.md`: строка 291 (`\approx` $\to$ `\x07` Bell)
  - `28. Кэширование. Cache Aside, Write Through, Write Back.md`: строка 525 (`\beta` $\to$ `\x08` Backspace)
  - `29. Consistency модели. Strong, Eventual, Causal.md`: строки 209, 212 (`\forall` $\to$ `\x0c` Formfeed)
  - `31. Partitioning и Sharding.md`: строка 108 (`\approx` $\to$ `\x07`, `\frac` $\to$ `\x0c`)
  - `33. Load Balancing на уровне архитектуры.md`: строки 83, 268 (`\approx` $\to$ `\x07`, `\text`/`\to`/`\times` $\to$ `0x09` Tab)
  - `38. Rate Limiting и защита системы.md`: строки 90, 156, 243 (`\text`/`\times` $\to$ `0x09` Tab)
* **claim:**  
  Примеры поврежденных формул в исходном Markdown:
  - `$$A_{\text{total}} = 0.999^5 \x07pprox 99.5\\%$$` (вместо `\approx`)
  - `$$\text{Time} - (\x08eta \times \delta \times \ln(\text{rand}())) > \text{Expiry}$$` (вместо `\beta`)
  - `$$\x0corall k: V_{local}[k] = \max(V_{local}[k], V_{msg}[k])$$` (вместо `\forall`)
  - `$$\text{Rebalanced Keys} \x07pprox \x0crac{K}{N+1}$$` (вместо `\approx \frac{K}{N+1}`)
  - `$10 	imes 100 = 1 000$` (байт табуляции вместо `\times`)
* **why it needs checking:**  
  При генерации статического сайта движок KaTeX падает с ошибкой синтаксического разбора формул, либо отображает управляющие мусорные символы в браузере. Это аналогично дефекту, выявленному в Модуле 10, и требует глобальной очистки исходных `.md` файлов от неэкранированных байтов ASCII `0x07`, `0x08`, `0x0C` и `0x09`.
* **evidence/source needed:** Сканирование файлов скриптом проверки управляющих байтов (см. вывод python-инспектора).
* **priority:** 🟡 **Medium**

---

### Кандидат 14: Угроза взрыва кардинальности (Cardinality Explosion) в Prometheus из-за сырого `r.URL.Path`
* **article/section:** `4. SLA, SLO, SLI и как они влияют на дизайн.md` / `#### 1. Latency (Задержка)` (строки 80–112)
* **claim:**  
  В качестве промышленного примера SLI-middleware предлагается код:
  ```go
  var httpRequestDuration = promauto.NewHistogramVec(
      prometheus.HistogramOpts{
          Name: "http_request_duration_seconds",
          Help: "Длительность обработки HTTP запросов",
      },
      []string{"method", "path"},
  )

  func MetricsMiddleware(next http.Handler) http.Handler {
      return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
          start := time.Now()
          defer func() {
              duration := time.Since(start).Seconds()
              httpRequestDuration.WithLabelValues(r.Method, r.URL.Path).Observe(duration)
          }()
          next.ServeHTTP(w, r)
      })
  }
  ```
* **why it needs checking:**  
  Использование сырого `r.URL.Path` в лейблах метрик Prometheus — хрестоматийный антипаттерн высоконагруженных систем:
  1. Если в приложении есть эндпоинты с динамическими параметрами в пути (например, `/users/123`, `/orders/f47ac10b-...`), каждый уникальный ID порождает **новую независимую временную серию (time series)** в памяти Go-приложения и базе Prometheus.
  2. При миллионе запросов клиентская библиотека Prometheus аллоцирует сотни тысяч объектов метрик, что приводит к исчерпанию оперативной памяти и OOM Killer.
  3. В продакшен-коде всегда используется шаблон маршрута (route template / pattern), например `chi.RouteContext(r.Context()).RoutePattern()` или ручная нормализация путей.
* **evidence/source needed:** Prometheus Best Practices: Metric and Label Naming («Caution with dynamic labels»).
* **priority:** 🟡 **Medium**

---

### Кандидат 15: Каскадный срыв сотен горутин при отмене контекста первого инициатора в `singleflight.Do`
* **article/section:** `28. Кэширование. Cache Aside, Write Through, Write Back.md` / `#### Защита через golang.org/x/sync/singleflight` (строки 488–519)
* **claim:**  
  ```go
  func (s *SafeCacheService) GetUserProfile(ctx context.Context, userID string) (*UserProfile, error) {
      cacheKey := "user:profile:" + userID

      val, err, shared := s.flightGroup.Do(cacheKey, func() (any, error) {
          // Тяжелый запрос в базу данных
          return s.loadFromDB(ctx, userID)
      })
      if err != nil { return nil, err }
      return val.(*UserProfile), nil
  }
  ```
* **why it needs checking:**  
  Классическая коварная ловушка пакета `singleflight`:
  1. Параметр `ctx` передается в функцию замыкания из вызова первого вошедшего клиента.
  2. Если 500 параллельных горутин ожидают завершения этого единого запроса, а у первого клиента сработает короткий клиентский таймаут (или пользователь закроет вкладку браузера, оборвав соединение), контекст `ctx` перейдет в состояние `Canceled`.
  3. Метод `loadFromDB(ctx, userID)` прервется по отмене контекста.
  4. В результате **все 500 ожидающих клиентов мгновенно упадут с ошибкой `context canceled`**, хотя их собственные контексты были абсолютно живы и имели запас по времени.
  5. Для надежной изоляции либо используют независимый контекст для фоновой загрузки (`context.WithoutCancel(ctx)` в Go 1.21+), либо применяют неблокирующий `flightGroup.DoChan` с индивидуальным `select` по `ctx.Done()` каждого клиента.
* **evidence/source needed:** Go Issue tracker: singleflight context propagation pitfalls.
* **priority:** 🟡 **Medium**

---

### Кандидат 16: Подмена алгоритма: выдача Fixed Window Counter за «скользящее окно» (Sliding Window)
* **article/section:** `38. Rate Limiting и защита системы.md` / `#### Распределённый Rate Limiting через Redis` (строки 171–199)
* **claim:**  
  ```go
  // Атомарный Lua-скрипт скользящего окна / Fixed Window
  var rateLimitLua = redis.NewScript(`
      local key = KEYS[1]
      local limit = tonumber(ARGV[1])
      local window = tonumber(ARGV[2])

      local current = redis.call("INCR", key)
      if current == 1 then
          redis.call("EXPIRE", key, window)
      end

      if current > limit then
          return 0
      else
          return 1
      end
  `)

  func IsAllowedDistributed(ctx context.Context, rdb *redis.Client, clientID string, limit int, windowSec int) (bool, error) {
      key := fmt.Sprintf("ratelimit:%s:%d", clientID, time.Now().Unix()/int64(windowSec))
      res, err := rateLimitLua.Run(ctx, rdb, []string{key}, limit, windowSec).Int()
      // ...
  }
  ```
* **why it needs checking:**  
  1. Код и ключ `time.Now().Unix()/int64(windowSec)` реализуют классический **Fixed Window Counter** (фиксированное дискретное окно), а не Sliding Window.
  2. На стыке окон (например, за секунду до конца окна и через секунду после старта нового) клиент может отправить $2 \times \text{limit}$ запросов без блокировки (краевой эффект Fixed Window Burst).
  3. Называть этот алгоритм «скользящим окном» методологически неверно. Для истинного скользящего окна (Sliding Window Log / Counter) требуется либо расчет взвешенного среднего между текущим и прошлым окном, либо использование `ZSET` (`ZADD`, `ZREMRANGEBYSCORE`).
  4. В этом же файле в методе `Reserve()` (строки 140–150) используется `time.Sleep(reservation.Delay())`, что игнорирует отмену контекста `r.Context().Done()` и может заблокировать горутину на часы при большом `Delay()` без проверки лимита ожидания.
* **evidence/source needed:** RFC 6585; документация Redis Rate Limiting patterns.
* **priority:** 🟡 **Medium**

---

### Кандидат 17: Неограниченная утечка памяти в внутрипроцессном Pub/Sub (`Subscribe` без `Unsubscribe`)
* **article/section:** `22. Pub Sub, Queue, Stream модели.md` / `### Pub/Sub в Go` (строки 70–103)
* **claim:**  
  ```go
  type Broker struct {
      mu   sync.RWMutex
      subs map[string][]chan Event
  }

  func (b *Broker) Subscribe(subject string) <-chan Event {
      ch := make(chan Event, 64)
      b.mu.Lock()
      b.subs[subject] = append(b.subs[subject], ch)
      b.mu.Unlock()
      return ch
  }
  ```
* **why it needs checking:**  
  1. В структуре отсутствует метод отписки `Unsubscribe(subject string, ch <-chan Event)`.
  2. При динамических подписках (например, клиент WebSocket подключается и отключается, либо создается временный слушатель на время HTTP-запроса) срез `b.subs[subject]` растет монотонно.
  3. Отключившиеся клиенты и их каналы остаются в памяти навсегда, приводя к медленной, но неизбежной утечке памяти (Unbounded Memory Leak) и замедлению `Publish`, который будет тратить циклы на попытки отправки в брошенные каналы.
* **evidence/source needed:** Идиоматичные паттерны Pub/Sub в Go; реализация подписок в библиотеке `nats.go`.
* **priority:** 🟡 **Medium**

---

### Кандидат 18: Мертвая ветка `case <-r.Context().Done()` в неблокирующем `select` с `default`
* **article/section:** `43. Backpressure и контроль нагрузки.md` / `### Семафор для ограничения конкурентности` (строки 140–158)
* **claim:**  
  ```go
  func handleRequest(w http.ResponseWriter, r *http.Request) {
      select {
      case sem <- struct{}{}: // Захватываем свободный слот семафора
          defer func() { <-sem }()
          process(r)

      case <-r.Context().Done():
          // Клиент оборвал соединение или истек таймаут ожидания
          http.Error(w, "request canceled or timed out", http.StatusGatewayTimeout)

      default:
          // Семафор переполнен: мгновенный сброс нагрузки с кодом 503
          w.Header().Set("Retry-After", "5")
          http.Error(w, "too many requests", http.StatusServiceUnavailable)
      }
  }
  ```
* **why it needs checking:**  
  1. Наличие ветки `default:` делает весь оператор `select` строго **неблокирующим**.
  2. Если в `sem` есть свободное место, срабатывает первая ветка. Если места нет, а контекст клиента еще не отменен (стандартный сценарий живого запроса), управление **мгновенно проваливается в `default:`**.
  3. Ветка `case <-r.Context().Done():` фактически является мертвым кодом — она может сработать только в том невероятном случае, если клиент разорвал соединение в микросекундный интервал ровно до входа в `select` и при этом `sem` оказался заполнен.
  4. Кроме того, возврат кода `504 Gateway Timeout` при отмене клиентского контекста семантически некорректен (RFC 9110 резервирует 504 для таймаутов апстрим-шлюзов).
* **evidence/source needed:** Спецификация Go (Select statements); RFC 9110 HTTP Semantics.
* **priority:** 🟡 **Medium**

---

### Кандидат 19: Использование опасного `time.After` в обработчике вопреки предупреждению через 50 строк
* **article/section:** `43. Backpressure и контроль нагрузки.md` (строки 272–282 vs 335–337)
* **claim:**  
  В строках 272–282 предлагается функция отправки с таймаутом:
  ```go
  func PushWithTimeout(ch chan<- Task, task Task, timeout time.Duration) error {
      select {
      case ch <- task:
          return nil
      case <-time.After(timeout):
          backpressureDropped.Inc()
          return ErrBufferFull
      }
  }
  ```
  А ровно через 50 строк (строка 335) следует предупреждение:
  > *«Ловушка / Gotcha: Смертоносный time.After() в горячем цикле select. Будьте предельно осторожны с вызовом time.After(duration)... Каждый вызов аллоцирует новый таймер в рантайме Go, который не может быть собран GC до тех пор, пока не истечет указанное время! ... приводит к колоссальной утечке памяти»*.
* **why it needs checking:**  
  Прямое внутреннее противоречие в рамках одной статьи:
  1. Функция `PushWithTimeout` вызывается на каждое входящее сообщение.
  2. При успешном помещении в канал (`ch <- task`) таймер, созданный `time.After(timeout)`, не останавливается и продолжает висеть в куче рантайма Go до истечения таймаута. При высоком Throughput это вызывает именно ту утечку таймеров, о которой предупреждает автор.
  3. Реализация обязана использовать `time.NewTimer` с явным `defer timer.Stop()`.
* **evidence/source needed:** Документация `time.After` и Go runtime timers.
* **priority:** 🟡 **Medium**

---

### Кандидат 20: Опасное умолчание о потере аналитики при выборе HTTP 301 vs 302 в URL Shortener
* **article/section:** `52. Разбор типичных System Design задач.md` / `### 1. Сервис сокращения ссылок (URL Shortener)` (строки 18, 91)
* **claim:**  
  - *«При переходе по короткой ссылке $\rightarrow$ мгновенный HTTP-редирект (301/302)»*.
  - *«Сбор аналитики переходов в реальном времени (гео-локация, User-Agent, Referrer)»*.
* **why it needs checking:**  
  В канонических задачах System Design выбор статуса редиректа — главный проверочный вопрос:
  1. Если сервер возвращает **`301 Moved Permanently`**, браузер клиента навсегда кэширует этот ответ в своем локальном дисковом кэше.
  2. Все последующие клики этого пользователя по короткой ссылке будут выполняться браузером локально, вообще без обращения к серверу редиректов!
  3. В результате **требование о сборе аналитики кликов будет полностью сорвано**: сервер зафиксирует только самый первый переход одного пользователя.
  4. Для систем, где сбор аналитики обязателен, стандартом является возврат **`302 Found`** или **`307 Temporary Redirect`** (с заголовками отключения кэширования). Упоминание `301/302` через слэш без разбора этого фундаментального компромисса — серьезный педагогический пробел.
* **evidence/source needed:** RFC 9110 (301 Moved Permanently vs 302 Found caching semantics); Alex Xu «System Design Interview» Chapter 8.
* **priority:** 🟡 **Medium**

---

### Кандидат 21: Содержательное дублирование кейсов в каталоге System Design (News Feed vs Twitter, Ozon vs E-commerce)
* **article/section:** `52. Разбор типичных System Design задач.md` (разделы 3 vs 5, 8 vs 10)
* **claim:**  
  В статье разбираются 10 систем:
  - Раздел 3: «Новостная лента (News Feed) — аналог ленты Твиттера/Фейсбука» (Fan-out on Write, Redis Sorted Sets, Celebrity Problem).
  - Раздел 5: «Аналог Твиттера» (посты, Fan-out, таймлайны, тренды).
  - Раздел 8: «Аналог Озона (Маркетплейс)» (каталог, корзина, резервирование остатков в Black Friday).
  - Раздел 10: «Интернет-магазин (High-Load E-commerce)» (каталог, корзина, оверселл в Black Friday, singleflight).
* **why it needs checking:**  
  Кейсы 3 и 5, а также 8 и 10 по сути дублируют архитектурные схемы и модели данных одного и того же класса систем. При этом из практикума выпали классические для Senior-собеседований темы:
  - Распределенный поисковый краулер (Distributed Web Crawler).
  - Платформа видеостриминга (YouTube / Netflix: транскодирование чанков, DASH/HLS).
  - Сервис совместного редактирования документов (Google Docs: Operational Transformation / CRDT).
* **evidence/source needed:** Программа типовых System Design интервью в бигтехе.
* **priority:** 🟡 **Medium**

---

### Кандидат 22: Последовательный блокирующий вызов коммита без таймаута в координаторе 2PC
* **article/section:** `25. Distributed Transactions. 2PC и проблемы.md` / `#### Координатор транзакций на Go` (строки 227–234)
* **claim:**  
  ```go
  // Рассылка Commit участникам
  var commitErrors []error
  for _, p := range c.participants {
      // Фаза Commit не может быть отменена обычным таймаутом!
      if err := p.Commit(context.Background(), txID); err != nil {
          log.Printf("ALERT: Сбой фиксации коммита на участнике %s: %v", p.ID(), err)
          commitErrors = append(commitErrors, err)
      }
  }
  ```
* **why it needs checking:**  
  1. Рассылка коммита выполняется **строго последовательно** в одном потоке с `context.Background()`.
  2. Если первый участник зависает из-за сетевого разделения сети (Partition), координатор навечно блокируется на первом же сетевом вызове, так и не отправив команду коммита остальным участникам кластера.
  3. Все остальные участники остаются подвешенными с заблокированными строками таблиц. Рассылка коммита обязана быть параллельной и снабженной независимым механизмом фоновых повторов.
* **evidence/source needed:** Jim Gray «Notes on Data Base Operating Systems» (Two-Phase Commit Protocol).
* **priority:** 🟡 **Medium**

---

### Кандидат 23: Использование устаревших API `grpc.DialContext` и `otlptracegrpc.WithInsecure()`
* **article/section:** `33. Load Balancing на уровне архитектуры.md` (строка 225), `34. Service Discovery...md` (строка 136), `40. Distributed Tracing...md` (строка 171)
* **claim:**  
  Использование `grpc.DialContext(...)` и `otlptracegrpc.WithInsecure()`.
* **why it needs checking:**  
  1. В современных версиях `google.golang.org/grpc` (v1.59+) методы `grpc.Dial` и `grpc.DialContext` **официально объявлены Deprecated**. Рекомендованным стандартом является использование **`grpc.NewClient`**.
  2. В `go.opentelemetry.io/otel/exporters/otlp/otlptrace/otlptracegrpc` опция `WithInsecure()` объявлена устаревшей в пользу `WithTLSCredentials(insecure.NewCredentials())`.
* **evidence/source needed:** Release notes `grpc-go` v1.59.0; OpenTelemetry Go SDK docs.
* **priority:** 🟢 **Low**

---

### Кандидат 24: Случайный H1-заголовок статьи 50 из-за bash-комментария
* **article/section:** `50. Cost optimization в архитектуре.md` (строка 1 и 234)
* **claim:**  
  Документ начинается с `## Архитектура, которая не разоряет` (отсутствует H1 уровня `# `), а парсер заголовков сборщика принимает за H1 комментарий из bash-блока на строке 234: `# Ограничиваем память рантайма 450 МБ внутри 512 МБ cgroups контейнера`.
* **why it needs checking:**  
  При сборке сайта на главной странице и в боковом меню статья отображается со странным заголовком про 450 МБ вместо темы Cost Optimization.
* **evidence/source needed:** Проверка заголовка статьи в `dist/index.html`.
* **priority:** 🟢 **Low**

---

### Кандидат 25: Пропуск обязательного заголовка `WWW-Authenticate` при ошибке 401 в Auth Middleware
* **article/section:** `45. Zero Trust и сетевые границы.md` / `### JWT и авторизация на уровне приложения` (строки 244, 260)
* **claim:**  
  При отсутствии токена или его невалидности возвращается:
  `http.Error(w, "missing or malformed authorization header", http.StatusUnauthorized)`.
* **why it needs checking:**  
  Согласно RFC 9110 (§15.5.2) и RFC 6750 (§3), при возврате статуса `401 Unauthorized` сервер **обязан** передавать заголовок `WWW-Authenticate: Bearer error="invalid_token"`, информирующий клиента о схеме авторизации.
* **evidence/source needed:** RFC 6750 «The OAuth 2.0 Authorization Framework: Bearer Token Usage».
* **priority:** 🟢 **Low**

---

### Кандидат 26: Обрыв конвейера данных без закрытия выходного канала в `RunPipeline`
* **article/section:** `41. Data Pipeline и потоковая обработка.md` (строка 142)
* **claim:**  
  При получении сигнала закрытия входного стрима:
  ```go
  case raw, ok := <-input:
      if !ok {
          logger.Info("input stream closed, terminating pipeline")
          return
      }
  ```
* **why it needs checking:**  
  Функция завершает работу через `return`, не закрывая канал `output`. Если следующая стадия конвейера вычитывает данные циклом `for ev := range output`, она навечно зависнет в ожидании, порождая дедлок конвейера. Корректный паттерн требует вызова `close(output)` при завершении обработки.
* **evidence/source needed:** Go Pipeline Patterns (Go Blog: Pipelines and cancellation).
* **priority:** 🟢 **Low**

---

### Кандидат 27: Необновление `order.Version` в памяти после `EventStore.Save`
* **article/section:** `24. Event Sourcing. Хранение событий вместо состояния.md` (строки 207–221)
* **claim:**  
  ```go
  func (r *OrderRepository) Save(ctx context.Context, order *Order) error {
      // Оптимистическая блокировка по версии агрегата:
      err := r.store.Append(ctx, order.ID, order.Version, order.uncommittedEvents)
      if err != nil { return err }

      order.uncommittedEvents = nil
      return nil
  }
  ```
* **why it needs checking:**  
  После успешного сохранения событий в `EventStore` поле `order.Version` остается старым (не увеличивается на количество сохраненных событий). Если вызывающий код продолжит работать с этим экземпляром агрегата в памяти и вызовет `Save` повторно, вызов упадет с ложным конфликтом версий оптимистической блокировки.
* **evidence/source needed:** Martin Fowler «Event Sourcing»; Greg Young CQRS/ES guidelines.
* **priority:** 🟢 **Low**

---

## 🔍 Системные белые пятна и архитектурные пробелы

В ходе глубокого анализа Модуля 11 выявлены важные темы и инженерные аспекты, оставшиеся за рамками текущего текста:

1. **Quorum Reads/Writes в Leaderless репликации ($W + R > N$) и сбои линеаризуемости:**  
   В статье [[32. Репликация. Leader Follower и Multi Leader]] упомянуты кворумы Dynamo, однако отсутствует критически важное объяснение, почему условие $W + R > N$ само по себе **НЕ гарантирует строгую линеаризуемость** при конкурентных записях (проблема фантомных чтений и необходимость Read Repair / Sloppy Quorums).
2. **Martin Kleppmann vs Redlock: проблема распределенных блокировок:**  
   В статьях о кэшировании и блокировках рекомендуется Redlock в Redis. Однако не упомянута классическая дискуссия Мартина Клеппмана о ненадежности Redlock при паузах Garbage Collector и необходимости применения монотонно возрастающих защитных токенов (**Fencing Tokens**).
3. **Проблема троттлинга CPU в Kubernetes CFS Quota (`cpu.cfs_quota_us`):**  
   Для многопоточного рантайма Go выставление жестких CPU Limits в Kubernetes часто приводит к парадоксальному троттлингу сервиса даже при утилизации CPU в 30–40% из-за всплесков параллельных потоков. Отсутствует разбор библиотеки `go.uber.org/automaxprocs` как обязательного средства адаптации `GOMAXPROCS` к cgroups.
4. **Change Data Capture (CDC / Debezium) как единственный надежный Outbox:**  
   В темах событийной архитектуры и идемпотентности часто рекомендуется Transactional Outbox, но процесс вычитки таблицы Outbox описан поверхностно (опрос шедулером). Не раскрыт промышленный стандарт CDC через чтение репликационного WAL-лога СУБД.
5. **Теорема CAP: Brewer vs Gilbert & Lynch (формализация понятий):**  
   В популярной культуре CAP трактуется вольно («выбери 2 из 3»). Стоит жестче зафиксировать формальные границы теоремы: доказательство Гилберт-Линч относится строго к асинхронной сети и модели атомарных регистров (Linearizability), а свойство $P$ является неотъемлемым свойством физического мира, а не опцией выбора.

---

## 💡 Рекомендации для следующей фазы (Fact-Check Action Plan)

1. **Первоочередные исправления кода (Кандидаты 1, 2, 3, 4, 8, 11, 12):**  
   - Исправить `CallWithResilience` в статье 36, исключив отмену контекста до вычитывания `resp.Body`.
   - Заменить `ReadMessage` на `FetchMessage` в примере Kafka (статья 22).
   - Привести `WorkerPool` в статье 6 к рабочей сигнатуре с передачей канала извне.
   - Исключить возврат `nil` при сбросе записей в `WriteBehindCache` (статья 28).
   - Защитить вычисление остатка шардирования `idx` в статье 31 от отрицательных чисел.
   - Исправить валидацию `nil` в Redis Lua-скрипте в статье 52.
   - Добавить загрузку сертификата и ключа в `NewTLSServer` (статья 45).
2. **Автоматическая санация KaTeX (Кандидат 13):**  
   Провести скриптовую замену разыменованных байтов `\x07`, `\x08`, `\x0c` и паразитных табуляций `0x09` внутри формул `$...$` и `$$...$$` во всех файлах модуля.
3. **Синхронизация заголовков и оглавления:**  
   Нормализовать верхнеуровневый заголовок H1 в `50. Cost optimization в архитектуре.md`.
