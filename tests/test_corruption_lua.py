from pathlib import Path

import pytest
from lupa.lua51 import LuaRuntime

from tools.corruption import campaign_defaults
from tools.render import render_corruption_script

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = (ROOT / "src/script/campaign/mod/permraze_corruption.lua").read_text(encoding="utf-8")
MOCK = (ROOT / "tests/lua/mock_game.lua").read_text(encoding="utf-8")

EMPIRE, MORS, NAGGAROND = "wh_main_emp_empire", "wh2_main_skv_clan_mors", "wh2_main_def_naggarond"
MORATHI, TRIPLETS = "wh2_main_def_cult_of_pleasure", "wh3_dlc29_chs_host_of_the_triplets"
CHAOS, DAEMON_PRINCE = "wh_main_chs_chaos", "wh3_main_dae_daemon_prince"
SAVED_KEY = "IEVictoryConditionRewardsDaemonPrinceAscendancyPath"


def load_corruption(g):
    g.lua.execute(render_corruption_script(TEMPLATE))


@pytest.fixture
def g():
    lua = LuaRuntime(unpack_returned_tuples=True)
    lua.execute(MOCK)
    g = lua.globals()
    g.lua = lua
    load_corruption(g)
    return g


def set_mct(g, values, broken=False):
    """Install a get_mct() global; values maps option key -> finalized value, None means no mod."""
    g.MCT_VALUES = g.lua.table_from(values) if values is not None else None
    g.MCT_BROKEN = broken
    g.lua.execute("""
        function get_mct()
            if MCT_BROKEN then error("mct is broken") end
            return { get_mod_by_key = function(_, key)
                if key ~= "permraze" or MCT_VALUES == nil then return nil end
                return { get_option_by_key = function(_, k)
                    local v = MCT_VALUES[k]
                    if v == nil then return nil end
                    return { get_finalized_setting = function() return v end }
                end }
            end }
        end
    """)


def settings(g):
    return g.permraze_corruption.settings(g.permraze_corruption)


def effect(g, faction, s=None, gods=None):
    s = s if s is not None else settings(g)
    gods = gods if gods is not None else g.lua.table()
    return g.permraze_corruption.effect_for(g.permraze_corruption, faction, s, gods)


def test_settings_without_mct_are_defaults(g):
    s = settings(g)
    assert s["mode"] == "off"
    assert s["ruin_strength"] == 5
    assert s["culture_wh_main_emp_empire"] == "reduce"
    for k, v in campaign_defaults().items():
        assert s[k] == v


def test_settings_from_mct(g):
    set_mct(g, {"mode": "per_province", "multiplier": 200})
    s = settings(g)
    assert s["mode"] == "per_province"
    assert s["multiplier"] == 200
    assert s["threshold"] == 50


def test_settings_mct_broken(g):
    set_mct(g, {"mode": "per_province"}, broken=True)
    assert settings(g)["mode"] == "off"


def test_settings_mod_not_registered(g):
    set_mct(g, None)
    assert settings(g)["mode"] == "off"


def test_settings_option_missing(g):
    set_mct(g, {"multiplier": 200})
    s = settings(g)
    assert s["multiplier"] == 200
    assert s["mode"] == "off"


def test_settings_wrong_type_ignored(g):
    set_mct(g, {"multiplier": "abc", "daemon_follow_god": 1})
    s = settings(g)
    assert s["multiplier"] == 100
    assert s["daemon_follow_god"] is False


def test_effect_for_culture_default(g):
    assert effect(g, EMPIRE) == "reduce"
    assert effect(g, MORS) == "skaven"
    assert effect(g, NAGGAROND) == "none"


def test_effect_for_overrides(g):
    set_mct(g, {"culture_wh_main_chs_chaos": "reduce"})
    s = settings(g)
    assert effect(g, MORATHI, s) == "slaanesh"
    assert effect(g, TRIPLETS, s) == "nurgle"
    assert effect(g, CHAOS, s) == "reduce"


def test_effect_for_mct_culture_override(g):
    set_mct(g, {"culture_wh_main_emp_empire": "khorne"})
    assert effect(g, EMPIRE) == "khorne"


def test_effect_for_nil_faction_is_none(g):
    assert effect(g, None) == "none"


def test_effect_for_unknown_faction_is_none(g):
    assert effect(g, "no_such_faction") == "none"


def test_daemon_prince_undivided_by_default(g):
    set_mct(g, {"daemon_follow_god": False})
    gods = g.lua.table_from({DAEMON_PRINCE: "nurgle"})
    assert effect(g, DAEMON_PRINCE, settings(g), gods) == "chaos"


def test_daemon_prince_follows_god(g):
    set_mct(g, {"daemon_follow_god": True})
    s = settings(g)
    gods = g.lua.table_from({DAEMON_PRINCE: "nurgle"})
    assert effect(g, DAEMON_PRINCE, s, gods) == "nurgle"
    g.SAVED_VALUES = g.lua.table_from({SAVED_KEY: "wh3_main_ritual_dae_ascend_tzeentch"})
    assert effect(g, DAEMON_PRINCE, s) == "tzeentch"
    g.SAVED_VALUES = g.lua.table_from({SAVED_KEY: "wh3_main_ritual_dae_ascend_undivided"})
    assert effect(g, DAEMON_PRINCE, s) == "chaos"
    g.SAVED_VALUES = g.lua.table_from({SAVED_KEY: "wh3_main_ritual_dae_ascend_bogus"})
    assert effect(g, DAEMON_PRINCE, s) == "chaos"
    g.SAVED_VALUES = g.lua.table()
    assert effect(g, DAEMON_PRINCE, s) == "chaos"


def test_other_daemon_faction_without_god_data_is_chaos(g):
    set_mct(g, {"daemon_follow_god": True, "culture_wh3_main_dae_daemons": "reduce"})
    assert effect(g, "wh3_main_dae_daemons") == "chaos"


RUIN_KEY, PROVINCE_KEY = "permraze_ruin_corruption", "permraze_province_corruption"
REDUCE = "wh3_main_effect_corruption_reduction_events"
SCOPE = "region_to_province_own_unseen"
CHAOS_EFFECT = "wh3_main_effect_corruption_chaos_events_bad"


def to_lua(g, value):
    if isinstance(value, dict):
        return g.lua.table_from({k: to_lua(g, v) for k, v in value.items()})
    return value


def erased(g, **regions):
    """regions: region key -> (faction, order)."""
    return {r: {"faction": f, "order": o} for r, (f, o) in regions.items()}


def refresh(g, erased_map, devastated=None):
    state = {"erased": erased_map}
    if devastated is not None:
        state["devastated_provinces"] = devastated
    g.permraze_corruption.refresh(g.permraze_corruption, to_lua(g, state))


def calls(g, name):
    return [list(c.values()) for c in g.CALLS.values() if c[1] == name]


def bundles(g):
    return {r: sorted(k for k in t.keys()) for r, t in g.REGION_BUNDLES.items() if any(True for _ in t.keys())}


def test_off_applies_nothing(g):
    refresh(g, erased(g, r1=(EMPIRE, 1)))
    assert calls(g, "apply_custom") == []


def test_per_settlement_each_ruin(g):
    set_mct(g, {"mode": "per_settlement"})
    refresh(g, erased(g, r1=(EMPIRE, 1), r2=(EMPIRE, 2)))
    assert calls(g, "apply_custom") == [
        ["apply_custom", RUIN_KEY, "r1", REDUCE, SCOPE, -5],
        ["apply_custom", RUIN_KEY, "r2", REDUCE, SCOPE, -5],
    ]


def test_multiplier_scales(g):
    set_mct(g, {"mode": "per_settlement", "multiplier": 200})
    refresh(g, erased(g, r1=(CHAOS, 1)))
    assert calls(g, "apply_custom") == [
        ["apply_custom", RUIN_KEY, "r1", "wh3_main_effect_corruption_chaos_events_bad", SCOPE, 10]]


def test_applied_bundles_are_permanent(g):
    set_mct(g, {"mode": "per_settlement"})
    refresh(g, erased(g, r1=(CHAOS, 1), r2=(EMPIRE, 2)))
    durations = [b.duration for b in g.APPLIED_BUNDLES.values()]
    assert durations == [0, 0]


def test_fractional_value_rounds_half_up(g):
    set_mct(g, {"mode": "per_settlement", "multiplier": 150})
    refresh(g, erased(g, r1=(CHAOS, 1)))
    assert calls(g, "apply_custom") == [
        ["apply_custom", RUIN_KEY, "r1", "wh3_main_effect_corruption_chaos_events_bad", SCOPE, 8]]


def test_value_rounding_to_zero_applies_nothing(g):
    set_mct(g, {"mode": "per_settlement", "ruin_strength": 1, "multiplier": 40})
    refresh(g, erased(g, r1=(CHAOS, 1)))
    assert calls(g, "apply_custom") == []


def test_reduce_rounds_magnitude_then_negates(g):
    set_mct(g, {"mode": "per_settlement", "multiplier": 150})
    refresh(g, erased(g, r1=(EMPIRE, 1)))
    assert calls(g, "apply_custom") == [
        ["apply_custom", RUIN_KEY, "r1", REDUCE, SCOPE, -8]]


def test_zero_strength_applies_nothing(g):
    set_mct(g, {"mode": "per_settlement", "multiplier": 0})
    refresh(g, erased(g, r1=(CHAOS, 1)))
    assert calls(g, "apply_custom") == []
    set_mct(g, {"mode": "per_settlement", "ruin_strength": 0})
    refresh(g, erased(g, r1=(CHAOS, 1)))
    assert calls(g, "apply_custom") == []


def test_none_culture_applies_nothing(g):
    set_mct(g, {"mode": "per_settlement"})
    refresh(g, erased(g, r1=(NAGGAROND, 1)))
    assert calls(g, "apply_custom") == []


def test_per_province_needs_threshold(g):
    set_mct(g, {"mode": "per_province"})
    refresh(g, erased(g, r1=(CHAOS, 1)))
    assert calls(g, "apply_custom") == []
    refresh(g, erased(g, r1=(CHAOS, 1), r2=(CHAOS, 2)))
    assert calls(g, "apply_custom") == [
        ["apply_custom", PROVINCE_KEY, "r2", "wh3_main_effect_corruption_chaos_events_bad", SCOPE, 30]]


def test_threshold_setting(g):
    set_mct(g, {"mode": "per_province", "threshold": 70})
    refresh(g, erased(g, r1=(CHAOS, 1), r2=(CHAOS, 2)))
    assert calls(g, "apply_custom") == []
    refresh(g, erased(g, r1=(CHAOS, 1), r2=(CHAOS, 2), r3=(CHAOS, 3)))
    assert calls(g, "apply_custom") == [
        ["apply_custom", PROVINCE_KEY, "r3", CHAOS_EFFECT, SCOPE, 30]]


def test_province_majority_faction(g):
    set_mct(g, {"mode": "per_province"})
    refresh(g, erased(g, r1=(CHAOS, 1), r2=(CHAOS, 2), r3=(MORS, 3)))
    assert calls(g, "apply_custom")[0][3] == "wh3_main_effect_corruption_chaos_events_bad"
    assert calls(g, "apply_custom")[0][2] == "r3"
    g.CALLS = g.lua.table()
    refresh(g, erased(g, r1=(CHAOS, 1), r2=(MORS, 2)))
    assert calls(g, "apply_custom")[-1] == [
        "apply_custom", PROVINCE_KEY, "r2", "wh3_main_effect_corruption_skaven_events_bad", SCOPE, 30]
    g.CALLS = g.lua.table()
    refresh(g, erased(g, r1=(MORS, 1), r2=(CHAOS, 2)))
    assert calls(g, "apply_custom") == [["apply_custom", PROVINCE_KEY, "r2", CHAOS_EFFECT, SCOPE, 30]]


def test_vanilla_devastation_blocks_province(g):
    g.ACTIVE_AREAS["area_p1"] = True
    set_mct(g, {"mode": "per_province"})
    refresh(g, erased(g, r1=(CHAOS, 1), r2=(CHAOS, 2)))
    assert calls(g, "apply_custom") == []
    set_mct(g, {"mode": "per_settlement"})
    refresh(g, erased(g, r1=(CHAOS, 1), r2=(CHAOS, 2)))
    assert calls(g, "apply_custom")[-2:] == [
        ["apply_custom", RUIN_KEY, "r1", CHAOS_EFFECT, SCOPE, 5],
        ["apply_custom", RUIN_KEY, "r2", CHAOS_EFFECT, SCOPE, 5],
    ]


def test_own_scorched_earth_keeps_province_corruption(g):
    g.ACTIVE_AREAS["area_p1"] = True
    set_mct(g, {"mode": "per_province"})
    refresh(g, erased(g, r1=(CHAOS, 1), r2=(CHAOS, 2)), devastated={"p1": True})
    assert calls(g, "apply_custom") == [["apply_custom", PROVINCE_KEY, "r2", CHAOS_EFFECT, SCOPE, 30]]


def test_refresh_twice_no_duplicates(g):
    set_mct(g, {"mode": "per_settlement"})
    e = erased(g, r1=(EMPIRE, 1), r2=(EMPIRE, 2))
    refresh(g, e)
    refresh(g, e)
    assert len(calls(g, "remove_bundle")) == 2
    assert len(calls(g, "apply_custom")) == 4
    assert bundles(g) == {"r1": [RUIN_KEY], "r2": [RUIN_KEY]}


def test_mode_off_after_on_removes_bundles(g):
    set_mct(g, {"mode": "per_settlement"})
    e = erased(g, r1=(EMPIRE, 1))
    refresh(g, e)
    assert bundles(g) == {"r1": [RUIN_KEY]}
    set_mct(g, {"mode": "off"})
    refresh(g, e)
    assert bundles(g) == {}


def test_switch_mode_moves_bundles(g):
    e = erased(g, r1=(CHAOS, 1), r2=(CHAOS, 2))
    set_mct(g, {"mode": "per_settlement"})
    refresh(g, e)
    set_mct(g, {"mode": "per_province"})
    refresh(g, e)
    assert bundles(g) == {"r2": [PROVINCE_KEY]}


def test_missing_state_tables_are_empty(g):
    set_mct(g, {"mode": "per_province"})
    # state with only `erased`: no devastated_provinces, no daemon_gods
    refresh(g, erased(g, r1=(CHAOS, 1), r2=(CHAOS, 2)))
    assert calls(g, "apply_custom") == [["apply_custom", PROVINCE_KEY, "r2", CHAOS_EFFECT, SCOPE, 30]]
    # entirely empty state
    g.permraze_corruption.refresh(g.permraze_corruption, g.lua.table())
    assert len(calls(g, "apply_custom")) == 1
