# 🧭 Исследовательский скаут-отчет: Модуль 18. Observability (Мониторинг и наблюдаемость)

> 📌 **Статус на 2026-10-10** (пометка Claude Opus 5.5 вне конвейера фактчека; текст отчёта ниже не менялся).
> Отчёт написан по `sources/` до коммита `2b7c9945` (2026-10-05). После этого книга прошла выделение движка
> `html-textbook-engine` и чистку: **фактура статей не менялась**, кроме отмеченного в таблице и у отдельных
> кандидатов («✅ Статус на 2026-10-10»). Изменился вывод сайта: списки Obsidian, блоки кода в пунктах, защита
> формул `$`/`$$`, ссылки с путём, один заголовок на странице. Если кандидат описывает, как статья *выглядит*
> на сайте, сверяйтесь с текущим `dist/`. Подробности — `AGENTS.md` § 11.4 и `engine-extraction/README.md`.
>
> Изменённые файлы модуля 18 (номера строк — «старые строки: сдвиг»):
>
> | Файл | Что изменилось | Строки |
> |---|---|---|
> | `02. Метрики/1. Типы метрик. Counter, Gauge, Histogram.md` | двойной H1 сведён (подзаголовок или удаление) | не сдвигались |
> | `02. Метрики/2. Prometheus. Основы.md` | двойной H1 сведён (подзаголовок или удаление) | не сдвигались |
> | `02. Метрики/3. Экспорт метрик в Go.md` | двойной H1 сведён (подзаголовок или удаление) | не сдвигались |
> | `02. Метрики/4. Label и их опасности.md` | двойной H1 сведён (подзаголовок или удаление) | не сдвигались |
> | `02. Метрики/5. SLA, SLO, SLI.md` | двойной H1 сведён (подзаголовок или удаление) | не сдвигались |
> | `03. Логирование/1. Structured logging.md` | двойной H1 сведён (подзаголовок или удаление) | 3–199: -2 |
> | `03. Логирование/2. Уровни логирования.md` | двойной H1 сведён (подзаголовок или удаление) | не сдвигались |
> | `03. Логирование/3. Логирование в Go.md` | двойной H1 сведён (подзаголовок или удаление) | не сдвигались |
> | `03. Логирование/4. Централизованные логи.md` | двойной H1 сведён (подзаголовок или удаление) | не сдвигались |
> | `03. Логирование/5. Log aggregation системы.md` | двойной H1 сведён (подзаголовок или удаление) | не сдвигались |
> | `04. Трейсинг/1. Distributed tracing.md` | двойной H1 сведён (подзаголовок или удаление) | не сдвигались |
> | `04. Трейсинг/2. OpenTelemetry.md` | двойной H1 сведён (подзаголовок или удаление) | не сдвигались |
> | `04. Трейсинг/3. Спаны и трейсы.md` | двойной H1 сведён (подзаголовок или удаление) | не сдвигались |
> | `04. Трейсинг/4. Контекст propagation.md` | двойной H1 сведён (подзаголовок или удаление) | не сдвигались |
> | `04. Трейсинг/5. Jaeger и альтернативы.md` | двойной H1 сведён (подзаголовок или удаление) | не сдвигались |
> | `05. Практика/1. Correlation ID.md` | двойной H1 сведён (подзаголовок или удаление) | не сдвигались |
> | `05. Практика/2. Debugging через observability.md` | двойной H1 сведён (подзаголовок или удаление) | не сдвигались |
> | `05. Практика/3. Alerting и алерты.md` | двойной H1 сведён (подзаголовок или удаление) | не сдвигались |
> | `05. Практика/4. Noise vs signal.md` | двойной H1 сведён (подзаголовок или удаление) | не сдвигались |
> | `05. Практика/5. Observability в Kubernetes.md` | двойной H1 сведён (подзаголовок или удаление) | не сдвигались |
> | `05. Практика/6. Итоги раздела. Observable system.md` | двойной H1 сведён (подзаголовок или удаление) | 3–105: -2 |

> *«Самым надежным инструментом отладки по-прежнему остается вдумчивое размышление, подкрепленное разумно расставленными операторами вывода».*  
> — Брайан Керниган

---

## 📌 Паспорт модуля и объем проверки

* **Название модуля:** Модуль 18: Observability (Мониторинг и наблюдаемость)
* **Расположение исходных материалов:** `sources/18. Observability (Мониторинг и наблюдаемость)/`
* **Количество статей:** 25 статей в 5 тематических разделах:
  1. `01. Основы` (4 статьи)
  2. `02. Метрики` (5 статей)
  3. `03. Логирование` (5 статей)
  4. `04. Трейсинг` (5 статей)
  5. `05. Практика` (6 статей)
* **Общий объем текста:** 4 220 строк Markdown
* **Роль и цель:** Первый независимый сквозной проход (First-Pass Fact-Check Research Scout). Широкий поиск потенциально некорректных, устаревших, вводящих в заблуждение, упрощенных, платформенно- и рантайм-зависимых утверждений, некомпилируемых примеров кода, гонок данных, нарушений контрактов стандартной библиотеки Go, а также системных архитектурных белых пятен (Blind Spots).

---

## 📊 Сводка найденных кандидатов

| Приоритет | Кол-во | Описание характера находок |
|:---:|:---:|---|
| 🔴 **High** | **8** | Ложное утверждение о ленивом вычислении аргументов функций в `slog`; использование несуществующего типа `slog.HandlerFunc`; сломанная инициализация сервера с потерей кастомного `http.ServeMux`; опасный миф об автоматическом определении лимитов памяти cgroups рантаймом Go 1.21+; вызов несуществующего метода `logger.Handler().Sync()`; некомпилируемый псевдокод OpenTelemetry Baggage API; использование антипаттерна ненормализованного пути `r.URL.Path` в качестве лейбла в обучающих примерах; физически невозможный порог алерта длительности пауз сборщика мусора `rate(...) > 10`. |
| 🟡 **Medium** | **7** | Несинхронизированная глобальная `map` в примере утечки памяти, вызывающая фатальную панику `concurrent map writes`; грубая математическая ошибка в расчете Burn Rate 14.4; некомпилируемый вызов метода `ObserveWithExemplar` на интерфейсе `prometheus.Observer`; селектор доступности SLI, классифицирующий 4xx ошибки клиентов как успешные запросы; опасная рекомендация передавать контекст HTTP-запроса в фоновую горутину без отвязки через `context.WithoutCancel`; наивная обертка `responseWriter`, скрывающая интерфейсы `http.Flusher` и `http.Hijacker`; устаревшие семантические конвенции OpenTelemetry HTTP. |
| 🟢 **Low** | **3** | Утечка тикера и бесконечная горутина в примере обновления `Gauge`; использование `rate(...[7d])` на сырых данных вместо Recording Rules; отсутствие упоминания `trace.Link` при асинхронном ветвлении трейсов. |

---

## 🧭 Каталог кандидатов на углубленный фактчекинг

---

### Кандидат 1: Ложное утверждение о ленивом вычислении аргументов в `slog`
* **article/section:** `03. Логирование/1. Structured logging.md` / `## Under the Hood: Mechanical Sympathy / 2. Проверка уровня логирования (Level Check)` (строки 121–132)
* **claim:**  
  ```go
  // ПЛОХО: Строка конкатенируется и аргументы вычисляются ВСЕГДА,
  // даже если уровень логирования INFO отключен в проде.
  log.Println("Debug info: " + heavyFunction())

  // ХОРОШО: slog проверяет уровень ДО выполнения.
  // Если уровень ниже Debug, тяжелая функция не вызывается.
  slog.Debug("Debug info", "data", slog.Any("val", heavyFunction()))
  ```
  Текст утверждает: *«Если логгер настроен на уровень Info, метод slog.Debug проверяет handler.Enabled(ctx, slog.LevelDebug) в первой же инструкции, и если уровень выключен — немедленно выходит без форматирования и аллокаций»*.
* **why it needs checking:** В языке Go аргументы функций вычисляются строго **до** входа в вызываемую функцию (call-by-value / eager evaluation). Вызов `heavyFunction()` будет выполнен **всегда**, вне зависимости от настроенного уровня логирования в хендлере `slog`.  
  Утверждение, что `slog.Debug(..., slog.Any("val", heavyFunction()))` предотвращает выполнение `heavyFunction()`, фундаментально ложно и формирует опаснейшее заблуждение у обучающихся.  
  *(Примечательно, что в следующей статье `03.02 Уровни логирования.md` (строки 78–97) автор сам себе противоречит, правильно объясняя необходимость явной проверки `if logger.Enabled(...)`).*
  Чтобы вычисление было действительно отложенным, необходимо либо обернуть вызов в `if logger.Enabled(ctx, slog.LevelDebug)`, либо использовать тип с реализацией интерфейса `slog.LogValuer`.
* **evidence/source needed:** Спецификация языка Go (Function calls and argument evaluation); документация пакета `log/slog` (`go doc log/slog.LogValuer`).
* **priority:** 🔴 **High**

---

### Кандидат 2: Несуществующий тип `slog.HandlerFunc` в примере связывания Trace ID
* **article/section:** `05. Практика/1. Correlation ID.md` / `### Шаг 2: Автоматическая запись Trace ID в логи` (строки 120–134)
* **claim:**  
  ```go
  // TraceLoggerMiddleware оборачивает slog, добавляя trace_id из ctx
  func TraceLoggerMiddleware(logger *slog.Logger) *slog.Logger {
      return slog.New(slog.HandlerFunc(func(ctx context.Context, r slog.Record) error {
          // Извлекаем SpanContext из контекста OpenTelemetry
          spanCtx := trace.SpanContextFromContext(ctx)

          // Если Trace ID валиден, добавляем его в лог
          if spanCtx.IsValid() {
              r.AddAttrs(slog.String("trace_id", spanCtx.TraceID().String()))
          }

          return logger.Handler().Handle(ctx, r)
      }))
  }
  ```
* **why it needs checking:** В стандартной библиотеке Go (`log/slog`) **не существует** типа или адаптера `slog.HandlerFunc`.  
  Интерфейс `slog.Handler` состоит из четырех методов: `Enabled`, `Handle`, `WithAttrs`, `WithGroup`. Попытка скомпилировать данный код завершится фатальной ошибкой компилятора:  
  `undefined: slog.HandlerFunc`.  
  Для декорирования `slog.Handler` разработчик обязан реализовать полноценную структуру со всеми четырьмя методами интерфейса.
* **evidence/source needed:** Исходный код и документация стандартной библиотеки Go: `log/slog/handler.go` (`go doc log/slog.Handler`).
* **priority:** 🔴 **High**

---

### Кандидат 3: Нерабочий запуск сервера и потеря кастомного `http.ServeMux`
* **article/section:** `02. Метрики/3. Экспорт метрик в Go.md` / `### Использование promhttp (Production Way)` (строки 208–214)
* **claim:**  
  ```go
      mux := http.NewServeMux()
      mux.Handle("/api/v1/hello", instrumentedHandler)

      // Запускаем сервер с кастомным регистром
      http.Handle("/metrics", promhttp.HandlerFor(reg, promhttp.HandlerOpts{}))
      http.ListenAndServe(":8080", nil)
  ```
* **why it needs checking:** В примере создается изолированный роутер `mux := http.NewServeMux()`, на котором регистрируется бизнес-маршрут `/api/v1/hello`. Однако затем вызывается `http.ListenAndServe(":8080", nil)`.  
  Передача аргумента `nil` в `http.ListenAndServe` предписывает стандартной библиотеке использовать глобальный `http.DefaultServeMux`. Созданный локальный экземпляр `mux` полностью игнорируется и отбрасывается! В результате:
  1. Любой запрос к `http://localhost:8080/api/v1/hello` будет возвращать ошибку `404 Not Found`.
  2. Ручка `/metrics` регистрируется в глобальном `DefaultServeMux`, что противоречит пропагандируемому в этой же статье отказу от глобального состояния.
  Код должен регистрировать `/metrics` на самом `mux` (`mux.Handle("/metrics", ...)`) и передавать `mux` в `ListenAndServe(":8080", mux)`.
* **evidence/source needed:** Документация пакета `net/http` (`go doc net/http.ListenAndServe`, `go doc net/http.DefaultServeMux`).
* **priority:** 🔴 **High**

---

### Кандидат 4: Ложное утверждение об автоматическом определении лимитов cgroups в Go 1.21+
* **article/section:** `05. Практика/5. Observability в Kubernetes.md` / `## Under the Hood: Container Metrics (cAdvisor)` (строки 96–98, 121)
* **claim:**  
  *«В Go 1.21+ runtime автоматически определяет cgroup limits и настраивает GC. Убедитесь, что вы используете свежую версию Go и задаете переменную окружения GOMEMLIMIT...»*  
  и в итогах:  
  *«В Go 1.19+ runtime «подружился» с cgroups, автоматически учитывая лимиты памяти контейнера»*.
* **why it needs checking:** Рантайм Go **НЕ определяет** автоматически лимиты памяти cgroups!  
  В Go 1.19 был добавлен механизм мягкого ограничения памяти `GOMEMLIMIT` (`debug.SetMemoryLimit`), но по умолчанию значение `GOMEMLIMIT` бесконечно (`math.MaxInt64`). Если разработчик или манифест Kubernetes явно не экспортирует переменную `GOMEMLIMIT`, сборщик мусора Go понятия не имеет о лимитах пода, ориентируясь на физическую память всей ноды (например, 64–128 ГБ), что гарантированно приводит к уничтожению контейнера ядром Linux через OOM Killer.  
  Для автоматического считывания лимитов cgroups в Kubernetes сообщество Go использует стороннюю библиотеку `github.com/KimMachineGun/automemlimit`. Утверждать, что Go делает это сам из коробки — критическая ошибка.
* **evidence/source needed:** Go Documentation: `runtime/debug.SetMemoryLimit`; Go Issue #51364 / #53455; репозиторий `KimMachineGun/automemlimit`.
* **priority:** 🔴 **High**

---

### Кандидат 5: Вызов несуществующего метода `logger.Handler().Sync()` в `log/slog`
* **article/section:** `03. Логирование/4. Централизованные логи.md` / `> [!warning] Ловушка / Gotcha` (строки 73–77)
* **claim:**  
  *«В log/slog используйте logger.Handler().Sync() (или Flush в асинхронных обертках) перед завершением работы в рамках Graceful Shutdown»*.
* **why it needs checking:** В стандартной библиотеке Go интерфейс `slog.Handler` **не содержит метода `Sync()`**. Метод `Sync()` является визитной карточкой библиотеки `go.uber.org/zap` (`zap.Logger.Sync()`), но не имеет никакого отношения к стандартному `slog`.  
  Попытка вызвать `logger.Handler().Sync()` приведет к ошибке компиляции:  
  `logger.Handler().Sync undefined (type slog.Handler has no field or method Sync)`.
* **evidence/source needed:** Исходный код `log/slog/handler.go` (`go doc log/slog.Handler`).
* **priority:** 🔴 **High**

---

### Кандидат 6: Несуществующий API OpenTelemetry Baggage
* **article/section:** `04. Трейсинг/4. Контекст propagation.md` / `## Baggage: Данные, которые путешествуют` (строки 188–197)
* **claim:**  
  ```go
  // В сервисе A:
  baggage.Set(ctx, "user.id", "12345")

  // В сервисе C (если настроен Baggage Propagator):
  member, _ := baggage.Member("user.id")
  fmt.Println(member.Value()) // "12345"
  ```
* **why it needs checking:** Данный листинг является вымышленным некомпилируемым кодом. В официальном пакете `go.opentelemetry.io/otel/baggage` отсутствуют функции `baggage.Set` и пакетный метод `baggage.Member`.  
  В OpenTelemetry Go объект `Baggage` неизменяем (immutable). Канонический синтаксис требует:
  ```go
  // Запись:
  m, _ := baggage.NewMember("user.id", "12345")
  b, _ := baggage.New(m)
  ctx = baggage.ContextWithBaggage(ctx, b)

  // Чтение:
  b := baggage.FromContext(ctx)
  member := b.Member("user.id")
  fmt.Println(member.Value())
  ```
* **evidence/source needed:** Документация пакета `go.opentelemetry.io/otel/baggage` (`go doc go.opentelemetry.io/otel/baggage`).
* **priority:** 🔴 **High**

---

### Кандидат 7: Использование `r.URL.Path` в качестве лейбла метрики в учебных листингах
* **article/section:** `02. Метрики/1. Типы метрик. Counter, Gauge, Histogram.md` (строки 72, 195) и `02. Метрики/3. Экспорт метрик в Go.md` (строка 147)
* **claim:**  
  В `02.01`:
  ```go
  defer func() {
      httpRequestsTotal.WithLabelValues(r.URL.Path, r.Method).Inc()
  }()
  ...
  requestDuration.WithLabelValues(r.URL.Path).Observe(duration)
  ```
  В `02.03`:
  ```go
  httpDuration.WithLabelValues(r.URL.Path).Observe(duration)
  ```
* **why it needs checking:** Передача сырого пути `r.URL.Path` напрямую в лейблы Prometheus — классический и опаснейший источник взрыва кардинальности (High Cardinality Explosion) и последующего OOM-падения сервиса при наличии URL-параметров (например, `/users/1`, `/users/2` или сканирования ботами).  
  При этом в следующей статье `02.04 Label и их опасности.md` (строка 83) этот же самый код прямо назван автором **«ОПАСНЫЙ КОД»**! Включение опасного антипаттерна в вводные главы под видом идиоматичного кода («Идиоматичное использование Counter в Go HTTP-сервере») без нормализации маршрута (через роутер или `r.Pattern` в Go 1.22+) является грубой педагогической ловушкой.
* **evidence/source needed:** `02. Метрики/4. Label и их опасности.md`; Prometheus Best Practices: Instrumentation & Label Naming.
* **priority:** 🔴 **High**

---

### Кандидат 8: Физически невозможный порог алерта длительности пауз GC
* **article/section:** `05. Практика/3. Alerting и алерты.md` / `## Специфика Go: Что нужно мониторить обязательно?` (строки 124–126)
* **claim:**  
  *«2. GC Pressure:  
  `rate(go_gc_duration_seconds_sum[5m]) > 10`.  
  Если GC запускается слишком часто, это значит, что приложение генерирует слишком много мусора. Это «тормозит» реальную работу (Stop-The-World pauses)»*.
* **why it needs checking:** Метрика `go_gc_duration_seconds` (или `go_gc_pauses_seconds`) измеряет суммарную длительность Stop-The-World (STW) пауз сборщика мусора в секундах.  
  Функция PromQL `rate(...[5m])` вычисляет среднюю скорость прироста этой величины в секунду (секунд паузы в секунду астрономического времени). В одной секунде реального времени отдельный процесс физически не может провести в паузе STW более 1.0 секунды!  
  Значение `rate(...)` для отдельного инстанса математически ограничено диапазоном $[0.0; 1.0]$ (где 1.0 — это 100% времени полная остановка мира). Порог `> 10` не может быть достигнут **никогда в физической реальности**, и такой алерт никогда не сработает даже при катастрофическом зависании приложения в GC.  
  Реалистичные пороги для алерта критической деградации от пауз GC составляют `> 0.05` (5% времени) или `> 0.1` (10% времени в STW).
* **evidence/source needed:** Prometheus Documentation: `rate()`; Go runtime memory & GC monitoring guide; спецификация метрик Go runtime в `client_golang`.
* **priority:** 🔴 **High**

---

### Кандидат 9: Несинхронизированная глобальная `map` в примере утечки памяти
* **article/section:** `05. Практика/2. Debugging через observability.md` / `### Шаг 3: Анализ кода (Go Specific)` (строки 110–119)
* **claim:**  
  ```go
  // Глобальная карта, из которой мы забываем удалять ключи
  var activeRequests = make(map[int]*Request)

  func process(id int) {
      activeRequests[id] = &Request{}
      // Если мы забыли delete(activeRequests, id) в конце, память утечет.
      // Поскольку map глобальная, GC не тронет значения.
  }
  ```
* **why it needs checking:** В конкурентном веб-сервере одновременный вызов функции `process(id)` из нескольких горутин приведет к параллельной записи в обычную карту Go без блокировок.  
  Рантайм Go мгновенно аварийно завершит процесс с фатальной неустранимой паникой:  
  `fatal error: concurrent map writes`.  
  Процесс упадет за микросекунды задолго до того, как память успеет утечь и инженер сможет снять дамп кучи через `pprof`. Учебный пример утечки обязан использовать потокобезопасную структуру (`sync.Mutex` или `sync.Map`), чтобы демонстрировать именно утечку памяти, а не тривиальный data race.
* **evidence/source needed:** Go runtime map concurrency safety; The Go Race Detector.
* **priority:** 🟡 **Medium**

---

### Кандидат 10: Математическая ошибка в расчете Burn Rate 14.4
* **article/section:** `02. Метрики/5. SLA, SLO, SLI.md` / `### Alerting: Burn Rate (Скорость сжигания бюджета)` (строка 121)
* **claim:**  
  *«Burn Rate = 14.4 означает, что 100% месячного бюджета сгорит всего за 2 дня (5% бюджета сгорает за 1 час)»*.
* **why it needs checking:** В формуле допущена грубая арифметическая ошибка:
  В месяце 30 дней, что равно $30 \times 24 = 720$ часам.
  При Burn Rate = 1 расход бюджета составляет $1 / 720 \approx 0.1389\%$ в час (100% за 30 дней).
  При Burn Rate = 14.4 расход бюджета в час равен $14.4 \times (1 / 720) = 14.4 / 720 = 0.02$, то есть **ровно 2% бюджета за 1 час** (а вовсе не 5%).
  100% бюджета при Burn Rate 14.4 сгорит за $720 / 14.4 = 50$ часов ($\approx 2.08$ дня).
  Если бы за 1 час сгорало 5% бюджета, то Burn Rate составлял бы $5\% \times 720 / 100\% = 36$, и весь бюджет сгорел бы за 20 часов (менее 1 суток).
  В канонической книге Google SRE (глава Alerting on SLOs) Burn Rate 14.4 привязан именно к расходу **2% бюджета за 1 час**.
* **evidence/source needed:** Google SRE Workbook, Chapter 5: Alerting on SLOs; Site Reliability Engineering book.
* **priority:** 🟡 **Medium**

---

### Кандидат 11: Некомпилируемый вызов `ObserveWithExemplar` на `prometheus.Observer`
* **article/section:** `05. Практика/1. Correlation ID.md` / `## Связь с метриками: Exemplars` (строки 157–160)
* **claim:**  
  ```go
  // При использовании Histogram
  httpDuration.WithLabelValues("/api").ObserveWithExemplar(duration, map[string]string{
      "traceID": trace.SpanContextFromContext(ctx).TraceID().String(),
  })
  ```
* **why it needs checking:** Метод `httpDuration.WithLabelValues(...)` возвращает интерфейс `prometheus.Observer`, у которого определен единственный метод `Observe(float64)`.  
  Метод `ObserveWithExemplar` принадлежит отдельному интерфейсу `prometheus.ExemplarObserver`. Попытка вызвать его напрямую приведет к ошибке компиляции:  
  `httpDuration.WithLabelValues("/api").ObserveWithExemplar undefined (type prometheus.Observer has no field or method ObserveWithExemplar)`.  
  Необходимо явное приведение типа:  
  `httpDuration.WithLabelValues("/api").(prometheus.ExemplarObserver).ObserveWithExemplar(...)`.  
  Кроме того, тип аргумента меток — `prometheus.Labels` (псевдоним `map[string]string`), а не анонимная `map`.
* **evidence/source needed:** Пакет `github.com/prometheus/client_golang/prometheus` (`go doc prometheus.ExemplarObserver`, `go doc prometheus.Observer`).
* **priority:** 🟡 **Medium**

---

### Кандидат 12: Некорректный селектор кодов ответов в формуле SLI доступности
* **article/section:** `02. Метрики/5. SLA, SLO, SLI.md` / `### SLI: Доступность (Availability)` (строки 100–105)
* **claim:**  
  ```promql
  # SLI: Доля успешных запросов (HTTP 2xx, 3xx) за последние 7 дней
  sum(rate(http_requests_total{status!~"5.."}[7d])) 
  / 
  sum(rate(http_requests_total[7d]))
  ```
* **why it needs checking:** Комментарий утверждает, что метрика считает долю успешных запросов (HTTP 2xx, 3xx). Однако фильтр `status!~"5.."` исключает только пятисотые коды.  
  Это означает, что запросы со статусами 400 Bad Request, 401 Unauthorized, 403 Forbidden, 404 Not Found и 429 Too Many Requests **будут засчитаны как успешные**! Если в продакшене из-за бага аутентификации 100% клиентов получат HTTP 401, данный SLI продолжит показывать идеальную доступность 100%.  
  Для корректного подсчета 2xx и 3xx фильтр должен быть явным: `status=~"[23].."`.  
  Кроме того, вычисление `rate(...[7d])` по сырым точкам за 7 дней в одном запросе перегружает PromQL-движок; в продакшене для таких интервалов применяются Recording Rules.
* **evidence/source needed:** Google SRE Book: Implementing SLOs; Prometheus PromQL Documentation.
* **priority:** 🟡 **Medium**

---

### Кандидат 13: Передача контекста запроса в фоновую горутину без `WithoutCancel`
* **article/section:** `04. Трейсинг/1. Distributed tracing.md` / `> [!warning] Ловушка / Gotcha` (строки 93–98)
* **claim:**  
  *«Если вы запускаете новую горутину для фоновой задачи, она не наследует контекст автоматически, если вы не передадите его явно. `go func() { doWork(ctx) }()` Если передать `ctx`, новая горутина продолжит участвовать в текущем трейсе. Если передать `context.Background()` или `context.TODO()`, связь потеряется»*.
* **why it needs checking:** В веб-серверах Go контекст запроса `r.Context()` автоматически **отменяется сразу же**, как только завершается выполнение метода `ServeHTTP`.  
  Если разработчик передаст этот `ctx` в фоновую горутину, все сетевые операции, запросы к БД и таймеры внутри этой горутины мгновенно завершатся с ошибкой `context.Canceled` в ту же миллисекунду, когда клиенту будет отправлен ответ.  
  Начиная с Go 1.21, для безопасного сохранения значений трейсинга без наследования отмены необходимо использовать `context.WithoutCancel(ctx)`, либо вручную отвязать SpanContext через `trace.ContextWithSpanContext(context.Background(), trace.SpanContextFromContext(ctx))`.
* **evidence/source needed:** Документация Go: `context.WithoutCancel` (Go 1.21+); спецификация OpenTelemetry Context API.
* **priority:** 🟡 **Medium**

---

### Кандидат 14: Наивная обертка `responseWriter` ломает `http.Flusher` и `http.Hijacker`
* **article/section:** `02. Метрики/3. Экспорт метрик в Go.md` / `### Реализация собственного Middleware` (строки 121–131)
* **claim:**  
  ```go
  // responseWriter перехватывает HTTP-статус код
  type responseWriter struct {
      http.ResponseWriter
      statusCode int
  }

  func (rw *responseWriter) WriteHeader(code int) {
      rw.statusCode = code
      rw.ResponseWriter.WriteHeader(code)
  }
  ```
* **why it needs checking:** Простое встраивание `http.ResponseWriter` в пользовательскую структуру приводит к скрытию опциональных интерфейсов, реализованных реальным объектом `ResponseWriter` стандартного сервера: `http.Flusher`, `http.Hijacker`, `http.Pusher`.  
  Это «молча» ломает:
  - Server-Sent Events (SSE) и потоковую передачу данных (так как `w.(http.Flusher)` завершится с `ok == false`);
  - WebSocket-соединения (так как `w.(http.Hijacker)` завершится с ошибкой);
  - HTTP/2 Server Push.
  Кроме того, повторные вызовы `WriteHeader` будут перезаписывать `rw.statusCode`, в то время как стандартный рантайм Go фиксирует только первый статус-код.
* **evidence/source needed:** Стандартная библиотека Go: `net/http` optional response writer interfaces (`http.Flusher`, `http.Hijacker`); реализация в production-библиотеках (например, `chi/middleware.WrapResponseWriter`).
* **priority:** 🟡 **Medium**

---

### Кандидат 15: Устаревшие семантические конвенции OpenTelemetry HTTP
* **article/section:** `04. Трейсинг/2. OpenTelemetry.md` / `## Semantic Conventions (Семантические соглашения)` (строки 147–152)
* **claim:**  
  *«OpenTelemetry ввел стандарты именования атрибутов:  
  `http.method`: "GET"  
  `net.peer.name`: "database-server"»*
* **why it needs checking:** В современных спецификациях OpenTelemetry Semantic Conventions (стабилизированных в v1.21+ / v1.25+) эти атрибуты были объявлены устаревшими (deprecated):
  - Вместо `http.method` стандартом является `http.request.method`.
  - Вместо `http.status_code` стандартом является `http.response.status_code`.
  - Вместо `net.peer.name` стандартом является `server.address` или `network.peer.address`.  
  Использование старых соглашений приводит к несовместимости с современными версиями Grafana Tempo, APM-дэшбордами и коллектором OTel.
* **evidence/source needed:** OpenTelemetry Semantic Conventions v1.26+ (HTTP and Network conventions migration).
* **priority:** 🟡 **Medium**

---

### Кандидат 16: Утечка тикера и фоновой горутины в примере обновления `Gauge`
* **article/section:** `02. Метрики/1. Типы метрик. Counter, Gauge, Histogram.md` / `### Under the Hood` (строки 124–133)
* **claim:**  
  ```go
  func recordMetrics() {
      // Периодическое обновление Gauge в фоновой горутине
      ticker := time.NewTicker(5 * time.Second)
      for range ticker.C {
          goroutinesGauge.Set(float64(runtime.NumGoroutine()))
      }
  }
  ```
* **why it needs checking:** Горутина запускает бесконечный цикл `for range ticker.C` без контекста завершения (`ctx.Done()`) и без вызова `defer ticker.Stop()`.  
  В тестах или при рестарте сервиса это приводит к утечке горутин и системных таймеров рантайма. Более того, сам этот паттерн опроса метрик рантайма вручную через фоновый таймер является антипаттерном в Prometheus: для таких вычислений `client_golang` предоставляет `GaugeFunc` (`promauto.NewGaugeFunc`), о чем справедливо говорится двумя статьями позже.
* **evidence/source needed:** Документация `time.NewTicker`; Effective Go: Concurrency & Resources Cleanup.
* **priority:** 🟢 **Low**

---

### Кандидат 17: Использование `rate(...[7d])` на сырых метриках вместо Recording Rules
* **article/section:** `02. Метрики/5. SLA, SLO, SLI.md` / `### SLO: Проверка цели` (строки 100–115)
* **claim:**  
  ```promql
  (sum(rate(http_requests_total{status!~"5.."}[7d])) / sum(rate(http_requests_total[7d]))) >= 0.999
  ```
* **why it needs checking:** Запрос `rate(...[7d])` на 7-дневном окне требует от Prometheus TSDB чтения и распаковки с диска сотен тысяч чанков за целую неделю в рамках одного вычислительного запроса.  
  В продакшене выполнение таких «тяжелых» выражений напрямую в Alert Rules или дашбордах перегружает CPU TSDB и приводит к таймаутам. Стандартом SRE является предварительный расчет суточных и часовых агрегатов через **Recording Rules** (например, `job:http_requests_total:rate5m`), поверх которых затем строится долгосрочный SLO.
* **evidence/source needed:** Prometheus Best Practices: Recording Rules & Alerting Rules.
* **priority:** 🟢 **Low**

---

### Кандидат 18: Отсутствие механизма `trace.Link` при асинхронном ветвлении трейсов
* **article/section:** `05. Практика/1. Correlation ID.md` / `> [!warning] Ловушка / Gotcha` (строки 171–177)
* **claim:**  
  *«Если вы передали ctx в горутину, вы сохраните Trace ID, но имейте в виду: спан родительской функции может закрыться (defer span.End()), когда горутина еще работает... В таких случаях нужно использовать trace.Link или новую логику трассировки»*.
* **why it needs checking:** Замечание абсолютно справедливо по сути, однако в тексте полностью отсутствует пример того, как технически создается спан со связью `trace.WithLinks(trace.Link{SpanContext: ...})`.  
  Без наглядного примера инженеры либо продолжают создавать разорванные дочерние спаны от уже закрытых родителей, либо полностью теряют контекст в фоновых задачах очередей сообщений.
* **evidence/source needed:** OpenTelemetry Go SDK: `trace.WithLinks`.
* **priority:** 🟢 **Low**

---

## 🔍 Системные слепые зоны и архитектурные пробелы модуля (Blind Spots)

### 1. Отсутствие современных Native Histograms (Sparse Histograms)
Во всех главах, посвященных метрикам (`01.04`, `02.01`, `02.02`), гистограммы рассматриваются исключительно в рамках классической модели дискретных корзин (`_bucket{le="..."}`) с подробным описанием катастрофического раздувания кардинальности при добавлении бакетов.  
Однако начиная с Prometheus 2.40+ (и окончательно в Prometheus 3.0 / OpenTelemetry Exponential Histograms) в индустрию вошли **Native Histograms (нативные разреженные гистограммы)**. Они кодируют экспоненциальные бакеты в одной-единственной временной серии без деления на десятки независимых рядов. Это революционное изменение кардинальности полностью обойдено вниманием.

### 2. Полное отсутствие темы `GOMAXPROCS` в контейнерах Kubernetes
В статье `05.05 Observability в Kubernetes.md` подробно обсуждаются cgroups, лимиты памяти и CPU, но полностью отсутствует упоминание критической проблемы **`GOMAXPROCS` в контейнеризованном Go**.  
По умолчанию рантайм Go устанавливает `GOMAXPROCS` по числу ядер физического хоста (например, 64 или 128 ядер), даже если поду в Kubernetes выделена квота в 2 ядра (`resources.limits.cpu: 2`). Это порождает сотни лишних потоков ОС, дикую конкуренцию за планировщик ядра (throttling) и деградацию задержек P99. Обязательным инструментом в K8s является библиотека `go.uber.org/automaxprocs` (или флаги рантайма в свежих версиях Go), о чем в модуле нет ни слова.

### 3. Мост OpenTelemetry Logs и `log/slog` (`otelslog`)
В главах 03 (Логирование) и 04 (Трейсинг) подробно описаны `log/slog` и OpenTelemetry Tracing, но полностью упущен связующий мост — официальный хендлер **`go.opentelemetry.io/contrib/bridges/otelslog`**.  
Он позволяет перенаправлять структурированные логи `slog` напрямую в OpenTelemetry Collector по протоколу OTLP вместе со спанами и метриками в едином бинарном потоке без промежуточных агентов Promtail/FluentBit.

### 4. Проброс контекста в асинхронных брокерах сообщений (Kafka / RabbitMQ)
В статье `04.04 Контекст propagation.md` механизм проброса показан исключительно для HTTP через `propagation.HeaderCarrier(req.Header)`.  
В реальных распределенных бэкендах на Go львиная доля взаимодействия идет асинхронно через Kafka или RabbitMQ. Студенту необходимо показать, как реализовывать интерфейс `propagation.TextMapCarrier` для заголовков сообщений (`kafka.Header` / `amqp.Table`), иначе трассировка неизбежно рвется при первой же асинхронной очереди.

---

## 📋 Рекомендации для последующих фаз верификации и редактуры

1. **Исправить некомпилируемые листинги:**
   - Заменить фиктивный `slog.HandlerFunc` в `05.01` на валидную структуру декоратора `slog.Handler`.
   - Заменить псевдокод `baggage.Set` / `baggage.Member` в `04.04` на официальный API `go.opentelemetry.io/otel/baggage`.
   - Исправить запуск сервера в `02.03`: связать роутер `mux` с `http.ListenAndServe(":8080", mux)`.
   - Добавить явное приведение типа к `prometheus.ExemplarObserver` в `05.01`.
   - Заменить `logger.Handler().Sync()` в `03.04` на корректное описание сброса буферов.
2. **Устранить опасные концептуальные мифы:**
   - Переписать параграф о проверке уровня в `03.01`: подчеркнуть, что аргументы функций в Go вычисляются всегда, и показать правильные паттерны ленивого логирования (`logger.Enabled`, `slog.LogValuer`).
   - Опровергнуть миф об «автоматическом определении cgroup limits» в Go 1.21+ в `05.05`, явно указав необходимость установки `GOMEMLIMIT` вручную или через библиотеку `automemlimit`.
   - Исправить физически невозможный порог алерта пауз GC (`rate > 10`) в `05.03` на корректные доли времени (`> 0.05`).
   - Исправить математический расчет Burn Rate 14.4 в `02.05` (2% за 1 час, а не 5%).
3. **Очистить вводные статьи от педагогических ловушек:**
   - В листингах `02.01` и `02.03` заменить прямой вызов `r.URL.Path` в качестве лейбла на нормализованный маршрут (или снабдить предупреждением со ссылкой на `02.04`).
   - В `04.01` предостеречь от передачи контекста HTTP-запроса в фоновую горутину, порекомендовав `context.WithoutCancel(ctx)`.
