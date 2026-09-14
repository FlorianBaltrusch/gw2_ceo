"""Encode and decode GW2 build template chat links ([&DQ...=]).

Layout of the binary payload (see wiki: Chat_link_format):
  byte 0      0x0D (build template)
  byte 1      profession code (1-9)
  bytes 2-7   three trait lines: (specialization id, choice byte) each;
              the choice byte packs the adept/master/grandmaster pick as
              2-bit values (0 = none, 1-3 = top/middle/bottom)
  bytes 8-27  ten uint16 skill palette ids:
              heal, utility 1-3, elite - terrestrial/aquatic interleaved
  bytes 28+   profession-specific data (pets, legends, weapons) - ignored
"""

import struct
from base64 import b64decode, b64encode

import gw2ceo.general_data as gd
from gw2ceo.api import get_api_data

# list index + 1 == in-game profession code
PROFESSION_CODES = ["Guardian", "Warrior", "Engineer", "Ranger", "Thief",
                    "Elementalist", "Mesmer", "Necromancer", "Revenant"]


def decode(link: str) -> dict:
    """Read profession, trait lines and skills from a chat link and return the
    ids of everything the optimizer knows (selected majors, all minors of the
    equipped lines, and known skills)."""
    payload = link.strip().strip("[]").removeprefix("&")
    try:
        data = b64decode(payload, validate=True)
    except Exception:
        raise ValueError("That does not look like a chat link (expected [&DQ...=]).")
    if len(data) < 28 or data[0] != 0x0D:
        raise ValueError("This chat link is not a build template link.")
    if not 1 <= data[1] <= len(PROFESSION_CODES):
        raise ValueError("Unknown profession in the chat link.")

    profession = PROFESSION_CODES[data[1] - 1]
    candidate_ids = []
    specializations = []
    elite_spec = None

    for line in range(3):
        spec_id, choices = data[2 + 2 * line], data[3 + 2 * line]
        if spec_id == 0:
            continue
        spec = get_api_data(f"specializations/{spec_id}")
        specializations.append(spec["name"])
        if spec["elite"]:
            elite_spec = spec["name"]
        candidate_ids.extend(spec["minor_traits"])
        for tier in range(3):
            choice = (choices >> (2 * tier)) & 0b11
            if choice:
                candidate_ids.append(spec["major_traits"][3 * tier + choice - 1])

    palettes = struct.unpack_from("<10H", data, 8)
    skill_by_palette = dict(get_api_data(f"professions/{profession}")["skills_by_palette"])
    candidate_ids.extend(skill_by_palette[palette] for palette in palettes
                         if palette in skill_by_palette)

    known = set(gd.traits["id"].tolist())
    selectable = [trait_id for trait_id in dict.fromkeys(candidate_ids) if trait_id in known]

    return {
        "profession": profession,
        "specializations": specializations,
        "elite_spec": elite_spec,
        "selectable_ids": selectable,
    }


def encode(profession: str, selected_ids: list[int]) -> str:
    """Build a chat link from the optimizer's selection: the trait lines that
    contain selected traits (minors need no encoding) and the selected skills."""
    if profession not in PROFESSION_CODES:
        raise ValueError(f"Unknown profession: {profession}")
    table = gd.traits
    rows = table[table["id"].isin(selected_ids)].drop_duplicates("id")

    # trait lines with the tier choices of the selected major traits
    lines = {}
    for spec_name in rows[rows["kind"] == "trait"]["specialization"].unique():
        specs = gd.specializations
        spec_id = int(specs[specs["name"] == spec_name]["id"].iloc[0])
        spec = get_api_data(f"specializations/{spec_id}")
        choices = [0, 0, 0]
        spec_rows = rows[(rows["kind"] == "trait") & (rows["specialization"] == spec_name)]
        for trait_id in spec_rows["id"]:
            if trait_id in spec["minor_traits"]:
                continue
            tier, choice = divmod(spec["major_traits"].index(int(trait_id)), 3)
            if choices[tier] and choices[tier] != choice + 1:
                raise ValueError(
                    f"Two competing {spec_name} traits of the same tier are selected - "
                    "a build can only take one per tier."
                )
            choices[tier] = choice + 1
        lines[spec_id] = (bool(spec["elite"]), choices)
    if len(lines) > 3:
        raise ValueError("The selection spans more than three trait lines, "
                         "but a build holds only three.")

    # skills into their slots
    slots = {"Heal": [0], "Utility": [0, 0, 0], "Elite": [0]}
    palette_by_skill = {skill: palette for palette, skill
                        in get_api_data(f"professions/{profession}")["skills_by_palette"]}
    for row in rows[rows["kind"] == "skill"].itertuples():
        palette = palette_by_skill.get(row.id)
        slot = slots.get(row.slot)
        if palette is None or slot is None:
            continue
        try:
            slot[slot.index(0)] = palette
        except ValueError:
            raise ValueError(f"More than {len(slot)} {row.slot.lower()} skills selected.")

    data = bytearray([0x0D, PROFESSION_CODES.index(profession) + 1])
    ordered = sorted(lines.items(), key=lambda item: item[1][0])  # elite line last
    for spec_id, (_, choices) in (ordered + [(0, (False, [0, 0, 0]))] * 3)[:3]:
        data.append(spec_id)
        data.append(choices[0] | choices[1] << 2 | choices[2] << 4)
    terrestrial = [slots["Heal"][0], *slots["Utility"], slots["Elite"][0]]
    for palette in terrestrial:
        data += struct.pack("<2H", palette, 0)  # aquatic slots stay empty
    data += bytes(16)  # profession-specific data (pets, legends): none

    return "[&" + b64encode(bytes(data)).decode() + "]"
