from tools.preview import make_preview, save_preview


def test_preview_size_and_weight(tmp_path):
    out = tmp_path / "permanent_raze.png"
    save_preview(make_preview(), out)
    assert make_preview().size == (512, 512)
    assert out.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"
    assert out.stat().st_size < 1_000_000

