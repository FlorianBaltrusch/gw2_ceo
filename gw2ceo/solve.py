"""The optimizer's request handling, independent of Flask: turn the query
parameters of /calculate (or of an optimizer link) into a solved build.

Shared by the /calculate endpoint and by the curated builds, whose gear
listing is derived from the optimizer link stored in the build file."""

import json
from collections import Counter

import numpy as np

import gw2ceo.general_data as gd
from gw2ceo import boon
from gw2ceo.calculate import calc_ep, calc_power
from gw2ceo.dtypes import BuildConstraints
from gw2ceo.gearselect import GearSelect
from gw2ceo.profession import Profession

ARMOR_SLOTS = ["onehanded", "twohanded", "chest", "legs", "head", "shoulders",
               "gloves", "boots", "amulet", "ring", "accessory", "back-item"]


def solve(args) -> dict:
    """`args` is any mapping with .get and .getlist (request.args or a
    MultiDict). Raises ValueError / NotImplementedError on bad input."""
    trait_ids = [int(trait_id) for trait_id in args.getlist("traits[]")]
    fury = args.get("fury") == "true"
    might = int(args.get("might", "25"))
    weapon_type = args.get("handedness")
    if weapon_type not in ("1h", "2h"):
        raise ValueError("handedness must be '1h' or '2h'")

    conditions = set()
    if fury:
        conditions.add("fury")
    if might >= gd.general_buffs.trait_might_threshold:
        conditions.add("might")
    # weapon-gated trait rows (Right-Hand Strength) follow the gear toggle
    conditions.add(f"weapon_{weapon_type}")
    # per-trait assumptions: "stacks[]=id:n" for stack-scaled traits,
    # "variants[]=id:fire,air" for attunement-style choices
    stacks = {}
    for item in args.getlist("stacks[]"):
        trait_id, _, count = item.partition(":")
        stacks[int(trait_id)] = int(count)
    variants = {}
    for item in args.getlist("variants[]"):
        trait_id, _, names = item.partition(":")
        variants[int(trait_id)] = [name for name in names.split(",") if name]

    profession = Profession(trait_ids, profession=args.get("profession"),
                            conditions=conditions, stacks=stacks, variants=variants)

    armor = args.getlist("armor[]")
    armor = [piece.replace("1", "").replace("2", "") for piece in armor]
    counts = Counter(armor)
    num_ascended = [counts[slot] for slot in ARMOR_SLOTS]

    mode = args.get("mode", "crit")
    if mode not in ("crit", "boon", "power"):
        raise ValueError("mode must be 'crit', 'boon' or 'power'")

    gear_environment = args.get("parameters")
    if mode == "boon" and gear_environment != "3p":
        raise ValueError("boon mode is 3-stat only (Harrier's/Magi's)")
    if gear_environment not in ("3p", "4p"):
        raise ValueError("parameters must be '3p' or '4p'")

    constraints = BuildConstraints(
        gear_environment=gear_environment,
        weapon_type=weapon_type,

        num_ascended=np.array(num_ascended),  # order as in ARMOR_SLOTS

        food=args.get("food", "true") == "true",
        utility=args.get("utility", "true") == "true",

        fury=fury,
        might=might,

        stacking_sigils=args.get("stacking", "true") == "true",
        writs=args.get("writs", "true") == "true",
        single_sigil=args.get("single_sigil", "false") == "true",
        omnomberry_pie=args.get("pie", "false") == "true",
        herald_relic=args.get("herald", "true") == "true",
        relic_reserved=args.get("relic_reserved", "false") == "true",
        ascended_food=args.get("ascended_food", "true") == "true",
        tank=args.get("tank", "false") == "true",
        stowed_stacking=args.get("stowed", "false") == "true",
    )

    if mode == "boon":
        ranking = args.get("ranking", "healing")
        if ranking not in ("healing", "outgoing", "k"):
            raise ValueError("ranking must be 'healing', 'outgoing' or 'k'")
        k = float(args.get("k", "2000"))
        if not 0 <= k <= 1e6:
            raise ValueError("k must be between 0 and 1000000")
        return boon_result(profession, constraints, ranking, k)
    if mode == "power":
        return power_result(profession, constraints)
    solution = calc_ep(profession, constraints)

    min_stats = gd.full_armor("Min", constraints.num_ascended,
                              constraints.gear_environment, constraints.weapon_type)
    total_infusions = int(gd.num_infusions(constraints.num_ascended,
                                           constraints.weapon_type))

    def render_row(row):
        """Full result for one solution row: stats, per-slot gear assignment
        (Valkyrie-capable in the low-remainder region of 3-stat gear) and the
        armor precision floor."""
        result = json.loads(row.to_json())
        result["total_infusions"] = total_infusions

        low_region = (constraints.gear_environment == "3p"
                      and row["remainder"] <= min_stats)
        gear = GearSelect(constraints, valkyrie=low_region)
        # the least precision the gear can possibly give: below this the crit
        # chance was already over the cap before gear (0 with Valkyrie pieces)
        result["armor_floor"] = float(sum(min(options) for options in gear.equipment))
        # among equal-precision splits the most power (Valkyrie splits differ);
        # near-miss rows show the achievable split, overshoot included
        assignment = gear.get_best_equipment(row["armor_precision_actual"])
        result["equipment"] = None
        if assignment is not None:
            groups = [(label, int(count), meta[choice])
                      for (label, count), meta, choice
                      in zip(gear.groups, gear.option_meta, assignment)
                      if count > 0]
            result["equipment"] = equipment_groups(groups)
        return result

    result = render_row(solution["best"])
    result["stable_fallback"] = None
    if solution["stable_fallback"] is not None:
        result["stable_fallback"] = render_row(solution["stable_fallback"])
    return result


def equipment_groups(groups):
    """Per-slot-family assignment rows; the rarity suffix only stays when a
    slot family actually mixes rarities (otherwise it would just echo the
    user's toggles)."""
    def family(label):
        return label.removesuffix(" (ascended)").removesuffix(" (exotic)")

    families = Counter(family(label) for label, _, _ in groups)
    return [
        {"slot": family(label) if families[family(label)] == 1 else label,
         "pieces": pieces, "precision_major": int(major), "no_precision": int(none_count)}
        for label, pieces, (major, _, none_count) in groups
    ]


def power_result(profession: Profession, constraints: BuildConstraints) -> dict:
    """Free-crit mode: the gear point maximizing true effective power, with
    the crit chance landing wherever that product peaks."""
    solution = calc_power(profession, constraints)
    gear = GearSelect(constraints, valkyrie=True)
    _, _, choices = gear.point_table()
    total_infusions = int(gd.num_infusions(constraints.num_ascended,
                                           constraints.weapon_type))

    def render(row):
        if row is None:
            return None
        result = json.loads(row.to_json())
        result["total_infusions"] = total_infusions
        result["no_cap"] = True  # this mode has no crit cap to miss
        result["crit_pct"] = round(float(row["crit_pct"]), 1)
        choice = choices[int(row["best_point"])]
        groups = [(label, int(count), meta[j])
                  for (label, count), meta, j
                  in zip(gear.groups, gear.option_meta, choice) if count > 0]
        result["equipment"] = equipment_groups(groups)
        return result

    result = render(solution["best"])
    assert result is not None  # a best row always exists
    result["stable_fallback"] = render(solution["stable_fallback"])
    return result


def boon_result(profession: Profession, constraints: BuildConstraints,
                ranking: str, k: float) -> dict:
    """The boon-mode ranking picked by the healing-profile slider, rendered
    with its gear assignment and stable backup."""
    solution = boon.calc_boon(profession, constraints, ranking, k)
    total_infusions = int(gd.num_infusions(constraints.num_ascended,
                                           constraints.weapon_type))

    def render_boon_row(row):
        if row is None:
            return None
        totals = boon.gear_totals(profession, constraints, row)
        return {
            "healing": float(row["healing"]),
            "outgoing": float(row["outgoing"]),
            "vitality": float(row["vitality"]),
            "power": float(row["power"]),
            "precision": float(row["precision"]),
            "toughness": float(row["toughness"]),
            "exact": bool(row["exact"]),
            # positive: concentration wasted beyond the cap; negative: missing
            "conc_delta": float(row["overshoot"]) if not row["exact"] else 0.0,
            "rune": row["rune"],
            "food": row["food"],
            "sigil": row["sigil"],
            "utility": row["utility"],
            "relic": row["relic"],
            "conc_infusions": int(row["conc_infusions"]),
            "total_infusions": total_infusions,
            # below the floor the cap was already broken before gear
            "overcapped": bool(row["remainder"] < totals["conc_floor"] - 1),
            "equipment": [
                {"slot": label, "pieces": int(count),
                 "counts": [int(n) for n in meta]}
                for label, count, meta in totals["groups"]
            ],
        }

    return {
        "mode": "boon",
        "ranking": ranking,
        "k": k,
        "best": render_boon_row(solution["best"]),
        "stable_fallback": render_boon_row(solution["stable_fallback"]),
        "zero_toughness": render_boon_row(solution["zero_toughness"]),
    }
