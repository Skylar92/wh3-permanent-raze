"""Draw the Workshop preview: a burning, razed settlement under smoke.

usage: python -m tools.preview   (writes dist/permanent_raze.png and dist/permanent_raze_<lang>.png)
"""
import random

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

SIZE = 512
GROUND = 430
FONT = r"C:\Windows\Fonts\georgiab.ttf"
FONT_BADGE = r"C:\Windows\Fonts\seguisb.ttf"
# Segoe has no Hangul or Han glyphs; these Windows fonts do.
FONT_BADGE_CJK = {
    "한국어": r"C:\Windows\Fonts\malgunbd.ttf",
    "简体中文": r"C:\Windows\Fonts\msyhbd.ttc",
    "繁體中文": r"C:\Windows\Fonts\msjhbd.ttc",
}
INK = (9, 6, 5, 255)

LANGUAGE_NAMES = {
    "en": "English", "ru": "Русский", "ge": "Deutsch", "fr": "Français", "it": "Italiano", "sp": "Español",
    "pl": "Polski", "cz": "Čeština", "tr": "Türkçe", "br": "Português (BR)", "kr": "한국어",
    "cn": "简体中文", "zh": "繁體中文",
}


def _sky(rng):
    y = np.linspace(0.0, 1.0, SIZE)[:, None]
    top, mid, low = np.array([10, 7, 7]), np.array([52, 16, 10]), np.array([196, 70, 16])
    t = np.clip(y / 0.78, 0, 1)
    col = np.where(t < 0.6, top + (mid - top) * (t / 0.6), mid + (low - mid) * ((t - 0.6) / 0.4))
    img = np.repeat(col[:, None, :], SIZE, axis=1).reshape(SIZE, SIZE, 3)
    img = img + rng.normal(0, 3.0, img.shape)
    return Image.fromarray(np.clip(img, 0, 255).astype("uint8")).convert("RGBA")


def _glow(fires):
    layer = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    for x, y, r in fires:
        for k in range(10, 0, -1):
            rr = r * k / 3
            a = int(26 * (11 - k) / 10)
            d.ellipse((x - rr, y - rr * 0.8, x + rr, y + rr * 0.8), fill=(255, 110, 20, a))
    return layer.filter(ImageFilter.GaussianBlur(18))


def _smoke(fires, rng):
    layer = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    for x, y, r in fires:
        cx, cy = float(x), float(y)
        for step in range(60):
            cx += rng.uniform(-5, 10)  # wind to the right
            cy -= rng.uniform(5, 9)
            rad = r * 0.6 + step * 2.4 + rng.uniform(0, 10)
            lit = max(0.0, 1.0 - step / 18)  # fire light fades with height
            base = rng.uniform(70, 110)
            colour = (int(base + 110 * lit), int(base * 0.9 + 36 * lit), int(base * 0.84), int(max(0, 215 - step * 3.0)))
            d.ellipse((cx - rad, cy - rad, cx + rad, cy + rad), fill=colour)
    return layer.filter(ImageFilter.GaussianBlur(7))


def _flames(fires, rng):
    layer = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    for x, y, r in fires:
        for colour, scale in (((255, 80, 10, 220), 1.0), ((255, 170, 40, 230), 0.65), ((255, 236, 150, 240), 0.33)):
            for _ in range(7):
                w = r * scale * rng.uniform(0.35, 0.7)
                h = r * scale * rng.uniform(1.4, 2.6)
                fx = x + rng.uniform(-r, r) * 0.8
                d.polygon([(fx - w, y), (fx + w, y), (fx + rng.uniform(-w, w), y - h)], fill=colour)
    return layer.filter(ImageFilter.GaussianBlur(2.2))


def _jagged(d, x0, x1, base, top, rng, teeth=9):
    pts = [(x0, base)]
    for i in range(teeth + 1):
        px = x0 + (x1 - x0) * i / teeth
        pts.append((px, top + rng.uniform(-14, 24)))
    pts.append((x1, base))
    d.polygon(pts, fill=INK)


def _ruins(rng):
    layer = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    # ground and rubble
    ground = [(0, SIZE), (0, GROUND)]
    for x in range(0, SIZE + 16, 16):
        ground.append((x, GROUND + rng.uniform(-6, 5)))
    ground.append((SIZE, SIZE))
    d.polygon(ground, fill=INK)
    for _ in range(26):
        x, s = rng.uniform(0, SIZE), rng.uniform(4, 13)
        d.polygon([(x, GROUND + 4), (x + s, GROUND - s * 0.8), (x + 2 * s, GROUND + 4)], fill=INK)
    # broken walls
    _jagged(d, 30, 150, GROUND + 4, 338, rng)
    _jagged(d, 300, 380, GROUND + 4, 360, rng, teeth=6)
    _jagged(d, 410, 500, GROUND + 4, 324, rng, teeth=7)
    # the broken keep: tall tower with a sheared-off top
    d.polygon([(180, GROUND + 4), (180, 222), (196, 210), (208, 226), (226, 190), (244, 216),
               (258, 206), (262, GROUND + 4)], fill=INK)
    # gothic windows glowing from the fire inside
    for wx, wy in ((205, 280), (236, 280), (221, 344)):
        d.rectangle((wx - 6, wy, wx + 6, wy + 22), fill=(230, 96, 24, 255))
        d.pieslice((wx - 6, wy - 6, wx + 6, wy + 6), 180, 360, fill=(230, 96, 24, 255))
    d.rectangle((60, 372, 72, 392), fill=(200, 80, 20, 255))
    # charred beams leaning out of the ruins
    for (x0, y0, x1, y1, w) in ((300, 368, 352, 300, 5), (342, 374, 300, 324, 4), (120, 350, 166, 290, 5),
                                (446, 338, 478, 274, 4)):
        d.line((x0, y0, x1, y1), fill=INK, width=w)
    return layer


def _foreground(rng):
    """Glowing cracks in the scorched ground and a few big dark stones up front."""
    layer = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    rim = [(x, GROUND - 1 + rng.uniform(-2, 2)) for x in range(0, SIZE + 8, 8)]
    d.line(rim, fill=(255, 110, 30, 150), width=2)
    for _ in range(6):
        x, y = rng.uniform(20, SIZE - 20), rng.uniform(GROUND + 14, SIZE - 30)
        pts = [(x, y)]
        for _ in range(4):
            x += rng.uniform(-18, 18)
            y += rng.uniform(-4, 6)
            pts.append((x, y))
        d.line(pts, fill=(255, 120, 30, 200), width=2)
    glow = layer.filter(ImageFilter.GaussianBlur(3))
    glow.alpha_composite(layer)
    d = ImageDraw.Draw(glow)
    for x, w, h in ((-10, 120, 46), (150, 70, 26), (400, 130, 52)):
        d.ellipse((x, SIZE - h, x + w, SIZE + h), fill=INK)
    return glow


def _embers(rng):
    layer = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    for _ in range(140):
        x, y = rng.uniform(0, SIZE), rng.uniform(110, GROUND)
        s = rng.uniform(0.6, 1.8)
        d.ellipse((x - s, y - s, x + s, y + s), fill=(255, int(rng.uniform(120, 220)), 60, int(rng.uniform(120, 255))))
    return layer


def _vignette():
    y, x = np.ogrid[:SIZE, :SIZE]
    dist = np.sqrt((x - SIZE / 2) ** 2 + (y - SIZE / 2) ** 2) / (SIZE / 1.35)
    alpha = np.clip((dist - 0.45) * 330, 0, 210).astype("uint8")
    v = np.zeros((SIZE, SIZE, 4), "uint8")
    v[..., 3] = alpha
    return Image.fromarray(v, "RGBA")


def _title(img):
    d = ImageDraw.Draw(img)
    font = ImageFont.truetype(FONT, 50)
    text = "RAZE FOREVER"
    box = d.textbbox((0, 0), text, font=font)
    x, y = (SIZE - (box[2] - box[0])) / 2, 26
    shadow = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(shadow).text((x, y + 2), text, font=font, fill=(0, 0, 0, 255), stroke_width=6, stroke_fill=(0, 0, 0, 255))
    img.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(4)))
    d.text((x, y), text, font=font, fill=(236, 214, 170, 255), stroke_width=1, stroke_fill=(120, 40, 10, 255))
    line_y = y + (box[3] - box[1]) + 18
    d.line(((SIZE / 2 - 120, line_y), (SIZE / 2 + 120, line_y)), fill=(180, 60, 20, 255), width=2)


def badge_font_path(label):
    return FONT_BADGE_CJK.get(label, FONT_BADGE)


def _badge(img, label):
    d = ImageDraw.Draw(img)
    font = ImageFont.truetype(badge_font_path(label), 22)
    box = d.textbbox((0, 0), label, font=font)
    w, h = box[2] - box[0] + 28, box[3] - box[1] + 18
    x, y = SIZE - w - 16, SIZE - h - 16
    d.rounded_rectangle((x, y, x + w, y + h), radius=8, fill=(20, 10, 8, 225), outline=(190, 70, 20, 255), width=2)
    d.text((x + 14, y + 7 - box[1]), label, font=font, fill=(236, 214, 170, 255))


def make_preview(language_label=None):
    rng = random.Random(1142710)
    nrng = np.random.default_rng(1142710)
    fires = [(214, 412, 40), (88, 418, 30), (342, 420, 28), (466, 414, 24)]
    img = _sky(nrng)
    img.alpha_composite(_glow(fires))
    img.alpha_composite(_smoke(fires, rng))
    img.alpha_composite(_flames(fires, rng))
    ruins = _ruins(rng)
    img.alpha_composite(ruins)
    img.alpha_composite(_foreground(rng))
    img.alpha_composite(_flames([(f[0], f[1] + 10, f[2] * 0.6) for f in fires], rng))
    img.alpha_composite(_embers(rng))
    img.alpha_composite(_vignette())
    _title(img)
    if language_label:
        _badge(img, language_label)
    return img.convert("RGB")


def save_preview(img, path):
    img.save(path, "PNG", optimize=True)


def main():
    from tools.paths import ROOT
    dist = ROOT / "dist"
    dist.mkdir(exist_ok=True)
    save_preview(make_preview(), dist / "permanent_raze.png")
    for code, name in LANGUAGE_NAMES.items():
        save_preview(make_preview(name), dist / ("permanent_raze_%s.png" % code))
    print("previews written to %s" % dist)


if __name__ == "__main__":
    main()
