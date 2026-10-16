import pytest

from tools.generate import BUNDLE_KEY, EFFECT_KEY, cultures_with_look, make_bundle_tables, make_effect_tables, make_loc


@pytest.mark.game
def test_bundle_clone(vanilla_bundles, vanilla_junctions):
    b, j = make_bundle_tables(vanilla_bundles, vanilla_junctions)
    assert BUNDLE_KEY == "permraze_block_occupation"
    assert [r[b.col("key")] for r in b.rows] == ["permraze_block_occupation"]
    assert b.rows[0][b.col("bundle_target")] == "region"
    assert b.rows[0][b.col("localised_title")] == "Erased Forever"
    assert [(r[j.col("effect_bundle_key")], r[j.col("effect_key")], r[j.col("effect_scope")]) for r in j.rows] == \
           [("permraze_block_occupation", "permraze_effect_block_occupation", "region_to_region_own")]


def test_loc_keys_russian():
    loc = dict(make_loc([2100500000], "ru"))
    assert loc["culture_settlement_occupation_options_tooltip_2100500000"].startswith("Стереть навсегда||")
    assert loc["effect_bundles_localised_title_permraze_block_occupation"] == "Стёрто навсегда"
    assert loc["effect_bundles_localised_description_permraze_block_occupation"] == \
           "Эти руины уничтожены окончательно. Здесь больше никто не сможет поселиться."


@pytest.mark.game
def test_cultures_with_look(vanilla_cultures):
    looks = cultures_with_look(vanilla_cultures)
    assert {"wh_main_chs_chaos", "wh_dlc03_bst_beastmen", "wh2_main_skv_skaven",
            "wh_main_vmp_vampire_counts"} <= set(looks)
    assert "wh_main_emp_empire" not in looks and "wh_main_brt_bretonnia" not in looks


@pytest.mark.game
def test_own_effect_with_same_bonus(vanilla_effects, vanilla_effect_bonus):
    assert EFFECT_KEY == "permraze_effect_block_occupation"
    e, bonus = make_effect_tables(vanilla_effects, vanilla_effect_bonus)
    assert [(r[e.col("effect")], r[e.col("icon")]) for r in e.rows] ==            [("permraze_effect_block_occupation", "blocked_ruins.png")]
    assert [(r[bonus.col("effect")], r[bonus.col("bonus_value_id")]) for r in bonus.rows] ==            [("permraze_effect_block_occupation", "block_region_occupation")]


def test_loc_defaults_to_english():
    loc = dict(make_loc([2100500000]))
    assert loc["culture_settlement_occupation_options_tooltip_2100500000"].startswith("Raze Forever||")
    assert loc["effects_description_permraze_effect_block_occupation"] ==            "Ruins erased forever: this region cannot be occupied or colonised"
