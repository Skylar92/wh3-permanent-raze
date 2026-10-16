import re

import pytest

from tools.texts import FIELDS, LANGUAGES, TEXTS, VANILLA_TEXTS


def test_all_game_languages_present():
    assert LANGUAGES == ("en", "ru", "ge", "fr", "it", "sp", "pl", "cz", "tr", "br", "kr", "cn", "zh")
    assert set(TEXTS) == set(LANGUAGES)


def test_every_language_has_every_text():
    for lang in LANGUAGES:
        assert set(TEXTS[lang]) == set(FIELDS), lang
        for field, text in TEXTS[lang].items():
            assert text.strip() and "||" not in text, (lang, field)


def test_english_and_russian_wording():
    assert TEXTS["en"]["title"] == "Raze Forever"
    assert TEXTS["ru"]["title"] == "Стереть навсегда"
    assert TEXTS["ru"]["bundle_title"] == "Стёрто навсегда"


def test_vanilla_texts_are_composites():
    assert set(VANILLA_TEXTS) == set(FIELDS)
    assert VANILLA_TEXTS["title"] == ("{{tr:effect_bundles_localised_title_wh_dlc03_bundle_horde_raze}}: "
                                      "{{tr:effect_bundles_localised_title_wh2_dlc11_noctilus_war_raiding}}")
    assert VANILLA_TEXTS["bundle_title"] == "{{tr:effect_bundles_localised_title_wh3_dlc26_block_occupation_beastmen}}"


@pytest.mark.game
def test_vanilla_keys_exist_in_every_language():
    from tools.loc import decode_loc
    from tools.packfile import read_pack
    from tools.paths import GAME_DATA
    keys = {k for text in VANILLA_TEXTS.values() for k in re.findall(r"\{\{tr:([^}]+)\}\}", text)}
    assert keys
    for lang in LANGUAGES:
        loc = {}
        for name, data in read_pack(GAME_DATA / f"local_{lang}.pack").items():
            if name.endswith(".loc"):
                loc.update(decode_loc(data))
        for key in keys:
            assert loc.get(key, "").strip(), (lang, key)
