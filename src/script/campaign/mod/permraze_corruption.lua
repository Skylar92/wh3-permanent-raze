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
			if not god then
				return "chaos"
			end
		end
		if god then
			return god_effect(god)
		end
	end

	return settings["culture_" .. culture] or "none"
end
