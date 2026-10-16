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
