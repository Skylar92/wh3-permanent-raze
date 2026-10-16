"""Build permanent_raze.pack from the installed game's vanilla data.

usage: python -m tools.build [--install [--lang ru]]

Writes dist/permanent_raze.pack (English texts) and one dist/permanent_raze_<lang>.pack
translation patch per other game language. --install copies the main pack and the
patch for --lang (default ru) into the game's data folder.
"""
import shutil
import sys

from tools.dbtable import decode_table, encode_table, load_schema
from tools.generate import (cultures_with_look, make_bundle_tables, make_effect_tables, make_loc,
                            make_option_clones)
from tools.loc import encode_loc
from tools.packfile import read_pack, write_pack
from tools.paths import GAME_DATA, ROOT, SCHEMA
from tools.render import render_script
from tools.texts import LANGUAGES

PACK_NAME = "permanent_raze.pack"
TABLE_FILE = "permanent_raze"
SCRIPT_PATH = "script/campaign/mod/permraze.lua"
OPTIONS = "culture_settlement_occupation_options_tables"
CRITERIA = "campaign_group_member_criteria_culture_settlement_occupation_options_tables"
BUNDLES = "effect_bundles_tables"
JUNCTIONS = "effect_bundles_to_effects_junctions_tables"
CULTURES = "cultures_tables"
EFFECTS = "effects_tables"
EFFECT_BONUS = "effect_bonus_value_basic_junction_tables"


def _vanilla_tables():
    schema = load_schema(SCHEMA)
    vanilla = read_pack(GAME_DATA / "db.pack")

    def table(name):
        return decode_table(schema, name, vanilla[f"db/{name}/data__"])

    return schema, table


def build(out_path):
    schema, table = _vanilla_tables()

    options, criteria, ids = make_option_clones(table(OPTIONS), table(CRITERIA))
    bundles, junctions = make_bundle_tables(table(BUNDLES), table(JUNCTIONS))
    effects, effect_bonus = make_effect_tables(table(EFFECTS), table(EFFECT_BONUS))
    template = (ROOT / "src" / SCRIPT_PATH).read_text(encoding="utf-8")

    files = {f"db/{t.name}/{TABLE_FILE}": encode_table(schema, t)
             for t in (options, criteria, bundles, junctions, effects, effect_bonus)}
    files[f"text/db/{TABLE_FILE}.loc"] = encode_loc(make_loc(ids))
    files[SCRIPT_PATH] = render_script(template, ids, cultures_with_look(table(CULTURES))).encode("utf-8")
    write_pack(out_path, files)
    return files


def patch_name(lang):
    return "permanent_raze_%s.pack" % lang


def build_language_patch(lang, out_path):
    """A translation patch: one loc file whose '!' prefix sorts it ahead of the main pack's English loc."""
    _, table = _vanilla_tables()
    _, _, ids = make_option_clones(table(OPTIONS), table(CRITERIA))
    files = {f"text/db/!permraze_{lang}.loc": encode_loc(make_loc(ids, lang))}
    write_pack(out_path, files)
    return files


def main(argv):
    dist = ROOT / "dist"
    dist.mkdir(exist_ok=True)
    built = [dist / PACK_NAME]
    build(built[0])
    for lang in LANGUAGES:
        if lang != "en":
            built.append(dist / patch_name(lang))
            build_language_patch(lang, built[-1])
    print("built %d packs in %s" % (len(built), dist))
    if "--install" in argv:
        lang = argv[argv.index("--lang") + 1] if "--lang" in argv else "ru"
        for name in [PACK_NAME] + ([patch_name(lang)] if lang != "en" else []):
            shutil.copyfile(dist / name, GAME_DATA / name)
            print("installed %s" % (GAME_DATA / name))


if __name__ == "__main__":
    main(sys.argv[1:])
