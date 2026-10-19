# Fact-Check Report · Модуль 6 «Стандартная библиотека Go»

> **Роль:** основной фактчекер по первоисточникам, 2026-10-19.
> **Входные данные:** `sources/6. Стандартная библиотека Go/` (48 статей; после брифа модуль не менялся — `git diff --stat 5410653b HEAD` по каталогу пуст, номера строк брифа актуальны), бриф судьи `6-opus-judge.md` (`J-001…J-247`), отчёт слепых зон `6-opus-blind-spot.md` (`B-01…B-19` и 10 замечаний к брифу).
> **Тулчейн:** `go version go1.27.1 linux/amd64` (`/usr/local/go`, сборка 2026-08-28), ядро Linux 7.2.11, 24 CPU. Все примеры собраны и запущены во временных каталогах вне репозитория (`go.mod` с `go 1.27`, если не сказано иное; для проверок зависимости от версии языка — модуль с `go 1.21`).
> **Источники версий:** release notes Go 1.5, 1.12, 1.19, 1.20, 1.22, 1.23, 1.24, 1.25, 1.26, 1.27 (`go.dev/doc/go1.N`, прочитаны в этой сессии); локальные `api/go1.*.txt`, `doc/godebug.md`, `src/internal/godebugs/table.go`, исходники `src/` go1.27.1; `go doc` для документации пакетов; staticcheck.dev/docs/checks; письмо Роба Пайка об истории UTF-8. Чего не открывал — сказано в пункте и собрано в § 7.
> **Адресат:** редактор (`6-sonnet-editor.md`).

---

## 1. Сводка

| Статус | High (J-001…035) | Medium (J-036…166) | Low (J-167…247) | B | F | Всего |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| `VERIFIED` | 0 | 3 | 9 | 3 | 0 | **15** |
| `INCORRECT` | 32 | 81 | 36 | 12 | 2 | **163** |
| `PARTIALLY CORRECT` | 0 | 30 | 27 | 2 | 0 | **59** |
| `OUTDATED` | 2 | 12 | 5 | 2 | 3 | **24** |
| `CONTEXT-DEPENDENT` | 1 | 1 | 0 | 0 | 0 | **2** |
| `OPINION / NOT A FACT CLAIM` | 0 | 4 | 2 | 0 | 1 | **7** |
| `NOT CHECKED` | 0 | 0 | 2 | 0 | 0 | **2** (целиком; подпункты — § 7) |
| **Всего** | 35 | 131 | 81 | 19 | 6 | **272** |

**Как читать статусы.**
- Статус относится к **утверждению статьи**, а не к находке. `INCORRECT` у находки брифа значит «статья ошибается»; где ошибся бриф или отчёт слепых зон, это сказано в пункте.
- Для находок-пропусков `VERIFIED` значит «пропуск подтверждён, факт, который стоит добавить, проверен» (J-102, J-121, J-155, J-173, J-187, J-189, J-202, J-205, J-225, J-247, B-04, B-10, B-11). J-197 — подтверждённый дефект разметки; J-175 — утверждение статьи верно, добавить стоит только про `go vet`.
- `OUTDATED` — утверждение было верно для старых версий Go; в правке указана граница версии.

**Главное.**
1. **Почти все High подтвердились:** из 35 — 32 `INCORRECT`, 2 `OUTDATED` (J-021 модель `map`, J-028 `math/rand`), 1 `CONTEXT-DEPENDENT` (J-027 литерал `Transport`: HTTP/2 отключается только при `DialContext`/`TLSClientConfig`, а `Proxy` теряется всегда). Большинство опровергнуто одним запуском: `ParseBool("yes")`, `omitempty` у `[]string{}`, `Redacted()`, `Scanner.Bytes()`, `t.Fatal` + `defer`, `quick.Check`, `Output()` на 10 МБ, graceful shutdown (запрос оборван, `curl` — код 52).
2. **Go 1.27 меняет несколько выводов брифа** (бриф проверял на том же тулчейне, но не учёл release notes 1.27):
   - `Response.Body.Close()` сам дочитывает небольшой остаток — J-138 (`OUTDATED`), F-01;
   - `asynctimerchan` удалён: каналы таймеров небуферизованы всегда, даже при `go 1.21` в `go.mod` (проверено запуском) — J-094;
   - `encoding/json` по умолчанию работает поверх v2, `encoding/json/v2` доступен — J-123, B-12;
   - `URL.Clone` — именно 1.27 (бриф прав) — J-131;
   - `strconv` печатает и разбирает float новым алгоритмом (`uscale.go`), а не Ryū — J-068, F-02;
   - кодировщик `compress/flate` переписан: `gzip.Writer` аллоцирует ~1,08 МБ, а не ~740 КБ из брифа — J-154;
   - состояния P `_Psyscall` больше нет — J-159, F-04.
3. **Поправки к брифу:**
   - **J-243:** `bufio.Writer` **не** отключает `ReaderFrom`: у него свой `ReadFrom`, который делегирует нижележащему.
   - **J-114:** сортировка `[]*User` в замере оказалась **быстрее** `[]User` (7,4 мс против 13,7 мс). Совет статьи зависит от раскладки объектов в памяти, «значения часто быстрее» не подтверждено.
   - **J-130:** `url.JoinPath` экранирует сегменты (`a b` → `a%20b`); неверна только «защита от traversal».
   - **J-227:** ст. 24:38 о перемещении стеков верна; строже документации только правило про `uintptr`.
   - **J-099:** замер — `atomic` быстрее `Mutex` в 2,2× без конкуренции и в 3,5× на 8 ядрах.
4. **Поправка к отчёту слепых зон (B-08):** `"1.234,56"` после замены запятой даёт **ошибку** разбора, а не тихое `1.234`; тихо ломается `"1,234"`.
5. **Атрибуция (J-166):** проверяемые эпиграфы ложны. История UTF-8 — рассказ Пайка (Томпсон придумал формат «на салфетке в закусочной»). «Делитесь памятью через общение» — Go-пословица Пайка. «Одна вещь хорошо» — Макилрой. Подлинная цитата Кернигана — только в ст. 2 (и первая фраза ст. 16).

---

## 2. High

### J-001 — INCORRECT
- **Где / цитата:** ст. 1:125 — «Начиная с определенного момента, `strings.Builder` паникует при попытке изменить уже записанные данные … за счет отсутствия аллокаций при получении финальной строки»; ст. 8:133 — «`strings.Builder` блокирует запись после `.String()`».
- **Вердикт:** запрета на запись после `String()` нет, «паники при изменении данных» нет. Паника бывает только при записи в **копию** уже использованного `Builder`. Zero-copy `String()` обеспечивает `unsafe.String`, а не паника. Ст. 7:109 описывает механизм верно, так что ст. 1 и 8 противоречат ст. 7.
- **Доказательство:** go1.27.1 `src/strings/builder.go`: `String()` = `unsafe.String(unsafe.SliceData(b.buf), len(b.buf))`; `copyCheck()` паникует `strings: illegal use of non-zero Builder copied by value` только при `b.addr != b`. Запуск: `WriteString("abc"); s1 := String(); WriteString("def")` → `abc abcdef`, паники нет; `cp := sb; cp.WriteString("x")` → паника `illegal use of non-zero Builder copied by value`.
- **Предлагаемая правка:** ст. 1:125 — «…`strings.Builder` предназначен только для записи. Метод `String()` не копирует данные: строка ссылается на внутренний буфер (`unsafe.String`). Это безопасно, потому что Builder никогда не меняет уже записанные байты, а только дописывает новые. Копировать использованный Builder по значению нельзя: запись в копию вызовет панику». Ст. 8:133 — «`strings.Builder` после `.String()` можно продолжать заполнять: возвращённая строка не изменится».

### J-002 — INCORRECT
- **Где / цитата:** ст. 2:51 — «вывод `%v` для хэш-таблицы (`map`) не гарантирует порядок ключей … Начиная с последних версий Go, `%#v` сортирует ключи мапы».
- **Вердикт:** с Go 1.12 `fmt` печатает map с ключами в отсортированном порядке для **всех** вербов. Вывод детерминирован. Выделение `%#v` и «последних версий» неверно.
- **Доказательство:** Go 1.12 release notes (`fmt`): «Maps are now printed in key-sorted order to ease testing». Запуск на go1.27.1: `%v` для `{"e","b","a","d","c"}` → `map[a:1 b:2 c:3 d:4 e:5]`; `%#v` → `map[string]int{"a":1, "b":2, "e":5}`.
- **Предлагаемая правка:** «С Go 1.12 `fmt` печатает map с ключами, отсортированными по значению, при любом верб (`%v`, `%+v`, `%#v`), поэтому вывод детерминирован и удобен в тестах. Итерация `for range` по map при этом остаётся случайной».

### J-003 — INCORRECT
- **Где / цитата:** ст. 3:130 — «Статический анализатор `staticcheck` (правило `ST1005`) умеет автоматически находить эту проблему».
- **Вердикт:** `ST1005` — «Incorrectly formatted error string» (заглавная буква, точка в конце). К typed nil не относится. Близкая проверка — `SA4023` («impossible comparison of interface value with untyped nil»): она ловит **сравнение** `err != nil`, которое всегда истинно, потому что функция возвращает конкретный тип в позиции интерфейса. Ловит не во всех случаях. Анализатора `go vet`, который ловил бы саму конструкцию `return p` при `p *MyErr == nil`, нет: в списке анализаторов vet go1.27.1 такого нет.
- **Доказательство:** staticcheck.dev/docs/checks (открыто в этой сессии): ST1005 — «Incorrectly formatted error string», SA4023 — «Impossible comparison of interface value with untyped nil», её пояснение описывает именно typed nil pointer; отдельной проверки для `return` typed nil нет. `go tool vet help` в go1.27.1: `appends asmdecl assign atomic bools buildtag cgocall composites copylocks defers directive errorsas framepointer hostport httpresponse ifaceassert loopclosure lostcancel nilfunc printf shift sigchanyzer slog stdmethods stdversion stringintconv structtag testinggoroutine tests timeformat unmarshal unreachable unsafeptr unusedresult waitgroup` — проверки typed nil нет.
- **Предлагаемая правка:** «Надёжно находят эту ошибку не компилятор и не `go vet`. `staticcheck` (проверка `SA4023`) замечает сравнение с `nil`, которое из-за этой ловушки всегда истинно. Главная защита — правило: функция, возвращающая `error`, возвращает `nil` литералом, а не переменную конкретного типа».

### J-004 — INCORRECT
- **Где / цитата:** ст. 6:182 — «Данные внутри буфера могут остаться. Вызовите `Flush()`, чтобы попытаться сбросить их и получить точную ошибку syscall»; ст. 6:139 — «можно попытаться Flush».
- **Вердикт:** ошибка `bufio.Writer` «липкая». После первой ошибки все `Write*` и `Flush` сразу возвращают её, не обращаясь к нижележащему writer. Повторный `Flush` ничего не досбросит. Writer снова пригоден только после `Reset`.
- **Доказательство:** doc `bufio.Writer` (go1.27.1): «If an error occurs writing to a Writer, no more data will be accepted and all subsequent writes, and Writer.Flush, will return the error». `src/bufio/bufio.go`, `Flush`: `if b.err != nil { return b.err }`. Запуск: writer-заглушка всегда возвращает ошибку; `WriteString`, `Flush`, `Flush` → три раза `disk full`, нижележащий `Write` вызван **один** раз, в буфере осталось 16 байт.
- **Предлагаемая правка:** таблица 182 — «После ошибки `bufio.Writer` запоминает её: все последующие `Write` и `Flush` возвращают ту же ошибку и ничего не пишут. Несброшенные данные в буфере потеряны для этого writer. Обработайте ошибку (повтор операции целиком, другой приёмник) и при повторном использовании вызовите `Reset(w)`». Комментарий 139 — «вернуть ошибку: повторный Flush её не исправит».

### J-005 — INCORRECT
- **Где / цитата:** ст. 6:170 — «`scanner.Text()` и `scanner.Bytes()` возвращают **ссылку на внутренний буфер сканера** … или используйте `strings.Clone()`/`[]byte(strings.Clone())`»; итог 209 — «…возвращает ссылку на внутренний буфер».
- **Вердикт:** `Text()` возвращает копию (`string(s.token)`). Буфер алиасит только `Bytes()`. `strings.Clone` принимает `string`, к `[]byte` неприменим; для среза — `bytes.Clone` (Go 1.20) или `append([]byte(nil), b...)`. Комментарий 162 про `Bytes()` верен.
- **Доказательство:** `src/bufio/scan.go:108–115`: `Bytes()` → `return s.token`, `Text()` → `return string(s.token)`. Запуск на входе из двух строк по 5000 байт: строки из `Text()` сохранились (`aaa`, `bbb`), а первый срез из `Bytes()` после второго `Scan()` показывает `bbb` — данные перезаписаны.
- **Предлагаемая правка:** «`scanner.Bytes()` возвращает срез внутреннего буфера, который следующий `Scan()` перезапишет. Чтобы сохранить данные, копируйте: `bytes.Clone(scanner.Bytes())`. `scanner.Text()` уже возвращает новую строку-копию (это аллокация на каждую строку)». Итог п. 3 — «…`Bytes()` возвращает ссылку на внутренний буфер, `Text()` — копию».

### J-006 — INCORRECT
- **Где / цитата:** ст. 7:69 — «выход слайса за пределы области видимости оставит строку с висячим указателем (dangling pointer), что вызовет панику или чтение мусора. Используйте это только в высокоспециализированных случаях (например, ключи в `map[string]struct{}` при поиске)».
- **Вердикт:** (1) висячего указателя при GC нет: строка, указывающая в массив среза, удерживает массив живым. Реальная опасность — изменение байтов после превращения в строку, в том числе через переиспользование буфера из пула. (2) Для `m[string(b)]` и `string(b) == "lit"` компилятор сам не копирует, `unsafe` здесь не нужен.
- **Доказательство:** doc `unsafe.String`: «Since Go strings are immutable, the bytes passed to String must not be modified as long as the returned string value exists». Запуск, `testing.AllocsPerRun`: `m[string(b)]` → 0 аллокаций, `string(b) == "hello"` → 0.
- **Предлагаемая правка:** «…Изменение байтов в слайсе после конвертации повредит строку: нарушится контракт неизменяемости, а map, где эта строка стала ключом, может перестать её находить. Особенно опасен буфер из `sync.Pool`, который потом перезапишут. Висячего указателя нет: строка удерживает массив от сборки мусора. Для поиска в map (`m[string(b)]`) и сравнения (`string(b) == "x"`) `unsafe` не нужен: компилятор не копирует байты в этих выражениях».

### J-007 — INCORRECT
- **Где / цитата:** ст. 8:178–191 — `func StructToBytes(s interface{}) []byte { size := unsafe.Sizeof(s); ptr := unsafe.Pointer(&s); return unsafe.Slice((*byte)(ptr), size) }`; п. 3 Gotcha — «GC может не распознать эти указатели … что приведет к преждевременному освобождению живой памяти».
- **Вердикт:** функция возвращает 16 байт заголовка интерфейса (указатель на тип + указатель на данные) из локальной копии, а не байты структуры. Довод про GC тоже неверен: `unsafe.Slice` по указателю на объект удерживает объект живым. Опасность сырых байт структуры с указателями в другом: адреса бессмысленны вне процесса, а запись в такие байты ломает указатели.
- **Доказательство:** запуск: структура `{A int64; B int32; C [20]byte}` (`Sizeof` = 32) → `len(StructToBytes(v)) = 16`, байтового шаблона поля `A` (`0x11…`) в результате нет.
- **Предлагаемая правка:**
  ```go
  // Байтовое представление значения T (без копирования; layout зависит от платформы).
  func StructToBytes[T any](p *T) []byte {
      return unsafe.Slice((*byte)(unsafe.Pointer(p)), unsafe.Sizeof(*p))
  }
  ```
  П. 3 Gotcha — «Если структура содержит указатели, байты содержат адреса, которые бессмысленны вне текущего процесса, а запись в такой срез портит указатели и ломает сборщик мусора. Используйте только для структур без указателей».

### J-008 — INCORRECT
- **Где / цитата:** ст. 9:114 — заголовок «Булевы значения и кватернионы»; 116 — «принимает … `"1"`/`"0"`, `"t"`/`"f"`, `"T"`/`"F"`, `"yes"`/`"no"` и т.д.».
- **Вердикт:** принимаются ровно `1 t T TRUE true True` и `0 f F FALSE false False`. `"yes"`, `"no"`, `"on"`, `"tRuE"` — `ErrSyntax`. Кватернионов в `strconv` нет; есть `ParseComplex`/`FormatComplex` для комплексных чисел (Go 1.15).
- **Доказательство:** go1.27.1 `src/internal/strconv/atob.go:10–18` (`case "1", "t", "T", "true", "TRUE", "True"` / `case "0", "f", "F", "false", "FALSE", "False"`). Запуск: `yes`, `no`, `on`, `tRuE` → `invalid syntax`; `TRUE`, `t`, `True`, `1` → `true`. `api/go1.15.txt` — `ParseComplex`, `FormatComplex` (по брифу, отдельно не открывал).
- **Предлагаемая правка:** заголовок «4. Булевы значения». Текст — «`strconv.ParseBool` принимает ровно `"1"`, `"t"`, `"T"`, `"TRUE"`, `"true"`, `"True"` и `"0"`, `"f"`, `"F"`, `"FALSE"`, `"false"`, `"False"`. Всё остальное, включая `"yes"`, `"no"`, `"on"`, — ошибка `strconv.ErrSyntax`. Если конфигурация допускает `yes`/`no`, разбирайте их сами».

### J-009 — INCORRECT
- **Где / цитата:** ст. 11:108 — «запись (`Setenv`, `Unsetenv`) **не является потокобезопасной** на уровне всего процесса. Если две горутины одновременно вызовут `os.Setenv`, результат непредсказуем … data race … внутри libc»; итог 214.
- **Вердикт:** в чистом Go `Setenv/Getenv/Unsetenv` защищены `sync.RWMutex` и безопасны для горутин. Проблема реальна только с cgo: рантайм дублирует запись в `setenv(3)` libc, а C-код, читающий `getenv` в других потоках, с Go не синхронизирован. Совет «менять окружение только при старте» разумен, обоснование неверно.
- **Доказательство:** go1.27.1 `src/syscall/env_unix.go:17–18` (`// envLock guards env and envs.` / `envLock sync.RWMutex`), строки 55–56 и 72 — `Lock`/`RLock` в `Setenv`/`Getenv`; `src/runtime/env_posix.go:67–73` — `setenv_c` вызывает C `setenv` «if cgo is loaded».
- **Предлагаемая правка:** «`os.Setenv`, `Getenv` и `Unsetenv` защищены внутренней блокировкой, и одновременные вызовы из горутин безопасны. Но окружение — глобальное состояние процесса. Если программа использует cgo, Go дублирует запись в окружение libc, а C-код в других потоках читает его без синхронизации — это гонка внутри libc. Поэтому меняйте окружение только при старте, до запуска горутин и C-библиотек». Итог п. 3 — так же.

### J-010 — INCORRECT
- **Где / цитата:** ст. 11:121–148 — горутина с `srv.Shutdown(ctx)`; в `main` после `ListenAndServe` сразу `log.Println("Server exited properly")`.
- **Вердикт:** `ListenAndServe` возвращает `ErrServerClosed` сразу после начала `Shutdown`, и `main` завершается, не дождавшись активных запросов. Пример обрывает именно те запросы, ради которых нужен graceful shutdown. `log.Fatal` в горутине вызывает `os.Exit` и обходит `defer`.
- **Доказательство:** doc `http.Server.Shutdown`: «When Shutdown is called, Serve, ListenAndServe, and ListenAndServeTLS immediately return ErrServerClosed. Make sure the program doesn't exit and waits instead for Shutdown to return». Запуск примера статьи (обработчик спит 2 с, SIGTERM через 0,5 с после начала запроса): сервер напечатал `Server exited properly` в ту же секунду, `curl` завершился с кодом 52 (Empty reply from server) — запрос оборван.
- **Предлагаемая правка:**
  ```go
  func main() {
      srv := &http.Server{Addr: ":8080"}
      ctx, stop := signal.NotifyContext(context.Background(), syscall.SIGINT, syscall.SIGTERM)
      defer stop()

      done := make(chan error, 1)
      go func() {
          <-ctx.Done()
          log.Println("Shutting down server...")
          shCtx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
          defer cancel()
          done <- srv.Shutdown(shCtx)
      }()

      if err := srv.ListenAndServe(); err != nil && !errors.Is(err, http.ErrServerClosed) {
          log.Fatal("ListenAndServe error:", err)
      }
      if err := <-done; err != nil { // ждём, пока Shutdown дождётся активных запросов
          log.Println("forced shutdown:", err)
      }
      log.Println("Server exited properly")
  }
  ```

### J-011 — INCORRECT
- **Где / цитата:** ст. 11:47 — «Даже если вы работаете с сетевым сокетом … внутри это файловый дескриптор» (о `*os.File`); 59 — `stdoutOrErr bool // Оптимизация для stdout/stderr`; 62 — «Поле `pfd` … позволяющий Go реализовывать асинхронный I/O без блокировки OS-тредов, даже при работе с обычными файлами»; 203 — «асинхронная реализация через G-M-P». Тот же тезис — ст. 4:249 и 4:277 (отмечено в B-отчёте).
- **Вердикт:** обычные файлы в netpoller не попадают: на Linux epoll возвращает `EPERM` для регулярного файла, `pfd.Init` молча откатывается в блокирующий режим. Горутина занимает M в системном вызове, `sysmon` отбирает у него P, под нагрузкой растёт число потоков. Netpoller обслуживает сокеты, пайпы, FIFO, терминалы. Сетевые соединения — `net.netFD` со своим `poll.FD`, а не `os.File`. `stdoutOrErr` нужен для обработки `EPIPE` на fd 1/2 (SIGPIPE), это не оптимизация.
- **Доказательство:** go1.27.1 `src/os/file_unix.go:209–219`: «An error here indicates a failure to register with the netpoll system. That can happen for a file descriptor that is not supported by epoll/kqueue; for example, disk files on Linux systems»; строка 235 — `if e == syscall.EPIPE && file.stdoutOrErr`; строки 165–182 — на BSD/macOS регулярные файлы и каталоги исключаются из kqueue явно.
- **Предлагаемая правка:** 62 — «Поле `pfd` связывает дескриптор с netpoller рантайма, если ОС это поддерживает: так работают пайпы, FIFO и терминалы. Обычные файлы на диске epoll не поддерживает, и для них чтение и запись — блокирующие системные вызовы: горутина занимает поток ОС, а планировщик отдаёт P другому потоку». 59 — «`stdoutOrErr` — признак fd 1/2: запись в закрытый stdout/stderr (EPIPE) завершает процесс, как в C». 47 — «stdin/stdout и пайпы тоже представлены `*os.File`; сетевые соединения — отдельный тип `net.Conn` поверх того же `internal/poll.FD`». 203 — «Синхронный API; сокеты и пайпы — через netpoller, дисковые файлы — блокирующими вызовами в отдельном потоке». Ст. 4:249, 277 — согласовать.

### J-012 — INCORRECT
- **Где / цитата:** ст. 12:104–124 — `safeFilePath` с `strings.HasPrefix(absPath, absBase)`; 128 — пояснение о `filepath.Abs`; 61 — «`path.Clean` … полезно для безопасности (защита от Directory Traversal)».
- **Вердикт:** проверка пропускает соседний каталог с тем же префиксом и любой симлинк внутри базы. Пример подан как защитный.
- **Доказательство:** запуск функции из статьи: `safeFilePath(base="/tmp/x/files", "../files-secret/x")` → `/tmp/x/files-secret/x`, ошибки нет. Симлинк `files/link → /tmp/x`: `safeFilePath(base, "link/outside.txt")` → путь прошёл проверку, `os.ReadFile` прочитал файл вне базы. `filepath.IsLocal("../files-secret/x")` → `false`. `os.OpenRoot(base)` + чтение `link/outside.txt` → `path escapes from parent`. Go 1.20 release notes — `filepath.IsLocal`; Go 1.24 release notes — `os.Root` («do not permit paths that refer to locations outside the directory, including ones that follow symbolic links out of the directory»).
- **Предлагаемая правка:**
  ```go
  // Go 1.24+: os.Root не выпускает за пределы каталога, в том числе по симлинкам.
  root, err := os.OpenRoot(baseDir)
  if err != nil { return err }
  defer root.Close()
  f, err := root.Open(userInput) // ошибка, если путь выходит наружу

  // До Go 1.24 — лексическая проверка (симлинки не учитывает):
  if !filepath.IsLocal(userInput) {
      return "", errors.New("access denied: path traversal detected")
  }
  full := filepath.Join(baseDir, userInput)
  ```
  Пояснение 128 — «Главная дыра ручной проверки — `HasPrefix` без разделителя: `/srv/files-secret` начинается с `/srv/files`. Вторая — симлинки: `Clean` и `Abs` работают только со строкой». Ст. 12:61 — «`Clean` лексический и от выхода по симлинкам не защищает».

### J-013 — INCORRECT
- **Где / цитата:** ст. 13:170 — «Запрет на символы `..` и абсолютные пути … гарантирует защиту от path traversal на уровне самого интерфейса»; 123 — «предотвращение выхода за пределы sandbox».
- **Вердикт:** `fs.ValidPath` — проверка строки. `os.DirFS` следует симлинкам наружу. Изоляцию даёт `os.Root` (Go 1.24) и `(*os.Root).FS()`.
- **Доказательство:** запуск: `os.DirFS(base)` + `fs.ReadFile(d, "link/outside.txt")` (симлинк наружу) → прочитано `OUTSIDE`; `fs.ReadFile(d, "../outside.txt")` → `invalid argument`; `r.FS()` из `os.OpenRoot(base)` → `path escapes from parent`. doc `os.DirFS` (go1.27.1): «if /prefix/file is a symbolic link pointing outside the /prefix tree, then using DirFS does not stop the access any more than using os.Open does … Use Root.FS to obtain a fs.FS that prevents escapes from the tree via symbolic links».
- **Предлагаемая правка:** итог п. 5 — «`fs.FS` запрещает в путях `..` и ведущий `/`, но это проверка строки, не песочница: `os.DirFS` пройдёт по симлинку за пределы каталога. Для изоляции используйте `os.OpenRoot(dir)` и `root.FS()` (Go 1.24+)». 123 — так же.

### J-014 — INCORRECT
- **Где / цитата:** ст. 14:85 — «При использовании `embed.FS.Open()` или вызова `staticFS.ReadFile()` рантайм Go не выделяет память в куче … Он возвращает срез `[]byte`, заголовок которого указывает напрямую на физические страницы секции `.rodata`»; 123; итог 144.
- **Вердикт:** `ReadFile` возвращает копию размером с файл, чтобы вызывающий мог её менять. `Open` + `Read` копирует в буфер вызывающего. Без копирования работает только встраивание в переменную `string` (и чтение через `string`).
- **Доказательство:** go1.27.1 `src/embed/embed.go:322–332`: `return []byte(ofile.f.data), nil`. Запуск: `sfs.ReadFile` → 2 аллокации на вызов; изменение байта результата не меняет данные при повторном `ReadFile`.
- **Предлагаемая правка:** «`embed.FS.ReadFile` возвращает **копию** содержимого: это аллокация размером с файл, зато срез можно менять. Чтение через `Open` и `Read` копирует данные в ваш буфер. Без копирования данные доступны только через переменную `//go:embed` типа `string`: её байты лежат в read-only секции бинарника». Итог п. 2 и ответ 123 — согласовать.

### J-015 — INCORRECT
- **Где / цитата:** ст. 15:127 — `verbose := flag.Bool("v", false, …)`; 154 — `*flag.Lookup("v").Value.(*bool)`.
- **Вердикт:** пример не компилируется. Две ошибки: неиспользуемая `verbose` и невозможное утверждение типа (`*bool` не реализует `flag.Value`). Alt считал, что будет паника в рантайме, — до рантайма дело не доходит.
- **Доказательство:** `go build` примера на go1.27.1: `declared and not used: verbose`; `impossible type assertion: flag.Lookup("v").Value.(*bool)` / `*bool does not implement flag.Value (missing method Set)`.
- **Предлагаемая правка:** передать значение явно: `serveCmd(flag.Args()[1:], *verbose)` и `func serveCmd(args []string, verbose bool)`. Если нужен поиск по имени — `flag.Lookup("v").Value.(flag.Getter).Get().(bool)`.

### J-016 — INCORRECT
- **Где / цитата:** ст. 16:101–114 — «Интерфейс `slog.Valuer` позволяет отложить тяжелое вычисление…»; `return slog.Int64("alloc_bytes", int64(m.Alloc))`; комментарий «ReadMemStats вызовется только если уровень DEBUG включен» при вызове `logger.Info(...)`. То же имя `slog.Valuer` — во врезке 185.
- **Вердикт:** интерфейс называется `slog.LogValuer`, `LogValue()` возвращает `slog.Value`, а `slog.Int64(...)` — `slog.Attr`: код не компилируется. Комментарий противоречит вызову `Info`: при уровне Info значение вычислится. `runtime.ReadMemStats` останавливает мир — неудачный пример для частого логирования.
- **Доказательство:** `go doc log/slog Valuer` → `no symbol Valuer in package log/slog`; `go doc log/slog LogValuer` → `type LogValuer interface { LogValue() Value }`. `go build`: `cannot use slog.Int64("alloc_bytes", int64(m.Alloc)) (value of struct type slog.Attr) as slog.Value value in return statement`.
- **Предлагаемая правка:**
  ```go
  type memoryStat struct{}

  func (memoryStat) LogValue() slog.Value {
      var m runtime.MemStats
      runtime.ReadMemStats(&m) // останавливает мир: не для горячего пути
      return slog.Int64Value(int64(m.Alloc))
  }

  logger.Debug("memory check", "mem", memoryStat{})
  // LogValue вызовется, только если включён уровень Debug
  ```
  Заголовок и текст — `slog.LogValuer`; врезка 185 — так же.

### J-017 — INCORRECT
- **Где / цитата:** ст. 19:27 — «вызывает рантайм-функцию `runtime_SemacquireMutex`. Это транслируется в системный вызов ядра `futex(SYS_futex, FUTEX_WAIT)` на Linux. Горутина переходит в состояние сна `Gwaiting`, а тред … (M) немедленно освобождается»; «помечает себя как `Woken`»; итог 194; ст. 48:63, 112.
- **Вердикт:** `runtime_SemacquireMutex` паркует **горутину** в очереди семафора рантайма (`semacquire1` → `goparkunlock`) без системного вызова. M сразу берёт другую горутину — что и сказано во второй половине фразы, так что фраза противоречит сама себе. `futex` рантайм использует, когда **потоку** нечего делать (`notesleep`, внутренние `lock`). Флаг `mutexWoken` ставит спиннящий претендент (чтобы `Unlock` не будил лишнего); паркующаяся горутина его не ставит, а проснувшаяся снимает.
- **Доказательство:** go1.27.1 `src/internal/sync/mutex.go:104–109` (спиннинг + `CompareAndSwapInt32(&m.state, old, old|mutexWoken)`), 135–138 (`new &^= mutexWoken` у проснувшегося), 149 (`runtime_SemacquireMutex(&m.sema, queueLifo, 2)`); `src/runtime/sema.go`, `semacquire1` → `goparkunlock(&root.lock, …)`; `src/runtime/lock_futex.go:47, 70, 89, 146` — `futexsleep` в `notesleep`/`lock2`.
- **Предлагаемая правка:** ст. 19:27 — «Если спиннинг не помог, мьютекс увеличивает счётчик ожидающих и вызывает `runtime_SemacquireMutex`. Рантайм ставит горутину в очередь семафора и паркует её (`gopark`): это переключение в пространстве пользователя, без системного вызова. Поток M сразу берёт следующую готовую горутину. Системный вызов `futex` рантайм делает, только когда самому потоку нечего исполнять». Итог п. 1 и ст. 48:63, 112 — «…паркует горутину в рантайме», без `futex`.

### J-018 — INCORRECT
- **Где / цитата:** ст. 19:167 — «Вызывайте `defer` непосредственно перед `mu.Lock()`, но только если вся функция является критической секцией».
- **Вердикт:** идиома обратная: `mu.Lock(); defer mu.Unlock()`. Если между `defer mu.Unlock()` и `Lock` возможен выход или паника, будет `Unlock` незахваченного мьютекса — фатальная ошибка, `recover` её не перехватывает.
- **Доказательство:** doc `sync.Mutex.Unlock` (go1.27.1): «It is a run-time error if m is not locked on entry to Unlock»; `src/internal/sync/mutex.go` — `fatal("sync: unlock of unlocked mutex")` (по брифу, строку не выводил).
- **Предлагаемая правка:** «Вызывайте `defer mu.Unlock()` сразу **после** `mu.Lock()`, если критическая секция — вся функция. Если секция короче функции, вынесите её в отдельную функцию или разблокируйте явно».

### J-019 — INCORRECT
- **Где / цитата:** ст. 21:136 — «В Go 1.18+ появилась обертка `pool.New()` с типизацией … Дженерики в самом `sync` пакете не планируются к внедрению ради сохранения ABI стабильности рантайма».
- **Вердикт:** типизированной обёртки над `sync.Pool` в stdlib нет ни в 1.18, ни в 1.27. Дженерики в `sync` и `sync/atomic` уже есть. Мотив «ABI стабильности» не подтверждается ничем.
- **Доказательство:** go1.27.1 `src/sync/pool.go:52` — `type Pool struct`, `Get() any`; `api/go1.*.txt` — `Pool[` нигде не встречается; `api/go1.21.txt:404–406` — `OnceFunc`, `OnceValue[$0]`, `OnceValues[$0, $1]`; `api/go1.19.txt:287` — `sync/atomic, type Pointer[$0 interface{}] struct`.
- **Предлагаемая правка:** «Пул появился до дженериков, и менять сигнатуру `Get() any` нельзя из-за обещания совместимости Go 1. Типизированной версии пула в stdlib нет, поэтому пишут тонкую обёртку (`type Pool[T any] struct{ p sync.Pool }`) или приводят тип при `Get`. Дженерики в пакеты синхронизации при этом приходят: `atomic.Pointer[T]` (Go 1.19), `sync.OnceValue[T]` (Go 1.21)».

### J-020 — INCORRECT
- **Где / цитата:** ст. 22:144 — «`runtime.NumCPU()` обращается к API ядра (`sched_getaffinity` или cgroups) … В Kubernetes `NumCPU()` корректно учитывает `requests/limits`»; 38 — «файлы `cgroups` напрямую рантаймом не парсятся»; 40 — «исторически требовалось настраивать `GOMAXPROCS` вручную … `uber-go/automaxprocs`».
- **Вердикт:** `NumCPU` учитывает только маску affinity (`cpuset`), не квоту CFS и не requests. Ответ собеседования противоречит строке 38 той же статьи. С Go 1.25 `GOMAXPROCS` по умолчанию на Linux учитывает лимит CPU cgroup («CPU limit» в Kubernetes, но не «requests») и периодически обновляется. Строка 38 «cgroups не парсятся» устарела для `GOMAXPROCS`; для `NumCPU` она по-прежнему верна.
- **Доказательство:** go1.27.1 `src/runtime/os_linux.go:111` — `sched_getaffinity` в `getproccount`; doc `runtime.NumCPU`: «The set of available CPUs is checked by querying the operating system at process startup». Go 1.25 release notes: «On Linux, the runtime considers the CPU bandwidth limit of the cgroup … The Go runtime does not consider the "CPU requests" option … the runtime periodically updates GOMAXPROCS … disabled if GOMAXPROCS is set manually … containermaxprocs=0 and updatemaxprocs=0». `src/internal/godebugs/table.go:30, 71` — `containermaxprocs`, `updatemaxprocs` (`Changed: 25`).
- **Предлагаемая правка:** 144 — «`runtime.NumCPU()` возвращает число CPU из маски affinity процесса (`sched_getaffinity`), то есть учитывает `cpuset`, но не квоту CPU (`cpu.max`) и тем более не requests. С Go 1.25 на Linux квоту учитывает `GOMAXPROCS` по умолчанию: он берёт меньшее из `NumCPU` и лимита cgroup и обновляется при его изменении; `NumCPU` при этом не меняется». 38 — «…и `NumCPU` их не читает. Но с Go 1.25 рантайм сам читает лимит CPU cgroup для `GOMAXPROCS`». 40 — «До Go 1.25 под квотой требовалось настраивать `GOMAXPROCS` вручную или через `automaxprocs`; с Go 1.25 (при `GOMAXPROCS`, не заданном вручную) это делается автоматически».

### J-021 — OUTDATED
- **Где / цитата:** ст. 26:8 (Swiss Tables с Go 1.24), далее «Under the hood»: `hmap` (14–25), `bmap`, overflow, `tophash` (28–30), рост и эвакуация; 75 — `clear` «без выделения нового заголовка `hmap` или массива бакетов»; 114 — «Бакеты `bmap` спроектированы так, чтобы занимать ровно одну кэш-линию (64 байта)»; таблица 150 — «`map` (buckets + overflow)»; итог 154, 157.
- **Вердикт:** вся модель `hmap/bmap` относится к Go ≤ 1.23. С Go 1.24 — Swiss Tables, а в go1.27.1 старой реализации нет совсем (флага `noswissmap` нет в `internal/goexperiment`). Утверждение «64 байта» неверно и для старой модели: бакет `map[int]int` = 8 (`tophash`) + 64 (ключи) + 64 (значения) + 8 (overflow) = 144 байта; раздельное хранение ключей и значений исключало паддинг, но не делало бакет равным кэш-линии.
- **Доказательство:** Go 1.24 release notes: «a new builtin `map` implementation based on Swiss Tables … may be disabled by setting `GOEXPERIMENT=noswissmap`»; go1.27.1: `grep swiss src/internal/goexperiment/flags.go` — пусто, `src/runtime/map.go` отсутствует; `src/internal/runtime/maps/map.go:220–221` — `seed uintptr` «computed as a unique random number per map»; `table.go:20` — `maxTableCapacity = 1024`. Размер бакета Go 1.23 посчитан по раскладке `bucketCnt = 8` (исходник 1.23 в сессии не открывал).
- **Предлагаемая правка:** раздел «Under the hood» озаглавить «Классическая реализация (Go 1.0–1.23)» и добавить короткий раздел «Go 1.24+: Swiss Tables»: группы по 8 слотов с 8-байтным контрольным словом (7 бит хэша на слот), таблицы до 1024 слотов, каталог таблиц, рост расщеплением одной таблицы, tombstones при удалении; seed на каждую map. Строку 114 — «В Go ≤ 1.23 бакет хранил 8 ключей подряд, затем 8 значений, чтобы избежать паддинга; размер бакета зависит от типов (для `map[int]int` — 144 байта) и с кэш-линией не совпадает». Итог п. 1 и таблицу 150 — «с Go 1.24 — Swiss Tables». Согласовать с модулем 5 (бриф 5, J-01).

### J-022 — INCORRECT
- **Где / цитата:** ст. 29:89 — «для указателей и слайсов `nil`. Пустой слайс `[]string{}` **не будет** опущен, только `nil`».
- **Вердикт:** ровно наоборот: `omitempty` опускает и пустой, и nil-слайс (и пустую map, и пустую строку).
- **Доказательство:** запуск: `json.Marshal(S{L: []string{}, M: map[string]int{}})` с тегами `omitempty` → `{}`. doc `encoding/json.Marshal`: «The "omitempty" option specifies that the field should be omitted from the encoding if the field has an empty value, defined as false, 0, a nil pointer, a nil interface value, and any array, slice, map, or string of length zero».
- **Предлагаемая правка:** «`omitempty` опускает `false`, `0`, `""`, nil-указатель, nil-интерфейс и любой массив, слайс или map **нулевой длины** — и `nil`, и пустой `[]string{}`. Пустая структура не опускается; для неё и для `time.Time` есть `omitzero` (Go 1.24)».

### J-023 — INCORRECT
- **Где / цитата:** ст. 30:46–47 — «**Пространства имен ломают маппинг.** … стандартный `xml.Unmarshal` не сопоставит поле с тегом `"item"` … Игнорирование этого правила приводит к нулевым структурам без ошибок».
- **Вердикт:** тег без пространства имён сопоставляется по локальному имени **при любом** namespace элемента. Ловушка обратная: namespace молча игнорируется, и одноимённые элементы из разных пространств попадают в одно поле.
- **Доказательство:** запуск: `<root xmlns:ns="http://api.example.com"><ns:item><name>x</name></ns:item><item xmlns="urn:other"><name>y</name></item></root>` в ``Items []Item `xml:"item"` `` → `{Items:[{Name:x} {Name:y}]}`, ошибки нет — оба элемента из разных пространств попали в одно поле.
- **Предлагаемая правка:** «**Пространства имён по умолчанию игнорируются.** Тег `xml:"item"` совпадёт с `<item>` из любого пространства имён — и с `<ns:item>`, и с `<item xmlns="urn:other">`. Если в документе встречаются одноимённые элементы из разных пространств, укажите namespace в теге: ``xml:"http://api.example.com item"`` — тогда поле примет только элементы этого пространства».

### J-024 — INCORRECT
- **Где / цитата:** ст. 30:89 — «поддерживает указатели, циклические ссылки и интерфейсы»; 141 — «Удаление поля в структуре ломает десериализацию старых данных … Используйте `omitempty`»; 129, 165 — «Очень низкий CPU overhead», «лучший выбор … кэширования и очередей».
- **Вердикт:** (1) рекурсивные **типы** gob поддерживает, рекурсивные **значения** (циклы) — нет: процесс падает с переполнением стека. (2) Удаление поля gob переносит: лишние поля в потоке игнорируются. Ломает смена типа поля. (3) Тегов и `omitempty` у gob нет. (4) «Очень низкий overhead» — без измерений; описание типов передаётся один раз на `Encoder`, поэтому для одиночных сообщений (запись кэша, сообщение очереди) накладные расходы велики.
- **Доказательство:** doc `encoding/gob` (go1.27.1): «Recursive types work fine, but recursive values (data with cycles) are problematic». Запуск: `Encode(n)` при `n.Next = n` → `fatal error: stack overflow` (с `debug.SetMaxStack(64<<20)`), ошибкой не возвращается. Поток `V1{A, B, C}` → декодирование в `V2{A, C}` → `{A:1 C:3.5}`, ошибки нет; в `V3{A string}` → `gob: wrong type (string) for received field V1.A`.
- **Предлагаемая правка:** 89 — «…поддерживает указатели, рекурсивные типы и интерфейсы (после `gob.Register`). Значения с циклами gob не поддерживает: кодирование такого графа уходит в бесконечную рекурсию и роняет процесс». 141 — «Смена типа поля ломает декодирование старых данных. Добавлять и удалять поля можно: лишние поля пропускаются, отсутствующие остаются нулевыми. Тегов (`omitempty`) у gob нет». 129/165 — «gob эффективен на длинном потоке одного `Encoder`: описание типов передаётся один раз. Для одиночных сообщений (кэш, очередь) это описание повторяется в каждом сообщении — сравните с Protobuf по размеру и скорости, прежде чем выбирать».

### J-025 — INCORRECT
- **Где / цитата:** ст. 32:109 — «Метод `u.Redacted()` заменяет `Userinfo` на `xxxxx` и очищает `RawQuery`»; итог 151.
- **Вердикт:** `Redacted()` заменяет только пароль. Имя пользователя и query остаются — совет ведёт к утечке токенов из query в логи.
- **Доказательство:** запуск: `https://user:pass@host/p?token=SECRET` → `https://user:xxxxx@host/p?token=SECRET`. doc `url.URL.Redacted`: «Redacted is like String but replaces any password with "xxxxx". Only the password in u.User is redacted».
- **Предлагаемая правка:** «`u.Redacted()` заменяет на `xxxxx` только **пароль** в `u.User`. Имя пользователя, путь и query (`?token=…`) остаются как есть. Перед логированием URL с секретами в параметрах удалите их сами: скопируйте URL, вызовите `q := u.Query(); q.Del("token"); u.RawQuery = q.Encode()` или логируйте только `u.Host` и `u.Path`».

### J-026 — INCORRECT
- **Где / цитата:** ст. 33:152 — «Игнорирование `r.Body.Close()` | Соединение не возвращается в пул Transport, FD утекает | Всегда `defer r.Body.Close()` или читайте до EOF. `http.Client` закрывает автоматически, но серверные хендлеры — нет».
- **Вердикт:** инвертировано. Тело **запроса** сервер закрывает сам. Закрывать тело **ответа** (`resp.Body`) обязан клиент, иначе соединение не вернётся в пул.
- **Доказательство:** go1.27.1 `src/net/http/request.go:183–184`: «The Server will close the request body. The ServeHTTP Handler does not need to». doc `http.Client.Do`: «If the returned error is nil, the Response will contain a non-nil Body which the user is expected to close».
- **Предлагаемая правка:** «Незакрытый `resp.Body` на клиенте | Соединение не возвращается в пул `Transport`, утекают FD и горутины | После `client.Do` всегда `defer resp.Body.Close()`. Тело **запроса** в обработчике закрывать не нужно: это делает сервер».

### J-027 — CONTEXT-DEPENDENT
- **Где / цитата:** ст. 34:99–114 — литерал `&http.Transport{… DialContext: (&net.Dialer{…}).DialContext, …}`; 128 — «используйте стандартный `http.Transport`, он сам делегирует `http2` при TLS»; ст. 33:62–70 (литерал без `DialContext`); ст. 38:222–225 (литерал с `TLSClientConfig`, отмечено в B-отчёте).
- **Вердикт:** зависит от того, какие поля заданы. Литерал с `DialContext`, `Dial`, `DialTLS` или `TLSClientConfig` без `ForceAttemptHTTP2: true` отключает HTTP/2 — так в ст. 34 и 38. Литерал ст. 33 (без этих полей) HTTP/2 сохраняет. Во **всех** трёх литералах нет `Proxy`, поэтому `HTTP(S)_PROXY` перестаёт работать. Утверждение 128 верно только для транспорта без этих полей или с `ForceAttemptHTTP2: true`.
- **Доказательство:** запуск против `httptest`-сервера с `EnableHTTP2 = true` и TLS: литерал с `DialContext` + `TLSClientConfig` → `HTTP/1.1`; тот же литерал + `ForceAttemptHTTP2: true` → `HTTP/2.0`; `http.DefaultTransport.(*http.Transport).Clone()` + `TLSClientConfig` → `HTTP/2.0`. `(&http.Transport{}).Proxy == nil`, у `DefaultTransport` — `ProxyFromEnvironment`. `src/net/http/transport.go` (`DefaultTransport`): `Proxy: ProxyFromEnvironment`, `ForceAttemptHTTP2: true`; doc `ForceAttemptHTTP2`: «By default, use of any those fields conservatively disables HTTP/2».
- **Предлагаемая правка:** ст. 34 — пример через клон:
  ```go
  tr := http.DefaultTransport.(*http.Transport).Clone() // Proxy, HTTP/2, таймауты по умолчанию
  tr.MaxIdleConns = 200
  tr.MaxIdleConnsPerHost = 50
  tr.MaxConnsPerHost = 100
  tr.IdleConnTimeout = 90 * time.Second
  ```
  Если нужен литерал — добавить `Proxy: http.ProxyFromEnvironment` и `ForceAttemptHTTP2: true` с комментарием «без него непустой `DialContext` отключает HTTP/2». Таблица 128 — «…он сам согласует HTTP/2 через ALPN, если не заданы `DialContext`/`DialTLS`/`TLSClientConfig`, или если `ForceAttemptHTTP2: true`». Ст. 33:62–70 и ст. 38:222–225 — добавить `Proxy` (в ст. 38 — и `ForceAttemptHTTP2`).

### J-028 — OUTDATED
- **Где / цитата:** ст. 37:18 — «Глобальные функции (`rand.Intn`, `rand.Float64`) защищены внутренним `sync.Mutex`»; 54 — «`sync.Mutex` внутри рантайма становится bottleneck'ом»; пример `randPool` (58–70); 72 — «состоянием PCG»; 101 — свой Фишер–Йетс «избегая мьютекса»; 111 — «Не вызывайте `rand.Seed()`…».
- **Вердикт:** с Go 1.20, если глобальный генератор не засеян вручную, функции верхнего уровня `math/rand` используют источник рантайма без мьютекса; в `math/rand/v2` — всегда. Пул из примера медленнее глобальных функций и сидирует `time.Now().UnixNano()` (совпадающие seed у одновременно созданных генераторов). У `rand.Rand` v1 состояние — ALFG, не PCG. Дополнение из B-отчёта: с `go 1.24`+ в `go.mod` вызов `rand.Seed` вообще ничего не делает (`randseednop`).
- **Доказательство:** go1.27.1 `src/math/rand/rand.go`, `globalRand()`: `lockedSource` только при `randautoseed=0`, иначе `&Rand{src: &runtimeSource{}, …}`; `runtimeSource` → `runtime_rand()` без блокировок. Go 1.24 release notes: «Calls to the deprecated top-level Seed function no longer have any effect … randseednop=0». Бенчмарк `b.RunParallel` (go1.27.1, 24 CPU): глобальный `rand.Intn` — 6,9 нс (1 поток) / 7,5 нс (`-cpu 8`); пул из статьи — 12,0 / 16,1 нс.
- **Предлагаемая правка:** 18 — «С Go 1.20 глобальные функции `math/rand` (если `Seed` не вызывался) и всегда — функции `math/rand/v2` используют генератор рантайма с состоянием на каждый поток, без мьютекса. Отдельный `rand.Rand` из `rand.New` небезопасен для конкурентного доступа». Раздел 1 «Цена конкуренции» — заменить: «В Go 1.20+ глобальные функции не создают точку конкуренции; пул локальных генераторов не нужен и медленнее (замер). Свой `rand.Rand` нужен для воспроизводимой последовательности с фиксированным seed». 72 — убрать «PCG». 101 — убрать «избегая мьютекса». 111 — «С `go 1.24`+ в `go.mod` `rand.Seed` ничего не делает; для воспроизводимости используйте `rand.New(rand.NewSource(seed))`».

### J-029 — INCORRECT
- **Где / цитата:** ст. 41:92 — «Идиоматичная защита — использование `io.CopyN` с жестким ограничением»; 101 — «тройной защитой … от архивов-бомб»; 169–170 — `// 3. Защита от архивов-бомб: читаем строго header.Size байт через io.CopyN`; итог 257 — «ограничивайте объем … через `header.Size` или `io.LimitReader`».
- **Вердикт:** `header.Size` берётся из недоверенного архива. `io.CopyN(f, tr, header.Size)` распакует столько, сколько заявил злоумышленник (для tar это и так ровно размер записи — `tr.Read` больше не отдаст). Защиты от бомбы в примере нет: нужен **собственный** предел на файл, на сумму и на число записей.
- **Доказательство:** код статьи (строки 156–174) сравнивает `header.Size` ни с чем; doc `archive/tar.Header.Size` — «logical file size in bytes», значение из заголовка записи. Отдельный эксперимент с бомбой не ставил: вывод следует из кода.
- **Предлагаемая правка:**
  ```go
  const (
      maxFileSize  = 100 << 20 // 100 МБ на файл
      maxTotalSize = 1 << 30   // 1 ГБ на архив
      maxEntries   = 10_000
  )
  var total int64
  // в цикле по записям:
  if entries++; entries > maxEntries { return errors.New("tar: too many entries") }
  if header.Size > maxFileSize || total+header.Size > maxTotalSize {
      return errors.New("tar: archive exceeds size limits")
  }
  n, err := io.Copy(f, io.LimitReader(tr, maxFileSize+1))
  total += n
  if n > maxFileSize { return errors.New("tar: file too large") }
  ```
  Итог п. 4 — «…ограничивайте объём собственными пределами (на файл, на архив, на число записей). `header.Size` задаёт автор архива, это не защита».

### J-030 — INCORRECT
- **Где / цитата:** ст. 42:7 — «традиционно применяется в … сетевых протоколах (SSH, TLS, сжатие заголовков HTTP/2 HPACK)»; 60 — «Графика PNG, протокол SSH, сжатие заголовков HTTP/2 HPACK»; 67 — «Для обработки изображений PNG или структур HPACK применяйте `compress/zlib`».
- **Вердикт:** HPACK (RFC 7541) — отдельная схема: статическая и динамическая таблицы индексов плюс статический код Хаффмана. Её придумали **вместо** DEFLATE-сжатия заголовков SPDY из-за атаки CRIME. Сжатие на уровне TLS (DEFLATE, RFC 3749) после CRIME отключают повсеместно, в TLS 1.3 оно запрещено, `crypto/tls` его не реализует. PNG (zlib) и SSH (zlib) — верно. Ответ собеседования (строка 224) описывает HPACK верно.
- **Доказательство:** go1.27.1 `src/vendor/golang.org/x/net/http2/hpack/*.go` — импорты только `bytes`, `errors`, `fmt`, `io`, `sync`, никаких `compress/*`. RFC 7541 § 1 (мотивация против DEFLATE и CRIME), § 2 (таблицы), § 5.2 (Хаффман) — по памяти; RFC 8446 § 4.1.2 (TLS 1.3: `legacy_compression_methods` только `null`) — по памяти.
- **Предлагаемая правка:** 7 — «…применяется в PNG и в протоколе SSH (опция сжатия)». 60 — «Графика PNG, протокол SSH». 67 — «Для PNG-подобных форматов — `compress/zlib`. Заголовки HTTP/2 сжимает HPACK — отдельный алгоритм (таблицы индексов + код Хаффмана), он не использует DEFLATE: сжатие заголовков через DEFLATE в SPDY было уязвимо к атаке CRIME».

### J-031 — INCORRECT
- **Где / цитата:** ст. 43:149 — «стандартные методы `cmd.Output()` или `cmd.CombinedOutput()` неприменимы — они выполняют чтение последовательно и гарантируют deadlock при объеме вывода более 64 КБ».
- **Вердикт:** `Output`, `CombinedOutput` и `Run` с `cmd.Stdout = &buf` читают пайпы в фоновых горутинах и корректно завершаются при любом объёме вывода (ограничение — память). Взаимная блокировка бывает при ручной работе с `StdoutPipe`: `Wait` до окончания чтения или запись в `Stdin` и чтение `Stdout` в одной горутине. Описание буфера пайпа 64 КБ (строки 61–63) верно.
- **Доказательство:** запуск на go1.27.1: `exec.Command("head", "-c", "10000000", "/dev/zero").Output()` → 10 000 000 байт, `err = nil`; `CombinedOutput` для 3 МБ в stdout + 3 МБ в stderr → 6 000 000 байт, `nil`.
- **Предлагаемая правка:** «`cmd.Output()` и `cmd.CombinedOutput()` сами читают вывод в фоновых горутинах и не зависают при любом объёме, но держат весь вывод в памяти. Взаимная блокировка возникает при ручной работе с пайпами (`StdoutPipe`, `StdinPipe`): если вызвать `Wait` до того, как вывод дочитан, или писать в stdin и читать stdout в одной горутине».

### J-032 — INCORRECT
- **Где / цитата:** ст. 44:110–131 — `changeNetworkNamespace`: `runtime.LockOSThread(); defer runtime.UnlockOSThread()`, затем `unix.Setns(nsFD, unix.CLONE_NEWNET)` и `return nil`; комментарий «Любые операции здесь гарантированно выполняются на этом же потоке ОС»; итог п. 3 (231); таблица 204 — «Системный тред ядра остается навсегда заблокированным за "мертвой" горутиной».
- **Вердикт:** после `Setns` функция возвращается и снимает привязку. Поток с чужим network namespace уходит в общий пул рантайма, и на нём окажутся **другие** горутины — ровно то, о чём статья предупреждает в строке 96. Работа в новом namespace должна идти внутри функции, а на выходе нужно вернуть исходный namespace (`Setns` на сохранённый fd) или завершить горутину, не вызывая `UnlockOSThread` (тогда поток уничтожится). Таблица 204: поток горутины, вышедшей без `UnlockOSThread`, рантайм уничтожает, а не держит.
- **Доказательство:** doc `runtime.LockOSThread` (go1.27.1): «If the calling goroutine exits without unlocking the thread, the thread will be terminated»; «no other goroutine will execute in it, until the calling goroutine has made as many calls to UnlockOSThread as to LockOSThread». Запуск с namespace не делал (нужен root).
- **Предлагаемая правка:**
  ```go
  // runInNetNS выполняет fn в сетевом namespace ns и возвращает поток в исходный.
  func runInNetNS(ns string, fn func() error) error {
      runtime.LockOSThread()
      defer runtime.UnlockOSThread()

      orig, err := unix.Open("/proc/thread-self/ns/net", unix.O_RDONLY|unix.O_CLOEXEC, 0)
      if err != nil { return err }
      defer unix.Close(orig)

      target, err := unix.Open(ns, unix.O_RDONLY|unix.O_CLOEXEC, 0)
      if err != nil { return err }
      defer unix.Close(target)

      if err := unix.Setns(target, unix.CLONE_NEWNET); err != nil { return err }
      defer unix.Setns(orig, unix.CLONE_NEWNET) // вернуть поток в исходный ns до Unlock

      return fn() // сокеты, созданные здесь, принадлежат ns
  }
  ```
  Если вернуть namespace не удалось, горутина должна завершиться без `UnlockOSThread`, чтобы поток был уничтожен. Таблица 204 — «Если горутина завершится, не сняв привязку, рантайм уничтожит поток (так и задумано для потоков с изменённым состоянием). Опасна обратная ошибка: снять привязку, не вернув состояние потока».

### J-033 — INCORRECT
- **Где / цитата:** ст. 45:132 — «// Тело фаззинг-теста запускается тысячами параллельных горутин»; 197–198 — «…работает непосредственно внутри процесса рантайма Go … без использования мостов и разделяемой памяти IPC … без системных вызовов `fork`/`exec`. Это позволяет достигать производительности до $10^5$–$10^6$ итераций в секунду на одно ядро».
- **Вердикт:** фаззер Go — процесс-координатор плюс рабочие **процессы** (их число задаёт `-parallel`, по умолчанию `GOMAXPROCS`). Координатор запускает их через `exec`, данные передаются через разделяемую память. Мутация и минимизация идут в рабочих процессах. Скорость зависит от цели. Сравнение «быстрее go-fuzz/AFL» без бенчмарка — мнение; вопрос собеседования построен на ложной посылке.
- **Доказательство:** go1.27.1 `src/internal/fuzz/worker.go:345` — `cmd := exec.Command(w.binPath, w.args...)`; строки 54, 64 — `sharedMem`, `sharedMemTempFile`; `fuzz.go:55` — «parallel is the number of worker processes to run in parallel». Запуск: `./t3.test -test.fuzz=FuzzNop -test.parallel=4` → в `ps` один координатор и **4** процесса `./t3.test -test.fuzzworker …`; пустая цель — 811 646 execs/s суммарно (~2·10⁵ на процесс).
- **Предлагаемая правка:** 132 — «// Тело фаззинг-теста выполняется в рабочих процессах (по одному на `-parallel`, по умолчанию `GOMAXPROCS`) на мутированных данных». Ответ 198 — «Встроенный фаззер не требует отдельной сборки и обвязки: он использует инструментирование покрытия компилятора Go и запускается командой `go test -fuzz`. Координатор запускает несколько рабочих процессов из того же тестового бинарника и обменивается с ними входами через разделяемую память. Пропускная способность зависит от цели: для простой функции — порядка 10⁵ запусков в секунду на процесс». Сам вопрос лучше переформулировать: «Чем встроенный фаззинг удобнее go-fuzz?».

### J-034 — INCORRECT
- **Где / цитата:** ст. 46:14 — «…запускает алгоритм поиска минимального контрпримера (shrinking)»; 28 — «**Алгоритм сужения (Shrinking):** …»; 133 — «Базовый shrinking в `testing/quick` умеет упрощать только элементарные скалярные типы»; 148 — «алгоритм сужения (shrinking) крайне примитивен»; диаграмма.
- **Вердикт:** `testing/quick` сужения не делает вообще. `Check` возвращает `*CheckError` с номером итерации и первым найденным входом.
- **Доказательство:** go1.27.1 `src/testing/quick/quick.go`: слово «shrink» встречается один раз — строка 64 («hint is used for shrinking as a function of indirection level», это про размер генерируемых значений). Запуск: `quick.Check(func(x int) bool { return x < 1000 }, nil)` → `#1: failed on input 6691353688392571136 (*quick.CheckError)` — огромное число, не минимальный контрпример.
- **Предлагаемая правка:** 14 — «…и, если инвариант нарушается, возвращает первый найденный контрпример. Сужения (shrinking) в `testing/quick` нет: контрпример бывает большим и неудобным, поэтому для серьёзного property-based тестирования используют `pgregory.net/rapid` или `gopter`». Пункт 4 раздела «Механика» и диаграмму — заменить на «4. Если предикат вернул `false`, `Check` возвращает `*quick.CheckError{Count, In}`». Строки 133 и 148 — «сужения нет».

### J-035 — INCORRECT
- **Где / цитата:** ст. 45:191 — «Метод `t.Cleanup` регистрирует коллбэки, гарантированно срабатывающие даже при досрочной остановке через `t.Fatal`…»; итог 218 — «`t.Cleanup` надежнее обычного `defer`: он гарантирует … утилизацию … даже при вызове `t.Fatal`».
- **Вердикт:** `t.Fatal` вызывает `runtime.Goexit`, отложенные функции **выполняются**. Настоящие отличия `Cleanup`: срабатывает после завершения теста **и всех его подтестов** (включая параллельные, которые стартуют после возврата родительской функции — там `defer` сработает раньше них); его можно зарегистрировать из хелпера.
- **Доказательство:** doc `testing.T.FailNow`: «…calling runtime.Goexit (which then runs all deferred calls in the current goroutine)». Запуск: тест `defer t.Log(…); t.Cleanup(…); t.Fatal("boom")` → в выводе и `defer ran after Fatal`, и `cleanup ran`.
- **Предлагаемая правка:** таблица 191 — «`defer` выполняется при выходе из функции теста — и при `t.Fatal` тоже. `t.Cleanup` выполняется позже: после завершения теста и всех его подтестов, включая параллельные. Его можно зарегистрировать из вспомогательной функции, которая создаёт ресурс». Итог п. 4 — «`t.Cleanup` удобнее `defer`, когда ресурс создаёт хелпер или когда ресурс нужен параллельным подтестам: очистка выполнится после них».

---

## 3. Medium

### J-036 — INCORRECT
- **Где / цитата:** ст. 1:111 — «`strings.Builder` спроектирован так, чтобы минимизировать утечки памяти в кучу (heap)»; 119–120 — «Компилятор видит, что внутреннее поле []byte не "убегает" за пределы, если мы не берем из него строку через .String() слишком рано».
- **Вердикт:** буфер Builder растёт через `append` и живёт в куче всегда. Экономия Builder — в отсутствии копирования при `String()` и в амортизированном росте (`Grow`), а не в escape analysis. «Утечка» (leak) и «убегание» (escape) — разные понятия. Эффекта «взять строку слишком рано» нет.
- **Доказательство:** `go build -gcflags=-m` на функции с `var b strings.Builder; b.Grow(1024); b.WriteString(...); return b.String()` → `append escapes to heap` (буфер в куче, `String()` инлайнится).
- **Предлагаемая правка:** «`strings.Builder` экономит аллокации: `Grow(n)` выделяет буфер один раз, а `String()` возвращает строку поверх этого буфера без копирования. Сам буфер лежит в куче».

### J-037 — PARTIALLY CORRECT
- **Где / цитата:** ст. 1:56 — «Стандартная библиотека принципиально не имеет внешних зависимостей. Она самодостаточна».
- **Вердикт:** при сборке ничего не скачивается — верно. Но stdlib содержит вендорные копии `golang.org/x/crypto`, `x/net`, `x/sys`, `x/text`; исправления в них приходят только с выпуском Go.
- **Доказательство:** go1.27.1 `src/vendor/modules.txt`: `golang.org/x/crypto v0.52.1-…`, `golang.org/x/net v0.55.1-…`, `golang.org/x/sys v0.45.0`, `golang.org/x/text v0.37.0`.
- **Предлагаемая правка:** «Стандартная библиотека не тянет внешних модулей: всё нужное, включая вендорные копии `golang.org/x/net`, `x/crypto`, `x/sys` и `x/text`, поставляется вместе с Go. Обратная сторона: исправления в этих копиях (например, в HTTP/2) приходят только с новым выпуском Go — обновляйте тулчейн».

### J-038 — INCORRECT
- **Где / цитата:** ст. 1, диаграмма 99–101 (`Net->>Kernel: epoll_ctl (Регистрация дескриптора)` после попытки чтения); ст. 31:19 — «Он регистрирует файловый дескриптор сокета в сетевом поллере» (после `EAGAIN`); 21 — «фоновый поток поллера (или `sysmon`) будит горутину»; диаграмма 37 — `epoll_ctl EPOLLIN`.
- **Вердикт:** дескриптор регистрируется в epoll **один раз** при создании (`EPOLL_CTL_ADD` с `EPOLLIN|EPOLLOUT|EPOLLRDHUP|EPOLLET`, edge-triggered). При `EAGAIN` горутина паркуется без нового `epoll_ctl`. Отдельного потока поллера нет: `netpoll` вызывают планировщик (`findRunnable`, в том числе блокирующий `netpoll(delay)` у простаивающего потока) и `sysmon`.
- **Доказательство:** go1.27.1 `src/runtime/netpoll_epoll.go:49–54` (`netpollopen`: `EPOLL_CTL_ADD`, `EPOLLET`); `EPOLL_CTL_MOD` в `src/runtime/*.go` не встречается; `src/internal/poll/fd_poll_runtime.go:38–40` (`pd.init` → `runtime_pollOpen` при создании `FD`); `src/runtime/proc.go:1778, 3511, 3769 (netpoll(delay) — «block until new work is available»), 3828, 6622` — вызовы `netpoll` из планировщика и `sysmon`.
- **Предлагаемая правка:** диаграмма ст. 1 — перенести `epoll_ctl (EPOLL_CTL_ADD, один раз)` на момент создания соединения, после неудачного `read` — только `gopark`. Ст. 31:19 — «Дескриптор сокета уже зарегистрирован в поллере при создании соединения (edge-triggered). Рантайм лишь паркует горутину до события готовности». 21 — «Поллер опрашивают сам планировщик (простаивающий поток ждёт в `epoll_wait`) и `sysmon`; когда приходит `EPOLLIN`, горутина становится `Grunnable`». Диаграмма 37 — «Ожидание в netpoller (FD зарегистрирован заранее)».

### J-039 — INCORRECT
- **Где / цитата:** ст. 2:26 — `%+v` → `{ID:42 Name:"server"}`; 240 — «Вывод fmt.Println(user): {Name:"admin" Password:"secret123"}».
- **Вердикт:** `%v` и `%+v` строки не квотируют. Кавычки (и имя типа) даёт только `%#v`.
- **Доказательство:** запуск: `%+v` → `{ID:42 Name:server}`; `fmt.Println(User{42,"server"})` → `{42 server}`; `%#v` → `main.User{ID:42, Name:"server"}`.
- **Предлагаемая правка:** таблица — `%+v` → `{ID:42 Name:server}`; комментарий 240 — `// Вывод fmt.Println(user): {admin secret123}; %+v: {Name:admin Password:secret123}`.

### J-040 — PARTIALLY CORRECT
- **Где / цитата:** ст. 2:133 — «Параметры … упаковываются в срез интерфейсов … `id` … обязана быть упакована в кучу»; 134 — «Для каждого верба рантайм использует пакет `reflect`»; 135 — «временный `bytes.Buffer` (или структура `pp` из пула)»; 150 — «~2 аллокации на вызов: срез интерфейсов + результирующая строка».
- **Вердикт:** массив variadic-аргументов не убегает и лежит на стеке. Аллоцируются упаковка не-указательных значений в `any` (`convT64`, `convTstring`; кроме констант и целых 0–255) и результирующая строка. Базовые типы `printArg` обрабатывает type switch-ем без `reflect`. Буфер — собственный `fmt.buffer` внутри `pp`, а `pp` берётся из `sync.Pool` **всегда**. Итоговое число зависит от аргументов: «~2» занижено для примера статьи.
- **Доказательство:** запуск: `fmt.Sprintf("User %s has ID %d", name, id)` с переменными `name string`, `id = 12345` → **3** аллокации (строка + `int` + результат); с константой `7` вместо `id` → 2. go1.27.1 `src/fmt/print.go` — `newPrinter` (`ppFree.Get()`), `printArg` (type switch).
- **Предлагаемая правка:** «1. Аргументы передаются как `...any`: сам срез обычно лежит на стеке, но значения, которые не помещаются в указатель (`string`, большие `int`, структуры), упаковываются в кучу. 2. Базовые типы `fmt` распознаёт через type switch, `reflect` нужен для структур, map, срезов. 3. Внутренний буфер берётся из `sync.Pool`. 4. Результат копируется в новую строку». Комментарий 150 — «// 3 аллокации: упаковка name и id в any + результирующая строка».

### J-041 — INCORRECT
- **Где / цитата:** ст. 2:164–166 и 216–220 — `sb.Write(strconv.AppendInt(nil, int64(id), 10))` с комментариями «избегает аллокаций», «1 аллокация на результат», «Единственная аллокация финальной строки».
- **Вердикт:** `AppendInt(nil, …)` аллоцирует новый срез. `Builder.String()` не аллоцирует; аллокации — в `Grow`. Пример даёт 2 аллокации вместо заявленной одной.
- **Доказательство:** `testing.AllocsPerRun`: `strconv.AppendInt(nil, 12345, 10)` → 1; функция `buildKey` из статьи → 2; тот же код с `var tmp [20]byte; AppendInt(tmp[:0], …)` → 1.
- **Предлагаемая правка:** `var tmp [20]byte; sb.Write(strconv.AppendInt(tmp[:0], int64(userID), 10))` с комментарием «буфер на стеке, без аллокации»; комментарий к `String()` — «`String()` не копирует: единственная аллокация — `Grow`».

### J-042 — INCORRECT
- **Где / цитата:** ст. 2:19 — «в Go вербы защищены строгой проверкой типов»; 255 — «`go vet` строго проверит соответствие верба типу данных на этапе компиляции»; 261 — «`go vet` немедленно выдаст ошибку `printf: fmt.Sprintf format %d has arg of type string`».
- **Вердикт:** компилятор форматные строки не проверяет: несоответствие в рантайме печатается как `%!d(string=abc)`. `go vet` — отдельный шаг; его анализатор `printf` автоматически запускается внутри `go test`, но не `go build`. Текст сообщения другой. Утверждение скаута, что проверки встроены в `go build` с 1.21, тоже неверно.
- **Доказательство:** запуск: `_ = fmt.Sprintf("%d", s)` — `go build` проходит молча; `go vet` → `fmt.Sprintf format %d has arg s of wrong type string`.
- **Предлагаемая правка:** 19 — «…в Go аргументы типизированы, и ошибка верба не портит память: `fmt` напечатает `%!d(string=abc)`. Найти такие ошибки до запуска помогает `go vet`». 255 — «`go vet` (отдельный шаг; автоматически — при `go test`) проверит соответствие верба типу». 261 — «…выдаст `fmt.Sprintf format %d has arg s of wrong type string`».

### J-043 — INCORRECT
- **Где / цитата:** ст. 2:228 — «Он не поддерживает перестановку аргументов в строках формата … (как позиционные параметры `{0}` и `{1}` в C#…)».
- **Вердикт:** `fmt` поддерживает явные индексы аргументов `%[n]`. Вывод, что `fmt` не годится для локализации, верен по другим причинам: нет плюральных форм и локальных форматов чисел.
- **Доказательство:** запуск: `fmt.Printf("%[2]d %[1]d\n", 11, 22)` → `22 11`.
- **Предлагаемая правка:** «Порядок аргументов можно менять явными индексами (`%[2]d %[1]d`), но `fmt` не знает плюральных форм, локальных разделителей чисел и форматов дат. Для локализации используйте `golang.org/x/text/message`».

### J-044 — PARTIALLY CORRECT
- **Где / цитата:** ст. 2:232–247 — решение: «Всегда реализуйте интерфейс `fmt.Stringer`».
- **Вердикт:** `Stringer` защищает `%v`, `%+v`, `%s` и `Println`. Не защищает: `%#v` (использует `GoStringer`), структуру-обёртку с неэкспортируемым полем `User` (`fmt` не вызывает методы неэкспортируемых полей), `encoding/json` и `slog` (свой интерфейс `LogValuer`). `String()`, вызывающий `Sprintf("%v", u)` на самом себе, уходит в бесконечную рекурсию.
- **Доказательство:** запуск с `func (u User) String()` из статьи: `%v` и `%+v` → `User{Name:admin, Password:***}`; `%#v` → `main.User{Name:"admin", Password:"secret123"}`; `Wrap{u User}` (поле неэкспортируемое) с `%v` → `{{admin secret123}}`.
- **Предлагаемая правка:** после решения добавить: «`Stringer` закрывает не всё: `%#v` печатает поля как есть (реализуйте и `GoString()`), структура, где `User` лежит в неэкспортируемом поле, напечатается без вызова `String()`, а JSON и `slog` используют свои интерфейсы (`MarshalJSON`, `slog.LogValuer`). Надёжнее держать секрет в отдельном типе (`type Secret string` с `String`, `GoString`, `MarshalJSON` и `LogValue`)».

### J-045 — OUTDATED
- **Где / цитата:** ст. 3:22 — «механизм упаковки типов (`runtime.convT2E`), который упаковывает данные и таблицу методов в двухсловную структуру `runtime.iface`»; ст. 23:44 — «Методы `.Interface()`, `.Set()`, `.Call()` требуют упаковки … через `runtime.convT2E`».
- **Вердикт:** `convT2E`/`convT2I` давно заменены семейством `convT`, `convTnoptr`, `convT16/32/64`, `convTstring`, `convTslice`; `itab` подставляет компилятор. Указатель кладётся в слово данных интерфейса без упаковки. `Value.Set` принимает `Value` и упаковки не требует.
- **Доказательство:** go1.27.1 `src/runtime/iface.go:352–456` — `convT`, `convTnoptr`, `convT16`, `convT32`, `convT64`, `convTstring`, `convTslice`; `grep convT2E src/runtime/*.go` — пусто. Версию удаления `convT2E` не уточнял (по брифу — 1.15–1.17).
- **Предлагаемая правка:** ст. 3:22 — «Присваивание значения интерфейсу заполняет два слова: указатель на `itab` (тип и таблица методов) и указатель на данные. Указатель (`*MyError`) кладётся как есть; значение, не помещающееся в указатель, рантайм копирует в кучу (`runtime.convT*`)». Ст. 23:44 — «`.Interface()` и `reflect.ValueOf` упаковывают значение в интерфейс (`runtime.convT*`), `.Call()` выделяет срезы аргументов».

### J-046 — PARTIALLY CORRECT
- **Где / цитата:** ст. 3:10 — «Отсутствие механизма раскрутки стека (Stack Unwinding) и громоздких таблиц исключений (DWARF Exception Tables) делает счастливым предсказатель ветвлений».
- **Вердикт:** исключения C++ в реализации Itanium ABI на «счастливом пути» бесплатны: таблицы `.eh_frame`/LSDA не исполняются. Go, наоборот, платит проверкой `err != nil` после каждого вызова (дёшево и хорошо предсказывается). Преимущество Go — дешёвый и предсказуемый путь **ошибки**, а не счастливый путь. «DWARF Exception Tables» — неточное имя (CFI и LSDA).
- **Доказательство:** Itanium C++ ABI, раздел Exception Handling (zero-cost модель) — по общеизвестному описанию ABI; отдельно в сессии не открывал.
- **Предлагаемая правка:** «**Mechanical Sympathy:** проверка `if err != nil` — одно хорошо предсказуемое сравнение. Путь ошибки стоит столько же, сколько обычный возврат, тогда как выброс исключения в C++ или Java требует раскрутки стека по таблицам и стоит микросекунды. Счастливый путь у исключений бесплатный, поэтому выигрыш Go — в цене и предсказуемости обработки ошибки».

### J-047 — INCORRECT
- **Где / цитата:** ст. 3:272–282 — «// ❌ Плохо: создает новую аллокацию и рефлексию на каждой итерации» (`return fmt.Errorf(...)` внутри `for`); «// ✅ … io.EOF — глобальный синглетон, проверка за доли наносекунды».
- **Вердикт:** `return` выполняется один раз — пример не показывает «аллокацию на каждой итерации». `errors.Is` — вызов функции с проверкой сравнимости и циклом по `Unwrap`: это наносекунды, не доли. Для `io.EOF` контракт `io.Reader` требует сравнения `err == io.EOF`. Фрагменты не компилируются сами по себе (`i`, `err` не объявлены; `break` вне цикла).
- **Доказательство:** бенчмарк на go1.27.1: `errors.Is(io.EOF, io.EOF)` — 2,9 нс, `e == io.EOF` — 1,25 нс; 0 аллокаций. doc `io.Reader`: «Read must return EOF itself, not an error wrapping EOF, because callers will test for EOF using ==».
- **Предлагаемая правка:**
  ```go
  // ❌ Плохо: ожидаемый сигнал оборачивается в новую ошибку на каждом вызове
  func readChunk(r io.Reader, i int) error {
      if _, err := r.Read(buf); err != nil {
          return fmt.Errorf("read chunk %d: %w", i, err) // аллокация даже для io.EOF
      }
      return nil
  }

  // ✅ Хорошо: конец данных — штатный сигнал, сравниваем с sentinel
  for {
      n, err := r.Read(buf)
      process(buf[:n])
      if err == io.EOF { // контракт io.Reader: EOF возвращается без обёртки
          break
      }
      if err != nil {
          return fmt.Errorf("read: %w", err)
      }
  }
  ```

### J-048 — INCORRECT
- **Где / цитата:** ст. 3:315 — «Компилятор запрещает неиспользуемые переменные; игнорирование через `_` сразу видно на код-ревью».
- **Вердикт:** самый частый способ потерять ошибку — вызвать функцию как оператор (`os.Remove(p)`, `defer f.Close()`, `w.Write(b)`). Компилятор и `go vet` это пропускают. Ловят `errcheck` (входит в golangci-lint) и аналоги.
- **Доказательство:** запуск: `os.Remove("nothing")` без обработки — `go build` и `go vet` молчат.
- **Предлагаемая правка:** «Ошибку легко потерять, просто не присвоив результат: `os.Remove(path)` или `defer f.Close()` компилятор и `go vet` пропускают. Включите в CI линтер `errcheck`».

### J-049 — INCORRECT
- **Где / цитата:** ст. 4:18 — «Всего 24 байта в оперативной памяти (два указателя …)».
- **Вердикт:** два указателя на 64-битной платформе — 16 байт.
- **Доказательство:** запуск: `unsafe.Sizeof(io.Reader(nil))` → 16.
- **Предлагаемая правка:** «Значение интерфейса — всего 16 байт на 64-битной платформе (два указателя: на `itab` с типом и методами и на данные)…».

### J-050 — INCORRECT
- **Где / цитата:** ст. 4:21 — «Go не проверяет тип источника через `instanceof` или тяжелые `type assertions` внутри ядра библиотек. Всё сводится к мгновенному вызову метода через таблицу `itab`».
- **Вердикт:** следующий раздел той же статьи описывает, как `io.Copy` проверяет `src.(WriterTo)` и `dst.(ReaderFrom)`. Утверждения типа — основной механизм оптимизаций stdlib.
- **Доказательство:** go1.27.1 `src/io/io.go`, `copyBuffer`: `if wt, ok := src.(WriterTo); ok { … }`, `if rf, ok := dst.(ReaderFrom); ok { … }`, `src.(*LimitedReader)`.
- **Предлагаемая правка:** «Обычные вызовы `Read` и `Write` — это вызов метода через таблицу `itab`. А там, где можно ускориться, библиотека проверяет дополнительные интерфейсы утверждением типа: `io.Copy` ищет у источника `WriterTo`, у приёмника — `ReaderFrom`».

### J-051 — INCORRECT
- **Где / цитата:** ст. 4, диаграмма 63–64 — `I{"err == nil или EOF?"}` → `I -->|Да| G` (снова `src.Read`).
- **Вердикт:** на `io.EOF` цикл завершается, `Copy` возвращает `nil`. Не показаны `ErrShortWrite` и уменьшение буфера под `*io.LimitedReader`.
- **Доказательство:** go1.27.1 `src/io/io.go`, `copyBuffer`: `if er != nil { if er != EOF { err = er }; break }`; `if nr != nw { err = ErrShortWrite; break }`; размер буфера `l.N` для `*LimitedReader`.
- **Предлагаемая правка:** `I{"Ошибка чтения?"}` → `-->|Нет| G`, `-->|io.EOF| J["Возврат written, nil"]`, `-->|Другая| K["Возврат written, err"]`; отдельной веткой — «Ошибка записи или n < len → ErrShortWrite».

### J-052 — PARTIALLY CORRECT
- **Где / цитата:** ст. 4:77 — «при копировании данных из `*os.File` в сетевой сокет `*net.Conn` на Linux … `sendfile` или `splice`»; 80 — «// Пример оптимизации в net/internal/poll»; таблица 248 — «`io.Copy` + `sendfile`/`splice` (автоматически)».
- **Вердикт:** механизм есть, но «автоматически» — только для конкретных типов: `*net.TCPConn`/`*net.UnixConn`, `*os.File` и `*io.LimitedReader` над ними. Любая обёртка (`bufio.Writer`, `tls.Conn`, `gzip.Writer`, middleware над `ResponseWriter`) отключает его; для TLS он невозможен. Пакета `net/internal/poll` нет — есть `internal/poll`. Типа `*net.Conn` в коде не бывает (указатель на интерфейс). Для file→file на Linux — `copy_file_range`.
- **Доказательство:** go1.27.1: `src/net/splice_linux.go`, `src/net/sendfile.go`, `src/os/zero_copy_linux.go`, `src/internal/poll/{sendfile_unix.go, splice_linux.go, copy_file_range_linux.go}`. Go 1.22 release notes: «When io.Copy copies from a File to a net.UnixConn, it will now use Linux's sendfile(2) … using the new method File.WriteTo».
- **Предлагаемая правка:** 77 — «…из `*os.File` в `*net.TCPConn` (или `*net.UnixConn`) на Linux…»; добавить: «Оптимизация срабатывает, только если `io.Copy` видит именно эти типы. Обёртка вроде `bufio.Writer`, `gzip.Writer` или TLS-соединения выключает её». 80 — «`internal/poll`». Таблица — «`io.Copy` + `sendfile`/`splice`/`copy_file_range` (для конкретных типов)».

### J-053 — OPINION / NOT A FACT CLAIM
- **Где / цитата:** ст. 4:89 — «Это не случайная константа, а выверенный инженерный баланс…»; 91 — «8 страниц … идеальный объем для насыщения очередей сокета»; 92 — «Буфер, кратный страницам памяти, минимизирует количество `Cache Misses`»; итог 276.
- **Вердикт:** сама константа верна (`size := 32 * 1024`), обоснования в коде нет. Остальное — рационализация. Фактические неточности внутри: срез из `make` не выровнен по странице; аппаратная предвыборка не пересекает границу 4 КБ; «насыщение очередей сокета» не зависит от размера пользовательского буфера при `sendfile`/`splice`. Бенчмарк размеров буфера не ставил.
- **Доказательство:** go1.27.1 `src/io/io.go` — `size := 32 * 1024` без комментария. История коммита константы не проверялась: репозитория Go в окружении нет (§ 4).
- **Предлагаемая правка:** «`io.Copy` по умолчанию использует буфер 32 КБ. Это компромисс: на каждые 32 КБ данных приходится по одному вызову `read` и `write`, а память под буфер невелика. Если профиль показывает, что копирование — узкое место, подберите размер через `io.CopyBuffer` и бенчмарк».

### J-054 — PARTIALLY CORRECT
- **Где / цитата:** ст. 4:196 — «`io.LimitReader` … Незаменим в HTTP-серверах для защиты от DoS-атак»; 267 — «Без `Content-Length` или `LimitReader` злоумышленник может отправить бесконечный поток».
- **Вердикт:** `LimitReader` защищает память, но молча обрезает поток и отдаёт `io.EOF` — обработчик увидит усечённое тело. Для HTTP есть `http.MaxBytesReader`: ошибка `*http.MaxBytesError` (Go 1.19) и закрытие соединения. `Content-Length` тоже задаёт клиент, и он может быть огромным.
- **Доказательство:** Go 1.19 release notes: «The io.ReadCloser returned by MaxBytesReader will now return the defined error type MaxBytesError when its read limit is exceeded».
- **Предлагаемая правка:** 196 — «…Ограничивает чтение `n` байтами и затем возвращает `io.EOF`, не сообщая, что данные обрезаны. В HTTP-обработчиках используйте `http.MaxBytesReader(w, r.Body, n)`: при превышении он вернёт `*http.MaxBytesError`». 267 — «…Заголовок `Content-Length` задаёт клиент, ему нельзя доверять: ограничивайте чтение `http.MaxBytesReader`».

### J-055 — INCORRECT
- **Где / цитата:** ст. 5:86–87 — «**Сигнатура `os.WriteFile` отличается.** … тип стал строго `os.FileMode` … Десятичное число `644` в восьмеричной системе равно `01204`, что приведет к установке … битов `setuid`».
- **Вердикт:** сигнатуры одинаковы (`perm fs.FileMode`; `os.FileMode` — псевдоним `fs.FileMode`). `644` = `0o1204`: это бит sticky (`01000`) и права `0204`, а не setuid (`04000`). Ловушка с десятичным `644` реальна, но к миграции отношения не имеет.
- **Доказательство:** go1.27.1 `src/io/ioutil/ioutil.go:52` — `func WriteFile(filename string, data []byte, perm fs.FileMode) error`; `src/os/file.go` — `func WriteFile(name string, data []byte, perm FileMode) error`. Арифметика: 644₁₀ = 1·512 + 2·64 + 0·8 + 4 = 0o1204.
- **Предлагаемая правка:** «**Права — восьмеричным литералом.** Сигнатура `os.WriteFile` та же, что у `ioutil.WriteFile`. Но легко ошибиться с литералом: десятичное `644` — это `0o1204`, то есть бит sticky и права `-w----r--`. Пишите `0o644` или `0644`».

### J-056 — INCORRECT
- **Где / цитата:** ст. 5:56 — «`go vet` и современные линтеры будут выдавать настойчивые предупреждения»; 182 — «Убедитесь, что `io/ioutil` удалён из `go.mod` через `go mod tidy`».
- **Вердикт:** в `go vet` нет анализатора устаревших API — это `staticcheck` SA1019 и подсветка в `gopls`. Пакеты stdlib в `go.mod` не записываются. «Конфликт имён» `ioutil.ReadAll` и `io.ReadAll` — не конфликт: это разные пакеты.
- **Доказательство:** `go tool vet help` (go1.27.1) — список анализаторов без deprecation-проверки (см. J-003); staticcheck.dev: SA1019 — «Using a deprecated function, variable, constant or field».
- **Предлагаемая правка:** 56 — «`staticcheck` (SA1019) и `gopls` помечают его функции как устаревшие». 182 — «Остатки `ioutil` найдёт `staticcheck` или `grep`; `go fix`/`gopls` предлагают автоматическую замену. `go.mod` пакетов стандартной библиотеки не содержит».

### J-057 — PARTIALLY CORRECT
- **Где / цитата:** ст. 5, пример 146–163 (`os.Stat` + `make([]byte, info.Size())` + один `f.Read`; комментарий «+1 байт запаса»); 189 — «`os.ReadFile` проверяет: если `info.Size() == 0`, то … выделяет стартовый буфер (512 байт) и переходит в адаптивный режим чтения `ReadAll`».
- **Вердикт:** суть (предвыделение по размеру, особый случай нулевого размера) верна. Детали: `ReadFile` делает `Open`, затем `f.Stat()`; буфер `Size()+1`, минимум 512 байт; затем собственный цикл `Read` с ростом на 512 байт (`slices.Grow`), а не `ReadAll`. В примере статьи нет `+1`, один `f.Read` может прочитать не всё, и при пустом файле вернётся `io.EOF` как ошибка. Нулевой размер типичен для `/proc`; файлы `/sys` обычно сообщают 4096.
- **Доказательство:** go1.27.1 `src/os/file.go:893–931` (`readFileContents`: `size++ // one byte for final read at EOF`, `minBuf = 512`, «files in Linux's /proc claim size 0», `slices.Grow(data, minBuf)`). `stat`: `/proc/self/status` — 0 байт, `/sys/class/net/lo/mtu` — 4096.
- **Предлагаемая правка:** пример —
  ```go
  // Упрощённо, как это делает os.ReadFile:
  f, err := os.Open(path)
  if err != nil { return nil, err }
  defer f.Close()
  size := 512
  if fi, err := f.Stat(); err == nil && int(fi.Size())+1 > size {
      size = int(fi.Size()) + 1 // +1 — чтобы сразу увидеть EOF
  }
  data := make([]byte, 0, size)
  for {
      n, err := f.Read(data[len(data):cap(data)])
      data = data[:len(data)+n]
      if err == io.EOF { return data, nil }
      if err != nil { return data, err }
      if len(data) == cap(data) { data = slices.Grow(data, 512) }
  }
  ```
  Ответ 189 — «Файлы `/proc` сообщают размер 0. `os.ReadFile` в этом случае начинает с буфера 512 байт и читает в цикле, наращивая его, пока не встретит EOF».

### J-058 — OUTDATED
- **Где / цитата:** ст. 5:140–142 — «читает чанками фиксированного размера (по 512 байт, затем удваивая буфер) и растёт через `append`, вызывая повторяющуюся реаллокацию и копирование памяти».
- **Вердикт:** до Go 1.25 `io.ReadAll` начинал с 512 байт и рос через `append` (рост `append` — не строгое удвоение). С **Go 1.26** реализация другая: куски растущего размера собираются отдельно и в конце один раз копируются в срез точного размера.
- **Доказательство:** Go 1.26 release notes (`io`): «ReadAll now allocates less intermediate memory and returns a minimally sized final slice. It is often about two times faster while typically allocating around half as much total memory». go1.27.1 `src/io/io.go`, `ReadAll`: «Build slices of exponentially growing size, then copy into a perfectly-sized slice at the end» (по брифу; строку повторно не выводил).
- **Предлагаемая правка:** «Функция `io.ReadAll` не знает размера потока заранее. До Go 1.25 она начинала с буфера 512 байт и наращивала его через `append`, копируя накопленное при каждом росте. С Go 1.26 она собирает куски растущего размера и один раз копирует их в срез точной длины — примерно вдвое меньше памяти. Но и так она читает всё до EOF: без ограничения (`io.LimitReader`, `http.MaxBytesReader`) это риск OOM». Формулу 142 — убрать или пометить «до Go 1.26».

### J-059 — PARTIALLY CORRECT
- **Где / цитата:** ст. 5:168 — заголовок «Атомарность и права доступа»; 171 — «`os.WriteFile` атомарно передает режим доступа в системный вызов `open(2)`».
- **Вердикт:** передача режима в `open(2)` при создании действительно закрывает окно между созданием и `chmod`. Но: (1) запись не атомарна — сбой посередине оставит усечённый файл; (2) `perm` действует только при **создании**, существующий файл сохраняет свои права; (3) режим фильтруется `umask`.
- **Доказательство:** go1.27.1 `src/os/file.go`, `WriteFile`: `OpenFile(name, O_WRONLY|O_CREATE|O_TRUNC, perm)`, затем `f.Write`, `f.Close`. `man 2 open`: mode применяется только при `O_CREAT` для нового файла и маскируется umask.
- **Предлагаемая правка:** заголовок — «Права доступа при создании». Добавить: «`perm` применяется только к новому файлу, с учётом `umask`; права существующего файла `WriteFile` не меняет. Сама запись не атомарна: при сбое останется усечённый файл. Для атомарной замены пишите во временный файл в том же каталоге, вызывайте `Sync`, затем `os.Rename`».

### J-060 — INCORRECT
- **Где / цитата:** ст. 5:186 — «…`filepath.WalkDir`, который вызывает callback на каждый элемент, не загружая всё содержимое в RAM».
- **Вердикт:** `WalkDir` на каждый каталог вызывает `os.ReadDir` — читает **все** записи каталога в память и сортирует их. Для каталогов-гигантов — `(*os.File).ReadDir(n)` или `Readdirnames(n)` с `n > 0` порциями.
- **Доказательство:** go1.27.1 `src/path/filepath/path.go:319` — `dirs, err := os.ReadDir(path)` в `walkDir`.
- **Предлагаемая правка:** «Для каталогов-гигантов открывайте каталог (`os.Open`) и читайте записи порциями: `f.ReadDir(1000)` в цикле до `io.EOF`. `filepath.WalkDir` удобен для деревьев, но каждый каталог читает целиком и сортирует».

### J-061 — PARTIALLY CORRECT
- **Где / цитата:** ст. 6:122 — «`4096` байт выбрано как безопасный компромисс (размер стандартной страницы памяти x86/ARM). Но для сетевого IO часто эффективнее использовать размер, кратный `TCP_MSS` (1460 байт)»; 123 — «…избегать внутренних реаллокаций».
- **Вердикт:** константа `defaultBufSize = 4096` верна, обоснования в коде нет. Страница ARM64 бывает 4, 16 и 64 КБ. Сегментацию делает ядро (TSO/GSO), кратность MSS на неё не влияет. Буфер `bufio` фиксирован и не реаллоцируется — «внутренних реаллокаций» нет.
- **Доказательство:** go1.27.1 `src/bufio/bufio.go:19` — `defaultBufSize = 4096`; `NewReaderSize` — `make([]byte, max(size, minReadBufferSize))`, без роста.
- **Предлагаемая правка:** «По умолчанию буфер — 4096 байт. Для крупных потоков (файлы, сеть с большими ответами) буфер 32–64 КБ уменьшает число системных вызовов: `bufio.NewReaderSize(conn, 32*1024)`. Размер буфера фиксирован на всё время жизни Reader/Writer».

### J-062 — INCORRECT
- **Где / цитата:** ст. 6:188 — «Он копирует данные во внутренний буфер и реаллоцирует его при превышении лимита … накладные расходы на … копирование строк»; 191 — «…инициализируйте `bufio.NewWriterSize` один раз при старте сервера, привязав к соединению … чтобы избежать гонки данных».
- **Вердикт:** у `Scanner` есть `ScanBytes`, `ScanRunes` и пользовательская `SplitFunc` (например, для фреймов с длиной), так что двоичные протоколы он читает. Строки копирует только `Text()`. Для `Writer` из пула: `Reset(w)` после `Get`, `Flush()` до `Put` (`Reset` выбрасывает несброшенные данные). Причина сброса — ссылка на прежний `io.Writer` (запись в чужой ответ), а не data race. Соединений «при старте сервера» нет.
- **Доказательство:** doc `bufio.Scanner`, `bufio.Writer.Reset` («Reset discards any unflushed buffered data»); go1.27.1 `src/net/http/server.go` — `newBufioWriterSize`/`putBufioWriter` как образец пула (по брифу; не выводил).
- **Предлагаемая правка:** 188 — «`Scanner` удобен, когда поток делится на токены: строки, слова, руны или ваш формат через `SplitFunc`. Для больших сплошных двоичных данных он не нужен: используйте `io.Copy` или `bufio.Reader`». 191 — «Возьмите `*bufio.Writer` из `sync.Pool`, вызовите `bw.Reset(w)`, а перед возвратом в пул — `bw.Flush()`. Без `Reset` writer продолжит писать в ответ предыдущего запроса».

### J-063 — PARTIALLY CORRECT
- **Где / цитата:** ст. 7:43 — «Операция `string(b)` или `[]byte(s)` требует **выделения новой памяти в куче** и **копирования содержимого**».
- **Вердикт:** как правило верно, но не всегда. Неубегающий результат до 32 байт размещается во временном буфере на стеке; для сравнения, поиска в map, конкатенации и `range` компилятор копию убирает совсем.
- **Доказательство:** `testing.AllocsPerRun`: неубегающий `string(b)` для 12-байтного `b` → 0; убегающий (присвоение глобальной переменной) → 1; `m[string(b)]` → 0; `string(b) == "hello"` → 0 (см. J-006).
- **Предлагаемая правка:** «Конвертация `string(b)` или `[]byte(s)` обычно копирует данные в новую память. Компилятор избегает копии там, где строка не переживает выражение: сравнение `string(b) == "x"`, ключ в `m[string(b)]`, `for range` по `[]byte(s)`, короткие (до 32 байт) неубегающие значения. Проверяйте `-gcflags=-m` и `testing.AllocsPerRun`».

### J-064 — INCORRECT
- **Где / цитата:** ст. 7:126–127 — `C -->|До Go 1.10| D["Копирование данных:<br>make + copy"]`, `C -->|Go 1.10+| E["Unsafe cast…"]`.
- **Вердикт:** `strings.Builder` появился в Go 1.10 сразу с zero-copy `String()`. Версии с копированием не было. Реальная граница — Go 1.20: вместо `*(*string)(unsafe.Pointer(&b.buf))` стала `unsafe.String(unsafe.SliceData(b.buf), len(b.buf))` (функции `unsafe.String`/`SliceData` появились в 1.20).
- **Доказательство:** Go 1.20 release notes: «The unsafe package defines three new functions SliceData, String, and StringData»; go1.27.1 `src/strings/builder.go` — `unsafe.String(unsafe.SliceData(b.buf), len(b.buf))`. Go 1.10 release notes (появление `strings.Builder`) в сессии не открывал.
- **Предлагаемая правка:** убрать ветку «До Go 1.10». Диаграмма: `C --> E["String() без копирования: строка указывает на буфер"]`; при желании подпись «Go 1.10–1.19: unsafe-приведение заголовка; Go 1.20+: unsafe.String».

### J-065 — INCORRECT
- **Где / цитата:** ст. 8:159 — `buf := (*bufPtr)[:0] // Сбрасываем длину, сохраняем емкость`; 164 — `bufferPool.Put(bufPtr)`; 169 — «явно занулять буфер перед `Put`: `clear(*bufPtr)`»; 142 — «GC тратит … такты … на сканирование множества мелких … объектов».
- **Вердикт:** (1) если `append` перерастёт ёмкость, выросший массив теряется: в пул вернётся старый. Нужно `*bufPtr = buf[:0]` перед `Put`. (2) `len(*bufPtr) == 0`, поэтому `clear(*bufPtr)` ничего не обнулит. (3) `[]byte` не содержит указателей, GC их содержимое не сканирует; цена — в аллокации и учёте объектов.
- **Доказательство:** запуск: после `buf = append(buf, "SECRET-TOKEN"...)` и `clear(*bp)` в массиве по-прежнему `"SECRET-TOKEN"`; при росте за ёмкость `cap(*bp) = 10`, а `cap(buf) = 112` — выросший буфер в пул не вернётся.
- **Предлагаемая правка:**
  ```go
  bufPtr := bufferPool.Get().(*[]byte)
  buf := (*bufPtr)[:0]
  // ... buf = append(buf, ...) ...
  clear(buf)          // обнулить использованную часть (Go 1.21+), если там секреты
  *bufPtr = buf[:0]   // сохранить, возможно, выросший массив
  bufferPool.Put(bufPtr)
  ```
  142 — «…Каждая аллокация стоит работы аллокатора и увеличивает частоту сборок мусора. Содержимое `[]byte` сборщик не сканирует (в нём нет указателей), но учитывает каждый объект».

### J-066 — INCORRECT
- **Где / цитата:** ст. 9:97–102 — «// ✅ Хорошо: Нулевая аллокация (если буфер достаточной емкости)»; `var buf []byte` … `key := string(buf) // Единственная аллокация в конце`.
- **Вердикт:** при старте с `nil` `append` аллоцирует, плюс `string(buf)`: итог не лучше `"user:" + strconv.Itoa(id)`. Выигрыш появляется с буфером на стеке или из пула.
- **Доказательство:** `testing.AllocsPerRun`: вариант статьи — 2 аллокации; `"user:" + strconv.Itoa(id)` — 2.
- **Предлагаемая правка:**
  ```go
  // ✅ Хорошо: буфер на стеке, аллокация только у итоговой строки
  var a [32]byte
  buf := append(a[:0], "user:"...)
  buf = strconv.AppendInt(buf, int64(userID), 10)
  key := string(buf)
  ```

### J-067 — INCORRECT
- **Где / цитата:** ст. 9:8 — «Они компилируются в прямолинейный, векторизованный машинный код».
- **Вердикт:** компилятор Go не делает автовекторизацию; разбор в `strconv` — скалярный код с ветвлениями (знак, префиксы оснований, `_`, переполнение).
- **Доказательство:** go1.27.1 `src/internal/strconv/atoi.go` — посимвольный цикл с ветвлениями (прочитан в сессии выборочно). Дизассемблер не запускал; отсутствие автовекторизации в `gc` — общеизвестное свойство компилятора (экспериментальный `simd` в 1.27 — только явный API, см. release notes 1.27).
- **Предлагаемая правка:** «Они разбирают байты в простом цикле, без парсинга шаблона и без упаковки в интерфейсы».

### J-068 — INCORRECT
- **Где / цитата:** ст. 9:61 — «`FormatFloat` использует современные вариации алгоритма Драгона4 (Dragon4 / Grisu3 / Ryu) … иногда быстрее умножить, привести к `int` и разделить»; 55 — «`'f'` … Стандарт для денежных величин».
- **Вердикт:** Dragon4 в Go не использовался. До Go 1.17 печать шла через Grisu3 с запасным точным алгоритмом, с 1.17 — через Ryū. **В go1.27.1 реализация снова другая:** «fast unrounded scaling» Расса Кокса (`internal/strconv/uscale.go`, 2026) с запасным вариантом на многоразрядной десятичной арифметике. Совет «умножить, привести к `int`» теряет точность и ломает округление. Деньги в `float64` не хранят.
- **Доказательство:** go1.27.1 `src/internal/strconv/uscale.go:1–6` — «Copyright 2026 … Floating point binary↔decimal conversion by fast unrounded scaling. See "Floating-Point Printing and Parsing Can Be Simple And Fast", https://research.swtch.com/fp»; файлов `ftoaryu.go` и `eisel_lemire.go` в go1.27.1 нет (в `src/strconv/` только обёртки над `internal/strconv`). В release notes 1.26 и 1.27 изменение не упомянуто; версию, с которой работает `uscale`, по исходникам старых версий не проверял.
- **Предлагаемая правка:** 61 — «`FormatFloat` выдаёт кратчайшее представление, которое при обратном разборе даст то же число. Алгоритм менялся: Grisu3 (до Go 1.16), Ryū (Go 1.17), в новых версиях — быстрое масштабирование Расса Кокса. Для отображения с фиксированной точностью используйте `FormatFloat(x, 'f', 2, 64)`: самодельное умножение и приведение к `int` теряет точность». 55 — «`'f'`: десятичная запись (-ddd.dddd). Для денег `float` не используйте: храните целое число минимальных единиц или decimal».

### J-069 — INCORRECT
- **Где / цитата:** ст. 9:139 — «Используем `strconv.ParseInt(vals.Get("id"), 10, 64)`. Аллокаций памяти не будет».
- **Вердикт:** `URL.Query()` при каждом вызове заново разбирает `RawQuery`: map, срезы значений, распакованные строки. Без аллокаций остаётся только `ParseInt` на успешном пути.
- **Доказательство:** `testing.AllocsPerRun`: `u.Query()` для `?id=42&token=SECRET` → 4 аллокации; `strconv.ParseInt("12345", 10, 64)` → 0.
- **Предлагаемая правка:** «`strconv.ParseInt` сам не аллоцирует. Но `r.URL.Query()` при каждом вызове строит новую map: вызывайте его один раз на запрос, а в горячем пути ищите параметр прямо в `r.URL.RawQuery`».

### J-070 — INCORRECT
- **Где / цитата:** ст. 10:73 — «fmt.Println(string(s[0])) // Выведет кракозябру или пустоту, так как 208 — невалидная UTF-8 последовательность».
- **Вердикт:** `s[0]` — `byte`, `string(byte(208))` — это преобразование **числа в руну** U+00D0, результат — валидная строка `"Ð"` (2 байта `C3 90`). Невалидный фрагмент получается из `s[:1]`.
- **Доказательство:** запуск: `string(s[0])` → `"Ð"`, байты `c3 90`, `utf8.ValidString` → `true`; `s[:1]` → `"\xd0"`, `ValidString` → `false`. Spec, Conversions to and from a string type («Converting a signed or unsigned integer value to a string type yields a string containing the UTF-8 representation of the integer»).
- **Предлагаемая правка:** «`fmt.Println(string(s[0])) // Выведет «Ð»: байт 208 превращается в руну U+00D0, а не в букву «П»`; `fmt.Println(s[:1]) // половина буквы «П» — невалидный UTF-8`».

### J-071 — PARTIALLY CORRECT
- **Где / цитата:** ст. 10:180–185 — «Как эффективно перевернуть строку с поддержкой Unicode? … Конвертировать в `[]rune` …».
- **Вердикт:** разворот по рунам корректен для кодовых точек, но ломает комбинирующие знаки и ZWJ-последовательности эмодзи. Полная поддержка требует графемных кластеров (в stdlib нет).
- **Доказательство:** запуск: разворот `"e\u0301x"` → `"x́e"` (ударение «переехало» на `x`); `"👨‍💻"` → `"💻\u200d👨"`.
- **Предлагаемая правка:** добавить: «Это разворот по кодовым точкам. Буквы с комбинирующими знаками (`"e\u0301"`) и составные эмодзи (`👨‍💻`) так развалятся: для них нужен разворот по графемным кластерам (UAX #29; в stdlib его нет, есть `github.com/rivo/uniseg`)».

### J-072 — OUTDATED
- **Где / цитата:** ст. 11:177 — «лимит на процесс задается директивой ядра `ulimit -n` (значение по умолчанию часто составляет скромные 1024 слота, что катастрофически мало…)»; ст. 31:90 — то же.
- **Вердикт:** мягкий лимит 1024 по умолчанию действительно распространён. Но с Go 1.19 программа, импортирующая `os`, при старте поднимает мягкий `RLIMIT_NOFILE` до жёсткого. Для Go-сервиса значим **жёсткий** лимит (`LimitNOFILE` в systemd, настройки Docker/Kubernetes). `ulimit` — команда оболочки, а не «директива ядра».
- **Доказательство:** Go 1.19 release notes: «Go programs that import package os now automatically increase the open file limit (RLIMIT_NOFILE) to the maximum allowed value; that is, they change the soft limit to match the hard limit». go1.27.1 `src/syscall/rlimit.go:32` (по брифу).
- **Предлагаемая правка:** «Число открытых дескрипторов ограничено `RLIMIT_NOFILE`. Мягкий лимит по умолчанию часто 1024, но Go (с 1.19) при старте сам поднимает его до жёсткого. Поэтому для Go-сервиса важен жёсткий лимит: `LimitNOFILE` в systemd, `--ulimit nofile` в Docker». Ст. 31:90 — так же.

### J-073 — INCORRECT
- **Где / цитата:** ст. 11:89 — «устанавливайте `umask` процесса в `0` при старте или явно вызывайте `f.Chmod(0600)` сразу после создания, но до записи данных, чтобы избежать окна уязвимости».
- **Вердикт:** создание с `0666 &^ umask` и последующий `Chmod` — это и есть окно гонки (ст. 5:171 говорит об этом верно). Безопасно передать права при создании: umask может их только сузить. `umask(0)` действует на весь процесс и на все остальные файлы.
- **Доказательство:** `man 2 open` (mode применяется атомарно при `O_CREAT`), `man 2 umask` (атрибут процесса). Ст. 5:169–171 — то же правило.
- **Предлагаемая правка:** «Для файлов с секретами задавайте права сразу при создании: `os.OpenFile(name, os.O_CREATE|os.O_EXCL|os.O_WRONLY, 0o600)`. `umask` может только сузить права, поэтому файл никогда не будет доступен шире `0600`. Менять `umask` процесса не нужно: это глобальная настройка».

### J-074 — PARTIALLY CORRECT
- **Где / цитата:** ст. 11:180 — «Всегда используйте идиому `defer f.Close()`»; 192 — «Второй вызов вернет ошибку `os.ErrClosed`».
- **Вердикт:** для файлов на чтение — верно. Для файлов на запись ошибка `Close` (NFS, квоты, отложенное выделение блоков) теряется. Второй `Close` возвращает `*fs.PathError`, у которого `Err == os.ErrClosed`: проверка `err == os.ErrClosed` ложна, нужна `errors.Is`.
- **Доказательство:** запуск: второй `f.Close()` → `close /tmp/x…: file already closed (*fs.PathError)`, `errors.Is(err, os.ErrClosed)` → `true`, `err == os.ErrClosed` → `false`. `man 2 close`, NOTES: «Not checking the return value of close() is a common but nevertheless serious programming error … errors on a previous write(2) operation are reported only on the final close()».
- **Предлагаемая правка:** «Для файлов, открытых на запись, проверяйте ошибку `Close` (и вызывайте `Sync`, если важна сохранность): `if err := f.Close(); err != nil { return err }`. Повторный `Close` вернёт ошибку, для которой `errors.Is(err, os.ErrClosed)` истинно».

### J-075 — INCORRECT
- **Где / цитата:** ст. 12:37 — «использование `path.Join` для локальных файлов на Windows может привести к созданию файла с именем, содержащим слеши».
- **Вердикт:** Win32 API принимает `/` как разделитель и нормализует его (кроме путей с префиксом `\\?\`): `a/b` откроет `a\b`. Реальные проблемы `path` на Windows — тома и UNC-пути: `path.Base("C:\\dir\\f")` вернёт всю строку, `path.Join` не знает о `C:`. На Windows не запускал.
- **Доказательство:** запуск (Linux): ``path.Base(`C:\dir\file.txt`)`` → вся строка, `path.Dir(...)` → `"."`. Microsoft Learn, «Naming Files, Paths, and Namespaces»: «File I/O functions in the Windows API convert "/" to "\" as part of converting the name to an NT-style name, except when using the "\\?\" prefix» (по общеизвестной документации; в сессии не открывал).
- **Предлагаемая правка:** «`path` не знает о разделителе `\`, буквах дисков и UNC-путях: `path.Base("C:\\dir\\file.txt")` вернёт всю строку, `path.Dir` — `"."`. Для путей ОС используйте `path/filepath`».

### J-076 — INCORRECT
- **Где / цитата:** ст. 13:87 — «**`tar.Reader`**: Аналогично для TAR-архивов (через адаптеры или новые методы в Go 1.17+)».
- **Вердикт:** `archive/tar.Reader` — последовательный потоковый ридер, `fs.FS` не реализует ни в одной версии. С Go 1.22 есть обратное направление — `(*tar.Writer).AddFS`. `zip.Reader` реализует `fs.FS` с Go 1.16 — верно.
- **Доказательство:** `api/go1.17.txt` … `api/go1.27.txt` по `archive/tar`: только `(*Writer) AddFS(fs.FS) error #58000` и `FileInfoNames`; `api/go1.16.txt` — `archive/zip, method (*Reader) Open(string) (fs.File, error)`.
- **Предлагаемая правка:** «`tar.Reader` читает архив последовательно и `fs.FS` не реализует. Обратное есть: `tar.Writer.AddFS` (Go 1.22) упаковывает любую `fs.FS` в архив».

### J-077 — INCORRECT
- **Где / цитата:** ст. 13, диаграмма 46, 63 (`class ReadFS`, `ReadFS ..|> FS`); 99 — «Специализированные реализации (например, `os.DirFS`) могут кэшировать результаты `readdir`»; описание `GlobFS`.
- **Вердикт:** интерфейса `fs.ReadFS` нет: есть `ReadDirFS`, `ReadFileFS`, `StatFS`, `GlobFS`, `SubFS`, с Go 1.25 — `ReadLinkFS`. `fs.Glob` использует синтаксис `path.Match`, `**` не поддерживается. `os.DirFS` ничего не кэширует.
- **Доказательство:** go1.27.1 `src/io/fs/`: `stat.go:8`, `glob.go:12`, `readdir.go:15`, `sub.go:13`, `readlink.go:9`, `readfile.go:11` — `ReadFS` нет. Запуск: `fs.Glob(fsys, "**/*.go")` → `[]`, `fs.Glob(fsys, "static/*/*.go")` → `[static/sub/a.go]`.
- **Предлагаемая правка:** диаграмма — `ReadFS` заменить на `ReadFileFS`. 99 — убрать пункт о кэшировании или «реализация может кэшировать; `os.DirFS` этого не делает». В описании `GlobFS` — «шаблоны `path.Match`; `**` не поддерживается».

### J-078 — PARTIALLY CORRECT
- **Где / цитата:** ст. 13:142 — «бесшовно переключаться между … `os.DirFS` и … `embed.FS` … не меняя ни единой строчки в коде HTTP-роутинга!»; ст. 14, итог п. 6.
- **Вердикт:** через общий интерфейс `fs.FS` переключение действительно возможно. Но: `embed.FS` хранит пути с именем каталога из директивы (`static/app.css`) — нужен `fs.Sub`; у встроенных файлов нулевой `ModTime`, и `FileServer` не ставит `Last-Modified`; `http.FileServer` по умолчанию отдаёт листинг каталогов.
- **Доказательство:** запуск: `fs.Stat(embedFS, "static/a.txt").ModTime().IsZero()` → `true`; пути `embed.FS` начинаются с `static/` (вывод `WalkDir` в эксперименте c14).
- **Предлагаемая правка:** «…переключаться между `os.DirFS("static")` и `fs.Sub(embedded, "static")`: код обработчиков не меняется. Учтите отличия: у встроенных файлов нет времени изменения (не будет `Last-Modified`, кэширование по `ETag` придётся настроить самим), а `http.FileServer` показывает листинг каталогов, если в них нет `index.html`».

### J-079 — INCORRECT
- **Где / цитата:** ст. 14:87 — «страницы `.rodata` помечены флагом `MAP_SHARED`»; 95 — «Попытка изменить байт через хаки с пакетом `unsafe` … немедленно приведет к аварийному падению с сигналом `SIGSEGV`»; итог 146 — «Изменение встроенных данных в рантайме невозможно».
- **Вердикт:** для переменной `//go:embed` типа `[]byte` данные лежат в **записываемой** секции, их можно менять обычным присваиванием, без `unsafe` и без падения. Только для read-only секции: `string` и содержимое `embed.FS`. Загрузчик ELF мапит сегменты `MAP_PRIVATE`; общие физические страницы между процессами — свойство page cache для неизменённых страниц, а не `MAP_SHARED`.
- **Доказательство:** запуск: `asBytes[0] = 'Y'` для `//go:embed static/a.txt` в `[]byte` → `"Yello embedded"`, без падения; запись через `unsafe.StringData` в `//go:embed` типа `string` → `unexpected fault address … signal SIGSEGV`. `readelf -S` бинарника: `.rodata` — флаги `A` (только чтение), `.noptrdata`/`.data` — `WA`. Флаг `MAP_PRIVATE` у загрузчика ELF — по `man 2 mmap`/устройству `execve`, в сессии не проверял.
- **Предлагаемая правка:** 95 — «Данные `embed.FS` и переменных типа `string` лежат в read-only секции бинарника: запись в них через `unsafe` приведёт к `SIGSEGV`. Переменная типа `[]byte` получает собственную записываемую копию — её можно менять». 87 — «Неизменённые страницы бинарника ОС держит в page cache, поэтому несколько процессов с одним бинарником разделяют одни физические страницы». Итог п. 4 — «Read-only: `string` и `embed.FS`; `[]byte` — изменяемая копия».

### J-080 — INCORRECT
- **Где / цитата:** ст. 14:62 — «Символ `*` допустим только для выбора файлов в текущей или вложенных директориях, но не для произвольного глоббинга (`*/*.go` запрещено)»; 116 — «Компилятор выдаст ошибку `invalid go:embed directive`».
- **Вердикт:** шаблоны — синтаксис `path.Match`, `*/*.go` допустим. Реальные ограничения: нет `..`, `.`-сегментов, абсолютных путей, выхода за модуль. Пропущено частое: при встраивании каталога файлы на `.` и `_` исключаются (если нет префикса `all:`, Go 1.18). Текст ошибки для директивы в функции другой.
- **Доказательство:** запуск: `//go:embed static/*/*.go` собирается и встраивает `static/sub/a.go`; `//go:embed static` не включил `.hidden` и `_u.txt`, `//go:embed all:static` — включил; директива внутри функции → `go:embed cannot apply to var inside func`.
- **Предлагаемая правка:** 62 — «Шаблоны — как в `path.Match` (`*`, `?`, `[...]`), включая `*/*.go`. Нельзя: `..`, абсолютные пути, `**`, выход за пределы модуля. При встраивании каталога файлы, имена которых начинаются с `.` или `_`, пропускаются — используйте префикс `all:`». 116 — «`go:embed cannot apply to var inside func`».

### J-081 — PARTIALLY CORRECT
- **Где / цитата:** ст. 14:91 — «…могут приводить к вытеснению полезного кода и вызывать `instruction cache miss` (… L1i)»; 123 — «`embed.FS` … никогда не блокирует поток ОС и выполняется за константное время $O(1)$».
- **Вердикт:** данные читаются через кэш данных (L1d), а не L1i; неиспользуемые встроенные данные из-за ленивого отображения стоят только адресного пространства и размера образа. `embed.FS.Open` ищет файл бинарным поиском — O(log n). Первое обращение к ещё не загруженной странице вызывает page fault и может заблокировать поток чтением с диска. Что `embed.FS` не делает системных вызовов на открытие — верно.
- **Доказательство:** go1.27.1 `src/embed/embed.go`, `lookup`: «Binary search to find where name would be in the list» (`sortSearch`).
- **Предлагаемая правка:** 91 — «Большие встроенные данные увеличивают бинарник и время его загрузки и копирования. В кэш процессора они попадают только при чтении». 123 — «`embed.FS` не делает системных вызовов: поиск файла — бинарный поиск по отсортированному списку (O(log n)), данные читаются из памяти. При первом обращении страницу может понадобиться подгрузить с диска (page fault)».

### J-082 — INCORRECT
- **Где / цитата:** ст. 15:101 — «Начиная с Go 1.21, стандартная библиотека получила удобную вспомогательную функцию `flag.Func`».
- **Вердикт:** `flag.Func` — Go 1.16. В 1.19 появился `flag.TextVar`, в 1.21 — `flag.BoolFunc`.
- **Доказательство:** `api/go1.16.txt:226` — `pkg flag, func Func(string, string, func(string) error)`; `api/go1.19.txt:166` — `TextVar`; `api/go1.21.txt:167` — `BoolFunc`.
- **Предлагаемая правка:** «Начиная с Go 1.16, есть функция `flag.Func` (а с Go 1.21 — `flag.BoolFunc` для флагов без значения)…».

### J-083 — OPINION / NOT A FACT CLAIM
- **Где / цитата:** ст. 15:66–69 — «Парсер `flag` спроектирован с учетом аппаратных особенностей … аппаратный prefetcher … Значение записывается процессором по адресу регистра … `flag.Parse()` не совершает аллокаций памяти».
- **Вердикт:** разбор флагов выполняется один раз при старте — это не горячий путь, аппаратные доводы к нему не относятся. Фактическая ошибка: `Parse` аллоцирует (map `actual` создаётся при первом флаге, ошибки, разбор значений). Отсутствие `reflect` — заслуга интерфейса `flag.Value`, а не «записи по адресу регистра». Число аллокаций не измерял.
- **Доказательство:** go1.27.1 `src/flag/flag.go:399–400` — `actual map[string]*Flag`, `formal map[string]*Flag`.
- **Предлагаемая правка:** раздел сократить: «`flag` не использует рефлексию: каждый флаг — значение, реализующее интерфейс `flag.Value` (`String`, `Set`). Разбор выполняется один раз при старте, поэтому его скорость почти никогда не важна».

### J-084 — INCORRECT
- **Где / цитата:** ст. 16:19 — `G["Кодирование в JSON<br>через encoding/json"]`; 77 — «Передается по ссылке в метод `handler.Handle()`»; 123 — «Зависит от `encoding/json`»; врезка 185 — «`encoding/json` внутри `JSONHandler` не использует кэш рефлективных структур для анонимных `slog.Any` значений».
- **Вердикт:** `JSONHandler` сериализует базовые типы своим кодом; `json.Marshal` вызывается только для значений вида `KindAny`. `Handler.Handle(ctx, Record)` принимает `Record` **по значению**. Врезка 185 неверна: `json.Marshal` кэширует кодировщики по типу для любых значений.
- **Доказательство:** go1.27.1 `src/log/slog/json_handler.go:106` — `appendJSONValue` (свои ветки для строк, чисел, времени), 159 — `appendJSONMarshal` для прочего; `src/log/slog/handler.go:65` — `Handle(context.Context, Record) error`.
- **Предлагаемая правка:** диаграмма — «Кодирование в JSON (свой кодировщик; `encoding/json` — только для `slog.Any`)». 77 — «Передаётся по значению в `handler.Handle(ctx, r)`». 123 — «`json.Marshal` нужен только для значений `slog.Any`». Врезку 185 — «Для `slog.Any` со структурой `JSONHandler` вызывает `json.Marshal` (с рефлексией; кодировщик типа кэшируется). Для горячих путей логируйте поля по отдельности или реализуйте `slog.LogValuer`».

### J-085 — OPINION / NOT A FACT CLAIM
- **Где / цитата:** ст. 16:44 — «каждый вызов `log.Print` блокируется одним общим `sync.Mutex`. При нагрузке в 10 000+ RPS это создает катастрофический contention»; 81 — стандартные хендлеры «используют `sync.Mutex` только на время сериализации и записи».
- **Вердикт:** у `log.Logger` мьютекс держится только на время записи; форматирование и заголовок — до блокировки, в буфер из пула. Стандартные хендлеры `slog` тоже сериализуют запись мьютексом — статья признаёт это ниже. «Катастрофический» при 10 000 RPS — без измерения.
- **Доказательство:** go1.27.1 `src/log/log.go`, `output`: `getBuffer()` и `formatHeader` до `l.outMu.Lock()`; `src/log/slog/handler.go:319` — `h.mu.Lock()`.
- **Предлагаемая правка:** «У пакета `log` нет уровней и структурированных полей. Запись в выход защищена мьютексом, но форматирование выполняется до блокировки, так что конкуренция возникает в основном из-за медленного `io.Writer` — у `slog` она та же».

### J-086 — PARTIALLY CORRECT
- **Где / цитата:** ст. 16:85 — «**обязательно** оборачивайте вывод в `bufio.NewWriter()` или используйте асинхронные каналы-буферы»; пример 149–153 (`bufio.NewWriterSize(os.Stdout, 32*1024)`, комментарий «Фоновый flush буфера раз в секунду», `defer buf.Flush()`).
- **Вердикт:** буферизация снижает число системных вызовов — верно. Но при панике, `log.Fatal`, `os.Exit` и `SIGKILL` несброшенные строки теряются — как раз последние перед падением; `defer buf.Flush()` при `os.Exit` не выполнится. Фонового сброса в примере нет, а буквальная реализация комментария (вызов `Flush` из другой горутины) — гонка: `bufio.Writer` не потокобезопасен, мьютекс хендлера защищает только его собственные `Write`.
- **Доказательство:** doc `os.Exit`: «The program terminates immediately; deferred functions are not run». Код примера (строки 147–156) — горутины сброса нет.
- **Предлагаемая правка:** «Если `Write` в stdout становится узким местом (профиль это покажет), можно буферизовать вывод. Цена — потеря последних строк лога при падении. Сбрасывайте буфер при штатном завершении, а не через `defer` в `main` (он не сработает при `os.Exit` и `log.Fatal`); периодический сброс из другой горутины требует общего мьютекса с записью. В контейнерах обычно проще писать в stdout без буфера и оставить буферизацию сборщику логов».

### J-087 — INCORRECT
- **Где / цитата:** ст. 16, таблица 120–121 — «`slog.Int("k", 42)` | 0», «`slog.String("k", "v")` | 0 (если строка литерал)»; диаграмма и раздел об уровнях («мгновенный возврат» при отключённом уровне).
- **Вердикт:** `logger.Info(msg, args ...any)` упаковывает каждый `Attr` в `any` — аллокация даже при отключённом уровне. Безаллокационный путь — `LogAttrs(ctx, level, msg, attrs...)`, в статье его нет. Аргументы вычисляются до вызова при любом уровне. `slog.String` не аллоцирует для любой строки, не только литерала.
- **Доказательство:** `testing.AllocsPerRun` (JSONHandler в `io.Discard`, уровень Info): `lg.Info("m", slog.Int("k", n))` → 1; `lg.Debug(...)` (отключён) → 1; `lg.LogAttrs(ctx, Info, …)` → 0; `LogAttrs` с Debug → 0; `slog.String("k", s)` для переменной → 0. `lg.Debug("x", "v", heavy())` — `heavy()` вызвана один раз при отключённом Debug.
- **Предлагаемая правка:** таблица — «`slog.Int`, `slog.String` | 0 | значение хранится в `Attr` без упаковки»; добавить строку «`logger.Info(msg, slog.Int(...))` | 1 на атрибут, даже при отключённом уровне | аргументы `...any`» и «`logger.LogAttrs(ctx, level, msg, attrs...)` | 0 | для горячих путей». В раздел об уровнях — «Аргументы вычисляются до вызова при любом уровне; тяжёлое значение откладывайте через `slog.LogValuer` или проверку `logger.Enabled(ctx, level)`».

### J-088 — INCORRECT
- **Где / цитата:** ст. 16:181 — «Отсутствие `context.Context` в `slog` API | Нет встроенного `slog.FromContext`».
- **Вердикт:** контекст в API есть: `InfoContext`, `DebugContext` и др., `Log(ctx, …)`, `LogAttrs(ctx, …)`, `Handler.Handle(ctx, r)`. Нет только функции, достающей логгер из контекста.
- **Доказательство:** go1.27.1 `src/log/slog/handler.go:65` — `Handle(context.Context, Record) error`; `go doc log/slog Logger` — методы `InfoContext`, `LogAttrs(ctx …)` (не выводил отдельно, но `LogAttrs(ctx, …)` вызывался в эксперименте J-087).
- **Предлагаемая правка:** «Логгер не хранится в `context` | В `slog` нет `FromContext`: контекст передаётся в `InfoContext`/`LogAttrs` и доходит до `Handler.Handle`, но логгер из него не достаётся | Передавайте `*slog.Logger` явно или напишите хендлер, который берёт поля (trace id) из `ctx`».

### J-089 — OUTDATED
- **Где / цитата:** ст. 17:152 — «Технически они абсолютно идентичны (оба возвращают указатель на один и тот же пустой тип `emptyCtx`)»; 44 — «Все реализации (`cancelCtx`, `timerCtx`, `valueCtx`) находятся внутри пакета `context`».
- **Вердикт:** до Go 1.21 — два разных значения одного типа `*emptyCtx`; с Go 1.21 — разные типы `backgroundCtx` и `todoCtx` (встраивают `emptyCtx`, у них разный `String()`), возвращаются значениями. Смысловой вывод («разница семантическая») верен. Строка 44 неточна: `Context` — интерфейс, его реализует любой тип с четырьмя методами.
- **Доказательство:** go1.27.1 `src/context/context.go:200, 206` — `type backgroundCtx struct{ emptyCtx }`, `type todoCtx struct{ emptyCtx }`; запуск: `%T` → `context.backgroundCtx context.todoCtx` (по брифу). Код 1.20 не открывал — граница 1.21 по брифу.
- **Предлагаемая правка:** 152 — «Поведение у них одинаковое: пустой контекст, который никогда не отменяется. С Go 1.21 это разные типы (`backgroundCtx` и `todoCtx`), различаются они только строковым представлением. Разница семантическая…». 44 — «Стандартные реализации… находятся внутри пакета; но `Context` — интерфейс, и его может реализовать любой тип».

### J-090 — OPINION / NOT A FACT CLAIM
- **Где / цитата:** ст. 17:97 — «Если вам нужно передать 10+ параметров, создайте единую структуру `RequestData` и передайте её через один ключ».
- **Вердикт:** совет противоречит таблице той же статьи (строка 176 — `WithValue` для бизнес-данных плохо) и документации `context`. Арифметика верна: один ключ — один шаг поиска. Не сказано главное правило ключей: собственный неэкспортируемый тип.
- **Доказательство:** doc `context.WithValue`: «Use context Values only for request-scoped data that transits processes and APIs, not for passing optional parameters to functions … The provided key must be comparable and should not be of type string or any other built-in type»; staticcheck SA1029 — «Inappropriate key in call to context.WithValue».
- **Предлагаемая правка:** «Храните в контексте только сквозные метаданные запроса (trace id, сведения об аутентификации). Если таких значений несколько, сгруппируйте их в одну структуру под одним ключом. Ключ — собственный неэкспортируемый тип (`type ctxKey struct{}`), не строка. Бизнес-параметры передавайте аргументами».

### J-091 — PARTIALLY CORRECT
- **Где / цитата:** ст. 17:131 — «При разрыве TCP-соединения клиентом, контекст немедленно отменяется»; пример 134–142 (`result, err := db.QueryContext(ctx, "SELECT ...")`).
- **Вердикт:** обрыв соединения обнаруживает фоновое чтение, которое в HTTP/1.x запускается только после того, как тело запроса прочитано: «немедленно» не гарантировано. Контекст отменяется и при возврате из `ServeHTTP`. Пример не компилируется: `result` объявлена и дальше не используется (строки 138–147 — до конца функции), а `rows.Close()` нет. Поведение фонового чтения экспериментом не проверял.
- **Доказательство:** doc `http.Request.Context`: «For incoming server requests, the context is canceled when the client's connection closes, the request is canceled (with HTTP/2), or when the ServeHTTP method returns».
- **Предлагаемая правка:** «`r.Context()` отменяется, когда сервер замечает, что клиент закрыл соединение (в HTTP/1.1 — обычно после того, как тело запроса прочитано), при отмене потока в HTTP/2 и после возврата из обработчика». В примере — `rows, err := db.QueryContext(...)` и `defer rows.Close()`.

### J-092 — OUTDATED
- **Где / цитата:** ст. 18:65 — «интегрированы … через глобальную кучу таймеров `runtime.timers`»; 68–69 — «min-heap (двоичную кучу) … Поток `sysmon` … или сам планировщик … проверяет корень кучи».
- **Вердикт:** с Go 1.14 таймеры хранятся в кучах на каждом P; в go1.27.1 — `p.timers` (тип `timers` с полем `heap []timerWhen`), запускает их планировщик, `sysmon` лишь будит. Арность кучи (четверичная) по исходнику не перепроверял. Go 1.23 переделал таймеры каналов: они попадают в кучу только когда кто-то ждёт на канале.
- **Доказательство:** go1.27.1 `src/runtime/time.go:54` — «Each P has a heap of pointers to timers that it manages»; 136–158 — `type timers struct { … heap []timerWhen … }`; `src/runtime/runtime2.go:893` — поле `timers timers` в `p`. Go 1.23 release notes (Timer/Ticker changes).
- **Предлагаемая правка:** «…интегрированы в планировщик: у каждого логического процессора P своя куча таймеров. Планировщик проверяет её при поиске работы и запускает наступившие таймеры; `sysmon` лишь подстраховывает, если все потоки заняты. С Go 1.23 таймер, на канале которого никто не ждёт, в куче не держится».

### J-093 — INCORRECT
- **Где / цитата:** ст. 18:34 — `ext int64 // Unix-секунды (для wall)…`; 38 — «Сравнение `t1 == t2` и вычисление разницы `t1.Sub(t2)` **всегда используют monotonic**»; 44 — «Тип `time.Duration` — это прямой псевдоним типа `int64`».
- **Вердикт:** `==` сравнивает поля структуры (`wall`, `ext`, `loc`) и даёт `false` для одного момента в разных `Location` или с monotonic и без него. `Equal` и `Sub` используют monotonic, только если он есть **у обоих** значений. Без monotonic `ext` хранит секунды с 1 января года 1, а не Unix-секунды. `Duration` — определённый тип `type Duration int64`, не псевдоним (`=`).
- **Доказательство:** запуск: `t1 == t1.In(FixedZone)` → `false`, `Equal` → `true`; `t1 == t1.Round(0)` → `false`, `Equal` → `true`; `reflect.TypeOf(time.Second).Name()` → `Duration`. go1.27.1 `src/time/time.go:915` — `type Duration int64`. Комментарий к `Time` о смысле `ext` — по брифу (не выводил).
- **Предлагаемая правка:** 34 — «`ext` — монотонные наносекунды с момента старта процесса (если есть monotonic) или секунды с 1 января года 1 (если нет)». 38 — «`t1.Sub(t2)`, `Before`, `After`, `Equal` используют монотонные часы, если они есть у обоих значений. Оператор `==` сравнивает поля структуры и для одного и того же момента может дать `false` — сравнивайте через `Equal`». 44 — «`time.Duration` — отдельный тип на основе `int64` (`type Duration int64`)».

### J-094 — OUTDATED
- **Где / цитата:** ст. 18:91 — «// ❌ ПЛОХО: Создает новый таймер на каждой итерации -> утечка в runtime.timers + GC»; 75, 102, 110 — `t.Reset(time.Second) // В Go 1.23+ Reset безопасен напрямую (канал unbuffered)`; итог 158.
- **Вердикт:** «канал небуферизованный» верно (скаут ошибся). Но: (1) для Go 1.23+ `time.After` в цикле — лишняя аллокация на итерацию, а не утечка: неиспользуемый таймер собирает GC. (2) Новая семантика в тулчейнах **1.23–1.26** включается строкой `go 1.23`+ в `go.mod` (иначе — старое поведение, `GODEBUG=asynctimerchan`). (3) С **Go 1.27** настройка удалена: каналы таймеров небуферизованы всегда, независимо от `go.mod`.
- **Доказательство:** Go 1.23 release notes: «These new behaviors are only enabled when the main Go program is in a module with a go.mod go line using Go 1.23.0 or later». Go 1.27 release notes: «The asynctimerchan GODEBUG setting … has been removed permanently. Channels created by package time are now always unbuffered (synchronous)». `src/internal/godebugs/table.go:110` — `asynctimerchan`, `Removed: 27`. Запуск на go1.27.1: `cap(time.NewTimer(time.Hour).C)` → 0 и при `go 1.27`, и в модуле с `go 1.21`.
- **Предлагаемая правка:** 91 — «// ❌ ПЛОХО: новый таймер на каждой итерации. До Go 1.23 он жил в куче таймеров до срабатывания; с Go 1.23 его соберёт GC, но аллокация на каждую итерацию остаётся». 110 — «// Go 1.23+ (при go ≥ 1.23 в go.mod; с тулчейна 1.27 — всегда): Reset безопасен без дренажа канала». Итог п. 3 — то же уточнение.

### J-095 — INCORRECT
- **Где / цитата:** ст. 18:139 — «Структура `time.Time` хранит только смещение от UTC в конкретный момент … Всегда используйте `time.UTC()` для хранения меток в БД и `time.Local()` только для вывода»; итог 161; введение 6 — «изолировать … от … скачков високосных секунд».
- **Вердикт:** `Time` хранит абсолютный момент и указатель на `*Location` (правила зоны), смещение вычисляется. `time.UTC` и `time.Local` — переменные типа `*Location`, а не функции: правильно `t.UTC()`, `t.Local()`, `t.In(loc)`. Настоящие ловушки перехода на летнее время — `Add(24*time.Hour)` не равно «следующий день», несуществующие локальные времена в `time.Date`, отсутствие базы часовых поясов в образе. Go работает с Unix-временем без високосных секунд.
- **Доказательство:** запуск: `%T` для `time.UTC` → `*time.Location`; Берлин, 2026-03-28 12:00 (накануне перехода): `Add(24h)` → `03-29 13:00`, `AddDate(0,0,1)` → `03-29 12:00`.
- **Предлагаемая правка:** «`time.Time` хранит момент времени и часовой пояс (`*Location` с правилами перехода). `Sub` считает по абсолютному времени, поэтому DST интервалы не ломает. Ломает календарная арифметика: `t.Add(24*time.Hour)` в день перехода даст другой час — для «следующего дня» используйте `t.AddDate(0, 0, 1)`. Храните метки в UTC (`t.UTC()`), для вывода — `t.In(loc)`. В минимальных образах подключите базу зон: `import _ "time/tzdata"`». Введение 6 — убрать «скачков високосных секунд».

### J-096 — OUTDATED
- **Где / цитата:** ст. 18:132 — «Используйте `time.Ticker` с коротким интервалом + `context` или новейший пакет `synctest` (Go 1.24+) для детерминированного тестирования времени без задержек».
- **Вердикт:** в Go 1.24 `testing/synctest` — эксперимент (`GOEXPERIMENT=synctest`, `synctest.Run`); стабильный пакет с `synctest.Test` — Go 1.25; в Go 1.27 добавлен `synctest.Sleep`, а `httptest.NewTestServer` даёт фейковую сеть для пузыря. `Ticker` с коротким интервалом детерминизма не даёт.
- **Доказательство:** Go 1.24 release notes: «The synctest package is experimental and must be enabled by setting GOEXPERIMENT=synctest». Go 1.25: «This package was first available in Go 1.24 under GOEXPERIMENT=synctest … The experiment has now graduated to general availability». Go 1.27: «testing/synctest.Sleep … net/http/httptest.NewTestServer».
- **Предлагаемая правка:** «Используйте `testing/synctest` (стабилен с Go 1.25): `synctest.Test(t, func(t *testing.T) {...})` запускает код с виртуальными часами, и `time.Sleep(time.Hour)` внутри выполняется мгновенно. Короткий `Ticker` тест не ускоряет и не делает детерминированным».

### J-097 — INCORRECT
- **Где / цитата:** ст. 19:157 — «Если блокировка критической секции длительна, планировщик Go … может порождать новые системные потоки M. Это приводит к явлению **Thread Thrashing**»; итог 198.
- **Вердикт:** горутина, ждущая `Mutex`, паркуется и поток не держит — из-за этого потоки не множатся. Новые M появляются, когда горутины блокируются в системных вызовах или cgo, например, при дисковом I/O под мьютексом. Совет держать секцию короткой верен, механизм — нет.
- **Доказательство:** см. J-017 (парковка в `semacquire1` без системного вызова); `src/runtime/proc.go` — передача P при блокирующем системном вызове (`retake`, строки 6736–6760).
- **Предлагаемая правка:** «Горутины, ждущие мьютекс, паркуются и потоки ОС не занимают. Но если внутри критической секции выполняется блокирующий системный вызов (дисковый I/O, cgo), владелец мьютекса занимает поток, а планировщик для остальных горутин заводит новые. Поэтому никакого I/O под `mu.Lock()`».

### J-098 — INCORRECT
- **Где / цитата:** ст. 20:13 — «**ARM64**: пара инструкций `LDREX` / `STREX` … или инструкции LSE (`LDADD`, `CAS`)»; итог 174 — только x86-инструкции.
- **Вердикт:** `LDREX/STREX` — 32-битный ARM. На ARM64 — `LDXR/STXR` (в Go — с семантикой acquire/release `LDAXR/STLXR`), при поддержке LSE — `LDADDAL`, `CASAL` и др. Итог стоит оговорить «на x86-64».
- **Доказательство:** go1.27.1 `src/internal/runtime/atomic/atomic_arm64.s:140–141, 164–165, 188–189` — `LDAXRB/STLXRB`, `LDAXRW/STLXRW`, `LDAXR/STLXR`; `LDREX` встречается в `atomic_arm.s` (13 раз).
- **Предлагаемая правка:** 13 — «**ARM64**: пары `LDAXR`/`STLXR` (load-acquire exclusive / store-release exclusive) или атомарные инструкции LSE (`LDADDAL`, `CASAL`), если процессор их поддерживает. **ARM (32 бита)**: `LDREX`/`STREX`». Итог п. 1 — «…(на x86-64 — `LOCK CMPXCHG`, `LOCK XADD`)».

### J-099 — INCORRECT
- **Где / цитата:** ст. 20:157 — «При низкой и средней конкуренции `atomic` быстрее в 10–50 раз … При запредельной конкуренции … `sync.Mutex` эффективнее».
- **Вердикт:** без конкуренции `Lock` + `Unlock` — две атомарные операции, разница в единицы раз. Под конкуренцией `atomic.Add` (`LOCK XADD`, без повторов) масштабируется лучше мьютекса; проигрывать может только CAS-цикл, и в замере он тоже быстрее мьютекса.
- **Доказательство:** бенчмарк на go1.27.1, x86-64: один поток — `atomic.Int64.Add` 5,2 нс, `Mutex` счётчик 11,6 нс (×2,2); `RunParallel`, `-cpu 8` — `Add` 10,6 нс, CAS-цикл 18,3 нс, `Mutex` 37,4 нс.
- **Предлагаемая правка:** «Без конкуренции `atomic` быстрее мьютекса в несколько раз (замер: ~2×), под конкуренцией разрыв растёт (~3,5× на 8 ядрах). Атомики не умеют ждать и защищают одно значение. Если нужно согласованно изменить несколько полей или долгий CAS-цикл постоянно проигрывает, нужен мьютекс».

### J-100 — INCORRECT
- **Где / цитата:** ст. 20:148 — «В Go с автоматическим GC и `atomic.Pointer` проблема ABA практически сведена на нет, так как адреса памяти освобожденных структур не переиспользуются мгновенно. Для примитивных типов используйте версионирование … или метод `atomic.Swap`».
- **Вердикт:** вывод частично верен, причина — нет. Пока горутина держит указатель `old`, объект достижим, и GC его не освободит — ABA через переиспользование памяти для `atomic.Pointer` невозможен. «Скорость переиспользования» тут ни при чём. Логический ABA остаётся: тот же узел вынули и вставили обратно (стек Трайбера с повторной вставкой). `Swap` — безусловная замена, ABA он не решает. Эксперимент не ставил: вывод из модели памяти и устройства GC.
- **Доказательство:** Go Memory Model (`doc/go_mem.html`), семантика GC: достижимый объект не освобождается (общеизвестно; специального теста не запускал).
- **Предлагаемая правка:** «С `atomic.Pointer` ABA через повторное использование памяти невозможен: пока у горутины есть указатель на узел, сборщик мусора его не освободит. Логический ABA остаётся, если тот же узел возвращают в структуру повторно. Защита — не переиспользовать узлы или добавить счётчик версий (указатель на неизменяемую пару «значение + версия»)».

### J-101 — INCORRECT
- **Где / цитата:** ст. 21:130 — «Если `New` паникует, пул не восстанавливается, последующие `Get` падают»; 128 — «Overhead `defer` на 10-20% снижает производительность в циклах».
- **Вердикт:** паника в `New` ничего не портит: следующий `Get` снова вызовет `New`. С Go 1.14 `defer` вне цикла компилируется inline (open-coded) и стоит наносекунды; дорог только `defer` внутри цикла, и то «10–20%» не измерено. Отдельно отмечу: `defer pool.Put()` в цикле — это не «overhead», а ошибка: объекты вернутся в пул только при выходе из функции.
- **Доказательство:** запуск: первый `New` паникует (перехвачено `recover`), второй `Get` → `2` (New вызван снова). Release notes Go 1.14 об open-coded defer в сессии не открывал.
- **Предлагаемая правка:** 130 — убрать строку или «Паника в `New` прерывает `Get`, но пул остаётся рабочим: следующий `Get` снова вызовет `New`». 128 — «`defer pool.Put()` внутри цикла возвращает объекты в пул только при выходе из функции — в цикле вызывайте `Put` явно в конце итерации».

### J-102 — VERIFIED
- **Где / цитата:** ст. 21, примеры `readData`/`handleRequest` — `process(buf[:n])` перед `Put`; таблица ловушек без пункта об удержании ссылок.
- **Вердикт:** пропуск подтверждён. Если `process` сохранит срез (в канал, map, горутину), после `Put` буфер перезапишет следующий владелец — гонка и порча данных. Под детектором гонок пул намеренно выбрасывает часть объектов, чтобы такие ошибки проявлялись.
- **Доказательство:** go1.27.1 `src/sync/pool.go:104–105` — `if race.Enabled { … if runtime_randn(4) == 0 { return } }` в `Put` (часть объектов отбрасывается); doc `sync.Pool` об этом тоже говорит (не цитирую дословно).
- **Предлагаемая правка:** добавить в таблицу: «Ссылка на буфер после `Put` | Срез, сохранённый в канал, map или горутину, после `Put` перезапишет другой запрос | До `Put` скопируйте данные, которые нужны дольше (`bytes.Clone`). Не возвращайте в пул слишком большие буферы (в `fmt` порог 64 КБ), иначе пул будет держать память».

### J-103 — INCORRECT
- **Где / цитата:** ст. 22:138 — «Тред помечается как deadlocked, ОС создает новый. Лимит потоков исчерпывается»; ст. 44:204 — «Системный тред ядра остается навсегда заблокированным».
- **Вердикт:** если горутина завершается, не сняв привязку, рантайм **уничтожает** поток. Цена — пересоздание потоков, а не их накопление; «помечается как deadlocked» не соответствует ничему в рантайме. Не сказано, что вызовы `LockOSThread` вкладываются (счётчик), а горутина, запущенная из привязанной, привязку не наследует.
- **Доказательство:** doc `runtime.LockOSThread` (go1.27.1): «If the calling goroutine exits without unlocking the thread, the thread will be terminated»; «until the calling goroutine has made as many calls to UnlockOSThread as to LockOSThread».
- **Предлагаемая правка:** ст. 22:138 — «Забытый `UnlockOSThread` | Пока горутина жива, поток занят только ею; при её завершении рантайм уничтожит поток, и следующей привязке понадобится новый | Ставьте `defer runtime.UnlockOSThread()` сразу после `LockOSThread()`, если состояние потока не менялось». Ст. 44:204 — см. J-032.

### J-104 — INCORRECT
- **Где / цитата:** ст. 22:89 — «`GOMEMLIMIT` (Go 1.19+) задает жесткий лимит RSS … Это замена ручному тюнингу `GOGC`»; 88 — «Увеличение (`GOGC=200`) повышает latency, но снижает CPU overhead GC».
- **Вердикт:** `GOMEMLIMIT` — **мягкий** лимит памяти, которой управляет рантайм (куча, стеки, служебные структуры), без памяти cgo; это не RSS, и рантайм его не гарантирует. Это дополнение к `GOGC`, а не замена. Главный эффект `GOGC=200` — больше памяти, меньше CPU на сборку; влияние на хвостовую задержку неоднозначно и в документации не указано.
- **Доказательство:** Go 1.19 release notes: «The runtime now includes support for a soft memory limit. This memory limit includes the Go heap and all other memory managed by the runtime, and excludes external memory sources … small memory limits, on the order of tens of megabytes or less, are less likely to be respected». Руководство go.dev/doc/gc-guide в сессии не открывал (защита от «спирали смерти» — по брифу).
- **Предлагаемая правка:** 89 — «`GOMEMLIMIT` (Go 1.19+) — мягкий лимит памяти, которой управляет рантайм Go (куча, стеки горутин, служебные структуры; память cgo не входит). При приближении к лимиту GC запускается чаще. Он дополняет `GOGC`: например, `GOGC=off` + `GOMEMLIMIT` даёт сборку только у лимита. Запас до лимита контейнера всё равно нужен». 88 — «Увеличение (`GOGC=200`) сокращает число сборок и CPU на GC ценой большего объёма кучи».

### J-105 — INCORRECT
- **Где / цитата:** ст. 22:8 — «Он не использует системные вызовы напрямую для внутренней координации»; 26 — «копирует их стеки из сегментированной памяти»; 28 — «`debug.Stack()` … работает асинхронно и не трогает другие потоки»; 30 — «Внутренний счетчик горутин (`sched.ngrun` + `sched.nmidle`)»; 119 — `Gosched` «перемещая текущую `g` в конец локальной очереди `P`».
- **Вердикт:** рантайм напрямую вызывает `futex`, `epoll_*`, `mmap`, `clone`, `rt_sigaction`. Стеки непрерывные с Go 1.4 (строка 131 той же статьи). `debug.Stack` — синхронный `runtime.Stack(buf, false)` для текущей горутины. `NumGoroutine` = `gcount()`; поля `ngrun` в `sched` нет, а `nmidle` — число простаивающих **потоков M**. `Gosched` кладёт горутину в **глобальную** очередь. Верно, что `runtime.Stack(…, true)` останавливает мир.
- **Доказательство:** go1.27.1 `src/runtime/debug/stack.go` — `Stack()` в цикле вызывает `runtime.Stack(buf, false)`; `src/runtime/debug.go:179–180` — `NumGoroutine` → `gcount(false)`; `src/runtime/runtime2.go:944` — `nmidle int32 // number of idle m's waiting for work`; `src/runtime/proc.go:4345–4353` (`goschedImpl`) — `globrunqput(gp)` (кроме вытеснения ради STW); `src/runtime/mprof.go:1359, 1581` — `stopTheWorld(stwGoroutineProfile)`; `src/runtime/lock_futex.go`, `netpoll_epoll.go` — прямые системные вызовы.
- **Предлагаемая правка:** 8 — «Рантайм линкуется в бинарник и обращается к ядру напрямую (без libc на Linux): `futex`, `epoll`, `mmap`, `clone`…». 26 — «…копирует их стеки». 28 — «`debug.Stack()` снимает стек только текущей горутины и мир не останавливает». 30 — «`runtime.NumGoroutine()` считает горутины по счётчикам планировщика без блокировок; результат — мгновенный снимок». 119 — «…ставит текущую горутину в глобальную очередь и отдаёт поток другим. С Go 1.14 плотные циклы вытесняются асинхронно, и `Gosched` в них почти не нужен».

### J-106 — INCORRECT
- **Где / цитата:** ст. 23:87 — «Попытка разыменовать `nil` указатель через рефлексию вызывает панику, а не возвращает `zero value`».
- **Вердикт:** `Indirect` и `Elem` на nil-указателе возвращают нулевой `Value` (`IsValid() == false`), паники нет. Паника — при дальнейших `.Int()`, `.Field()` и т. п. Совет проверять `IsNil` верен. `reflect.Ptr` — старое имя, актуальное `reflect.Pointer` (Go 1.18).
- **Доказательство:** запуск: `reflect.Indirect(reflect.ValueOf((*int)(nil))).IsValid()` → `false`; `.Elem().IsValid()` → `false`; паники нет.
- **Предлагаемая правка:** «`reflect.Indirect` и `Elem()` на nil-указателе возвращают нулевой `reflect.Value` (`IsValid() == false`), а паника случится при первом обращении к нему (`.Field`, `.Int`) | Проверяйте `v.Kind() == reflect.Pointer && !v.IsNil()` до `.Elem()`».

### J-107 — INCORRECT
- **Где / цитата:** ст. 23:79 — «`reflect.DeepEqual` **не работает** с функциями, каналами и мапами корректно во всех сценариях … Для структур с полями `time.Time` или `sync.Mutex` он может вести себя непредсказуемо»; 85 — «порядок в мапе не детерминирован».
- **Вердикт:** мапы сравниваются глубоко и без учёта порядка. Поведение детерминировано и задокументировано, реальные ловушки — другие: `nil` и пустой слайс не равны (и `nil` и пустая map); функции равны только если обе `nil`; `time.Time` сравнивается по полям (одинаковый момент в разных зонах — не равен, нужен `Equal`); `NaN` не равен себе.
- **Доказательство:** запуск: `DeepEqual([]int(nil), []int{})` → `false`; две map с одинаковыми парами, вставленными в разном порядке → `true`. doc `reflect.DeepEqual` (правила для func, map, NaN — по документации, дословно не выводил).
- **Предлагаемая правка:** 79 — «`reflect.DeepEqual` сравнивает строго: `nil`-слайс не равен пустому, функции равны только если обе `nil`, `NaN` не равен самому себе, а `time.Time` сравнивается по внутренним полям (используйте `Equal`)». 85 — «Map сравниваются по содержимому, порядок не важен; слайсы — поэлементно, но `nil` ≠ `[]T{}`».

### J-108 — PARTIALLY CORRECT
- **Где / цитата:** ст. 23:43 — «Компилятор не может инлайнить код, использующий `reflect`. Вызов `v.Field(i).Interface()` транслируется в косвенный вызов функции по указателю»; 45 — «рефлексия вычисляет смещения динамически»; 44 — `.Set()` требует упаковки.
- **Вердикт:** вывод «рефлексия медленнее» верен. Неверно: `reflect.TypeOf`, `Kind`, `Value.Int` инлайнятся; `Field(i).Interface()` — прямые вызовы (косвенный — `Call`). Смещения полей хранятся в метаданных типа, а не вычисляются. Упаковка — в `Interface()` и `ValueOf`, не в `Set`.
- **Доказательство:** `go build -gcflags=-m` на `reflect.TypeOf(x).Kind()` и `v.Int()` → `inlining call to reflect.TypeOf`, `inlining call to reflect.(*rtype).Kind`, `inlining call to reflect.Value.Int`.
- **Предлагаемая правка:** «Рефлексия медленнее обычного кода: каждый шаг проверяет вид и флаги значения, `Interface()` и `ValueOf` упаковывают значения в интерфейсы (аллокация), `Call` выделяет срезы аргументов и вызывает функцию косвенно. Компилятор не может заранее подставить конкретный тип и оптимизировать код под него».

### J-109 — INCORRECT
- **Где / цитата:** ст. 24:114 — «`unsafe.Slice` с `nil` указателем и `len > 0` | Создает валидный слайс с `nil` данными, но доступ к нему вызывает панику».
- **Вердикт:** паника происходит в момент вызова, слайс не создаётся.
- **Доказательство:** запуск: `unsafe.Slice((*byte)(nil), 1)` → `runtime error: unsafe.Slice: ptr is nil and len is not zero`.
- **Предлагаемая правка:** «`unsafe.Slice(nil, n)` при `n > 0` паникует сразу (`ptr is nil and len is not zero`); `unsafe.Slice(nil, 0)` возвращает `nil`».

### J-110 — INCORRECT
- **Где / цитата:** ст. 24:48–55 — таблица «Функция → Замена legacy-подходу»: `unsafe.Sizeof` ↔ `reflect.TypeOf(x).Size()`, `Alignof`, `Offsetof`; 102 — «убедитесь, что `unsafe.Alignof(packet) == 1`»; итог 137 — «Современный Go (1.17+/1.20+)».
- **Вердикт:** `Sizeof`, `Alignof`, `Offsetof` — исходные операции с Go 1.0, их `reflect`-аналоги — не «legacy». Новое: `unsafe.Add`, `unsafe.Slice` — Go 1.17; `String`, `StringData`, `SliceData` — Go 1.20. Структура из статьи имеет выравнивание 4, packed-структур в Go нет: совет невыполним.
- **Доказательство:** запуск: `unsafe.Alignof(Packet{})` для `{uint8, uint16, uint32, uint32}` → 4, `Sizeof` → 12. Go 1.20 release notes: «three new functions SliceData, String, and StringData. Along with Go 1.17's Slice…». Spec, Package unsafe.
- **Предлагаемая правка:** таблицу разделить: «С Go 1.0: `Sizeof`, `Alignof`, `Offsetof`»; «Go 1.17: `Add`, `Slice` (вместо арифметики `uintptr` и `reflect.SliceHeader`)»; «Go 1.20: `String`, `StringData`, `SliceData` (вместо `reflect.StringHeader`)». 102 — «В Go нет упакованных (packed) структур: выравнивание полей задаёт компилятор. Сетевые форматы читайте через `encoding/binary` (`binary.Read`, `binary.BigEndian.Uint32`)».

### J-111 — INCORRECT
- **Где / цитата:** ст. 25:32 — «Для **стабильной сортировки** (`slices.SortStableFunc`) используется оптимизированный Block Merge Sort … сливает с использованием временного буфера»; 134 — «`SortStable` медленнее на ~15%»; 150 — «Pdqsort / Block Merge Sort».
- **Вердикт:** в Go стабильная сортировка — вставками блоками по 20 элементов и слияние SymMerge (Ким–Куцнер) без дополнительного буфера: O(n log n) сравнений и O(n log² n) перестановок. «Block Merge Sort» — другие алгоритмы (WikiSort, GrailSort). Разница в скорости — в разы, не 15%.
- **Доказательство:** go1.27.1 `src/slices/zsortanyfunc.go:336` — `blockSize := 20`, 348 — `symMergeCmpFunc` (по брифу; файл просматривал выборочно). Бенчмарк: 100 000 элементов по 40 байт — `SortFunc` 13,7 мс, `SortStableFunc` 43,2 мс (×3,1).
- **Предлагаемая правка:** 32 — «Для стабильной сортировки Go сортирует вставками блоки по 20 элементов, а затем сливает их алгоритмом SymMerge на месте, без дополнительной памяти. Цена — O(n·log² n) перестановок». 134 — «`SortStable` заметно медленнее (в замере на 100 000 структур — в 3 раза)». 150 — «Pdqsort / вставки + SymMerge».

### J-112 — INCORRECT
- **Где / цитата:** ст. 25, диаграмма 47 — «Малый массив < 50 элементов → Insertion Sort»; 131 — «Нарушение транзитивности … Pdqsort зацикливается или паникует»; 133 — «`NaN` … Алгоритм не может определить порядок».
- **Вердикт:** вставки — при длине ≤ 12 (`maxInsertion`); 50 — порог выбора медианы из девяти (Tukey ninther). При некорректном компараторе алгоритм завершается (страховка heapsort), результат не определён; ни зацикливания, ни паники в замере нет. `slices.Sort` и `cmp.Compare` уже упорядочивают NaN (NaN меньше любого числа); совет «обрабатывайте NaN» относится к самописным компараторам и к `sort.Float64s`/`<`.
- **Доказательство:** go1.27.1 `src/slices/zsortanyfunc.go:62` — `const maxInsertion = 12`; `src/cmp/cmp.go`, `Compare` — ветки `isNaN`. Запуск: `slices.SortFunc` на 10⁶ элементов со случайным компаратором `rand.IntN(3)-1` → завершилась за 44 мс; `slices.Sort([3, NaN, 1, NaN, 2])` → `[NaN NaN 1 2 3]`.
- **Предлагаемая правка:** диаграмма — «≤ 12 элементов». 131 — «Порядок результата не определён (алгоритм завершится, но слайс останется неотсортированным)». 133 — «`slices.Sort` и `cmp.Compare` ставят NaN в начало. В самописном компараторе на `<` NaN ломает порядок — используйте `cmp.Compare`».

### J-113 — INCORRECT
- **Где / цитата:** ст. 25:65 — «Дженерики + монотонизация»; 66 — «Инлайн компилятора»; 121 — «Функция `cmp.Compare` компилируется в инструкции `SETL`, `SETG`»; 125 — «`sort.Slice` … при каждом вызове рантайм создает замыкание, которое аллоцируется в куче»; 150; ст. 26:104 — «компилятор монотонизирует их»; 108 — `SETL/SETG`; итог 159; ст. 48:103 — «мономорфизацию дженериков».
- **Вердикт:** «монотонизация» — искажённое monomorphization; Go использует **GC shape stenciling со словарями** (ст. 25:125 сама так пишет — противоречие). Компаратор `SortFunc` передаётся значением функции и вызывается косвенно, «инлайн компилятора» его не касается. `cmp.Compare` содержит ветвления по NaN; утверждение о `SETL/SETG` дизассемблером не проверял. У `sort.Slice` аллоцируются упаковка слайса в `any` и `Swapper`, а не замыкание. `maps.Clone` делегирует рантайму, а не «make нужного размера».
- **Доказательство:** go1.27.1 `src/cmp/cmp.go` — `Compare` с `isNaN`-ветками; `src/maps/maps.go`, `Clone` → `clone(m).(M)` (рантайм); `testing.AllocsPerRun`: `sort.Slice(xs, func…)` (замыкание без захвата) → 2 аллокации, `slices.SortFunc` → 0.
- **Предлагаемая правка:** ст. 25:65 — «Дженерики (GC shape stenciling)»; 66 — «без рефлексии; компаратор вызывается через значение функции»; 121 — «Простой компаратор (`cmp.Compare` для чисел) короче и предсказуемее цепочки `if/else`» (без `SETL/SETG`); 125 — «`sort.Slice` принимает слайс как `any` и строит функцию перестановки через рефлексию — это аллокации на каждый вызов. `slices.Sort` и `SortFunc` работают с типизированным слайсом без них». Ст. 26:104 — «`maps.Clone` реализован в рантайме; `maps.Copy` — обычный цикл». Ст. 26:108, итог 159, ст. 48:103 — убрать «монотонизацию»/«мономорфизацию» и `SETL/SETG`.

### J-114 — CONTEXT-DEPENDENT
- **Где / цитата:** ст. 25:101 — «При сортировке `[]User`, где `User` занимает 40 байт … Это быстро выходит за пределы кэш-линии L1 (64 байта)»; 104 — «сортировка слайса указателей `[]*User` часто быстрее».
- **Вердикт:** арифметика неверна: 40 < 64. Совет зависит от раскладки: в моём замере указатели выиграли, потому что объекты лежали подряд в одном массиве (разыменования почти последовательные). Если объекты разбросаны по куче, разыменование в компараторе даёт промахи кэша, и картина может смениться. Без бенчмарка конкретного случая совет не обоснован.
- **Доказательство:** бенчмарк, 100 000 элементов `struct{ID, A, B int64; Name string}` (40 байт): `[]U40` — 13,7 мс, `[]*U40` (указатели в исходный массив) — 7,4 мс. Случай разбросанных объектов не мерил.
- **Предлагаемая правка:** «Каждая перестановка `[]User` копирует 40 байт, а перестановка `[]*User` — 8. Зато компаратор для указателей обращается к памяти объекта, и если объекты разбросаны по куче, это промахи кэша. Что быстрее — зависит от размера структуры и раскладки в памяти; измерьте бенчмарком».

### J-115 — INCORRECT
- **Где / цитата:** ст. 26:108 — «`cmp.Compare[T constraints.Ordered](a, b T)` … Заменяет громоздкие `if/else` при сортировке мап по ключам».
- **Вердикт:** в stdlib ограничение — `cmp.Ordered`; `constraints.Ordered` — из `golang.org/x/exp/constraints`. Мапы не сортируются; сортируют ключи. Не упомянуты `cmp.Less`, `cmp.Or` (Go 1.22).
- **Доказательство:** go1.27.1 `src/cmp/cmp.go:18` — `type Ordered interface`; `func Compare[T Ordered](x, y T) int`. Go 1.22 release notes: «The new function Or returns the first in a sequence of values that is not the zero value».
- **Предлагаемая правка:** «`cmp.Compare[T cmp.Ordered](a, b T) int` возвращает `-1`, `0` или `+1` и правильно упорядочивает NaN. Удобен в компараторах `slices.SortFunc`; несколько ключей сортировки объединяет `cmp.Or` (Go 1.22): `cmp.Or(cmp.Compare(a.Age, b.Age), cmp.Compare(a.Name, b.Name))`».

### J-116 — OUTDATED
- **Где / цитата:** ст. 26:69 — «Всегда копируйте ключи в слайс и сортируйте их, если важен порядок вывода»; раздел «Новые утилиты Go 1.21+».
- **Вердикт:** совет верен, но с Go 1.23 есть идиома в одну строку: `maps.Keys/Values/All` возвращают итераторы, `slices.Sorted` собирает и сортирует.
- **Доказательство:** Go 1.23 release notes: «Keys returns an iterator over keys in a map», «Sorted collects values from an iterator into a new slice, and then sorts the slice».
- **Предлагаемая правка:** «…Если важен порядок, отсортируйте ключи: `for _, k := range slices.Sorted(maps.Keys(m)) { … }` (Go 1.23+)».

### J-117 — OUTDATED
- **Где / цитата:** ст. 26:123–124 — «Он использует атомарные операции и разделяет данные на `read` (только чтение, lock-free) и `dirty` (требует мьютекс при miss). При частых обновлениях одних и тех же ключей `sync.Map` проигрывает `map + RWMutex`».
- **Вердикт:** схема `read`/`dirty` описывает реализацию до Go 1.23. С Go 1.24 `sync.Map` — конкурентное хеш-дерево (`HashTrieMap`); в go1.27.1 только оно, старой реализации в `src/sync/map.go` нет. Вывод о проигрыше при частых обновлениях не перепроверял; release notes 1.24 говорят обратное для изменений непересекающихся ключей.
- **Доказательство:** Go 1.24 release notes: «The implementation of sync.Map has been changed, improving performance, particularly for map modifications … GOEXPERIMENT=nosynchashtriemap». go1.27.1 `src/sync/map.go:41` — `m isync.HashTrieMap[any, any]`; `src/internal/sync/hashtriemap.go`.
- **Предлагаемая правка:** «До Go 1.23 `sync.Map` хранил две map (`read` без блокировок и `dirty` под мьютексом) и хорошо работал при редких записях. С Go 1.24 он реализован как конкурентное хеш-дерево: изменения разных ключей почти не конкурируют. Для типичного кэша с конкурентной записью он стал заметно лучше; выбирайте между ним и `map + RWMutex` по бенчмарку».

### J-118 — PARTIALLY CORRECT
- **Где / цитата:** ст. 26:21 — «`hash0` … Соль для хеширования (рандомизируется при создании)»; 141 — «`hash0` генерируется криптографически случайным образом при старте процесса … AES-NI инструкции … делает подбор вычислительно невозможным»; итог 158.
- **Вердикт:** защита от HashDoS действительно держится на секретном случайном seed. Но seed выбирается **для каждой map** (строка 21 верна, 141 ей противоречит). Хеш на AES-NI — быстрый, но не криптографический MAC: стойкость обеспечивает секретность seed, а не AES. Не упомянуты ловушки ключей: интерфейс с несравнимым динамическим типом → паника `hash of unhashable type`; ключи `NaN` создают недостижимые записи.
- **Доказательство:** go1.27.1 `src/internal/runtime/maps/map.go:220–221` — «seed is the hash seed, computed as a unique random number per map», 288, 352 — `m.seed = uintptr(rand())`. Паники с несравнимым ключом и NaN не воспроизводил.
- **Предлагаемая правка:** 141 — «Каждая map получает случайный seed хеш-функции при создании. Не зная его, злоумышленник не может заранее подобрать ключи, попадающие в одну группу. Аппаратный AES ускоряет хеширование, но защиту даёт именно секретность seed». Итог п. 5 — так же.

### J-119 — INCORRECT
- **Где / цитата:** ст. 27:149 — «Утечка памяти в `heap.Pop` | Забытый срез слайса `*h = (*h)[:n-1]` приводит к удержанию памяти | … Иначе GC не сможет собрать удаленные элементы».
- **Вердикт:** без усечения ломается сама куча (`Len` не уменьшается). Удержание памяти — в другом: после усечения в хвосте базового массива остаётся ссылка на удалённый элемент. Пример `PriorityQueue` в документации делает `old[n-1] = nil // avoid memory leak`.
- **Доказательство:** doc `container/heap`, Example (PriorityQueue): `old[n-1] = nil // don't stop the GC from reclaiming the item eventually` (по документации; дословный текст комментария не выводил).
- **Предлагаемая правка:** «Утечка памяти в `Pop` | После `*h = old[:n-1]` в хвосте массива остаётся указатель на вынутый элемент, и GC его не соберёт | Обнулите слот перед усечением: `old[n-1] = nil` (или нулевое значение)».

### J-120 — PARTIALLY CORRECT
- **Где / цитата:** ст. 28:5 — «Go использует движок **RE2**, спроектированный Рассом Коксом»; 21 — «Движок использует симуляцию NFA … В типичных случаях он работает как DFA, проходя по строке за один проход без возвратов».
- **Вердикт:** гарантии линейного времени — верно. Но `regexp` — собственная реализация на Go с гарантиями RE2, а не сам RE2 (C++, автор — Расс Кокс). DFA в Go нет: исполнители — `onepass`, ограниченный backtrack с картой посещённых состояний (линейность сохраняется) и NFA (Pike VM). Сложность — O(m·n).
- **Доказательство:** go1.27.1 `src/regexp/`: `onepass.go`, `backtrack.go`, `exec.go` — файлов DFA нет.
- **Предлагаемая правка:** 5 — «…Go использует собственную реализацию с гарантиями RE2 (автор обоих — Расс Кокс)». 21 — «Для простых выражений работает one-pass исполнитель, для коротких входов — ограниченный перебор с запоминанием посещённых состояний, иначе — симуляция NFA. Все три линейны по длине входа; время — O(размер выражения × длина входа)».

### J-121 — VERIFIED
- **Где / цитата:** ст. 28, таблица 107–111 — о классах `\w`, `\d`, `\s`, `\b` ни слова.
- **Вердикт:** пропуск подтверждён: Perl-классы в Go — только ASCII; `\w` не совпадает с кириллицей.
- **Доказательство:** запуск: `^\w+$` на «привет» → `false`; `^\p{L}+$` → `true`. doc `regexp/syntax` («`\w` word characters (== [0-9A-Za-z_])»).
- **Предлагаемая правка:** строка таблицы: «`\w`, `\d`, `\s`, `\b` и Unicode | Классы — только ASCII: `\w` не совпадёт с «привет» | Используйте `\p{L}` (любая буква), `\p{Cyrillic}`, `[\p{L}\p{N}_]`».

### J-122 — INCORRECT
- **Где / цитата:** ст. 28:74 — «Методы `FindString`, `FindAllString`, `FindStringSubmatch` всегда создают новые строки в куче»; 100–101 — «Если `logLine` будет собран заново или изменен пулом байтов, ссылки по индексам станут указывать на мусор».
- **Вердикт:** результаты — подстроки исходной строки (`s[a:b]`), данные не копируются; аллоцируются срезы результатов. Выигрыш `…Index` — в отсутствии `[]string`. Строки неизменяемы: индексы, применённые к той же строке, на «мусор» указать не могут; риск есть только для `[]byte`-вариантов при переиспользовании буфера.
- **Доказательство:** go1.27.1 `src/regexp/regexp.go:819–826` — `FindString` возвращает `s[a[0]:a[1]]`; запуск: `unsafe.StringData` результата `FindString` совпадает с адресом внутри исходной строки.
- **Предлагаемая правка:** 74 — «`FindString` возвращает подстроку исходной строки без копирования, а `FindAllString` и `FindStringSubmatch` выделяют срезы `[]string`. `…Index` возвращают только `[]int`». 100 — «Индексы относятся к конкретной строке или срезу. Если вы работаете с `[]byte` из пула, данные по этим индексам изменятся после возврата буфера. Для необязательной группы индекс равен `-1` — проверяйте его».

### J-123 — OUTDATED
- **Где / цитата:** ст. 29:155 — «Пустая структура `User{}` не считается нулевой и не пропускается. | Используйте указатели `*User` или кастомный `MarshalJSON`»; 41 — «В сообществе Go активно разрабатывается новая спецификация `encoding/json/v2`».
- **Вердикт:** про `omitempty` и структуру — верно. Но с Go 1.24 есть тег `omitzero` (учитывает `IsZero()`, решает и случай `time.Time`). `encoding/json/v2` — в stdlib: Go 1.25 — эксперимент (`GOEXPERIMENT=jsonv2`), **Go 1.27** — `encoding/json/v2` и `encoding/json/jsontext` доступны, а `encoding/json` по умолчанию работает поверх v2 (отключение — `GOEXPERIMENT=nojsonv2`).
- **Доказательство:** Go 1.24 release notes (`omitzero`); Go 1.25 release notes («GOEXPERIMENT=jsonv2»); Go 1.27 release notes: «The encoding/json package is now backed by the v2 implementation … disable it by setting GOEXPERIMENT=nojsonv2». go1.27.1 `src/internal/buildcfg/exp.go:87` — `JSONv2: true`.
- **Предлагаемая правка:** 155 — «…Используйте тег `omitzero` (Go 1.24+): поле опускается, если оно нулевое или его `IsZero()` возвращает `true`». 41 — «С Go 1.25 в стандартной библиотеке появился `encoding/json/v2` (сначала экспериментально), а с Go 1.27 `encoding/json` работает поверх новой реализации, сохраняя прежнее поведение. У v2 строже умолчания: он отвергает невалидный UTF-8 и повторяющиеся ключи».

### J-124 — INCORRECT
- **Где / цитата:** ст. 29:61 — `w.Write(data)` (`data LargePayload`); 69–71 — `var item PayloadItem; for dec.More() { dec.Decode(&item) … }`; 82 — «`json.Decoder` и `json.Encoder` работают напрямую с буфером `bufio`».
- **Вердикт:** (1) `w.Write(data)` со структурой не компилируется. (2) Для тела-массива `[...]` без предварительного `dec.Token()` первый `Decode(&item)` вернёт ошибку. (3) `Decoder` использует собственный буфер и читает значение верхнего уровня целиком перед разбором; `bufio` здесь нет. (4) См. B-01: одна переменная `item` переносит поля между объектами.
- **Доказательство:** запуск: поток `[{"A":1},{"A":2}]`, цикл `for dec.More() { dec.Decode(&it) }` без `Token()` → `json: cannot unmarshal array into Go value of type main.It`. Тип `ResponseWriter.Write([]byte)` — сигнатура интерфейса.
- **Предлагаемая правка:**
  ```go
  // ✅ Стриминг массива JSON: [{"id":1}, {"id":2}, ...]
  dec := json.NewDecoder(r.Body)
  if _, err := dec.Token(); err != nil { // открывающая '['
      http.Error(w, "bad json", http.StatusBadRequest); return
  }
  enc := json.NewEncoder(w)
  for dec.More() {
      var item PayloadItem // новая переменная на каждый элемент (см. B-01)
      if err := dec.Decode(&item); err != nil { return }
      if err := enc.Encode(item); err != nil { return }
  }
  ```
  В «плохом» примере — `json.NewEncoder(w).Encode(data)`. 82 — «`Decoder` читает поток своим буфером и разбирает значения по одному, не собирая всё тело в `[]byte`».

### J-125 — OUTDATED
- **Где / цитата:** ст. 29:157 — «Рекурсивные структуры | Бесконечная сериализация при перекрестных ссылках».
- **Вердикт:** `json.Marshal` обнаруживает цикл и возвращает ошибку (с Go 1.15, по брифу; в 1.27 — и в реализации v2).
- **Доказательство:** запуск на go1.27.1 (реализация v2 по умолчанию) и с `GOEXPERIMENT=nojsonv2`: `json.Marshal(n)` при `n.Next = n` → `json: unsupported value: encountered a cycle via *main.Node`. Версию появления проверки (1.15) не проверял.
- **Предлагаемая правка:** «Циклические ссылки | `Marshal` возвращает ошибку `encountered a cycle` | Разрывайте цикл (`json:"-"` у обратной ссылки) или сериализуйте идентификаторы вместо указателей».

### J-126 — PARTIALLY CORRECT
- **Где / цитата:** ст. 30:150 — «Не используйте `csv.Reader`, если не нужна валидация кавычек. Для чистых данных пишите кастомный парсер на `bufio.Scanner` + `bytes.Split` … Это снижает аллокации на 40-60%»; 140 — «используйте `csv.Reader.Read()` в цикле или `bufio.Scanner`».
- **Вердикт:** совет допустим только для данных, где точно нет кавычек и переводов строк внутри полей; иначе построчный разбор сломается. Штатный способ сэкономить — `csv.Reader.ReuseRecord = true`. Цифра «40–60%» без источника, не измерял.
- **Доказательство:** запуск: CSV с полем `"line1\nline2, with comma"` — `csv.Reader` → одна запись из двух полей; построчный разбор дал бы три фрагмента. `FieldsPerRecord` по умолчанию: строка с лишним полем → `record on line 2: wrong number of fields`.
- **Предлагаемая правка:** «Сначала включите `r.ReuseRecord = true`: Reader будет переиспользовать срез записи. Собственный разбор через `bufio.Scanner` оправдан только если формат гарантирует отсутствие кавычек и переводов строк внутри полей». Строка 140 — убрать «или `bufio.Scanner`».

### J-127 — INCORRECT
- **Где / цитата:** ст. 31:125–130 — `if netErr, ok := err.(net.Error); ok && netErr.Timeout() { continue }`, иначе `return`; 142 — `conn.SetReadDeadline(time.Now().Add(30 * time.Second))` до цикла; 146–158 — при `err != nil` данные `buf[:n]` не обрабатываются.
- **Вердикт:** `Timeout()` у `Accept` возможен только при `SetDeadline`, которого нет. Временные ошибки `accept` (`EMFILE`, `ENFILE`, `ECONNABORTED`) приводят к `return` — сервер навсегда перестаёт принимать соединения; `http.Server.Serve` в таких случаях ждёт с удвоением (5 мс → 1 с) и продолжает. Закрытие листенера проверяют через `errors.Is(err, net.ErrClosed)`. Один дедлайн до цикла — общий таймаут на всё соединение, а не таймаут простоя. Потеря `buf[:n]` при ошибке противоречит правилу «сначала `n`, потом `err`». Код `http.Server.Serve` по брифу, не перечитывал.
- **Доказательство:** doc `net.ErrClosed` (Go 1.16) — «returned … on a network connection that has been closed»; doc `net.Error.Temporary` — «Deprecated». Эксперимента с исчерпанием FD не ставил.
- **Предлагаемая правка:**
  ```go
  func runServer(ln net.Listener) error {
      var delay time.Duration
      for {
          conn, err := ln.Accept()
          if err != nil {
              if errors.Is(err, net.ErrClosed) {
                  return nil // листенер закрыт — штатный выход
              }
              // Временная ошибка (например, EMFILE): подождать и продолжить
              delay = min(max(2*delay, 5*time.Millisecond), time.Second)
              log.Printf("accept error: %v; retrying in %v", err, delay)
              time.Sleep(delay)
              continue
          }
          delay = 0
          go handleConnection(conn)
      }
  }
  ```
  В `handleConnection` — продлевать дедлайн перед каждым `Read` и обрабатывать `buf[:n]` до проверки `err`.

### J-128 — INCORRECT
- **Где / цитата:** ст. 31:84 — «В `net/http` они связаны: при отмене `r.Context()` сервер автоматически вызывает `conn.Close()`, что пробуждает горутины, ждущие IO».
- **Вердикт:** связь обратная: контекст запроса отменяется, **когда** клиент закрыл соединение (или `ServeHTTP` вернулся). Отмена контекста сама соединение не закрывает и не прерывает чтение и запись обработчика, если код не передаёт `ctx` в операции.
- **Доказательство:** doc `http.Request.Context` (цитата в J-091). Исходник `conn.serve` не перечитывал.
- **Предлагаемая правка:** «В `net/http` связь обратная: когда сервер замечает, что клиент закрыл соединение, он отменяет `r.Context()`. Чтобы обработчик прервал работу, передавайте этот контекст в свои вызовы (БД, исходящие HTTP-запросы)».

### J-129 — INCORRECT
- **Где / цитата:** ст. 31:165 — «До Go 1.14 DNS-резолвер использовал `cgo` (`getaddrinfo`)»; 167 — «С Go 1.14+ по умолчанию используется **чисто Go'шный асинхронный резолвер**»; 67 — «две параллельные горутины, одновременно пишущие в сокет, перемешают свои байты».
- **Вердикт:** чисто-Go резолвер по умолчанию на большинстве Unix-систем — с **Go 1.5**. Выбор между ним и cgo — политика времени выполнения (`GODEBUG=netdns`, `nsswitch.conf`, ОС; на macOS и Windows используется системный). Один вызов `Write` держит блокировку записи в `poll.FD` и пишет свои байты целиком; перемешиваются сообщения из нескольких `Write`.
- **Доказательство:** Go 1.5 release notes: «A change in Go 1.5 means that on most Unix systems DNS resolution will no longer require cgo … if the system's networking configuration permits, the native Go resolver will suffice … To force cgo resolution at run time set GODEBUG=netdns=cgo … This change applies to Unix systems only». `src/internal/poll/fd_unix.go`, `Write` — `fd.writeLock()` (по брифу).
- **Предлагаемая правка:** 165–167 — «С Go 1.5 на большинстве Unix-систем по умолчанию используется резолвер на чистом Go: каждый запрос занимает горутину, а не поток. Рантайм переключается на системный `getaddrinfo` (cgo), если этого требует конфигурация (`/etc/nsswitch.conf`, особые опции `resolv.conf`); на macOS и Windows по умолчанию используется системный резолвер. Принудительно — `GODEBUG=netdns=go` или `netdns=cgo`». 67 — «Один вызов `Write` пишет свои байты целиком, но если сообщение протокола собирается из нескольких `Write`, сообщения разных горутин перемешаются. Сериализуйте запись мьютексом или отдельной горутиной-писателем».

### J-130 — PARTIALLY CORRECT
- **Где / цитата:** ст. 32:113 — «`url.JoinPath` (Go 1.19+). Он корректно обрабатывает слеши, кодирует компоненты и предотвращает Directory Traversal»; итог 151.
- **Вердикт:** слеши и кодирование — верно. Защиты от выхода нет: `..` разрешается лексически и поднимается выше базового пути.
- **Доказательство:** запуск: `url.JoinPath("https://h/v1/", "..", "admin")` → `https://h/admin`; `url.JoinPath("https://h/v1/", "a b", "c?d")` → `https://h/v1/a%20b/c%3Fd`.
- **Предлагаемая правка:** «`url.JoinPath` (Go 1.19+) склеивает сегменты с правильными слешами и экранирует их. Но `..` в сегменте поднимает путь выше базового (`JoinPath("https://h/v1/", "..", "admin")` → `https://h/admin`). Пользовательский ввод проверяйте отдельно или экранируйте `url.PathEscape`, чтобы `/` и `..` не стали сегментами пути». Итог п. 3 — «`JoinPath` для конкатенации (не защита от `..`)».

### J-131 — INCORRECT
- **Где / цитата:** ст. 32:132 — «В Go 1.17+ метод `Clone()` добавлен именно для этого … Всегда используйте `u1.Clone()`»; итог 151.
- **Вердикт:** `(*url.URL).Clone` появился в **Go 1.27**, а не 1.17. На Go 1.17–1.26 совет не компилируется.
- **Доказательство:** Go 1.27 release notes: «The new URL.Clone method creates a deep copy of a URL. The new Values.Clone method creates a deep copy of Values». `api/go1.27.txt:285` — `pkg net/url, method (*URL) Clone() *URL #73450` (по брифу).
- **Предлагаемая правка:** «Простое копирование `u2 := *u1` копирует указатель на `Userinfo`: оба URL будут ссылаться на одну структуру. С Go 1.27 есть `u1.Clone()` (глубокая копия). В старых версиях копируйте вручную: `u2 := *u1; if u1.User != nil { ui := *u1.User; u2.User = &ui }`». Итог — «`Clone()` (Go 1.27+)».

### J-132 — INCORRECT
- **Где / цитата:** ст. 33:154 — «HTTP/2 Head-of-Line Blocking | Один медленный запрос блокирует мультиплексированный поток | В Go 1.22+ исправлено. Для старых версий используйте `GODEBUG=http2server=0`».
- **Вердикт:** HOL-блокировка HTTP/2 на уровне TCP присуща протоколу поверх TCP и в приложении не «исправляется». В release notes Go 1.22 исправлений HTTP/2 по HOL нет. Близкое по смыслу изменение — в **Go 1.27**: сервер HTTP/2 учитывает приоритеты клиента (RFC 9218) вместо round-robin. `GODEBUG=http2server=0` просто отключает HTTP/2.
- **Доказательство:** Go 1.22 release notes (раздел `net/http` — routing, cgi, Content-Length, FileServerFS; о HTTP/2 ничего). Go 1.27 release notes: «HTTP/2 server now accepts client priority signals, as defined in RFC 9218 … Server.DisableClientPriority».
- **Предлагаемая правка:** «HTTP/2 и потеря пакетов | Все потоки идут по одному TCP-соединению: потеря пакета задерживает все запросы на нём (HOL на уровне TCP) | Это свойство HTTP/2 поверх TCP; решает HTTP/3 (QUIC). В Go 1.27 сервер HTTP/2 учитывает приоритеты клиентов (RFC 9218), но TCP-блокировку это не снимает».

### J-133 — INCORRECT
- **Где / цитата:** ст. 33:151 — «`http.Client` без `Transport` | Создаются новые соединения на каждый запрос, лимит FD исчерпывается»; 57 — «// ❌ Смерть для production: нет таймаутов, нет ограничения на редиректы».
- **Вердикт:** при `Transport == nil` используется `http.DefaultTransport` — с пулом соединений, таймаутом подключения 30 с и `TLSHandshakeTimeout` 10 с. Нет только общего `Client.Timeout`. Редиректы по умолчанию ограничены десятью.
- **Доказательство:** запуск: `&http.Client{}`, три запроса подряд → `GotConnInfo.Reused`: `[false true true]`; сервер с бесконечным редиректом → `stopped after 10 redirects`. go1.27.1 `src/net/http/transport.go`, `DefaultTransport`: `Timeout: 30 * time.Second`, `TLSHandshakeTimeout: 10 * time.Second`.
- **Предлагаемая правка:** 151 — «`http.Client` без `Timeout` | Запрос может висеть бесконечно: у `DefaultTransport` есть таймауты подключения и TLS, но нет ограничения на ожидание ответа | Задавайте `Client.Timeout` или контекст с дедлайном». 57 — «// ❌ Нет общего таймаута на запрос».

### J-134 — INCORRECT
- **Где / цитата:** ст. 33:50 — «`r.Context()` содержит `http.responseContext` … При обрыве TCP-соединения … или таймауте `ReadTimeout`, контекст закрывается. Все операции внутри хендлера, использующие `ctx`, мгновенно прерываются»; 18 — «Переменные в путях: `PathValue(r, "id")`».
- **Вердикт:** типа `responseContext` в `net/http` нет. `ReadTimeout`/`WriteTimeout` ставят дедлайн на соединение, но контекст сами не отменяют (контекст с дедлайном даёт `http.TimeoutHandler`). `PathValue` — метод: `r.PathValue("id")`. Поиск по исходникам на `responseContext` не делал; вывод — по документации `Request.Context`.
- **Доказательство:** doc `http.Request.Context` (цитата в J-091); запуск в эксперименте B-04: `r.PathValue("id")` → `id=42`.
- **Предлагаемая правка:** 50 — «`r.Context()` отменяется, когда клиент закрыл соединение, при отмене потока HTTP/2 или когда обработчик вернулся. Операции, которым передан этот `ctx`, прерываются. `ReadTimeout` и `WriteTimeout` ограничивают ввод-вывод соединения, но контекст не отменяют; дедлайн для обработчика даёт `http.TimeoutHandler` или `context.WithTimeout`». 18 — «`r.PathValue("id")`».

### J-135 — INCORRECT
- **Где / цитата:** ст. 33:109–122 — `errCh` заполняется, но не читается; 139 — `log.Printf("%s %s %d %v", …, http.StatusOK, …)`; 153 — «`http.TimeoutHandler` vs `Server.Timeout`»; 5 — «поддержка HTTP/3 развивается в пакете `x/net/http3`».
- **Вердикт:** если `ListenAndServe` сразу завершится (порт занят), функция будет ждать сигнала — сервис «молча мёртв». Лог всегда печатает 200. Поля `Server.Timeout` нет (есть `ReadTimeout`, `ReadHeaderTimeout`, `WriteTimeout`, `IdleTimeout`). HTTP/3 разрабатывается в `golang.org/x/net/internal/http3` — внутренний пакет, «work in progress, not ready for production»; `x/net/http3` — служебная обвязка для тестов `net/http`.
- **Доказательство:** `go doc net/http.Server` — поля `ReadTimeout`, `ReadHeaderTimeout`, `WriteTimeout`, `IdleTimeout`; go1.27.1 `src/vendor/golang.org/x/net/internal/http3/doc.go`: «This package is a work in progress. It is not ready for production usage»; `src/vendor/golang.org/x/net/http3/http3.go` — только `go:linkname`-функции для `net/http_test`.
- **Предлагаемая правка:** в `runGracefulServer` — `select { case err := <-errCh: return err; case <-quit: }` перед `Shutdown`, после `Shutdown` — дождаться `<-errCh`. Middleware — обёртка `ResponseWriter`, запоминающая статус:
  ```go
  type statusWriter struct { http.ResponseWriter; status int }
  func (w *statusWriter) WriteHeader(c int) { w.status = c; w.ResponseWriter.WriteHeader(c) }
  ```
  и лог `sw.status`; при `recover` пробрасывать `http.ErrAbortHandler` (`if rec == http.ErrAbortHandler { panic(rec) }`). 153 — «`http.TimeoutHandler` vs таймауты `http.Server`». 5 — «(HTTP/3 разрабатывается в `golang.org/x/net/internal/http3` и пока не готов к использованию)».

### J-136 — INCORRECT
- **Где / цитата:** ст. 34:76 — «В Go `Transport` включает `SetKeepAlive(true)` и `SetKeepAlivePeriod(3 * time.Minute)` по умолчанию».
- **Вердикт:** TCP keep-alive включает `net.Dialer`, а не `Transport`. `DefaultTransport` задаёт `KeepAlive: 30 * time.Second`; при нулевом `Dialer.KeepAlive` используется 15 с. Пример той же статьи ставит 30 с — противоречие. С Go 1.23 есть `net.KeepAliveConfig`.
- **Доказательство:** go1.27.1 `src/net/dial.go:20` — `defaultTCPKeepAliveIdle = 15 * time.Second`; `src/net/http/transport.go`, `DefaultTransport` — `KeepAlive: 30 * time.Second`. Go 1.23 release notes: «The new type KeepAliveConfig permits fine-tuning the keep-alive options for TCP connections». Происхождение «3 минут» (старый `tcpKeepAliveListener`) не проверял.
- **Предлагаемая правка:** «TCP keep-alive в Go включает `net.Dialer`: по умолчанию первая проба через 15 с простоя, `DefaultTransport` задаёт 30 с. Тонкая настройка (интервал, число проб) — `net.KeepAliveConfig` (Go 1.23)».

### J-137 — INCORRECT
- **Где / цитата:** ст. 34:10 — «Внутренние структуры пула (`connPool`, `dialing`, `idleConnCh`)»; 16–27 — «Внутренний пул (`http.connPool`)», структура с `dialing`; 83 — «Лимит `MaxIdleConnsPerHost` (по умолчанию 2) быстро вызывает очередь `dialing`»; 84 — «`http2.ConfigureTransports` … увеличивая `MaxIdleConns` и `MaxConnsPerHost`»; 111 — «// Лимит одновременных диалов на хост»; 129 — «Клонирование небезопасно, если оригинал уже использовался».
- **Вердикт:** типов `connPool` и полей `dialing`, `idleConnCh` нет: в `Transport` — `idleConn`, `idleConnWait`, `idleLRU`, `connsPerHostWait`, ключ — `connectMethodKey`. `MaxIdleConnsPerHost` ограничивает только **простаивающие** соединения: при 100 параллельных запросах будет 100 соединений, после ответа лишние закроются. `MaxConnsPerHost` — лимит всех соединений (включая устанавливаемые и активные), а не «диалов». `ConfigureTransports` лимиты не меняет (по брифу, исходник не открывал). `Clone()` возвращает копию настроек с пустым пулом и безопасен. `MaxIdleConnsPerHost` по умолчанию 2 — верно.
- **Доказательство:** go1.27.1 `src/net/http/transport.go:101–113` — `idleConn map[connectMethodKey][]*persistConn`, `idleConnWait`, `idleLRU connLRU`, `connsPerHostWait`; `grep connPool` — только в комментарии; `Clone()` (344) создаёт новый `&Transport{…}` с копией полей конфигурации. doc `Transport.MaxConnsPerHost`: «limits the total number of connections per host, including connections in the dialing, active, and idle states».
- **Предлагаемая правка:** схему 20–27 заменить: «`Transport` хранит простаивающие соединения в `idleConn` (по ключу схема+хост+прокси), ожидающих — в `idleConnWait`; лимит `MaxConnsPerHost` — через очередь `connsPerHostWait`». 83 — «При 100 параллельных запросах HTTP/1.1 откроет 100 соединений; после ответов в пуле останутся только `MaxIdleConnsPerHost` (по умолчанию 2), остальные закроются — при следующем всплеске их придётся открывать заново». 84 — убрать про лимиты. 111 — «// Лимит всех соединений на хост (активных, простаивающих и устанавливаемых)». 129 — «`Clone()` безопасен: копирует настройки, пул у копии пустой».

### J-138 — OUTDATED
- **Где / цитата:** ст. 34:69–70 — «**Непрочитанное тело запроса.** Если вы … игнорируете `resp.Body`, соединение **никогда не вернется в пул** … Всегда закрывайте тело: `defer resp.Body.Close()` или читайте до EOF»; итог 143.
- **Вердикт:** речь о теле **ответа**. До Go 1.26 `Close()` без дочитывания в HTTP/1.x закрывал соединение, и keep-alive не работал: нужно было дочитать, затем закрыть («или» неверно). С **Go 1.27** `Close()` сам дочитывает небольшой остаток (до консервативного предела), и соединение переиспользуется; для больших тел соединение по-прежнему закрывается.
- **Доказательство:** Go 1.27 release notes: «HTTP/1 Response.Body now automatically drains any unread content upon being closed, up to a conservative limit, to allow better connection reuse». Запуск на go1.27.1, `Close()` без чтения, `httptrace.GotConn.Reused`: тело 1 КБ → `[false true true]`; тело 1 МБ → `[false false false]`.
- **Предлагаемая правка:** «**Незакрытое тело ответа.** Если не закрыть `resp.Body`, соединение не вернётся в пул. Закрывайте всегда: `defer resp.Body.Close()`. Чтобы соединение переиспользовалось и при большом непрочитанном ответе, дочитайте остаток перед закрытием: `io.Copy(io.Discard, io.LimitReader(resp.Body, 64<<10))`. (С Go 1.27 `Close` сам дочитывает небольшой остаток.)». Итог п. 3 — «Всегда закрывайте `resp.Body`; большой непрочитанный ответ закроет соединение».

### J-139 — INCORRECT
- **Где / цитата:** ст. 35:21–29 — структура с полем `flushed`, «синхронизируя состояние через внутренние мьютексы. Это делает её потокобезопасной»; 145 — «`ResponseRecorder` не симулирует `http.Flusher` по умолчанию»; 141 — `rr.Header()` vs `rr.Result().Header`.
- **Вердикт:** мьютексов у `ResponseRecorder` нет, конкурентное использование не предусмотрено. `Flush()` он реализует и выставляет экспортируемое поле `Flushed`; `Hijacker` не реализует. Смысл `Result()` — снимок заголовков на момент первой записи.
- **Доказательство:** go1.27.1 `src/net/http/httptest/recorder.go:42–43` — `Flushed bool // Flushed is whether the Handler called Flush`, `func (rw *ResponseRecorder) Flush()`; в файле нет `sync`/`Mutex` (по брифу; grep не повторял).
- **Предлагаемая правка:** 29 — «`ResponseRecorder` записывает код, заголовки и тело в память. Он не потокобезопасен: если обработчик пишет из нескольких горутин, синхронизируйте запись сами». Структуру — с полем `Flushed bool`. 145 — «Проверка `Flush()` | `ResponseRecorder` реализует `http.Flusher` и выставляет `rr.Flushed`, но `Hijacker` не реализует | Для `Hijack` и WebSocket используйте `httptest.NewServer`».

### J-140 — INCORRECT
- **Где / цитата:** ст. 35:38 — «вызов `server.Close()` немедленно закрывает `Listener`, обрывает активные соединения»; 143 — «`NewServer` и IPv6 | На некоторых машинах `127.0.0.1` недоступен, сервер падает при старте»; 115 — «`httptest.NewTLSServer` генерирует самоподписанный сертификат на лету».
- **Вердикт:** `Close` закрывает листенер и простаивающие соединения и **ждёт** завершения активных запросов (заблокированный обработчик подвесит тест). `NewServer` сам пробует `127.0.0.1:0`, затем `[::1]:0`. Сертификат — встроенный тестовый (`internal/testcert`), не генерируется.
- **Доказательство:** go1.27.1 `src/net/http/httptest/server.go:215–225` — `net.Listen("tcp", "127.0.0.1:0")`, при ошибке `net.Listen("tcp6", "[::1]:0")`; 349 — `tls.X509KeyPair(testcert.LocalhostCert, testcert.LocalhostKey)`; 548 — `// Wait for outstanding closes to finish.` (по брифу).
- **Предлагаемая правка:** 38 — «`server.Close()` закрывает листенер и простаивающие соединения и ждёт завершения активных запросов. Обработчик, который висит, подвесит и `Close` — используйте `CloseClientConnections()`». 143 — убрать строку или «Если недоступны и `127.0.0.1`, и `::1`, `NewServer` паникует». 115 — «…использует встроенный тестовый сертификат для `127.0.0.1` и `example.com` и возвращает клиент, который ему доверяет».

### J-141 — PARTIALLY CORRECT
- **Где / цитата:** ст. 36:32 — «`goroutine` профиль … **операция с остановкой мира (STW)** на микросекунды … `block` и `mutex` профили используют атомарные счетчики в примитивах `sync`, записывая длительность блокировки только если она превысила порог `runtime.SetBlockProfileRate`».
- **Вердикт:** STW у goroutine-профиля — верно. Неверно: оба профиля `block` и `mutex` **выключены по умолчанию** — без `SetBlockProfileRate`/`SetMutexProfileFraction` эндпоинты пусты. События записывает рантайм при ожидании на семафорах и каналах, а не «атомарные счётчики в `sync`». `SetBlockProfileRate` задаёт частоту выборки (в среднем одно событие на `rate` наносекунд блокировки), а не порог; mutex-профиль управляется `SetMutexProfileFraction`.
- **Доказательство:** go1.27.1 `src/runtime/mprof.go:1359, 1581` — `stopTheWorld(stwGoroutineProfile)`; doc `runtime.SetBlockProfileRate`: «The profiler aims to sample an average of one blocking event per rate nanoseconds spent blocked»; doc `SetMutexProfileFraction`: «On average 1/rate events are reported».
- **Предлагаемая правка:** «Профили `block` и `mutex` по умолчанию выключены. Включите их при старте: `runtime.SetBlockProfileRate(rate)` (в среднем одно событие на `rate` наносекунд ожидания) и `runtime.SetMutexProfileFraction(n)` (записывается каждое n-е событие конкуренции). События записывает рантайм, когда горутина ждёт на мьютексе, канале или `select`».

### J-142 — INCORRECT
- **Где / цитата:** ст. 36:115 — «Любой может скачать дамп кучи, содержащий пароли, токены, приватные данные. | … используйте `build tag` `-tags noprof`».
- **Вердикт:** heap-профиль содержит стеки аллокаций и размеры, а не содержимое памяти. Реальные риски публичного `/debug/pprof`: `/cmdline` (аргументы, часто с секретами), `goroutine?debug=2` (стеки с аргументами функций), CPU-профили и trace на 30 секунд как DoS. Стандартного тега `noprof` нет.
- **Доказательство:** запуск: `/debug/pprof/cmdline` на `http.DefaultServeMux` (после `_ "net/http/pprof"`) → 200 и путь бинарника (аргументы командной строки отдаются целиком). Формат heap-профиля (`profile.proto`) — по документации pprof, в сессии не открывал.
- **Предлагаемая правка:** «`pprof` в production без защиты | `/debug/pprof/cmdline` отдаёт аргументы командной строки (часто с секретами), `goroutine?debug=2` — стеки всех горутин, а `profile` и `trace` позволяют нагрузить сервис | Слушайте отладочный порт только на `127.0.0.1` или за аутентификацией. Если хотите исключить pprof из релизных сборок, заведите собственный тег сборки (`//go:build !noprof` на файле с импортом)».

### J-143 — INCORRECT
- **Где / цитата:** ст. 36:67 — «Метод `expvar.Map.Set()` блокирует глобальный мьютекс»; 86 — `pprof.Handler("profile").ServeHTTP // и т.д. для каждого эндпоинта`; 95 — `pass != os.Getenv("DEBUG_PASS")`; 128 — «JFR мощный, но лицензирован для production».
- **Вердикт:** `Map.Set` — `sync.Map` плюс мьютекс списка ключей, который берётся только при добавлении **нового** ключа; глобальная блокировка — только в `Publish`. Строка 86 — выражение без вызова: пример не компилируется. Сравнение через `!=` — не за постоянное время, но главные дыры примера — B-02 и B-03. JFR открыт в OpenJDK 11 (2018) и бесплатен (JEP 328, по памяти — не проверял).
- **Доказательство:** go1.27.1 `src/expvar/expvar.go`, `Map.Set` → `v.m.Load`/`LoadOrStore`, `addKey` (`keysMu.Lock`) только для нового ключа; `Publish` → `vars.keysMu.Lock()`. Сборку примера не запускал; B-отчёт приводит ошибку `pprof.Handler("profile").ServeHTTP (value of type func(…)) is not used`, что следует из спецификации (выражение-оператор без вызова недопустимо).
- **Предлагаемая правка:** 67 — «`expvar.Map` построен на `sync.Map`: обновление существующего ключа блокировок не берёт, добавление нового — берёт мьютекс списка ключей. Для счётчиков используйте `expvar.Int`/`Float` (атомарные) или `m.Add(key, delta)`». 86 — удалить строку. 95 — `subtle.ConstantTimeCompare` и отказ от старта при пустом пароле (B-02). 128 — «JFR встроен в OpenJDK начиная с 11 и бесплатен».

### J-144 — INCORRECT
- **Где / цитата:** ст. 37:16 — «в современном `math/rand/v2` (Go 1.22+) стандартным быстрым генератором стал **PCG** … (а также криптографически обоснованный ChaCha8)»; 72 — «изолированным состоянием PCG»; 108 — «Внутреннее состояние PCG повреждается гонкой данных»; диаграмма `IntN → PCG`.
- **Вердикт:** глобальные функции `math/rand/v2` используют **ChaCha8** (источник рантайма с непредсказуемым seed). PCG — отдельный источник для воспроизводимых последовательностей. «Криптографически сильный» ChaCha8 не делает v2 пригодным для секретов: документация требует `crypto/rand`. В v1 `rand.Rand` — ALFG (строка 16 сама так пишет), не PCG.
- **Доказательство:** Go 1.22 release notes: «ChaCha8 is a new, cryptographically strong random number generator … ChaCha8 is the algorithm used for the top-level functions in math/rand/v2».
- **Предлагаемая правка:** 16 — «В `math/rand/v2` (Go 1.22+) глобальные функции используют ChaCha8 со случайным seed. Для воспроизводимых последовательностей есть источники `rand.NewPCG(seed1, seed2)` и `rand.NewChaCha8(seed)`. Для ключей и токенов всё равно используйте `crypto/rand`». 72, 108 — убрать «PCG» для v1 (состояние — ALFG). Диаграмму — `IntN → ChaCha8 (рантайм)`.

### J-145 — PARTIALLY CORRECT
- **Где / цитата:** ст. 37:94–95 — «// URL-safe, без padding, предсказуемая длина» + `base64.URLEncoding.EncodeToString(b)`; 109 — «Go использует `/dev/urandom` или `getrandom`, которые **никогда** не блокируются»; 91 — `if _, err := rand.Read(b); err != nil`; 24 — `sysctl(KERN_URND)`.
- **Вердикт:** (1) `URLEncoding` добавляет `=`; без него — `RawURLEncoding`. (2) `getrandom(2)` без `GRND_NONBLOCK` блокируется до инициализации CRNG ядра на раннем этапе загрузки — «никогда» шире правды, но в работающей системе верно. (3) С Go 1.24 `crypto/rand.Read` не возвращает ошибку (при сбое процесс падает), и есть `crypto/rand.Text()`. Пункт про macOS/FreeBSD (`sysctl`) не проверял.
- **Доказательство:** запуск: `base64.URLEncoding.EncodeToString([]byte{1,2,3,4})` → `AQIDBA==`, `RawURLEncoding` → `AQIDBA`. Go 1.24 release notes: «The Read function is now guaranteed not to fail … The new Text function can be used to generate cryptographically secure random text strings». `man 2 getrandom` (поведение до инициализации пула) — по памяти, man не открывал.
- **Предлагаемая правка:** пример — `base64.RawURLEncoding` и комментарий «URL-safe, без `=`»; добавить: «С Go 1.24 проще: `rand.Text()` возвращает криптостойкую строку (26 символов base32, 128 бит)». 109 — «Go использует `getrandom` (или `/dev/urandom`). После инициализации пула ядра они не блокируются; ждать можно только в первые секунды загрузки системы». 110 — «С Go 1.24 `rand.Read` всегда возвращает `nil`».

### J-146 — INCORRECT
- **Где / цитата:** ст. 38:218 — `PreferServerCipherSuites: false, // В TLS 1.3 выбор набора шифров сервером не имеет значения`; 219 — `SessionTicketsDisabled: false, // … возобновления сессий (0-RTT/1-RTT)`; 254, 297 — «Включайте `tls.Config.SessionTicketsDisabled = false` для reuse сессий»; 204 — «Начиная с … Go (1.22+) … минимальная поддерживаемая версия — `tls.VersionTLS12`»; 236 — «**Асинхронное согласование cipher suite**».
- **Вердикт:** `PreferServerCipherSuites` — устаревшее поле без эффекта (его выставление ничего не меняет). На клиенте возобновление сессий включает `ClientSessionCache` (например, `tls.NewLRUClientSessionCache`); без него тикеты не используются, а `SessionTicketsDisabled: false` — это и так значение по умолчанию. 0-RTT (early data) `crypto/tls` для TCP-соединений не поддерживает (только через QUIC API). Минимум TLS 1.2 по умолчанию: у клиента — раньше (по брифу, 1.18), у **сервера** — с Go 1.22. «Асинхронное согласование» — бессодержательно. Не упомянут гибридный постквантовый обмен ключами (`X25519MLKEM768` по умолчанию с Go 1.24).
- **Доказательство:** doc `tls.Config` (go1.27.1): «PreferServerCipherSuites is a legacy field and has no effect»; «SessionTicketsDisabled may be set to true to disable session ticket and PSK (resumption) support. Note that on clients, session ticket support is also disabled if ClientSessionCache is nil»; «By default, TLS 1.2 is currently used as the minimum». `src/crypto/tls/handshake_client_tls13.go:364–366` — `earlyData` только в ветке QUIC (`quicRejectedEarlyData`). Go 1.22 release notes: «By default, the minimum version offered by crypto/tls servers is now TLS 1.2 … matching the behavior of crypto/tls clients». Go 1.24 release notes — `X25519MLKEM768` по умолчанию. Версию для клиента (1.18) не проверял.
- **Предлагаемая правка:**
  ```go
  tlsConfig := &tls.Config{
      MinVersion:         tls.VersionTLS12,
      ClientSessionCache: tls.NewLRUClientSessionCache(256), // возобновление сессий (1-RTT без полного рукопожатия)
  }
  transport := http.DefaultTransport.(*http.Transport).Clone() // Proxy и HTTP/2 сохраняются
  transport.TLSClientConfig = tlsConfig
  transport.TLSHandshakeTimeout = 5 * time.Second
  ```
  204 — «Клиенты и (с Go 1.22) серверы `crypto/tls` по умолчанию требуют TLS 1.2+; с Go 1.24 по умолчанию включён гибридный постквантовый обмен ключами X25519MLKEM768». 236 — «Согласование параметров: в TLS 1.3 полное рукопожатие занимает один RTT». 254/297 — «Для возобновления сессий на клиенте задайте `ClientSessionCache`; на сервере тикеты включены по умолчанию».

### J-147 — PARTIALLY CORRECT
- **Где / цитата:** ст. 38:7 — «Стандартная библиотека Go … скрывает или вытесняет сломанные примитивы (`MD5`, `SHA1`, `DES`)»; 9 — «Операции сравнения, расшифровки и проверки подписи в Go реализованы так, что время их выполнения строго инвариантно относительно секретных данных».
- **Вердикт:** «вытесняет» — частично: `crypto/md5`, `crypto/sha1`, `crypto/des`, `crypto/rc4` в stdlib есть и документированы как небезопасные; из TLS по умолчанию убраны 3DES (Go 1.23), RSA-обмен ключами и т. д. Постоянное время обеспечено для основных путей (AES-GCM с аппаратной поддержкой, ChaCha20-Poly1305, P-256, Ed25519, RSA через constant-time backend с Go 1.20), но не для всех операций; обычное сравнение `bytes.Equal` — не constant-time. Программный путь AES в 1.27 не проверял.
- **Доказательство:** Go 1.20 release notes: «crypto/rsa now uses a new, safer, constant-time backend»; Go 1.23 release notes: «3DES cipher suites were removed from the default list»; Go 1.27 release notes — удалены `tls3des`, `tlsrsakex`, `tls10server` (GODEBUG).
- **Предлагаемая правка:** 7 — «Слабые алгоритмы (`MD5`, `SHA-1`, `DES`, `RC4`) в стандартной библиотеке есть — для совместимости, с предупреждением в документации, — но в TLS по умолчанию они не используются». 9 — «Ключевые операции (AES-GCM на аппаратной поддержке, ChaCha20-Poly1305, P-256, Ed25519, RSA с Go 1.20) реализованы за постоянное время. Сравнение секретов в своём коде делайте через `subtle.ConstantTimeCompare` или `hmac.Equal`: `bytes.Equal` и `==` выходят на первом несовпадении».

### J-148 — PARTIALLY CORRECT
- **Где / цитата:** ст. 38:198 — «Генератор `crypto/rand` обеспечивает криптографическую псевдослучайность, при которой вероятность коллизии 96-битного случайного nonce пренебрежимо мала»; 267 — «Генерация больших простых чисел занимает секунды CPU».
- **Вердикт:** для одного сообщения — верно, но граница «дней рождения» ограничивает число шифрований одним ключом: NIST SP 800-38D допускает не более 2³² случайных 96-битных nonce на ключ. При больших объёмах нужны счётчик, ротация ключа или XChaCha20-Poly1305; с Go 1.24 есть `cipher.NewGCMWithRandomNonce`. Генерация RSA-2048 — десятки миллисекунд, не секунды.
- **Доказательство:** замер на go1.27.1: `rsa.GenerateKey(rand.Reader, 2048)` — в среднем 26 мс (5 прогонов). Go 1.24 release notes: «The new NewGCMWithRandomNonce function returns an AEAD that implements AES-GCM by generating a random nonce during Seal». NIST SP 800-38D § 8.3 — по памяти, документ не открывал.
- **Предлагаемая правка:** 198 — «…Случайный 96-битный nonce безопасен, пока число сообщений на один ключ невелико: NIST ограничивает его 2³² (иначе вероятность повтора становится заметной). При больших объёмах меняйте ключи или используйте XChaCha20-Poly1305; с Go 1.24 `cipher.NewGCMWithRandomNonce` генерирует nonce сам». 267 — «…занимает десятки–сотни миллисекунд CPU и сильно колеблется по времени».

### J-149 — INCORRECT
- **Где / цитата:** ст. 39:161 — «Если же разработчик вызовет `QueryRow()`, но забудет вызвать `Scan()`, соединение останется заблокированным в пуле до срабатывания финализатора GC»; ст. 40, итог п. 5 (213) — «Непрочитанный или незакрытый курсор блокирует сетевое соединение до финализации GC».
- **Вердикт:** финализаторов у `*sql.Rows`, `*sql.Row`, `*sql.Tx`, `*sql.Conn` нет. Брошенный курсор держит соединение до конца процесса или до отмены `ctx`, переданного в `QueryContext`/`BeginTx` (`awaitDone`). «До финализатора» преуменьшает серьёзность утечки.
- **Доказательство:** `grep SetFinalizer src/database/sql/*.go` без тестов — пусто (go1.27.1); `src/database/sql/sql.go:3015` — `func (rs *Rows) awaitDone(ctx, txctx, closectx context.Context)`, `2214` — `Tx.awaitDone` ждёт `<-tx.ctx.Done()`.
- **Предлагаемая правка:** ст. 39:161 — «…соединение останется занятым навсегда (финализаторов в `database/sql` нет) — пока не будет отменён контекст запроса, переданный в `QueryRowContext`». Ст. 40:213 — «…блокирует соединение, пока курсор не закрыт или не отменён его контекст».

### J-150 — PARTIALLY CORRECT
- **Где / цитата:** ст. 39:61 — «Настройка `SetConnMaxLifetime` гарантирует, что соединение будет закрыто и переоткрыто … до того, как его разорвет сетевое оборудование»; 156 — «Всегда задавайте `SetConnMaxLifetime` (обычно от 1 до 5 минут)»; ст. 40:198 — «`sql.Conn` (появившегося в Go 1.10)».
- **Вердикт:** `ConnMaxLifetime` отсчитывается от создания соединения и не зависит от простоя: короткий срок жизни помогает косвенно. От NAT/балансировщика, сбрасывающего **простаивающие** сессии, прямо защищает `SetConnMaxIdleTime` (Go 1.15) меньше таймаута простоя оборудования — его в статьях нет. Умолчания: `MaxOpenConns = 0` (без ограничения), `MaxIdleConns = 2`, срок жизни и простоя не ограничены. `sql.Conn` — Go 1.9.
- **Доказательство:** `api/go1.15.txt:30` — `(*DB) SetConnMaxIdleTime(time.Duration)`; `api/go1.9.txt:18` — `database/sql, type Conn struct`; go1.27.1 `src/database/sql/sql.go:965` — `const defaultMaxIdleConns = 2`.
- **Предлагаемая правка:** ст. 39:61 — «…Против разрыва простаивающих соединений задайте `SetConnMaxIdleTime` меньше таймаута простоя сетевого оборудования; `SetConnMaxLifetime` (возраст соединения) помогает при ротации серверов и балансировке». 156 — «Всегда задавайте `SetConnMaxIdleTime` и `SetConnMaxLifetime`. По умолчанию `MaxOpenConns` не ограничен, `MaxIdleConns = 2`». Ст. 40:198 — «Go 1.9».

### J-151 — INCORRECT
- **Где / цитата:** ст. 40:192 — «отправляйте явные команды `SAVEPOINT sp1; ... ROLLBACK TO sp1;` через `db.Exec()` или `tx.Exec()`».
- **Вердикт:** `db.Exec` берёт любое соединение пула, а не то, на котором открыта транзакция: savepoint окажется в другой сессии. Подходит только `tx.Exec`/`tx.ExecContext`.
- **Доказательство:** doc `database/sql.Tx`: все операции транзакции идут через одно соединение (по документации; дословно не выводил); устройство `db.Exec` → `db.conn(ctx, …)` берёт соединение из пула (см. J-240).
- **Предлагаемая правка:** «…через `tx.ExecContext(ctx, "SAVEPOINT sp1")` и `tx.ExecContext(ctx, "ROLLBACK TO SAVEPOINT sp1")`. Через `db.Exec` нельзя: команда уйдёт на другое соединение пула».

### J-152 — PARTIALLY CORRECT
- **Где / цитата:** ст. 40:147 — «явный вызов `db.Prepare()` часто оказывается **медленнее**, чем прямой параметризованный вызов `db.Query(…)`»; раздел «Prepare vs Query с параметрами».
- **Вердикт:** верно для разовых запросов у драйверов, реализующих `QueryerContext`/`ExecerContext` (например, pgx). Если драйвер их не реализует, `database/sql` на каждый параметризованный вызов делает Prepare + Exec + Close (2–3 обмена); для повторяющихся запросов `Stmt` быстрее. От инъекций защищают параметры, а не сам `PREPARE`. Исходник `database/sql` в этой части не перечитывал.
- **Доказательство:** по брифу: `src/database/sql/sql.go` (`queryDC`, `ctxDriverPrepare`), `driver.QueryerContext`. Отдельно не проверял.
- **Предлагаемая правка:** «Для разовых запросов `db.QueryContext` с параметрами обычно не медленнее явного `Prepare`, если драйвер умеет выполнять параметризованные запросы напрямую (интерфейс `driver.QueryerContext`; так делает pgx). Иначе `database/sql` сам готовит и закрывает стейтмент на каждый вызов. Для часто повторяемых запросов `Stmt` выгоден».

### J-153 — INCORRECT
- **Где / цитата:** ст. 41:162–164 — «// Открываем файл на запись без следования внешним ссылкам» + `os.OpenFile(cleanTarget, os.O_CREATE|os.O_WRONLY|os.O_TRUNC, mode)`; 93 — «Стандартные пакеты Go … **не фильтруют** пути автоматически».
- **Вердикт:** эти флаги **следуют** симлинкам, уже лежащим в целевом каталоге (созданным раньше или предсуществующим). Нужен `O_EXCL`/`O_NOFOLLOW` или `os.Root` (Go 1.24). Проверка префикса лексическая. С Go 1.20 есть `filepath.IsLocal` и проверка `ErrInsecurePath` в `archive/tar`/`archive/zip`, включаемая `GODEBUG=tarinsecurepath=0`/`zipinsecurepath=0` (по умолчанию выключена).
- **Доказательство:** Go 1.20 release notes: «When the GODEBUG=tarinsecurepath=0 environment variable is set, Reader.Next method will now return the error ErrInsecurePath for an entry with a file name that is an absolute path, refers to a location outside the current directory…»; `src/internal/godebugs/table.go:62, 82` — `tarinsecurepath`, `zipinsecurepath` (без смены умолчания). Поведение `O_CREAT` с симлинком — `man 2 open` (по памяти); эксперимент со `safeFilePath` в J-012 показывает тот же класс обхода.
- **Предлагаемая правка:** 162–164 — «// Не создавать поверх существующего файла или симлинка» + `os.OpenFile(cleanTarget, os.O_CREATE|os.O_EXCL|os.O_WRONLY, mode)`; лучше — распаковывать через `root, _ := os.OpenRoot(destDir)` и `root.OpenFile(header.Name, …)` (Go 1.24+), тогда выход за каталог невозможен и по симлинкам. 93 — «По умолчанию `archive/tar` и `archive/zip` пути не проверяют; с Go 1.20 проверку включает `GODEBUG=tarinsecurepath=0`/`zipinsecurepath=0`, а для своей проверки есть `filepath.IsLocal`».

### J-154 — INCORRECT
- **Где / цитата:** ст. 42:51 — «Почему разработчики DEFLATE выбрали размер скользящего окна ровно 32 КБ? … буфер в 32 КБ идеально помещается в кэш данных первого уровня (L1d)»; раздел «Влияние на GC и пулы» (оценка «десятки килобайт» на писатель).
- **Вердикт:** компрессор `flate` держит хеш-таблицы и окно — порядка мегабайта на писатель в go1.27.1, а не «десятки килобайт»; вывод о пуле только усиливается. Окно 32 КБ (DEFLATE, 1990-е) определено памятью машин того времени; L1d тогда был 8–16 КБ — это рационализация постфактум. В Go 1.27 кодировщик `flate` переписан (release notes), поэтому цифры из исходников 1.26 и раньше к 1.27 не переносятся.
- **Доказательство:** запуск на go1.27.1: `gzip.NewWriter` + `Write("hello")` + `Close` → 1 084 320 байт аллокаций (`TotalAlloc` до и после); повторное использование `Reset`+`Write`+`Close` → 0 аллокаций. Go 1.27 release notes (`compress/flate`): «Compression speed is improved … encoder implementation change». Историю выбора окна (RFC 1951) не проверял.
- **Предлагаемая правка:** 51 — «Окно DEFLATE — 32 КБ: так задано форматом (RFC 1951), и это ограничивает, на каком расстоянии алгоритм ищет повторы». Раздел о пулах — «Каждый `gzip.Writer` выделяет порядка мегабайта под хеш-таблицы и окно (замер на Go 1.27), поэтому переиспользуйте писатели через `sync.Pool` и `Reset`: повторное использование не аллоцирует».

### J-155 — VERIFIED
- **Где / цитата:** ст. 42:115–142 — `gzipMiddleware` (`strings.Contains(r.Header.Get("Accept-Encoding"), "gzip")`, только `Content-Encoding`, обёртка без `Flush`).
- **Вердикт:** дефекты подтверждены по коду примера: нет `Vary: Accept-Encoding`; `Content-Length`, выставленный обработчиком, не совпадёт со сжатым телом; `gzip;q=0` распознаётся как поддержка; `gzipResponseWriter` не реализует `http.Flusher` (ломает SSE и стриминг); `Content-Type` без явной установки `net/http` определит по сжатым байтам; нет пропуска `HEAD`, 204/304 и уже сжатых типов. Сжатие ответов HTTPS с секретами и отражённым вводом — условие атаки BREACH. Порядок `defer` (`Close` до `Put`) — корректен. Сам пример не запускал: выводы прямо следуют из кода.
- **Доказательство:** код статьи 115–142; RFC 9110 (§ 12.5.3 `Accept-Encoding` с `q=0`, § 12.5.5 `Vary`) — по памяти.
- **Предлагаемая правка:** добавить в middleware: `w.Header().Add("Vary", "Accept-Encoding")`, `w.Header().Del("Content-Length")`, разбор `Accept-Encoding` с учётом `q=0`, метод `Flush()` у обёртки (`gz.Flush(); if f, ok := w.ResponseWriter.(http.Flusher); ok { f.Flush() }`), установку `Content-Type` до сжатия; пропуск `HEAD`, 204, 304. Абзац: «Не сжимайте ответы, в которых секрет соседствует с данными из запроса (BREACH)». Либо сослаться на готовое решение (`github.com/klauspost/compress/gzhttp`).

### J-156 — INCORRECT
- **Где / цитата:** ст. 42:218 — «`gzip.NewReader` на пустом потоке | Возникает ошибка `unexpected EOF` уже при первом вызове `Read()`»; 220 — «Ошибка `flate.ErrDictionary`»; итоги — о защите от бомб при распаковке ни слова.
- **Вердикт:** `gzip.NewReader` читает заголовок сразу и на пустом потоке возвращает `io.EOF` из конструктора. `flate.ErrDictionary` не существует — есть `zlib.ErrDictionary`. Главный риск — бомба при приёме `Content-Encoding: gzip` от клиента — не упомянут.
- **Доказательство:** запуск: `gzip.NewReader(bytes.NewReader(nil))` → `EOF`. go1.27.1 `src/compress/zlib/reader.go:44–45` — `ErrDictionary = errors.New("zlib: invalid dictionary")`; в `compress/flate` такой переменной нет.
- **Предлагаемая правка:** 218 — «`gzip.NewReader` на пустом потоке | Конструктор сразу читает заголовок и возвращает `io.EOF` | Проверяйте ошибку `NewReader`». 220 — «`zlib.ErrDictionary`: поток zlib требует предустановленного словаря (`zlib.NewReaderDict`)». Добавить строку: «Распаковка недоверенных данных | 1 МБ gzip разворачивается в гигабайты | Ограничивайте объём после распаковки: `io.LimitReader(gz, max)` или `http.MaxBytesReader` поверх `gzip.Reader`».

### J-157 — INCORRECT
- **Где / цитата:** ст. 43:12 — «Рантайм Go использует оптимизированный ассемблерный вызов `syscall.ForkExec`: он клонирует текущий процесс … принудительно закрывает все унаследованные файловые дескрипторы»; 51 — «Рантайм Go закрывает в дочернем процессе абсолютно все дескрипторы, кроме стандартных потоков … и … `cmd.ExtraFiles`»; 65–67 — «Стоимость fork и COW»; ст. 11:162 — «`fork` + `execve` (или `clone`)».
- **Вердикт:** на Linux `forkExec` использует `clone(CLONE_VFORK|CLONE_VM)`: родитель ждёт `execve`, таблицы страниц не копируются, и «цена fork многогигабайтной кучи» к Go на Linux не относится (кроме случая `CLONE_NEWUSER`). `clone3` — только при `UseCgroupFD`, `CLONE_NEWTIME` и т. п. `ForkExec` — Go-код с raw-вызовами, не «ассемблерный вызов». Дескрипторы не закрываются перебором: Go открывает свои с `O_CLOEXEC`, а дескриптор без этого флага (полученный из cgo или через `syscall` без флага) потомок унаследует.
- **Доказательство:** go1.27.1 `src/syscall/exec_linux.go:307–310` — `if sys.Cloneflags&CLONE_NEWUSER == 0 && … { flags |= CLONE_VFORK | CLONE_VM }`; 314–316 — `clone3` при `sys.UseCgroupFD || flags&CLONE_NEWTIME != 0 || forceClone3`. Версию появления vfork-пути (по alt — 1.9) не проверял.
- **Предлагаемая правка:** 12 — «На Linux `os/exec` запускает процесс через `clone(CLONE_VFORK | CLONE_VM)`: дочерний процесс до `execve` работает в памяти родителя, родитель ждёт. Поэтому копирования таблиц страниц нет, и запуск из процесса с большой кучей дешёвый». 51 — «Все дескрипторы, которые открывает Go, создаются с `O_CLOEXEC` и при `execve` закрываются; потомку передаются только 0, 1, 2 и `cmd.ExtraFiles`. Дескриптор без `O_CLOEXEC` (например, открытый C-кодом) потомок унаследует». Раздел «Стоимость fork и COW» — переписать соответственно. Ст. 11:162 — «через `clone` с `CLONE_VFORK` и `execve`».

### J-158 — INCORRECT
- **Где / цитата:** ст. 44:64 — «Только устаревший базовый набор … Отсутствуют современные механизмы `epoll`, `fanotify`, `io_uring`» / «`golang.org/x/sys` … Полная поддержка всех современных фич Linux: `io_uring`, eBPF …»; 70–72 — «определяют собственные, несовместимые … структуры … `syscall.FD` в функцию, принимающую `unix.FD`, или смешивание … `syscall.SIGINT` с типами `unix.Signal` приводят либо к ошибкам компиляции, либо … к неявным ошибкам кастинга памяти»; 66 — «**Категорически запрещен**»; итог 229 — «Устаревший пакет `syscall`».
- **Вердикт:** типов `syscall.FD`/`unix.FD` нет: дескриптор — `int`. В `x/sys/unix` `Errno` и `Signal` — **псевдонимы** `syscall.Errno`/`syscall.Signal`, полностью совместимы. В `syscall` на Linux есть `EpollCreate1`, `EpollCtl`, `EpollWait`. `x/sys/unix` даёт обёртки и константы новых вызовов, а не «поддержку io_uring как фичу»; cgroups v2 — файловый интерфейс. `syscall` заморожен, но не помечен deprecated и нужен (`SysProcAttr`, `syscall.SIGTERM` в `os/signal`); документация говорит «most new code should prefer» `x/sys`, а не «запрещён».
- **Доказательство:** `golang.org/x/sys@v0.48.0/unix/aliases.go:11–12` — `type Signal = syscall.Signal`, `type Errno = syscall.Errno`; go1.27.1 `src/syscall/zsyscall_linux_amd64.go:365, 376, 1584` — `EpollCreate1`, `EpollCtl`, `EpollWait`; `go doc syscall`: «That package has more system call support than this one, and most new code should prefer that package where possible».
- **Предлагаемая правка:** 64 — «Набор вызовов и констант заморожен: новых системных вызовов (`io_uring_setup`, `fanotify`, новые флаги) в нём нет, хотя базовые, включая `epoll`, есть. | `x/sys/unix` регулярно пополняется обёртками и константами новых ядер». 70–72 — убрать про несовместимость; «`unix.Signal` и `unix.Errno` — псевдонимы типов `syscall`, их можно смешивать. Разница в другом: часть структур (`unix.Stat_t` и т. п.) — отдельные типы, и передавать их между пакетами нельзя». 66 — «Предпочитайте `x/sys/unix` в новом коде». Итог п. 1 — «Замороженный пакет `syscall`».

### J-159 — PARTIALLY CORRECT
- **Где / цитата:** ст. 44:50 — «Планировщик отвязывает логический процессор `P` от заблокированного системного потока `M`»; 52 — «Вызывающая горутина переводится в состояние ожидания `Gwaiting`»; 83 — «процессор тратит до 80% тактов на смену контекста»; 20 — «Go вызывает ядро операционной системы **напрямую**».
- **Вердикт:** P не отвязывается сразу: горутина в системном вызове остаётся на P, и `sysmon` отбирает P, если вызов длится дольше одного своего тика (не менее 20 мкс). В go1.27.1 отдельного состояния P для системного вызова больше нет (`_Psyscall_unused`), признак — состояние горутины `_Gsyscall`, а не `Gwaiting`. «Напрямую, без libc» — верно для Linux, но на macOS, Windows, OpenBSD, illumos рантайм вызывает системные библиотеки. «80%» — без источника.
- **Доказательство:** go1.27.1 `src/runtime/runtime2.go:50–55` — `_Gsyscall`; 143–146 — «_Psyscall_unused is a now-defunct state for a P. A P is identified as "in a system call" by looking at the goroutine's state»; `src/runtime/proc.go:6743` — «Retake the P if it's there for more than 1 sysmon tick (at least 20us)».
- **Предлагаемая правка:** 50–52 — «Горутина переходит в состояние `_Gsyscall` и остаётся на своём P. Если вызов длится дольше ~20 мкс, `sysmon` забирает P и передаёт его другому потоку, чтобы остальные горутины продолжали работать». 20 — «На Linux Go вызывает ядро напрямую, без libc; на macOS, Windows и OpenBSD — через системные библиотеки». 83 — «…значительная доля тактов уходит на переключение режимов» (без «80%»).

### J-160 — PARTIALLY CORRECT
- **Где / цитата:** ст. 45:64 — «Как только все последовательные тесты завершаются, раннер … снимает барьер синхронизации и одновременно пробуждает все…».
- **Вердикт:** для параллельных **подтестов** барьер — завершение функции родительского теста, а не «всех последовательных тестов»; для параллельных тестов верхнего уровня — завершение последовательной части пакета (тут формулировка ближе к правде). Одновременно выполняется не больше `-parallel` (по умолчанию `GOMAXPROCS`). Не упомянута ловушка `tc` в цикле при `go` < 1.22 в `go.mod`.
- **Доказательство:** запуск на go1.27.1 в модуле с `go 1.21`: замыкания в `for i := 0; i < 3; i++` печатают `3 3 3` — старая семантика переменной цикла сохраняется при старой строке `go`. Поведение `t.Parallel` — по документации пакета `testing` (дословно не выводил).
- **Предлагаемая правка:** «Вызов `t.Parallel()` приостанавливает тест. Параллельные подтесты продолжаются, когда функция родительского теста вернётся; параллельные тесты верхнего уровня — когда закончатся последовательные. Одновременно выполняется не больше `-parallel` тестов (по умолчанию `GOMAXPROCS`). Если в `go.mod` указано `go 1.21` или ниже, переменная цикла `tc` общая для всех итераций — скопируйте её (`tc := tc`) перед `t.Run`».

### J-161 — PARTIALLY CORRECT
- **Где / цитата:** ст. 45:108 — «Для получения чистых, статистически повторяемых результатов запускайте бенчмарки с отключенным сборщиком: `GOGC=off`»; итог 216; 195 — «последовательно умножает `b.N` (1, 10, 100, 1000...)».
- **Вердикт:** `GOGC=off` искажает результаты аллоцирующего кода: стоимость GC — часть реальной стоимости, а куча растёт без предела. Корректнее `-benchmem`, `-count` и `benchstat`. `b.N` подбирается прогнозом по времени предыдущего прогона (рост ограничен), а не строго умножением на 10. С Go 1.24 `b.Loop` выполняет тело ровно столько, сколько нужно, и не даёт компилятору выбросить вызовы (описан в статье верно). Исходник `benchmark.go` не перечитывал.
- **Доказательство:** Go 1.24 release notes (`testing.B.Loop`): «Function call parameters and results are kept alive, preventing the compiler from fully optimizing away the loop body».
- **Предлагаемая правка:** 108 — «Для повторяемых результатов запускайте `go test -bench=. -benchmem -count=10` и сравнивайте прогоны `benchstat`. `GOGC=off` не используйте: работа сборщика — часть цены аллоцирующего кода». 195 — «…раннер прогнозирует `b.N` по времени предыдущего прогона и повторяет, пока суммарное время не достигнет `-benchtime`». Итог п. 2 — так же; «…используйте `b.Loop()` (Go 1.24+), он защищает от выброса тела компилятором».

### J-162 — INCORRECT
- **Где / цитата:** ст. 46:25 — «Предикат обязан возвращать либо `(bool, error)`, либо просто `(bool)`»; 28 — «упал на срезе из 10 000 элементов»; 135 — «Генератор создает экстремальные граничные числа вроде `math.MaxInt64`».
- **Вердикт:** предикат `Check` возвращает ровно один `bool`. Длина срезов и map ограничена `complexSize = 50`; «10 000 элементов» недостижимы. Целые берутся случайно по всему диапазону, граничных значений генератор специально не создаёт (случайное попадание в `MaxInt64` маловероятно). Срезы и map генерируются не-nil (в моём прогоне 2000 вызовов nil не было), указатели бывают `nil`.
- **Доказательство:** запуск: предикат `func(x int) (bool, error)` → `quick.Check` вернул ошибку `function does not return one value`; 2000 вызовов с `[]int` → максимальная длина 49, nil-срезов и map — 0. go1.27.1 `src/testing/quick/quick.go:54` — `const complexSize = 50`.
- **Предлагаемая правка:** 25 — «Предикат должен возвращать ровно один `bool`». 28 — убрать вместе с пунктом о сужении (J-034). 135 — «Целые числа генерируются случайно по всему диапазону типа, поэтому арифметика внутри предиката может переполниться. Граничные значения (`0`, `-1`, `MaxInt64`) генератор специально не подставляет — проверяйте их отдельным табличным тестом».

### J-163 — INCORRECT
- **Где / цитата:** ст. 47:91 — диаграмма «Паника: plugin: symbol mismatch»; 102 — «вызов `plugin.Open()` или `p.Lookup()` завершится фатальной паникой: `plugin was built with a different version of package...`»; 157 — «Загрузка новой версии `.so` поверх старой приводит к коллизиям … и падению процесса»; 159 — «Циклические ссылки между хостом и плагином могут препятствовать очистке памяти … `FreeOSMemory()`».
- **Вердикт:** `plugin.Open` в таких случаях возвращает **ошибку** `plugin.Open("…"): plugin was built with a different version of package …`; `Lookup` при отсутствии символа — ошибку. Паника — только при неудачном утверждении типа без `ok`. Повторная загрузка того же пути возвращает уже загруженный плагин; другой файл с тем же путём пакета — ошибку `plugin already loaded`. GC справляется с циклами; совет с `FreeOSMemory` без основания. Плагин сам не собирал (нужен cgo и отдельная сборка), вывод — по исходникам.
- **Доказательство:** go1.27.1 `src/runtime/plugin.go:57` — `return …, "plugin was built with a different version of package " + …` (строка ошибки), 29 и 35 — `"plugin already loaded"`; `src/plugin/plugin_dlopen.go:84` — ``return nil, errors.New(`plugin.Open("` + name + `"): ` + errstr)``, 134 — `errors.New("plugin: symbol … not found in plugin …")`, 54–60 — повторный `Open` того же файла возвращает сохранённый плагин.
- **Предлагаемая правка:** 102 — «…`plugin.Open()` вернёт ошибку `plugin was built with a different version of package …`». Диаграмма — «Ошибка Open: different version of package». 157 — «Выгрузить плагин нельзя. Повторный `Open` того же файла вернёт уже загруженный; новая сборка того же пакета не загрузится (`plugin already loaded`)». 159 — убрать или «Код и данные плагина остаются в памяти до конца процесса».

### J-164 — INCORRECT
- **Где / цитата:** ст. 47:158 — «`go build -buildmode=plugin` исторически не имеет нативной поддержки на Windows и требует MinGW / `cgo`»; 12 — «регистрирует их во внутренней структуре `runtime.symtab`»; 90 — «Регистрация в runtime.symtab».
- **Вердикт:** пакет `plugin` работает только на Linux, FreeBSD и macOS и только с cgo; на Windows его нет вовсе — ни через MinGW, ни через cgo. Требование cgo (`CGO_ENABLED=1`) плохо сочетается с образом `scratch` из введения. Плагин регистрируется в списке `moduledata` рантайма (`plugin_lastmoduleinit`), а не в «`runtime.symtab`».
- **Доказательство:** go1.27.1 `src/plugin/plugin_dlopen.go:1` — `//go:build (linux && cgo) || (darwin && cgo) || (freebsd && cgo)`; `plugin_stubs.go` — `//go:build (!linux && !freebsd && !darwin) || !cgo`; `src/runtime/plugin.go:13–16` — обход `firstmoduledata.next`.
- **Предлагаемая правка:** 158 — «Пакет `plugin` работает только на Linux, FreeBSD и macOS и требует cgo. На Windows его нет. | Для переносимых расширений используйте отдельные процессы (RPC, `hashicorp/go-plugin`) или WebAssembly». 12, 90 — «…и регистрирует модуль плагина в рантайме (`moduledata`)».

### J-165 — INCORRECT
- **Где / цитата:** ст. 48:13 — «единый кооперативный планировщик горутин»; 51 — «`OpenTelemetry`, `Structlog`»; 63 — «рантайм Go обращается к системному вызову `futex` … паркуя горутину»; 64 — «удерживает объекты в быстром поколении памяти»; 75 — «Применяйте `unsafe.Slice` … в критических путях»; 78 — «Оборачивайте ошибки с сохранением стека … через `fmt.Errorf("%w", err)`»; 103 — «мономорфизацию дженериков»; 112 — «переход от `CAS/futex`».
- **Вердикт:** итоговая статья повторяет и усиливает ошибки модуля. Сборщик мусора Go не поколенческий; с Go 1.14 планировщик вытесняет горутины асинхронно; `%w` стек не сохраняет (ст. 3 модуля говорит это верно); `structlog` — библиотека Python; совет про `unsafe.Slice` противоречит предостережениям ст. 24; `futex` — см. J-017; «мономорфизация» — J-113.
- **Доказательство:** перекрёстно: J-017 (`futex`), J-113 (дженерики), ст. 3 модуля (`%w` без стека); go1.27.1 `src/runtime/proc.go` — асинхронное вытеснение (`preemptone`, сигнал) — по общему знанию рантайма, файл здесь специально не открывал; поколенческого GC в Go нет (go.dev/doc/gc-guide — не открывал).
- **Предлагаемая правка:** править последней, после исходных статей: 13 — «вытесняющий планировщик горутин (G-M-P)»; 51 — «OpenTelemetry» (без Structlog); 63 — «…паркует горутину в рантайме, не занимая поток»; 64 — «…снижает число аллокаций и частоту сборок мусора»; 75 — «`strings.Builder` и `strconv.Append*`; `unsafe` — только после профилирования и с тестами (см. ст. 24)»; 78 — «Оборачивайте ошибки с контекстом через `fmt.Errorf("…: %w", err)` (стек `%w` не сохраняет)»; 103 — «…GC shape stenciling дженериков»; 112 — «…как работает `CAS` и парковка горутин».

### J-166 — INCORRECT
- **Где / цитата:** эпиграфы с подписью «— Брайан Керниган» в ст. 2, 7–20; ст. 6 — «Инженерная аналогия Bell Labs»; ст. 5 — «Философия Unix»; ст. 43:3 — «Кен Томпсон и Деннис Ритчи сформулировали принцип: программы должны делать одну вещь хорошо»; ст. 2:8 — `printf` «созданной … Кеном Томпсоном и Деннисом Ритчи».
- **Вердикт:** проверяемые утверждения в эпиграфах ложны:
  - **ст. 10** — история UTF-8 известна в изложении **Роба Пайка**, а не Кернигана. Пайк пишет, что формат придумал Кен Томпсон «на салфетке в закусочной в Нью-Джерси» в сентябре 1992 г. («в кафетерии» и «вместе с Пайком» — неточно).
  - **ст. 9** — в K&R `atoi` (§ 2.7) занимает около 9 строк, а не «три».
  - **ст. 19** — «Не общайтесь через разделяемую память — делитесь памятью через общение» — Go-пословица Роба Пайка (Go Proverbs, Effective Go), а не Кернигана.
  - **ст. 15, 43** — «программа должна делать одно дело хорошо» — формулировка Дугласа Макилроя (BSTJ, 1978), а не Кернигана или Томпсона и Ритчи.
  - **ст. 2** — подлинная цитата Кернигана («The most effective debugging tool is still careful thought, coupled with judiciously placed print statements», «Unix for Beginners», 1979). **Ст. 16** — первая фраза та же подлинная цитата, но к ней приписано продолжение, которого у Кернигана нет.
  - Эпиграфы ст. 7, 8, 11, 12, 13, 14, 17, 18, 20 в первоисточниках не нашёл (см. § 4); по содержанию (Go-пакеты, `io/fs`, Kubernetes) это авторские тексты, а не цитаты.
- **Доказательство:** письмо Роба Пайка «UTF-8 history» (2003, `cl.cam.ac.uk/~mgk25/ucs/utf-8-history.txt`, открыто в сессии): «UTF-8 was designed, in front of my eyes, on a placemat in a New Jersey diner one night in September or so 1992 … Ken designed it with me cheering him on». Остальное — по общеизвестным источникам (K&R 2-е изд. § 2.7; McIlroy, Pinson, Tague, «UNIX Time-Sharing System: Foreword», BSTJ 57(6), 1978; Go Proverbs, go-proverbs.github.io; Kernighan & Plauger / «Unix for Beginners») — в сессии не открывал.
- **Предлагаемая правка:** подлинные цитаты оставить (ст. 2; в ст. 16 — только первую фразу). Ст. 19 — подпись «— Роб Пайк, Go Proverbs». Ст. 10 — либо подлинный фрагмент письма Пайка с его подписью, либо убрать эпиграф. Ст. 15 и 43 — принцип приписать Макилрою: «Пусть каждая программа делает одну вещь хорошо» — Дуглас Макилрой. Ст. 9 — убрать «три строчки». Прочие — заменить подлинными цитатами или убрать подпись (оформить как авторский текст). Ст. 2:8 — «`printf` пришёл в Go из языка C (Bell Labs)».

---

## 4. Low

Формат короче: одна строка на поле.

### J-167 — OPINION / NOT A FACT CLAIM
- **Где / цитата:** ст. 1:80, 108 — «привилегированный доступ к рантайму»; «чего сложно добиться на сторонних фреймворках без глубокой интеграции с рантаймом».
- **Вердикт:** частично есть (internal-пакеты, `go:linkname`, интринсики), но сторонние серверы поверх `net.Conn` пользуются тем же netpoller. Оценка, не факт.
- **Доказательство:** устройство `net`: любой `net.Conn` идёт через `internal/poll.FD` (J-038). Сравнительных замеров не делал.
- **Предлагаемая правка:** «…`net/http` построен на том же netpoller, что доступен любому коду через `net.Conn`, поэтому держит сотни тысяч соединений без особых настроек».

### J-168 — INCORRECT
- **Где / цитата:** ст. 1:41 (диаграмма) — `crypto/cipher.Stream` как реализация `io.Reader`.
- **Вердикт:** `cipher.Stream` — интерфейс с `XORKeyStream`; читателем его делает `cipher.StreamReader`.
- **Доказательство:** `go doc crypto/cipher.Stream` / `StreamReader` (по брифу, `src/crypto/cipher/io.go`; не выводил).
- **Предлагаемая правка:** узел диаграммы — `cipher.StreamReader`.

### J-169 — OPINION / NOT A FACT CLAIM
- **Где / цитата:** ст. 1:10 — «философия Bell Labs», «90–95% типовых задач».
- **Вердикт:** число без источника. Go создан в Google (авторы — выходцы из Bell Labs, это верно как происхождение идей).
- **Доказательство:** источника цифры нет.
- **Предлагаемая правка:** «…покрывает большинство типовых задач бэкенда» (без процента).

### J-170 — OUTDATED
- **Где / цитата:** ст. 1:152; ст. 48:36 — `nhooyr.io/websocket`, «`net/http` в будущем может покрыть».
- **Вердикт:** библиотека перенесена в `github.com/coder/websocket` (2024, по брифу). Статус golang/go#18152 не проверял.
- **Доказательство:** не проверял в сессии — см. § 5.
- **Предлагаемая правка:** «`github.com/coder/websocket` (бывший `nhooyr.io/websocket`)»; фразу про будущее `net/http` убрать.

### J-171 — INCORRECT
- **Где / цитата:** ст. 2:94–96 — пример `fmt.Print("Error: ", err, " at ", time.Now())` и пояснение о пробелах.
- **Вердикт:** `Print` добавляет пробел только между двумя соседними **не-строковыми** операндами; здесь у каждой пары одна сторона — строка, видимые пробелы — из литералов.
- **Доказательство:** запуск: `fmt.Print(1, 2, "x", 3, 4, "\n")` → `1 2x3 4`.
- **Предлагаемая правка:** «`Print` добавляет пробел между операндами, только если ни один из них не строка: `Print(1, 2, "x", 3)` → `1 2x3`. Пробелы в примере — из самих строк».

### J-172 — PARTIALLY CORRECT
- **Где / цитата:** ст. 2:99, 190 — «Docker/K8s/systemd маркируют stdout/stderr разными уровнями критичности»; порог «>1000 RPS».
- **Вердикт:** Docker и Kubernetes помечают только поток (`stream: stdout/stderr`), уровня не назначают; systemd-journald по умолчанию присваивает stderr и stdout одинаковый приоритет (уровни задаются префиксами `<N>` или sd-daemon). Порог RPS — без обоснования.
- **Доказательство:** по документации Docker json-file и journald — в сессии не открывал.
- **Предлагаемая правка:** «Docker и Kubernetes сохраняют, из какого потока пришла строка (stdout или stderr), но уровень лога определяют только по её содержимому».

### J-173 — VERIFIED
- **Где / цитата:** ст. 2, таблица вербов («полный справочник»).
- **Вердикт:** пропуск подтверждён: нет `%t`, `%c`, `%U`, `%o/%O`, `%g`, `%p`, флагов; нет `fmt.Append*` (Go 1.19).
- **Доказательство:** doc `fmt` (Printing); `api/go1.19.txt` — `fmt.Append`, `Appendf`, `Appendln` (по брифу).
- **Предлагаемая правка:** назвать таблицу «основные вербы» и добавить `fmt.Appendf(buf, …)` как способ форматировать без аллокации строки результата.

### J-174 — PARTIALLY CORRECT
- **Где / цитата:** ст. 3:265 — «`fmt.Errorf` … создает новую структуру `wrapError`».
- **Вердикт:** верно для одного `%w`; при нескольких `%w` (Go 1.20) — `wrapErrors`; без `%w` — `errorString` из `errors.New`.
- **Доказательство:** go1.27.1 `src/fmt/errors.go:70, 83` — `type wrapError struct`, `type wrapErrors struct`.
- **Предлагаемая правка:** «…создаёт `*fmt.wrapError` (при нескольких `%w` — `*fmt.wrapErrors`)».

### J-175 — VERIFIED
- **Где / цитата:** ст. 3:296 — «`errors.As(err, e)` успешно скомпилируется, но вызовет панику в рантайме».
- **Вердикт:** верно; пропущено, что `go vet` (анализатор `errorsas`) ловит это до запуска. Версию включения анализатора в vet не проверял.
- **Доказательство:** запуск `go vet`: `second argument to errors.As must be a non-nil pointer to either a type that implements error, or to any interface type`.
- **Предлагаемая правка:** «…но `go vet` поймает ошибку заранее (проверка `errorsas`)».

### J-176 — PARTIALLY CORRECT
- **Где / цитата:** ст. 3:264 — «аллоцируется лишь крошечная оболочка (16–24 байта в куче)».
- **Вердикт:** `errorString{s string}` — 16 байт, класс размера 16.
- **Доказательство:** `unsafe.Sizeof(struct{ s string }{})` = 16 (по брифу; совпадает с размером заголовка строки на amd64).
- **Предлагаемая правка:** «…оболочка в 16 байт».

### J-177 — INCORRECT
- **Где / цитата:** ст. 3:245 — «В Go 1.20 появился метод `errors.Join`».
- **Вердикт:** `errors.Join` — функция. Не сказано: несколько `%w` в `fmt.Errorf` (Go 1.20), `Join` отбрасывает `nil` и возвращает `nil`, если все аргументы `nil`; `errors.ErrUnsupported` (1.21).
- **Доказательство:** Go 1.20 release notes: «The new Join function returns an error wrapping a list of errors … The Errorf function supports multiple occurrences of the %w format verb».
- **Предлагаемая правка:** «…появилась функция `errors.Join` (и поддержка нескольких `%w` в `fmt.Errorf`). `Join` пропускает `nil` и возвращает `nil`, если ошибок нет».

### J-178 — INCORRECT
- **Где / цитата:** ст. 3:166 — «мгновенное сравнение по адресу памяти (pointer comparison)»; 198 — «должно сравниваться по значению»; диаграмма 223 — `*pq.Error (lib/pq error)`.
- **Вердикт:** 166 и 198 противоречат друг другу; на деле `errors.Is` сравнивает значения интерфейсов (`==`), а для `*errorString` это сравнение указателей. `lib/pq` в режиме поддержки, рекомендуют `pgx` (`*pgconn.PgError`). Статус `lib/pq` не проверял.
- **Доказательство:** `src/errors/wrap.go` — `is(err, target, isComparable)` использует `err == target` (код просмотрен частично).
- **Предлагаемая правка:** 198 — «…и сравниваться с самим значением sentinel (для `errors.New` это сравнение указателей)». Диаграмма — `*pgconn.PgError (pgx)`.

### J-179 — PARTIALLY CORRECT
- **Где / цитата:** ст. 3:303 — «`errors.Is` … сравнивает значения указателей или вызывает метод `Is(error) bool`».
- **Вердикт:** сравнивает интерфейсы через `==` (тип + значение), если тип сравним; для указателей это и есть сравнение указателей. `errors.As` принимает и указатель на интерфейс.
- **Доказательство:** go1.27.1 `src/errors/wrap.go`, `Is` — `reflectlite.TypeOf(target).Comparable()`.
- **Предлагаемая правка:** «…сравнивает каждую ошибку цепочки с `target` оператором `==` (если тип сравним) или вызывает её метод `Is`».

### J-180 — INCORRECT
- **Где / цитата:** ст. 4:264 — «Паника: `runtime: invalid pointer dereference` … `io` не проверяет на `nil` из соображений производительности».
- **Вердикт:** текст паники другой; причина — вызов метода у nil-интерфейса, специальной «экономии» нет.
- **Доказательство:** запуск: `io.Copy(nil, strings.NewReader("x"))` → `runtime error: invalid memory address or nil pointer dereference`.
- **Предлагаемая правка:** «Паника `runtime error: invalid memory address or nil pointer dereference`: у nil-интерфейса нельзя вызвать метод».

### J-181 — INCORRECT
- **Где / цитата:** ст. 4:211 — `// TeeReader читает из файла и параллельно пишет хешеру`.
- **Вердикт:** запись синхронная, внутри того же `Read`; ошибка `w.Write` возвращается из `Read`. `io.Discard.ReadFrom` использует пул буферов по 8 КБ.
- **Доказательство:** go1.27.1 `src/io/io.go` — `teeReader.Read` вызывает `t.w.Write(p[:n])` и возвращает его ошибку; `blackHolePool` — `make([]byte, 8192)`.
- **Предлагаемая правка:** «// TeeReader при каждом Read сразу пишет прочитанное в хешер».

### J-182 — INCORRECT
- **Где / цитата:** ст. 4:275 — «`io.Copy`, `io.LimitReader`, `io.TeeReader` оптимизированы на уровне рантайма и поддерживают zero-copy fallback»; 248 — C++ «`std::filesystem` + mmap».
- **Вердикт:** это обычный Go-код; zero-copy — только у `io.Copy` для конкретных типов (J-052), у `TeeReader` нет. `std::filesystem` к zero-copy не относится (это `sendfile`/`copy_file_range` или `std::filesystem::copy_file`).
- **Доказательство:** `src/io/io.go` — обычные реализации; см. J-052.
- **Предлагаемая правка:** «`io.Copy` умеет делегировать копирование `WriterTo`/`ReaderFrom` и через них — системным вызовам `sendfile`/`splice`; `LimitReader` и `TeeReader` — простые обёртки». C++ — «`sendfile`, `copy_file_range`».

### J-183 — INCORRECT
- **Где / цитата:** ст. 5:65 — «путями `os.Path`»; 67 — «позволило компилятору строже проверять типы»; 80 — `ioutil.ReadDir` → `os.ReadDir`.
- **Вердикт:** типа `os.Path` нет. Довод о компиляторе беспредметен. Замена `ReadDir` не drop-in: `[]fs.FileInfo` → `[]fs.DirEntry`.
- **Доказательство:** `api/go1.16.txt` — `os.ReadDir(string) ([]fs.DirEntry, error)`; `io/ioutil/ioutil.go:76` — `ReadDir(dirname string) ([]fs.FileInfo, error)`.
- **Предлагаемая правка:** 65 — «…путями, дескрипторами и правами». 67 — убрать довод про компилятор. В таблице — «тип результата другой: `[]fs.DirEntry`; для `FileInfo` вызывайте `entry.Info()`».

### J-184 — PARTIALLY CORRECT
- **Где / цитата:** ст. 5:97, 115, 131, 180 — тип из `getdents64`, «используется кэш ядра», «в десятки и сотни раз», «сортировка … ядром/рантаймом».
- **Вердикт:** `d_type` действительно приходит из `getdents64`, но на части ФС он `DT_UNKNOWN`, и тогда Go делает `lstat`. «Кэш ядра» — неточно. Сортирует пакет `os`, не ядро. Ускорение без замера.
- **Доказательство:** устройство `os.ReadDir` (по брифу; `DT_UNKNOWN` → `lstat` в исходнике не проверял).
- **Предлагаемая правка:** «Имя и тип берутся из записи каталога (`getdents64`), без `stat`. На файловых системах, не сообщающих тип, Go сделает `lstat` сам. Сортировку по имени выполняет `os.ReadDir`».

### J-185 — PARTIALLY CORRECT
- **Где / цитата:** ст. 6:79–87 — алгоритмы `Writer.Write` и `Reader.Read`.
- **Вердикт:** упрощено: если буфер пуст, а `p` не меньше буфера, `Write` и `Read` идут напрямую в нижележащий writer/reader без копирования; `Read` при пустом буфере делает **один** `rd.Read` (не цикл `fill`).
- **Доказательство:** go1.27.1 `src/bufio/bufio.go`, `Reader.Read`: «Large read, empty buffer. Read directly into p to avoid copy»; «One read. Do not use b.fill, which will loop».
- **Предлагаемая правка:** в оба алгоритма — «Если буфер пуст, а `p` не меньше его размера, данные идут напрямую, минуя буфер».

### J-186 — INCORRECT
- **Где / цитата:** ст. 6:117 — «Мелкие syscall заставляют ядро мапить разные виртуальные адреса в физические»; 10 — «99% процессорного времени».
- **Вердикт:** системный вызов не перемапливает адресное пространство процесса. «99%» без измерения.
- **Доказательство:** общее устройство системных вызовов; замера не делал.
- **Предлагаемая правка:** 117 — убрать пункт про TLB. 10 — «…большая часть времени уходит на переход в ядро и обратно».

### J-187 — VERIFIED
- **Где / цитата:** ст. 6:201 — PHP `stream_set_chunk_size()`; итог — без упоминания небуферизованного `os.Stdout`.
- **Вердикт:** пропуск подтверждён: `os.Stdout` в Go не буферизован, каждый `Write` — системный вызов (это и есть главный сценарий `bufio.NewWriter(os.Stdout)`). Про PHP не проверял.
- **Доказательство:** `os.File.Write` → `poll.FD.Write` → `write(2)` без промежуточного буфера (устройство `os`, см. J-011).
- **Предлагаемая правка:** в итог — «`os.Stdout` в Go не буферизован: при выводе многих мелких строк оберните его в `bufio.NewWriter` и не забудьте `Flush`».

### J-188 — PARTIALLY CORRECT
- **Где / цитата:** ст. 7:82 — «Для переменных создает новую строку на каждую операцию `+`».
- **Вердикт:** выражение `a + b + c` компилируется в один вызов конкатенации с одной аллокацией. Квадратичность — у `s += x` в цикле (это статья тоже говорит).
- **Доказательство:** `testing.AllocsPerRun`: `sink = a + b + c` → 1 аллокация.
- **Предлагаемая правка:** «Цепочка `a + b + c` склеивается одной операцией (одна аллокация). Дорого `s += x` в цикле: каждая итерация копирует всю накопленную строку».

### J-189 — VERIFIED
- **Где / цитата:** ст. 7, вся статья.
- **Вердикт:** пропуск подтверждён: в статье нет `Cut`/`CutPrefix`, `EqualFold`, `strings.Clone`, итераторов `Lines`/`SplitSeq` (Go 1.24), ловушки `TrimLeft` (cutset).
- **Доказательство:** `grep` по статье — 0 совпадений по `Cut`, `CutPrefix`, `EqualFold`, `strings.Lines`, `SplitSeq`, `strings.Clone`; Go 1.24 release notes — `Lines`, `SplitSeq`.
- **Предлагаемая правка:** короткий раздел «Частые функции и ловушки»: `TrimLeft("xxabc", "xa")` убирает **символы** набора (для префикса — `TrimPrefix`); `strings.Cut`; `EqualFold` вместо `ToLower(a) == ToLower(b)`; подстрока удерживает всю исходную строку — `strings.Clone`; `for line := range strings.Lines(s)` (Go 1.24).

### J-190 — PARTIALLY CORRECT
- **Где / цитата:** ст. 7:186 — сравнение хешей вместо строк; «`fnv` или `xxhash`».
- **Вердикт:** при совпадении хеша строки всё равно надо сравнить (статья упоминает коллизии вскользь). `xxhash` не входит в stdlib; в stdlib — `hash/maphash`.
- **Доказательство:** `go doc hash/maphash` (пакет есть; дословно не выводил).
- **Предлагаемая правка:** «…храните хеш (`hash/maphash` или `fnv`) и сравнивайте сначала его; при совпадении хешей сравнивайте сами строки».

### J-191 — INCORRECT
- **Где / цитата:** ст. 8:76–91 — пример «aliasing».
- **Вердикт:** пример показывает обычное разделение массива. Настоящая ловушка — `append(sub, x)` затирает `buf[len(sub)]`; лечится `buf[:2:2]` или копией (`bytes.Clone`).
- **Доказательство:** запуск: `bb = [1 2 3]`, `sub := bb[:2]`, `append(sub, 42)` → `bb` стал `[1 2 42]`.
- **Предлагаемая правка:**
  ```go
  buf := []byte{1, 2, 3}
  sub := buf[:2]
  sub = append(sub, 42) // ёмкости хватает — запись идёт в buf[2]
  fmt.Println(buf)      // [1 2 42] — данные buf испорчены
  // Защита: sub := buf[:2:2] (append создаст новый массив) или bytes.Clone(buf[:2])
  ```

### J-192 — PARTIALLY CORRECT
- **Где / цитата:** ст. 8:103–104 — «// ❌ Медленно: конвертация строки в []byte внутри HasPrefix (аллокация!)».
- **Вердикт:** направление обратное: это `[]byte` → `string` до вызова. Аллокация реальна для длинных срезов (больше 32 байт). `strings` и `bytes` используют одни функции `internal/bytealg`.
- **Доказательство:** `testing.AllocsPerRun`: `strings.HasPrefix(string(header), "Content-Type")` для 71-байтного `header` → 1 аллокация.
- **Предлагаемая правка:** «// ❌ Конвертация []byte → string перед вызовом (для длинных срезов — аллокация и копия)».

### J-193 — INCORRECT
- **Где / цитата:** ст. 8:204 — Java «`StringBuilder` (аналог `bytes.Buffer`)».
- **Вердикт:** `StringBuilder` ближе к `strings.Builder`; аналог `bytes.Buffer` — `ByteArrayOutputStream`.
- **Доказательство:** общая семантика классов Java (строки против байтов).
- **Предлагаемая правка:** «`ByteArrayOutputStream` (аналог `bytes.Buffer`), `StringBuilder` (аналог `strings.Builder`)».

### J-194 — INCORRECT
- **Где / цитата:** ст. 9:129 — «`strconv.Itoa/ParseInt` | … | 1 (результат) | Низкая (только base 10)».
- **Вердикт:** `ParseInt` поддерживает основания 2–36 (и 0 — по префиксу) и на успешном пути не аллоцирует. `Itoa` — да, 1 аллокация (кроме малых чисел).
- **Доказательство:** запуск: `ParseInt("12345", 10, 64)` → 0 аллокаций; `ParseInt("zz", 36, 64)` → 1295.
- **Предлагаемая правка:** разнести строки: «`Itoa` | 1 (строка результата)» и «`ParseInt(s, base, bits)` | 0 | основания 2–36».

### J-195 — PARTIALLY CORRECT
- **Где / цитата:** ст. 9:146 — «RFC 4627 (JSON)»; 149 — «явно привести тип: `float32(f)`. При этом возможна потеря точности округления».
- **Вердикт:** RFC 4627 заменён RFC 8259. `float32(ParseFloat(s, 64))` даёт двойное округление; правильно `ParseFloat(s, 32)` (результат точно представим в `float32`). Дополнение: при `ErrRange` `ParseInt` возвращает предельное значение, а не 0.
- **Доказательство:** запуск: `ParseInt("99999999999999999999", 10, 64)` → `9223372036854775807` и ошибка `value out of range`. Двойное округление на конкретном числе не воспроизводил.
- **Предлагаемая правка:** 146 — «RFC 8259 (JSON)». 149 — «Для `float32` разбирайте с `bitSize = 32`: `f, err := strconv.ParseFloat(s, 32); v := float32(f)` — так округление будет однократным».

### J-196 — PARTIALLY CORRECT
- **Где / цитата:** ст. 9:108 — «Сборка SQL-запросов» через `Append`.
- **Вердикт:** без оговорки об инъекциях опасно; `strconv.AppendQuote` экранирует по правилам Go, а не JSON/SQL.
- **Доказательство:** doc `strconv.Quote` — «Go string literal» (по документации).
- **Предлагаемая правка:** «Сборка ключей кэша и метрик. SQL с данными пользователя собирайте только через параметры запроса».

### J-197 — VERIFIED
- **Где / цитата:** ст. 9:57 — ``*   `'g'`/`'G'**: Автоматический выбор…``.
- **Вердикт:** дефект разметки подтверждён: после `'G'` стоит `**` вместо закрывающей обратной кавычки.
- **Доказательство:** `dist/docs/06-standartnaya-biblioteka-go/9-strconv-konvertatsiya-strok-i-chisel.html` содержит `<code>'G'**: Автоматический выбор: использует</code>`.
- **Предлагаемая правка:** ``*   `'g'`/`'G'`: Автоматический выбор…``.

### J-198 — INCORRECT
- **Где / цитата:** ст. 10:14 — «Эмодзи и редкие исторические символы — **4 байта**»; диаграмма («7–11 байт, 2+ руны»).
- **Вердикт:** эмодзи из BMP занимают 3 байта (☺ — сама статья ниже); `👨‍💻` — 3 руны и 11 байт.
- **Доказательство:** запуск: `👨‍💻` → `RuneCountInString` 3, `len` 11; `len("☺")` = 3.
- **Предлагаемая правка:** «Символы вне BMP (большинство эмодзи, редкие письменности) — 4 байта; часть старых эмодзи (☺) — 3 байта». Диаграмма — «👨‍💻: 3 руны, 11 байт».

### J-199 — INCORRECT
- **Где / цитата:** ст. 10:92–100 — `processFirstChar`; 87 — «подсчитывая стартовые байты»; 112 — «`for range` — это единственный встроенный … механизм».
- **Вердикт:** на пустой строке `ValidString("")` истинно, `DecodeRuneInString` → `(RuneError, 0)`, проверка `size == 1` не срабатывает — функция обработает «руну» `U+FFFD`. `RuneCountInString` считает каждый невалидный байт отдельной руной. Конвертация `[]rune(s)` тоже декодирует UTF-8.
- **Доказательство:** запуск: `DecodeRuneInString("")` → `RuneError`, size 0; `RuneCountInString("\xff\xfe")` → 2.
- **Предлагаемая правка:** в начале `processFirstChar` — `if s == "" { return }`. 87 — «…каждый невалидный байт считается отдельной руной». 112 — «…один из двух встроенных механизмов (второй — `[]rune(s)`)».

### J-200 — OUTDATED
- **Где / цитата:** ст. 10:6, 194 — Java `char` (2 байта), «`length()` может врать для эмодзи»; 159 — «`unicode.Is` выполняет поиск по битовым маскам».
- **Вердикт:** с Java 9 (JEP 254) строки Latin-1 хранятся по байту на символ; `length()` считает UTF-16 code units — «врёт» только для символов вне BMP. `unicode.Is` — поиск по таблицам диапазонов (линейный для коротких, бинарный для длинных), не битовые маски.
- **Доказательство:** go1.27.1 `src/unicode/letter.go:157–168` — `Is` вызывает `is16`/`is32` по таблицам диапазонов. JEP 254 — по памяти.
- **Предлагаемая правка:** 194 — «`length()` считает UTF-16 code units: символ вне BMP (большинство эмодзи) даёт 2». 159 — «…ищет руну в отсортированной таблице диапазонов».

### J-201 — PARTIALLY CORRECT
- **Где / цитата:** ст. 11:203, 206 — Java NIO.2 «Асинхронная (CompletableFuture)», Python «GIL блокирует», Go «близкая к C».
- **Вердикт:** NIO.2 `Files` синхронны, асинхронен `AsynchronousFileChannel`; GIL освобождается на блокирующем вводе-выводе; «близкая к C» — без замеров.
- **Доказательство:** по документации Java/Python — в сессии не открывал.
- **Предлагаемая правка:** Java — «Синхронный `Files`; асинхронный `AsynchronousFileChannel`». Python — «Синхронная; GIL освобождается на время ввода-вывода». Строку производительности убрать.

### J-202 — VERIFIED
- **Где / цитата:** ст. 11, вся статья; ст. 43:90–94, 244 (из B-отчёта) — «✅ АБСОЛЮТНО БЕЗОПАСНО: `exec.Command("grep", userInput, …)`».
- **Вердикт:** пропуски подтверждены (`os.Root`, `os.UserConfigDir`, `os.Executable`, `errors.Is(err, fs.ErrNotExist)`). Argument injection реальна: аргумент, начинающийся с `-`, программа разбирает как опцию.
- **Доказательство:** запуск: `exec.Command("grep", "-f"+файл_с_шаблоном, "/etc/passwd")` — `grep` прочитал шаблоны из файла и вывел совпавшую строку `/etc/passwd`.
- **Предлагаемая правка:** ст. 43:90 — «✅ Без командной оболочки: инъекция через `;`, `|`, `$()` невозможна. Но аргумент, начинающийся с `-`, программа примет за опцию: ставьте `--` перед пользовательскими аргументами — `exec.Command("grep", "--", userInput, "/var/log/app.log")`». Итог ст. 43 п. 3 — то же уточнение.

### J-203 — INCORRECT
- **Где / цитата:** ст. 12:79 — «Исторический метод `filepath.Walk` устарел»; ст. 13:96.
- **Вердикт:** `filepath.Walk` не помечен deprecated; документация говорит «less efficient than WalkDir». Не упомянут `fs.SkipAll` (1.20).
- **Доказательство:** `go doc path/filepath.Walk`: «Walk is less efficient than WalkDir, introduced in Go 1.16, which avoids calling os.Lstat on every visited file or directory».
- **Предлагаемая правка:** «`filepath.Walk` не рекомендуется для нового кода: он медленнее `WalkDir` (Go 1.16), который не вызывает `Lstat` для каждого элемента. Остановить обход целиком — `return fs.SkipAll` (Go 1.20)».

### J-204 — INCORRECT
- **Где / цитата:** ст. 12:157 — «`os.Getwd()` (который вызывает `filepath.Abs`) вернет ошибку».
- **Вердикт:** наоборот: `Abs` вызывает `Getwd`, и только для относительных путей.
- **Доказательство:** go1.27.1 `src/path/filepath/path.go:165–169` — `unixAbs`: `if IsAbs(path) { return Clean(path), nil }`, затем `os.Getwd()`.
- **Предлагаемая правка:** «Для относительного пути `filepath.Abs` вызывает `os.Getwd()`; если текущий каталог удалён или недоступен, вернётся ошибка».

### J-205 — VERIFIED
- **Где / цитата:** ст. 12:137 и др.
- **Вердикт:** пропуск подтверждён: нет `filepath.IsLocal` (1.20), `Localize` (1.23), `EvalSymlinks`, `VolumeName`. Сравнение с Java `Path` «ленивое, требует JVM» и `strings.Builder` «ради GC» — без содержания.
- **Доказательство:** Go 1.20 release notes (`IsLocal`), Go 1.23 release notes (`Localize`).
- **Предлагаемая правка:** добавить абзац о `IsLocal`/`Localize`/`EvalSymlinks` рядом с J-012; строку о Java убрать.

### J-206 — PARTIALLY CORRECT
- **Где / цитата:** ст. 13:3–4 (эпиграф про Plan 9 с подписью Кернигана); итоги.
- **Вердикт:** см. J-166: подлинность эпиграфа не подтверждена (Керниган не был в основной команде Plan 9). «`filepath.Walk` устаревший» — J-203. Нет `fs.ReadFile`, `fs.ValidPath`, `fstest.TestFS`, `os.CopyFS` (1.23).
- **Доказательство:** Go 1.23 release notes (`os.CopyFS`); эпиграф — § 5.
- **Предлагаемая правка:** эпиграф — по J-166; в обзор интерфейсов добавить `fs.ReadFile`, `fs.ValidPath`, `testing/fstest.TestFS`, `os.CopyFS`.

### J-207 — INCORRECT
- **Где / цитата:** ст. 14:118 — «Метод `Stat()` всегда возвращает права `0644`».
- **Вердикт:** у встроенного файла права `0444`, у каталога — `ModeDir|0555`; нулевой `ModTime` — верно.
- **Доказательство:** запуск: `fs.Stat(embedFS, "static/a.txt").Mode()` → `-r--r--r--`, каталог → `dr-xr-xr-x`, `ModTime().IsZero()` → `true`.
- **Предлагаемая правка:** «…возвращает права `0444` (каталоги — `0555`) и нулевое время изменения».

### J-208 — NOT CHECKED
- **Где / цитата:** ст. 14, таблица языков — «В C/C++ нет встроенной поддержки».
- **Вердикт:** по брифу — устарело (`#embed` в C23); поддержку в компиляторах и статус в C++26 не проверял.
- **Доказательство:** —
- **Предлагаемая правка:** —

### J-209 — INCORRECT
- **Где / цитата:** ст. 14:72 — «Содержимое файлов последовательно читается и пакуется в единый монолитный блок данных»; итог 148.
- **Вердикт:** каждый файл — отдельный символ данных; `embed.FS` — отсортированный список записей `file{name, data, hash}`, по которому идёт бинарный поиск.
- **Доказательство:** go1.27.1 `src/embed/embed.go`, `lookup` — бинарный поиск по `*f.files` (отсортированный список); устройство символов в компиляторе не проверял.
- **Предлагаемая правка:** «Компилятор встраивает каждый файл отдельным блоком данных, а для `embed.FS` строит отсортированный список файлов».

### J-210 — INCORRECT
- **Где / цитата:** ст. 15:48–54 — «упрощённая структура `FlagSet`» с полями `funcs []func() error`, `exitOnError bool`.
- **Вердикт:** таких полей нет; есть `errorHandling ErrorHandling` с тремя режимами: `ContinueOnError`, `ExitOnError`, `PanicOnError`.
- **Доказательство:** go1.27.1 `src/flag/flag.go:402` — `errorHandling ErrorHandling`; 381 — `PanicOnError`.
- **Предлагаемая правка:** убрать `funcs`, заменить `exitOnError bool` на `errorHandling ErrorHandling // ContinueOnError, ExitOnError или PanicOnError`.

### J-211 — PARTIALLY CORRECT
- **Где / цитата:** ст. 15:173 — «немедленное завершение с кодом ошибки — стандартное поведение POSIX».
- **Вердикт:** код 2 для ошибки использования — конвенция утилит, а не требование POSIX. Не описаны `-flag=false` (булев флаг нельзя выключить как `-flag false`) и терминатор `--`.
- **Доказательство:** doc `flag` («Boolean flags may be … -flag=false … the form -flag x is permitted only for non-boolean flags», «Flag parsing stops … after the terminator "--"») — по документации, дословно не выводил.
- **Предлагаемая правка:** «…код 2 — общепринятая конвенция для ошибки использования (ей следуют многие утилиты Unix)»; добавить: «булев флаг выключается только как `-v=false`; `--` завершает разбор флагов».

### J-212 — NOT CHECKED
- **Где / цитата:** ст. 16:191 — Logback `AsyncAppender`, pino и SIMD.
- **Вердикт:** по брифу — неточности; в документации Logback/pino не проверял.
- **Доказательство:** —
- **Предлагаемая правка:** —

### J-213 — INCORRECT
- **Где / цитата:** ст. 16:203 — «Забудьте про устаревший пакет `log`».
- **Вердикт:** пакет `log` не помечен deprecated.
- **Доказательство:** `go doc log | grep -i deprecat` — пусто.
- **Предлагаемая правка:** «Для сервисов используйте `log/slog`; пакет `log` остаётся для простых утилит».

### J-214 — INCORRECT
- **Где / цитата:** ст. 17:50 — «Каждый контекст знает о своих потомках через slice или map».
- **Вердикт:** только `map[canceler]struct{}`. Для родителя-не-из-пакета `context` заводится горутина-мост (`propagateCancel`) или используется `AfterFunc`.
- **Доказательство:** go1.27.1 `src/context/context.go:437` — `children map[canceler]struct{}`.
- **Предлагаемая правка:** «…хранит потомков в map `children`».

### J-215 — INCORRECT
- **Где / цитата:** ст. 17:80 — «Zero-аллокация при чтении `Done()`».
- **Вердикт:** первый вызов `Done()` у `cancelCtx` лениво создаёт канал (аллокация); дальнейшие — без аллокаций.
- **Доказательство:** go1.27.1 `src/context/context.go`, `(*cancelCtx).Done` — `if d == nil { d = make(chan struct{}); c.done.Store(d) }`.
- **Предлагаемая правка:** «Канал `Done()` создаётся при первом обращении; повторные вызовы и ожидание в `select` не аллоцируют».

### J-216 — INCORRECT
- **Где / цитата:** ст. 17:163 — Java «`CancellationToken`»; 178 — «Экспоненциальный рост числа дочерних контекстов».
- **Вердикт:** `CancellationToken` — .NET; рост числа дочерних контекстов в цикле линейный.
- **Доказательство:** общеизвестный API .NET (`System.Threading.CancellationToken`); арифметика: одна итерация — один контекст.
- **Предлагаемая правка:** Java — «`Future.cancel`, `Thread.interrupt`, `ThreadLocal`»; 178 — «Число дочерних контекстов растёт с каждой итерацией, пока не отменён родитель».

### J-217 — INCORRECT
- **Где / цитата:** ст. 18:84 — «рантайм может использовать ассемблерную инструкцию `rdtsc` … (~10–20 тактов)» для замера времени.
- **Вердикт:** `time.Now()` на Linux идёт через vDSO `clock_gettime`; `RDTSC`/`RDTSCP` рантайм использует для `cputicks()` (внутренние метрики), а не для `time.Now`.
- **Доказательство:** go1.27.1 `src/runtime/time_linux_amd64.s:54, 61` — `vdsoClockgettimeSym`; `src/runtime/asm_amd64.s:1226–1228` — `RDTSCP` в `cputicks`.
- **Предлагаемая правка:** убрать пункт 2 или «Внутренние счётчики рантайма читают TSC (`rdtsc`); `time.Now()` использует vDSO».

### J-218 — PARTIALLY CORRECT
- **Где / цитата:** ст. 18:147, 149 — Java «Сравнение всегда monotonic» (`Instant`); Python «`datetime` мутабелен», «GIL блокирует `sleep()`».
- **Вердикт:** `Instant` — время по часам (wall clock), монотонное — `System.nanoTime()`; `datetime` неизменяем; `time.sleep` освобождает GIL. Документацию не открывал.
- **Доказательство:** общеизвестные свойства API Java/Python.
- **Предлагаемая правка:** Java — «`Instant` — wall clock, монотонное — `System.nanoTime()`»; Python — «`datetime` неизменяем; монотонное время — `time.monotonic()`».

### J-219 — OUTDATED
- **Где / цитата:** ст. 19:75 — «поле `state1 [3]uint32` (или `uint64`)»; 106 — паника «`runtime: sync: WaitGroup misuse`».
- **Вердикт:** в go1.27.1 — `state atomic.Uint64` и `sema uint32` (с Go 1.20, по брифу); в Go 1.25 добавлен `WaitGroup.Go`. Текст паники — `sync: WaitGroup misuse: …` без `runtime:`.
- **Доказательство:** go1.27.1 `src/sync/waitgroup.go` — `state atomic.Uint64`, `sema uint32`, `panic("sync: WaitGroup misuse: Add called concurrently with Wait")`, `func (wg *WaitGroup) Go(f func())` (236); Go 1.25 release notes: «The new WaitGroup.Go method».
- **Предлагаемая правка:** 75 — «…поле `state atomic.Uint64` (счётчик и число ожидающих) и семафор `sema`». 106 — «…паника `sync: WaitGroup misuse`». Добавить: «С Go 1.25 — `wg.Go(func(){…})` сам делает `Add(1)` и `Done()`».

### J-220 — PARTIALLY CORRECT
- **Где / цитата:** ст. 19:139 — «В Go 1.21+ это поведение задокументировано явно»; 195 — «Избегайте дедлоков через рекурсию».
- **Вердикт:** поведение `Once.Do` при панике документировано давно (версию не проверял); в 1.21 появились `OnceFunc/OnceValue(s)` с **другой** семантикой: паника повторяется при каждом вызове. Рекурсивный `RLock` при ждущем писателе — дедлок, документация прямо запрещает.
- **Доказательство:** doc `sync.Once.Do`: «If f panics, Do considers it to have returned»; doc `sync.OnceValue`: «If f panics, the returned function will panic with the same value on every call»; doc `RWMutex`: «this prohibits recursive read-locking».
- **Предлагаемая правка:** 139 — «…У `sync.OnceFunc`/`OnceValue` (Go 1.21) поведение другое: если `f` паникует, каждый вызов возвращённой функции паникует тем же значением». 195 — «Не берите `RLock` повторно в той же горутине: если между вызовами придёт писатель, будет дедлок».

### J-221 — PARTIALLY CORRECT
- **Где / цитата:** ст. 19:25 — «CAS … за ~5 тактов»; 146 — «падение производительности на 10–30%»; 148–152 — паддинг до 64 байт.
- **Вердикт:** паддинг 56 байт для 8-байтного `Mutex` арифметически верен. «~5 тактов» для `LOCK CMPXCHG` занижено (обычно 15–30+ тактов; в замере `atomic.Add` — 5 нс ≈ 20 тактов). «10–30%» без источника. Кэш-линия 64 байта не везде: на Apple Silicon — 128.
- **Доказательство:** `unsafe.Sizeof(sync.Mutex{})` → 8; бенчмарк `atomic.Int64.Add` — 5,15 нс/операция.
- **Предлагаемая правка:** 25 — «…за десятки тактов»; 146 — без процента; к паддингу — «на части ARM64 (Apple M) линия 128 байт; `golang.org/x/sys/cpu.CacheLinePad` учитывает архитектуру».

### J-222 — INCORRECT
- **Где / цитата:** ст. 20:86 — «чтению разорванных слов (torn reads) на уровне регистров CPU».
- **Вердикт:** для выровненного слова на 64-битной платформе разрыва не бывает; опасность — отсутствие отношения happens-before (и как следствие — перестановки, кэширование значения в регистре).
- **Доказательство:** Go Memory Model (`doc/go_mem.html`): программа с гонкой данных не имеет гарантий упорядоченности; атомики — sequentially consistent (Go 1.19 release notes).
- **Предлагаемая правка:** «…это гонка данных: без атомарной записи нет гарантии, что другая горутина увидит новое значение и что остальные записи будут видны в правильном порядке».

### J-223 — PARTIALLY CORRECT
- **Где / цитата:** ст. 20:103–110 — `GoodMetrics{a; _ [56]byte; b}`, «ускоряет исполнение в 5–10 раз».
- **Вердикт:** `a` и `b` отстоят на 64 байта и в одну 64-байтную линию не попадут; но от соседей до `a` и после `b` структура не защищена, и на 128-байтных линиях этого мало. «5–10 раз» без источника.
- **Доказательство:** арифметика смещений (0 и 64); замера false sharing не делал.
- **Предлагаемая правка:** «…`a` и `b` не делят кэш-линию (при линии 64 байта); ускорение зависит от нагрузки — измерьте».

### J-224 — INCORRECT
- **Где / цитата:** ст. 21:30 (диаграмма «глобальный пул»), 44 — «Это глобальная очередь»; 45 — «объекты сначала мигрируют из victim в local»; 55 — «системных вызовов `mmap`».
- **Вердикт:** глобального пула нет: у каждого P `private` + `shared`, остальные P обворовываются. Объект из victim возвращается вызывающему сразу, «миграции» нет. `mmap` при аллокации — редкость (рост кучи), не на каждый объект.
- **Доказательство:** go1.27.1 `src/sync/pool.go`, `getSlow` — кража из `shared` других P, затем `p.victim`, найденный объект сразу возвращается (`return x`).
- **Предлагаемая правка:** диаграмма — «Есть объекты в shared других P? → кража»; 44 — убрать «глобальная очередь»; 45 — «…если основного пула нет, `Get` берёт объект прямо из victim»; 55 — «…и при нехватке памяти — запрос новых страниц у ОС».

### J-225 — VERIFIED
- **Где / цитата:** ст. 22:131 и вся статья.
- **Вердикт:** «2 КБ» верно, но с Go 1.19 стартовый размер стека подбирается по средней истории; пропущены `debug.SetMemoryLimit`, `runtime.AddCleanup` (1.24), `runtime.Pinner` (1.21), Flight Recorder (1.25).
- **Доказательство:** Go 1.19 release notes: «allocate initial goroutine stacks based on the historic average stack usage»; `api/go1.24.txt` (`AddCleanup`), `api/go1.21.txt` (`Pinner`), `api/go1.25.txt:87` (`NewFlightRecorder`).
- **Предлагаемая правка:** 131 — «…стартовый стек — 2 КБ (с Go 1.19 рантайм может начинать с большего размера, по средней истории)»; добавить короткий список новых API.

### J-226 — INCORRECT
- **Где / цитата:** ст. 23:92 — «`Elem()` паникует с сообщением о невалидном типе».
- **Вердикт:** `reflect.TypeOf(nil)` возвращает `nil`-интерфейс `Type`; вызов метода у него — обычная nil-паника.
- **Доказательство:** запуск: `reflect.TypeOf(nil).Elem()` → `runtime error: invalid memory address or nil pointer dereference`.
- **Предлагаемая правка:** «…`reflect.TypeOf(nil)` возвращает `nil`, и вызов `.Elem()` у него — паника разыменования nil».

### J-227 — PARTIALLY CORRECT
- **Где / цитата:** ст. 24:38 — «Если сборщик перемещает память (например, при расширении непрерывного стека горутины), рантайм автоматически корректирует все переменные типа `unsafe.Pointer`»; 42 — «Преобразование `Pointer` → `uintptr` допустимо **только** если результат используется немедленно…».
- **Вердикт:** 38 верно (перемещаются стеки, объекты кучи не перемещаются; пример в статье — именно стек). 42 строже документации: шаблоны `unsafe.Pointer` допускают и `uintptr` только для печати/хеширования (без обратного преобразования), а также вызов `syscall.Syscall`.
- **Доказательство:** doc `unsafe.Pointer` (шесть допустимых шаблонов) — по документации, дословно не выводил.
- **Предлагаемая правка:** 42 — «Превращать `uintptr` обратно в `Pointer` можно только в том же выражении (арифметика указателя) или в аргументах `syscall.Syscall`. Хранить `uintptr`, чтобы потом снова получить указатель, нельзя».

### J-228 — OUTDATED
- **Где / цитата:** ст. 24:106 — «ускорить обработку в 5–10 раз и снизить `GC Pause` до нуля»; 119 — сборщик «полагается на битовые карты (`heap bitmap`)».
- **Вердикт:** цифры без источника. С Go 1.22 информация об указателях хранится в заголовках объектов (allocation headers) и в битах внутри span для мелких объектов, а не в единой heap bitmap (по брифу; release notes 1.22 не проверял).
- **Доказательство:** go1.27.1 `src/runtime/mbitmap.go:68, 76, 103` — `heapBitsInSpan` и заголовки объектов («This may be nil if the object is in a span where heapBitsInSpan…»).
- **Предлагаемая правка:** 106 — без чисел. 119 — «…который отслеживает, где в объектах лежат указатели (метаданные типа и заголовки объектов)».

### J-229 — INCORRECT
- **Где / цитата:** ст. 25:141 — «`slices.Sort` для `[]byte` … используйте `slices.SortFunc` с `bytes.Compare`»; 18 — «$O(1)$ дополнительной памяти».
- **Вердикт:** `bytes.Compare` нужен для `[][]byte` (сравнение срезов), а не для `[]byte`. pdqsort рекурсивен: O(log n) памяти стека. `cmp.Or` (1.22) не упомянут.
- **Доказательство:** сигнатура `bytes.Compare(a, b []byte) int`; рекурсия в `pdqsortCmpFunc` (`src/slices/zsortanyfunc.go`).
- **Предлагаемая правка:** 141 — «Для `[][]byte` используйте `slices.SortFunc(xs, bytes.Compare)`». 18 — «…без дополнительного буфера (O(log n) стека на рекурсию)».

### J-230 — INCORRECT
- **Где / цитата:** ст. 27:26 — «внутренний вызов `runtime.newElement`»; 52 — «`e.Next()` вернет `nil` или указатель на освобожденный узел».
- **Вердикт:** функции `runtime.newElement` нет — `PushBack` делает `&Element{Value: v}`. После `Remove` `e.Next()` возвращает `nil` (ссылки обнулены), «освобождённых узлов» под GC не бывает.
- **Доказательство:** запуск: после `l.Remove(e)` → `e.Next()` = `<nil>`.
- **Предлагаемая правка:** 26 — «Каждый `PushBack` выделяет новый `Element` в куче». 52 — «…после `Remove` `e.Next()` вернёт `nil`, и цикл оборвётся».

### J-231 — PARTIALLY CORRECT
- **Где / цитата:** ст. 28:55–69 — `validateEmail` с `^[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}$`.
- **Вердикт:** как пример компиляции регулярки — нормально, но подан как рабочая проверка: регистрозависим (`User@Example.com` не пройдёт), без IDN. Для разбора адреса — `net/mail.ParseAddress`.
- **Доказательство:** регулярное выражение содержит только строчные классы `[a-z]` (по тексту).
- **Предлагаемая правка:** добавить флаг `(?i)` и примечание: «для настоящей проверки адреса используйте `net/mail.ParseAddress` и письмо с подтверждением».

### J-232 — PARTIALLY CORRECT
- **Где / цитата:** ст. 29:14 — «кэшируются в `sync.Map` (`typeCache`)»; 31; 180; отсутствие оговорок про регистр ключей и дубликаты.
- **Вердикт:** в реализации v1 кэш называется `encoderCache`/`fieldCache`; в go1.27.1 по умолчанию работает реализация v2 (B-12). `Unmarshal` сопоставляет ключи без учёта регистра, при дубликатах побеждает последний — источник расхождения парсеров (замечание B-отчёта, поддерживаю повышение до Medium). Числа в `any` — `float64`.
- **Доказательство:** запуск: `{"role":"user","ROLE":"admin"}` → `Role == "admin"`; `{"role":"user","role":"admin"}` → `admin`, ошибки нет; `{"n":12345678901234567890}` в `any` → `float64`. Go 1.27 release notes: v2 «rejects duplicate names within a JSON object» (только для пакета v2).
- **Предлагаемая правка:** 14 — «…кэшируются по типу». Добавить в ловушки: «`Unmarshal` сопоставляет ключи без учёта регистра, а при повторяющихся ключах побеждает последний: `{"role":"user","ROLE":"admin"}` даст `admin`. Для строгих API используйте `encoding/json/v2` (Go 1.27), который отвергает дубликаты, или проверку схемы».

### J-233 — INCORRECT
- **Где / цитата:** ст. 30:11 — «парсер, работающий в стиле SAX … строгого соблюдения порядка тегов»; 158 — `simdjson` (CSV/JSON).
- **Вердикт:** `xml.Decoder.Token` — pull-парсер (вызывающий запрашивает токены), не SAX (callbacks). `Unmarshal` порядка дочерних элементов не требует. `simdjson` — только JSON.
- **Доказательство:** API `xml.Decoder.Token()` (pull); в эксперименте J-023 элементы разных пространств разобраны независимо от порядка.
- **Предлагаемая правка:** 11 — «…потоковый pull-парсер (`Decoder.Token`) и сопоставление со структурами через рефлексию». 158 — «`simdjson` (JSON)».

### J-234 — INCORRECT
- **Где / цитата:** ст. 32:50 — «Преобразование в `url.Values` происходит только при первом вызове метода `u.Query()`»; 64 — «`make([]byte, 3*len(s))` в худшем случае»; 74 — «`url.PathUnescape` на сырой подстроке»; 127 — «инвалидирует логику кэширования».
- **Вердикт:** `Query()` разбирает `RawQuery` при **каждом** вызове, кэша нет. `QueryEscape` сначала считает символы для экранирования и выделяет ровно `len(s) + 2*hexCount`. Для значений query нужен `QueryUnescape` (`+` — пробел), не `PathUnescape`.
- **Доказательство:** go1.27.1 `src/net/url/url.go:1164–1167` — `Query()` = `ParseQuery(u.RawQuery)`; `escape` — `required := len(s) + 2*hexCount`.
- **Предлагаемая правка:** 50 — «…`u.Query()` разбирает её заново при каждом вызове». 64 — «…сначала подсчитывает символы для экранирования и выделяет буфер точного размера». 74 — «`url.QueryUnescape`». 127 — «Прямая запись в `RawQuery` безопасна, если строка корректно закодирована (`q.Encode()`)».

### J-235 — INCORRECT
- **Где / цитата:** ст. 33:92 — «создание замыканий в middleware цепочке … генерирует аллокации замыканий в куче».
- **Вердикт:** цепочка middleware собирается один раз при старте; на запрос новых замыканий нет (аллокации на запрос возможны внутри middleware, например обёртка `ResponseWriter`).
- **Доказательство:** код `func Middleware(next http.Handler) http.Handler { return http.HandlerFunc(...) }` выполняется при сборке цепочки (по тексту примера).
- **Предлагаемая правка:** «Цепочка middleware собирается один раз при старте. На каждый запрос аллоцируют только объекты, которые middleware создаёт внутри (например, обёртка `ResponseWriter`)».

### J-236 — PARTIALLY CORRECT
- **Где / цитата:** ст. 35:72 — «`NewRequest` и `NewRecorder` выделяют память на стеке или в куче в зависимости от размера тела»; 73 — «данные остаются горячими в L1/L2».
- **Вердикт:** оценки без содержания. Полезное не сказано: `httptest.NewRequest` паникует на некорректной цели и ставит `RemoteAddr = "192.0.2.1:1234"`.
- **Доказательство:** go1.27.1 `src/net/http/httptest/httptest.go:85` — `req.RemoteAddr = "192.0.2.1:1234"`.
- **Предлагаемая правка:** заменить пп. 2–3: «`httptest.NewRequest` паникует при неверном URL и подставляет `RemoteAddr` `192.0.2.1:1234` — учитывайте это в тестах, которые смотрят на IP клиента».

### J-237 — PARTIALLY CORRECT
- **Где / цитата:** ст. 36:18 — «настраивает системный таймер (`setitimer` на Linux …)»; 24 — «~5-10% CPU», «компенсирует … математической экстраполяцией».
- **Вердикт:** на Linux рантайм использует потоковые таймеры `timer_create` (с Go 1.18, по брифу; версию не проверял), `setitimer` — запасной путь. Цифра и «экстраполяция» без источника.
- **Доказательство:** go1.27.1 `src/runtime/os_linux.go:434, 437, 593–594` — есть и `setitimer`, и `timer_create`, сигналы обоих видов различаются по `si_code`.
- **Предлагаемая правка:** «…на Linux — таймеры на каждый поток (`timer_create`), иначе `setitimer`, сигнал `SIGPROF` 100 раз в секунду». Без «5–10%» и «экстраполяции».

### J-238 — PARTIALLY CORRECT
- **Где / цитата:** ст. 37:108 — «Общий `rand.Rand` … Вызовет панику или зацикливание»; 101 — Фишер–Йетс «избегая мьютекса».
- **Вердикт:** гонка на `rand.Rand` — реальна (данные портятся, `-race` её ловит); «паника или зацикливание» не подтверждены. Про Python не проверял.
- **Доказательство:** doc `math/rand.New`: «Unlike the default Source used by top-level functions, this source is not safe for concurrent use by multiple goroutines» (по документации).
- **Предлагаемая правка:** «Общий `rand.Rand` между горутинами | Гонка данных: состояние генератора портится, `go test -race` это покажет | Свой генератор на горутину или глобальные функции (они потокобезопасны)».

### J-239 — OUTDATED
- **Где / цитата:** ст. 38:115 — «Стандартный пакет `crypto` содержит только быстрые криптографические хеши»; 296 — «Стандартная библиотека сознательно не содержит хешеров паролей».
- **Вердикт:** bcrypt/argon2 в stdlib действительно нет (они в `x/crypto`). Но с Go 1.24 есть `crypto/pbkdf2`, `crypto/hkdf`, `crypto/sha3`. Лимит bcrypt — 72 байта пароля (не проверял).
- **Доказательство:** `api/go1.24.txt:11–13` — `crypto/hkdf`; Go 1.24 release notes: «The new crypto/pbkdf2 package implements … PBKDF2».
- **Предлагаемая правка:** «В stdlib нет bcrypt и Argon2 (они в `golang.org/x/crypto`). С Go 1.24 есть `crypto/pbkdf2` — допустим для паролей с большим числом итераций (FIPS), но memory-hard Argon2id предпочтительнее».

### J-240 — INCORRECT
- **Где / цитата:** ст. 39:12 — «`sql.Open()` … валидирует DSN»; 23 — «New Conn Channel: внутренняя логика асинхронного открытия новых TCP-сокетов»; ст. 40:12 — «в фоне инициируется открытие нового TCP-сокета, а горутина переводится в состояние ожидания».
- **Вердикт:** `Open` «may just validate its arguments» — валидация DSN зависит от драйвера. Если лимит не исчерпан, новое соединение открывает **сама вызывающая горутина** синхронно (`db.connector.Connect(ctx)`); фоновый `connectionOpener` открывает соединения для ожидающих в очереди.
- **Доказательство:** go1.27.1 `src/database/sql/sql.go:860` — «Open may just validate its arguments without creating a connection»; `DB.conn`: `db.numOpen++ // optimistically` → `db.connector.Connect(ctx)`.
- **Предлагаемая правка:** 39:12 — «…проверяет, что драйвер зарегистрирован; проверит ли он DSN — зависит от драйвера». 23 и 40:12 — «Если лимит не достигнут, горутина сама открывает новое соединение. Если достигнут — встаёт в очередь `connRequests` и ждёт, пока соединение освободится».

### J-241 — PARTIALLY CORRECT
- **Где / цитата:** ст. 39:98 — `return nil, nil` при `sql.ErrNoRows`; 174 — PHP «хранить пул … невозможно».
- **Вердикт:** `nil, nil` — спорный приём (вызывающий легко забудет проверку), лучше вернуть свою ошибку `ErrNotFound`. PHP: у PDO есть persistent connections, у Swoole/RoadRunner — пулы (не проверял).
- **Доказательство:** мнение о стиле; про PHP — по общему знанию.
- **Предлагаемая правка:** 98 — `return nil, ErrUserNotFound` и комментарий «отсутствие строки — штатная ситуация, но явная ошибка надёжнее `nil, nil`». 174 — «…в классической модели share-nothing пул между запросами не сохранить (кроме persistent connections PDO); долгоживущие среды (Swoole, RoadRunner) держат пулы».

### J-242 — PARTIALLY CORRECT
- **Где / цитата:** ст. 40:66 — «переводит его в состояние `txCtx`»; 195 — «Отмена контекста в `ExecContext` … не откатывает транзакцию автоматически».
- **Вердикт:** 195 верно для контекста `ExecContext`; но отмена контекста, переданного в `BeginTx`, откатывает транзакцию автоматически (`Tx.awaitDone`). Состояния «`txCtx`» нет.
- **Доказательство:** go1.27.1 `src/database/sql/sql.go:2214–2226` — `awaitDone`: `<-tx.ctx.Done()` → `tx.rollback(discardConnection)`.
- **Предлагаемая правка:** 66 — «…резервирует соединение за транзакцией до `Commit` или `Rollback`». 195 — «…отмена контекста `ExecContext` прерывает команду, но не транзакцию. А отмена контекста, переданного в `BeginTx`, откатит транзакцию автоматически».

### J-243 — PARTIALLY CORRECT
- **Где / цитата:** ст. 41:88 — «Всегда оборачивайте входящий поток `tar.NewReader` в `bufio.Reader`, а целевые файлы при записи — в `bufio.Writer`»; 31 — «доступ к любому файлу за $O(1)$»; 245 — GIL «блокирует параллельную распаковку».
- **Вердикт:** `io.Copy(f, tr)` и так идёт крупными кусками (у `*os.File` есть `ReadFrom`); `bufio.Writer` здесь не нужен. Поправка к брифу: `bufio.Writer` **не** отключает `ReaderFrom` — у него свой `ReadFrom`, который при пустом буфере делегирует нижележащему. Индекс ZIP действительно позволяет открыть файл сразу, но весь Central Directory при `NewReader` читается в память. GIL освобождается в zlib-распаковке (не проверял).
- **Доказательство:** go1.27.1 `src/bufio/bufio.go`, `(*Writer).ReadFrom`: `if readerFromOK && b.Buffered() == 0 { nn, err := readerFrom.ReadFrom(r) … }`.
- **Предлагаемая правка:** 88 — «Буферизуйте источник архива (`bufio.NewReader(file)`), если он отдаёт данные мелкими порциями. Запись в файл через `io.Copy` и так идёт крупными блоками». 31 — «…`zip.NewReader` читает Central Directory целиком и строит индекс, после чего любой файл открывается без чтения архива с начала».

### J-244 — INCORRECT
- **Где / цитата:** ст. 43:3 — «Кен Томпсон и Деннис Ритчи сформулировали принцип: программы должны делать одну вещь хорошо»; 233 — GIL.
- **Вердикт:** принцип сформулирован Дугласом Макилроем (см. J-166). Про GIL на вводе-выводе — см. J-201.
- **Доказательство:** McIlroy, Pinson, Tague, «UNIX Time-Sharing System: Foreword», BSTJ 1978 — по памяти.
- **Предлагаемая правка:** «Ещё в Bell Labs Дуглас Макилрой сформулировал принцип: пусть каждая программа делает одну вещь хорошо…».

### J-245 — INCORRECT
- **Где / цитата:** ст. 44:152–189 — `createNonblockingSocketAndEpoll`; 205 — `unix.MADV_EXEC`, `MAP_JIT`.
- **Вердикт:** `epfd` создаётся и при успехе теряется (функция возвращает только `fd`) — утечка дескриптора. Неблокирующий режим проще задать флагом `SOCK_NONBLOCK` в `Socket`. Константы `unix.MADV_EXEC` в `x/sys/unix` для Linux нет; `MAP_JIT` — только macOS. Не упомянуты `SyscallConn()`/`RawConn` для работы с fd сокетов `net`.
- **Доказательство:** код статьи (строки 171, 188); `golang.org/x/sys@v0.48.0/unix` — `MADV_EXEC` в `zerrors_linux*.go` не найден, `MAP_JIT` — только в `zerrors_darwin_arm64.go:963`.
- **Предлагаемая правка:** `func createNonblockingSocketAndEpoll() (fd, epfd int, err error)` и `unix.Socket(unix.AF_INET, unix.SOCK_STREAM|unix.SOCK_NONBLOCK|unix.SOCK_CLOEXEC, …)`. 205 — «…используйте `mmap` с `PROT_READ|PROT_WRITE`, затем `mprotect(PROT_READ|PROT_EXEC)`; на macOS — `MAP_JIT`». Добавить: «Для сокетов, созданных пакетом `net`, доступ к fd — через `conn.(syscall.Conn).SyscallConn()`».

### J-246 — INCORRECT
- **Где / цитата:** ст. 45:126–143 — `FuzzParseInt` с инвариантом `strconv.Itoa(val) != s && s[0] != '+' && s != "-0"`.
- **Вердикт:** ведущие нули (`"00"`, `"007"`) инвариант нарушают — фаззер сразу находит «баг» в самом тесте.
- **Доказательство:** запуск теста из статьи: `go test -fuzz=FuzzParseInt` → падение через 0,13 с на `"00"` (`invariant broken: strconv.Itoa(0) != "00"`).
- **Предлагаемая правка:** проверять обратимость в другую сторону: `f.Fuzz(func(t *testing.T, n int) { s := strconv.Itoa(n); got, err := strconv.Atoi(s); if err != nil || got != n { t.Fatalf(…) } })` (seed — `f.Add(123)`), либо для строкового входа сравнивать `Atoi(Itoa(v)) == v`.

### J-247 — VERIFIED
- **Где / цитата:** ст. 48, вся статья; 90 — «пламенная диаграмма Flame Graph (flame graph / 火焰 graph)».
- **Вердикт:** пропуски подтверждены (`html/template`, `net/netip`, `mime/multipart`, `os/signal`, `iter`/`unique`/`weak`, `runtime/trace`, `testing/fstest`). Посторонние иероглифы в строке 90 есть и в исходнике, и на сайте.
- **Доказательство:** `grep -c 火焰` — 1 в исходнике ст. 48 и 1 в `dist/docs/06-…/48-*.html`.
- **Предлагаемая правка:** 90 — «…на которые указывает flame graph». В раздел «Что изучить дальше» — краткий список перечисленных пакетов.

---

## 5. Находки отчёта слепых зон (B)

### B-01 — INCORRECT
- **Где / цитата:** ст. 29:64–79 — «// ✅ Хорошо: стриминг, минимизация аллокаций»; `var item PayloadItem` вне цикла; `for dec.More() { dec.Decode(&item) … }`; итог 181.
- **Вердикт:** подтверждаю. `Decode` в существующую структуру не обнуляет поля, которых нет в очередном объекте: они остаются от предыдущего. Если среди полей флаги прав или владелец — это уязвимость.
- **Доказательство:** запуск на go1.27.1 (реализация v2 по умолчанию): поток `{"id":1,"admin":true,"name":"root"} {"id":2}` → `{ID:1 Admin:true Name:root}`, затем `{ID:2 Admin:true Name:root}`.
- **Предлагаемая правка:** объявлять `var item PayloadItem` внутри цикла (код — в J-124) и добавить комментарий: «новая переменная на каждый элемент: `Decode` не обнуляет поля, отсутствующие в JSON».

### B-02 — INCORRECT
- **Где / цитата:** ст. 36:95 — `if !ok || user != "admin" || pass != os.Getenv("DEBUG_PASS") {`.
- **Вердикт:** подтверждаю. При незаданной переменной `os.Getenv` возвращает `""`, и запрос с `admin:` и пустым паролем проходит.
- **Доказательство:** запуск: `DEBUG_PASS` не задан, `req.SetBasicAuth("admin", "")` → условие отказа ложно, доступ разрешён.
- **Предлагаемая правка:**
  ```go
  pass := os.Getenv("DEBUG_PASS")
  if pass == "" {
      return errors.New("DEBUG_PASS is not set: debug server disabled")
  }
  // …
  u, p, ok := r.BasicAuth()
  if !ok || subtle.ConstantTimeCompare([]byte(u), []byte("admin")) != 1 ||
      subtle.ConstantTimeCompare([]byte(p), []byte(pass)) != 1 {
      http.Error(w, "Unauthorized", http.StatusUnauthorized)
      return
  }
  ```
  и слушать `127.0.0.1:6060`.

### B-03 — INCORRECT
- **Где / цитата:** ст. 36:10 — «если вы не используете `http.ListenAndServe` на default-мультиплексоре, профилировщик останется недоступным»; 85 — `// Явная регистрация pprof (без импорта _ "net/http/pprof")`.
- **Вердикт:** подтверждаю. Опасность обратная: `init()` пакета `net/http/pprof` **всегда** регистрирует `/debug/pprof/…` на `http.DefaultServeMux`, `expvar` — `/debug/vars`. Сервис, запущенный как `http.ListenAndServe(addr, nil)`, открывает их наружу. Вызвать `pprof.Index` без импорта пакета невозможно, поэтому «без импорта» в примере неверно: регистрация на `DefaultServeMux` всё равно произойдёт.
- **Доказательство:** go1.27.1 `src/net/http/pprof/pprof.go:95–104` — `func init()` с `http.HandleFunc(prefix+"/debug/pprof/", Index)` и ещё четырьмя путями. Запуск: после `import _ "net/http/pprof"` запрос к `http.DefaultServeMux` на `/debug/pprof/cmdline` → `200`, тело — командная строка процесса.
- **Предлагаемая правка:** 10 — «Импорт `net/http/pprof` (и `expvar`) регистрирует эндпоинты на `http.DefaultServeMux`. Если основной сервер запущен с `nil`-обработчиком (`http.ListenAndServe(":8080", nil)`), профилировщик окажется доступен всем. Основной сервер — только со своим `ServeMux`; отладочный — на `127.0.0.1` или отдельном порту». 85 — «// Регистрация pprof на отдельном mux (импорт пакета всё равно добавит обработчики в DefaultServeMux — не используйте его в основном сервере)».

### B-04 — VERIFIED
- **Где / цитата:** ст. 33:14–20 — «Начиная с Go 1.22, встроенный роутер … Методы в маршрутах: `GET /users/{id}`»; ст. 1:133; ст. 48:52.
- **Вердикт:** подтверждаю пропуск. Новые паттерны включаются строкой `go` основного модуля: при `go 1.21` в `go.mod` паттерн `"GET /users/{id}"` трактуется буквально, и запросы получают 404 без ошибки при регистрации.
- **Доказательство:** запуск на тулчейне go1.27.1 в модуле с `go 1.21`: `mux.HandleFunc("GET /users/{id}", …)` + `GET /users/42` → `404 404 page not found`; при `go 1.27` (эксперимент J-134) — `200 id=42`. `src/internal/godebugs/table.go:48` — `httpmuxgo121`, `Changed: 22`.
- **Предлагаемая правка:** в ст. 33 после списка возможностей — «Новые паттерны работают, только если в `go.mod` указано `go 1.22` или новее. При старой строке `go` маршрут `"GET /users/{id}"` будет искаться буквально, и сервер ответит 404».

### B-05 — INCORRECT
- **Где / цитата:** ст. 43:126–135 (комментарии «Если процесс завершился с ненулевым кодом выхода» / «Если произошла отмена контекста»); 222 — «Обычный `error` свидетельствует о том, что процессу не удалось запуститься вовсе … `*exec.ExitError` означает, что процесс … завершился с ненулевым кодом выхода».
- **Вердикт:** подтверждаю. Когда контекст истекает во время работы процесса, `CommandContext` убивает его, и `Run` возвращает `*exec.ExitError` (`signal: killed`, код −1), а не ошибку контекста. Ветка «отмена контекста» в примере для этого случая недостижима. Что `exitErr.Stderr` заполняется только `Output()` при `cmd.Stderr == nil` — по документации, не запускал.
- **Доказательство:** запуск: `exec.CommandContext(ctx /*200ms*/, "sleep", "5").Run()` → `signal: killed`, `errors.As(err, &exitErr) == true`, `ExitCode() == -1`, `errors.Is(err, context.DeadlineExceeded) == false`, `ctx.Err()` → `context deadline exceeded`.
- **Предлагаемая правка:**
  ```go
  if err := cmd.Run(); err != nil {
      if ctx.Err() != nil { // таймаут или отмена: процесс убит
          return fmt.Errorf("task cancelled: %w (%v)", ctx.Err(), err)
      }
      var exitErr *exec.ExitError
      if errors.As(err, &exitErr) {
          return fmt.Errorf("process failed with code %d: %s", exitErr.ExitCode(), stderr.String())
      }
      return fmt.Errorf("start failed: %w", err)
  }
  ```
  Ответ 222 — «…`*exec.ExitError` значит, что процесс запустился и завершился неуспешно — с ненулевым кодом или от сигнала, в том числе убитый по таймауту `CommandContext`. Причину отмены проверяйте через `ctx.Err()`».

### B-06 — INCORRECT
- **Где / цитата:** ст. 28:7 — «делает Go-приложения полностью иммунными к атакам ReDoS …, где злоумышленник отправляет специально составленный паттерн или строку»; 115; итог 131.
- **Вердикт:** подтверждаю. Линейность гарантирована по длине входа при фиксированном выражении; время — O(m·n). Короткий паттерн злоумышленника с ограниченными повторами раздувает программу и даёт сотни миллисекунд CPU на запрос. Номера CVE по `regexp/syntax` 2022 г. не проверял.
- **Доказательство:** запуск на go1.27.1, вход — 100 КБ символов `a`: `a.{0,20}b` — 25 мс, `a.{0,200}b` — 168 мс, `(?:a.{0,50}){10}b` — 420 мс. `src/regexp/syntax/parse.go:94` — `maxHeight = 1000`, 103 — `maxSize`; `(a{1000}){1000}` → `invalid repeat count`.
- **Предлагаемая правка:** 7 — «…иммунными к ReDoS от вредоносной **строки**: время растёт линейно с длиной входа. Если же паттерн задаёт пользователь, время пропорционально и размеру выражения: ограничьте длину паттерна и входа». 115 — добавить: «…и ограничьте длину паттерна, длину входа и время обработки».

### B-07 — PARTIALLY CORRECT
- **Где / цитата:** ст. 6:183 — «используйте `bufio.Reader.ReadBytes('\n')` для потоковой обработки длинных строк»; 184 — «`ReadString` или `ReadBytes` предпочтительнее для сетевого IO».
- **Вердикт:** подтверждаю по сути: `ReadBytes`/`ReadString` накапливают фрагмент до разделителя без предела, и клиент без `\n` может исчерпать память. Это не «потоковая обработка»: строка собирается целиком. Сценарий исчерпания памяти не запускал.
- **Доказательство:** go1.27.1 `src/bufio/bufio.go`, `collectFragments`: цикл с `fullBuffers = append(fullBuffers, buf)` на каждом `ErrBufferFull`, без ограничения размера.
- **Предлагаемая правка:** 183 — «Увеличьте лимит через `scanner.Buffer(buf, max)`. `ReadBytes('\n')` ограничения не имеет: для недоверенного ввода ставьте `io.LimitReader` под `bufio.Reader` или читайте `ReadSlice`/`ReadLine` с обработкой `ErrBufferFull`». 184 — «…для сетевого ввода — только с ограничением длины».

### B-08 — PARTIALLY CORRECT
- **Где / цитата:** ст. 9, раздел 2; 146 — «необходимо предварительно заменять запятые на точки через `strings.Replace`»; итог 163.
- **Вердикт:** подтверждаю главное: `ParseFloat` без ошибки принимает `NaN`, `Inf`, `infinity`, шестнадцатеричные литералы и подчёркивания; `ParseInt(s, 0, …)` — префиксы и `_`. `NaN` обходит проверки вида `amount > limit`. Поправка к отчёту: `"1.234,56"` после замены запятой превращается в `"1.234.56"` и даёт **ошибку**, а не тихое `1.234`. Тихо ломается другой случай: `"1,234"` (английский разделитель тысяч) станет `1.234`.
- **Доказательство:** запуск: `ParseFloat("NaN")`, `("nan")` → `NaN <nil>`; `("-Inf")` → `-Inf`; `("infinity")` → `+Inf`; `("0x1p-2")` → `0.25`; `("1_000")` → `1000`; `ParseInt("0x10", 0, 64)` → 16; `Atoi("1_000")` → `invalid syntax`; `"1.234,56"` после `Replace` → ошибка; для `NaN` и `NaN > 100`, и `NaN <= 100` — `false`.
- **Предлагаемая правка:** в раздел «Ловушки» — «`ParseFloat` принимает `NaN`, `Inf`, `0x1p-2` и `1_000` без ошибки. После разбора внешних данных проверяйте `math.IsNaN`, `math.IsInf` и допустимый диапазон. Замена запятой на точку годится, только если в числе нет разделителей тысяч: `"1,234"` в английской записи станет `1.234`. Для локализованного ввода нужен разбор с учётом локали».

### B-09 — INCORRECT
- **Где / цитата:** ст. 47:3 — «возврат к бескомпромиссной **статической линковке по умолчанию**»; 5 — «копируете один файл в чистый Docker-образ `scratch`»; ст. 44:20 — «нет неявной зависимости от … `libc` (если не используется cgo)».
- **Вердикт:** подтверждаю. При наличии C-компилятора `CGO_ENABLED` по умолчанию `1`, и программа с `net/http` линкуется динамически (cgo-резолвер `net`). В `scratch` такой бинарник не запустится. С Go 1.20 cgo по умолчанию выключается, если C-компилятора нет.
- **Доказательство:** запуск: `go env CGO_ENABLED` → `1`; программа с `import "net/http"` → `file`: `dynamically linked, interpreter /lib64/ld-linux-x86-64.so.2`; с `CGO_ENABLED=0` → `statically linked`. Go 1.20 release notes: «when the CGO_ENABLED environment variable is unset, the CC environment variable is unset, and the default C compiler … is not found in the path, CGO_ENABLED defaults to 0».
- **Предлагаемая правка:** ст. 47:3, 5 — «…Go собирает приложение в один файл; полностью статическим он будет при `CGO_ENABLED=0` (или если на машине сборки нет C-компилятора). Для `scratch` собирайте `CGO_ENABLED=0 go build`». Ст. 44:20 — «…(если cgo выключен: при включённом cgo пакеты `net` и `os/user` используют libc)».

### B-10 — VERIFIED
- **Где / цитата:** ст. 30:127 — «SOAP, банковские шлюзы»; итог 163 — «`encoding/xml` обязателен для интеграций с legacy-системами и финансовыми шлюзами».
- **Вердикт:** подтверждаю пропуск. `encoding/xml` не сохраняет документ при разборе и обратной сериализации (префиксы пространств имён атрибутов и элементов, директивы): CVE-2020-29509 (атрибуты), CVE-2020-29511 (элементы), опубликованы 14.12.2020; команда Go не считает это исправимым в пакете, обходной путь — `mattermost/xml-roundtrip-validator`. Проверять подписи XML (XMLDSig, SAML) через `Unmarshal` → `Marshal` нельзя. CVE-2020-29510 и версии исправлений ограничения глубины (2022) не проверял.
- **Доказательство:** поиск в сессии (Wiz, Arch Linux AVG-1357, Tenable): CVE-2020-29509 — «attribute prefixes», CVE-2020-29511 — «element prefixes», «Upstream Go … does not consider the issue to be fixable … shifted responsibility to SAML packages».
- **Предлагаемая правка:** в итог п. 1 — «…Для подписанных документов (XMLDSig, SAML) не проверяйте подпись поверх `xml.Unmarshal`/`Marshal`: пакет не сохраняет документ при обратной сериализации (CVE-2020-29509, -29511). Используйте специализированные библиотеки с канонизацией».

### B-11 — VERIFIED
- **Где / цитата:** ст. 33:101–107 — `http.Server{ReadHeaderTimeout: 5 * time.Second, IdleTimeout: 120 * time.Second}`; 150; итог 176.
- **Вердикт:** подтверждаю пропуск. `ReadHeaderTimeout` защищает только от медленных заголовков. Медленное тело (slow POST) и медленное чтение ответа держат горутину и соединение без предела: нет `ReadTimeout`, `WriteTimeout`, ограничения тела. Для долгих ответов таймауты снимает `http.ResponseController` (Go 1.20).
- **Доказательство:** поля `http.Server` в go1.27.1 (`go doc net/http.Server`): `ReadTimeout`, `ReadHeaderTimeout`, `WriteTimeout`, `IdleTimeout`; Go 1.20 release notes — `ResponseController` с примером `rc.SetWriteDeadline(time.Time{})`. Атаку slow POST не воспроизводил.
- **Предлагаемая правка:** в пример — `ReadTimeout: 15 * time.Second, WriteTimeout: 30 * time.Second`; в обработчиках — `http.MaxBytesReader`; комментарий: «для стриминга снимите дедлайн в конкретном обработчике: `http.NewResponseController(w).SetWriteDeadline(time.Time{})`».

### B-12 — OUTDATED
- **Где / цитата:** ст. 29:13–15 — «кэшируются в `sync.Map` (`typeCache`)», «внутренний `encodeStatePool`»; 41 — «В сообществе Go активно разрабатывается … `encoding/json/v2`»; итог 180.
- **Вердикт:** подтверждаю. В go1.27.1 `encoding/json` по умолчанию собирается из `v2_*.go` поверх `encoding/json/v2`; файлы классической реализации помечены `//go:build !goexperiment.jsonv2`. Поведение v1 сохранено (проверено на J-022, J-125, J-232, B-01), а описание «под капотом» относится к реализации, которая по умолчанию не используется. Отключение — `GOEXPERIMENT=nojsonv2`.
- **Доказательство:** go1.27.1 `src/encoding/json/encode.go` начинается с `//go:build !goexperiment.jsonv2`; каталог содержит `v2_decode.go`, `v2_encode.go`, `v2_stream.go` и др.; `src/internal/buildcfg/exp.go:87` — `JSONv2: true`. Go 1.27 release notes: «The encoding/json package is now backed by the v2 implementation … GOEXPERIMENT=nojsonv2».
- **Предлагаемая правка:** раздел «Под капотом» — пометить «классическая реализация (до Go 1.26)» и добавить: «С Go 1.27 `encoding/json` работает поверх `encoding/json/v2`: поведение прежнее, разбор заметно быстрее». Строку 41 — по J-123. Согласовать с модулем 5 (B-01 отчёта слепых зон модуля 5).

### B-13 — INCORRECT
- **Где / цитата:** ст. 4:143 — «Если создавать буфер внутри цикла, Escape Analysis гарантированно отправит его в кучу».
- **Вердикт:** подтверждаю. Буфер убегает потому, что передаётся в метод интерфейса `io.Reader`, а не из-за цикла. С конкретным типом тот же `make` внутри цикла остаётся на стеке.
- **Доказательство:** `go build -gcflags=-m`: `make([]byte, 4096)` в цикле с `r io.Reader` → `escapes to heap`; тот же код с `r *bytes.Reader` → `does not escape`.
- **Предлагаемая правка:** «Буфер, переданный в `r.Read` через интерфейс `io.Reader`, уходит в кучу: компилятор не знает, не сохранит ли его реализация. Если создавать его внутри цикла, будет аллокация на каждой итерации. Вынесите буфер из цикла — память выделится один раз».

### B-14 — INCORRECT
- **Где / цитата:** ст. 24:55 — «`unsafe.StringData(s)` / `unsafe.SliceData(b)` | … | `*(*byte)(unsafe.Pointer(s))`».
- **Вердикт:** подтверждаю: строку нельзя преобразовать в `unsafe.Pointer`, «legacy»-вариант не компилируется.
- **Доказательство:** `go build`: `cannot convert s (variable of type string) to type unsafe.Pointer`.
- **Предлагаемая правка:** «`(*reflect.StringHeader)(unsafe.Pointer(&s)).Data` / `(*reflect.SliceHeader)(unsafe.Pointer(&b)).Data` (устарели)».

### B-15 — INCORRECT
- **Где / цитата:** ст. 30:57 — «`TrimLeadingSpace`: игнорирует пробелы перед разделителем».
- **Вердикт:** подтверждаю: флаг убирает пробелы в **начале поля** (после разделителя); пробелы в конце поля остаются.
- **Доказательство:** запуск: `"a ;  b ;c"`, `Comma = ';'`, `TrimLeadingSpace = true` → `["a " "b " "c"]`.
- **Предлагаемая правка:** «`TrimLeadingSpace`: убирает пробелы в начале каждого поля (пробелы в конце поля остаются)».

### B-16 — INCORRECT
- **Где / цитата:** ст. 40:124 — «последующий вызов `Rollback()` в `defer` безопасно выполнит no-op … и не вернет ошибку»; 115.
- **Вердикт:** подтверждаю: после `Commit` `Rollback` возвращает `sql.ErrTxDone`. Вызов безопасен, но ошибка есть — обёртка, которая логирует ошибку отложенного `Rollback`, будет писать ложные ошибки.
- **Доказательство:** go1.27.1 `src/database/sql/sql.go`, `Tx.rollback` — `return ErrTxDone`, если транзакция уже завершена (строка 2333).
- **Предлагаемая правка:** «…`Rollback()` ничего не сделает и вернёт `sql.ErrTxDone` — эту ошибку в `defer` игнорируйте: `if err := tx.Rollback(); err != nil && !errors.Is(err, sql.ErrTxDone) { log… }`».

### B-17 — INCORRECT
- **Где / цитата:** ст. 31:192 — «Для `SO_REUSEPORT` нужен `syscall.SetsockoptInt`».
- **Вердикт:** подтверждаю по устройству `net.Listen`: сокет создаётся, привязывается и переводится в режим прослушивания одним вызовом, поэтому опцию, выставленную потом на полученном fd, `bind` уже не учтёт. Ставить её нужно в `net.ListenConfig.Control`, который вызывается до `bind`. Экспериментом с двумя процессами не проверял.
- **Доказательство:** go1.27.1 `src/net/dial.go` — поле `Control func(network, address string, c syscall.RawConn) error` у `ListenConfig` с описанием «called after creating the network connection but before binding it» (по документации; строки 209–211 просмотрены частично).
- **Предлагаемая правка:**
  ```go
  lc := net.ListenConfig{Control: func(network, address string, c syscall.RawConn) error {
      var serr error
      err := c.Control(func(fd uintptr) {
          serr = unix.SetsockoptInt(int(fd), unix.SOL_SOCKET, unix.SO_REUSEPORT, 1)
      })
      return errors.Join(err, serr)
  }}
  ln, err := lc.Listen(ctx, "tcp", ":8080")
  ```

### B-18 — INCORRECT
- **Где / цитата:** ст. 25:28 — «**Introsort**: Отслеживает глубину рекурсии. Если она превышает `2 * log2(n)`, алгоритм переключается на Heapsort»; диаграмма 49.
- **Вердикт:** подтверждаю: в Go счётчик `limit = bits.Len(n)` уменьшается только после **несбалансированного** разбиения, и heapsort запускается при `limit == 0`. Глубина рекурсии сама по себе переход не вызывает.
- **Доказательство:** go1.27.1 `src/slices/sort.go:32` — `pdqsortCmpFunc(x, 0, n, bits.Len(uint(n)), cmp)`; `src/slices/zsortanyfunc.go:78` — `if limit == 0` (heapsort), 84–86 — `if !wasBalanced { … limit-- }`.
- **Предлагаемая правка:** «**Страховка от худшего случая:** алгоритм считает несбалансированные разбиения; после примерно log₂ n таких разбиений он переключается на Heapsort, гарантируя O(n log n)». Диаграмма — «Слишком много плохих разбиений?».

### B-19 — OUTDATED
- **Где / цитата:** ст. 37:27 — «Вызов `crypto/rand` инициирует переход в Ring 0»; 76 — «Каждый вызов `rand.Read()` требует переключения контекста … ~100-300 наносекунд, что в 50-100 раз медленнее `math/rand`».
- **Вердикт:** подтверждаю: с Go 1.24 на Linux 6.11+ `crypto/rand` использует `getrandom` через vDSO, без перехода в ядро на каждый вызов. Совет запрашивать крупные порции остаётся разумным.
- **Доказательство:** Go 1.24 release notes: «On Linux 6.11 and later, Reader now uses the getrandom system call via vDSO. This is several times faster, especially for small reads». go1.27.1 `src/runtime/vgetrandom_linux.go` есть. Бенчмарк (ядро 7.2.11): `crypto/rand.Read` 16 байт — 41 нс; глобальный `math/rand.Intn` — 6,9 нс (≈ 6×, а не 50–100×).
- **Предлагаемая правка:** 27 — «…На Linux 6.11+ (Go 1.24+) `getrandom` вызывается через vDSO, без перехода в ядро». 76 — «На старых ядрах каждый `rand.Read` — системный вызов (сотни наносекунд); с vDSO — десятки наносекунд. Всё равно запрашивайте нужный объём одним вызовом».

---

## 6. Замечания отчёта слепых зон к брифу

Каждое замечание сверено; итоги внесены в соответствующие пункты.

| Замечание | Результат проверки | Где учтено |
|---|---|---|
| J-011 / К-3: ст. 4:249, 277 | Подтверждаю: тот же тезис «не блокирует потоки ОС» | J-011 (правка ст. 4) |
| J-027: ст. 38:222–225 | Подтверждаю: литерал с `TLSClientConfig` без `ForceAttemptHTTP2` и `Proxy` | J-027, J-146 (код через `Clone()`) |
| J-028: `rand.Seed` — no-op с Go 1.24 | Подтверждаю: Go 1.24 release notes, `randseednop` (`Changed: 24`) | J-028 |
| J-030: TLS-сжатие | Подтверждаю: TLS-компрессия отключена после CRIME, в TLS 1.3 её нет | J-030 |
| J-086: гонка при фоновом `Flush` | Подтверждаю по устройству `bufio.Writer` и `commonHandler.mu` (эксперимент не ставил) | J-086 |
| J-094: `asynctimerchan` удалена в 1.27 | Подтверждаю: release notes 1.27, `table.go:110`, запуск при `go 1.21` → `cap = 0` | J-094 |
| J-123/124/125/232: доказательная база для 1.27 | Подтверждаю: по умолчанию работает v2; выводы о поведении проверены запуском в обоих режимах (J-125, J-232) | J-123, J-232, B-12 |
| J-232 → Medium | Согласен: рассинхронизация парсеров при дубликатах и регистре — проблема безопасности | J-232 |
| J-202 → ст. 43 | Подтверждаю запуском (`-f<файл>` разобран `grep` как опция) | J-202 |
| J-143: строка 86 — не комментарий | Согласен по тексту: выражение стоит до `//`; сборку не запускал | J-143 |

---

## 7. Непроверенное

**Целиком `NOT CHECKED`:**
- **J-208** (ст. 14, `#embed` в C/C++): поддержку в C23-компиляторах и статус в C++26 не проверял.
- **J-212** (ст. 16, Logback `AsyncAppender`, pino и SIMD): документацию Logback и pino не открывал.

**Подпункты, оставшиеся без проверки** (статус пункта поставлен по проверенной части):
- **Нет репозитория Go с историей:** точные версии изменений, которые видны только по `git log` исходников — удаление `convT2E` (J-045), происхождение константы 32 КБ (J-053), появление vfork-пути в `os/exec` (J-157, по alt — 1.9), версия, с которой работает `internal/strconv/uscale.go` (J-068, F-02), проверка цикла в `json.Marshal` с 1.15 (J-125), «3 минуты» keep-alive в старом сервере (J-136), минимальная версия TLS 1.2 у клиента с 1.18 (J-146), потоковые таймеры CPU-профиля с 1.18 (J-237), allocation headers с 1.22 (J-228), версия анализатора `errorsas` в vet (J-175), версия документирования паники в `sync.Once` (J-220).
- **Release notes, которые не открывал:** Go 1.10 (`strings.Builder`, J-064), 1.14 (open-coded defer, per-P таймеры, асинхронное вытеснение — J-101, J-092, J-165), 1.15, 1.16, 1.17, 1.18, 1.21.
- **Исходники Go 1.23 и раньше** (в окружении только 1.27.1): размер бакета старой `map` посчитан по раскладке (J-021); устройство `context` в 1.20 (J-089) — по брифу.
- **Не запускал:** код на Windows (J-075); сборку плагина (J-163, нужен cgo и отдельная сборка); переключение network namespace (J-032, нужен root); исчерпание FD в accept-цикле (J-127); атаки slow POST и OOM через `ReadBytes` (B-11, B-07); паники ключей map с несравнимым типом и NaN (J-118); дизассемблирование `cmp.Compare` на `SETL/SETG` и `strconv` на векторизацию (J-113, J-067); сортировку указателей на разбросанные по куче объекты (J-114); отложенное фоновое чтение `net/http` при обрыве клиента (J-091); бенчмарки размеров буфера `io.Copy` (J-053) и CSV (J-126); двойное округление `float32(ParseFloat(s, 64))` (J-195); сборку примера `setupDebugServer` (J-143); `SO_REUSEPORT` с двумя процессами (B-17); поведение `exitErr.Stderr` (B-05).
- **Внешние документы, которые не открывал:** Itanium C++ ABI (J-046), Microsoft «Naming Files, Paths, and Namespaces» (J-075), RFC 7541 и RFC 8446 (J-030), RFC 9110 (J-155), NIST SP 800-38D (J-148), go.dev/doc/gc-guide (J-104, J-165), `man 2 getrandom`, `man 2 open` (J-145, J-153), JEP 254 и JEP 328 (J-200, J-143), документация Docker/journald (J-172), Java/Python/PHP/.NET (J-201, J-216, J-218, J-238, J-241, J-243 — GIL), статус `golang/go#18152` и переезд `nhooyr.io/websocket` (J-170), статус `lib/pq` (J-178), лимит bcrypt 72 байта (J-239).
- **Атрибуция (J-166):** K&R § 2.7, BSTJ 1978 (Макилрой), Go Proverbs и «Unix for Beginners» — по общеизвестным источникам, в сессии не открывал. Для эпиграфов ст. 7, 8, 11, 12, 13, 14, 17, 18, 20 поиск первоисточника не делал; вывод «авторский текст» — по содержанию (упоминания Go-пакетов и современных технологий).
- **CVE:** CVE-2020-29510 (директивы XML) и версии исправлений `encoding/xml` 2022 г. (B-10); номера CVE `regexp/syntax` 2022 г. (B-06).

---

## 8. Пропущенное брифом (F)

Ниже — то, чего нет ни в брифе, ни в отчёте слепых зон. Большинство найдено при проверке смежных пунктов; где это уточнение к пункту брифа, правка внесена туда, а здесь дана ссылка.

### F-01 — OUTDATED
- **Где / цитата:** ст. 34:69–70 — «соединение **никогда не вернется в пул**»; итог 143.
- **Вердикт:** бриф (J-138) не учёл изменение Go 1.27: `Response.Body.Close()` сам дочитывает небольшой остаток тела, и соединение переиспользуется.
- **Доказательство:** Go 1.27 release notes (`net/http`); запуск: тело 1 КБ → соединение переиспользовано, 1 МБ → нет.
- **Предлагаемая правка:** см. J-138.

### F-02 — OUTDATED
- **Где / цитата:** ст. 9:61 — «Dragon4 / Grisu3 / Ryu».
- **Вердикт:** бриф (J-068) называет текущим алгоритмом Ryū; в go1.27.1 преобразование чисел с плавающей точкой реализовано иначе — «fast unrounded scaling» (`internal/strconv/uscale.go`, 2026), файлов Ryū и Eisel–Lemire нет.
- **Доказательство:** go1.27.1 `src/internal/strconv/uscale.go:1–6`; `ls src/internal/strconv` — нет `ftoaryu.go`, `eisel_lemire.go`. Версию, с которой это работает, не установил (в release notes 1.26 и 1.27 не упомянуто).
- **Предлагаемая правка:** см. J-068 (формулировка без привязки к конкретному алгоритму).

### F-03 — INCORRECT
- **Где / цитата:** ст. 16:185 — «`encoding/json` внутри `JSONHandler` не использует кэш рефлективных структур для анонимных `slog.Any` значений»; там же снова `slog.Valuer`.
- **Вердикт:** `json.Marshal` кэширует кодировщики по типу для любых значений; интерфейс называется `slog.LogValuer`. Бриф (J-084) только просил проверить эту строку.
- **Доказательство:** см. J-084 и J-016.
- **Предлагаемая правка:** см. J-084.

### F-04 — OUTDATED
- **Где / цитата:** ст. 44:50–52 (механика системного вызова).
- **Вердикт:** бриф (J-159) пишет про состояние P `_Psyscall`; в go1.27.1 его больше нет (`_Psyscall_unused`), признак системного вызова — состояние горутины `_Gsyscall`.
- **Доказательство:** go1.27.1 `src/runtime/runtime2.go:143–146`.
- **Предлагаемая правка:** см. J-159.

### F-05 — OPINION / NOT A FACT CLAIM
- **Где / цитата:** ст. 42:145 — «Вызов `Reset(w)` … не совершая ни единой аллокации в куче! Это … ускоряет инициализацию на 40–60%».
- **Вердикт:** «ни единой аллокации» подтверждено замером; «40–60%» — без источника (на деле выигрыш от пула больше: новый писатель аллоцирует около мегабайта, J-154).
- **Доказательство:** `testing.AllocsPerRun`: `gz.Reset(io.Discard); gz.Write(…); gz.Close()` → 0 аллокаций; `gzip.NewWriter` + запись → ~1,08 МБ.
- **Предлагаемая правка:** «…`Reset(w)` переиспользует внутренние буферы (около мегабайта на писатель) без новых аллокаций».

### F-06 — INCORRECT
- **Где / цитата:** ст. 33:62–70 — «// ✅ Production-ready клиент» с литералом `&http.Transport{…}`.
- **Вердикт:** бриф (J-027) разбирает литералы ст. 34 и 38; у ст. 33 HTTP/2 сохраняется (нет `DialContext`/`TLSClientConfig`), но нет `Proxy` — переменные `HTTP(S)_PROXY` перестанут работать, и нет таймаута подключения (`DialContext` по умолчанию без `Timeout`; общий `Client.Timeout` его покрывает частично).
- **Доказательство:** запуск: `(&http.Transport{}).Proxy == nil`; `DefaultTransport` — `ProxyFromEnvironment` и `Dialer{Timeout: 30s}`.
- **Предлагаемая правка:** собрать клиент через `http.DefaultTransport.(*http.Transport).Clone()` и менять нужные поля (код — в J-027).

