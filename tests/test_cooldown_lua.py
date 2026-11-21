"""Cooldown on ruins (MCT raze_cooldown, 0 by default): an attempt to erase forever that fails its roll
blocks the ruins for that many turns instead, put on as a bundle with a duration so the game counts it
down and lifts it. Attempts: an AI raze under AI erasing, and a player's Raze Forever under its own chance
(MCT raze_forever_chance, 100% by default: it always erases).
Ordinary vanilla razes are left alone."""

from test_ai_erase_lua import BEASTMEN, ERASE_R1, ai_raze, calls, logged, setup
from test_invasion_lua import debug_setup, gd  # noqa: F401
from test_permraze_lua import CONTEXTS, EMPIRE, OUR_ID, g  # noqa: F401
from test_rebuild_lua import turn

COOLDOWN = "permraze_cooldown_block"
INVASION = "wh3_dlc29_chaos_invasion_confederation_owner"
VANILLA_RAZE = 596
AI_ON = {"raze_cooldown": 4, "ai_erase": True, "ai_erase_chance": 25}
ROLLING = {"raze_cooldown": 5, "raze_forever_chance": 25}


def cooldowns(g):
    return [(c[2], c[3]) for c in calls(g) if c[0] == "apply_effect_bundle_to_region" and c[1] == COOLDOWN]


def player_raze(g, region, option=int(OUR_ID), decision_first=True):
    decision = ("CharacterPerformsSettlementOccupationDecision", g.make_context(option, True, region, EMPIRE))
    raze = ("CharacterRazedSettlement", g.make_context(option, True, region, EMPIRE))
    for event, ctx in ((decision, raze) if decision_first else (raze, decision)):
        if event == "CharacterRazedSettlement":
            g.ABANDONED[region] = True
        g.fire(event, ctx)


# AI razes under AI erasing

def test_off_by_default_without_mct(g):
    setup(g, values=None)
    ai_raze(g, "r1")
    assert calls(g) == []


def test_failed_ai_roll_gets_the_cooldown(g):
    setup(g, values=AI_ON, roll=26)
    ai_raze(g, "r1")
    assert calls(g) == [("apply_effect_bundle_to_region", COOLDOWN, "r1", 4)]
    assert g.permraze.persistent.erased["r1"] is None


def test_successful_ai_roll_erases_without_cooldown(g):
    setup(g, values=AI_ON, roll=25)
    ai_raze(g, "r1")
    assert calls(g) == ERASE_R1


def test_zero_turns_is_off(g):
    setup(g, values=dict(AI_ON, raze_cooldown=0), roll=26)
    ai_raze(g, "r1")
    assert calls(g) == []


def test_cooldown_turns_are_whole(g):
    setup(g, values=dict(AI_ON, raze_cooldown=7.6), roll=26)
    ai_raze(g, "r1")
    assert cooldowns(g) == [("r1", 7)]


def test_ai_raze_without_ai_erasing_is_left_alone(g):
    setup(g, values={"raze_cooldown": 5, "ai_erase": False}, roll=26)
    ai_raze(g, "r1")
    assert calls(g) == []


def test_culture_at_zero_percent_is_left_alone(g):
    setup(g, values=dict(AI_ON, ai_erase_chance=100, ai_chance_wh_dlc03_bst_beastmen="0"))
    ai_raze(g, "r1")
    assert calls(g) == []


def test_nagash_legions_are_left_alone(g):
    setup(g, values=dict(AI_ON, ai_erase_chance=100), roll=100)
    ai_raze(g, "r1", faction="nagash_legions")
    assert calls(g) == []


def test_invasion_raze_erased_gets_no_cooldown(g):
    setup(g, values=dict(AI_ON, invasion_erase=True), roll=100)
    ai_raze(g, "r1", faction=INVASION)
    assert cooldowns(g) == []
    assert g.permraze.persistent.erased["r1"].faction == INVASION


def test_invasion_raze_without_its_option_follows_ai_erasing(g):
    setup(g, values=AI_ON, roll=26)
    ai_raze(g, "r1", faction=INVASION)
    assert cooldowns(g) == [("r1", 4)]


def test_failing_again_puts_the_cooldown_on_again(g):
    setup(g, values=AI_ON, roll=26)
    ai_raze(g, "r1")
    ai_raze(g, "r1")
    assert cooldowns(g) == [("r1", 4), ("r1", 4)]


def test_erasing_takes_a_cooldown_off(g):
    setup(g, values=AI_ON, roll=26)
    ai_raze(g, "r1")
    g.ROLL = 1
    g.CALLS = g.lua.table()
    ai_raze(g, "r1")
    assert calls(g)[:len(ERASE_R1)] == ERASE_R1
    assert ("remove_bundle", COOLDOWN, "r1") in calls(g)


def test_erased_ruins_get_no_cooldown(g):
    setup(g, values=AI_ON, roll=1)
    ai_raze(g, "r1")
    g.ROLL = 100
    g.CALLS = g.lua.table()
    ai_raze(g, "r1", faction="wh2_dlc09_tmb_exiles_of_nehek")
    assert calls(g) == []


def test_cooldown_is_logged(g):
    setup(g, values=AI_ON, roll=26)
    g.OUT = g.lua.table()
    ai_raze(g, "r1")
    assert "cooldown of 4 turns on r1, razed by " + BEASTMEN in logged(g)


# A player's Raze Forever

def test_raze_forever_always_erases_by_default(g):
    setup(g, values={"raze_cooldown": 5, "ai_erase": True, "ai_erase_chance": 1}, roll=100)
    player_raze(g, "r1")
    assert calls(g) == ERASE_R1
    assert g.ROLL_MAX is None


def test_raze_forever_at_100_percent_never_rolls(g):
    setup(g, values={"raze_cooldown": 5, "raze_forever_chance": 100}, roll=100)
    player_raze(g, "r1")
    assert calls(g) == ERASE_R1
    assert g.ROLL_MAX is None


def test_raze_forever_rolls_the_general_chance(g):
    setup(g, values=ROLLING, roll=25)
    player_raze(g, "r1")
    assert calls(g) == ERASE_R1
    assert g.permraze.persistent.erased["r1"].faction == EMPIRE
    assert g.ROLL_MAX == 100


def test_failed_raze_forever_gets_the_cooldown(g):
    setup(g, values=ROLLING, roll=26)
    player_raze(g, "r1")
    assert calls(g) == [("apply_effect_bundle_to_region", COOLDOWN, "r1", 5)]
    assert g.permraze.persistent.erased["r1"] is None


def test_failed_raze_forever_when_the_raze_comes_first(g):
    setup(g, values=ROLLING, roll=26)
    player_raze(g, "r1", decision_first=False)
    assert cooldowns(g) == [("r1", 5)]


def test_failed_raze_forever_without_cooldown_leaves_plain_ruins(g):
    setup(g, values=dict(ROLLING, raze_cooldown=0), roll=26)
    player_raze(g, "r1")
    assert calls(g) == []
    assert g.permraze.persistent.erased["r1"] is None


def test_raze_forever_ignores_the_ai_chances(g):
    setup(g, values=dict(ROLLING, ai_erase=True, ai_erase_chance=100, ai_chance_wh_main_emp_empire="100"), roll=26)
    player_raze(g, "r1")
    assert g.permraze.persistent.erased["r1"] is None


def test_raze_forever_chance_works_without_ai_erasing(g):
    setup(g, values=dict(ROLLING, ai_erase=False), roll=26)
    player_raze(g, "r1")
    assert cooldowns(g) == [("r1", 5)]


def test_failed_raze_forever_is_logged(g):
    setup(g, values=ROLLING, roll=60)
    g.OUT = g.lua.table()
    player_raze(g, "r1")
    assert "Raze Forever of r1 by " + EMPIRE + " failed: rolled 60, chance 25" in logged(g)


# Ordinary vanilla razes are left alone

def test_vanilla_raze_gets_nothing(g):
    setup(g, values=ROLLING, roll=1)
    player_raze(g, "r1", option=VANILLA_RAZE)
    player_raze(g, "r2", option=VANILLA_RAZE, decision_first=False)
    assert calls(g) == []
    assert g.ROLL_MAX is None


# Nothing at the start of a turn: the game lifts the cooldown itself

def test_turn_starts_never_touch_the_cooldown(g):
    setup(g, values=AI_ON, roll=26)
    ai_raze(g, "r1")
    g.CALLS = g.lua.table()
    g.fire("WorldStartRound", g.lua.table())
    turn(g, faction=BEASTMEN, human=False)
    turn(g, faction=EMPIRE, human=True)
    assert calls(g) == []


def test_debug_report_on_load_lists_cooling_ruins(gd):
    debug_setup(gd, AI_ON)
    gd.lua.execute(CONTEXTS)
    gd.ROLL = 26
    gd.ABANDONED["r1"] = True
    gd.fire("CharacterRazedSettlement", gd.make_context(VANILLA_RAZE, False, "r1", BEASTMEN))
    gd.OUT = gd.lua.table()
    for f in gd.FIRST_TICK.values():
        f()
    assert any("r1 ruin +cooldown" in line for line in logged(gd))


def test_raze_forever_at_0_percent_never_erases(g):
    setup(g, values={"raze_cooldown": 5, "raze_forever_chance": 0}, roll=1)
    player_raze(g, "r1")
    assert g.permraze.persistent.erased["r1"] is None
    assert cooldowns(g) == [("r1", 5)]
