------------------------------------------------------------------------------
--
--	Permanent Raze: corruption of erased ruins
--
--	Reads the Mod Configuration Tool settings and decides which corruption
--	effect an erased ruin gives to its province, depending on the culture of
--	the faction that erased it. Without MCT (or with its defaults) the mode is
--	"off" and nothing changes.
--
------------------------------------------------------------------------------

-- Filled in by tools/render.py from tools/corruption.py.
local DEFAULTS = {} --@@DEFAULTS@@
local FACTION_OVERRIDES = {} --@@FACTION_OVERRIDES@@
local DAEMONS_CULTURE = {} --@@DAEMONS_CULTURE@@
local DAEMON_PRINCE_FACTION = {} --@@DAEMON_PRINCE_FACTION@@
local RUIN_BUNDLE = {} --@@RUIN_BUNDLE@@
local PROVINCE_BUNDLE = {} --@@PROVINCE_BUNDLE@@
local EFFECT_SCOPE = {} --@@EFFECT_SCOPE@@
local EFFECT_KEYS = {} --@@EFFECT_KEYS@@

local MOD_KEY = "permraze"
local ASCEND_PREFIX = "wh3_main_ritual_dae_ascend_"
local ASCEND_SAVED_KEY = "IEVictoryConditionRewardsDaemonPrinceAscendancyPath"
local GODS = { khorne = true, nurgle = true, slaanesh = true, tzeentch = true }

permraze_corruption = {}

-- "wh3_main_ritual_dae_ascend_nurgle" or "nurgle" -> "nurgle"; everything else -> "chaos".
local function god_effect(name)
	if type(name) ~= "string" then
		return "chaos"
	end
	if name:sub(1, #ASCEND_PREFIX) == ASCEND_PREFIX then
		name = name:sub(#ASCEND_PREFIX + 1)
	end
	if GODS[name] then
		return name
	end
	return "chaos"
end

local function read_mct(result)
	local mod = get_mct():get_mod_by_key(MOD_KEY)
	if not mod then
		return
	end
	for key, default in pairs(DEFAULTS) do
		local option = mod:get_option_by_key(key)
		if option then
			local value = option:get_finalized_setting()
			if type(value) == type(default) then
				result[key] = value
			end
		end
	end
end

function permraze_corruption:settings()
	local result = {}
	for key, default in pairs(DEFAULTS) do
		result[key] = default
	end
	if type(get_mct) == "function" then
		pcall(read_mct, result)
	end
	return result
end

function permraze_corruption:effect_for(faction_key, settings, daemon_gods)
	if not faction_key then
		return "none"
	end
	if FACTION_OVERRIDES[faction_key] then
		return FACTION_OVERRIDES[faction_key]
	end

	local faction = cm:get_faction(faction_key)
	if not faction or faction:is_null_interface() then
		return "none"
	end
	local culture = faction:culture()

	if culture == DAEMONS_CULTURE and settings.daemon_follow_god then
		local god = daemon_gods and daemon_gods[faction_key]
		if not god and faction_key == DAEMON_PRINCE_FACTION then
			god = cm:get_saved_value(ASCEND_SAVED_KEY)
		end
		return god_effect(god or "chaos")
	end

	return settings["culture_" .. culture] or "none"
end

local function sorted_keys(t)
	local keys = {}
	for key in pairs(t) do
		keys[#keys + 1] = key
	end
	table.sort(keys)
	return keys
end

-- Signed effect value for a corruption type, or nil when nothing should be applied.
local function signed_value(effect, strength, settings)
	local value = strength * settings.multiplier / 100
	if effect == "none" or not EFFECT_KEYS[effect] or value <= 0 then
		return nil
	end
	if effect == "reduce" then
		return -value
	end
	return value
end

local function apply_bundle(bundle_key, region_key, effect, value)
	local bundle = cm:create_new_custom_effect_bundle(bundle_key)
	bundle:add_effect(EFFECT_KEYS[effect], EFFECT_SCOPE, value)
	bundle:set_duration(0)
	cm:apply_custom_effect_bundle_to_region(bundle, cm:get_region(region_key))
end

-- Picks the faction with the most erased ruins in the province; ties go to the latest erasure.
local function province_faction(entries)
	local counts, last_order = {}, {}
	for _, entry in ipairs(entries) do
		local faction = entry.data.faction
		if faction then
			counts[faction] = (counts[faction] or 0) + 1
			if entry.data.order > (last_order[faction] or -1) then
				last_order[faction] = entry.data.order
			end
		end
	end
	local best
	for _, faction in ipairs(sorted_keys(counts)) do
		if not best or counts[faction] > counts[best]
			or (counts[faction] == counts[best] and last_order[faction] > last_order[best]) then
			best = faction
		end
	end
	return best
end

-- Rebuilds the corruption bundles of every permanently erased ruin from `state`
-- (permraze.persistent): erased, devastated_provinces, daemon_gods.
function permraze_corruption:refresh(state)
	local erased = state.erased or {}
	local devastated = state.devastated_provinces or {}
	local daemon_gods = state.daemon_gods or {}
	local settings = self:settings()
	local regions = sorted_keys(erased)

	for _, region_key in ipairs(regions) do
		local region = cm:get_region(region_key)
		for _, bundle_key in ipairs({ RUIN_BUNDLE, PROVINCE_BUNDLE }) do
			if region:has_effect_bundle(bundle_key) then
				cm:remove_effect_bundle_from_region(bundle_key, region_key)
			end
		end
	end

	if settings.mode == "per_settlement" then
		for _, region_key in ipairs(regions) do
			local effect = self:effect_for(erased[region_key].faction, settings, daemon_gods)
			local value = signed_value(effect, settings.ruin_strength, settings)
			if value then
				apply_bundle(RUIN_BUNDLE, region_key, effect, value)
			end
		end
	elseif settings.mode == "per_province" then
		local provinces, province_keys = {}, {}
		for _, region_key in ipairs(regions) do
			local province = cm:get_region(region_key):province()
			local key = province:key()
			if not provinces[key] then
				provinces[key] = { province = province, entries = {} }
				province_keys[#province_keys + 1] = key
			end
			local entries = provinces[key].entries
			entries[#entries + 1] = { region = region_key, data = erased[region_key] }
		end
		table.sort(province_keys)

		for _, key in ipairs(province_keys) do
			local province = provinces[key].province
			local entries = provinces[key].entries
			local total = province:regions():num_items()
			local capital = province:capital_region():name()
			local vanilla_devastated = cm:is_campaign_map_event_area_activated_in_region(capital) and not devastated[key]

			if #entries * 100 > settings.threshold * total and not vanilla_devastated then
				local effect = self:effect_for(province_faction(entries), settings, daemon_gods)
				local value = signed_value(effect, settings.province_strength, settings)
				if value then
					local target = entries[1]
					for _, entry in ipairs(entries) do
						if entry.data.order > target.data.order then
							target = entry
						end
					end
					apply_bundle(PROVINCE_BUNDLE, target.region, effect, value)
				end
			end
		end
	end
end
