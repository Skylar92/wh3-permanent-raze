# Raze Forever / Стереть навсегда

> *"Some places should never rise again."*

**Archaon is not the only one who can end the world.** This Total War: WARHAMMER III mod gives every culture a **Raze Forever** option next to the usual Raze. The settlement is wiped off the map, and its ruins can never be occupied or colonised again, by anyone, you included. It is the same permanent block Archaon uses on his Lord of the End Times path, now available to every faction.

| | |
|---|---|
| **Game** | Total War: WARHAMMER III, update 9.0 (Lords of the End Times) |
| **Cultures** | all, except Nagash's Undead Legions |
| **Languages** | every game language |
| **Save-game** | safe to add mid-campaign, do not remove mid-campaign |
| **Tests** | 83 automated tests (pack/db encoding, generated options, the campaign script) |

*Русская версия ниже.*

## Features

- **Raze Forever** option after capturing a settlement, for every culture except Nagash's Undead Legions (devastation is already their whole mechanic).
- The ruins get the vanilla "devastated" look and a permanent occupation block — the engine's own `block_region_occupation`, not an "AI won't target it" trick.
- When more than half of a province's settlements are in ruins, the province gets the campaign devastation visuals, but only for cultures that fit:
  - Chaos wasteland: Warriors of Chaos, Khorne, Nurgle, Slaanesh, Tzeentch, Daemons of Chaos, Beastmen, Norsca, Chaos Dwarfs;
  - Skaven blight: Skaven;
  - Nagash's dead land: Vampire Counts, Vampire Coast;
  - everyone else (Empire, Bretonnia, Dwarfs, Kislev, Cathay, elves, Lizardmen, Greenskins, Ogres, Tomb Kings…) leaves the land as it is.
- No corruption, no climate change, no faction bonuses. The option costs and loots exactly like that culture's normal raze, minus faction-specific raze rewards (skulls, chivalry, souls…) — those stay with the vanilla Raze.
- Human players only: the AI never gets a permanent block from it.
- Works with Archaon's Destroyer path: his own script still devastates the province and counts it toward his bonuses and long victory.
- Works in every game language: the option reads **"Raze: Scorched Earth"**, using the game's own translations.

## Install

Subscribe to (or copy into `data/`) **`permanent_raze.pack`** and enable it in the launcher.

Safe to add to a running campaign. **Do not remove it mid-campaign**: saves reference the mod's effect bundle and may fail to load, and erased ruins could become settleable again.

## Known behaviour

- On the very first scripted capture of some campaigns (the "Attack the enemy" tutorial mission, e.g. Ku'gath, Skaven, Chaos Dwarfs starts) the game ignores any raze option, vanilla Raze included; the settlement stays with the enemy and the "Capture and occupy" mission follows. Later captures work normally.
- When an endgame crisis ends, the game may clear devastation visuals in its area; the ruins stay blocked.
- The new option uses the same picture as the culture's Raze; only the label and tooltip differ.

## Building from source

Requires Python 3.14 and the game installed (the builder reads vanilla `db.pack`).

```bash
python -m pip install pytest lupa
python -m pytest
python -m tools.build
```

`python -m tools.build` writes `dist/permanent_raze.pack`, thirteen `dist/permanent_raze_<lang>.pack` patches and their Workshop preview images (`tools/preview.py` draws them). `--install [--lang ru]` also copies the main pack and one patch into the game's `data` folder (close the game first). Game path: `tools/paths.py`.

### How it works

- `tools/generate.py` clones each culture's vanilla "raze without occupy" option (one per option group, faction rewards stripped), Archaon's permanent block effect and bundle, and builds the loc entries from `tools/texts.py`.
- `tools/build.py` writes the db tables, loc and the campaign script into PFH5 packs (`tools/packfile.py`, `tools/dbtable.py`, `tools/loc.py`, RPFM schema in `schemas/`).
- `src/script/campaign/mod/permraze.lua` listens for the occupation decision and the raze, then blocks the region, sets the devastated look and, past the province threshold, activates the devastation area. Tested through `lupa` against a mock of the campaign API (`tests/lua/mock_game.lua`).
- In-game checks: `docs/ingame-checklist.md`; store page texts: `docs/publish/`.

### Translations

All texts live in [`tools/texts.py`](tools/texts.py): `VANILLA_TEXTS` for the main pack (references to the game's own strings via `{{tr:key}}`) and `TEXTS` for the patches. English and Russian are written by the authors; the other languages follow the game's own official wording for "Raze" and "ruins" but have not been proofread by native speakers. Corrections are very welcome — open an issue or a pull request.

## Credits

- [RPFM](https://github.com/Frodo45127/rpfm) and its [schemas](https://github.com/Frodo45127/rpfm-schemas) by Frodo45127 — the table layouts in `schemas/` come from there.
- Creative Assembly, for Archaon's devastation mechanic this mod borrows.

## License

The mod's code, scripts and texts are released under the [MIT License](LICENSE) © 2026 Skylar92. Total War: WARHAMMER III and its game data, art and mechanics belong to Creative Assembly and Games Workshop; this is an unofficial fan mod and is not endorsed by them.

---

## Стереть навсегда (по-русски)

> *«Есть места, которым не суждено подняться снова».*

**Конец света теперь не только у Архаона.** Мод для Total War: WARHAMMER III. Рядом с обычным «Разрушить» у каждой культуры появляется **«Стереть навсегда»**: поселение исчезает с карты, и руины больше никто и никогда не сможет занять или заселить, включая самого игрока. Это тот же вечный запрет, что у Архаона на пути «Повелителя Конца Времён», только для всех фракций.

### Что делает

- Кнопка есть у всех культур, кроме Легионов Нежити Нагаша: опустошение и так их суть.
- Руины выглядят опустошёнными и закрыты для заселения встроенным в движок запретом, а не трюком «ИИ туда не ходит».
- Когда больше половины поселений провинции в руинах, земля выгорает, но только у тех, кому это по лору: хаосная пустошь у Хаоса, его богов, Демонов, Зверолюдов, Норски и Гномов Хаоса; скавенская у Скавенов; мёртвая земля Нагаша у Вампиров и Вампирского побережья. У остальных земля не меняется.
- Ни скверны, ни смены климата, ни бонусов. Цена и добыча как у обычного разрушения, но без фракционных наград (черепа, честь, души и т.п.): они остаются у обычной кнопки.
- Только для игроков: ИИ вечный запрет не получает.
- Совместим с путём «Разрушителя» у Архаона: провинцию опустошает и засчитывает его собственная механика.
- Работает на любом языке игры: кнопка называется **«Разрушить: Выжженная земля»**, по официальным переводам игры.

### Установка

Подпишитесь на мод (или положите **`permanent_raze.pack`** в папку `data`) и включите его в лаунчере.

Можно добавлять в идущую кампанию. **Не удаляйте мод посреди кампании**: сохранение может не загрузиться, а стёртые руины могут снова стать заселяемыми.

### Известное поведение

- На первом обучающем захвате кампании (задание «Нападите на врага», например старт Ку'гата, скавенов, гномов Хаоса) игра игнорирует любое разрушение, в том числе обычное: поселение остаётся у врага, и выдаётся задание «Захватите и оккупируйте». Дальше всё работает.
- После окончания эндгейм-кризиса игра может убрать выжженную землю в его области, но руины остаются заблокированными.
- У новой кнопки та же картинка, что у «Разрушить», отличаются только подпись и подсказка.
