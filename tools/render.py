"""Embed generated data into the Lua campaign script template."""

from tools.corruption import (CORRUPTION_TYPES, CULTURE_DEFAULTS, DAEMON_PRINCE_FACTION, DAEMONS_CULTURE, EFFECT_SCOPE,
                              EFFECT_VALUES, FACTION_OVERRIDES, MCT_TEXTS, RU_PROBE, SETTINGS_DEFAULTS, SLIDERS,
                              campaign_defaults, effect_key)
from tools.generate import PROVINCE_BUNDLE_KEY, RUIN_BUNDLE_KEY

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


def render_corruption_script(template):
    """Fill every placeholder of the corruption script template."""
    return fill_placeholders(template, {
        "DEFAULTS": campaign_defaults(),
        "FACTION_OVERRIDES": FACTION_OVERRIDES,
        "DAEMONS_CULTURE": DAEMONS_CULTURE,
        "DAEMON_PRINCE_FACTION": DAEMON_PRINCE_FACTION,
        "RUIN_BUNDLE": RUIN_BUNDLE_KEY,
        "PROVINCE_BUNDLE": PROVINCE_BUNDLE_KEY,
        "EFFECT_SCOPE": EFFECT_SCOPE,
        "EFFECT_KEYS": {v: effect_key(v) for v in EFFECT_VALUES if v != "none"},
    })


UNTAINTED_KEY = "uied_component_texts_localised_string_region_corruption_untainted_Tooltip_40058"


def render_mct_settings(template):
    """Fill every placeholder of the MCT settings template."""
    return fill_placeholders(template, {
        "DEFAULTS": SETTINGS_DEFAULTS,
        "SLIDERS": SLIDERS,
        "CULTURES": list(CULTURE_DEFAULTS),
        "CULTURE_DEFAULTS": CULTURE_DEFAULTS,
        "EFFECT_VALUES": list(EFFECT_VALUES),
        "TYPE_NAME_KEYS": {t: "pooled_resources_display_name_wh3_main_corruption_" + t for t in CORRUPTION_TYPES},
        "UNTAINTED_KEY": UNTAINTED_KEY,
        "TEXTS": MCT_TEXTS,
        "RU_PROBE": list(RU_PROBE),
    })
