"""Readable class palettes.

The class colours in custom_colors.profession_palettes are hand-picked dyes.
Some of them are too dark for the roles they play on the site: colour 3 is
used as text and must reach WCAG AA (4.5:1) against the card background,
colour 2 paints the Optimize button and tints the borders and must at least
be visible against the card. This module lifts a colour's lightness - and
only its lightness, hue and saturation stay - by the smallest amount that
meets the floor, so a dye stays recognisable. Colours that already pass are
returned unchanged, which is the case for most of them and for the default
phthalo blue / ruby red / aureus theme.

The surface mixes mirror static/style.css: the page is colour 1 at the soft
alpha (30%) over black, the card colour 1 at 35% over #12141c, the button
colour 2 at the strong alpha (70%) over black, the border colour 2 at the
soft alpha over #262b3a.
"""

import colorsys

BLACK = (0, 0, 0)
CARD_BASE = (0x12, 0x14, 0x1c)
BORDER_BASE = (0x26, 0x2B, 0x3A)
PAGE_MIX, CARD_MIX, BUTTON_MIX, BORDER_MIX = 0.30, 0.35, 0.70, 0.30

# floors: WCAG AA for normal text; the default theme's own button and border
# contrast for the two surfaces (so every class is at least as clear as it)
TEXT_FLOOR = 4.5
BUTTON_FLOOR = 1.7
BORDER_FLOOR = 1.3


def rgb(value: str) -> tuple[int, int, int]:
    value = value.lstrip("#")[:6]
    return tuple(int(value[i:i + 2], 16) for i in (0, 2, 4))  # type: ignore[return-value]


def hex_of(color) -> str:
    return "#%02x%02x%02x" % tuple(int(round(c)) for c in color)


def mix(a, b, share_a: float):
    """color-mix(in srgb, a share_a, b) - gamma-encoded channels like the browser."""
    return tuple(x * share_a + y * (1 - share_a) for x, y in zip(a, b))


def luminance(color) -> float:
    def channel(v):
        v /= 255
        return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
    r, g, b = (channel(v) for v in color)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a, b) -> float:
    la, lb = luminance(a), luminance(b)
    return (max(la, lb) + 0.05) / (min(la, lb) + 0.05)


def lighter(color, step: float = 0.01):
    h, l, s = colorsys.rgb_to_hls(*(c / 255 for c in color))
    return tuple(c * 255 for c in colorsys.hls_to_rgb(h, min(1.0, l + step), s))


def lift(color, passes, limit: int = 100):
    """The least-lightened version of `color` for which passes() holds."""
    for _ in range(limit):
        if passes(color):
            return color
        color = lighter(color)
    return color


def readable_palette(dark: str, mid: str, bright: str) -> tuple[tuple[str, str, str], list[str]]:
    """(dark, mid, bright) with mid and bright lifted to the floors, and a
    list of notes saying what was lifted (empty when nothing was)."""
    d = rgb(dark)
    page, card = mix(d, BLACK, PAGE_MIX), mix(d, CARD_BASE, CARD_MIX)

    b0 = rgb(bright)
    b = lift(b0, lambda c: min(contrast(c, card), contrast(c, page)) >= TEXT_FLOOR)

    m0 = rgb(mid)
    m = lift(m0, lambda c: contrast(mix(c, BLACK, BUTTON_MIX), card) >= BUTTON_FLOOR
             and contrast(mix(c, BORDER_BASE, BORDER_MIX), card) >= BORDER_FLOOR)

    notes = []
    if hex_of(b) != hex_of(b0):
        notes.append(f"bright {hex_of(b0)} -> {hex_of(b)} for {TEXT_FLOOR}:1 text contrast")
    if hex_of(m) != hex_of(m0):
        notes.append(f"mid {hex_of(m0)} -> {hex_of(m)} for a visible button and border")
    return (dark[:7], hex_of(m), hex_of(b)), notes
