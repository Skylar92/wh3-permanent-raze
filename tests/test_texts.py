from tools.texts import FIELDS, LANGUAGES, TEXTS


def test_all_game_languages_present():
    assert LANGUAGES == ("en", "ru", "ge", "fr", "it", "sp", "pl", "cz", "tr", "br", "kr", "cn", "zh")
    assert set(TEXTS) == set(LANGUAGES)


def test_every_language_has_every_text():
    for lang in LANGUAGES:
        assert set(TEXTS[lang]) == set(FIELDS), lang
        for field, text in TEXTS[lang].items():
            assert text.strip() and "||" not in text, (lang, field)


def test_english_and_russian_wording():
    assert TEXTS["en"]["title"] == "Raze Forever"
    assert TEXTS["ru"]["title"] == "Стереть навсегда"
    assert TEXTS["ru"]["bundle_title"] == "Стёрто навсегда"
