"""Player-only rebuild: our block is lifted where a human army stands, so the vanilla Colonise button works there."""

from test_corruption_lua import set_mct
from test_permraze_lua import BEASTMEN, EMPIRE, apply_customs, calls, decide, first_tick, g, raze  # noqa: F401

BLOCK = "permraze_block_occupation"
MARKER = "permraze_erased_marker"
LIFT_R1 = [("remove_bundle", BLOCK, "r1")]
RESTORE_R1 = [("apply_effect_bundle_to_region", BLOCK, "r1", 0)]
DWARFS = "wh_main_dwf_dwarfs"

CONTEXTS = """
function make_turn_context(name, human)
    local faction = { name = function() return name end, is_human = function() return human end }
    return { faction = function() return faction end }
end
function make_move_context(human, has_force)
    local faction = { is_human = function() return human end }
    local character = { faction = function() return faction end,
                        has_military_force = function() return has_force end }
    return { character = function() return character end }
end
function make_region_context(region)
    return { region = function() return cm:get_region(region) end }
end
"""


def setup(g):
    """Starts the next turn: ruins erased before it may be rebuilt."""
    if g.MCT_VALUES is None:
        set_mct(g, {"allow_rebuild": True})
    first_tick(g)
    g.lua.execute(CONTEXTS)
    g.TURN = g.TURN + 1
    g.CALLS = g.lua.table()


def reset_calls(g):
    g.CALLS = g.lua.table()


def erase(g, region, faction=EMPIRE):
    decide(g, region, faction=faction)
    raze(g, region, faction=faction)


def army(g, *regions, faction=EMPIRE):
    g.ARMIES[faction] = g.lua.table_from(list(regions))


def turn(g, faction=EMPIRE, human=True):
    g.fire("FactionTurnStart", g.make_turn_context(faction, human))


def move(g, human=True, has_force=True):
    g.fire("CharacterFinishedMovingEvent", g.make_move_context(human, has_force))


def colonise(g, region):
    g.ABANDONED[region] = None
    g.fire("RegionFactionChangeEvent", g.make_region_context(region))


def named(g, *names):
    return [c for c in calls(g) if c[0] in names]


def test_human_turn_lifts_only_where_army_stands(g):
    erase(g, "r1")
    erase(g, "r2")
    setup(g)
    army(g, "r1")
    turn(g)
    assert calls(g) == LIFT_R1
    assert g.permraze.persistent.lifted["r1"] is True
    assert g.permraze.persistent.lifted["r2"] is None


def test_freshly_erased_ruin_stays_blocked_this_turn(g):
    setup(g)
    army(g, "r1")
    erase(g, "r1")
    reset_calls(g)
    move(g)  # the army that erased it still stands in the region
    assert calls(g) == []
    g.TURN = g.TURN + 1
    turn(g)
    assert calls(g) == LIFT_R1


def test_erase_records_turn(g):
    g.TURN = 7
    erase(g, "r1")
    assert g.permraze.persistent.erased["r1"].turn == 7


def test_entry_without_turn_can_be_lifted(g):
    g.permraze.persistent.erased["r1"] = g.lua.table_from({"order": 0})
    g.ABANDONED["r1"] = True
    setup(g)
    army(g, "r1")
    turn(g)
    assert calls(g) == LIFT_R1


def test_army_in_neighbouring_region_lifts(g):
    erase(g, "r1")
    setup(g)
    army(g, "r9")
    turn(g)
    assert calls(g) == LIFT_R1


def test_army_in_non_adjacent_region_lifts_nothing(g):
    erase(g, "r1")
    setup(g)
    army(g, "r2")
    turn(g)
    assert calls(g) == []


def test_marker_stays_while_lifted(g):
    erase(g, "r1")
    setup(g)
    army(g, "r1")
    turn(g)
    assert g.REGION_BUNDLES["r1"][MARKER] is True


def test_first_tick_marks_old_ruins(g):
    g.permraze.persistent.erased["r1"] = g.lua.table_from({"order": 0})
    g.permraze.persistent.erased["r2"] = g.lua.table_from({"order": 0})
    g.REGION_BUNDLES["r2"] = g.lua.table_from({MARKER: True})
    first_tick(g)
    assert [c for c in calls(g) if c[1] == MARKER] == [("apply_effect_bundle_to_region", MARKER, "r1", 0)]


def test_no_army_nothing_lifted(g):
    erase(g, "r1")
    setup(g)
    turn(g)
    assert calls(g) == []


def test_army_at_sea_lifts_nothing(g):
    erase(g, "r1")
    setup(g)
    army(g, False)
    turn(g)
    assert calls(g) == []


def test_army_moving_in_lifts(g):
    erase(g, "r1")
    setup(g)
    turn(g)
    army(g, "r1")
    move(g)
    assert calls(g) == LIFT_R1


def test_army_moving_out_restores(g):
    erase(g, "r1")
    setup(g)
    army(g, "r1")
    turn(g)
    reset_calls(g)
    army(g, "r2")  # same province, not next to r1
    move(g)
    assert calls(g) == RESTORE_R1
    assert g.permraze.persistent.lifted["r1"] is None


def test_army_staying_keeps_lift(g):
    erase(g, "r1")
    setup(g)
    army(g, "r1")
    turn(g)
    reset_calls(g)
    move(g)
    assert calls(g) == []


def test_ai_move_ignored(g):
    erase(g, "r1")
    setup(g)
    army(g, "r1")
    move(g, human=False)
    move(g, has_force=False)
    assert calls(g) == []


def test_other_human_army_lifts(g):
    g.HUMANS = g.lua.table_from([EMPIRE, "wh2_main_skv_clan_mors"])
    erase(g, "r1")
    setup(g)
    army(g, "r1", faction="wh2_main_skv_clan_mors")
    turn(g)
    assert calls(g) == LIFT_R1


def test_ai_turn_restores_block(g):
    erase(g, "r1")
    setup(g)
    army(g, "r1")
    turn(g)
    reset_calls(g)
    turn(g, faction=DWARFS, human=False)
    assert calls(g) == RESTORE_R1
    assert g.permraze.persistent.lifted["r1"] is None


def test_ai_turn_without_lift_does_nothing(g):
    erase(g, "r1")
    setup(g)
    turn(g, faction=DWARFS, human=False)
    assert calls(g) == []


def test_second_human_turn_does_not_lift_twice(g):
    erase(g, "r1")
    setup(g)
    army(g, "r1")
    turn(g)
    turn(g, faction="wh2_main_skv_clan_mors")
    assert calls(g) == LIFT_R1


def test_round_start_restores_block(g):
    erase(g, "r1")
    setup(g)
    army(g, "r1")
    turn(g)
    reset_calls(g)
    g.fire("WorldStartRound", None)
    assert calls(g) == RESTORE_R1


def test_rebuild_off_without_mct(g):
    erase(g, "r1")
    setup(g)
    g.lua.execute("get_mct = nil")
    army(g, "r1")
    turn(g)
    assert calls(g) == []


def test_rebuild_disabled_in_mct(g):
    erase(g, "r1")
    setup(g)
    set_mct(g, {"allow_rebuild": False})
    army(g, "r1")
    turn(g)
    move(g)
    assert calls(g) == []


def test_mct_disabling_rebuild_restores_block(g):
    erase(g, "r1")
    setup(g)
    army(g, "r1")
    turn(g)
    reset_calls(g)
    set_mct(g, {"allow_rebuild": False})
    g.fire("MctFinalized", None)
    assert ("apply_effect_bundle_to_region", BLOCK, "r1", 0) in calls(g)


def test_colonise_rebuilds_settlement(g):
    erase(g, "r1")
    setup(g)
    army(g, "r1")
    turn(g)
    reset_calls(g)
    colonise(g, "r1")
    assert g.permraze.persistent.erased["r1"] is None
    assert g.permraze.persistent.lifted["r1"] is None
    assert calls(g) == [
        ("remove_bundle", BLOCK, "r1"),
        ("remove_bundle", MARKER, "r1"),
        ("cai_enable_targeting_against_settlement", "settlement:r1"),
        ("set_settlement_devastated_state", "r1", "none"),
    ]


def test_rebuilt_region_not_blocked_again(g):
    erase(g, "r1")
    setup(g)
    army(g, "r1")
    turn(g)
    colonise(g, "r1")
    reset_calls(g)
    army(g, "r9")
    move(g)
    turn(g, faction=DWARFS, human=False)
    assert calls(g) == []


def test_raze_change_event_ignored(g):
    setup(g)
    erase(g, "r1")
    reset_calls(g)
    g.fire("RegionFactionChangeEvent", g.make_region_context("r1"))
    assert g.permraze.persistent.erased["r1"] is not None
    assert calls(g) == []


def test_occupied_lifted_region_rebuilt_on_restore(g):
    erase(g, "r1")
    setup(g)
    army(g, "r1")
    turn(g)
    g.ABANDONED["r1"] = None  # owner changed without the event reaching us
    reset_calls(g)
    turn(g, faction=DWARFS, human=False)
    assert g.permraze.persistent.erased["r1"] is None
    assert ("cai_enable_targeting_against_settlement", "settlement:r1") in calls(g)
    assert ("apply_effect_bundle_to_region", BLOCK, "r1", 0) not in calls(g)


def test_rebuild_below_threshold_clears_scorched_land(g):
    for r in ("r1", "r2"):
        erase(g, r, faction=BEASTMEN)
    setup(g)
    army(g, "r2")
    turn(g)
    colonise(g, "r2")
    assert named(g, "deactivate_campaign_map_event_area") == [("deactivate_campaign_map_event_area", "area_p1")]
    assert g.permraze.persistent.devastated_provinces["p1"] is None


def test_rebuild_above_threshold_keeps_scorched_land(g):
    for r in ("r1", "r2", "r3"):
        erase(g, r, faction=BEASTMEN)
    setup(g)
    army(g, "r3")
    turn(g)
    colonise(g, "r3")
    assert named(g, "deactivate_campaign_map_event_area") == []
    assert g.permraze.persistent.devastated_provinces["p1"] is True


def test_rebuild_leaves_foreign_devastation_alone(g):
    g.ACTIVE_AREAS["area_p1"] = True  # an endgame or Archaon scorched it, not us
    for r in ("r1", "r2"):
        erase(g, r)
    setup(g)
    army(g, "r2")
    turn(g)
    colonise(g, "r2")
    assert named(g, "deactivate_campaign_map_event_area") == []


def test_rebuild_then_erase_again_scorches_again(g):
    for r in ("r1", "r2"):
        erase(g, r, faction=BEASTMEN)
    setup(g)
    army(g, "r2")
    turn(g)
    colonise(g, "r2")
    erase(g, "r2", faction=BEASTMEN)
    assert ("activate_campaign_map_event_area", "area_p1", "wh_dlc03_bst_beastmen") in calls(g)


def test_rebuild_removes_ruin_corruption(g):
    set_mct(g, {"mode": "per_settlement", "allow_rebuild": True})
    erase(g, "r1")
    erase(g, "r2")
    setup(g)
    army(g, "r1")
    turn(g)
    colonise(g, "r1")
    assert ("remove_bundle", "permraze_ruin_corruption", "r1") in calls(g)
    assert [c[2] for c in apply_customs(g)] == ["r2"]


def test_lifted_survives_save_load(g):
    erase(g, "r1")
    setup(g)
    army(g, "r1")
    turn(g)
    ctx = g.lua.table()
    g.SAVE_CALLBACKS[1](ctx)
    g.permraze.persistent = None
    g.LOAD_CALLBACKS[1](ctx)
    reset_calls(g)
    turn(g, faction=DWARFS, human=False)
    assert calls(g) == RESTORE_R1
