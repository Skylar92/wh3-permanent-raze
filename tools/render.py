"""Embed generated data into the Lua campaign script template."""

OPTION_IDS_PLACEHOLDER = "{} --@@OPTION_IDS@@"
LOOK_CULTURES_PLACEHOLDER = "{} --@@LOOK_CULTURES@@"


def _lua_set(keys):
    return "{" + ", ".join('["%s"] = true' % k for k in keys) + "}"


def _lua_map(mapping):
    return "{" + ", ".join('["%s"] = "%s"' % item for item in mapping.items()) + "}"


def render_script(template, option_ids, look_cultures):
    """look_cultures: {culture key: culture whose devastation look it uses}."""
    for placeholder in (OPTION_IDS_PLACEHOLDER, LOOK_CULTURES_PLACEHOLDER):
        if template.count(placeholder) != 1:
            raise ValueError("template must contain exactly one " + placeholder)
    return (template
            .replace(OPTION_IDS_PLACEHOLDER, _lua_set(str(i) for i in option_ids))
            .replace(LOOK_CULTURES_PLACEHOLDER, _lua_map(look_cultures)))
