"""AI erase (MCT option, off by default): an AI raze erases the ruins forever by a set chance."""

import pytest

from test_corruption_lua import set_mct
from test_permraze_lua import (BEASTMEN, CONTEXTS, EMPIRE, ERASE_R1, OUR_ID, activations, apply_customs, calls, decide,
                               first_tick, g, raze)  # noqa: F401
from test_rebuild_lua import CONTEXTS as REBUILD_CONTEXTS, RESEAL_R1, army, colonise, move, turn

TOMB_KINGS = "wh2_dlc09_tmb_exiles_of_nehek"
ON = {"ai_erase": True, "ai_erase_chance": 25}


def setup(g, values=ON, roll=1):
    if values is not None:
        set_mct(g, values)
    first_tick(g)
    g.lua.execute(CONTEXTS)
    g.lua.execute(REBUILD_CONTEXTS)
    g.ROLL = roll
    g.CALLS = g.lua.table()


def ai_raze(g, region, faction=BEASTMEN, option=596):
    g.fire("CharacterPerformsSettlementOccupationDecision", g.make_context(option, False, region, faction))
    g.ABANDONED[region] = True
    g.fire("CharacterRazedSettlement", g.make_context(option, False, region, faction))


def logged(g):
    return [s.split(": ", 2)[2] for s in g.OUT.values()]


def test_off_by_default_without_mct(g):
    setup(g, values=None)
    ai_raze(g, "r1")
    assert calls(g) == []
    assert g.ROLL_MAX is None


def test_off_in_mct(g):
    setup(g, values={"ai_erase": False, "ai_erase_chance": 100})
    ai_raze(g, "r1")
    assert calls(g) == []
    assert g.ROLL_MAX is None


def test_broken_mct_keeps_it_off(g):
    set_mct(g, ON, broken=True)
    setup(g, values=None)
    ai_raze(g, "r1")
    assert calls(g) == []


def test_roll_within_chance_erases(g):
    setup(g, roll=25)
    ai_raze(g, "r1")
    assert calls(g) == ERASE_R1
    assert g.ROLL_MAX == 100
    entry = g.permraze.persistent.erased["r1"]
    assert (entry.faction, entry.order) == (BEASTMEN, 1)


def test_roll_over_chance_keeps_vanilla_raze(g):
    setup(g, roll=26)
    ai_raze(g, "r1")
    assert calls(g) == []
    assert g.permraze.persistent.erased["r1"] is None


@pytest.mark.parametrize("chance", [0, -5])
def test_bad_chance_never_rolls(g, chance):
    setup(g, values={"ai_erase": True, "ai_erase_chance": chance})
    ai_raze(g, "r1")
    assert calls(g) == []
    assert g.ROLL_MAX is None


def test_full_chance_always_erases(g):
    setup(g, values={"ai_erase": True, "ai_erase_chance": 100}, roll=100)
    ai_raze(g, "r1")
    assert calls(g) == ERASE_R1


def test_ai_picking_our_option_counts_as_any_raze(g):
    setup(g, roll=26)
    ai_raze(g, "r1", option=int(OUR_ID))
    assert calls(g) == []


def test_rolls_are_logged(g):
    setup(g, roll=26)
    g.OUT = g.lua.table()
    ai_raze(g, "r1")
    g.ROLL = 3
    ai_raze(g, "r2")
    assert "AI raze of r1 by wh_dlc03_bst_beastmen kept: rolled 26, chance 25" in logged(g)
    assert "AI raze of r2 by wh_dlc03_bst_beastmen erased: rolled 3, chance 25" in logged(g)


def test_already_erased_ruins_not_erased_twice(g):
    setup(g)
    ai_raze(g, "r1")
    g.CALLS = g.lua.table()
    ai_raze(g, "r1", faction=TOMB_KINGS)
    assert calls(g) == []
    assert g.permraze.persistent.erased["r1"].faction == BEASTMEN


def test_ai_erase_scorches_with_its_own_culture(g):
    setup(g)
    ai_raze(g, "r1")
    ai_raze(g, "r2")
    assert activations(g) == [("activate_campaign_map_event_area", "area_p1", "wh_dlc03_bst_beastmen")]


def test_human_path_untouched_when_on(g):
    setup(g)
    g.fire("CharacterPerformsSettlementOccupationDecision", g.make_context(596, True, "r1", EMPIRE))
    g.ABANDONED["r1"] = True
    g.fire("CharacterRazedSettlement", g.make_context(596, True, "r1", EMPIRE))
    assert calls(g) == []
    assert g.ROLL_MAX is None


def test_human_erase_still_works_when_on(g):
    setup(g, roll=100)
    g.fire("CharacterPerformsSettlementOccupationDecision", g.make_context(int(OUR_ID), True, "r1", EMPIRE))
    g.ABANDONED["r1"] = True
    g.fire("CharacterRazedSettlement", g.make_context(int(OUR_ID), True, "r1", EMPIRE))
    assert calls(g) == ERASE_R1
    assert g.ROLL_MAX is None
    assert g.permraze.persistent.erased["r1"].faction == EMPIRE


def test_corruption_waits_for_round_start(g):
    setup(g, values=dict(ON, mode="per_settlement"))
    ai_raze(g, "r1")
    ai_raze(g, "r2")
    assert apply_customs(g) == []
    g.fire("WorldStartRound", g.lua.table())
    assert [c[2] for c in apply_customs(g)] == ["r1", "r2"]
    g.CALLS = g.lua.table()
    g.fire("WorldStartRound", g.lua.table())
    assert apply_customs(g) == []  # nothing new, no second rebuild


def test_corruption_refreshed_on_human_turn(g):
    setup(g, values=dict(ON, mode="per_settlement"))
    ai_raze(g, "r1")
    turn(g, faction=EMPIRE, human=True)
    assert [c[2] for c in apply_customs(g)] == ["r1"]


def test_corruption_not_refreshed_on_ai_turn(g):
    setup(g, values=dict(ON, mode="per_settlement"))
    ai_raze(g, "r1")
    turn(g, faction=TOMB_KINGS, human=False)
    assert apply_customs(g) == []


def test_player_rebuilds_ai_ruins_when_allowed(g):
    setup(g, values=dict(ON, allow_rebuild=True))
    ai_raze(g, "r1")
    g.TURN = g.TURN + 1
    army(g, "r1")
    move(g)
    colonise(g, "r1")
    assert g.permraze.persistent.erased["r1"] is None
    assert ("set_settlement_devastated_state", "r1", "none") in calls(g)


def test_ai_ruins_taken_by_script_are_sealed_again(g):
    setup(g)
    ai_raze(g, "r1")
    g.CALLS = g.lua.table()
    colonise(g, "r1", owner=TOMB_KINGS)
    assert calls(g) == RESEAL_R1


def test_ai_erase_survives_save_and_load(g):
    setup(g)
    ai_raze(g, "r1")
    ctx = g.lua.table()
    g.SAVE_CALLBACKS[1](ctx)
    g.permraze.persistent = None
    g.LOAD_CALLBACKS[1](ctx)
    assert g.permraze.persistent.erased["r1"].faction == BEASTMEN


def test_nagash_legions_skipped(g):
    setup(g, values={"ai_erase": True, "ai_erase_chance": 100})
    ai_raze(g, "r1", faction="nagash_legions")
    assert calls(g) == []
    assert g.ROLL_MAX is None


def test_unknown_faction_still_rolls(g):
    setup(g)
    ai_raze(g, "r1", faction="no_such_faction")
    assert calls(g)[:len(ERASE_R1)] == ERASE_R1
