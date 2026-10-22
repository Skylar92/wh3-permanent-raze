from pathlib import Path

import pytest
from lupa.lua51 import LuaRuntime

from tools.corruption import (CORRUPTION_TYPES, CULTURE_DEFAULTS, EFFECT_VALUES, MCT_TEXTS, RU_PROBE, SETTINGS_DEFAULTS,
                              SLIDERS, campaign_defaults)
from tools.render import render_mct_settings

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = (ROOT / "src/script/mct/settings/permraze.lua").read_text(encoding="utf-8")

FAKE_MCT = """
LOG = { mods = {} }
local function recorder(rec)
    local self = {}
    for _, name in ipairs({"set_text", "set_tooltip_text", "set_default_value", "add_dropdown_values",
                           "slider_set_min_max", "slider_set_step_size", "slider_set_precision"}) do
        self[name] = function(me, a, b)
            rec[name] = {a, b}
            return me
        end
    end
    return self
end
function get_mct()
    return { register_mod = function(_, key)
        local mod = { key = key, options = {}, order = {}, sections = {} }
        LOG.mods[key] = mod
        local current
        local m = {}
        for _, name in ipairs({"set_title", "set_author", "set_workshop_id", "set_description"}) do
            m[name] = function(me, v) mod[name] = v return me end
        end
        m.add_new_section = function(me, skey, name)
            current = skey
            mod.sections[#mod.sections + 1] = {key = skey, name = name}
            return me
        end
        m.add_new_option = function(me, okey, otype)
            local rec = {type = otype, section = current}
            mod.options[okey] = rec
            mod.order[#mod.order + 1] = okey
            return recorder(rec)
        end
        return m
    end }
end
common = { get_localised_string = function(key) return LOC[key] or "" end }
"""


def load(russian=False):
    lua = LuaRuntime(unpack_returned_tuples=True)
    lua.execute(FAKE_MCT)
    g = lua.globals()
    g.LOC = lua.table_from({RU_PROBE[0]: RU_PROBE[1]} if russian else {})
    lua.execute(render_mct_settings(TEMPLATE))
    return lua, g.LOG.mods["permraze"]


def py(table):
    return list(table.values()) if table is not None else None


def opt(mod, key):
    return mod.options[key]


@pytest.fixture
def mod():
    return load()[1]


def test_registers_permraze(mod):
    assert mod.key == "permraze"
    assert mod.set_author == "Skylar92"
    assert mod.set_workshop_id == "3820765666"
    assert mod.set_title == MCT_TEXTS["mod_title"][0]
    assert [mod.sections[i].key for i in (1, 2)] == ["general", "cultures"]


def test_general_options_match_defaults(mod):
    types = {"mode": "dropdown", "daemon_follow_god": "checkbox"}
    for key, default in SETTINGS_DEFAULTS.items():
        o = opt(mod, key)
        assert o.type == types.get(key, "slider"), key
        assert o.set_default_value[1] == default, key
        assert o.section == "general"
        if key in SLIDERS:
            assert (o.slider_set_min_max[1], o.slider_set_min_max[2], o.slider_set_step_size[1]) == SLIDERS[key]
            assert o.slider_set_precision[1] == 0
    modes = [(v.key, v.text) for v in py(opt(mod, "mode").add_dropdown_values[1])]
    assert modes == [("off", MCT_TEXTS["mode_off"][0]), ("per_settlement", MCT_TEXTS["mode_per_settlement"][0]),
                     ("per_province", MCT_TEXTS["mode_per_province"][0])]


def test_culture_dropdowns(mod):
    for culture, default in CULTURE_DEFAULTS.items():
        o = opt(mod, "culture_" + culture)
        assert o.type == "dropdown"
        assert o.section == "cultures"
        assert o.set_text[1] == "cultures_name_" + culture
        values = py(o.add_dropdown_values[1])
        assert [v.key for v in values] == list(EFFECT_VALUES)
        assert len(values) == 9
        texts = {v.key: v.text for v in values}
        assert texts["none"] == MCT_TEXTS["value_none"][0]
        assert texts["reduce"] == "uied_component_texts_localised_string_region_corruption_untainted_Tooltip_40058"
        for t in CORRUPTION_TYPES:
            assert texts[t] == "pooled_resources_display_name_wh3_main_corruption_" + t
        assert o.set_default_value[1] == default
    cultures = [k for k in mod.order.values() if k.startswith("culture_")]
    assert cultures == ["culture_" + c for c in CULTURE_DEFAULTS]


def test_texts_english_by_default(mod):
    assert mod.set_title == MCT_TEXTS["mod_title"][0]
    assert opt(mod, "mode").set_text[1] == MCT_TEXTS["mode_label"][0]
    assert opt(mod, "mode").set_tooltip_text[1] == MCT_TEXTS["mode_tip"][0]
    assert mod.sections[2].name == MCT_TEXTS["section_cultures"][0]


def test_texts_russian_when_probe_matches():
    _, mod = load(russian=True)
    assert mod.set_title == MCT_TEXTS["mod_title"][1]
    assert opt(mod, "mode").set_text[1] == MCT_TEXTS["mode_label"][1]
    assert opt(mod, "multiplier").set_tooltip_text[1] == MCT_TEXTS["multiplier_tip"][1]
    assert mod.sections[1].name == MCT_TEXTS["section_general"][1]
    assert py(opt(mod, "mode").add_dropdown_values[1])[0].text == MCT_TEXTS["mode_off"][1]


def test_campaign_defaults_equal_mct_defaults(mod):
    found = {k: mod.options[k].set_default_value[1] for k in mod.order.values()}
    assert found == campaign_defaults()


def test_does_nothing_without_mct():
    lua = LuaRuntime(unpack_returned_tuples=True)
    lua.execute(render_mct_settings(TEMPLATE))
