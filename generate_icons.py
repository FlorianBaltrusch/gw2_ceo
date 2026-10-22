"""The site's icon in every form: favicon (.ico, PNG, apple-touch-icon) and
the BIMI logo (SVG Tiny Portable/Secure) for e-mail inboxes. One design:
the brand's gold "C" in the site's font on phthalo blue.

    PYTHONPATH=. .venv/bin/python generate_icons.py

Needs pillow for the bitmaps and fonttools + brotli (dev only, not in
requirements.txt) to turn the glyph into an SVG path."""
from PIL import Image, ImageDraw, ImageFont

GOLD = (0xED, 0xB2, 0x27)
BLUE = (0x00, 0x1C, 0x67)               # phthalo blue, the site's background colour
RING = tuple(round(c * 0.70) for c in GOLD)
FONT = "static/fonts/LibertinusSerif-Semibold.woff2"


def render(size):
    """The favicon at one size: rounded blue square, gold ring, centred C."""
    scale = 8
    s = size * scale
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    pad = round(s * 0.02)
    draw.rounded_rectangle((pad, pad, s - pad, s - pad), radius=round(s * 0.22), fill=BLUE + (255,))
    ring = round(s * 0.05)
    draw.rounded_rectangle((pad + ring // 2, pad + ring // 2, s - pad - ring // 2, s - pad - ring // 2),
                           radius=round(s * 0.2), outline=RING + (255,), width=ring)
    font = ImageFont.truetype(FONT, round(s * 0.82))
    box = draw.textbbox((0, 0), "C", font=font)
    w, h = box[2] - box[0], box[3] - box[1]
    draw.text(((s - w) / 2 - box[0], (s - h) / 2 - box[1]), "C", font=font, fill=GOLD + (255,))
    return img.resize((size, size), Image.LANCZOS)


def favicons():
    icons = {size: render(size) for size in (16, 32, 48, 180)}
    icons[32].save("static/favicon.png")
    icons[180].save("static/apple-touch-icon.png")
    icons[48].save("static/favicon.ico", format="ICO", sizes=[(16, 16), (32, 32), (48, 48)],
                   append_images=[icons[16], icons[32]])


def bimi_svg():
    """SVG Tiny P/S as BIMI requires: version 1.2, baseProfile tiny-ps, a
    <title>, a square viewBox, a solid (non-transparent) background, no
    text, scripts, styles or external references - the C is a path."""
    from fontTools.pens.svgPathPen import SVGPathPen
    from fontTools.pens.transformPen import TransformPen
    from fontTools.ttLib import TTFont

    font = TTFont(FONT)
    glyph_set = font.getGlyphSet()
    glyph = glyph_set[font.getBestCmap()[ord("C")]]
    upem = font["head"].unitsPerEm
    # the glyph's own box, to centre it in the square
    from fontTools.pens.boundsPen import BoundsPen
    bounds = BoundsPen(glyph_set)
    glyph.draw(bounds)
    x_min, y_min, x_max, y_max = bounds.bounds
    size = 512
    height = size * 0.62                     # the C's cap height in the square
    scale = height / (y_max - y_min)
    tx = (size - (x_max - x_min) * scale) / 2 - x_min * scale
    ty = (size + (y_max - y_min) * scale) / 2 + y_min * scale   # y flips: font up, SVG down
    pen = SVGPathPen(glyph_set, ntos=lambda v: f"{v:.1f}")
    glyph.draw(TransformPen(pen, (scale, 0, 0, -scale, tx, ty)))
    ring = size * 0.05
    inset = size * 0.08
    svg = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" version="1.2" baseProfile="tiny-ps" viewBox="0 0 {size} {size}">
  <title>Critical Effect Optimizer</title>
  <rect width="{size}" height="{size}" fill="#001c67"/>
  <rect x="{inset:.0f}" y="{inset:.0f}" width="{size - 2 * inset:.0f}" height="{size - 2 * inset:.0f}" rx="{size * 0.16:.0f}" fill="none" stroke="#a67c1b" stroke-width="{ring:.0f}"/>
  <path d="{pen.getCommands()}" fill="#edb227"/>
</svg>
'''
    with open("static/bimi-logo.svg", "w") as file:
        file.write(svg)


if __name__ == "__main__":
    favicons()
    bimi_svg()
    print("written: static/favicon.ico, static/favicon.png, static/apple-touch-icon.png, static/bimi-logo.svg")
