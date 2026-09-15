"""Generate assets/traits.csv from the official GW2 API.

Pulls every specialization trait and profession skill for all nine professions,
extracts the facts that affect Power, Precision, Ferocity (API: "CritDamage"),
Vitality, Toughness or critical chance/damage, and writes one row per effect.

Rows with review=True need a manual pass against the wiki:
  - rows where the same fact appears with several values are usually the
    PvE / WvW-PvP split; keep the PvE value.
  - Buff facts (signet passives, stacking trait buffs) carry no numbers in
    the API; their value is left empty and must be filled in by hand.
  - rows mentioning pets may not apply to the player at all.

Manual decisions live in assets/trait_overrides.csv (same columns, minus
icon). Any id present there replaces ALL generated rows for that id; an
override row with effect="drop" removes the id entirely. This keeps the
review work stable across regenerations. Icons (official render-service
URLs) are attached by id after the override merge, so overrides never need
to carry them.

Usage:  python generate_traits.py   (run from the repository root)
"""

import os
import re

import numpy as np
import pandas as pd
import requests
from PIL import Image

from gw2ceo.api import get_api_data, get_api_data_bulk

WIKI_API = "https://wiki.guildwars2.com/api.php"

OVERRIDES_PATH = os.path.join("assets", "trait_overrides.csv")

ATTR_MAP = {
    "Power": "power",
    "Precision": "precision",
    "CritDamage": "ferocity",
    "Vitality": "vitality",
    "Toughness": "toughness",
}

# standard boons a trait may apply; their stat effect is handled by the
# fury/might toggles of the optimizer, not by trait rows
BOONS = {
    "Aegis", "Alacrity", "Fury", "Might", "Protection", "Quickness",
    "Regeneration", "Resistance", "Resolution", "Stability", "Swiftness",
    "Vigor",
}

ATTR_WORDS = re.compile(
    r"(?i)\b(power|precision|ferocity|vitality|critical chance|critical damage)\b"
)
# phrases that would otherwise false-positive the attribute regex
ATTR_NOISE = re.compile(r"(?i)healing power|condition damage|condition duration")
ALL_ATTRIBUTES = re.compile(r"(?i)(\d+) to All Attributes")
# AttributeAdjust facts that are outgoing damage numbers, not player stats
DAMAGE_FACT = re.compile(r"(?i)siphon|life steal|damage")


def strip_markup(text: str) -> str:
    return re.sub(r"<[^>]*>", " ", text or "").replace("\n", " ").strip()


def extract_facts(facts):
    """Yield (effect, source, value, note, review) tuples for relevant facts."""
    for fact in facts:
        fact_type = fact.get("type")

        if fact_type == "AttributeAdjust":
            effect = ATTR_MAP.get(fact.get("target"))
            if effect and not DAMAGE_FACT.search(fact.get("text", "")):
                yield effect, "", fact.get("value"), fact.get("text", ""), False

        elif fact_type == "BuffConversion":
            effect = ATTR_MAP.get(fact.get("target"))
            source = ATTR_MAP.get(fact.get("source"))
            if effect and source:
                yield effect, source, fact["percent"] / 100, fact.get("text", ""), False

        elif fact_type == "Percent":
            text = fact.get("text", "")
            if text == "Critical Chance Increase":
                yield "crit_chance", "", fact["percent"], text, True
            elif text == "Critical Damage Increase":
                yield "crit_damage_pct", "", fact["percent"], text, True
            elif "Attribute Increase" in text:
                yield "all_stats_pct", "", fact["percent"], text, True

        elif fact_type in ("Buff", "PrefixedBuff"):
            if fact.get("status", "") in BOONS:
                continue
            description = fact.get("description", "") or ""
            note = f"{fact.get('status', '')}: {strip_markup(description)[:100]}"

            flat_all = ALL_ATTRIBUTES.search(description)
            if flat_all:
                yield "all_stats_flat", "", float(flat_all.group(1)), note, True
                continue

            cleaned = ATTR_NOISE.sub(" ", description)
            matches = list(dict.fromkeys(m.lower() for m in ATTR_WORDS.findall(cleaned)))
            for match in matches:
                effect = {
                    "critical chance": "crit_chance",
                    "critical damage": "crit_damage_pct",
                }.get(match, match)
                yield effect, "", None, note, True


def download_icons(df):
    """Cache every referenced icon locally as assets/icons/<id>.png.

    Files that already exist are kept, so this only downloads new icons."""
    icon_dir = os.path.join("assets", "icons")
    os.makedirs(icon_dir, exist_ok=True)
    referenced = df[df["icon"] != ""][["id", "icon"]].drop_duplicates()
    downloaded = 0
    for row in referenced.itertuples():
        path = os.path.join(icon_dir, f"{row.id}.png")
        if not os.path.isfile(path):
            with open(path, "wb") as file:
                file.write(requests.get(row.icon).content)
            downloaded += 1
    print(f"icons: {len(referenced)} referenced, {downloaded} newly downloaded"
          f" -> {icon_dir}/<id>.png")


def generate_specializations():
    """Write assets/specializations.csv and cache the spec images locally.

    Per specialization the API provides a small icon and a wide background
    banner; they land in assets/icons/ as spec_<id>.png and spec_bg_<id>.png
    for the website's elite-specialization picker."""
    rows = []
    icon_dir = os.path.join("assets", "icons")
    os.makedirs(icon_dir, exist_ok=True)
    for prof_name in get_api_data("professions"):
        profession = get_api_data(f"professions/{prof_name}")
        prof_icon = os.path.join(icon_dir, f"prof_{prof_name}.png")
        if profession.get("icon_big") and not os.path.isfile(prof_icon):
            with open(prof_icon, "wb") as file:
                file.write(requests.get(profession["icon_big"]).content)
        for spec_id in profession["specializations"]:
            spec = get_api_data(f"specializations/{spec_id}")
            rows.append({
                "id": spec["id"],
                "profession": prof_name,
                "name": spec["name"],
                "elite": spec["elite"],
                "icon": spec.get("icon", ""),
                "background": spec.get("background", ""),
            })
    df = pd.DataFrame(rows)
    df.to_csv("assets/specializations.csv", index=False)

    downloaded = 0
    for row in df.to_dict("records"):
        for prefix, url in (("spec_", row["icon"]), ("spec_bg_", row["background"])):
            path = os.path.join(icon_dir, f"{prefix}{row['id']}.png")
            if url and not os.path.isfile(path):
                with open(path, "wb") as file:
                    file.write(requests.get(url).content)
                downloaded += 1
            if prefix == "spec_bg_" and os.path.isfile(path):
                trim_banner_border(path)
    print(f"specializations: {len(df)} rows, {downloaded} images newly downloaded")

    download_tango_icons(
        list(get_api_data("professions")) + df[df["elite"]]["name"].tolist()
    )


def trim_banner_border(path, threshold=18, content_fraction=0.01):
    """The spec banners bleed into the in-game UI panel and pad the painted
    area with fully transparent or near-black margins; crop to the painted
    area (idempotent). A row/column only counts as content if more than 1%
    of its pixels are bright and visible, so a few stray specks in a black
    region do not stop the trim - while dark artwork in the middle of a
    banner stays safe because only the border is removed."""
    image = Image.open(path).convert("RGBA")
    pixels = np.asarray(image)
    content = (pixels[..., :3].max(axis=2) > threshold) & (pixels[..., 3] > 8)

    row_has_content = content.mean(axis=1) > content_fraction
    col_has_content = content.mean(axis=0) > content_fraction
    if not row_has_content.any() or not col_has_content.any():
        return
    top, bottom = np.flatnonzero(row_has_content)[[0, -1]]
    left, right = np.flatnonzero(col_has_content)[[0, -1]]
    box = (int(left), int(top), int(right) + 1, int(bottom) + 1)
    if box != (0, 0, image.width, image.height):
        image.crop(box).save(path)


def download_tango_icons(names, sizes=(200, 48)):
    """Fetch the wiki's flat 'tango' icons for professions and elite
    specializations into assets/icons/tango_<Name>.png, preferring the
    largest available size."""
    icon_dir = os.path.join("assets", "icons")
    missing = [n for n in names
               if not os.path.isfile(os.path.join(icon_dir, f"tango_{n}.png"))]
    downloaded = 0
    for size in sizes:
        if not missing:
            break
        titles = "|".join(f"File:{name} tango icon {size}px.png" for name in missing)
        response = requests.get(WIKI_API, params={
            "action": "query", "format": "json", "prop": "imageinfo",
            "iiprop": "url", "titles": titles,
        }).json()
        found = {}
        for page in response["query"]["pages"].values():
            if "imageinfo" in page:
                name = page["title"].removeprefix("File:").removesuffix(f" tango icon {size}px.png")
                found[name] = page["imageinfo"][0]["url"]
        for name, url in found.items():
            path = os.path.join(icon_dir, f"tango_{name}.png")
            with open(path, "wb") as file:
                file.write(requests.get(url).content)
            downloaded += 1
        missing = [n for n in missing if n not in found]
    print(f"tango icons: {downloaded} newly downloaded, unresolved: {missing or 'none'}")


def spec_name(spec_id) -> str:
    if not spec_id:
        return ""
    return get_api_data(f"specializations/{spec_id}")["name"]


def main():
    rows = []
    icons = {}
    trait_slots = {}
    trait_tiers = {}
    trait_positions = {}

    for prof_name in get_api_data("professions"):
        profession = get_api_data(f"professions/{prof_name}")

        for spec_id in profession["specializations"]:
            spec = get_api_data(f"specializations/{spec_id}")
            trait_ids = spec["minor_traits"] + spec["major_traits"]
            for trait in get_api_data_bulk("traits", trait_ids):
                icons[trait["id"]] = trait.get("icon", "")
                trait_slots[trait["id"]] = trait.get("slot", "")
                trait_tiers[trait["id"]] = trait.get("tier", "")
                trait_positions[trait["id"]] = trait.get("order", "")
                for effect, source, value, note, review in extract_facts(trait.get("facts", [])):
                    rows.append({
                        "id": trait["id"],
                        "kind": "trait",
                        "profession": prof_name,
                        "specialization": spec["name"],
                        "elite": spec["elite"],
                        "slot": trait.get("slot", ""),
                        "tier": trait.get("tier", ""),
                        "name": trait["name"],
                        "effect": effect,
                        "source": source,
                        "value": value,
                        "note": note,
                        "review": review,
                        "description": strip_markup(trait.get("description", ""))[:160],
                    })

        skill_ids = [s["id"] for s in profession.get("skills", [])]
        for skill in get_api_data_bulk("skills", skill_ids):
            if skill.get("type") not in ("Heal", "Utility", "Elite"):
                continue
            icons[skill["id"]] = skill.get("icon", "")
            for effect, source, value, note, review in extract_facts(skill.get("facts", [])):
                if effect == "toughness":
                    continue
                rows.append({
                    "id": skill["id"],
                    "kind": "skill",
                    "profession": prof_name,
                    "specialization": spec_name(skill.get("specialization")),
                    "elite": bool(skill.get("specialization")),
                    "slot": skill.get("type", ""),
                    "tier": "",
                    "name": skill["name"],
                    "effect": effect,
                    "source": source,
                    "value": value,
                    "note": note,
                    "review": review,
                    "description": strip_markup(skill.get("description", ""))[:160],
                })

    df = pd.DataFrame(rows)
    df = df.drop_duplicates(subset=["id", "effect", "source", "value", "note"])

    # several distinct values for the same fact usually mean a PvE / WvW-PvP
    # split; pet-related rows may not apply to the player at all
    value_variants = df.groupby(["id", "effect", "source", "note"])["value"].transform("nunique")
    split = value_variants > 1  # type: ignore
    pets = df["description"].str.contains(r"\bpets?\b", case=False, regex=True)
    df.loc[split | pets, "review"] = True

    if os.path.isfile(OVERRIDES_PATH):
        overrides = pd.read_csv(OVERRIDES_PATH)
        df = df.loc[~df["id"].isin(overrides["id"])]
        df = pd.concat([df, overrides.loc[overrides["effect"] != "drop"]], ignore_index=True)

    df = df.sort_values(by=["profession", "elite", "specialization", "name", "effect"])
    df["icon"] = df["id"].map(icons).fillna("")  # type: ignore

    # slot and tier come from the API even for hand-written override rows -
    # the conflict warning on the website relies on them being complete
    is_trait = df["kind"] == "trait"
    df.loc[is_trait, "slot"] = df.loc[is_trait, "id"].map(trait_slots)  # type: ignore
    df.loc[is_trait, "tier"] = df.loc[is_trait, "id"].map(trait_tiers)  # type: ignore
    # position within the tier column (top/middle/bottom in the trait tree);
    # skills have no position and stay empty
    df["position"] = df["id"].map(trait_positions)  # type: ignore
    df.to_csv("assets/traits.csv", index=False)
    download_icons(df)
    generate_specializations()

    print(df.groupby(["profession", "kind"]).size().to_string())
    review_count = int(df["review"].sum())  # type: ignore
    unvalued_count = int(df["value"].isna().sum())  # type: ignore
    print(f"\ntotal rows: {len(df)}, rows needing review: {review_count},"
          f" rows without value: {unvalued_count}")
    if review_count:
        review_columns = ["id", "profession", "name", "effect", "value", "note"]
        print("\nrows to review:")
        print(df.loc[df["review"], review_columns]
              .to_string(index=False, max_colwidth=60))  # type: ignore


if __name__ == "__main__":
    main()
