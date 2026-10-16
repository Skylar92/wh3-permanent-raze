------------------------------------------------------------------------------
--
--	Permanent Raze ("Стереть навсегда")
--
--	Adds a "raze forever" occupation option for every culture. When a human
--	player picks it, the ruins are blocked for everyone the same way Archaon's
--	Lord of the End Times path does it, and once more than half of a province
--	is in ruins the province gets the campaign devastation visuals (no
--	corruption, no climate change, no bonuses).
--
------------------------------------------------------------------------------

-- Filled in by tools/build.py: our occupation option ids and the cultures
-- that have their own devastation look.
local OPTION_IDS = {} --@@OPTION_IDS@@
local LOOK_CULTURES = {} --@@LOOK_CULTURES@@

local BUNDLE_KEY = "permraze_block_occupation"
local SETTLEMENT_TYPE = "wh3_dlc29_devastated"
local SETTLEMENT_STATE = "devastated"
local FALLBACK_LOOK_CULTURE = "wh_main_chs_chaos"
local SAVE_KEY = "permraze"

local function new_state()
	return {
		pending = {},              -- [region_key] = culture_key: our option chosen, raze not seen yet
		razed = {},                -- [region_key] = culture_key: human raze seen, decision not seen yet
		erased = {},               -- [region_key] = true
		devastated_provinces = {}, -- [province_key] = true
	}
end

permraze = {
	persistent = new_state(),
}

-- Both events happen in the same occupation, in an order we do not rely on.
function permraze:on_decision(option_id, is_human, region_key, culture_key)
	if not OPTION_IDS[option_id] or not is_human then
		return
	end

	if self.persistent.razed[region_key] then
		self.persistent.razed[region_key] = nil
		self:erase_region(region_key, culture_key)
	else
		self.persistent.pending[region_key] = culture_key
	end
end

function permraze:on_razed(region_key, culture_key)
	local pending_culture = self.persistent.pending[region_key]
	if pending_culture then
		self.persistent.pending[region_key] = nil
		self:erase_region(region_key, pending_culture)
	else
		self.persistent.razed[region_key] = culture_key
	end
end

function permraze:clear_turn_state()
	self.persistent.pending = {}
	self.persistent.razed = {}
end

function permraze:erase_region(region_key, culture_key)
	local settlement = cm:get_region(region_key):settlement()

	cm:cai_disable_targeting_against_settlement("settlement:" .. region_key)
	cm:apply_effect_bundle_to_region(BUNDLE_KEY, region_key, 0)
	cm:reset_settlement_type(settlement, SETTLEMENT_TYPE, 1)
	cm:set_settlement_devastated_state(settlement, SETTLEMENT_STATE)

	self.persistent.erased[region_key] = true
	out("Permanent Raze: erased " .. region_key)

	self:maybe_devastate_province(region_key, culture_key)
end

function permraze:maybe_devastate_province(region_key, culture_key)
	local region = cm:get_region(region_key)
	local province = region:province()
	local province_key = province:key()

	if self.persistent.devastated_provinces[province_key] then
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

	cm:activate_campaign_map_event_area(event_area_key, self:look_culture(culture_key))
	self.persistent.devastated_provinces[province_key] = true
	out("Permanent Raze: devastated province " .. province_key)
	return true
end

function permraze:look_culture(culture_key)
	if LOOK_CULTURES[culture_key] then
		return culture_key
	end
	return FALLBACK_LOOK_CULTURE
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
				faction:culture()
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
				context:character():faction():culture()
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
