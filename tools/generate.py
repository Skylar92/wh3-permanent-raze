"""Generate the mod's db rows and localisation from vanilla tables."""
from tools.dbtable import Table

OPTION_ID_BASE = 2100500000
RAZE_OPTION = "occupation_decision_raze_without_occupy"
TITLE = "Стереть навсегда"
DESCRIPTION = "Сравнять поселение с землёй так, что его больше никто и никогда не сможет занять. Это необратимо."

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
BUNDLE_TITLE = "Стёрто навсегда"
BUNDLE_DESCRIPTION = "Эти руины уничтожены окончательно. Здесь больше никто не сможет поселиться."
FALLBACK_LOOK_CULTURE = "wh_main_chs_chaos"


def _empty_like(table):
    return Table(table.name, table.version, table.guid, list(table.fields), [])


def select_sources(options):
    """Vanilla raze rows to clone; drop resource-gated rows when their group has a free one."""
    raze = [r for r in options.rows if r[options.col("settlement_option")] == RAZE_OPTION]
    group, required = options.col("group"), options.col("required_resources")
    free_groups = {r[group] for r in raze if not r[required]}
    return [r for r in raze if not (r[required] and r[group] in free_groups)]


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
        clone[options.col("tooltip")] = TITLE + "||" + DESCRIPTION
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
            clone[bundles.col("localised_title")] = BUNDLE_TITLE
            clone[bundles.col("localised_description")] = BUNDLE_DESCRIPTION
            new_bundles.rows.append(clone)
    for row in junctions.rows:
        if row[junctions.col("effect_bundle_key")] == ARCHAON_BUNDLE_KEY:
            clone = list(row)
            clone[junctions.col("effect_bundle_key")] = BUNDLE_KEY
            new_junctions.rows.append(clone)
    return new_bundles, new_junctions


def make_loc(option_ids):
    entries = [("culture_settlement_occupation_options_tooltip_%d" % i, TITLE + "||" + DESCRIPTION)
               for i in option_ids]
    entries.append(("effect_bundles_localised_title_" + BUNDLE_KEY, BUNDLE_TITLE))
    entries.append(("effect_bundles_localised_description_" + BUNDLE_KEY, BUNDLE_DESCRIPTION))
    return entries


def cultures_with_look(cultures):
    """Culture keys that have their own campaign devastation look."""
    key, look = cultures.col("key"), cultures.col("devastation_state")
    return sorted(r[key] for r in cultures.rows if r[look])
