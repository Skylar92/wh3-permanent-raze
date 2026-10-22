"""Embed generated data into the Lua campaign script template."""

OPTION_IDS_PLACEHOLDER = "{} --@@OPTION_IDS@@"
LOOK_CULTURES_PLACEHOLDER = "{} --@@LOOK_CULTURES@@"


_LUA_ESCAPES = {
    ord("\\"): "\\\\", ord('"'): '\\"', ord("\n"): "\\n", ord("\r"): "\\r", 0: "\\0",
}


def lua_literal(value):
    """Render a Python value as a Lua literal: dict -> table with string keys, list -> array table."""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, float):
        if value != value or value in (float("inf"), float("-inf")):
            raise ValueError("inf/nan is not a Lua literal")
        return repr(value)
    if isinstance(value, int):
        return repr(value)
    if isinstance(value, str):
        escaped = value.translate(_LUA_ESCAPES)
        return '"' + escaped + '"'
    if isinstance(value, dict):
        return "{" + ", ".join("[%s] = %s" % (lua_literal(str(k)), lua_literal(v)) for k, v in value.items()) + "}"
    if isinstance(value, (list, tuple)):
        return "{" + ", ".join(lua_literal(v) for v in value) + "}"
    raise TypeError("cannot render %r as a Lua literal" % (value,))


def fill_placeholders(template, values):
    """Replace each `{} --@@NAME@@` in the template with the Lua literal of values[NAME]."""
    for name, value in values.items():
        placeholder = "{} --@@%s@@" % name
        if template.count(placeholder) != 1:
            raise ValueError("template must contain exactly one " + placeholder)
        template = template.replace(placeholder, lua_literal(value))
    return template


def render_script(template, option_ids, look_cultures):
    """look_cultures: {culture key: culture whose devastation look it uses}."""
    return fill_placeholders(template, {
        "OPTION_IDS": {str(i): True for i in option_ids},
        "LOOK_CULTURES": dict(look_cultures),
    })
