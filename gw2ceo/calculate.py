import numpy as np
import pandas as pd

import gw2ceo.general_data as gd
from gw2ceo.dtypes import BuildConstraints
from gw2ceo.gearselect import GearSelect
from gw2ceo.profession import Profession

TARGET = 2995  # precision-equivalent for 100% critical chance at level 80

# tie preferences at equal effective power (lower is preferred):
# a damage sigil is a free bonus at night, stacking sigils are fragile
SIGIL_PRIO = {"impact": 0, "force": 0, "accuracy": 1, "perception": 2, "bloodlust": 2}
# sharpening stones last longer than writs; the accuracy writ additionally
# puts the crit cap at risk below 90% health
UTILITY_PRIO = {"none": 0, "stones": 0, "writ_strength": 1, "writ_accuracy": 2}
FOOD_PRIO = {"truffle": 1, "curry": 2, "butternut": 2}


def _sigil_candidates(build: BuildConstraints) -> pd.DataFrame:
    """Candidates for the second sigil slot (the first holds a damage sigil
    like Force, which multiplies every option equally and cancels out).
    Stacking sigils are modeled at their 25-stack maximum."""
    sigils = pd.DataFrame(data={
        "sigil": ["none", "accuracy", "perception", "bloodlust"],
        "chance": [0.0, float(gd.general_buffs.sigil_accuracy), 0.0, 0.0],
        "sigil_precision": [0.0, 0.0, float(gd.general_buffs.sigil_perception), 0.0],
        "sigil_power": [0.0, 0.0, 0.0, float(gd.general_buffs.sigil_bloodlust)],
    })
    if not build.stacking_sigils:
        sigils = sigils.loc[~sigils["sigil"].isin(["perception", "bloodlust"])]
    return sigils


def _utility_candidates(build: BuildConstraints) -> pd.DataFrame:
    """Candidates for the utility-consumable slot: sharpening stones (handled
    as a conversion later) and the flat +200 writs (active above 90% health)
    are independent toggles; 'none' is always in the pool, so unticking both
    simply leaves the slot empty."""
    names = ["none"]
    precisions = [0.0]
    powers = [0.0]
    if build.utility:
        names.append("stones")
        precisions.append(0.0)
        powers.append(0.0)
    if build.writs:
        names += ["writ_accuracy", "writ_strength"]
        precisions += [float(gd.general_buffs.writ_precision), 0.0]
        powers += [0.0, float(gd.general_buffs.writ_power)]
    return pd.DataFrame(data={"utility": names, "util_precision": precisions,
                              "util_power": powers})


def _relic_candidates(build: BuildConstraints) -> pd.DataFrame:
    """The relic slot: Mistburn's crit chance (a passive while at or above
    10 might, so it only qualifies when the might setting reaches the
    threshold) competes against a damage relic, handled later as a
    multiplicative branch like the Impact sigil."""
    relics = {"relic": ["none"], "relic_chance": [0.0]}
    if build.might >= gd.general_buffs.relic_might_threshold:
        relics = {"relic": ["none", "mistburn"],
                  "relic_chance": [0.0, float(gd.general_buffs.relic_mistburn)]}
    return pd.DataFrame(data=relics)


def _mixed_runes() -> pd.DataFrame | None:
    """All 5+1/4+2/3+3 two-rune mixes, built from the per-piece bonuses in
    assets/rune_tiers.csv. Used only as a rescue when no full rune set can
    hit the crit cap exactly - mixing creates finer precision steps."""
    tiers = gd.rune_tiers
    if tiers is None:
        return None
    cumulative = {}
    for rune, group in tiers.groupby("rune"):
        by_count = group.sort_values(by=["tier"])[["power", "precision", "ferocity", "vitality"]].cumsum()
        cumulative[rune] = by_count.set_axis(group.sort_values(by=["tier"])["tier"].tolist())
    names = sorted(cumulative)
    rows = {}
    for first_index, first in enumerate(names):
        for second in names[first_index + 1:]:
            for count in range(1, 6):
                mix = cumulative[first].loc[count] + cumulative[second].loc[6 - count]
                rows[f"{first}({count})+{second}({6 - count})"] = mix
    mixed = pd.DataFrame(rows).T
    mixed.index.name = "rune"
    return pd.concat([gd.runes, mixed])


def _solve(profession: Profession, build: BuildConstraints, runes: pd.DataFrame) -> pd.DataFrame:
    """Score every food x rune x sigil x utility x infusion combination and
    return the fully ranked table."""
    min_stats = gd.full_armor("Min", build.num_ascended, build.gear_environment, build.weapon_type)
    maj_stats = gd.full_armor("Maj", build.num_ascended, build.gear_environment, build.weapon_type)

    if build.food:
        food = gd.food
    else:
        food = pd.DataFrame(data={"power": [0], "precision": [0], "ferocity": [0]}, index=["no food"])
        food.index.name = "food"

    num_infusions = gd.num_infusions(build.num_ascended, build.weapon_type)
    infusions = pd.DataFrame(data={
        "prec_infusions": list(range(num_infusions + 1)),
        "precision_inf": [5 * i for i in range(num_infusions + 1)],
        "power_inf": [5 * (num_infusions - i) for i in range(num_infusions + 1)],
    })

    options = pd.merge(food.reset_index(), runes.reset_index(), how="cross", suffixes=("_food", "_rune"))
    options = pd.merge(_sigil_candidates(build), options, how="cross")
    options = pd.merge(_utility_candidates(build), options, how="cross")
    options = pd.merge(_relic_candidates(build), options, how="cross")
    options = pd.merge(infusions, options, how="cross")

    options["power"] = options["power_rune"] + options["power_food"] + options["power_inf"]
    options["precision"] = options["precision_rune"] + options["precision_food"] + options["precision_inf"]
    options["ferocity"] = options["ferocity_rune"] + options["ferocity_food"]
    # only runes carry vitality among the merged tables, so no suffix applied
    options = options.rename(columns={"vitality": "vitality_rune"})

    stats = options[["prec_infusions", "sigil", "sigil_precision", "sigil_power",
                     "utility", "util_precision", "util_power", "relic", "relic_chance",
                     "food", "rune", "power", "precision", "chance", "ferocity",
                     "vitality_rune"]].copy()
    stats[["power", "precision", "ferocity", "chance"]] = \
        stats[["power", "precision", "ferocity", "chance"]].astype(float)

    stats["precision"] += gd.general_buffs.base_precision + stats["sigil_precision"] + stats["util_precision"]
    stats["chance"] += profession.additional_crit_chance() + stats["relic_chance"]
    if build.fury:
        stats["chance"] += gd.general_buffs.fury
    stats["precision"] += profession.additional_precision()

    stats["power"] += (gd.general_buffs.base_power
                       + gd.general_buffs.might * build.might / 25
                       + profession.additional_power()
                       + profession.power_per_might() * build.might
                       + stats["sigil_power"] + stats["util_power"])
    stats["ferocity"] += profession.additional_ferocity()
    stats["vitality"] = (gd.general_buffs.base_vitality + gd.general_buffs.jade_bot
                         + profession.additional_vitality() + stats["vitality_rune"])

    vit_prec_conversion = profession.vit_prec_conversion()
    stats["precision"] += stats["vitality"] * vit_prec_conversion

    stats["remainder"] = TARGET - stats["precision"] - stats["chance"]
    stats["precision"] += stats["remainder"]

    # distribute the armor's Maj/Min budget: the armor must contribute the
    # remaining precision, the rest of its budget goes into power/ferocity
    if build.gear_environment == "3p":
        stats["ferocity"] += min_stats
        high = stats["remainder"] > min_stats
        armor_precision = np.where(
            high,
            stats["remainder"],
            (stats["remainder"] - min_stats * vit_prec_conversion) / (1 - vit_prec_conversion),
        )
        stats["armor_precision"] = armor_precision
        stats["power"] += np.where(high, min_stats + maj_stats - armor_precision, maj_stats)
        stats["vitality"] += np.where(high, 0, min_stats - armor_precision)
    else:
        stats["armor_precision"] = stats["remainder"] - min_stats * vit_prec_conversion
        stats["power"] += maj_stats
        stats["ferocity"] += min_stats + maj_stats - stats["armor_precision"]
        stats["vitality"] += min_stats

    stats["vitality"], stats["power"], stats["ferocity"] = profession.stat_conversion(
        stats["vitality"], stats["power"], stats["precision"], stats["ferocity"])

    # sharpening stones convert precision and ferocity into power
    stones = (stats["utility"] == "stones").astype(float)
    stats["power"] += stones * (stats["precision"] * gd.general_buffs.stones_prec
                                + stats["ferocity"] * gd.general_buffs.stones_fero)

    # the low-remainder region (armor precision below the all-minor floor) is
    # priced with the Valkyrie trade in 3-stat gear, so the gear check gets
    # the Valkyrie-capable options there; 4-stat gear has no such prefix
    gear = GearSelect(build)
    gear_low = GearSelect(build, valkyrie=True) if build.gear_environment == "3p" else gear
    low_region = stats["remainder"] <= min_stats
    stats["overshoot"] = [
        (gear_low if low else gear).overshoot_values(remainder)
        for remainder, low in zip(stats["armor_precision"], low_region)
    ]
    stats["absolute_overshoot"] = [min(overshoot) for overshoot in stats["overshoot"]]
    stats["exact"] = stats["absolute_overshoot"] == 0

    # a forced overshoot eats into the armor budget, so rank those rows with
    # the (approximate) honest effective power instead of the ideal one
    stats["ferocity_equivalent"] = profession.ferocity_equivalent(stats["ferocity"])
    stats["effective_power"] = ((stats["power"] - stats["absolute_overshoot"])
                                * (1.5 + stats["ferocity_equivalent"] / 1500))

    stats["absolute_remainder"] = np.minimum(abs(stats["armor_precision"] - min_stats),
                                             abs(stats["armor_precision"] - maj_stats))
    stats["food_prio"] = stats["food"].map(FOOD_PRIO).fillna(0)  # type: ignore
    stats["utility_prio"] = stats["utility"].map(UTILITY_PRIO).fillna(0)  # type: ignore

    # the sigil-less rows become the damage-sigil branch. With both slots
    # free that is the second slot's 3% sigil (Impact by day, Night at
    # night) next to an always-on Force that cancels out of the comparison;
    # with only one free slot (the other reserved, e.g. Energy) the stat
    # sigils compete against Force's 5% itself.
    if build.single_sigil:
        branch_sigil, branch_bonus = "force", float(gd.general_buffs.sigil_force)
    else:
        branch_sigil, branch_bonus = "impact", float(gd.general_buffs.sigil_impact)
    damage_sigil = stats.loc[stats["sigil"] == "none"].copy()
    damage_sigil["sigil"] = branch_sigil
    damage_sigil["effective_power"] *= 1 + branch_bonus
    stats = pd.concat([stats.loc[stats["sigil"] != "none"], damage_sigil], ignore_index=True)
    stats["sigil_prio"] = stats["sigil"].map(SIGIL_PRIO).fillna(0)  # type: ignore

    # likewise the relic-less rows become the "damage relic" branch
    # (Fireworks/Thief/Claw): same gear solution, scaled effective power
    damage_relic = stats.loc[stats["relic"] == "none"].copy()
    damage_relic["relic"] = "damage"
    damage_relic["effective_power"] *= 1 + gd.general_buffs.relic_damage
    stats = pd.concat([stats.loc[stats["relic"] != "none"], damage_relic], ignore_index=True)
    # at equal effective power the damage relic is safer than Mistburn's
    # might-threshold condition
    stats["relic_prio"] = stats["relic"].map({"damage": 0, "mistburn": 1}).fillna(0)  # type: ignore

    # hitting the cap exactly is the point of the tool; effective power only
    # ranks within that, and the remaining keys break ties
    by, ascending = zip(
        ("exact", False),
        ("effective_power", False),
        ("prec_infusions", True),
        ("absolute_remainder", True),
        ("utility_prio", True),
        ("sigil_prio", True),
        ("relic_prio", True),
        ("food_prio", True),
    )
    stats.sort_values(by=list(by), ascending=list(ascending), inplace=True)  # type: ignore
    return stats


def calc_ep(profession: Profession, build: BuildConstraints) -> dict:
    stats = _solve(profession, build, gd.runes)

    # rescue: when no full rune set can hit the cap exactly, mixed rune sets
    # provide finer precision steps (only then - mixes are never preferred)
    if not bool(stats.iloc[0]["exact"]):
        extended_runes = _mixed_runes()
        if extended_runes is not None:
            rescued = _solve(profession, build, extended_runes)
            if bool(rescued.iloc[0]["exact"]):
                stats = rescued

    best = stats.iloc[0]

    # one combined backup: when the winner relies on stacking sigils and/or
    # the accuracy writ, offer the best build using neither, so a downstate
    # or low health never silently costs the crit cap (the relic needs no
    # backup - swapping Mistburn for a damage relic keeps the cap)
    stable_fallback = None
    if best["sigil"] in ("perception", "bloodlust") or best["utility"] == "writ_accuracy":
        stable = stats.loc[stats["sigil"].isin(["accuracy", "impact", "force"])
                           & stats["utility"].isin(["stones", "writ_strength", "none"])]
        if not stable.empty:
            stable_fallback = stable.iloc[0]

    return {"best": best, "stable_fallback": stable_fallback}
