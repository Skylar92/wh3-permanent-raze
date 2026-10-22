"""Data for the ruins-corruption feature: culture defaults, settings, effect keys and MCT texts."""

CORRUPTION_TYPES = ("chaos", "khorne", "nurgle", "slaanesh", "tzeentch", "vampiric", "skaven")
EFFECT_VALUES = ("none", "reduce") + CORRUPTION_TYPES

# Insertion order is the order of the culture rows on the MCT page.
CULTURE_DEFAULTS = {
    "wh_main_chs_chaos": "chaos",
    "wh3_main_dae_daemons": "chaos",
    "wh_dlc08_nor_norsca": "chaos",
    "wh_dlc03_bst_beastmen": "chaos",
    "wh3_dlc23_chd_chaos_dwarfs": "chaos",
    "wh3_main_kho_khorne": "khorne",
    "wh3_main_nur_nurgle": "nurgle",
    "wh3_main_sla_slaanesh": "slaanesh",
    "wh3_main_tze_tzeentch": "tzeentch",
    "wh2_main_skv_skaven": "skaven",
    "wh_main_vmp_vampire_counts": "vampiric",
    "wh2_dlc11_cst_vampire_coast": "vampiric",
    "wh_main_emp_empire": "reduce",
    "wh_main_brt_bretonnia": "reduce",
    "wh_main_dwf_dwarfs": "reduce",
    "wh3_main_ksl_kislev": "reduce",
    "wh3_main_cth_cathay": "reduce",
    "wh2_main_hef_high_elves": "reduce",
    "wh_dlc05_wef_wood_elves": "reduce",
    "wh2_main_lzd_lizardmen": "reduce",
    "wh2_main_def_dark_elves": "none",
    "wh_main_grn_greenskins": "none",
    "wh3_main_ogr_ogre_kingdoms": "none",
    "wh2_dlc09_tmb_tomb_kings": "none",
}

FACTION_OVERRIDES = {
    "wh2_main_def_cult_of_pleasure": "slaanesh",
    "wh3_dlc29_chs_host_of_the_triplets": "nurgle",
}

DAEMONS_CULTURE = "wh3_main_dae_daemons"
DAEMON_PRINCE_FACTION = "wh3_main_dae_daemon_prince"

SETTINGS_DEFAULTS = {
    "mode": "off",
    "ruin_strength": 5,
    "province_strength": 30,
    "multiplier": 100,
    "threshold": 50,
    "daemon_follow_god": False,
}

# key: (min, max, step)
SLIDERS = {
    "ruin_strength": (0, 30, 1),
    "province_strength": (0, 100, 1),
    "multiplier": (0, 300, 10),
    "threshold": (1, 99, 1),
}

RU_PROBE = ("cultures_name_wh_main_emp_empire", "Империя")

EFFECT_SCOPE = "region_to_province_own_unseen"

# text key: (English, Russian)
MCT_TEXTS = {
    "mod_title": ("Raze Forever", "Стереть навсегда"),
    "section_general": ("General", "Общие"),
    "section_cultures": ("Effect of erased ruins by culture", "Эффект руин по культурам"),
    "mode_label": ("Corruption mode", "Режим скверны"),
    "mode_tip": ("When erased ruins spread corruption: never, per erased settlement, or once per province.",
                 "Когда стёртые руины распространяют скверну: никогда, за каждое поселение или за провинцию."),
    "mode_off": ("Off", "Выкл."),
    "mode_per_settlement": ("Per settlement", "За поселение"),
    "mode_per_province": ("Per province", "За провинцию"),
    "ruin_strength_label": ("Ruin strength", "Сила руин"),
    "ruin_strength_tip": ("Corruption added or removed by each erased settlement.",
                          "Скверна, добавляемая или снимаемая каждым стёртым поселением."),
    "province_strength_label": ("Province strength", "Сила провинции"),
    "province_strength_tip": ("Corruption applied once a province counts as erased.",
                              "Скверна, применяемая, когда провинция считается стёртой."),
    "multiplier_label": ("Multiplier, %", "Множитель, %"),
    "multiplier_tip": ("Scales the strength of every effect.",
                       "Масштабирует силу каждого эффекта."),
    "threshold_label": ("Province threshold, %", "Порог провинции, %"),
    "threshold_tip": ("Share of erased settlements after which a province counts as erased.",
                      "Доля стёртых поселений, после которой провинция считается стёртой."),
    "daemon_follow_god_label": ("Daemon Prince follows his god", "Принц демонов следует своему богу"),
    "daemon_follow_god_tip": ("Daemon Prince uses the corruption of the god he ascended to.",
                              "Принц демонов использует скверну бога, к которому вознёсся."),
    "value_none": ("Nothing", "Ничего"),
}


def effect_key(value: str) -> str:
    if value == "reduce":
        return "wh3_main_effect_corruption_reduction_events"
    if value in CORRUPTION_TYPES:
        return f"wh3_main_effect_corruption_{value}_events_bad"
    raise ValueError(f"no corruption effect for {value!r}")


def campaign_defaults() -> dict:
    """Every MCT option key with its default value; shared by the Lua script and the MCT page."""
    defaults = dict(SETTINGS_DEFAULTS)
    for culture, value in CULTURE_DEFAULTS.items():
        defaults["culture_" + culture] = value
    return defaults
