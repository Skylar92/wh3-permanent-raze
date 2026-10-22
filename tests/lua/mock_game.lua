-- Minimal stand-ins for the campaign API used by permraze.lua.
-- Every cm call that changes the game is recorded in CALLS as {name, args...}.
CALLS = {}
LISTENERS = {}
FIRST_TICK = {}
SAVE_CALLBACKS = {}
LOAD_CALLBACKS = {}
ABANDONED = {}
ACTIVE_AREAS = {}

local function rec(...) CALLS[#CALLS + 1] = {...} end

local PROVINCE_REGIONS = { p1 = {"r1", "r2", "r3"}, p9 = {"r9"} }
local REGION_PROVINCE = { r1 = "p1", r2 = "p1", r3 = "p1", r9 = "p9" }
local REGION_AREA = { r1 = "area_p1", r2 = "area_p1", r3 = "area_p1", r9 = "" }

local function list(items)
	return {
		num_items = function() return #items end,
		item_at = function(_, i) return items[i + 1] end,
	}
end

local make_region

local function make_province(key)
	return {
		key = function() return key end,
		regions = function()
			local items = {}
			for _, rk in ipairs(PROVINCE_REGIONS[key]) do items[#items + 1] = make_region(rk) end
			return list(items)
		end,
		capital_region = function() return make_region(PROVINCE_REGIONS[key][1]) end,
	}
end

make_region = function(key)
	return {
		name = function() return key end,
		is_abandoned = function() return ABANDONED[key] == true end,
		settlement = function() return { region_key = key } end,
		province = function() return make_province(REGION_PROVINCE[key]) end,
		event_area_name = function() return REGION_AREA[key] end,
	}
end

local FACTIONS = {
	wh_main_emp_empire = { culture = "wh_main_emp_empire" },
	wh2_main_skv_clan_mors = { culture = "wh2_main_skv_skaven" },
	wh_main_chs_chaos = { culture = "wh_main_chs_chaos" },
	wh_dlc03_bst_beastmen = { culture = "wh_dlc03_bst_beastmen" },
	wh_main_vmp_vampire_counts = { culture = "wh_main_vmp_vampire_counts" },
	wh2_dlc11_cst_pirates = { culture = "wh2_dlc11_cst_vampire_coast" },
	wh3_main_kho_vassal = { culture = "wh3_main_kho_khorne", master = "wh_main_chs_chaos" },
	wh2_main_def_cult_of_pleasure = { culture = "wh2_main_def_dark_elves" },
	wh3_dlc29_chs_host_of_the_triplets = { culture = "wh_main_chs_chaos" },
	wh3_main_dae_daemon_prince = { culture = "wh3_main_dae_daemons" },
	wh2_main_def_naggarond = { culture = "wh2_main_def_dark_elves" },
	wh3_main_dae_daemons = { culture = "wh3_main_dae_daemons" },
}

local function null_interface() return { is_null_interface = function() return true end } end

function make_faction(key)
	local data = FACTIONS[key]
	if not data then return false end
	return {
		name = function() return key end,
		culture = function() return data.culture end,
		is_null_interface = function() return false end,
		master = function()
			if data.master then return make_faction(data.master) end
			return null_interface()
		end,
	}
end

SAVED_VALUES = {}

cm = {}
function cm:get_saved_value(k) return SAVED_VALUES[k] end
function cm:get_region(key) return make_region(key) end
function cm:get_faction(key) return make_faction(key) end
function cm:cai_disable_targeting_against_settlement(s) rec("cai_disable_targeting_against_settlement", s) end
function cm:apply_effect_bundle_to_region(b, r, t) rec("apply_effect_bundle_to_region", b, r, t) end
function cm:reset_settlement_type(s, t, l) rec("reset_settlement_type", s.region_key, t, l) end
function cm:set_settlement_devastated_state(s, st) rec("set_settlement_devastated_state", s.region_key, st) end
function cm:is_campaign_map_event_area_activated_in_region(rk) return ACTIVE_AREAS[REGION_AREA[rk]] == true end
function cm:activate_campaign_map_event_area(a, c) rec("activate_campaign_map_event_area", a, c); ACTIVE_AREAS[a] = true end
function cm:kill_character(...) rec("kill_character") end
function cm:override_settlement_climate(...) rec("override_settlement_climate") end
function cm:add_first_tick_callback(f) FIRST_TICK[#FIRST_TICK + 1] = f end
function cm:add_saving_game_callback(f) SAVE_CALLBACKS[#SAVE_CALLBACKS + 1] = f end
function cm:add_loading_game_callback(f) LOAD_CALLBACKS[#LOAD_CALLBACKS + 1] = f end
-- Mirrors lib_campaign_manager: tables are serialised (stored as copies here) and
-- only come back when the default is a table; a nil default without allow_nil
-- is an error that returns false.
local function deep_copy(v)
	if type(v) ~= "table" then return v end
	local t = {}
	for k, x in pairs(v) do t[k] = deep_copy(x) end
	return t
end
function cm:save_named_value(name, value, context) context[name] = deep_copy(value) end
function cm:load_named_value(name, default, context, allow_nil)
	local stored = context[name]
	if type(default) == "table" then
		if type(stored) == "table" then return deep_copy(stored) end
		return default
	end
	if default == nil and not allow_nil then
		rec("script_error", "load_named_value without default")
		return false
	end
	if stored == nil then return default end
	return stored
end

climate_change = { add_climate_override = function() rec("add_climate_override") end }

core = {}
function core:add_listener(name, event, condition, callback, persistent)
	LISTENERS[#LISTENERS + 1] = { name = name, event = event, condition = condition, callback = callback }
end

function fire(event, context)
	for _, l in ipairs(LISTENERS) do
		if l.event == event and (l.condition == true or l.condition(context)) then l.callback(context) end
	end
end

function out() end
