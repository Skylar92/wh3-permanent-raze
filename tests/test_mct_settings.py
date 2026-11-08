from pathlib import Path

import pytest
from lupa.lua51 import LuaRuntime

from tools.corruption import (AI_CHANCE_DEFAULT, AI_CHANCE_PREFIX, AI_CHANCE_VALUES, CORRUPTION_TYPES, CULTURE_DEFAULTS,
                              EFFECT_VALUES, MCT_TEXTS, RU_PROBE, SETTINGS_DEFAULTS, SLIDERS, campaign_defaults)
from tools.render import render_mct_settings

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = (ROOT / "src/script/mct/settings/permraze.lua").read_text(encoding="utf-8")

# A fake MCT that records calls. PAGES = false mimics an old MCT without settings pages.
FAKE_MCT = """
LOG = { mods = {} }
LISTENERS = {}
SELECTED = {}
core = { add_listener = function(_, name, event, cond, cb, persist)
    LISTENERS[#LISTENERS + 1] = {name = name, event = event, cb = cb}
end }
local function recorder(rec, key)
    local self = { callbacks = {} }
    for _, name in ipairs({"set_text", "set_tooltip_text", "set_default_value", "add_dropdown_values",
                           "slider_set_min_max", "slider_set_step_size", "slider_set_precision"}) do
        self[name] = function(me, a, b)
            rec[name] = {a, b}
            return me
        end
    end
    self.set_locked = function(me, locked, reason)
        rec.locked = locked
        rec.lock_reason = reason
    end
    self.get_selected_setting = function(me)
        if SELECTED[key] ~= nil then return SELECTED[key] end
        return rec.set_default_value and rec.set_default_value[1]
    end
    self.add_option_set_callback = function(me, cb, is_context)
        rec.callback = cb
        rec.callback_is_context = is_context
    end
    return self
end
function get_mct()
    return { register_mod = function(_, key)
        local mod = { key = key, options = {}, order = {}, sections = {}, pages = {}, removed = {} }
        LOG.mods[key] = mod
        local current
        local objects = {}
        local m = {}
        for _, name in ipairs({"set_title", "set_author", "set_workshop_id", "set_description"}) do
            m[name] = function(me, v) mod[name] = v return me end
        end
        local function new_page(title)
            local page = { title = title, sections = {} }
            mod.pages[#mod.pages + 1] = page
            return page
        end
        if PAGES then
            mod.default = new_page("Settings")
            m.get_default_settings_page = function() return mod.default end
            m.create_settings_page = function(me, title, cols) return new_page(title) end
            m.set_default_settings_page = function(me, page) mod.default = page end
            m.remove_settings_page = function(me, page)
                for i, p in ipairs(mod.pages) do
                    if p == page then table.remove(mod.pages, i) end
                end
                mod.removed[#mod.removed + 1] = page.title
            end
        end
        m.add_new_section = function(me, skey, name)
            current = skey
            local rec = {key = skey, name = name}
            mod.sections[#mod.sections + 1] = rec
            local section = {}
            if PAGES then
                rec.page = mod.pages[1]
                section.assign_to_page = function(s, page) rec.page = page end
            end
            return section
        end
        m.add_new_option = function(me, okey, otype)
            local rec = {type = otype, section = current}
            mod.options[okey] = rec
            mod.order[#mod.order + 1] = okey
            objects[okey] = recorder(rec, okey)
            return objects[okey]
        end
        m.get_option_by_key = function(me, okey) return objects[okey] end
        return m
    end }
end
common = { get_localised_string = function(key) return LOC[key] or "" end }
"""

AI_CULTURE_KEYS = [AI_CHANCE_PREFIX + c for c in CULTURE_DEFAULTS]
CORRUPTION_CULTURE_KEYS = ["culture_" + c for c in CULTURE_DEFAULTS]
AI_LOCKED = ["ai_erase_chance"] + AI_CULTURE_KEYS
CORRUPTION_LOCKED = ["ruin_strength", "province_strength", "multiplier", "threshold",
                     "daemon_follow_god"] + CORRUPTION_CULTURE_KEYS


def load(russian=False, pages=True, selected=None):
    lua = LuaRuntime(unpack_returned_tuples=True)
    lua.execute(FAKE_MCT)
    g = lua.globals()
    g.PAGES = pages
    g.LOC = lua.table_from({RU_PROBE[0]: RU_PROBE[1]} if russian else {})
    for key, value in (selected or {}).items():
        g.SELECTED[key] = value
    lua.execute(render_mct_settings(TEMPLATE))
    return lua, g.LOG.mods["permraze"]


def py(table):
    return list(table.values()) if table is not None else None


def opt(mod, key):
    return mod.options[key]


def locked(mod):
    return {k for k in mod.order.values() if opt(mod, k).locked}


def fire_option(lua, mod, key, value):
    ctx = lua.eval("function(v) return { setting = function() return v end } end")(value)
    opt(mod, key).callback(ctx)


@pytest.fixture
def loaded():
    return load()


@pytest.fixture
def mod(loaded):
    return loaded[1]


def test_registers_permraze(mod):
    assert mod.key == "permraze"
    assert mod.set_author == "Skylar92"
    assert mod.set_workshop_id == "3820765666"
    assert mod.set_title == MCT_TEXTS["mod_title"][0]
    assert [s.key for s in py(mod.sections)] == ["general", "ai", "ai_cultures", "corruption", "cultures"]


def test_three_pages_replace_the_default_one(mod):
    titles = [p.title for p in py(mod.pages)]
    assert titles == [MCT_TEXTS[k][0] for k in ("page_general", "page_ai", "page_corruption")]
    assert py(mod.removed) == ["Settings"]
    assert mod.default.title == MCT_TEXTS["page_general"][0]


def test_sections_on_their_pages(mod):
    page_of = {s.key: s.page.title for s in py(mod.sections)}
    general, ai, corruption = (MCT_TEXTS[k][0] for k in ("page_general", "page_ai", "page_corruption"))
    assert page_of == {"general": general, "ai": ai, "ai_cultures": ai, "corruption": corruption,
                       "cultures": corruption}


def test_options_in_their_sections(mod):
    section = {k: opt(mod, k).section for k in mod.order.values()}
    assert section["allow_rebuild"] == "general"
    assert section["ai_erase"] == section["ai_erase_chance"] == "ai"
    order = list(mod.order.values())
    assert order[:3] == ["allow_rebuild", "ai_erase", "ai_erase_chance"]
    for key in ["mode", "ruin_strength", "province_strength", "multiplier", "threshold", "daemon_follow_god"]:
        assert section[key] == "corruption", key
    for key in AI_CULTURE_KEYS:
        assert section[key] == "ai_cultures"
    for key in CORRUPTION_CULTURE_KEYS:
        assert section[key] == "cultures"


def test_old_mct_without_pages_still_registers_everything():
    _, mod = load(pages=False)
    assert [s.key for s in py(mod.sections)] == ["general", "ai", "ai_cultures", "corruption", "cultures"]
    assert set(mod.order.values()) == set(campaign_defaults())


def test_general_options_match_defaults(mod):
    types = {"mode": "dropdown", "daemon_follow_god": "checkbox", "allow_rebuild": "checkbox", "ai_erase": "checkbox"}
    for key, default in SETTINGS_DEFAULTS.items():
        o = opt(mod, key)
        assert o.type == types.get(key, "slider"), key
        assert o.set_default_value[1] == default, key
        assert o.set_text[1] == MCT_TEXTS[key + "_label"][0], key
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
    assert cultures == CORRUPTION_CULTURE_KEYS


def test_ai_culture_dropdowns(mod):
    for culture in CULTURE_DEFAULTS:
        o = opt(mod, AI_CHANCE_PREFIX + culture)
        assert o.type == "dropdown"
        assert o.set_text[1] == "cultures_name_" + culture
        assert o.set_tooltip_text[1] == MCT_TEXTS["ai_culture_tip"][0]
        values = [(v.key, v.text) for v in py(o.add_dropdown_values[1])]
        assert values[0] == ("general", MCT_TEXTS["ai_culture_general"][0])
        assert values[1:] == [(str(p), "%d%%" % p) for p in range(0, 101, 5)]
        assert [k for k, _ in values] == list(AI_CHANCE_VALUES)
        assert o.set_default_value[1] == AI_CHANCE_DEFAULT == "general"
    assert [k for k in mod.order.values() if k.startswith(AI_CHANCE_PREFIX)] == AI_CULTURE_KEYS


def test_ai_culture_dropdown_russian():
    _, mod = load(russian=True)
    values = py(opt(mod, AI_CHANCE_PREFIX + "wh_main_emp_empire").add_dropdown_values[1])
    assert values[0].text == "Общий"


def test_texts_english_by_default(mod):
    assert mod.set_title == MCT_TEXTS["mod_title"][0]
    assert opt(mod, "mode").set_text[1] == MCT_TEXTS["mode_label"][0]
    assert opt(mod, "mode").set_tooltip_text[1] == MCT_TEXTS["mode_tip"][0]
    assert mod.sections[5].name == MCT_TEXTS["section_cultures"][0]


def test_texts_russian_when_probe_matches():
    _, mod = load(russian=True)
    assert mod.set_title == MCT_TEXTS["mod_title"][1]
    assert opt(mod, "mode").set_text[1] == MCT_TEXTS["mode_label"][1]
    assert opt(mod, "multiplier").set_tooltip_text[1] == MCT_TEXTS["multiplier_tip"][1]
    assert mod.sections[1].name == MCT_TEXTS["section_general"][1]
    assert mod.pages[2].title == MCT_TEXTS["page_ai"][1]
    assert py(opt(mod, "mode").add_dropdown_values[1])[0].text == MCT_TEXTS["mode_off"][1]
    assert opt(mod, "ai_erase_chance").lock_reason == MCT_TEXTS["lock_ai_off"][1]


def test_campaign_defaults_equal_mct_defaults(mod):
    found = {k: mod.options[k].set_default_value[1] for k in mod.order.values()}
    assert found == campaign_defaults()


def test_does_nothing_without_mct():
    lua = LuaRuntime(unpack_returned_tuples=True)
    lua.execute(render_mct_settings(TEMPLATE))


def test_ai_erase_tip_warns_about_chaos(mod):
    assert opt(mod, "ai_erase").set_tooltip_text[1] == MCT_TEXTS["ai_erase_tip"][0]
    assert "chaos" in MCT_TEXTS["ai_erase_tip"][0].lower() and "хаос" in MCT_TEXTS["ai_erase_tip"][1].lower()


# Locks

def test_defaults_lock_ai_and_corruption_pages(mod):
    assert locked(mod) == set(AI_LOCKED) | set(CORRUPTION_LOCKED)
    assert opt(mod, "ai_erase_chance").lock_reason == MCT_TEXTS["lock_ai_off"][0]
    assert opt(mod, "multiplier").lock_reason == MCT_TEXTS["lock_mode_off"][0]


def test_switches_are_never_locked(mod):
    for key in ("allow_rebuild", "ai_erase", "mode"):
        assert not opt(mod, key).locked


def test_saved_settings_unlock_on_load():
    _, mod = load(selected={"ai_erase": True, "mode": "per_province"})
    assert locked(mod) == {"ruin_strength"}


def test_ticking_ai_erase_unlocks_the_ai_page(loaded):
    lua, mod = loaded
    assert opt(mod, "ai_erase").callback_is_context is True
    fire_option(lua, mod, "ai_erase", True)
    assert not locked(mod) & set(AI_LOCKED)
    fire_option(lua, mod, "ai_erase", False)
    assert set(AI_LOCKED) <= locked(mod)


@pytest.mark.parametrize("mode, still_locked", [
    ("per_settlement", {"province_strength", "threshold"}),
    ("per_province", {"ruin_strength"}),
    ("off", set(CORRUPTION_LOCKED)),
])
def test_mode_locks_what_it_does_not_use(loaded, mode, still_locked):
    lua, mod = loaded
    fire_option(lua, mod, "mode", "per_settlement" if mode == "off" else "off")
    fire_option(lua, mod, "mode", mode)
    assert locked(mod) & set(CORRUPTION_LOCKED) == still_locked
    for key in still_locked:
        assert opt(mod, key).lock_reason == MCT_TEXTS["lock_mode_" + mode][0]


def test_mode_does_not_touch_ai_locks(loaded):
    lua, mod = loaded
    fire_option(lua, mod, "mode", "per_settlement")
    assert set(AI_LOCKED) <= locked(mod)


def test_panel_opened_reapplies_locks(loaded):
    lua, mod = loaded
    (listener,) = [lst for lst in py(lua.globals().LISTENERS) if lst.event == "MctPanelOpened"]
    lua.globals().SELECTED["ai_erase"] = True
    listener.cb(None)
    assert not locked(mod) & set(AI_LOCKED)
