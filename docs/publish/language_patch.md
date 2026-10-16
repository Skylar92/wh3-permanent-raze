# Языковые патчи: что писать на страницах

Каждый патч `permanent_raze_<код>.pack` выкладывается отдельным предметом. В Steam основной мод указывается в «Required Items», на Nexus — в «Requirements».

| Код | Язык | Название страницы |
|-----|------|-------------------|
| en | English | Raze Forever — English |
| ru | Русский | Стереть навсегда — русский |
| ge | Deutsch | Raze Forever — Deutsch |
| fr | Français | Raze Forever — Français |
| it | Italiano | Raze Forever — Italiano |
| sp | Español | Raze Forever — Español |
| pl | Polski | Raze Forever — Polski |
| cz | Čeština | Raze Forever — Čeština |
| tr | Türkçe | Raze Forever — Türkçe |
| br | Português (Brasil) | Raze Forever — Português (Brasil) |
| kr | 한국어 | Raze Forever — 한국어 |
| cn | 简体中文 | Raze Forever — 简体中文 |
| zh | 繁體中文 | Raze Forever — 繁體中文 |

Описание (BBCode, одно на все патчи; `<LANGUAGE>` заменить):

```
[h1]Raze Forever — <LANGUAGE>[/h1]
Full <LANGUAGE> texts for [b]Raze Forever[/b]: the option is called "Raze Forever" with a detailed tooltip. Optional — the main mod already works in every game language. Enable it together with the main mod.

Requires: Raze Forever (main mod).
```

Переводы, кроме английского и русского, сделаны по официальной терминологии игры, но не вычитаны носителями. Правки приветствуются: тексты лежат в `tools/texts.py`.

## Чек-лист публикации

- Картинка-превью для Steam: `<имя пака>.png` рядом с паком в папке `data` (PNG, до ~1 МБ, обычно 256×256 или 512×512). У основного мода и патчей можно сделать одну и ту же картинку с подписью языка.
- Steam: выкладывается через лаунчер игры (Mod Manager → Upload). Сначала основной мод, потом патчи с ним в «Required Items».
- Nexus: основной файл `permanent_raze.pack` в «Main files», патчи в «Optional files» той же страницы (так проще, чем 12 отдельных страниц).
