# Публикация

## Steam Workshop

1. `python -m tools.build --install` — кладёт `permanent_raze.pack` и превью `permanent_raze.png` в папку `data` игры (игра должна быть закрыта).
2. Лаунчер игры → Mod Manager → `permanent_raze` → загрузка, тег **Campaign**, принять соглашение Workshop.
3. На странице мода в Steam: название **Raze Forever**, описание из `main_en.bbcode`; русское описание из `main_ru.bbcode` через выбор языка; **Visibility → Public**.
4. Подписаться на свой мод и снять галочку с локальной копии в лаунчере, чтобы игра не грузила две копии.

## Nexus Mods

- Файл: `dist/permanent_raze.pack` в «Main files».
- Описание: те же `main_en.bbcode` / `main_ru.bbcode` (Nexus тоже понимает BBCode).
- Картинка: `dist/permanent_raze.png`.
- Permissions: использовать и изменять можно с указанием автора (как в лицензии MIT).
