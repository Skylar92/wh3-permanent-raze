"""Archaon's Chaos Invasion (End Times): its razes can be erased forever, and while it runs the
vanilla invasion script paints provinces instead of us."""

from test_ai_erase_lua import ai_raze, logged, setup
from test_permraze_lua import BEASTMEN, ERASE_R1, EMPIRE, activations, calls, g  # noqa: F401
from test_rebuild_lua import turn

INVASION = "wh3_dlc29_chaos_invasion_confederation_owner"
INVASION_ICON = "wh3_dlc29_episodes_chaos_invasion_devastated_region"

# Same shape as the vanilla episode_chaos_invasion this mod reads. The mod reads its saved data
# and must not call into it: calls at round start crashed the game when the episode began.
EPISODE = """
episode_chaos_invasion = {
    persistent = { invasion_spawned = %s, current_stage_index = 3 },
    stages = {
        { stage_key = "episode_chaos_invasion_stage_foreshadow_1" },
        { stage_key = "episode_chaos_invasion_stage_foreshadow_2" },
        { stage_key = "episode_chaos_invasion_stage_main" },
        { stage_key = "episode_chaos_invasion_stage_battle" },
        { stage_key = "episode_chaos_invasion_stage_final" },
    },
}
function episode_chaos_invasion:is_main_invasion_active()
    CALLS[#CALLS + 1] = {"is_main_invasion_active"}
    return false
end
function episode_chaos_invasion:update_razed_region(region_key)
    CALLS[#CALLS + 1] = {"update_razed_region", region_key}
end
"""


def episode(g, spawned=True, stage_main=True):
    g.lua.execute(EPISODE % ("true" if spawned else "false"))
    g.episode_chaos_invasion.persistent.current_stage_index = 3 if stage_main else 5


def vanilla_raze(g, region):
    """A region the invasion script razed: abandoned, with the vanilla icon, no raze event."""
    g.ABANDONED[region] = True
    g.lua.execute('REGION_BUNDLES["%s"] = REGION_BUNDLES["%s"] or {}' % (region, region))
    g.REGION_BUNDLES[region][INVASION_ICON] = True


def erased(g):
    return sorted(k for k, _ in g.permraze.persistent.erased.items())


def updates(g):
    return [c[1] for c in calls(g) if c[0] == "update_razed_region"]


# Province painting during the invasion

def test_erase_during_invasion_left_to_vanilla_script(g):
    setup(g, values={"ai_erase": True, "ai_erase_chance": 100}, roll=1)
    episode(g)
    ai_raze(g, "r1")
    ai_raze(g, "r2")
    assert activations(g) == []
    assert updates(g) == []  # waits for the region to settle
    g.run_callbacks()
    assert updates(g) == ["r1", "r2"]


def test_no_invasion_paints_as_before(g):
    setup(g, values={"ai_erase": True, "ai_erase_chance": 100}, roll=1)
    ai_raze(g, "r1")
    ai_raze(g, "r2")
    g.run_callbacks()
    assert activations(g) == [("activate_campaign_map_event_area", "area_p1", BEASTMEN)]
    assert updates(g) == []


def test_invasion_not_spawned_yet_paints_as_before(g):
    setup(g, values={"ai_erase": True, "ai_erase_chance": 100}, roll=1)
    episode(g, spawned=False)
    ai_raze(g, "r1")
    ai_raze(g, "r2")
    g.run_callbacks()
    assert len(activations(g)) == 1
    assert updates(g) == []


def test_invasion_over_paints_as_before(g):
    setup(g, values={"ai_erase": True, "ai_erase_chance": 100}, roll=1)
    episode(g, stage_main=False)
    ai_raze(g, "r1")
    ai_raze(g, "r2")
    assert len(activations(g)) == 1


def test_broken_episode_paints_as_before(g):
    setup(g, values={"ai_erase": True, "ai_erase_chance": 100}, roll=1)
    episode(g)
    g.episode_chaos_invasion.stages = None
    ai_raze(g, "r1")
    ai_raze(g, "r2")
    assert len(activations(g)) == 1


def test_player_erase_during_invasion_left_to_vanilla_script(g):
    setup(g, values=None)
    episode(g)
    g.fire("CharacterPerformsSettlementOccupationDecision", g.make_context(2100500000, True, "r1", EMPIRE))
    g.ABANDONED["r1"] = True
    g.fire("CharacterRazedSettlement", g.make_context(2100500000, True, "r1", EMPIRE))
    assert calls(g) == ERASE_R1
    g.run_callbacks()
    assert updates(g) == ["r1"]


def test_vanilla_script_skipped_when_region_taken_meanwhile(g):
    setup(g, values={"ai_erase": True, "ai_erase_chance": 100}, roll=1)
    episode(g)
    ai_raze(g, "r1")
    g.ABANDONED["r1"] = None
    g.OUT = g.lua.table()
    g.run_callbacks()
    assert updates(g) == []
    assert any("r1 no longer in ruins" in line for line in logged(g))


def test_vanilla_script_failure_is_logged(g):
    setup(g, values={"ai_erase": True, "ai_erase_chance": 100}, roll=1)
    episode(g)
    ai_raze(g, "r1")
    g.lua.execute('function episode_chaos_invasion:update_razed_region() error("boom") end')
    g.OUT = g.lua.table()
    g.run_callbacks()
    assert any("Chaos Invasion update of r1 failed" in line for line in logged(g))


# Invasion razes erased forever (MCT option invasion_erase)

def test_invasion_raze_erased_without_roll(g):
    setup(g, values={"invasion_erase": True}, roll=100)
    episode(g)
    ai_raze(g, "r1", faction=INVASION)
    assert calls(g)[:len(ERASE_R1)] == ERASE_R1
    assert g.permraze.persistent.erased["r1"].faction == INVASION
    assert g.ROLL_MAX is None


def test_invasion_raze_kept_when_option_off(g):
    setup(g, values={"invasion_erase": False}, roll=1)
    episode(g)
    ai_raze(g, "r1", faction=INVASION)
    assert calls(g) == []


def test_invasion_raze_off_by_default_without_mct(g):
    setup(g, values=None)
    episode(g)
    ai_raze(g, "r1", faction=INVASION)
    assert calls(g) == []


def test_invasion_option_off_falls_back_to_ai_chance(g):
    setup(g, values={"invasion_erase": False, "ai_erase": True, "ai_erase_chance": 100}, roll=100)
    episode(g)
    ai_raze(g, "r1", faction=INVASION)
    assert g.ROLL_MAX == 100
    assert g.permraze.persistent.erased["r1"].faction == INVASION


def test_invasion_option_does_not_touch_other_ai(g):
    setup(g, values={"invasion_erase": True}, roll=1)
    episode(g)
    ai_raze(g, "r1", faction=BEASTMEN)
    assert calls(g) == []


# Ruins the invasion script razes when it begins: caught as they fall to ruin

FALL = """
function make_fall_context(region, reason)
    return { region = function() return cm:get_region(region) end,
             reason = function() return reason end,
             previous_faction = function() return cm:get_faction("wh_main_chs_chaos") end }
end
"""


def fall(g, region, reason="abandoned"):
    """The region falls to ruin with no raze event, as the invasion script razes it."""
    g.lua.execute(FALL)
    g.ABANDONED[region] = True
    g.fire("RegionFactionChangeEvent", g.make_fall_context(region, reason))


def beginning(g, values=None):
    """The main stage has begun, the invasion has not spawned yet."""
    setup(g, values={"invasion_erase": True} if values is None else values)
    episode(g, spawned=False)


def test_ruins_falling_as_the_invasion_begins_are_erased(g):
    beginning(g)
    fall(g, "r1")
    assert calls(g) == ERASE_R1
    assert g.permraze.persistent.erased["r1"].faction == INVASION


def test_start_ruins_left_to_the_invasion_script_to_paint(g):
    beginning(g)
    for region in ("r1", "r2", "r3"):
        fall(g, region)
    g.run_callbacks()
    assert activations(g) == []
    assert updates(g) == []


def test_ruins_falling_after_the_invasion_spawned_wait_for_their_raze_event(g):
    setup(g, values={"invasion_erase": True})
    episode(g)
    fall(g, "r1")
    assert erased(g) == []


def test_ruins_falling_during_the_warnings_are_not_erased(g):
    beginning(g)
    g.episode_chaos_invasion.persistent.current_stage_index = 2
    fall(g, "r1")
    assert erased(g) == []


def test_start_ruins_untouched_when_option_off(g):
    beginning(g, values={"invasion_erase": False})
    fall(g, "r1")
    assert erased(g) == []


def test_start_ruins_off_by_default_without_mct(g):
    setup(g, values=None)
    episode(g, spawned=False)
    fall(g, "r1")
    assert erased(g) == []


def test_ruins_falling_without_episode_are_not_erased(g):
    setup(g, values={"invasion_erase": True})
    fall(g, "r1")
    assert erased(g) == []


def test_other_owner_changes_are_ignored(g):
    beginning(g)
    fall(g, "r1", reason="unopposed capture")
    assert erased(g) == []


def test_start_ruins_already_erased_keep_their_eraser(g):
    beginning(g, values={"invasion_erase": True, "ai_erase": True, "ai_erase_chance": 100})
    g.ROLL = 1
    ai_raze(g, "r1")
    fall(g, "r1")
    assert g.permraze.persistent.erased["r1"].faction == BEASTMEN


def test_start_ruins_survive_save_and_load(g):
    beginning(g)
    fall(g, "r1")
    ctx = g.lua.table()
    g.SAVE_CALLBACKS[1](ctx)
    g.permraze.persistent = None
    g.LOAD_CALLBACKS[1](ctx)
    assert g.permraze.persistent.erased["r1"].faction == INVASION


def test_start_ruins_taken_later_are_sealed_again(g):
    beginning(g)
    fall(g, "r1")
    g.CALLS = g.lua.table()
    from test_rebuild_lua import colonise
    colonise(g, "r1", owner=BEASTMEN)
    assert ("set_region_abandoned", "r1") in calls(g)


# Debug build (build.py --log): fog of war lifted and the extra log lines

import pytest
from lupa.lua51 import LuaRuntime

from test_corruption_lua import load_corruption
from test_permraze_lua import CONTEXTS, LOOK_CULTURES, MOCK, OUR_ID, TEMPLATE
from test_rebuild_lua import CONTEXTS as REBUILD_CONTEXTS
from tools.render import render_script

DEBUG_CONTEXTS = """
function make_change_context(region, reason, previous)
    return { region = function() return cm:get_region(region) end,
             reason = function() return reason end,
             previous_faction = function() return cm:get_faction(previous) end }
end
"""


@pytest.fixture
def gd():
    lua = LuaRuntime(unpack_returned_tuples=True)
    lua.execute(MOCK)
    lua.execute("io.open = function() return nil end")  # no permraze_log.txt from tests
    lua.execute(render_script(TEMPLATE, [int(OUR_ID)], LOOK_CULTURES, file_log=True))
    g = lua.globals()
    g.lua = lua
    load_corruption(g)
    return g


def debug_setup(g, values):
    from test_corruption_lua import set_mct
    set_mct(g, values)
    for f in g.FIRST_TICK.values():
        f()
    g.lua.execute(CONTEXTS)
    g.lua.execute(REBUILD_CONTEXTS)
    g.lua.execute(DEBUG_CONTEXTS)


def change(g, region, reason, previous=BEASTMEN):
    g.fire("RegionFactionChangeEvent", g.make_change_context(region, reason, previous))


def test_release_build_keeps_fog_of_war(g):
    setup(g, values={"invasion_erase": True})
    turn(g, faction=EMPIRE, human=True)
    g.fire("WorldStartRound", g.lua.table())
    assert [c for c in calls(g) if "shroud" in c[0]] == []


def test_debug_build_lifts_fog_of_war_only_when_ticked(gd):
    debug_setup(gd, {})
    assert [c for c in calls(gd) if "shroud" in c[0]] == []
    gd.MCT_VALUES["debug_reveal_map"] = True
    gd.CALLS = gd.lua.table()
    turn(gd, faction=EMPIRE, human=True)
    shroud = [c for c in calls(gd) if "shroud" in c[0]]
    assert ("show_shroud", False) in shroud
    assert sorted(c[2] for c in shroud if c[0] == "make_region_visible_in_shroud") == ["r1", "r2", "r3", "r9"]
    assert all(c[1] == EMPIRE for c in shroud if c[0] == "make_region_visible_in_shroud")
    gd.CALLS = gd.lua.table()
    turn(gd, faction=BEASTMEN, human=False)
    assert [c for c in calls(gd) if "shroud" in c[0]] == []


def test_release_build_skips_debug_lines(g):
    setup(g, values={"invasion_erase": True})
    g.OUT = g.lua.table()
    ai_raze(g, "r1")
    assert not any(line.startswith("raze event") for line in logged(g))


def scenario(gd):
    """A whole invasion: before, scripted razes at the start, its razes, a normal raze, the end."""
    debug_setup(gd, {"invasion_erase": True, "allow_rebuild": True})
    gd.lua.execute(EPISODE % "false")
    gd.episode_chaos_invasion.persistent.current_stage_index = 2
    gd.TURN = 80
    gd.fire("WorldStartRound", gd.lua.table())
    turn(gd, faction=EMPIRE, human=True)
    # the invasion begins: its script razes r9 (no raze event), then the invasion spawns
    gd.episode_chaos_invasion.persistent.current_stage_index = 3
    vanilla_raze(gd, "r9")
    change(gd, "r9", "abandoned", previous="wh_main_chs_chaos")
    gd.episode_chaos_invasion.persistent.invasion_spawned = True
    turn(gd, faction=EMPIRE, human=True)
    gd.run_callbacks()
    # the invasion razes r1 and r2; the vanilla update gives the icon
    gd.lua.execute("""
        function episode_chaos_invasion:update_razed_region(region_key)
            CALLS[#CALLS + 1] = {"update_razed_region", region_key}
            REGION_BUNDLES[region_key] = REGION_BUNDLES[region_key] or {}
            REGION_BUNDLES[region_key]["%s"] = true
        end""" % INVASION_ICON)
    for region in ("r1", "r2"):
        gd.ABANDONED[region] = True
        change(gd, region, "abandoned", previous=EMPIRE)
        gd.fire("CharacterRazedSettlement", gd.make_context(596, False, region, INVASION))
    # beastmen raze r3 normally
    gd.ABANDONED["r3"] = True
    gd.fire("CharacterRazedSettlement", gd.make_context(596, False, "r3", BEASTMEN))
    vanilla_raze(gd, "r3")
    change(gd, "r3", "abandoned", previous=EMPIRE)
    gd.run_callbacks()
    gd.TURN = 81
    gd.fire("WorldStartRound", gd.lua.table())
    turn(gd, faction=EMPIRE, human=True)
    # the invasion ends; a save and load logs the state of every erased ruin
    gd.episode_chaos_invasion.persistent.current_stage_index = 5
    gd.TURN = 95
    gd.fire("WorldStartRound", gd.lua.table())
    turn(gd, faction=EMPIRE, human=True)
    for f in gd.FIRST_TICK.values():
        f()
    return logged(gd)


def test_debug_log_tells_the_whole_invasion(gd):
    lines = scenario(gd)
    print("\n".join(lines))
    text = "\n".join(lines)
    expected = [
        "debug build: fog of war kept, the MCT box is off",
        "owner change at r9: wh_main_chs_chaos -> nobody, reason abandoned, not erased, NOT blocked, not marked, invasion icon",
        "erased r9 as the Chaos Invasion began",
        "raze event at r1 by " + INVASION + " (wh_main_chs_chaos, AI), in ruins already true, no invasion icon, "
        "invasion stage episode_chaos_invasion_stage_main, spawned true",
        "AI raze of r1 by the Chaos Invasion erased",
        "province of r1 left to the Chaos Invasion's script",
        "Chaos Invasion updated r1, icon was missing, icon now there",
        "province p1: 3 of 3 in ruins, event area area_p1 3 of 3 in ruins, scorched by us false "
        "[r1 erased +icon +block; r2 erased +icon +block; r3 ruin +icon]",
        "raze event at r3 by " + BEASTMEN + " (wh_dlc03_bst_beastmen, AI), in ruins already true",
        "loaded, 3 erased ruins",
        "provinces on load: 2 with erased or invasion ruins",
    ]
    for line in expected:
        assert line in text, line


# Debug build: MCT box "Start the Chaos Invasion now"

MANAGER = """
episodes_manager = {}
function episodes_manager:get_episode_stage_index_by_name(episode, name)
    assert(name == "episode_chaos_invasion_stage_main")
    return 3
end
function episodes_manager:start_episode(episode)
    CALLS[#CALLS + 1] = {"start_episode"}
    episode.persistent.current_stage_index = 1
end
function episodes_manager:advance_stage(episode, stage)
    CALLS[#CALLS + 1] = {"advance_stage", stage}
    episode.persistent.current_stage_index = stage + 1
end
"""


def debug_start(gd, stage=None, lords=True, ticked=True):
    debug_setup(gd, {"debug_start_invasion": ticked})
    gd.lua.execute(EPISODE % "false")
    gd.lua.execute(MANAGER)
    if lords:
        gd.episode_chaos_invasion.persistent.legendary_lords = gd.lua.table()
    gd.episode_chaos_invasion.persistent.current_stage_index = stage
    gd.CALLS = gd.lua.table()
    gd.OUT = gd.lua.table()
    gd.fire("MctFinalized", gd.lua.table())
    gd.run_callbacks()
    return [c for c in calls(gd) if c[0] in ("start_episode", "advance_stage")]


def test_debug_box_starts_and_skips_warnings(gd):
    assert debug_start(gd) == [("start_episode",), ("advance_stage", 1), ("advance_stage", 2)]
    assert gd.episode_chaos_invasion.persistent.current_stage_index == 3
    assert "debug start: Chaos Invasion now at stage 3" in logged(gd)


def test_debug_box_skips_remaining_warning(gd):
    assert debug_start(gd, stage=2) == [("advance_stage", 2)]


def test_debug_box_does_nothing_once_begun(gd):
    assert debug_start(gd, stage=3) == []
    assert "debug start: the Chaos Invasion already began or ended (stage 3)" in logged(gd)


def test_debug_box_does_nothing_after_the_end(gd):
    assert debug_start(gd, stage=-1) == []


def test_debug_box_unticked_does_nothing(gd):
    assert debug_start(gd, ticked=False) == []


def test_debug_box_refuses_without_invasion_in_campaign(gd):
    assert debug_start(gd, lords=False) == []
    assert any(line.startswith("debug start: the Chaos Invasion is not available here") for line in logged(gd))


def test_release_build_ignores_debug_box(g):
    setup(g, values={"debug_start_invasion": True})
    g.lua.execute(EPISODE % "false")
    g.lua.execute(MANAGER)
    g.episode_chaos_invasion.persistent.legendary_lords = g.lua.table()
    g.fire("MctFinalized", g.lua.table())
    g.run_callbacks()
    assert [c for c in calls(g) if c[0] in ("start_episode", "advance_stage")] == []


def test_debug_build_logs_every_turn(gd):
    debug_setup(gd, {})
    gd.OUT = gd.lua.table()
    turn(gd, faction=BEASTMEN, human=False)
    gd.fire("FactionTurnEnd", gd.make_turn_context(BEASTMEN, False))
    assert "turn start of " + BEASTMEN in logged(gd)
    assert "turn end of " + BEASTMEN in logged(gd)


def test_release_build_does_not_log_turns(g):
    setup(g, values={})
    g.OUT = g.lua.table()
    turn(g, faction=BEASTMEN, human=False)
    assert not any(line.startswith("turn start of") for line in logged(g))


# Regression: anything about the invasion at the start of a turn crashed the game when an episode
# stage began (the event feed showing its messages)

def test_turn_starts_never_touch_the_invasion(g):
    beginning(g)
    vanilla_raze(g, "r1")
    g.episode_chaos_invasion.persistent.invasion_spawned = True
    g.OUT = g.lua.table()
    g.CALLS = g.lua.table()
    g.fire("WorldStartRound", g.lua.table())
    turn(g, faction=BEASTMEN, human=False)
    turn(g, faction=EMPIRE, human=True)
    assert erased(g) == []
    assert calls(g) == []
    assert not any("Invasion" in line for line in logged(g))


def test_mod_never_calls_into_the_episode(g):
    beginning(g, values={"invasion_erase": True, "ai_erase": True, "ai_erase_chance": 100})
    fall(g, "r9")
    g.episode_chaos_invasion.persistent.invasion_spawned = True
    ai_raze(g, "r1", faction=INVASION)
    g.run_callbacks()
    g.fire("WorldStartRound", g.lua.table())
    turn(g, faction=EMPIRE, human=True)
    assert ("is_main_invasion_active",) not in calls(g)


def test_final_battle_stage_counts_as_active(g):
    setup(g, values={"invasion_erase": True})
    episode(g)
    g.episode_chaos_invasion.persistent.current_stage_index = 4
    ai_raze(g, "r1", faction=INVASION)
    g.run_callbacks()
    assert updates(g) == ["r1"]
