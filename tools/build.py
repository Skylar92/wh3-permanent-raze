"""Build permanent_raze.pack from the installed game's vanilla data.

usage: python -m tools.build [--install]

Writes dist/permanent_raze.pack and its Workshop preview dist/permanent_raze.png;
--install copies both into the game's data folder.
"""
import shutil
import sys

from tools.dbtable import decode_table, encode_table, load_schema
from tools.generate import (clone_sources, devastation_looks, make_bundle_tables, make_effect_tables, make_loc,
                            make_option_clones, make_scripted_bonus_table)
from tools.loc import encode_loc
from tools.packfile import read_pack, write_pack
from tools.preview import make_preview, save_preview
from tools.paths import GAME_DATA, ROOT, SCHEMA
from tools.render import render_corruption_script, render_mct_settings, render_script

PACK_NAME = "permanent_raze.pack"
PREVIEW_NAME = "permanent_raze.png"
TABLE_FILE = "permanent_raze"
SCRIPT_PATH = "script/campaign/mod/permraze.lua"
CORRUPTION_PATH = "script/campaign/mod/permraze_corruption.lua"
MCT_PATH = "script/mct/settings/permraze.lua"
OPTIONS = "culture_settlement_occupation_options_tables"
CRITERIA = "campaign_group_member_criteria_culture_settlement_occupation_options_tables"
BUNDLES = "effect_bundles_tables"
JUNCTIONS = "effect_bundles_to_effects_junctions_tables"
CULTURES = "cultures_tables"
EFFECTS = "effects_tables"
EFFECT_BONUS = "effect_bonus_value_basic_junction_tables"
EFFECT_SCRIPTED = "effect_bonus_value_scripted_junctions_tables"


def _vanilla_tables():
    schema = load_schema(SCHEMA)
    vanilla = read_pack(GAME_DATA / "db.pack")

    def table(name):
        return decode_table(schema, name, vanilla[f"db/{name}/data__"])

    return schema, table


def build(out_path, file_log=False):
    schema, table = _vanilla_tables()

    vanilla_options = table(OPTIONS)
    options, criteria, ids = make_option_clones(vanilla_options, table(CRITERIA))
    bundles, junctions = make_bundle_tables(table(BUNDLES), table(JUNCTIONS))
    effects, effect_bonus = make_effect_tables(table(EFFECTS), table(EFFECT_BONUS))
    scripted = make_scripted_bonus_table(table(EFFECT_SCRIPTED))
    template = (ROOT / "src" / SCRIPT_PATH).read_text(encoding="utf-8")
    corruption = (ROOT / "src" / CORRUPTION_PATH).read_text(encoding="utf-8")
    mct = (ROOT / "src" / MCT_PATH).read_text(encoding="utf-8")

    files = {f"db/{t.name}/{TABLE_FILE}": encode_table(schema, t)
             for t in (options, criteria, bundles, junctions, effects, effect_bonus, scripted)}
    files[f"text/db/{TABLE_FILE}.loc"] = encode_loc(make_loc(ids))
    files[SCRIPT_PATH] = render_script(template, ids, devastation_looks(table(CULTURES)),
                                       clone_sources(vanilla_options), file_log).encode("utf-8")
    files[CORRUPTION_PATH] = render_corruption_script(corruption).encode("utf-8")
    files[MCT_PATH] = render_mct_settings(mct, file_log).encode("utf-8")
    write_pack(out_path, files)
    return files


def main(argv, dist=ROOT / "dist"):
    dist.mkdir(exist_ok=True)
    build(dist / PACK_NAME, file_log="--log" in argv)  # --log: local debug build that writes permraze_log.txt
    save_preview(make_preview(), dist / PREVIEW_NAME)
    print("built %s and %s" % (dist / PACK_NAME, dist / PREVIEW_NAME))
    if "--install" in argv:
        for name in (PACK_NAME, PREVIEW_NAME):  # the launcher wants the preview next to the pack
            shutil.copyfile(dist / name, GAME_DATA / name)
            print("installed %s" % (GAME_DATA / name))

if __name__ == "__main__":
    main(sys.argv[1:])
