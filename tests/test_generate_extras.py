import pytest

from tools.generate import BUNDLE_KEY, cultures_with_look, make_bundle_tables, make_loc


@pytest.mark.game
def test_bundle_clone(vanilla_bundles, vanilla_junctions):
    b, j = make_bundle_tables(vanilla_bundles, vanilla_junctions)
    assert BUNDLE_KEY == "permraze_block_occupation"
    assert [r[b.col("key")] for r in b.rows] == ["permraze_block_occupation"]
    assert b.rows[0][b.col("bundle_target")] == "region"
    assert b.rows[0][b.col("localised_title")] == "Стёрто навсегда"
    assert [(r[j.col("effect_bundle_key")], r[j.col("effect_key")], r[j.col("effect_scope")]) for r in j.rows] == \
           [("permraze_block_occupation", "wh3_dlc29_effect_chs_archaon_block_occupation", "region_to_region_own")]


def test_loc_keys():
    loc = dict(make_loc([2100500000]))
    assert loc["culture_settlement_occupation_options_tooltip_2100500000"].startswith("Стереть навсегда||")
    assert loc["effect_bundles_localised_title_permraze_block_occupation"] == "Стёрто навсегда"
    assert loc["effect_bundles_localised_description_permraze_block_occupation"] == \
           "Эти руины уничтожены окончательно. Здесь больше никто не сможет поселиться."


@pytest.mark.game
def test_cultures_with_look(vanilla_cultures):
    looks = cultures_with_look(vanilla_cultures)
    assert "wh_main_chs_chaos" in looks and "wh2_main_skv_skaven" in looks
    assert "wh_main_emp_empire" not in looks
