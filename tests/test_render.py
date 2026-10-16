from tools.render import render_script

TEMPLATE = "local OPTION_IDS = {} --@@OPTION_IDS@@\nlocal LOOK_CULTURES = {} --@@LOOK_CULTURES@@\n"


def test_render_ids_and_looks():
    lua = render_script(TEMPLATE, [7], {"a": "b"})
    assert 'local OPTION_IDS = {["7"] = true}' in lua
    assert 'local LOOK_CULTURES = {["a"] = "b"}' in lua
