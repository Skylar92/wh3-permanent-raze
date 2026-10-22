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
