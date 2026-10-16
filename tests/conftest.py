import pytest

from tools.dbtable import load_schema
from tools.packfile import read_pack
from tools.paths import GAME_DATA, SCHEMA


@pytest.fixture(scope="session")
def schema():
    return load_schema(SCHEMA)


@pytest.fixture(scope="session")
def vanilla_db():
    return read_pack(GAME_DATA / "db.pack")


def vanilla_table(schema, vanilla_db, name):
    from tools.dbtable import decode_table
    return decode_table(schema, name, vanilla_db[f"db/{name}/data__"])


@pytest.fixture(scope="session")
def vanilla_options(schema, vanilla_db):
    return vanilla_table(schema, vanilla_db, "culture_settlement_occupation_options_tables")


@pytest.fixture(scope="session")
def vanilla_criteria(schema, vanilla_db):
    return vanilla_table(schema, vanilla_db,
                         "campaign_group_member_criteria_culture_settlement_occupation_options_tables")


@pytest.fixture(scope="session")
def vanilla_bundles(schema, vanilla_db):
    return vanilla_table(schema, vanilla_db, "effect_bundles_tables")


@pytest.fixture(scope="session")
def vanilla_junctions(schema, vanilla_db):
    return vanilla_table(schema, vanilla_db, "effect_bundles_to_effects_junctions_tables")


@pytest.fixture(scope="session")
def vanilla_cultures(schema, vanilla_db):
    return vanilla_table(schema, vanilla_db, "cultures_tables")


@pytest.fixture(scope="session")
def vanilla_effects(schema, vanilla_db):
    return vanilla_table(schema, vanilla_db, "effects_tables")


@pytest.fixture(scope="session")
def vanilla_effect_bonus(schema, vanilla_db):
    return vanilla_table(schema, vanilla_db, "effect_bonus_value_basic_junction_tables")
