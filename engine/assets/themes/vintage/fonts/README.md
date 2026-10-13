# Шрифты Vintage и Retro Manual

Все файлы — подмножества оригиналов в woff2 (латиница, Latin-1, Latin Extended-A, кириллица, пунктуация, стрелки), с сохранённой осью веса у Bitter. Лицензии — `OFL-*.txt`.

| Файл | Исходник | Примечание |
|---|---|---|
| `Bitter-Variable.woff2`, `Bitter-Italic-Variable.woff2` | Bitter (Google Fonts) | вес 100–900 |
| `CourierPrime-Regular.woff2`, `CourierPrime-Bold.woff2` | Courier Prime | только латиница |
| `PTMono-Regular.woff2` | PT Mono (ParaType) | кириллица для кода; имя в таблице имён изменено на «Vintage Cyrillic Mono» (имя «PT Mono» зарезервировано лицензией) |

## Как пересобрать

Нужны `fonttools` и `brotli` — только для этой операции, в зависимости сборки они не входят.

```bash
pyftsubset <исходник>.ttf \
  --unicodes="U+0020-007E,U+00A0-017F,U+0400-04FF,U+2010-2027,U+2030-203A,U+20A0-20BF,U+2116,U+2122,U+2190-21FF,U+2212,U+2215,U+2248,U+2260,U+2264-2265,U+25A0-25FF,U+FEFF" \
  --layout-features='*' --flavor=woff2 --output-file=<имя>.woff2
```
