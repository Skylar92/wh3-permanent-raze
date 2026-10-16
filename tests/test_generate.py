from types import SimpleNamespace

import pytest

from tools.generate import make_option_clones

pytestmark = pytest.mark.game


@pytest.fixture(scope="module")
def clones(vanilla_options, vanilla_criteria):
    options, criteria, ids = make_option_clones(vanilla_options, vanilla_criteria)
    return SimpleNamespace(options=options, criteria=criteria, ids=ids)


def test_clone_count(clones):
    # one clone per raze group: 51 vanilla raze rows in 49 groups (Khorne and Beastmen have two each),
    # minus Nagash's Undead Legions, who devastate everything anyway
    assert len(clones.ids) == 48
    assert clones.ids == list(range(2100500000, 2100500048))
    assert [r[clones.options.col("id")] for r in clones.options.rows] == clones.ids


def test_khorne_gets_single_clone(clones):
    t = clones.options
    kho = [r for r in t.rows
           if r[t.col("group")] == "wh3_main_sc_kho_khorne_occupation_decision_raze_without_occupy"]
    assert len(kho) == 1
    assert kho[0][t.col("captive_option_outcome")] == "none"  # the "Skulls" row, id 2135151227


def test_clone_strips_rewards(clones):
    t = clones.options
    for r in t.rows:
        for c in ("resource_transaction", "required_resources", "target_settlement_faction_effect_bundle",
                  "acting_army_faction_effect_bundle", "acting_army_effect_bundle",
                  "capturing_force_resource_transaction", "captured_region_resource_transaction",
                  "override_settlement_type"):
            assert r[t.col(c)] is None, c
        for c in ("target_settlement_faction_effect_bundle_turns", "acting_army_faction_effect_bundle_turns",
                  "acting_army_effect_bundle_turns"):
            assert r[t.col(c)] == 0, c
        assert r[t.col("settlement_option")] == "occupation_decision_raze_without_occupy"
        assert r[t.col("tooltip")].startswith("Raze Forever||")


def test_clone_keeps_loot_and_captives(clones, vanilla_options):
    t, v = clones.options, vanilla_options
    src = next(r for r in v.rows if r[v.col("id")] == 664)  # Empire raze
    clone = next(r for r in t.rows if r[t.col("group")] == src[v.col("group")])
    for c in ("captive_option_outcome", "base_loot", "building_loot_mod", "icon",
              "disable_gaining_action_points_for_a_turn"):
        assert clone[t.col(c)] == src[v.col(c)], c


def test_one_clone_per_group(clones):
    groups = [r[clones.options.col("group")] for r in clones.options.rows]
    assert len(groups) == len(set(groups))


def test_beastmen_criteria_copied(clones):
    t = clones.criteria
    members = sorted(r[t.col("member")] for r in t.rows)
    assert members == ["wh2_dlc17_raze_option_beastmen_2"]  # source row 411, lowest id in the group
    assert {r[t.col("culture_settlement_occupation_option")] for r in t.rows} <= set(clones.ids)


def test_ids_do_not_collide(clones, vanilla_options):
    vanilla = {r[vanilla_options.col("id")] for r in vanilla_options.rows}
    assert not vanilla & set(clones.ids) and max(clones.ids) < 2**31


def test_undead_legions_excluded(clones):
    groups = [r[clones.options.col("group")] for r in clones.options.rows]
    assert "wh3_dlc29_sc_nag_undead_legions_occupation_decision_raze_without_occupy" not in groups
