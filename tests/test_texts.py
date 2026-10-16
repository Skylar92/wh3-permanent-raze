import re

import pytest

from tools.texts import FIELDS, GAME_LANGUAGES, VANILLA_TEXTS


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
    for lang in GAME_LANGUAGES:
        loc = {}
        for name, data in read_pack(GAME_DATA / f"local_{lang}.pack").items():
            if name.endswith(".loc"):
                loc.update(decode_loc(data))
        for key in keys:
            assert loc.get(key, "").strip(), (lang, key)
