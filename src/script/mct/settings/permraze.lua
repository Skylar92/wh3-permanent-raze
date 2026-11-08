-- MCT settings for Raze Forever. The placeholders are filled in by tools/render.py at build time.
-- Three pages: General (rebuild), AI erasing (switch, general and per-culture chance),
-- Corruption (mode and everything it uses). Options the current choices make pointless are locked.
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
local AI_CHANCE = {} --@@AI_CHANCE@@

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

-- Settings pages need a recent MCT; an older one keeps every section on its single page.
local pages = {}
local function make_pages()
    local old_default = mod:get_default_settings_page()
    pages.general = mod:create_settings_page(T("page_general"), 2)
    pages.ai = mod:create_settings_page(T("page_ai"), 2)
    pages.corruption = mod:create_settings_page(T("page_corruption"), 2)
    mod:set_default_settings_page(pages.general)
    if old_default then
        mod:remove_settings_page(old_default)
    end
end
if mod.create_settings_page and mod.set_default_settings_page and mod.remove_settings_page then
    if not pcall(make_pages) then
        pages = {}
    end
end

local function add_section(key, page)
    local section = mod:add_new_section(key, T("section_" .. key))
    if pages[page] and section and section.assign_to_page then
        section:assign_to_page(pages[page])
    end
end

local function add_option(key, kind, text_key)
    local opt = mod:add_new_option(key, kind)
    opt:set_text(T((text_key or key) .. "_label"))
    opt:set_tooltip_text(T((text_key or key) .. "_tip"))
    return opt
end

local function add_slider(key, range, default)
    local opt = mod:add_new_option(key, "slider")
    opt:slider_set_min_max(range[1], range[2])
    opt:slider_set_step_size(range[3])
    opt:slider_set_precision(0)
    opt:set_default_value(default)
    return opt
end

local function add_setting_slider(key)
    local opt = add_slider(key, SLIDERS[key], DEFAULTS[key])
    opt:set_text(T(key .. "_label"))
    opt:set_tooltip_text(T(key .. "_tip"))
    return opt
end

-- General page

add_section("general", "general")

local rebuild = add_option("allow_rebuild", "checkbox")
rebuild:set_default_value(DEFAULTS.allow_rebuild)

-- AI erasing page

add_section("ai", "ai")

local ai_erase = add_option("ai_erase", "checkbox")
ai_erase:set_default_value(DEFAULTS.ai_erase)

add_setting_slider("ai_erase_chance")

add_section("ai_cultures", "ai")

local ai_chance_values = {}
for i, value in ipairs(AI_CHANCE.values) do
    local text = value == AI_CHANCE.default and T("ai_culture_general") or (value .. "%")
    ai_chance_values[i] = {key = value, text = text}
end

local AI_KEYS = {"ai_erase_chance"}
for _, culture in ipairs(CULTURES) do
    local key = AI_CHANCE.prefix .. culture
    local opt = mod:add_new_option(key, "dropdown")
    opt:set_text("cultures_name_" .. culture)
    opt:set_tooltip_text(T("ai_culture_tip"))
    opt:add_dropdown_values(ai_chance_values)
    opt:set_default_value(AI_CHANCE.default)
    AI_KEYS[#AI_KEYS + 1] = key
end

-- Corruption page

add_section("corruption", "corruption")

local mode = add_option("mode", "dropdown")
mode:add_dropdown_values({
    {key = "off", text = T("mode_off")},
    {key = "per_settlement", text = T("mode_per_settlement")},
    {key = "per_province", text = T("mode_per_province")},
})
mode:set_default_value(DEFAULTS.mode)

for _, key in ipairs({"ruin_strength", "province_strength", "multiplier", "threshold"}) do
    add_setting_slider(key)
end

local follow = add_option("daemon_follow_god", "checkbox")
follow:set_default_value(DEFAULTS.daemon_follow_god)

add_section("cultures", "corruption")

local function effect_text(value)
    if value == "none" then return T("value_none") end
    if value == "reduce" then return UNTAINTED_KEY end
    return TYPE_NAME_KEYS[value]
end

local values = {}
for i, value in ipairs(EFFECT_VALUES) do
    values[i] = {key = value, text = effect_text(value)}
end

local CORRUPTION_KEYS = {"ruin_strength", "province_strength", "multiplier", "threshold", "daemon_follow_god"}
for _, culture in ipairs(CULTURES) do
    local opt = mod:add_new_option("culture_" .. culture, "dropdown")
    opt:set_text("cultures_name_" .. culture)
    opt:add_dropdown_values(values)
    opt:set_default_value(CULTURE_DEFAULTS[culture])
    CORRUPTION_KEYS[#CORRUPTION_KEYS + 1] = "culture_" .. culture
end

-- Locks: grey out what the AI switch and the corruption mode make pointless.

-- Options each mode leaves unused; "off" leaves all of them unused.
local UNUSED_IN_MODE = {
    per_settlement = {province_strength = true, threshold = true},
    per_province = {ruin_strength = true},
}

local function set_lock(key, locked, reason)
    local opt = mod:get_option_by_key(key)
    if opt and opt.set_locked then
        opt:set_locked(locked, locked and reason or nil)
    end
end

local function lock_ai(enabled)
    for _, key in ipairs(AI_KEYS) do
        set_lock(key, enabled ~= true, T("lock_ai_off"))
    end
end

local function lock_corruption(mode_value)
    local unused = UNUSED_IN_MODE[mode_value]
    for _, key in ipairs(CORRUPTION_KEYS) do
        if unused then
            set_lock(key, unused[key] == true, T("lock_mode_" .. mode_value))
        else
            set_lock(key, true, T("lock_mode_off"))
        end
    end
end

local function current(opt, fallback)
    local ok, value = pcall(function()
        return opt:get_selected_setting()
    end)
    if ok and value ~= nil then
        return value
    end
    return fallback
end

local function refresh_locks()
    pcall(lock_ai, current(ai_erase, DEFAULTS.ai_erase))
    pcall(lock_corruption, current(mode, DEFAULTS.mode))
end

if ai_erase.add_option_set_callback then
    ai_erase:add_option_set_callback(function(context)
        pcall(lock_ai, context:setting())
    end, true)
    mode:add_option_set_callback(function(context)
        pcall(lock_corruption, context:setting())
    end, true)
end

if core and core.add_listener then
    core:add_listener("permraze_mct_locks", "MctPanelOpened", true, refresh_locks, true)
end

refresh_locks()
