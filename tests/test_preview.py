from tools.preview import make_preview, save_preview


def test_preview_size_and_weight(tmp_path):
    out = tmp_path / "permanent_raze.png"
    save_preview(make_preview(), out)
    assert make_preview().size == (512, 512)
    assert out.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"
    assert out.stat().st_size < 1_000_000


def test_language_badge_changes_image():
    assert make_preview("Русский").tobytes() != make_preview().tobytes()


def test_badge_fonts_cover_cjk():
    from tools.preview import badge_font_path
    assert badge_font_path("한국어").endswith("malgunbd.ttf")
    assert badge_font_path("简体中文").endswith("msyhbd.ttc")
    assert badge_font_path("繁體中文").endswith("msjhbd.ttc")
    assert badge_font_path("Русский").endswith("seguisb.ttf")


def test_every_patch_language_has_a_badge():
    from tools.preview import LANGUAGE_NAMES
    from tools.texts import LANGUAGES
    assert set(LANGUAGE_NAMES) == set(LANGUAGES)
