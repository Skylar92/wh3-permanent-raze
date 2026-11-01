"""Rewards that vanilla scripts give by option id are given for our copy of that option too."""
import pytest
from lupa.lua51 import LuaRuntime

from test_corruption_lua import load_corruption
from test_permraze_lua import LOOK_CULTURES, MOCK, OUR_ID, TEMPLATE, first_tick
from tools.render import render_script

FOREST_ID, BEASTMEN_ID, NURGLE_ID = "2100500001", "2100500002", "2100500003"
SOURCES = {int(OUR_ID): 664, int(FOREST_ID): 1598549406, int(BEASTMEN_ID): 411, int(NURGLE_ID): 1714590130}
TAMURKHAN = "wh3_dlc25_nur_tamurkhan"

CONTEXT = """
function make_context(option, human, region, faction_name)
    local faction = { is_human = function() return human end, name = function() return faction_name end }
    local character = { faction = function() return faction end, command_queue_index = function() return 42 end }
    local residence = { region = function() return cm:get_region(region) end }
    return {
        occupation_decision = function() return option end,
        character = function() return character end,
        garrison_residence = function() return residence end,
    }
end
"""

# Same shapes as the vanilla scripts this mod calls into.
VANILLA = """
GOT = {}
local function got(...) GOT[#GOT + 1] = table.concat({...}, " ") end
Worldroots = { razing_value = 5 }
function Worldroots:is_adjacent_to_forest(region_key)
    if region_key == "r1" then return { key = "forest_1" } end
end
function Worldroots:add_pooled_resource_to_all_wood_elves(forest, factor, amount, excluded, in_turn_gain)
    got("forest", forest.key, factor, amount, tostring(excluded), tostring(in_turn_gain))
end
function cm:get_factions_bonus_value(faction, key)
    if key == "additional_worldroots_health_from_razing" then return 2 end
    return 0
end
function cm:replenish_action_points(lookup, factor) got("ap", lookup, factor) end
Bloodgrounds = { razing_settlement_options = { ["1172"] = 0.2, ["411"] = 0.4 },
                 defiled_bloodground_vfx_key = "wh2_dlc17_bloodground_defilement" }
function Bloodgrounds:is_bloodground_region(region_key)
    if region_key == "r2" then return { ritual_completed = true } end
end
function Bloodgrounds:apply_vfx(region_key, vfx) got("vfx", region_key, vfx) end
function Bloodgrounds:update_effect_bundles_for_bloodgrounds() got("bloodground_bundles") end
nur_chieftains = { faction = "wh3_dlc25_nur_tamurkhan",
                   exalted_hero = { has_spawned = true, pr_deference_key = "exalted", pr_factor_unique = "razing" } }
function nur_chieftains:increase_deference_amount(key, factor, amount) got("deference", key, factor, amount) end
"""


@pytest.fixture
def g():
    lua = LuaRuntime(unpack_returned_tuples=True)
    lua.execute(MOCK)
    lua.execute(render_script(TEMPLATE, [int(i) for i in SOURCES], LOOK_CULTURES, SOURCES))
    g = lua.globals()
    g.lua = lua
    load_corruption(g)
    lua.execute(CONTEXT)
    lua.execute(VANILLA)
    first_tick(g)
    return g


def decide(g, option, region="r1", human=True, faction="wh_dlc05_wef_wood_elves"):
    g.fire("CharacterPerformsSettlementOccupationDecision", g.make_context(option, human, region, faction))


def got(g):
    return list(g.GOT.values())


def test_clear_heathland_feeds_forest(g):
    decide(g, FOREST_ID)
    assert got(g) == ["forest forest_1 wh2_dlc16_resource_factor_razing_and_battles 7 nil true"]


def test_forest_away_from_forest_feeds_nothing(g):
    decide(g, FOREST_ID, region="r2")
    assert got(g) == []


def test_forest_ai_feeds_nothing(g):
    decide(g, FOREST_ID, human=False)
    assert got(g) == []


def test_beastmen_raze_gives_back_action_points(g):
    decide(g, BEASTMEN_ID)
    assert got(g) == ["ap character_cqi:42 0.4", "bloodground_bundles"]


def test_beastmen_raze_defiles_completed_bloodground(g):
    decide(g, BEASTMEN_ID, region="r2")
    assert got(g) == ["vfx r2 wh2_dlc17_bloodground_defilement", "ap character_cqi:42 0.4", "bloodground_bundles"]


def test_nurgle_raze_gives_exalted_hero_deference(g):
    decide(g, NURGLE_ID, faction=TAMURKHAN)
    assert got(g) == ["deference exalted razing 1"]


def test_nurgle_deference_needs_spawned_hero_and_tamurkhan(g):
    decide(g, NURGLE_ID, faction="wh3_main_nur_poxmakers_of_nurgle")
    g.lua.execute("nur_chieftains.exalted_hero.has_spawned = false")
    decide(g, NURGLE_ID, faction=TAMURKHAN)
    assert got(g) == []


def test_option_without_scripted_reward_gives_nothing(g):
    decide(g, OUR_ID)
    assert got(g) == []


def test_without_vanilla_scripts_no_error(g):
    g.lua.execute("Worldroots = nil; Bloodgrounds = nil; nur_chieftains = nil")
    for option in (FOREST_ID, BEASTMEN_ID, NURGLE_ID):
        decide(g, option)
    assert got(g) == []
    assert not [s for s in g.OUT.values() if "failed" in s]


def test_reward_error_does_not_stop_erasing(g):
    g.lua.execute("function Worldroots:add_pooled_resource_to_all_wood_elves() error('boom') end")
    decide(g, FOREST_ID)
    assert g.permraze.persistent.pending["r1"] == "wh_dlc05_wef_wood_elves"
    assert any("scripted reward failed" in s for s in g.OUT.values())
