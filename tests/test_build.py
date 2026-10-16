import pytest

from tools.build import build
from tools.dbtable import decode_table
from tools.loc import decode_loc
from tools.packfile import read_pack

pytestmark = pytest.mark.game

TABLES = {
    "culture_settlement_occupation_options_tables": 50,
    "campaign_group_member_criteria_culture_settlement_occupation_options_tables": 2,
    "effect_bundles_tables": 1,
    "effect_bundles_to_effects_junctions_tables": 1,
}


@pytest.fixture(scope="module")
def built(tmp_path_factory):
    out = tmp_path_factory.mktemp("dist") / "permanent_raze.pack"
    build(out)
    return read_pack(out)


def test_pack_contents(built):
    assert set(built) == {f"db/{t}/permanent_raze" for t in TABLES} | {
        "text/db/permanent_raze.loc", "script/campaign/mod/permraze.lua"}


@pytest.mark.parametrize("name,rows", TABLES.items())
def test_tables_decode_back(built, schema, name, rows):
    assert len(decode_table(schema, name, built[f"db/{name}/permanent_raze"]).rows) == rows


def test_loc_has_every_option(built):
    keys = dict(decode_loc(built["text/db/permanent_raze.loc"]))
    assert len(keys) == 52
    assert "culture_settlement_occupation_options_tooltip_2100500049" in keys


def test_script_has_all_ids(built):
    lua = built["script/campaign/mod/permraze.lua"].decode("utf-8")
    assert "--@@" not in lua and '["2100500049"] = true' in lua and '["wh_main_chs_chaos"] = true' in lua
