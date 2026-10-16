"""Generate the mod's db rows and localisation from vanilla tables."""
from tools.dbtable import Table
from tools.texts import TEXTS

OPTION_ID_BASE = 2100500000
RAZE_OPTION = "occupation_decision_raze_without_occupy"
DEFAULT_LANGUAGE = "en"
# Option groups that get no "raze forever" button: Nagash's Undead Legions devastate everything anyway.
EXCLUDED_GROUPS = frozenset({
    "wh3_dlc29_sc_nag_undead_legions_occupation_decision_raze_without_occupy",
})

# Columns cleared on every clone: faction-specific rewards, costs and timed bundles.
_CLEARED = (
    "acting_army_faction_effect_bundle", "target_settlement_faction_effect_bundle",
    "acting_army_effect_bundle", "resource_transaction", "required_resources",
    "capturing_force_resource_transaction", "captured_region_resource_transaction",
    "override_settlement_type",
)
_ZEROED = (
    "acting_army_faction_effect_bundle_turns", "target_settlement_faction_effect_bundle_turns",
    "acting_army_effect_bundle_turns",
)


ARCHAON_BUNDLE_KEY = "wh3_dlc29_chs_archaon_block_occupation"
BUNDLE_KEY = "permraze_block_occupation"
ARCHAON_EFFECT_KEY = "wh3_dlc29_effect_chs_archaon_block_occupation"
EFFECT_KEY = "permraze_effect_block_occupation"


def _empty_like(table):
    return Table(table.name, table.version, table.guid, list(table.fields), [], table.versioned)


def select_sources(options):
    """One vanilla raze row per option group: prefer rows without a resource cost, then the lowest id.

    Rows sharing a group are shown side by side (Khorne's two rites, Beastmen's two raze styles),
    so cloning more than one would give the player two "raze forever" buttons.
    """
    group, required, row_id = options.col("group"), options.col("required_resources"), options.col("id")
    best = {}
    for r in options.rows:
        if r[options.col("settlement_option")] != RAZE_OPTION or r[group] in EXCLUDED_GROUPS:
            continue
        rank = (bool(r[required]), r[row_id])
        if r[group] not in best or rank < best[r[group]][0]:
            best[r[group]] = (rank, r)
    return [r for _, r in sorted(best.values(), key=lambda item: item[0][1])]


def make_option_clones(options, criteria):
    """Return (new options table, new criteria table, new option ids)."""
    new_options, new_criteria = _empty_like(options), _empty_like(criteria)
    crit_option = criteria.col("culture_settlement_occupation_option")
    ids = []
    for n, source in enumerate(select_sources(options)):
        new_id = OPTION_ID_BASE + n
        clone = list(source)
        for name in _CLEARED:
            clone[options.col(name)] = None
        for name in _ZEROED:
            clone[options.col(name)] = 0
        clone[options.col("id")] = new_id
        clone[options.col("tooltip")] = _tooltip(DEFAULT_LANGUAGE)
        new_options.rows.append(clone)
        for crit in criteria.rows:
            if crit[crit_option] == source[options.col("id")]:
                copy = list(crit)
                copy[crit_option] = new_id
                new_criteria.rows.append(copy)
        ids.append(new_id)
    return new_options, new_criteria, ids


def make_bundle_tables(bundles, junctions):
    """Clone Archaon's permanent block-occupation bundle under our own key."""
    new_bundles, new_junctions = _empty_like(bundles), _empty_like(junctions)
    for row in bundles.rows:
        if row[bundles.col("key")] == ARCHAON_BUNDLE_KEY:
            clone = list(row)
            clone[bundles.col("key")] = BUNDLE_KEY
            clone[bundles.col("localised_title")] = TEXTS[DEFAULT_LANGUAGE]["bundle_title"]
            clone[bundles.col("localised_description")] = TEXTS[DEFAULT_LANGUAGE]["bundle_description"]
            new_bundles.rows.append(clone)
    for row in junctions.rows:
        if row[junctions.col("effect_bundle_key")] == ARCHAON_BUNDLE_KEY:
            clone = list(row)
            clone[junctions.col("effect_bundle_key")] = BUNDLE_KEY
            clone[junctions.col("effect_key")] = EFFECT_KEY
            new_junctions.rows.append(clone)
    return new_bundles, new_junctions


def make_effect_tables(effects, bonus_values):
    """Our own copy of Archaon's block-occupation effect, so the ruins don't claim Chaos razed them."""
    new_effects, new_bonus = _empty_like(effects), _empty_like(bonus_values)
    for source, target in ((effects, new_effects), (bonus_values, new_bonus)):
        for row in source.rows:
            if row[source.col("effect")] == ARCHAON_EFFECT_KEY:
                clone = list(row)
                clone[source.col("effect")] = EFFECT_KEY
                target.rows.append(clone)
    return new_effects, new_bonus


def _tooltip(lang):
    return TEXTS[lang]["title"] + "||" + TEXTS[lang]["description"]


def make_loc(option_ids, lang=DEFAULT_LANGUAGE):
    texts = TEXTS[lang]
    entries = [("culture_settlement_occupation_options_tooltip_%d" % i, _tooltip(lang)) for i in option_ids]
    entries.append(("effect_bundles_localised_title_" + BUNDLE_KEY, texts["bundle_title"]))
    entries.append(("effect_bundles_localised_description_" + BUNDLE_KEY, texts["bundle_description"]))
    entries.append(("effects_description_" + EFFECT_KEY, texts["effect_description"]))
    return entries


# Cultures without their own devastation look that borrow one (author's call):
# Chaos Dwarfs scorch the land like Chaos, the Vampire Coast leaves Nagash's dead land.
BORROWED_LOOKS = {
    "wh3_dlc23_chd_chaos_dwarfs": "wh_main_chs_chaos",
    "wh2_dlc11_cst_vampire_coast": "wh_main_vmp_vampire_counts",
}


def devastation_looks(cultures):
    """{culture key: culture whose devastation look it uses}; cultures not listed leave the land alone."""
    key, look = cultures.col("key"), cultures.col("devastation_state")
    looks = {r[key]: r[key] for r in cultures.rows if r[look]}
    looks.update(BORROWED_LOOKS)
    return dict(sorted(looks.items()))
