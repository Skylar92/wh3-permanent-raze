<p align="center">
  <img src="assets/preview.png" alt="Raze Forever" width="360">
</p>

<h1 align="center">Raze Forever / Стереть навсегда</h1>

<p align="center"><i>"Some places should never rise again."</i></p>

<p align="center">
  <a href="https://steamcommunity.com/sharedfiles/filedetails/?id=3820765666">Steam Workshop</a> ·
  <a href="https://www.nexusmods.com/totalwarwarhammer3/mods/413">Nexus Mods</a> ·
  <a href="LICENSE">MIT License</a>
</p>

**Archaon is not the only one who can end the world.** This Total War: WARHAMMER III mod gives every culture a **Raze Forever** option next to the usual Raze. The settlement is wiped off the map, and its ruins can never be occupied or colonised again, by anyone, you included. It is the same permanent block Archaon uses on his Lord of the End Times path, now available to every faction.

| | |
|---|---|
| **Download** | [Steam Workshop](https://steamcommunity.com/sharedfiles/filedetails/?id=3820765666) · [Nexus Mods](https://www.nexusmods.com/totalwarwarhammer3/mods/413) |
| **Game** | Total War: WARHAMMER III, update 9.0 (Lords of the End Times) |
| **Cultures** | all, except Nagash's Undead Legions |
| **Languages** | every game language |
| **Save-game** | safe to add mid-campaign, do not remove mid-campaign |
| **Tests** | 136 automated tests (pack/db encoding, generated options, the campaign script) |

*Русская версия ниже.*

## Features

- **Raze Forever** option after capturing a settlement, for every culture except Nagash's Undead Legions (devastation is already their whole mechanic).
- The ruins get the vanilla "devastated" look and a permanent occupation block — the engine's own `block_region_occupation`, not an "AI won't target it" trick.
- When more than half of a province's settlements are in ruins, the province gets the campaign devastation visuals, but only for cultures that fit:
  - Chaos wasteland: Warriors of Chaos, Khorne, Nurgle, Slaanesh, Tzeentch, Daemons of Chaos, Beastmen, Norsca, Chaos Dwarfs;
  - Skaven blight: Skaven;
  - Nagash's dead land: Vampire Counts, Vampire Coast;
  - everyone else (Empire, Bretonnia, Dwarfs, Kislev, Cathay, elves, Lizardmen, Greenskins, Ogres, Tomb Kings…) leaves the land as it is.
- By default no corruption, no climate change, no faction bonuses. With the optional [Mod Configuration Tool](https://steamcommunity.com/sharedfiles/filedetails/?id=2927955021) erased ruins can spread the destroyer's corruption or cleanse it (see below). The option costs and loots exactly like that culture's normal raze, minus faction-specific raze rewards (skulls, chivalry, souls…) — those stay with the vanilla Raze.
- Human players only: the AI never gets a permanent block from it.
- Works with Archaon's Destroyer path: his own script still devastates the province and counts it toward his bonuses and long victory.
- Works in every game language: the option reads **"Raze: Scorched Earth"**, using the game's own translations.

## Optional: corruption settings (MCT)

Without the [Mod Configuration Tool](https://steamcommunity.com/sharedfiles/filedetails/?id=2927955021) nothing changes: no corruption, exactly as before. With it, the **permraze** settings page lets erased ruins spread the destroyer's corruption or cleanse it.

- **Mode:** Off (default) / per settlement / per province.
- **Strength:** ruin 5 (default), province 30 (the same as Archaon's devastated province), multiplier 100% (0–300%).
- **Province threshold:** more than 50% of the province's settlements by default; only ruins erased with Raze Forever count.
- **By culture:** each culture has a dropdown: nothing / cleanse (Untainted) / spread a corruption type. Defaults: Chaos factions, Daemons, Norsca, Beastmen and Chaos Dwarfs spread Chaos Undivided; Khorne, Nurgle, Slaanesh and Tzeentch spread their own god's corruption; Skaven spread Skaven corruption; Vampire Counts and Vampire Coast spread Vampiric corruption; Empire, Bretonnia, Dwarfs, Kislev, Cathay, High Elves, Wood Elves and Lizardmen cleanse; Dark Elves, Greenskins, Ogres and Tomb Kings do nothing.
- **Fixed exceptions:** Morathi spreads Slaanesh, the Glottkin (Host of the Triplets) spread Nurgle. An option (off by default) makes a Daemon Prince follow the god they ascended to.
- Settings are per campaign and can be changed mid-campaign; all ruins are recalculated when you do. Human players only. Province mode does not stack on provinces the game itself has already devastated (Archaon, endgames).

## Install

Subscribe on the [Steam Workshop](https://steamcommunity.com/sharedfiles/filedetails/?id=3820765666), or download from [Nexus Mods](https://www.nexusmods.com/totalwarwarhammer3/mods/413) and copy **`permanent_raze.pack`** into the game's `data` folder. Enable it in the launcher.

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

`python -m tools.build` writes `dist/permanent_raze.pack` and its Workshop preview image `dist/permanent_raze.png` (drawn by `tools/preview.py`). `--install` also copies both into the game's `data` folder (close the game first). Game path: `tools/paths.py`.

### How it works

- `tools/generate.py` clones each culture's vanilla "raze without occupy" option (one per option group, faction rewards stripped), Archaon's permanent block effect and bundle, and builds the loc entries from `tools/texts.py`.
- `tools/build.py` writes the db tables, loc and the campaign script into PFH5 packs (`tools/packfile.py`, `tools/dbtable.py`, `tools/loc.py`, RPFM schema in `schemas/`).
- `tools/corruption.py` holds the corruption data (culture defaults, effect keys, MCT texts); `src/script/mct/settings/permraze.lua` is the optional MCT settings file; `src/script/campaign/mod/permraze_corruption.lua` reads those settings and applies the corruption of erased ruins.
- `src/script/campaign/mod/permraze.lua` listens for the occupation decision and the raze, then blocks the region, sets the devastated look and, past the province threshold, activates the devastation area. Tested through `lupa` against a mock of the campaign API (`tests/lua/mock_game.lua`).

### Texts

The mod writes no translations of its own: [`tools/texts.py`](tools/texts.py) composes every text from strings the game already ships in all its languages, referenced as `{{tr:key}}` (for example "Raze" + "Scorched Earth"). A test checks that each referenced string exists in every game language.

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
- По умолчанию ни скверны, ни смены климата, ни бонусов. С необязательным [Mod Configuration Tool](https://steamcommunity.com/sharedfiles/filedetails/?id=2927955021) стёртые руины могут распространять скверну разрушителя или очищать землю (см. ниже). Цена и добыча как у обычного разрушения, но без фракционных наград (черепа, честь, души и т.п.): они остаются у обычной кнопки.
- Только для игроков: ИИ вечный запрет не получает.
- Совместим с путём «Разрушителя» у Архаона: провинцию опустошает и засчитывает его собственная механика.
- Работает на любом языке игры: кнопка называется **«Разрушить: Выжженная земля»**, по официальным переводам игры.

### Необязательно: настройки скверны (MCT)

Без [Mod Configuration Tool](https://steamcommunity.com/sharedfiles/filedetails/?id=2927955021) ничего не меняется: скверны нет, как и раньше. С ним на странице настроек **permraze** стёртые руины могут распространять скверну разрушителя или очищать землю.

- **Режим:** выкл. (по умолчанию) / по поселению / по провинции.
- **Сила:** руина 5 (по умолчанию), провинция 30 (как у опустошённой провинции Архаона), множитель 100% (0–300%).
- **Порог провинции:** по умолчанию больше 50% поселений провинции; считаются только руины, стёртые через «Стереть навсегда».
- **По культурам:** у каждой культуры список: ничего / очищать («Незапятнанность») / распространять тип скверны. По умолчанию: Хаос, Демоны, Норска, Зверолюды и Гномы Хаоса распространяют скверну Хаоса неделимого; Кхорн, Нургл, Слаанеш и Тзинч свою; Скавены скавенскую; Графства Вампиров и Вампирское побережье вампирскую; Империя, Бретония, Гномы, Кислев, Катай, Высшие эльфы, Лесные эльфы и Ящеролюды очищают; Тёмные эльфы, Зеленокожие, Огры и Короли гробниц ничего не делают.
- **Исключения:** Морати распространяет Слаанеш, Глоттки («Племя Тройняшек») Нургла. Отдельная настройка (по умолчанию выкл.) заставляет Принца демонов следовать богу, к которому он вознёсся.
- Настройки действуют на кампанию и меняются посреди неё; все руины при этом пересчитываются. Только для игроков. Режим провинции не складывается с провинциями, которые игра уже опустошила сама (Архаон, эндгейм).

### Установка

Подпишитесь в [Мастерской Steam](https://steamcommunity.com/sharedfiles/filedetails/?id=3820765666) или скачайте с [Nexus Mods](https://www.nexusmods.com/totalwarwarhammer3/mods/413) и положите **`permanent_raze.pack`** в папку `data` игры. Включите мод в лаунчере.

Можно добавлять в идущую кампанию. **Не удаляйте мод посреди кампании**: сохранение может не загрузиться, а стёртые руины могут снова стать заселяемыми.

### Известное поведение

- На первом обучающем захвате кампании (задание «Нападите на врага», например старт Ку'гата, скавенов, гномов Хаоса) игра игнорирует любое разрушение, в том числе обычное: поселение остаётся у врага, и выдаётся задание «Захватите и оккупируйте». Дальше всё работает.
- После окончания эндгейм-кризиса игра может убрать выжженную землю в его области, но руины остаются заблокированными.
- У новой кнопки та же картинка, что у «Разрушить», отличаются только подпись и подсказка.
