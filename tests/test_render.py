import pytest

from tools.render import fill_placeholders, lua_literal, render_script

TEMPLATE = "local OPTION_IDS = {} --@@OPTION_IDS@@\nlocal LOOK_CULTURES = {} --@@LOOK_CULTURES@@\n"


def test_render_ids_and_looks():
    lua = render_script(TEMPLATE, [7], {"a": "b"})
    assert 'local OPTION_IDS = {["7"] = true}' in lua
    assert 'local LOOK_CULTURES = {["a"] = "b"}' in lua


def test_lua_literal_string_escapes():
    assert lua_literal('a"b\\c') == '"a\\"b\\\\c"'


def test_lua_literal_nested_dict():
    assert lua_literal({"a": {"b": 1}, "c": [1, "x"]}) == '{["a"] = {["b"] = 1}, ["c"] = {1, "x"}}'


def test_lua_literal_bool():
    assert lua_literal(True) == "true"
    assert lua_literal(False) == "false"


def test_lua_literal_float():
    assert lua_literal(2.5) == "2.5"


def test_fill_placeholders_requires_exactly_one():
    assert fill_placeholders("x = {} --@@A@@", {"A": 1}) == "x = 1"
    with pytest.raises(ValueError):
        fill_placeholders("x = 1", {"A": 1})
    with pytest.raises(ValueError):
        fill_placeholders("{} --@@A@@\n{} --@@A@@", {"A": 1})


def test_lua_literal_string_newlines():
    assert lua_literal("a\nb\rc\0") == '"a\\nb\\rc\\0"'


def test_lua_literal_rejects_inf_and_nan():
    for bad in (float("inf"), float("-inf"), float("nan")):
        with pytest.raises(ValueError):
            lua_literal(bad)
