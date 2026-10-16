"""Build permanent_raze.pack from the installed game's vanilla data.

usage: python -m tools.build [--install]
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


def build(out_path):
    schema = load_schema(SCHEMA)
    vanilla = read_pack(GAME_DATA / "db.pack")

    def table(name):
        return decode_table(schema, name, vanilla[f"db/{name}/data__"])

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


def main(argv):
    out = ROOT / "dist" / PACK_NAME
    out.parent.mkdir(exist_ok=True)
    files = build(out)
    print("built %s (%d files)" % (out, len(files)))
    if "--install" in argv:
        shutil.copyfile(out, GAME_DATA / PACK_NAME)
        print("installed to %s" % (GAME_DATA / PACK_NAME))


if __name__ == "__main__":
    main(sys.argv[1:])
