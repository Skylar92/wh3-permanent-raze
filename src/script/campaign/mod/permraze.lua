------------------------------------------------------------------------------
--
--	Permanent Raze ("Стереть навсегда")
--
--	Adds a "raze forever" occupation option for every culture. When a human
--	player picks it, the ruins are blocked for everyone the same way Archaon's
--	Lord of the End Times path does it, and once more than half of a province
--	is in ruins the province gets the campaign devastation visuals, but only
--	for cultures that have a devastation look (Chaos, Beastmen, Norsca,
--	Daemons, Chaos Dwarfs, Skaven, Vampires, Vampire Coast). No climate change,
--	no bonuses, and corruption only when enabled in MCT (see
--	permraze_corruption.lua; off by default).
--
------------------------------------------------------------------------------

-- Filled in by tools/build.py: our occupation option ids, and for each culture
-- that scorches the land the culture whose devastation look it uses.
local OPTION_IDS = {} --@@OPTION_IDS@@
local LOOK_CULTURES = {} --@@LOOK_CULTURES@@

local BUNDLE_KEY = "permraze_block_occupation"
local SETTLEMENT_TYPE = "wh3_dlc29_devastated"
local SETTLEMENT_STATE = "devastated"
local SAVE_KEY = "permraze"
local ASCEND_PREFIX = "wh3_main_ritual_dae_ascend_"

local function new_state()
	return {
		pending = {},              -- [region_key] = faction_key: our option chosen, raze not seen yet
		razed = {},                -- [region_key] = faction_key: human raze seen, decision not seen yet
		erased = {},               -- [region_key] = {faction = faction_key, order = n}; order 0 = erased before we tracked it
		devastated_provinces = {}, -- [province_key] = true
		daemon_gods = {},          -- [faction_key] = god suffix of the last wh3_main_ritual_dae_ascend_<god>
	}
end

permraze = {
	persistent = new_state(),
}

-- Both events happen in the same occupation, in an order we do not rely on.
function permraze:on_decision(option_id, is_human, region_key, faction_key)
	if not OPTION_IDS[option_id] or not is_human then
		return
	end

	if self.persistent.razed[region_key] then
		self.persistent.razed[region_key] = nil
		self:erase_region(region_key, faction_key)
	else
		self.persistent.pending[region_key] = faction_key
	end
end

function permraze:on_razed(region_key, faction_key)
	local pending_faction = self.persistent.pending[region_key]
	if pending_faction then
		self.persistent.pending[region_key] = nil
		self:erase_region(region_key, pending_faction)
	else
		self.persistent.razed[region_key] = faction_key
	end
end

function permraze:clear_turn_state()
	self.persistent.pending = {}
	self.persistent.razed = {}
end

function permraze:erase_region(region_key, faction_key)
	self:erase_and_devastate(region_key, faction_key)
	-- Last, on every path: it reads devastated_provinces that the step above may update.
	self:refresh_corruption()
end

function permraze:next_erase_order()
	local max_order = 0
	for _, entry in pairs(self.persistent.erased) do
		if type(entry) == "table" and type(entry.order) == "number" and entry.order > max_order then
			max_order = entry.order
		end
	end
	return max_order + 1
end

function permraze:erase_and_devastate(region_key, faction_key)
	local settlement = cm:get_region(region_key):settlement()

	cm:cai_disable_targeting_against_settlement("settlement:" .. region_key)
	cm:apply_effect_bundle_to_region(BUNDLE_KEY, region_key, 0)
	cm:reset_settlement_type(settlement, SETTLEMENT_TYPE, 1)
	cm:set_settlement_devastated_state(settlement, SETTLEMENT_STATE)

	self.persistent.erased[region_key] = { faction = faction_key, order = self:next_erase_order() }
	out("Permanent Raze: erased " .. region_key)

	local faction = cm:get_faction(faction_key)
	if not faction or faction:is_null_interface() then
		return
	end

	-- On Archaon's Destroyer path his own script devastates the province and counts it
	-- toward his bonuses and long victory; doing it first would make him skip it.
	if self:archaon_devastates_for(faction) then
		return
	end

	self:maybe_devastate_province(region_key, faction:culture())
end

-- Saves from before we tracked who erased what hold `true`. With a single human
-- player it was certainly them; otherwise the culture is unknown.
function permraze:migrate_erased()
	local humans = cm:get_human_factions()
	local faction_key = #humans == 1 and humans[1] or nil
	for region_key, entry in pairs(self.persistent.erased) do
		if type(entry) ~= "table" then
			self.persistent.erased[region_key] = { faction = faction_key, order = 0 }
		end
	end
end

function permraze:refresh_corruption()
	local ok, err = pcall(function()
		if type(permraze_corruption) == "table" then
			permraze_corruption:refresh(self.persistent)
		end
	end)
	if not ok then
		out("Permanent Raze: corruption refresh failed: " .. tostring(err))
	end
end

function permraze:archaon_devastates_for(faction)
	if type(archaon_narrative) ~= "table" or type(archaon_narrative.persistent) ~= "table" then
		return false
	end
	local destroyer_key = archaon_narrative.config.mission_data.long_victory_mission.main_objective_options.option_2.key
	if archaon_narrative.persistent.long_victory_condition_chosen_option_key ~= destroyer_key then
		return false
	end
	return archaon_narrative:is_archaon_or_archaon_vassal(faction)
end

function permraze:maybe_devastate_province(region_key, culture_key)
	local region = cm:get_region(region_key)
	local province = region:province()
	local province_key = province:key()

	local look = self:look_for(culture_key)
	if self.persistent.devastated_provinces[province_key] or not look then
		return false
	end

	local event_area_key = region:event_area_name()
	if not event_area_key or event_area_key == "" then
		return false
	end

	-- Endgames, Archaon or Nagash may already have devastated this area.
	if cm:is_campaign_map_event_area_activated_in_region(province:capital_region():name()) then
		return false
	end

	local regions = province:regions()
	local total = regions:num_items()
	local abandoned = 0
	for i = 0, total - 1 do
		if regions:item_at(i):is_abandoned() then
			abandoned = abandoned + 1
		end
	end

	if abandoned < math.floor(total / 2) + 1 then
		return false
	end

	cm:activate_campaign_map_event_area(event_area_key, look)
	self.persistent.devastated_provinces[province_key] = true
	out("Permanent Raze: devastated province " .. province_key)
	return true
end

-- Only cultures with a devastation look scorch the land; Bretonnia razing a
-- province should not turn it into a Chaos wasteland. Returns nil for them.
function permraze:look_for(culture_key)
	return LOOK_CULTURES[culture_key]
end

function permraze:init()
	core:add_listener(
		"permraze_occupation_decision",
		"CharacterPerformsSettlementOccupationDecision",
		true,
		function(context)
			local faction = context:character():faction()
			self:on_decision(
				tostring(context:occupation_decision()),
				faction:is_human(),
				context:garrison_residence():region():name(),
				faction:name()
			)
		end,
		true
	)

	core:add_listener(
		"permraze_settlement_razed",
		"CharacterRazedSettlement",
		function(context)
			return context:character():faction():is_human()
		end,
		function(context)
			self:on_razed(
				context:garrison_residence():region():name(),
				context:character():faction():name()
			)
		end,
		true
	)

	core:add_listener(
		"permraze_round_start",
		"WorldStartRound",
		true,
		function()
			self:clear_turn_state()
		end,
		true
	)

	core:add_listener(
		"permraze_mct_finalized",
		"MctFinalized",
		true,
		function()
			self:refresh_corruption()
		end,
		true
	)

	core:add_listener(
		"permraze_daemon_ascend",
		"RitualCompletedEvent",
		function(context)
			return context:ritual():ritual_key():sub(1, #ASCEND_PREFIX) == ASCEND_PREFIX
				and context:performing_faction():is_human()
		end,
		function(context)
			local key = context:ritual():ritual_key()
			self.persistent.daemon_gods[context:performing_faction():name()] = key:sub(#ASCEND_PREFIX + 1)
			self:refresh_corruption()
		end,
		true
	)

	-- Last on purpose: nothing in here may stop the listeners above from registering.
	self:migrate_erased()
	self:refresh_corruption()
end

cm:add_first_tick_callback(
	function()
		permraze:init()
	end
)

--------------------------------------------------------------
----------------------- SAVING / LOADING ---------------------
--------------------------------------------------------------
cm:add_saving_game_callback(
	function(context)
		cm:save_named_value(SAVE_KEY, permraze.persistent, context)
	end
)

cm:add_loading_game_callback(
	function(context)
		local loaded = cm:load_named_value(SAVE_KEY, new_state(), context)
		local state = new_state()
		if type(loaded) == "table" then
			for key, value in pairs(state) do
				if type(loaded[key]) == "table" then
					state[key] = loaded[key]
				end
			end
		end
		permraze.persistent = state
	end
)
