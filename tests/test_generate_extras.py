import pytest

from tools.generate import (BUNDLE_KEY, EFFECT_KEY, PROVINCE_BUNDLE_KEY, RUIN_BUNDLE_KEY, devastation_looks,
                            make_bundle_tables, make_corruption_bundles, make_effect_tables, make_loc)
from tools.texts import VANILLA_TEXTS


@pytest.mark.game
def test_bundle_clone(vanilla_bundles, vanilla_junctions):
    b, j = make_bundle_tables(vanilla_bundles, vanilla_junctions)
    assert BUNDLE_KEY == "permraze_block_occupation"
    assert [r[b.col("key")] for r in b.rows][0] == "permraze_block_occupation"
    assert b.rows[0][b.col("bundle_target")] == "region"
    assert b.rows[0][b.col("localised_title")] == "{{tr:effect_bundles_localised_title_wh3_dlc26_block_occupation_beastmen}}"
    assert [(r[j.col("effect_bundle_key")], r[j.col("effect_key")], r[j.col("effect_scope")]) for r in j.rows] == \
           [("permraze_block_occupation", "permraze_effect_block_occupation", "region_to_region_own")]


@pytest.mark.game
def test_devastation_looks(vanilla_cultures):
    looks = devastation_looks(vanilla_cultures)
    assert looks["wh_main_chs_chaos"] == "wh_main_chs_chaos"
    assert looks["wh_dlc03_bst_beastmen"] == "wh_dlc03_bst_beastmen"
    assert looks["wh2_main_skv_skaven"] == "wh2_main_skv_skaven"
    assert looks["wh_main_vmp_vampire_counts"] == "wh_main_vmp_vampire_counts"
    # borrowed looks, author's call: Chaos Dwarfs scorch like Chaos, Vampire Coast like Nagash
    assert looks["wh3_dlc23_chd_chaos_dwarfs"] == "wh_main_chs_chaos"
    assert looks["wh2_dlc11_cst_vampire_coast"] == "wh_main_vmp_vampire_counts"
    assert "wh_main_emp_empire" not in looks and "wh_main_brt_bretonnia" not in looks


@pytest.mark.game
def test_own_effect_with_same_bonus(vanilla_effects, vanilla_effect_bonus):
    assert EFFECT_KEY == "permraze_effect_block_occupation"
    e, bonus = make_effect_tables(vanilla_effects, vanilla_effect_bonus)
    assert [(r[e.col("effect")], r[e.col("icon")]) for r in e.rows] ==            [("permraze_effect_block_occupation", "blocked_ruins.png")]
    assert [(r[bonus.col("effect")], r[bonus.col("bonus_value_id")]) for r in bonus.rows] ==            [("permraze_effect_block_occupation", "block_region_occupation")]


def test_loc_defaults_to_vanilla_composites():
    loc = dict(make_loc([2100500000]))
    assert loc["culture_settlement_occupation_options_tooltip_2100500000"] == (
        "{{tr:effect_bundles_localised_title_wh_dlc03_bundle_horde_raze}}: "
        "{{tr:effect_bundles_localised_title_wh2_dlc11_noctilus_war_raiding}}"
        "||{{tr:effect_bundles_localised_title_wh3_dlc26_block_occupation_beastmen}}")
    assert loc["effects_description_permraze_effect_block_occupation"] ==            "{{tr:effects_description_wh3_main_effect_endgame_block_occupation}}"



@pytest.mark.game
def test_corruption_bundles_cloned(vanilla_bundles):
    rows = make_corruption_bundles(vanilla_bundles)
    b = vanilla_bundles
    source = next(r for r in b.rows if r[b.col("key")] == "wh3_main_bundle_corruption_chaos_high_reduction")
    assert [r[b.col("key")] for r in rows] == [RUIN_BUNDLE_KEY, PROVINCE_BUNDLE_KEY]
    assert RUIN_BUNDLE_KEY == "permraze_ruin_corruption"
    assert PROVINCE_BUNDLE_KEY == "permraze_province_corruption"
    for r in rows:
        assert r[b.col("localised_title")] == VANILLA_TEXTS["title"]
        assert r[b.col("localised_description")] == ""
        for name, _ in b.fields:
            if name not in ("key", "localised_title", "localised_description"):
                assert r[b.col(name)] == source[b.col(name)]


def test_loc_has_corruption_bundle_titles():
    loc = dict(make_loc([2100500000]))
    for key in (RUIN_BUNDLE_KEY, PROVINCE_BUNDLE_KEY):
        assert loc["effect_bundles_localised_title_" + key] == VANILLA_TEXTS["title"]
