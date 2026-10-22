"""Everything the front end reads that is fixed per deploy: the theme
stylesheet and the JSON documents under /data/. The Flask app serves them
live; generate_site.py writes the very same texts into a static site."""
import json
import os

import pandas as pd

import gw2ceo.general_data as gd
from gw2ceo import builds, custom_colors, theme
from gw2ceo.icons import ensure_icon
from gw2ceo.paths import ICONS


def professions() -> str:
    known = set(gd.traits["profession"].unique())
    return json.dumps([name for name in gd.PROFESSION_ORDER if name in known])


def versioned_icon(filename: str) -> str:
    """Icon URL stamped with the file's mtime: browsers may cache long but
    fetch a fresh copy when the image changes. Missing files are downloaded
    first."""
    ensure_icon(filename)
    path = ICONS / filename
    version = int(os.path.getmtime(path)) if os.path.isfile(path) else 0
    return f"/icons/{filename}?v={version}"


def specializations(profession: str) -> str:
    """The profession's trait lines with icon and banner URLs."""
    table: pd.DataFrame = gd.specializations
    table = table.loc[table["profession"].str.lower() == profession.lower()]

    def spec_icon(row):
        # only elite specs (and professions) have wiki tango icons; core
        # trait lines fall back to their hexagon icon directly
        if row["elite"] and ensure_icon(f"tango_{row['name']}.png"):
            return versioned_icon(f"tango_{row['name']}.png")
        return versioned_icon(f"spec_{row['id']}.png")

    table = table.assign(
        icon=table.apply(spec_icon, axis=1),
        background=table["id"].apply(lambda spec_id: versioned_icon(f"spec_bg_{spec_id}.png")),
    )
    return table.to_json(orient="records")


def traits(profession: str) -> str:
    """The selectable traits and skills of a profession."""
    table: pd.DataFrame = gd.traits
    return table.loc[table["profession"].str.lower() == profession.lower()].to_json(orient="records")


def heal_skills(profession: str) -> str:
    """Healing skills with their K = base/coefficient ratio for the boon
    mode's slider; rows without a profession (the regeneration boon) apply
    to everyone."""
    table: pd.DataFrame = gd.heal_skills
    universal = table["profession"].fillna("") == ""
    return table.loc[universal | (table["profession"].str.lower() == profession.lower())].to_json(orient="records")


def builds_list(library: list[dict]) -> str:
    return json.dumps([builds.summary(build) for build in library])


def build_detail(build: dict) -> str:
    return json.dumps(build)


def theme_css() -> str:
    """CSS variables generated from gw2ceo/custom_colors.py (single source
    of truth), plus one palette block per profession."""
    colors = {name: value for name, value in vars(custom_colors).items()
              if isinstance(value, str) and value.startswith("#")}
    lines = [f"  --{name.replace('_', '-')}: {value[:7]};" for name, value in colors.items()]
    lines += ["  --alpha-strong: 70%;", "  --alpha-mid: 50%;", "  --alpha-soft: 30%;",
              "  --alpha-faint: 10%;"]
    # the three theme roles: dark (backgrounds), mid (buttons, borders),
    # bright (text/headings) - the default until a profession is chosen
    lines += ["  --theme-dark: var(--phthalo-blue);", "  --theme-mid: var(--ruby-red);",
              "  --theme-bright: var(--aureus);"]
    # the glow at the top of the page: the default mixes phthalo blue at the
    # strong alpha; the classes' dark colours are near black, so their glow
    # comes from the mid colour at the soft alpha instead
    lines += ["  --theme-glow: var(--phthalo-blue);", "  --glow-mix: var(--alpha-strong);"]
    css = ":root {\n" + "\n".join(lines) + "\n}\n"
    # the hand-picked dyes, lifted in lightness only where a role would be
    # unreadable (gw2ceo/theme.py); the comment documents every lift
    for profession, palette in custom_colors.profession_palettes.items():
        (dark, mid, bright), notes = theme.readable_palette(*palette)
        comment = f"  /* {'; '.join(notes)} */\n" if notes else ""
        css += (f':root[data-profession="{profession}"] {{\n{comment}'
                f"  --theme-dark: {dark};\n  --theme-mid: {mid};\n"
                f"  --theme-bright: {bright};\n"
                f"  --theme-glow: {mid};\n  --glow-mix: var(--alpha-soft);\n}}\n")
    return css
