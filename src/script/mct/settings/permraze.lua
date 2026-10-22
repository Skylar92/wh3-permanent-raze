-- MCT settings page for Raze Forever. The placeholders are filled in by tools/render.py at build time.
if not get_mct then return end

local DEFAULTS = {} --@@DEFAULTS@@
local SLIDERS = {} --@@SLIDERS@@
local CULTURES = {} --@@CULTURES@@
local CULTURE_DEFAULTS = {} --@@CULTURE_DEFAULTS@@
local EFFECT_VALUES = {} --@@EFFECT_VALUES@@
local TYPE_NAME_KEYS = {} --@@TYPE_NAME_KEYS@@
local UNTAINTED_KEY = {} --@@UNTAINTED_KEY@@
local TEXTS = {} --@@TEXTS@@
local RU_PROBE = {} --@@RU_PROBE@@

local ru = common.get_localised_string(RU_PROBE[1]) == RU_PROBE[2]

local function T(key)
    local t = TEXTS[key]
    return ru and t[2] or t[1]
end

local mct = get_mct()
local mod = mct:register_mod("permraze")
mod:set_title(T("mod_title"))
mod:set_author("Skylar92")
mod:set_workshop_id("3820765666")
mod:set_description(T("mod_description"))

mod:add_new_section("general", T("section_general"))

local function add_option(key, kind)
    local opt = mod:add_new_option(key, kind)
    opt:set_text(T(key .. "_label"))
    opt:set_tooltip_text(T(key .. "_tip"))
    return opt
end

local mode = add_option("mode", "dropdown")
mode:add_dropdown_values({
    {key = "off", text = T("mode_off")},
    {key = "per_settlement", text = T("mode_per_settlement")},
    {key = "per_province", text = T("mode_per_province")},
})
mode:set_default_value(DEFAULTS.mode)

for _, key in ipairs({"ruin_strength", "province_strength", "multiplier", "threshold"}) do
    local opt = add_option(key, "slider")
    local range = SLIDERS[key]
    opt:slider_set_min_max(range[1], range[2])
    opt:slider_set_step_size(range[3])
    opt:slider_set_precision(0)
    opt:set_default_value(DEFAULTS[key])
end

local follow = add_option("daemon_follow_god", "checkbox")
follow:set_default_value(DEFAULTS.daemon_follow_god)

mod:add_new_section("cultures", T("section_cultures"))

local function effect_text(value)
    if value == "none" then return T("value_none") end
    if value == "reduce" then return UNTAINTED_KEY end
    return TYPE_NAME_KEYS[value]
end

local values = {}
for i, value in ipairs(EFFECT_VALUES) do
    values[i] = {key = value, text = effect_text(value)}
end

for _, culture in ipairs(CULTURES) do
    local opt = mod:add_new_option("culture_" .. culture, "dropdown")
    opt:set_text("cultures_name_" .. culture)
    opt:add_dropdown_values(values)
    opt:set_default_value(CULTURE_DEFAULTS[culture])
end
