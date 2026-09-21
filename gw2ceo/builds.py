"""Curated builds: one TOML file per build in builds/.

A build file names the build, its category and the in-game build template
chat link; traits, skills and weapon types are decoded from that link (the
game exports all of them). Gear is listed explicitly per slot because the
optimizer's result is only a per-slot-family count, while the build page
shows every slot (later with its skin). See builds/README.md for the schema.

Everything the page needs (trait icons, skill icons, the specialization
panel backgrounds) is served through /icons/, whose cache downloads missing
images on demand - a fresh clone renders every build without preparation.
"""

import os
import struct
from base64 import b64decode

try:
    import tomllib
except ModuleNotFoundError:  # Python < 3.11
    import tomli as tomllib  # type: ignore[no-redef]

from gw2ceo.api import get_api_data, get_api_data_bulk
from gw2ceo.buildlink import PROFESSION_CODES

BUILDS_DIR = "builds"

# a build belongs to exactly one category; "event" and the like are tags
CATEGORIES = {
    "openworld": "Open world",
    "raid": "Raid",
    "support": "Support",
    "wvw": "WvW",
}

# weapon type ids of the chat link's weapon section (wiki: Chat_link_format)
WEAPON_TYPES = {
    5: "Axe", 35: "Longbow", 47: "Dagger", 49: "Focus", 50: "Greatsword",
    51: "Hammer", 53: "Mace", 54: "Pistol", 85: "Rifle", 86: "Scepter",
    87: "Shield", 89: "Staff", 90: "Sword", 102: "Torch", 103: "Warhorn",
    107: "Shortbow", 265: "Spear",
}

ARMOR_SLOTS = [("head", "Head"), ("shoulders", "Shoulders"), ("chest", "Chest"),
               ("gloves", "Gloves"), ("legs", "Legs"), ("boots", "Boots")]
TRINKET_SLOTS = [("back", "Back item"), ("accessory1", "Accessory 1"),
                 ("accessory2", "Accessory 2"), ("amulet", "Amulet"),
                 ("ring1", "Ring 1"), ("ring2", "Ring 2")]
WEAPON_SETS = [("set1", "Weapon set 1"), ("set2", "Weapon set 2"), ("aquatic", "Aquatic")]
RARITIES = ("exotic", "ascended", "legendary")

SKILL_LABELS = ["Heal", "Utility", "Utility", "Utility", "Elite"]


def _trait_entry(trait: dict) -> dict:
    return {
        "id": trait["id"],
        "name": trait["name"],
        "description": trait.get("description", ""),
        "icon": f"/icons/trait_{trait['id']}.png",
    }


def _skill_entry(skill: dict | None, label: str) -> dict | None:
    if skill is None:
        return None
    return {
        "id": skill["id"],
        "name": skill["name"],
        "description": skill.get("description", ""),
        "icon": f"/icons/skill_{skill['id']}.png",
        "slot": label,
    }


def decode_template(link: str) -> dict:
    """The complete content of a build template chat link: profession, the
    three trait lines with every trait and the chosen ones, all ten skills
    (land and underwater) and the equipped weapon types."""
    payload = link.strip().strip("[]").removeprefix("&")
    try:
        data = b64decode(payload, validate=True)
    except ValueError:
        raise ValueError("That does not look like a chat link (expected [&DQ...=]).")
    if len(data) < 28 or data[0] != 0x0D:
        raise ValueError("This chat link is not a build template link.")
    if not 1 <= data[1] <= len(PROFESSION_CODES):
        raise ValueError("Unknown profession in the chat link.")
    profession = PROFESSION_CODES[data[1] - 1]

    lines = []
    for line in range(3):
        spec_id, choices = data[2 + 2 * line], data[3 + 2 * line]
        if spec_id == 0:
            continue
        spec = get_api_data(f"specializations/{spec_id}")
        traits = {trait["id"]: trait for trait in
                  get_api_data_bulk("traits", spec["minor_traits"] + spec["major_traits"])}
        majors = spec["major_traits"]
        selected = [(choices >> (2 * tier)) & 0b11 for tier in range(3)]
        lines.append({
            "id": spec_id,
            "name": spec["name"],
            "elite": bool(spec["elite"]),
            "icon": f"/icons/spec_{spec_id}.png",
            "background": f"/icons/spec_panel_{spec_id}.png",
            "minors": [_trait_entry(traits[trait_id]) for trait_id in spec["minor_traits"]],
            "majors": [[_trait_entry(traits[trait_id]) for trait_id in majors[3 * tier:3 * tier + 3]]
                       for tier in range(3)],
            "selected": selected,  # per tier: 0 none, 1 top, 2 middle, 3 bottom
        })

    palettes = struct.unpack_from("<10H", data, 8)
    skill_by_palette = dict(get_api_data(f"professions/{profession}")["skills_by_palette"])
    skill_ids = [skill_by_palette.get(palette) for palette in palettes]
    skills = {skill["id"]: skill for skill in
              get_api_data_bulk("skills", [skill_id for skill_id in skill_ids if skill_id])}
    # palette order: heal, utility 1-3, elite - land and underwater interleaved
    land = [_skill_entry(skills.get(skill_ids[2 * slot]), SKILL_LABELS[slot]) for slot in range(5)]
    aquatic = [_skill_entry(skills.get(skill_ids[2 * slot + 1]), SKILL_LABELS[slot])
               for slot in range(5)]

    weapons = []
    if len(data) > 44:
        count = data[44]
        if len(data) >= 45 + 2 * count:
            weapons = [WEAPON_TYPES.get(weapon_id, f"weapon {weapon_id}")
                       for weapon_id in struct.unpack_from(f"<{count}H", data, 45)]

    return {
        "profession": profession,
        "lines": lines,
        "skills": {"land": land, "aquatic": aquatic},
        "weapons": weapons,
    }


def _item(value, where: str, weapon: bool = False) -> dict:
    """One gear slot from the TOML: a bare string is the stat prefix, a table
    may add rarity, upgrade (rune / sigils) and skin."""
    if isinstance(value, str):
        value = {"prefix": value}
    if not isinstance(value, dict):
        raise ValueError(f"{where}: expected a prefix string or a table, got {value!r}")
    rarity = value.get("rarity", "ascended")
    if rarity not in RARITIES:
        raise ValueError(f"{where}: rarity must be one of {', '.join(RARITIES)}")
    sigils = value.get("sigils", [value["sigil"]] if "sigil" in value else [])
    if isinstance(sigils, str):
        sigils = [sigils]
    item = {
        "prefix": value.get("prefix", ""),
        "rarity": rarity,
        "skin": value.get("skin"),
        "icon": value.get("icon"),
        "rune": value.get("rune"),
        "sigils": list(sigils),
        "infusions": value.get("infusions"),
    }
    if weapon:
        if not value.get("type"):
            raise ValueError(f"{where}: a weapon needs a type (Staff, Dagger, ...)")
        item["type"] = value["type"]
    return item


def _gear(raw: dict, where: str) -> dict:
    armor_raw = raw.get("armor", {})
    trinkets_raw = raw.get("trinkets", {})
    weapons_raw = raw.get("weapons", {})
    for group, allowed in ((armor_raw, ARMOR_SLOTS), (trinkets_raw, TRINKET_SLOTS),
                           (weapons_raw, WEAPON_SETS)):
        unknown = set(group) - {key for key, _ in allowed}
        if unknown:
            raise ValueError(f"{where}: unknown gear slot(s) {sorted(unknown)}; "
                             f"allowed: {[key for key, _ in allowed]}")

    def slots(group, allowed):
        return [{"slot": key, "label": label, **_item(group[key], f"{where} [{key}]")}
                for key, label in allowed if key in group]

    weapon_sets = []
    for key, label in WEAPON_SETS:
        if key not in weapons_raw:
            continue
        entries = weapons_raw[key]
        if isinstance(entries, dict) or isinstance(entries, str):
            entries = [entries]
        weapon_sets.append({
            "set": key, "label": label,
            "weapons": [_item(entry, f"{where} [weapons.{key}]", weapon=True)
                        for entry in entries],
        })

    consumables = [(label, raw[key]) for key, label in (
        ("rune", "Rune"), ("relic", "Relic"), ("food", "Food"), ("utility", "Utility"),
        ("infusions", "Infusions"), ("jade_core", "Jade bot core"),
    ) if raw.get(key)]

    return {
        "armor": slots(armor_raw, ARMOR_SLOTS),
        "trinkets": slots(trinkets_raw, TRINKET_SLOTS),
        "weapon_sets": weapon_sets,
        "consumables": [{"label": label, "value": value} for label, value in consumables],
        "rune": raw.get("rune"),
    }


def load_build(path: str) -> dict:
    with open(path, "rb") as file:
        raw = tomllib.load(file)
    where = os.path.basename(path)
    slug = raw.get("slug") or os.path.splitext(where)[0]

    for key in ("name", "category", "chatlink"):
        if not raw.get(key):
            raise ValueError(f"{where}: missing required key '{key}'")
    if raw["category"] not in CATEGORIES:
        raise ValueError(f"{where}: category must be one of {list(CATEGORIES)}")

    template = decode_template(raw["chatlink"])
    elite = next((line for line in template["lines"] if line["elite"]), None)
    gear = _gear(raw.get("gear", {}), where)

    # the card's weapon summary: the explicit sets, or the chat link's types
    if gear["weapon_sets"]:
        weapon_summary = [" / ".join(weapon["type"] for weapon in weapon_set["weapons"])
                          for weapon_set in gear["weapon_sets"] if weapon_set["set"] != "aquatic"]
    else:
        weapon_summary = [" / ".join(template["weapons"])] if template["weapons"] else []

    return {
        "slug": slug,
        "name": raw["name"],
        "category": raw["category"],
        "category_label": CATEGORIES[raw["category"]],
        "tags": list(raw.get("tags", [])),
        "summary": raw.get("summary", ""),
        "notes": raw.get("notes", ""),
        "chatlink": raw["chatlink"].strip(),
        "optimizer": raw.get("optimizer"),
        "profession": template["profession"],
        "spec": elite["name"] if elite else f"Core {template['profession']}",
        "spec_icon": elite["icon"] if elite else f"/icons/tango_{template['profession']}.png",
        "banner": (elite or template["lines"][-1])["background"] if template["lines"] else None,
        "profession_icon": f"/icons/tango_{template['profession']}.png",
        "lines": template["lines"],
        "skills": template["skills"],
        "template_weapons": template["weapons"],
        "weapon_summary": weapon_summary,
        "gear": gear,
    }


def load_all() -> list[dict]:
    """Every build in builds/, in a stable display order: by profession (the
    in-game order), then elite spec, then category, then name."""
    if not os.path.isdir(BUILDS_DIR):
        return []
    builds = [load_build(os.path.join(BUILDS_DIR, name))
              for name in sorted(os.listdir(BUILDS_DIR)) if name.endswith(".toml")]
    slugs = [build["slug"] for build in builds]
    duplicates = {slug for slug in slugs if slugs.count(slug) > 1}
    if duplicates:
        raise ValueError(f"duplicate build slug(s): {sorted(duplicates)}")
    order = list(CATEGORIES)
    builds.sort(key=lambda build: (PROFESSION_CODES.index(build["profession"]), build["spec"],
                                   order.index(build["category"]), build["name"]))
    return builds


def summary(build: dict) -> dict:
    """The card content for the list page."""
    return {key: build[key] for key in (
        "slug", "name", "category", "category_label", "tags", "summary", "profession",
        "spec", "spec_icon", "banner", "profession_icon", "weapon_summary",
    )} | {
        "traitlines": [{"name": line["name"], "icon": line["icon"]} for line in build["lines"]],
    }
