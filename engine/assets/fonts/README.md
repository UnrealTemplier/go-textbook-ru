# Шрифт кода: Engine Mono

`EngineMono-Variable.woff2` — подмножество вариативного Cascadia Code (Microsoft, SIL OFL 1.1; текст лицензии — `OFL-cascadiacode.txt`). Ось веса `wght` 200–700 сохранена, лигатуры и `zero` на месте.

Лицензия закрепляет за именем «Cascadia Code» статус зарезервированного, поэтому изменённая копия названа **Engine Mono** (таблица имён и `font-family` в `style.css`). Системный «Cascadia Code» остаётся запасным в стеке `--font-mono`.

Состав: Basic Latin, Latin-1 и Latin Extended-A, кириллица (U+0400–04FF), типографская пунктуация, стрелки, математика, Box Drawing и блоки.

## Как пересобрать

Нужны `fonttools` и `brotli` — **только для этой операции**, в зависимости сборки они не входят. Исходник: `CascadiaCode_VariableFont_wght.ttf` из релиза Cascadia Code.

```bash
pyftsubset CascadiaCode_VariableFont_wght.ttf \
  --unicodes="U+0020-007E,U+00A0-017F,U+0400-04FF,U+2010-2027,U+2030-203A,U+20A0-20BF,U+2116,U+2122,U+2190-21FF,U+2200-22FF,U+2300-23FF,U+2500-259F,U+25A0-25FF,U+2713,U+2717,U+FEFF" \
  --layout-features='*' --flavor=woff2 --output-file=EngineMono-Variable.woff2
```

Затем в таблице имён (`name`, ID 1, 3, 4, 6) заменить имя на «Engine Mono» через `fontTools.ttLib`.
