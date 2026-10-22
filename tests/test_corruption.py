import pytest

from tools.corruption import (
    CORRUPTION_TYPES, CULTURE_DEFAULTS, DAEMON_PRINCE_FACTION, DAEMONS_CULTURE, EFFECT_SCOPE,
    EFFECT_VALUES, FACTION_OVERRIDES, MCT_TEXTS, RU_PROBE, SETTINGS_DEFAULTS, SLIDERS, effect_key,
)
from tools.texts import GAME_LANGUAGES

# Cultures that get (or would get) a raze clone but are never played by a human.
NON_PLAYER_CULTURES = {"wh3_dlc29_nag_undead_legions", "wh2_main_rogue"}
UNTAINTED_KEY = "uied_component_texts_localised_string_region_corruption_untainted_Tooltip_40058"


def test_culture_defaults_values_valid():
    assert CULTURE_DEFAULTS
    assert set(CULTURE_DEFAULTS.values()) <= set(EFFECT_VALUES)
    assert DAEMONS_CULTURE in CULTURE_DEFAULTS


def test_overrides_valid():
    assert set(FACTION_OVERRIDES.values()) <= set(EFFECT_VALUES)
    assert FACTION_OVERRIDES == {"wh2_main_def_cult_of_pleasure": "slaanesh",
                                 "wh3_dlc29_chs_host_of_the_triplets": "nurgle"}


def test_sliders_cover_numeric_defaults():
    assert set(SLIDERS) == {"ruin_strength", "province_strength", "multiplier", "threshold"}
    for key, (lo, hi, step) in SLIDERS.items():
        assert lo <= SETTINGS_DEFAULTS[key] <= hi and step > 0
    assert SETTINGS_DEFAULTS["mode"] == "off"
    assert SETTINGS_DEFAULTS["daemon_follow_god"] is False
    assert len(SETTINGS_DEFAULTS) == 6


def test_mct_texts_have_both_languages():
    assert MCT_TEXTS
    for key, (en, ru) in MCT_TEXTS.items():
        assert en.strip() and ru.strip(), key
    for key in ("mode_off", "mode_per_settlement", "mode_per_province", "value_none"):
        assert key in MCT_TEXTS or any(k.endswith(key) for k in MCT_TEXTS)


def test_effect_key():
    assert effect_key("nurgle") == "wh3_main_effect_corruption_nurgle_events_bad"
    assert effect_key("reduce") == "wh3_main_effect_corruption_reduction_events"
    with pytest.raises(ValueError):
        effect_key("none")
    assert EFFECT_SCOPE == "region_to_province_own_unseen"


def _loc(lang):
    from tools.loc import decode_loc
    from tools.packfile import read_pack
    from tools.paths import GAME_DATA
    loc = {}
    for name, data in read_pack(GAME_DATA / f"local_{lang}.pack").items():
        if name.endswith(".loc"):
            loc.update(decode_loc(data))
    return loc


@pytest.mark.game
def test_cultures_cover_every_raze_culture(schema, vanilla_db, vanilla_options, vanilla_criteria):
    from tests.conftest import vanilla_table
    from tools.generate import select_sources
    members = vanilla_table(schema, vanilla_db, "campaign_group_members_tables")
    subs = vanilla_table(schema, vanilla_db, "campaign_group_member_criteria_subcultures_tables")
    cultures = vanilla_table(schema, vanilla_db, "cultures_subcultures_tables")
    groups = {r[vanilla_options.col("group")] for r in select_sources(vanilla_options)}
    member_ids = {r[members.col("id")] for r in members.rows if r[members.col("group")] in groups}
    subcultures = {r[subs.col("subculture")] for r in subs.rows if r[subs.col("member")] in member_ids}
    found = {r[cultures.col("culture")] for r in cultures.rows if r[cultures.col("subculture")] in subcultures}
    assert found - NON_PLAYER_CULTURES == set(CULTURE_DEFAULTS)


@pytest.mark.game
def test_override_factions_exist(vanilla_factions):
    keys = {r[vanilla_factions.col("key")] for r in vanilla_factions.rows}
    assert set(FACTION_OVERRIDES) <= keys
    assert DAEMON_PRINCE_FACTION in keys


@pytest.mark.game
def test_effect_keys_exist(vanilla_effects):
    keys = {r[vanilla_effects.col("effect")] for r in vanilla_effects.rows}
    for v in EFFECT_VALUES:
        if v != "none":
            assert effect_key(v) in keys, v


@pytest.mark.game
def test_loc_keys_exist_in_every_language():
    keys = [f"cultures_name_{c}" for c in CULTURE_DEFAULTS]
    keys += [f"pooled_resources_display_name_wh3_main_corruption_{t}" for t in CORRUPTION_TYPES]
    keys.append(UNTAINTED_KEY)
    for lang in GAME_LANGUAGES:
        loc = _loc(lang)
        for key in keys:
            assert loc.get(key, "").strip(), (lang, key)


@pytest.mark.game
def test_ru_probe_matches_russian():
    key, ru = RU_PROBE
    assert _loc("ru").get(key) == ru
    assert _loc("en").get(key) != ru
