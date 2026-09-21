"""Gear of a curated build, derived from its optimizer link.

The optimizer link (the result card's "Copy optimizer link") carries every
input of the solver, so the build page runs the same calculation and lists
the outcome per slot: stat prefix and rarity of every piece, rune, sigils,
relic, food, utility and infusions. Weapon types come from the chat link's
weapon section (each type listed once); the sets are inferred from the
profession's main-hand/off-hand flags. Anything the solver cannot know -
skins, an aquatic set, a deliberate deviation - is added or overridden per
slot in the build file (see builds/README.md).
"""

from urllib.parse import parse_qs, urlsplit

from werkzeug.datastructures import MultiDict

import gw2ceo.general_data as gd
from gw2ceo.api import get_api_data
from gw2ceo.solve import solve

# solver keys -> item names (all verified against the wiki, 2026-09-21)
RUNES = {
    "scholar": "Superior Rune of the Scholar", "dragonh": "Superior Rune of the Dragonhunter",
    "gole": "Superior Rune of the Golemancer", "deadeye": "Superior Rune of the Deadeye",
    "eagle": "Superior Rune of the Eagle", "infil": "Superior Rune of Infiltration",
    "ranger": "Superior Rune of the Ranger",
    "water": "Superior Rune of the Water", "monk": "Superior Rune of the Monk",
    "altruism": "Superior Rune of Altruism", "leadership": "Superior Rune of Leadership",
    "radiance": "Superior Rune of Radiance", "sanctuary": "Superior Rune of Sanctuary",
    "fireworks": "Superior Rune of Fireworks", "pack": "Superior Rune of the Pack",
    "herald": "Superior Rune of the Herald", "durability": "Superior Rune of Durability",
    "rebirth": "Superior Rune of the Rebirth", "mercy": "Superior Rune of Mercy",
    "guardian": "Superior Rune of the Guardian",
}
SIGILS = {
    "force": "Superior Sigil of Force", "impact": "Superior Sigil of Impact",
    "accuracy": "Superior Sigil of Accuracy", "perception": "Superior Sigil of Perception",
    "bloodlust": "Superior Sigil of Bloodlust",
    "concentration": "Superior Sigil of Concentration", "bounty": "Superior Sigil of Bounty",
    "life": "Superior Sigil of Life", "benevolence": "Superior Sigil of Benevolence",
    "transference": "Superior Sigil of Transference",
    "free": "utility sigil of your choice",
}
STACKING_SIGILS = {"perception", "bloodlust", "bounty", "life", "benevolence"}
FOODS = {
    "butternut": "Bowl of Butternut Squash Soup", "truffle": "Plate of Truffle Steak",
    "curry": "Bowl of Curry Butternut Squash Soup", "omnomberry": "Omnomberry Pie",
    "mint_brulee": "Mint Creme Brulee", "mint_salad": "Bowl of Fruit Salad with Mint Garnish",
    "rice_ball": "Delicious Rice Ball", "eggs_benedict": "Plate of Eggs Benedict",
    "nopalitos": "Bowl of Nopalitos Sauté",
    "no food": "none",
}
UTILITIES = {
    "stones": "Superior Sharpening Stone", "writ_accuracy": "Writ of Masterful Accuracy",
    "writ_strength": "Writ of Masterful Strength",
    "magnanimous": "Magnanimous Maintenance Oil", "toxic": "Toxic Maintenance Oil",
    "lucent": "Potent Lucent Oil", "bountiful": "Bountiful Maintenance Oil",
    "none": "none",
}
RELICS = {
    "mistburn": "Relic of Mistburn",
    "damage": "Relic of the Thief (or Eagle / Fireworks)",
    "herald": "Relic of the Herald", "monk": "Relic of the Monk", "castora": "Relic of Castora",
    "reserved": "your reserved relic", "utility": "free choice", "none": "free choice",
}

# stat prefixes behind the solver's (precision-major, -minor, none) split,
# and the jewels of exotic trinkets in the same order
PREFIXES = {"3p": ("Assassin's", "Berserker's", "Valkyrie"),
            "4p": ("Marauder", "Dragon's", "Dragon's")}
JEWELS = {"3p": ("Exquisite Opal Jewel", "Exquisite Ruby Jewel", "Exquisite Beryl Jewel"),
          "4p": ("Exquisite Ebony Jewel", "Exquisite Jade Jewel", "Exquisite Jade Jewel")}
BOON_PREFIXES = ("Harrier's", "Magi's", "Giver's")
BOON_UPGRADES = ("Platinum Doubloon", "Brandspark Jewel", "Crest of the Magi",
                 "Exquisite Freshwater Pearl")

ARMOR = [("head", "Head"), ("shoulders", "Shoulders"), ("chest", "Chest"),
         ("gloves", "Gloves"), ("legs", "Legs"), ("boots", "Boots")]
TRINKETS = [("back-item", "back", "Back item"), ("accessory1", "accessory1", "Accessory 1"),
            ("accessory2", "accessory2", "Accessory 2"), ("amulet", "amulet", "Amulet"),
            ("ring1", "ring1", "Ring 1"), ("ring2", "ring2", "Ring 2")]
ARMOR_TRINKET_KEYS = ["chest", "legs", "head", "shoulders", "gloves", "boots", "amulet",
                      "ring1", "ring2", "accessory1", "accessory2", "back-item"]

# solver slot family -> the concrete slot keys it covers, in assignment order
FAMILIES = {
    "Weapons": ["onehanded1", "onehanded2"], "Weapon": ["twohanded"],
    "Chest": ["chest"], "Legs": ["legs"], "Head": ["head"],
    "Shoulders/Gloves/Boots": ["shoulders", "gloves", "boots"],
    "Amulet": ["amulet"], "Rings": ["ring1", "ring2"],
    "Accessories": ["accessory1", "accessory2"], "Back item": ["back-item"],
}
# the solver counts exotic-trinket upgrades over amulet, rings, accessories, back
UPGRADE_ORDER = ["amulet", "ring1", "ring2", "accessory1", "accessory2", "back-item"]

# level-80 base health per profession (wiki: Health); max health adds 10 per vitality
BASE_HEALTH = {"Warrior": 9212, "Necromancer": 9212,
               "Revenant": 5922, "Engineer": 5922, "Ranger": 5922, "Mesmer": 5922,
               "Guardian": 1645, "Thief": 1645, "Elementalist": 1645}
# level-80 conversions (wiki: Precision, Ferocity, Concentration)
PRECISION_PER_CRIT_PCT = 21     # 1000 precision = 5% critical chance
PRECISION_AT_ZERO_CRIT = 895
FEROCITY_PER_CRIT_DAMAGE_PCT = 15  # on top of the 150% base
CONCENTRATION_PER_BOON_PCT = 15

TOGGLE_DEFAULTS = {"fury": "1", "food": "1", "utility": "1", "stacking": "1", "writs": "1",
                   "single_sigil": "0", "pie": "0", "herald": "1", "relic_reserved": "0",
                   "stowed": "0", "ascended_food": "1", "tank": "0"}


def weapon_keys(handedness: str) -> list[str]:
    return ["twohanded"] if handedness == "2h" else ["onehanded1", "onehanded2"]


def ranking_from_slider(profession: str, position: int) -> tuple[str, float | None]:
    """The boon mode's K slider, as the client computes it: the edges rank
    by healing power / outgoing %, the interior spans the class's own
    healing skills on a log scale."""
    table = gd.heal_skills
    universal = table["profession"].fillna("") == ""
    ks = table.loc[universal | (table["profession"].str.lower() == profession.lower()), "k"]
    if position <= 0 or ks.empty:
        return "healing", None
    if position >= 100:
        return "outgoing", None
    kmin, kmax = float(ks.min()), float(ks.max())
    return "k", round(kmin * (kmax / kmin) ** ((position - 1) / 98))


def solver_args(link: str) -> tuple[MultiDict, set[str], str, str]:
    """Translate an optimizer link's query into /calculate parameters.
    Returns (args, ascended slot keys, gear environment, handedness)."""
    query = parse_qs(urlsplit(link).query)

    def get(key, default=None):
        return query.get(key, [default])[0]

    profession = get("profession")
    if not profession or not get("traits"):
        raise ValueError("the optimizer link carries no profession/traits "
                         "(copy it from the result card's 'Copy optimizer link')")
    mode = get("mode", "crit")
    handedness = get("weapon", "2h")
    env = get("env", "3p")
    all_keys = weapon_keys(handedness) + ARMOR_TRINKET_KEYS
    asc_param = get("asc")
    if asc_param == "all":
        ascended = set(all_keys)
    else:
        ascended = {key for key in (asc_param or "").split(",") if key in all_keys}

    args = MultiDict()
    args["mode"] = mode
    args["profession"] = profession
    for trait_id in get("traits").split(","):
        if trait_id:
            args.add("traits[]", trait_id)
    for item in (get("stacks") or "").split(","):
        if item:
            args.add("stacks[]", item)
    for item in (get("variants") or "").split(","):
        if item:
            trait_id, _, chosen = item.partition(":")
            args.add("variants[]", f"{trait_id}:{chosen.replace('.', ',')}")
    args["parameters"] = "3p" if mode == "boon" else env
    args["handedness"] = handedness
    for key in ascended:
        args.add("armor[]", key)
    for key, default in TOGGLE_DEFAULTS.items():
        args[key] = "true" if get(key, default) == "1" else "false"
    args["might"] = get("might", "25")
    if mode == "boon":
        ranking, k = ranking_from_slider(profession, int(get("kpos", "0") or 0))
        args["ranking"] = ranking
        if k is not None:
            args["k"] = str(k)
    return args, ascended, env, handedness


def _spread(counts, names) -> list[str]:
    """(n0, n1, n2) counts -> the names in order, e.g. (1, 2, 0) -> [a, b, b]."""
    return [name for count, name in zip(counts, names) for _ in range(count)]


def _crit_counts(group: dict) -> tuple[int, int, int]:
    major = int(group["precision_major"])
    none = int(group.get("no_precision") or 0)
    return major, int(group["pieces"]) - major - none, none


def infer_weapon_sets(profession: str, types: list[str]) -> list[list[str]]:
    """Weapon sets from the chat link's weapon types: two-handers stand
    alone, one-handers pair a main hand with an off hand in the order the
    link lists them; a lone dual-wieldable type pairs with itself."""
    flags = {name: set(data.get("flags", []))
             for name, data in get_api_data(f"professions/{profession}")["weapons"].items()}
    remaining = [name for name in types if "Aquatic" not in flags.get(name, set())]
    sets = []
    while remaining:
        current = remaining.pop(0)
        current_flags = flags.get(current, {"Mainhand"})
        if "TwoHand" in current_flags:
            sets.append([current])
        elif "Mainhand" in current_flags:
            partner = next((other for other in remaining
                            if "Offhand" in flags.get(other, set())
                            and "TwoHand" not in flags.get(other, set())), None)
            if partner:
                remaining.remove(partner)
                sets.append([current, partner])
            elif "Offhand" in current_flags:
                sets.append([current, current])  # dual wield
            else:
                sets.append([current])
        else:  # off-hand only: find its main hand
            partner = next((other for other in remaining
                            if "Mainhand" in flags.get(other, set())), None)
            if partner:
                remaining.remove(partner)
                sets.append([partner, current])
            else:
                sets.append([current])
    return sets


def _sigil_lists(sigil_field: str, single_sigil: bool) -> tuple[list[str], list[str]]:
    """Sigil names for the optimized set and for the other sets. Three
    sigils mean a stacking sigil parked in the stowed set."""
    keys = [key for key in str(sigil_field).split("+") if key]
    names = [SIGILS.get(key, key.capitalize()) for key in keys]
    if single_sigil:
        names.append("sigil of your choice")
    if len(keys) == 3:
        stowed = [SIGILS[key] for key in keys if key in STACKING_SIGILS]
        active = [SIGILS.get(key, key) for key in keys if key not in STACKING_SIGILS]
        return active, stowed + active[:1]
    return names, names


def character(row: dict, mode: str, profession: str) -> dict:
    """The build's attributes with what they mean in game: precision as
    critical chance, ferocity as critical damage, vitality as health,
    concentration as boon duration."""
    def pct(value):
        return f"{value:.1f}%"

    health = BASE_HEALTH.get(profession, 5922) + 10 * float(row["vitality"])
    attributes = []
    if mode == "boon":
        boon_duration = 100.0 if row.get("exact") else 100.0 + float(row.get("conc_delta", 0)) / CONCENTRATION_PER_BOON_PCT
        attributes += [
            {"name": "Healing power", "value": round(row["healing"]),
             "effect": "Outgoing healing bonus", "effect_value": f"+{row['outgoing']:.1f}%"},
            {"name": "Boon duration", "value": pct(boon_duration),
             "effect": "Concentration and flat bonuses, capped at +100%", "effect_value": ""},
        ]
        precision = float(row["precision"])
    else:
        precision = float(row["precision"]) + float(row.get("chance", 0))
    crit_chance = row["crit_pct"] if row.get("crit_pct") is not None \
        else max(0.0, min(100.0, (precision - PRECISION_AT_ZERO_CRIT) / PRECISION_PER_CRIT_PCT))
    attributes.append({"name": "Power", "value": round(row["power"]), "effect": None, "effect_value": None})
    attributes.append({"name": "Precision", "value": round(precision),
                       "effect": "Critical chance", "effect_value": pct(float(crit_chance))})
    if "ferocity" in row:
        attributes.append({"name": "Ferocity", "value": round(row["ferocity"]),
                           "effect": "Critical damage",
                           "effect_value": pct(150 + float(row["ferocity"]) / FEROCITY_PER_CRIT_DAMAGE_PCT)})
    attributes.append({"name": "Vitality", "value": round(row["vitality"]),
                       "effect": "Health", "effect_value": round(health)})
    if mode == "boon":
        attributes.append({"name": "Toughness", "value": round(row["toughness"]),
                           "effect": None, "effect_value": None})
    if mode == "boon":
        headline = {"value": round(row["healing"]), "caption": "healing power at 100% boon duration"}
    else:
        crit_pct = row.get("crit_pct")
        headline = {"value": round(row["effective_power"]),
                    "caption": (f"effective power at {crit_pct}% critical chance"
                                if crit_pct is not None else "effective power at 100% crit")}
    return {"headline": headline, "attributes": attributes}


def derive(link: str, profession: str, template_weapons: list[str]) -> dict:
    """Run the optimizer link and list its result per slot."""
    args, ascended, env, handedness = solver_args(link)
    result = solve(args)
    mode = args["mode"]
    row = result["best"] if mode == "boon" else result
    if row is None or not row.get("equipment"):
        raise ValueError("the optimizer found no gear assignment for this link")

    def rarity(key):
        return "ascended" if key in ascended else "exotic"

    # solver groups -> prefix per slot key, upgrade per exotic trinket
    prefix_of: dict[str, str] = {}
    upgrade_of: dict[str, str] = {}
    exotic_trinkets = [key for key in UPGRADE_ORDER if key not in ascended]
    for group in row["equipment"]:
        label = group["slot"]
        if mode == "boon":
            counts, names = tuple(group["counts"]), BOON_PREFIXES
            upgrade_names = BOON_UPGRADES
        else:
            counts, names = _crit_counts(group), PREFIXES[env]
            upgrade_names = JEWELS[env]
        if label.startswith(("Jewels", "Upgrades")):
            for key, name in zip(exotic_trinkets, _spread(counts, upgrade_names)):
                upgrade_of[key] = name
            continue
        family = label.removesuffix(" (ascended)").removesuffix(" (exotic)")
        slots = FAMILIES.get(family, [])
        if label.endswith("(ascended)"):
            slots = [key for key in slots if key in ascended]
        elif label.endswith("(exotic)"):
            slots = [key for key in slots if key not in ascended]
        for key, name in zip(slots, _spread(counts, names)):
            prefix_of[key] = name

    # rune(s): a mixed set like "scholar(4)+eagle(2)" spreads over the armor
    rune_field = str(row["rune"])
    rune_names = []
    if "(" in rune_field:
        for part in rune_field.split("+"):
            key, _, count = part.rstrip(")").partition("(")
            rune_names += [RUNES.get(key, key.capitalize())] * int(count)
        rune_text = " + ".join(f"{part.rstrip(')').partition('(')[2]}× "
                               f"{RUNES.get(part.partition('(')[0], part.partition('(')[0].capitalize())}"
                               for part in rune_field.split("+"))
    else:
        rune_text = RUNES.get(rune_field, rune_field.capitalize())
        rune_names = [rune_text] * 6

    def item(key, label, prefix, **extra):
        return {"slot": key, "label": label, "prefix": prefix, "rarity": rarity(key),
                "skin": None, "icon": None, "rune": None, "sigils": [], "infusions": None,
                "upgrade": None, "note": None} | extra

    armor = [item(key, label, prefix_of.get(key, ""), rune=rune_names[index])
             for index, (key, label) in enumerate(ARMOR)]
    trinkets = [item(slot, label, prefix_of.get(key, ""), upgrade=upgrade_of.get(key))
                | {"slot": slot}
                for key, slot, label in TRINKETS]
    for trinket, (key, _, _) in zip(trinkets, TRINKETS):
        trinket["rarity"] = rarity(key)

    # weapons: types from the chat link, stats from the optimized set
    single_sigil = args["single_sigil"] == "true"
    active_sigils, other_sigils = _sigil_lists(row["sigil"], single_sigil)
    optimized_keys = weapon_keys(handedness)
    optimized_prefixes = [prefix_of.get(key, "") for key in optimized_keys]
    majority = max(set(optimized_prefixes), key=optimized_prefixes.count) if optimized_prefixes else ""
    # the set the optimizer priced (matching its handedness) is listed first
    inferred = infer_weapon_sets(profession, template_weapons)
    inferred.sort(key=lambda types: 0 if len(types) == (2 if handedness == "1h" else 1) else 1)
    weapon_sets = []
    primary_done = False
    for index, types in enumerate(inferred):
        is_two_handed = len(types) == 1 and handedness == "2h"
        is_one_handed = len(types) == 2 and handedness == "1h"
        primary = not primary_done and (is_two_handed or is_one_handed)
        weapons = []
        for position, weapon_type in enumerate(types):
            if primary:
                key = optimized_keys[position]
                prefix, weapon_rarity = prefix_of.get(key, ""), rarity(key)
                sigils = active_sigils
                note = None
            else:
                prefix, weapon_rarity = majority, rarity(optimized_keys[0])
                sigils = other_sigils
                note = "not optimized separately - mirrors the optimized set"
            if len(types) == 2:  # one sigil per one-handed weapon
                sigils = sigils[position:position + 1] if position < 1 else sigils[1:]
            weapons.append({"type": weapon_type, "prefix": prefix, "rarity": weapon_rarity,
                            "sigils": list(sigils), "skin": None, "icon": None, "rune": None,
                            "infusions": None, "upgrade": None, "note": note})
        weapon_sets.append({"set": f"set{index + 1}", "label": f"Weapon set {index + 1}",
                            "weapons": weapons})
        primary_done = primary_done or primary

    # consumables
    total = int(row["total_infusions"])
    if mode == "boon":
        conc = int(row["conc_infusions"])
        infusions = " + ".join(part for part in (
            f"{conc}× +5 Concentration" if conc else "",
            f"{total - conc}× +5 Healing Power" if total - conc else "") if part) or "none"
    else:
        prec = int(row["prec_infusions"])
        infusions = " + ".join(part for part in (
            f"{prec}× +5 Precision" if prec else "",
            f"{total - prec}× +5 Power" if total - prec else "") if part) or "none"
    consumables = [
        ("Rune", rune_text),
        ("Relic", RELICS.get(str(row["relic"]), str(row["relic"]).capitalize())),
        ("Food", FOODS.get(str(row["food"]), str(row["food"]).capitalize())),
        ("Utility", UTILITIES.get(str(row["utility"]), str(row["utility"]).capitalize())),
        ("Infusions", infusions),
        ("Jade bot core", "Tier 10 (+235 vitality)"),
    ]

    notes = []
    if not row.get("exact") and not row.get("no_cap"):
        notes.append("The optimizer could not land exactly on the cap with these inputs - "
                     "open it for the details.")
    if row.get("stable_fallback") or (mode == "boon" and result.get("stable_fallback")):
        notes.append("This is the optimizer's best build; it also offers a stable backup "
                     "without stacking sigils.")

    return {
        "armor": armor,
        "trinkets": trinkets,
        "weapon_sets": weapon_sets,
        "consumables": [{"label": label, "value": value} for label, value in consumables],
        "rune": rune_text,
        "character": character(row, mode, profession),
        "notes": notes,
        "mode": mode,
    }
