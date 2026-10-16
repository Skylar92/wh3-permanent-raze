"""Mod texts, composed from strings the game already ships in every language."""

# The main pack's texts, composed from strings the game already translates into every language,
# so players without a translation patch still read their own language:
# "Raze: Scorched Earth" on the button, "Cannot Colonise" on the ruins.
_RAZE = "{{tr:effect_bundles_localised_title_wh_dlc03_bundle_horde_raze}}"
_SCORCHED_EARTH = "{{tr:effect_bundles_localised_title_wh2_dlc11_noctilus_war_raiding}}"
_CANNOT_COLONISE = "{{tr:effect_bundles_localised_title_wh3_dlc26_block_occupation_beastmen}}"
_CANNOT_REOCCUPY = "{{tr:effects_description_wh3_main_effect_endgame_block_occupation}}"
VANILLA_TEXTS = {
    "title": _RAZE + ": " + _SCORCHED_EARTH,
    "description": _CANNOT_COLONISE,
    "bundle_title": _CANNOT_COLONISE,
    "bundle_description": _CANNOT_REOCCUPY,
    "effect_description": _CANNOT_REOCCUPY,
}

# Game language codes, as in data/local_<code>.pack; every referenced string must exist in all of them.
GAME_LANGUAGES = ("en", "ru", "ge", "fr", "it", "sp", "pl", "cz", "tr", "br", "kr", "cn", "zh")
FIELDS = tuple(VANILLA_TEXTS)
