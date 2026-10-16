from pathlib import Path

import pytest
from lupa.lua51 import LuaRuntime

from tools.render import render_script

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = (ROOT / "src/script/campaign/mod/permraze.lua").read_text(encoding="utf-8")
MOCK = (ROOT / "tests/lua/mock_game.lua").read_text(encoding="utf-8")
OUR_ID = "2100500000"
EMPIRE, SKAVEN = "wh_main_emp_empire", "wh2_main_skv_skaven"
ARCHAON, ARCHAON_VASSAL = "wh_main_chs_chaos", "wh3_main_kho_vassal"
SKAVEN_FACTION = "wh2_main_skv_clan_mors"
BEASTMEN, VAMPIRES = "wh_dlc03_bst_beastmen", "wh_main_vmp_vampire_counts"
# Same as cultures_with_look() on vanilla data, trimmed to what the tests use.
LOOK_CULTURES = [SKAVEN, "wh_main_chs_chaos", "wh_dlc03_bst_beastmen", "wh_main_vmp_vampire_counts"]

# Same shape as the vanilla archaon_narrative this mod defers to.
ARCHAON_NARRATIVE = """
archaon_narrative = {
    config = { archaon_faction_key = "wh_main_chs_chaos",
               mission_data = { long_victory_mission = { main_objective_options = {
                   option_1 = { key = "conqueror" }, option_2 = { key = "destroyer" } } } } },
    persistent = { long_victory_condition_chosen_option_key = %s },
}
function archaon_narrative:is_archaon_or_archaon_vassal(faction)
    local master = faction:master()
    return faction:name() == "wh_main_chs_chaos" or (not master:is_null_interface() and master:name() == "wh_main_chs_chaos")
end
"""


@pytest.fixture
def g():
    lua = LuaRuntime(unpack_returned_tuples=True)
    lua.execute(MOCK)
    lua.execute(render_script(TEMPLATE, [int(OUR_ID)], LOOK_CULTURES))
    g = lua.globals()
    g.lua = lua
    return g


def calls(g):
    return [tuple(c[i] for i in range(1, len(c) + 1)) for c in g.CALLS.values()]


def decide(g, region, option=OUR_ID, human=True, faction=EMPIRE):
    g.permraze.on_decision(g.permraze, option, human, region, faction)


def raze(g, region, faction=EMPIRE):
    g.ABANDONED[region] = True
    g.permraze.on_razed(g.permraze, region, faction)


def activations(g):
    return [c for c in calls(g) if c[0] == "activate_campaign_map_event_area"]


ERASE_R1 = [
    ("cai_disable_targeting_against_settlement", "settlement:r1"),
    ("apply_effect_bundle_to_region", "permraze_block_occupation", "r1", 0),
    ("reset_settlement_type", "r1", "wh3_dlc29_devastated", 1),
    ("set_settlement_devastated_state", "r1", "devastated"),
]


def test_human_decision_then_razed_erases(g):
    decide(g, "r1")
    raze(g, "r1")
    assert calls(g) == ERASE_R1
    assert g.permraze.persistent.erased["r1"] is True


def test_razed_before_decision_still_erases(g):
    raze(g, "r1")
    decide(g, "r1")
    assert calls(g) == ERASE_R1


def test_ai_decision_ignored(g):
    decide(g, "r1", human=False)
    raze(g, "r1")
    assert calls(g) == []


def test_vanilla_raze_id_ignored(g):
    decide(g, "r1", option="596")
    raze(g, "r1")
    assert calls(g) == []


def test_razed_without_decision_ignored(g):
    raze(g, "r1")
    assert calls(g) == []


def test_turn_state_cleared_each_round(g):
    raze(g, "r1")
    g.permraze.clear_turn_state(g.permraze)
    decide(g, "r1")
    assert calls(g) == []


def test_province_threshold(g):
    decide(g, "r1", faction=BEASTMEN); raze(g, "r1", faction=BEASTMEN)
    assert activations(g) == []
    decide(g, "r2", faction=BEASTMEN); raze(g, "r2", faction=BEASTMEN)
    decide(g, "r3", faction=BEASTMEN); raze(g, "r3", faction=BEASTMEN)
    assert activations(g) == [("activate_campaign_map_event_area", "area_p1", "wh_dlc03_bst_beastmen")]
    assert g.permraze.persistent.devastated_provinces["p1"] is True


def test_vampires_get_their_own_look(g):
    for r in ("r1", "r2"):
        decide(g, r, faction=VAMPIRES); raze(g, r, faction=VAMPIRES)
    assert activations(g) == [("activate_campaign_map_event_area", "area_p1", "wh_main_vmp_vampire_counts")]


def test_culture_without_look_leaves_land_alone(g):
    for r in ("r1", "r2", "r3"):
        decide(g, r); raze(g, r)
    assert activations(g) == []
    assert ("apply_effect_bundle_to_region", "permraze_block_occupation", "r3", 0) in calls(g)


def test_area_already_active_skipped(g):
    g.ACTIVE_AREAS["area_p1"] = True
    for r in ("r1", "r2"):
        decide(g, r, faction=BEASTMEN); raze(g, r, faction=BEASTMEN)
    assert not [c for c in calls(g) if c[0] == "activate_campaign_map_event_area"]


def test_no_event_area_no_activation(g):
    decide(g, "r9"); raze(g, "r9")
    assert [c[0] for c in calls(g)] == [c[0] for c in ERASE_R1]


def test_has_look(g):
    assert g.permraze.has_look(g.permraze, SKAVEN) is True
    assert g.permraze.has_look(g.permraze, EMPIRE) is False


def test_forbidden_calls_never_made(g):
    for r in ("r1", "r2", "r3", "r9"):
        decide(g, r); raze(g, r)
    names = {c[0] for c in calls(g)}
    assert not names & {"kill_character", "override_settlement_climate", "add_climate_override"}


def test_save_load_roundtrip(g):
    decide(g, "r1"); raze(g, "r1")
    ctx = g.lua.table()
    g.SAVE_CALLBACKS[1](ctx)
    g.permraze.persistent = None
    g.LOAD_CALLBACKS[1](ctx)
    assert g.permraze.persistent.erased["r1"] is True


def test_load_without_saved_state(g):
    g.LOAD_CALLBACKS[1](g.lua.table())
    p = g.permraze.persistent
    assert p.erased is not None and p.pending is not None
    assert p.razed is not None and p.devastated_provinces is not None
    assert calls(g) == []  # no script_error from load_named_value


CONTEXTS = """
function make_context(option, human, region, culture)
    local faction = { is_human = function() return human end, culture = function() return culture end,
                      name = function() return culture end }
    local character = { faction = function() return faction end }
    local residence = { region = function() return cm:get_region(region) end }
    return {
        occupation_decision = function() return option end,
        character = function() return character end,
        garrison_residence = function() return residence end,
    }
end
"""


def test_listeners_wire_context(g):
    for f in g.FIRST_TICK.values():
        f()
    g.lua.execute(CONTEXTS)
    g.fire("CharacterPerformsSettlementOccupationDecision", g.make_context(int(OUR_ID), True, "r1", EMPIRE))
    g.ABANDONED["r1"] = True
    g.fire("CharacterRazedSettlement", g.make_context(int(OUR_ID), True, "r1", EMPIRE))
    assert calls(g) == ERASE_R1


def test_ai_razed_listener_ignored(g):
    for f in g.FIRST_TICK.values():
        f()
    g.lua.execute(CONTEXTS)
    g.fire("CharacterRazedSettlement", g.make_context(int(OUR_ID), False, "r1", EMPIRE))
    assert g.permraze.persistent.razed["r1"] is None


@pytest.mark.parametrize("faction", [ARCHAON, ARCHAON_VASSAL])
def test_archaon_destroyer_province_left_to_archaon(g, faction):
    g.lua.execute(ARCHAON_NARRATIVE % '"destroyer"')
    for r in ("r1", "r2", "r3"):
        decide(g, r, faction=faction); raze(g, r, faction=faction)
    assert ("apply_effect_bundle_to_region", "permraze_block_occupation", "r1", 0) in calls(g)
    assert activations(g) == []


def test_archaon_conqueror_path_devastates_normally(g):
    g.lua.execute(ARCHAON_NARRATIVE % '"conqueror"')
    for r in ("r1", "r2"):
        decide(g, r, faction=ARCHAON); raze(g, r, faction=ARCHAON)
    assert activations(g) == [("activate_campaign_map_event_area", "area_p1", "wh_main_chs_chaos")]


def test_other_faction_devastates_while_archaon_is_destroyer(g):
    g.lua.execute(ARCHAON_NARRATIVE % '"destroyer"')
    for r in ("r1", "r2"):
        decide(g, r, faction=SKAVEN_FACTION); raze(g, r, faction=SKAVEN_FACTION)
    assert activations(g) == [("activate_campaign_map_event_area", "area_p1", "wh2_main_skv_skaven")]


def test_unknown_faction_still_erases_region(g):
    decide(g, "r1", faction="no_such_faction"); raze(g, "r1", faction="no_such_faction")
    assert calls(g)[:4] == ERASE_R1
