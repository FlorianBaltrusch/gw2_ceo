"""Self-healing image cache.

assets/icons/ is gitignored, so a fresh clone has none of the images. Any
missing file is downloaded on first request, resolving its source from the
committed CSVs (trait icons, specialization icons/banners), the GW2 API
(profession icons, any trait/skill by id for the builds pages) or the wiki
(tango icons). generate_traits.py pre-warms
the same cache in bulk.
"""

import os
import re

import numpy as np
import requests
from PIL import Image

import gw2ceo.general_data as gd
from gw2ceo.api import get_api_data

ICON_DIR = os.path.join("assets", "icons")
WIKI_API = "https://wiki.guildwars2.com/api.php"

# names the wiki has no tango icon for (avoids repeating lookups)
_known_missing: set[str] = set()


# Four banners (the Mesmer core lines) were exported with a piece of the
# in-game panel frame still in them: a purple band along the top and a
# diagonal frame on the right, Inspiration even bleeds into the next
# picture. The brightness trim cannot see that, so these get a fixed crop
# box first (left, top, right, bottom in the original 1024x256 pixels;
# checked by eye against the images, 2026-09-21).
BANNER_CROPS = {
    1: (0, 26, 665, 256),    # Dueling
    45: (0, 28, 730, 256),   # Chaos
    23: (0, 28, 648, 256),   # Inspiration
    24: (0, 0, 830, 256),    # Illusions
}


def crop_banner_bleed(path):
    """Apply the fixed crop of BANNER_CROPS to spec_bg_<id>.png files that
    still carry the panel frame (idempotent: a cropped file is smaller
    than its box and is left alone)."""
    match = re.fullmatch(r"spec_bg_(\d+)\.png", os.path.basename(path))
    if not match or int(match.group(1)) not in BANNER_CROPS:
        return
    left, top, right, bottom = BANNER_CROPS[int(match.group(1))]
    image = Image.open(path)
    if image.width > right or (top and image.height == bottom):
        image.crop((left, top, min(right, image.width), min(bottom, image.height))).save(path)


def trim_banner_border(path, threshold=18, content_fraction=0.01, min_mean=12):
    """The spec banners bleed into the in-game UI panel and pad the painted
    area with fully transparent or near-black margins; crop to the painted
    area (idempotent). A row/column only counts as content if more than 1%
    of its pixels are bright and visible AND its mean brightness is not
    near black, so a few stray specks in a black region do not stop the
    trim - while dark artwork in the middle of a banner stays safe because
    only the border is removed."""
    crop_banner_bleed(path)
    image = Image.open(path).convert("RGBA")
    pixels = np.asarray(image)
    visible = pixels[..., 3] > 8
    brightness = pixels[..., :3].max(axis=2) * visible
    content = (brightness > threshold) & visible

    row_has_content = (content.mean(axis=1) > content_fraction) & (brightness.mean(axis=1) > min_mean)
    col_has_content = (content.mean(axis=0) > content_fraction) & (brightness.mean(axis=0) > min_mean)
    if not row_has_content.any() or not col_has_content.any():
        return
    top, bottom = np.flatnonzero(row_has_content)[[0, -1]]
    left, right = np.flatnonzero(col_has_content)[[0, -1]]
    box = (int(left), int(top), int(right) + 1, int(bottom) + 1)
    if box != (0, 0, image.width, image.height):
        image.crop(box).save(path)


def tango_icon_url(name: str) -> str | None:
    """URL of the wiki's flat tango icon for a profession or elite spec,
    preferring the largest size the wiki hosts."""
    for size in (200, 48):
        response = requests.get(WIKI_API, params={
            "action": "query", "format": "json", "prop": "imageinfo",
            "iiprop": "url", "titles": f"File:{name} tango icon {size}px.png",
        }, timeout=15).json()
        for page in response["query"]["pages"].values():
            if "imageinfo" in page:
                return page["imageinfo"][0]["url"]
    return None


def _resolve(filename: str):
    """(source url, needs banner trim) for a cache filename, (None, False)
    when the name matches nothing we know."""
    specs = gd.specializations

    if match := re.fullmatch(r"spec_bg_(\d+)\.png", filename):
        rows = specs.loc[specs["id"] == int(match.group(1)), "background"]
        return (rows.iloc[0], True) if len(rows) else (None, False)

    if match := re.fullmatch(r"spec_(\d+)\.png", filename):
        rows = specs.loc[specs["id"] == int(match.group(1)), "icon"]
        return (rows.iloc[0], False) if len(rows) else (None, False)

    # any trait or skill by API id (the builds page shows whole trait lines
    # and skill bars, not just the stat-relevant rows of traits.csv)
    if match := re.fullmatch(r"trait_(\d+)\.png", filename):
        return (get_api_data(f"traits/{match.group(1)}").get("icon"), False)

    if match := re.fullmatch(r"skill_(\d+)\.png", filename):
        return (get_api_data(f"skills/{match.group(1)}").get("icon"), False)

    if match := re.fullmatch(r"pet_(\d+)\.png", filename):
        return (get_api_data(f"pets/{match.group(1)}").get("icon"), False)

    if match := re.fullmatch(r"prof_([A-Za-z]+)\.png", filename):
        return (get_api_data(f"professions/{match.group(1)}").get("icon_big"), False)

    if match := re.fullmatch(r"tango_([A-Za-z]+)\.png", filename):
        name = match.group(1)
        if name in _known_missing:
            return (None, False)
        url = tango_icon_url(name)
        if url is None:
            _known_missing.add(name)
        return (url, False)

    if match := re.fullmatch(r"(\d+)\.png", filename):
        rows = gd.traits.loc[gd.traits["id"] == int(match.group(1)), "icon"]
        return (rows.iloc[0], False) if len(rows) else (None, False)

    return (None, False)


def ensure_icon(filename: str) -> bool:
    """True when the file exists in the cache, downloading it first if the
    source is known; False (never an exception) otherwise."""
    path = os.path.join(ICON_DIR, filename)
    if os.path.isfile(path):
        return True
    try:
        url, needs_trim = _resolve(filename)
        if not url:
            return False
        os.makedirs(ICON_DIR, exist_ok=True)
        with open(path, "wb") as file:
            file.write(requests.get(url, timeout=15).content)
        if needs_trim:
            trim_banner_border(path)
        return True
    except (requests.RequestException, OSError):
        return False
