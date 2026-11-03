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
--	no bonuses of our own, and corruption only when enabled in MCT (see
--	permraze_corruption.lua; off by default). The button keeps the rewards
--	and costs of the culture's own raze; the few that vanilla scripts give
--	by option id are given here too (SCRIPTED_REWARDS).
--
--	Rebuilding (MCT option, off by default): during a human turn our block is
--	lifted only from ruins whose region, or a region next to it, holds a
--	human army, so the vanilla Colonise button works there
--	while every other erased ruin keeps its burning icon (the engine draws it
--	only when the viewing faction cannot occupy). It comes back when the army
--	leaves and on the first non-human turn. The AI only acts in its own turn,
--	so only players can rebuild. Ruins stay shut for the rest of the turn
--	they were erased in, or the army that erased them would reopen them.
--	A marker bundle keeps a burning icon next to the name of every erased
--	ruin, lifted or not.
--	A colonised ruin is no longer erased and loses its devastated look, and
--	the scorched land goes once no more than half the province is in ruins.
--	Only a human colonising a lifted ruin counts as rebuilding: vanilla
--	scripts (Khorne's spread to ruins and others) hand ruins over without an
--	army, past the block, and such ruins are abandoned and sealed again.
--
--	AI erasing (MCT option, off by default): the AI cannot pick our option
--	on purpose, so each AI raze erases the ruins by the chance set in MCT,
--	the same way a player's erase does. Corruption of these ruins is rebuilt
--	once at round start or on a human turn, not after every AI raze.
--
------------------------------------------------------------------------------

-- Filled in by tools/build.py: our occupation option ids, for each culture
-- that scorches the land the culture whose devastation look it uses, and for
-- each of our options the id of the vanilla raze it copies. FILE_LOG is true
-- only in a debug build (build.py --log).
local OPTION_IDS = {} --@@OPTION_IDS@@
local LOOK_CULTURES = {} --@@LOOK_CULTURES@@
local SOURCE_IDS = {} --@@SOURCE_IDS@@
local FILE_LOG = {} --@@FILE_LOG@@

local BUNDLE_KEY = "permraze_block_occupation"
local MARKER_KEY = "permraze_erased_marker"
local SETTLEMENT_TYPE = "wh3_dlc29_devastated"
local SETTLEMENT_STATE = "devastated"
local REBUILT_STATE = "none"
local SAVE_KEY = "permraze"
local ASCEND_PREFIX = "wh3_main_ritual_dae_ascend_"

local function new_state()
	return {
		pending = {},              -- [region_key] = faction_key: our option chosen, raze not seen yet
		razed = {},                -- [region_key] = faction_key: human raze seen, decision not seen yet
		erased = {},               -- [region_key] = {faction = faction_key, order = n, turn = n}; order 0 = erased before we tracked it
		devastated_provinces = {}, -- [province_key] = true
		daemon_gods = {},          -- [faction_key] = god suffix of the last wh3_main_ritual_dae_ascend_<god>
		lifted = {},               -- [region_key] = true: block taken off while a human army stands there
		watched = {},              -- [region_key] = last owner seen ("nobody" when abandoned): razed by a human with any option; owner changes are logged
	}
end

permraze = {
	persistent = new_state(),
}

local function sorted_keys(t)
	local keys = {}
	for key in pairs(t) do
		keys[#keys + 1] = key
	end
	table.sort(keys)
	return keys
end

-- Script log; a debug build also writes permraze_log.txt next to the game
-- executable (the script log is often off).
local function log(msg)
	local has_turn, turn = pcall(function() return cm:model():turn_number() end)
	msg = "Permanent Raze: turn " .. (has_turn and tostring(turn) or "?") .. ": " .. tostring(msg)
	out(msg)
	if not FILE_LOG then
		return
	end
	local ok, file = pcall(io.open, "permraze_log.txt", "a")
	if ok and file then
		file:write(msg .. "\n")
		file:close()
	end
end

-- For permraze_corruption.lua, so its work lands in the same log.
function permraze:log(msg)
	log(msg)
end

-- A listener whose errors land in our log; the game would only put them in its script log.
local function listen(name, event, condition, callback)
	local guarded_condition = condition
	if condition ~= true then
		guarded_condition = function(context)
			local ok, result = pcall(condition, context)
			if not ok then
				log(name .. " condition failed: " .. tostring(result))
				return false
			end
			return result
		end
	end
	core:add_listener(name, event, guarded_condition, function(context)
		local ok, err = pcall(callback, context)
		if not ok then
			log(name .. " failed: " .. tostring(err))
		end
	end, true)
end

-- Regions where a human picked a vanilla option this turn: their raze is not ours.
local vanilla_decided = {}

-- Both events happen in the same occupation, in an order we do not rely on.
function permraze:on_decision(option_id, is_human, region_key, faction_key)
	if is_human then
		log("decision " .. option_id .. (OPTION_IDS[option_id] and " (ours)" or " (vanilla)")
			.. " at " .. region_key .. " by " .. faction_key)
	end
	if not is_human then
		return
	end
	if not OPTION_IDS[option_id] then
		self.persistent.razed[region_key] = nil -- a vanilla raze
		vanilla_decided[region_key] = true
		return
	end

	-- Watched even if the raze never comes; the round audit then logs who holds it.
	self.persistent.watched[region_key] = self.persistent.watched[region_key] or "unknown"
	if self.persistent.razed[region_key] then
		self.persistent.razed[region_key] = nil
		self:erase_region(region_key, faction_key)
	else
		self.persistent.pending[region_key] = faction_key
	end
end

-- Rewards that vanilla scripts give only for their own option id, keyed by that id.
-- Each repeats the vanilla listener for our copy of the option.
local SCRIPTED_REWARDS = {
	-- Wood Elves' Clear Heathland feeds the nearby Magical Forest (wh2_dlc16_wef_worldroots.lua).
	["1598549406"] = function(context)
		local faction = context:character():faction()
		if not faction:is_human() or type(Worldroots) ~= "table" then
			return
		end
		local forest = Worldroots:is_adjacent_to_forest(context:garrison_residence():region():name())
		if forest then
			local amount = Worldroots.razing_value + cm:get_factions_bonus_value(faction, "additional_worldroots_health_from_razing")
			Worldroots:add_pooled_resource_to_all_wood_elves(forest, "wh2_dlc16_resource_factor_razing_and_battles", amount, nil, true)
		end
	end,
	-- Beastmen's raze and retreat gives back action points (wh2_dlc17_bloodgrounds.lua).
	["411"] = function(context)
		if type(Bloodgrounds) ~= "table" then
			return
		end
		local region_key = context:garrison_residence():region():name()
		local bloodground = Bloodgrounds:is_bloodground_region(region_key)
		if bloodground and bloodground.ritual_completed then
			Bloodgrounds:apply_vfx(region_key, Bloodgrounds.defiled_bloodground_vfx_key)
		end
		cm:replenish_action_points("character_cqi:" .. context:character():command_queue_index(), Bloodgrounds.razing_settlement_options["411"])
		Bloodgrounds:update_effect_bundles_for_bloodgrounds()
	end,
	-- Tamurkhan's Exalted Hero chieftain gains deference from razing (wh3_dlc25_campaign_nur_chieftains.lua).
	["1714590130"] = function(context)
		if type(nur_chieftains) ~= "table" or not nur_chieftains.exalted_hero.has_spawned
			or context:character():faction():name() ~= nur_chieftains.faction then
			return
		end
		local hero = nur_chieftains.exalted_hero
		nur_chieftains:increase_deference_amount(hero.pr_deference_key, hero.pr_factor_unique, 1)
	end,
}

function permraze:give_scripted_reward(option_id, context)
	local reward = SCRIPTED_REWARDS[SOURCE_IDS[option_id]]
	if not reward then
		return
	end
	local ok, err = pcall(reward, context)
	if ok then
		log("scripted reward of vanilla option " .. SOURCE_IDS[option_id] .. " run")
	else
		log("scripted reward failed: " .. tostring(err))
	end
end

function permraze:on_razed(region_key, faction_key)
	log("razed " .. region_key .. " by " .. faction_key)
	self.persistent.watched[region_key] = "nobody"
	local pending_faction = self.persistent.pending[region_key]
	if pending_faction then
		self.persistent.pending[region_key] = nil
		self:erase_region(region_key, pending_faction)
	elseif not vanilla_decided[region_key] then
		self.persistent.razed[region_key] = faction_key
	end
end

-- Set when the AI erased ruins since the last corruption refresh.
local corruption_stale = false

-- Chance in percent that an AI raze erases the ruins; 0 when the option is off or without MCT.
function permraze:ai_erase_chance()
	local ok, settings = pcall(function()
		return permraze_corruption:settings()
	end)
	if not ok or type(settings) ~= "table" or settings.ai_erase ~= true or type(settings.ai_erase_chance) ~= "number" then
		return 0
	end
	return settings.ai_erase_chance
end

-- Cultures with no "raze forever" button: Nagash's Undead Legions devastate everything anyway (tools/generate.py).
local AI_SKIPPED_CULTURES = { wh3_dlc29_nag_undead_legions = true }

function permraze:on_ai_razed(region_key, faction_key)
	local chance = self:ai_erase_chance()
	if chance <= 0 or self.persistent.erased[region_key] then
		return
	end
	local faction = cm:get_faction(faction_key)
	if faction and not faction:is_null_interface() and AI_SKIPPED_CULTURES[faction:culture()] then
		return
	end
	local roll = cm:random_number(100)
	if roll > chance then
		log("AI raze of " .. region_key .. " by " .. faction_key .. " kept: rolled " .. roll .. ", chance " .. chance)
		return
	end
	log("AI raze of " .. region_key .. " by " .. faction_key .. " erased: rolled " .. roll .. ", chance " .. chance)
	self:erase_and_devastate(region_key, faction_key)
	corruption_stale = true
end

function permraze:refresh_stale_corruption()
	if corruption_stale then
		self:refresh_corruption()
	end
end

function permraze:clear_turn_state()
	for _, region_key in ipairs(sorted_keys(self.persistent.pending)) do
		log("our option at " .. region_key .. " was never followed by a raze")
	end
	for _, region_key in ipairs(sorted_keys(self.persistent.razed)) do
		log("raze of " .. region_key .. " came without a decision")
	end
	self.persistent.pending = {}
	self.persistent.razed = {}
	vanilla_decided = {}
end

-- Settings live in the corruption script, which reads every MCT option. Off without MCT.
function permraze:rebuild_allowed()
	local ok, settings = pcall(function()
		return permraze_corruption:settings()
	end)
	if not ok or type(settings) ~= "table" or type(settings.allow_rebuild) ~= "boolean" then
		return false
	end
	return settings.allow_rebuild
end

-- Regions where a human faction has an army led by a general, and the regions
-- next to them: an army colonises ruins straight from a neighbouring region.
function permraze:human_army_regions()
	local regions = {}
	for _, faction_key in ipairs(cm:get_human_factions()) do
		local faction = cm:get_faction(faction_key)
		if faction and not faction:is_null_interface() then
			local forces = faction:military_force_list()
			for i = 0, forces:num_items() - 1 do
				local force = forces:item_at(i)
				if force:has_general() then
					local character = force:general_character()
					if character:has_region() then
						local region = character:region()
						regions[region:name()] = true
						local adjacent = region:adjacent_region_list()
						for j = 0, adjacent:num_items() - 1 do
							regions[adjacent:item_at(j):name()] = true
						end
					end
				end
			end
		end
	end
	return regions
end

-- Lifts the block where a human army stands and puts it back everywhere else.
function permraze:sync_blocks()
	if not self:rebuild_allowed() then
		self:restore_blocks()
		return
	end
	local armies = self:human_army_regions()
	for _, region_key in ipairs(sorted_keys(self.persistent.lifted)) do
		if not armies[region_key] then
			self:restore_block(region_key)
		end
	end
	for _, region_key in ipairs(sorted_keys(self.persistent.erased)) do
		if armies[region_key] and self:can_lift(region_key) then
			cm:remove_effect_bundle_from_region(BUNDLE_KEY, region_key)
			self.persistent.lifted[region_key] = true
			log("lifted block from " .. region_key)
		end
	end
end

function permraze:can_lift(region_key)
	return not self.persistent.lifted[region_key]
		and self.persistent.erased[region_key].turn ~= cm:model():turn_number()
		and cm:get_region(region_key):is_abandoned()
end

function permraze:restore_block(region_key)
	if not self.persistent.erased[region_key] then
		self.persistent.lifted[region_key] = nil
		return
	end
	if cm:get_region(region_key):is_abandoned() then
		self.persistent.lifted[region_key] = nil
		cm:apply_effect_bundle_to_region(BUNDLE_KEY, region_key, 0)
		log("restored block on " .. region_key)
	else
		self:on_occupied(region_key)
	end
end

function permraze:restore_blocks()
	for _, region_key in ipairs(sorted_keys(self.persistent.lifted)) do
		self:restore_block(region_key)
	end
end

function permraze:on_region_changed(region_key)
	if self.persistent.erased[region_key] and not cm:get_region(region_key):is_abandoned() then
		self:on_occupied(region_key)
	end
end

-- An erased ruin got an owner: rebuilt if a player colonised it while lifted, sealed again otherwise.
function permraze:on_occupied(region_key)
	local owner = cm:get_region(region_key):owning_faction()
	log("erased " .. region_key .. " taken by " .. (owner:is_null_interface() and "nobody" or owner:name())
		.. (self.persistent.lifted[region_key] and " while lifted" or ""))
	if self.persistent.lifted[region_key] and self:rebuild_allowed()
		and not owner:is_null_interface() and owner:is_human() then
		self:rebuild(region_key)
	else
		self:reseal(region_key)
	end
end

function permraze:reseal(region_key)
	self.persistent.lifted[region_key] = nil
	cm:set_region_abandoned(region_key)
	self:seal(region_key)
	log("sealed again " .. region_key .. ", abandoned now: " .. tostring(cm:get_region(region_key):is_abandoned()))
	self:refresh_corruption()
end

-- Round start: catches owners that changed without the event reaching us.
function permraze:reseal_taken()
	for _, region_key in ipairs(sorted_keys(self.persistent.erased)) do
		local region = cm:get_region(region_key)
		if not region:is_abandoned() then
			self:on_occupied(region_key)
		elseif not self.persistent.lifted[region_key] and not region:has_effect_bundle(BUNDLE_KEY) then
			log("block missing on " .. region_key .. ", put back")
			cm:apply_effect_bundle_to_region(BUNDLE_KEY, region_key, 0)
		end
	end
end

-- Armies of a faction in a region or next to it: an army colonises ruins from a neighbouring region.
function permraze:armies_near(faction_key, region)
	local faction = cm:get_faction(faction_key)
	if not faction or faction:is_null_interface() then
		return 0
	end
	local near = { [region:name()] = true }
	local adjacent = region:adjacent_region_list()
	for i = 0, adjacent:num_items() - 1 do
		near[adjacent:item_at(i):name()] = true
	end
	local count = 0
	local forces = faction:military_force_list()
	for i = 0, forces:num_items() - 1 do
		local force = forces:item_at(i)
		if force:has_general() and force:general_character():has_region()
			and near[force:general_character():region():name()] then
			count = count + 1
		end
	end
	return count
end

local function faction_name(get)
	local ok, faction = pcall(get)
	if not ok or not faction or faction:is_null_interface() then
		return "nobody"
	end
	return faction:name()
end

local function owner_name(region)
	if region:is_abandoned() then
		return "nobody"
	end
	return faction_name(function() return region:owning_faction() end)
end

-- Round start: owners of razed regions that changed without the event reaching us.
function permraze:audit_watched()
	for _, region_key in ipairs(sorted_keys(self.persistent.watched)) do
		local region = cm:get_region(region_key)
		local owner = owner_name(region)
		if owner ~= self.persistent.watched[region_key] then
			log("owner of " .. region_key .. " changed with no event seen: "
				.. tostring(self.persistent.watched[region_key]) .. " -> " .. owner
				.. (self.persistent.erased[region_key] and ", erased" or ", not erased")
				.. (region:has_effect_bundle(BUNDLE_KEY) and ", blocked" or ", NOT blocked"))
			self.persistent.watched[region_key] = owner
		end
	end
end

-- Who took a ruin a human razed, and how: the clue for ruins settled with no army in sight.
function permraze:log_owner_change(context)
	local region = context:region()
	local region_key = region:name()
	if not self.persistent.watched[region_key] and not self.persistent.erased[region_key]
		and not region:has_effect_bundle(MARKER_KEY) then
		return
	end
	local owner = owner_name(region)
	if self.persistent.watched[region_key] then
		self.persistent.watched[region_key] = owner
	end
	local has_reason, reason = pcall(function() return context:reason() end)
	log("owner change at " .. region_key .. ": "
		.. faction_name(function() return context:previous_faction() end) .. " -> " .. owner
		.. ", reason " .. (has_reason and tostring(reason) or "?")
		.. (self.persistent.erased[region_key] and ", erased" or ", not erased")
		.. (region:has_effect_bundle(BUNDLE_KEY) and ", blocked" or ", NOT blocked")
		.. (region:has_effect_bundle(MARKER_KEY) and ", marked" or ", not marked")
		.. ", " .. self:armies_near(owner, region) .. " of its armies near")
end

function permraze:rebuild(region_key)
	local region = cm:get_region(region_key)

	self.persistent.erased[region_key] = nil
	self.persistent.lifted[region_key] = nil
	cm:remove_effect_bundle_from_region(BUNDLE_KEY, region_key)
	cm:remove_effect_bundle_from_region(MARKER_KEY, region_key)
	cm:cai_enable_targeting_against_settlement("settlement:" .. region_key)
	cm:set_settlement_devastated_state(region:settlement(), REBUILT_STATE)
	log("rebuilt " .. region_key)

	self:maybe_restore_province(region)

	local ok, err = pcall(function()
		if type(permraze_corruption) == "table" then
			permraze_corruption:clear(region_key)
		end
	end)
	if not ok then
		log("corruption clear failed: " .. tostring(err))
	end
	self:refresh_corruption()
end

-- Only lifts scorched land we laid ourselves, by the same threshold that laid it.
function permraze:maybe_restore_province(region)
	local province = region:province()
	local province_key = province:key()
	if not self.persistent.devastated_provinces[province_key] then
		return
	end

	local regions = province:regions()
	local total = regions:num_items()
	local abandoned = 0
	for i = 0, total - 1 do
		if regions:item_at(i):is_abandoned() then
			abandoned = abandoned + 1
		end
	end
	if abandoned >= math.floor(total / 2) + 1 then
		return
	end

	cm:deactivate_campaign_map_event_area(region:event_area_name())
	self.persistent.devastated_provinces[province_key] = nil
	log("restored province " .. province_key)
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

function permraze:seal(region_key)
	local settlement = cm:get_region(region_key):settlement()

	cm:cai_disable_targeting_against_settlement("settlement:" .. region_key)
	cm:apply_effect_bundle_to_region(BUNDLE_KEY, region_key, 0)
	cm:apply_effect_bundle_to_region(MARKER_KEY, region_key, 0)
	cm:reset_settlement_type(settlement, SETTLEMENT_TYPE, 1)
	cm:set_settlement_devastated_state(settlement, SETTLEMENT_STATE)
end

function permraze:erase_and_devastate(region_key, faction_key)
	self:seal(region_key)

	self.persistent.erased[region_key] = {
		faction = faction_key,
		order = self:next_erase_order(),
		turn = cm:model():turn_number(),
	}
	log("erased " .. region_key)

	local faction = cm:get_faction(faction_key)
	if not faction or faction:is_null_interface() then
		return
	end

	-- On Archaon's Destroyer path his own script devastates the province and counts it
	-- toward his bonuses and long victory; doing it first would make him skip it.
	if self:archaon_devastates_for(faction) then
		log("province of " .. region_key .. " left to Archaon's script")
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

-- Ruins erased before the marker existed.
function permraze:mark_erased()
	for _, region_key in ipairs(sorted_keys(self.persistent.erased)) do
		if not cm:get_region(region_key):has_effect_bundle(MARKER_KEY) then
			cm:apply_effect_bundle_to_region(MARKER_KEY, region_key, 0)
			log("marker put back on " .. region_key)
		end
	end
end

function permraze:refresh_corruption()
	corruption_stale = false
	local ok, err = pcall(function()
		if type(permraze_corruption) == "table" then
			permraze_corruption:refresh(self.persistent)
		end
	end)
	if not ok then
		log("corruption refresh failed: " .. tostring(err))
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
	if self.persistent.devastated_provinces[province_key] then
		return false
	end
	if not look then
		log("province " .. province_key .. " not scorched: " .. tostring(culture_key) .. " has no devastation look")
		return false
	end

	local event_area_key = region:event_area_name()
	if not event_area_key or event_area_key == "" then
		log("province " .. province_key .. " not scorched: " .. region_key .. " has no event area")
		return false
	end

	-- Endgames, Archaon or Nagash may already have devastated this area.
	if cm:is_campaign_map_event_area_activated_in_region(province:capital_region():name()) then
		log("province " .. province_key .. " not scorched: already devastated by the game")
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
		log("province " .. province_key .. " not scorched yet: " .. abandoned .. " of " .. total .. " regions in ruins")
		return false
	end

	cm:activate_campaign_map_event_area(event_area_key, look)
	self.persistent.devastated_provinces[province_key] = true
	log("devastated province " .. province_key)
	return true
end

-- Only cultures with a devastation look scorch the land; Bretonnia razing a
-- province should not turn it into a Chaos wasteland. Returns nil for them.
function permraze:look_for(culture_key)
	return LOOK_CULTURES[culture_key]
end

function permraze:init()
	listen("permraze_occupation_decision", "CharacterPerformsSettlementOccupationDecision",
		true,
		function(context)
			local faction = context:character():faction()
			local option_id = tostring(context:occupation_decision())
			local region_key = context:garrison_residence():region():name()
			self:on_decision(option_id, faction:is_human(), region_key, faction:name())
			self:give_scripted_reward(option_id, context)
		end
	)

	listen("permraze_settlement_razed", "CharacterRazedSettlement",
		function(context)
			return context:character():faction():is_human()
		end,
		function(context)
			self:on_razed(
				context:garrison_residence():region():name(),
				context:character():faction():name()
			)
		end
	)

	listen("permraze_ai_razed", "CharacterRazedSettlement",
		function(context)
			return not context:character():faction():is_human()
		end,
		function(context)
			self:on_ai_razed(
				context:garrison_residence():region():name(),
				context:character():faction():name()
			)
		end
	)

	listen("permraze_round_start", "WorldStartRound",
		true,
		function()
			self:clear_turn_state()
			self:restore_blocks()
			self:reseal_taken()
			self:refresh_stale_corruption()
			local ok, err = pcall(function()
				self:audit_watched()
			end)
			if not ok then
				log("owner audit failed: " .. tostring(err))
			end
		end
	)

	listen("permraze_turn_start", "FactionTurnStart",
		true,
		function(context)
			if context:faction():is_human() then
				self:refresh_stale_corruption()
				self:sync_blocks()
			else
				self:restore_blocks()
			end
		end
	)

	listen("permraze_army_moved", "CharacterFinishedMovingEvent",
		function(context)
			local character = context:character()
			return character:faction():is_human() and character:has_military_force()
		end,
		function()
			self:sync_blocks()
		end
	)

	listen("permraze_region_changed", "RegionFactionChangeEvent",
		true,
		function(context)
			local ok, err = pcall(function()
				self:log_owner_change(context)
			end)
			if not ok then
				log("owner change log failed: " .. tostring(err))
			end
			self:on_region_changed(context:region():name())
		end
	)

	listen("permraze_mct_finalized", "MctFinalized",
		true,
		function()
			log("MCT settings changed: " .. self:settings_text())
			if not self:rebuild_allowed() then
				self:restore_blocks()
			end
			self:refresh_corruption()
		end
	)

	listen("permraze_daemon_ascend", "RitualCompletedEvent",
		function(context)
			return context:ritual():ritual_key():sub(1, #ASCEND_PREFIX) == ASCEND_PREFIX
				and context:performing_faction():is_human()
		end,
		function(context)
			local key = context:ritual():ritual_key()
			self.persistent.daemon_gods[context:performing_faction():name()] = key:sub(#ASCEND_PREFIX + 1)
			log(context:performing_faction():name() .. " ascended to " .. key:sub(#ASCEND_PREFIX + 1))
			self:refresh_corruption()
		end
	)

	-- Last on purpose: nothing in here may stop the listeners above from registering.
	self:migrate_erased()
	self:mark_erased()
	self:refresh_corruption()
	self:log_state()
end

function permraze:settings_text()
	local ok, settings = pcall(function()
		return permraze_corruption:settings()
	end)
	if not ok or type(settings) ~= "table" then
		return "unreadable"
	end
	local parts = {}
	for _, key in ipairs(sorted_keys(settings)) do
		if not key:find("^culture_") then
			parts[#parts + 1] = key .. "=" .. tostring(settings[key])
		end
	end
	return table.concat(parts, " ")
end

-- One line per erased ruin on load, to tell lost state from a ruin that lost its block.
function permraze:log_state()
	local ok, err = pcall(function()
		local keys = sorted_keys(self.persistent.erased)
		log("loaded, " .. #keys .. " erased ruins, " .. #sorted_keys(self.persistent.watched) .. " razed regions watched, "
			.. #sorted_keys(self.persistent.devastated_provinces) .. " scorched provinces; settings " .. self:settings_text())
		for _, region_key in ipairs(keys) do
			local region = cm:get_region(region_key)
			local owner = region:owning_faction()
			log("  " .. region_key
				.. (region:is_abandoned() and " abandoned" or " owned by " .. (owner:is_null_interface() and "?" or owner:name()))
				.. (region:has_effect_bundle(BUNDLE_KEY) and ", blocked" or ", NOT blocked")
				.. (region:has_effect_bundle(MARKER_KEY) and ", marked" or ", not marked")
				.. (self.persistent.lifted[region_key] and ", lifted" or ""))
		end
	end)
	if not ok then
		log("state log failed: " .. tostring(err))
	end
end

cm:add_first_tick_callback(
	function()
		local ok, err = pcall(function()
			permraze:init()
		end)
		if not ok then
			log("start failed: " .. tostring(err))
		end
	end
)

--------------------------------------------------------------
----------------------- SAVING / LOADING ---------------------
--------------------------------------------------------------
cm:add_saving_game_callback(
	function(context)
		cm:save_named_value(SAVE_KEY, permraze.persistent, context)
		log("saved, " .. #sorted_keys(permraze.persistent.erased) .. " erased ruins")
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
