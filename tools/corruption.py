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
    "allow_rebuild": False,
    "ai_erase": False,
    "ai_erase_chance": 25,
    "mode": "off",
    "ruin_strength": 5,
    "province_strength": 30,
    "multiplier": 100,
    "threshold": 50,
    "daemon_follow_god": False,
}

# Per-culture AI erase chance: one dropdown per culture, in the order of CULTURE_DEFAULTS.
# "general" (the default) uses the general AI erase chance; "0" means the culture never erases.
AI_CHANCE_PREFIX = "ai_chance_"
AI_CHANCE_DEFAULT = "general"
AI_CHANCE_VALUES = (AI_CHANCE_DEFAULT,) + tuple(str(p) for p in range(0, 101, 5))

# key: (min, max, step)
SLIDERS = {
    "ai_erase_chance": (1, 100, 1),
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
    "mod_description": ("Optionally lets players rebuild erased ruins, lets the AI erase ruins too and lets erased "
                        "ruins spread or cleanse corruption. Settings apply per campaign.",
                        "По желанию: игрок может восстанавливать стёртые руины, ИИ тоже может их стирать, а руины "
                        "могут распространять или снимать скверну. Настройки действуют для кампании."),
    "page_general": ("General", "Общие"),
    "page_ai": ("AI erasing", "Стирание ИИ"),
    "page_corruption": ("Corruption", "Скверна"),
    "section_general": ("General", "Общие"),
    "section_ai": ("AI erasing", "Стирание ИИ"),
    "section_ai_cultures": ("AI erase chance by culture", "Шанс стирания ИИ по культурам"),
    "section_corruption": ("Corruption of erased ruins", "Скверна стёртых руин"),
    "section_cultures": ("Effect of erased ruins by culture", "Эффект руин по культурам"),
    "ai_culture_tip": ("Chance that this culture's AI erases the ruins it razes. General: use the general AI chance. "
                       "0%: this culture never erases.",
                       "Шанс, что ИИ этой культуры сотрёт разорённые руины. «Общий»: общий шанс ИИ. "
                       "0%: эта культура никогда не стирает."),
    "ai_culture_general": ("General", "Общий"),
    "lock_ai_off": ("Tick \"The AI erases ruins forever too\" above first.",
                    "Сначала включите «ИИ тоже стирает руины навсегда» выше."),
    "lock_mode_off": ("Corruption mode is Off.", "Режим скверны выключен."),
    "lock_mode_per_settlement": ("Not used in Per settlement mode.", "Не используется в режиме «За поселение»."),
    "lock_mode_per_province": ("Not used in Per province mode.", "Не используется в режиме «За провинцию»."),
    "allow_rebuild_label": ("Players can rebuild erased ruins", "Игрок может восстанавливать стёртые руины"),
    "allow_rebuild_tip": ("On your turn an army in or next to the ruins' region can colonise them as usual. "
                          "The AI never can.",
                          "В ваш ход армия в регионе руин или рядом может колонизировать их как обычно. "
                          "ИИ не может никогда."),
    "ai_erase_label": ("The AI erases ruins forever too", "ИИ тоже стирает руины навсегда"),
    "ai_erase_tip": ("Every settlement the AI razes may be erased forever, by the chances below. "
                     "Warning: the result may be insane, pure chaos. Chaos and Beastmen will love it; "
                     "your campaign might not.",
                     "Каждое поселение, разорённое ИИ, может быть стёрто навсегда с шансами ниже. "
                     "Внимание: результат может быть безумным, чистый хаос. Хаосу и зверолюдам понравится, "
                     "вашей кампании — не факт."),
    "ai_erase_chance_label": ("AI erase chance, %", "Шанс стирания ИИ, %"),
    "ai_erase_chance_tip": ("Chance that an AI raze erases the ruins forever, for every culture left at General below.",
                            "Шанс, что разорение ИИ сотрёт руины навсегда, для всех культур с «Общий» ниже."),
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
    for culture in CULTURE_DEFAULTS:
        defaults[AI_CHANCE_PREFIX + culture] = AI_CHANCE_DEFAULT
    return defaults
