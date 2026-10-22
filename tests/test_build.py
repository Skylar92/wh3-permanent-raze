import pytest
from lupa.lua51 import LuaRuntime

from test_corruption_lua import MOCK, set_mct
from test_permraze_lua import decide, raze
from tools.build import build, main
from tools.dbtable import decode_table
from tools.loc import decode_loc
from tools.packfile import read_pack

pytestmark = pytest.mark.game

TABLES = {
    "culture_settlement_occupation_options_tables": 48,
    "campaign_group_member_criteria_culture_settlement_occupation_options_tables": 1,
    "effect_bundles_tables": 3,
    "effect_bundles_to_effects_junctions_tables": 1,
    "effects_tables": 1,
    "effect_bonus_value_basic_junction_tables": 1,
}


@pytest.fixture(scope="module")
def built(tmp_path_factory):
    out = tmp_path_factory.mktemp("dist") / "permanent_raze.pack"
    build(out)
    return read_pack(out)


def test_pack_contents(built):
    assert set(built) == {f"db/{t}/permanent_raze" for t in TABLES} | {
        "text/db/permanent_raze.loc", "script/campaign/mod/permraze.lua",
        "script/campaign/mod/permraze_corruption.lua", "script/mct/settings/permraze.lua"}


@pytest.mark.parametrize("name,rows", TABLES.items())
def test_tables_decode_back(built, schema, name, rows):
    assert len(decode_table(schema, name, built[f"db/{name}/permanent_raze"]).rows) == rows


def test_loc_has_every_option(built):
    keys = dict(decode_loc(built["text/db/permanent_raze.loc"]))
    assert len(keys) == 53
    assert "culture_settlement_occupation_options_tooltip_2100500047" in keys


def test_script_has_all_ids(built):
    lua = built["script/campaign/mod/permraze.lua"].decode("utf-8")
    assert "--@@" not in lua and '["2100500047"] = true' in lua and '["wh3_dlc23_chd_chaos_dwarfs"] = "wh_main_chs_chaos"' in lua


def test_main_loc_uses_vanilla_translations(built):
    keys = dict(decode_loc(built["text/db/permanent_raze.loc"]))
    assert keys["culture_settlement_occupation_options_tooltip_2100500000"].startswith(
        "{{tr:effect_bundles_localised_title_wh_dlc03_bundle_horde_raze}}")



def test_built_scripts_have_no_placeholders(built):
    lua_files = {n: b for n, b in built.items() if n.endswith(".lua")}
    assert len(lua_files) == 3
    for name, data in lua_files.items():
        assert "--@@" not in data.decode("utf-8"), name


def built_game(built):
    lua = LuaRuntime(unpack_returned_tuples=True)
    lua.execute(MOCK)
    for name in ("permraze", "permraze_corruption"):
        lua.execute(built[f"script/campaign/mod/{name}.lua"].decode("utf-8"))
    g = lua.globals()
    g.lua = lua  # set_mct installs its get_mct() through it
    for f in g.FIRST_TICK.values():
        f()
    return g


def erase_r1(g):
    decide(g, "r1")
    raze(g, "r1")


def test_built_corruption_script_runs(built):
    g = built_game(built)
    erase_r1(g)
    rows = [[c[i] for i in range(1, len(c) + 1)] for c in g.CALLS.values()]
    assert ["apply_effect_bundle_to_region", "permraze_block_occupation", "r1", 0] in rows
    assert g.permraze.persistent.erased.r1.order == 1
    assert not [r for r in rows if r[0] in ("apply_custom", "remove_bundle")]


def test_built_corruption_script_refreshes_with_mct(built):
    g = built_game(built)
    set_mct(g, {"mode": "per_settlement"})
    erase_r1(g)
    rows = [[c[i] for i in range(1, len(c) + 1)] for c in g.CALLS.values()]
    assert [r for r in rows if r[0] == "apply_custom"] == [[
        "apply_custom", "permraze_ruin_corruption", "r1",
        "wh3_main_effect_corruption_reduction_events", "region_to_province_own_unseen", -5]]


def test_main_writes_only_the_mod_and_its_preview(tmp_path):
    main([], dist=tmp_path)
    assert sorted(p.name for p in tmp_path.iterdir()) == ["permanent_raze.pack", "permanent_raze.png"]
