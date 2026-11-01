"""Generate the mod's db rows and localisation from vanilla tables."""
from tools.dbtable import Table
from tools.texts import VANILLA_TEXTS

OPTION_ID_BASE = 2100500000
RAZE_OPTION = "occupation_decision_raze_without_occupy"
# Option groups that get no "raze forever" button: Nagash's Undead Legions devastate everything anyway.
EXCLUDED_GROUPS = frozenset({
    "wh3_dlc29_sc_nag_undead_legions_occupation_decision_raze_without_occupy",
})

# Clones keep the rewards and costs of the raze they copy; only a settlement type override is cleared,
# as erased ruins get Archaon's devastated type. Rewards that vanilla scripts give by option id are
# given by our script, which gets each clone's source id from clone_sources().
_CLEARED = ("override_settlement_type",)


ARCHAON_BUNDLE_KEY = "wh3_dlc29_chs_archaon_block_occupation"
BUNDLE_KEY = "permraze_block_occupation"
# Burning-ruins icon next to the settlement name, shown to everyone. The engine's own icon on the
# label follows the block only for the viewing faction, so it goes out while a player may rebuild.
MARKER_BUNDLE_KEY = "permraze_erased_marker"
ARCHAON_EFFECT_KEY = "wh3_dlc29_effect_chs_archaon_block_occupation"
EFFECT_KEY = "permraze_effect_block_occupation"
# The marker's only effect, hidden: Khorne's settlements take over ruins in their province by script at round
# start, past the block. The script adds this target bonus to the spread chance, so it never rolls.
NO_SPREAD_EFFECT_KEY = "permraze_effect_no_ruin_spread"
NO_SPREAD_SOURCE_KEY = "wh3_main_effect_region_chance_to_spread_to_ruin_source_hidden"
NO_SPREAD_BONUS = "settlement_spread_to_province_ruin_chance_target_bonus"
NO_SPREAD_VALUE = -1000
CORRUPTION_SOURCE_KEY = "wh3_main_bundle_corruption_chaos_high_reduction"
RUIN_BUNDLE_KEY = "permraze_ruin_corruption"
PROVINCE_BUNDLE_KEY = "permraze_province_corruption"


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
        clone[options.col("id")] = new_id
        clone[options.col("tooltip")] = _tooltip(VANILLA_TEXTS)
        new_options.rows.append(clone)
        for crit in criteria.rows:
            if crit[crit_option] == source[options.col("id")]:
                copy = list(crit)
                copy[crit_option] = new_id
                new_criteria.rows.append(copy)
        ids.append(new_id)
    return new_options, new_criteria, ids


def clone_sources(options):
    """{our option id: id of the vanilla raze it copies}, numbered as make_option_clones numbers them."""
    return {OPTION_ID_BASE + n: source[options.col("id")] for n, source in enumerate(select_sources(options))}


def make_bundle_tables(bundles, junctions):
    """Clone Archaon's permanent block-occupation bundle under our own key, plus the erased-ruins marker."""
    new_bundles, new_junctions = _empty_like(bundles), _empty_like(junctions)
    for row in bundles.rows:
        if row[bundles.col("key")] == ARCHAON_BUNDLE_KEY:
            clone = list(row)
            clone[bundles.col("key")] = BUNDLE_KEY
            clone[bundles.col("localised_title")] = VANILLA_TEXTS["bundle_title"]
            clone[bundles.col("localised_description")] = VANILLA_TEXTS["bundle_description"]
            marker = list(clone)
            marker[bundles.col("key")] = MARKER_BUNDLE_KEY
            marker[bundles.col("localised_title")] = VANILLA_TEXTS["marker_title"]
            marker[bundles.col("localised_description")] = ""
            marker[bundles.col("show_in_3d_space")] = True
            marker[bundles.col("owner_only")] = False
            new_bundles.rows.extend([clone, marker])
    new_bundles.rows.extend(make_corruption_bundles(bundles))
    for row in junctions.rows:
        if row[junctions.col("effect_bundle_key")] == ARCHAON_BUNDLE_KEY:
            clone = list(row)
            clone[junctions.col("effect_bundle_key")] = BUNDLE_KEY
            clone[junctions.col("effect_key")] = EFFECT_KEY
            no_spread = list(clone)
            no_spread[junctions.col("effect_bundle_key")] = MARKER_BUNDLE_KEY
            no_spread[junctions.col("effect_key")] = NO_SPREAD_EFFECT_KEY
            no_spread[junctions.col("value")] = NO_SPREAD_VALUE
            new_junctions.rows.extend([clone, no_spread])
    return new_bundles, new_junctions


def make_corruption_bundles(bundles):
    """Base rows for the runtime custom bundles that carry corruption; effects are added at runtime."""
    source = next(r for r in bundles.rows if r[bundles.col("key")] == CORRUPTION_SOURCE_KEY)
    rows = []
    for key in (RUIN_BUNDLE_KEY, PROVINCE_BUNDLE_KEY):
        clone = list(source)
        clone[bundles.col("key")] = key
        clone[bundles.col("localised_title")] = VANILLA_TEXTS["title"]
        clone[bundles.col("localised_description")] = ""
        rows.append(clone)
    return rows


def make_effect_tables(effects, bonus_values):
    """Our own copy of Archaon's block-occupation effect, so the ruins don't claim Chaos razed them,
    and the hidden no-spread effect."""
    new_effects, new_bonus = _empty_like(effects), _empty_like(bonus_values)
    for source, target in ((effects, new_effects), (bonus_values, new_bonus)):
        for row in source.rows:
            if row[source.col("effect")] == ARCHAON_EFFECT_KEY:
                clone = list(row)
                clone[source.col("effect")] = EFFECT_KEY
                target.rows.append(clone)
    for row in effects.rows:
        if row[effects.col("effect")] == NO_SPREAD_SOURCE_KEY:
            clone = list(row)
            clone[effects.col("effect")] = NO_SPREAD_EFFECT_KEY
            new_effects.rows.append(clone)
    return new_effects, new_bonus


def make_scripted_bonus_table(scripted):
    """Ties the no-spread effect to the target bonus Khorne's spread script reads."""
    new_scripted = _empty_like(scripted)
    for row in scripted.rows:
        if row[scripted.col("effect")] == NO_SPREAD_SOURCE_KEY:
            clone = list(row)
            clone[scripted.col("effect")] = NO_SPREAD_EFFECT_KEY
            clone[scripted.col("scripted_record")] = NO_SPREAD_BONUS
            new_scripted.rows.append(clone)
    return new_scripted


def _tooltip(texts):
    return texts["title"] + "||" + texts["description"]


def make_loc(option_ids):
    texts = VANILLA_TEXTS
    entries = [("culture_settlement_occupation_options_tooltip_%d" % i, _tooltip(texts)) for i in option_ids]
    entries.append(("effect_bundles_localised_title_" + BUNDLE_KEY, texts["bundle_title"]))
    entries.append(("effect_bundles_localised_description_" + BUNDLE_KEY, texts["bundle_description"]))
    entries.append(("effect_bundles_localised_title_" + MARKER_BUNDLE_KEY, texts["marker_title"]))
    for key in (RUIN_BUNDLE_KEY, PROVINCE_BUNDLE_KEY):
        entries.append(("effect_bundles_localised_title_" + key, texts["title"]))
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
