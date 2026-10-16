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

cm = {}
function cm:get_region(key) return make_region(key) end
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
function cm:save_named_value(name, value, context) context[name] = value end
function cm:load_named_value(name, default, context)
	if context[name] == nil then return default end
	return context[name]
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
