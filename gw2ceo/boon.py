"""Boon-duration optimizer: reach exactly 100% boon duration, then maximize
healing output.

Same philosophy as the crit optimizer, different axes. Boon duration caps at
+100% = 1500 concentration at level 80; every percentage point of boon
duration from runes, the Concentration sigil or traits adds linearly inside
the same capped term and equals 15 concentration. Gear is 3-stat only:
Harrier's pieces carry concentration as a minor stat, Magi's pieces carry
none (their budget goes into healing/precision/vitality instead). Exotic
trinkets take a Platinum Doubloon (+40 concentration) or a Crest of the Magi
(one rarity below the crit mode's exquisite jewels, which do not exist for
these prefixes).

Unlike the crit mode's Assassin's<->Berserker's swap, Harrier's<->Magi's is
not a 1:1 stat trade: the healing lost per point of concentration differs
per slot. The gear search therefore does not just check reachability - a
memoized DP finds, among all assignments hitting the target exactly, the one
with the best (healing, vitality, power, precision) total, in that order.

Outgoing-healing modifiers stack additively in GW2 (wiki-confirmed), so the
two result rankings just sort by different columns: healing power first or
total outgoing % first - the user picks the tab matching their skills' base-
to-coefficient ratio.

Landing on the cap exactly is the point of the tool: a solution only counts
as exact when the model reaches 1500 to the (floating) point. When no exact
split exists, the gear never undershoots - it overcaps by the least possible
amount, so 100% boon duration always holds - and the website shows a warning
for any deviation, even a fraction of a point. Attribute conversions (oils,
traits) are modeled continuously while the game floors them to whole points,
so a sub-point warning can be conservative; the warning keeps that honest
instead of hiding it.
"""

from dataclasses import dataclass
from itertools import combinations

import numpy as np
import pandas as pd

import gw2ceo.general_data as gd
from gw2ceo.dtypes import BuildConstraints
from gw2ceo.profession import BASE_TOUGHNESS, Profession

# tie preferences (lower preferred): stacking effects are fragile, an empty
# slot ("free") loses ties against any real sigil
SIGIL_PRIO = {"transference": 0, "concentration": 0, "free": 1,
              "bounty": 2, "life": 2, "benevolence": 2}
STACKING_SIGILS = ("bounty", "life", "benevolence")
# Castora's bonus needs the healed ally below 50% health, Monk and Herald
# need boons pulsing - a reserved or free-choice slot has no condition
RELIC_PRIO = {"utility": 0, "reserved": 0, "monk": 1, "castora": 1, "herald": 1}

EXACT_EPSILON = 1e-4  # float noise from conversion rates like 0.065


@dataclass(frozen=True)
class Conversions:
    """Active conversion rates of one candidate row (oil + traits). All
    conversions read pre-conversion values and do not chain."""
    to_conc_from_power: float = 0.0
    to_conc_from_healing: float = 0.0
    to_conc_from_vitality: float = 0.0
    to_conc_from_precision: float = 0.0
    to_healing_from_power: float = 0.0

    def conc_equivalent(self, healing, power, precision, vitality):
        return (self.to_conc_from_power * power
                + self.to_conc_from_healing * healing
                + self.to_conc_from_vitality * vitality
                + self.to_conc_from_precision * precision)


class BoonGear:
    """Achievable concentration totals per slot group, valued by healing.

    Each piece is Harrier's (concentration + healing minor, power major) or
    Magi's (healing major, precision + vitality minor); each exotic-trinket
    upgrade slot holds a Platinum Doubloon or a Crest of the Magi. Option
    metadata mirrors the crit mode's (major, minor, none) triples as
    (harrier, magi, 0) resp. (doubloon, crest, 0), so the renderer is shared.

    Concentration option values are conversion-adjusted ("effective"): a
    piece's side stats feed the row's active conversions, so the same gear
    carries different effective concentration under different oils - one
    BoonGear instance exists per conversion profile.
    """

    def __init__(self, build: BuildConstraints, conversions: Conversions):
        if build.weapon_type == "1h":
            full_armor = np.array([2, 0, 1, 1, 1, 1, 1, 1, 1, 2, 2, 1])
        else:
            full_armor = np.array([0, 1, 1, 1, 1, 1, 1, 1, 1, 2, 2, 1])
        armor_names = ["One-handed", "Two-handed", "Chest", "Legs", "Head", "Shoulders",
                       "Gloves", "Boots", "Amulet", "Ring", "Accessory", "Back item"]

        num_asc = pd.Series(np.minimum(build.num_ascended, full_armor), index=armor_names)
        num_ex: pd.Series = pd.Series(full_armor - num_asc, index=armor_names)  # type: ignore

        exotic = gd.gear_stats["Ex", "3p"]
        ascend = gd.gear_stats["Asc", "3p"]
        conv = conversions

        # options per slot group with parallel metadata: option_meta[i][j] is
        # the (harrier, magi, 0) split behind equipment[i][j]; equipment holds
        # (effective concentration, healing, power, precision, vitality)
        self.equipment: list[list[tuple]] = []
        self.groups: list[tuple] = []
        self.option_meta: list[list[tuple]] = []

        def piece_option(gear, slot, harrier, magi):
            """Stat tuple of harrier+magi pieces of one slot; the healing
            value already includes the power->healing conversion share."""
            major, minor = float(gear["Maj", slot]), float(gear["Min", slot])
            healing = minor * harrier + major * magi
            power = major * harrier
            precision = minor * magi
            vitality = minor * magi
            conc = minor * harrier + conv.conc_equivalent(healing, power, precision, vitality)
            return (round(conc, 6), healing + conv.to_healing_from_power * power,
                    power, precision, vitality)

        def add_group(label, count, gear, slot):
            if count == 0:
                return
            options, meta = [], []
            for harrier in range(count + 1):
                options.append(piece_option(gear, slot, harrier, count - harrier))
                meta.append((harrier, count - harrier, 0))
            self.equipment.append(options)
            self.groups.append((label, count))
            self.option_meta.append(meta)

        def split_rarity(label, slot):
            asc, ex = int(num_asc[slot]), int(num_ex[slot])  # type: ignore
            add_group(f"{label} (ascended)" if ex else label, asc, ascend, slot)
            add_group(f"{label} (exotic)" if asc else label, ex, exotic, slot)

        if build.weapon_type == "1h":
            split_rarity("Weapons", "One-handed")
        else:
            split_rarity("Weapon", "Two-handed")
        split_rarity("Chest", "Chest")
        split_rarity("Legs", "Legs")
        split_rarity("Head", "Head")

        # Shoulders/Gloves/Boots share their stat values and are interchangeable
        asc_sgb = int(num_asc[["Shoulders", "Gloves", "Boots"]].sum())
        ex_sgb = int(num_ex[["Shoulders", "Gloves", "Boots"]].sum())
        add_group("Shoulders/Gloves/Boots (ascended)" if ex_sgb else "Shoulders/Gloves/Boots",
                  asc_sgb, ascend, "Shoulders")
        add_group("Shoulders/Gloves/Boots (exotic)" if asc_sgb else "Shoulders/Gloves/Boots",
                  ex_sgb, exotic, "Shoulders")

        split_rarity("Amulet", "Amulet")
        split_rarity("Rings", "Ring")
        split_rarity("Accessories", "Accessory")
        split_rarity("Back item", "Back item")

        # upgrade slots of exotic trinkets: Platinum Doubloon vs Crest of the Magi
        buffs = gd.general_buffs
        num_upgrades = int(num_ex.iloc[8:12].sum())
        if num_upgrades:
            options, meta = [], []
            for doubloons in range(num_upgrades + 1):
                crests = num_upgrades - doubloons
                healing = float(buffs.crest_healing) * crests
                precision = float(buffs.crest_precision) * crests
                vitality = float(buffs.crest_vitality) * crests
                conc = (float(buffs.doubloon_concentration) * doubloons
                        + conv.conc_equivalent(healing, 0, precision, vitality))
                options.append((round(conc, 6), healing, 0.0, precision, vitality))
                meta.append((doubloons, crests, 0))
            self.equipment.append(options)
            self.groups.append(("Upgrades (in exotic trinkets)", num_upgrades))
            self.option_meta.append(meta)

        # bottom-up enumeration of every reachable gear point: effective
        # concentration -> best (healing, vitality, power, precision) tuple
        # and the option choices behind it. A few thousand points at most,
        # so every query afterwards is a binary search.
        points: dict[float, tuple[tuple, tuple]] = {0.0: ((0.0, 0.0, 0.0, 0.0), ())}
        for options in self.equipment:
            merged: dict[float, tuple[tuple, tuple]] = {}
            for conc_sum, (value, choices) in points.items():
                for j, (conc, healing, power, precision, vitality) in enumerate(options):
                    key = round(conc_sum + conc, 6)
                    candidate = ((value[0] + healing, value[1] + vitality,
                                  value[2] + power, value[3] + precision),
                                 choices + (j,))
                    if key not in merged or candidate[0] > merged[key][0]:
                        merged[key] = candidate
            points = merged
        self.conc_points = np.array(sorted(points))
        self.point_values = [points[conc][0] for conc in self.conc_points]
        self.point_choices = [points[conc][1] for conc in self.conc_points]
        self.point_value_matrix = np.array(self.point_values)

    def conc_floor(self) -> float:
        return float(self.conc_points[0])

    def conc_ceiling(self) -> float:
        return float(self.conc_points[-1])

    def query_many(self, needs: np.ndarray) -> np.ndarray:
        """Gear point index per required effective concentration: the exact
        point when one exists, otherwise the smallest point above the need
        (the cap is never undershot while reaching it is possible), or the
        all-Harrier ceiling when even that falls short."""
        return np.minimum(np.searchsorted(self.conc_points, needs - EXACT_EPSILON),
                          len(self.conc_points) - 1)

    def query(self, need: float):
        """(exact, delta, value, choices) for a single required amount."""
        i = int(self.query_many(np.array([float(need)]))[0])
        delta = float(self.conc_points[i]) - need
        return abs(delta) <= EXACT_EPSILON, delta, \
            self.point_values[i], self.point_choices[i]


def _sigil_members(build: BuildConstraints) -> list[tuple]:
    """(name, concentration, healing, outgoing %, boon duration % as
    concentration-equivalent) per sigil; stacking sigils at their 25-stack
    maximum. The Concentration sigil grants duration % (not the attribute),
    so percentage-attribute traits never multiply it. "free" is an empty
    slot for a proc sigil of the user's choice (Water, Renewal ...)."""
    buffs = gd.general_buffs
    members = [
        ("transference", 0.0, 0.0, float(buffs.sigil_transference_pct), 0.0),
        ("concentration", 0.0, 0.0, 0.0,
         float(buffs.sigil_concentration_pct * buffs.conc_per_bd_pct)),
        ("free", 0.0, 0.0, 0.0, 0.0),
    ]
    if build.stacking_sigils:
        members += [
            ("bounty", float(buffs.sigil_bounty), 0.0, 0.0, 0.0),
            ("life", 0.0, float(buffs.sigil_life), 0.0, 0.0),
            ("benevolence", 0.0, 0.0, float(buffs.sigil_benevolence_pct), 0.0),
        ]
    return members


def _sigil_candidates(build: BuildConstraints) -> pd.DataFrame:
    """Both sigil slots are optimized together: every unordered pair of
    distinct sigils competes (only one attribute-stacking sigil can be
    active). In single-sigil mode the other slot is reserved for the user,
    so the sigils compete alone."""
    members = _sigil_members(build)
    if build.single_sigil:
        picks = [(member,) for member in members]
    else:
        picks = [pair for pair in combinations(members, 2)
                 if sum(sigil[0] in STACKING_SIGILS for sigil in pair) <= 1]
    return pd.DataFrame(data=[{
        "sigil": "+".join(sigil[0] for sigil in pick),
        "sigil_conc": sum(sigil[1] for sigil in pick),
        "sigil_healing": sum(sigil[2] for sigil in pick),
        "sigil_outgoing": sum(sigil[3] for sigil in pick),
        "sigil_bd_equiv": sum(sigil[4] for sigil in pick),
        "sigil_stacking": any(sigil[0] in STACKING_SIGILS for sigil in pick),
        "sigil_prio": sum(SIGIL_PRIO[sigil[0]] for sigil in pick),
    } for pick in picks])


def _utility_candidates(build: BuildConstraints) -> pd.DataFrame:
    """The oil slot: three concentration conversions and the outgoing-healing
    oil; 'none' is always in the pool."""
    names = ["none"]
    if build.utility:
        names += ["magnanimous", "toxic", "lucent", "bountiful"]
    return pd.DataFrame(data={"utility": names})


def _oil_conversions(utility: str) -> dict[str, float]:
    buffs = gd.general_buffs
    return {
        "magnanimous": {"vitality": float(buffs.magnanimous_vitality),
                        "toughness": float(buffs.magnanimous_toughness)},
        "toxic": {"power": float(buffs.toxic_power)},
        "lucent": {"power": float(buffs.lucent_power),
                   "precision": float(buffs.lucent_precision)},
    }.get(utility, {})


def _row_conversions(profession: Profession, utility: str) -> tuple[Conversions, float]:
    """Conversion profile of one candidate row and the toughness->conc rate
    (toughness is fixed at its base, so it never enters the gear model)."""
    rates = profession.conversion_rates("concentration")
    for source, rate in _oil_conversions(utility).items():
        rates[source] = rates.get(source, 0.0) + rate
    conv = Conversions(
        to_conc_from_power=rates.get("power", 0.0),
        to_conc_from_healing=rates.get("healing", 0.0),
        to_conc_from_vitality=rates.get("vitality", 0.0),
        to_conc_from_precision=rates.get("precision", 0.0),
        to_healing_from_power=profession.conversion_rates("healing").get("power", 0.0),
    )
    return conv, rates.get("toughness", 0.0)


def _boon_solve(profession: Profession, build: BuildConstraints) -> pd.DataFrame:
    """Score every food x rune x sigil x oil x relic x infusion combination
    against the 1500-concentration-equivalent target."""
    buffs = gd.general_buffs
    target = float(buffs.boon_target)
    per_pct = float(buffs.conc_per_bd_pct)

    if build.food:
        food = gd.boon_food
    else:
        food = pd.DataFrame(data={"concentration": [0], "healing": [0], "outgoing_pct": [0]},
                            index=["no food"])
        food.index.name = "food"

    num_infusions = gd.num_infusions(build.num_ascended, build.weapon_type)
    infusions = pd.DataFrame(data={
        "conc_infusions": list(range(num_infusions + 1)),
        "conc_inf": [5 * i for i in range(num_infusions + 1)],
        "healing_inf": [5 * (num_infusions - i) for i in range(num_infusions + 1)],
    })

    # the relic slot: Herald's concentration and the outgoing-healing relics
    # (Monk at 10 boon-application stacks, Castora at an effective value -
    # its +25% only counts while the healed ally is below 50% health) compete
    # for the slot; reserving it keeps every stat relic out so a proc relic
    # like Karakosa can live there
    if build.relic_reserved:
        relics = {"relic": ["reserved"], "relic_conc": [0.0], "relic_outgoing": [0.0]}
    else:
        relics = {"relic": ["none", "monk", "castora"],
                  "relic_conc": [0.0, 0.0, 0.0],
                  "relic_outgoing": [0.0, float(buffs.relic_monk_pct),
                                     float(buffs.relic_castora_pct)]}
        if build.herald_relic:
            relics["relic"].append("herald")
            relics["relic_conc"].append(float(buffs.relic_herald))
            relics["relic_outgoing"].append(0.0)

    options = pd.merge(food.reset_index(), gd.boon_runes.reset_index(),
                       how="cross", suffixes=("_food", "_rune"))
    options = pd.merge(_sigil_candidates(build), options, how="cross")
    options = pd.merge(_utility_candidates(build), options, how="cross")
    options = pd.merge(pd.DataFrame(data=relics), options, how="cross")
    options = pd.merge(infusions, options, how="cross")

    heal_from_power = profession.conversion_rates("healing").get("power", 0.0)
    toughness = BASE_TOUGHNESS + profession._flat("toughness")

    stats = options
    stats["power_base"] = (buffs.base_power
                           + buffs.might * build.might / 25
                           + profession.additional_power()
                           + profession.power_per_might() * build.might
                           + stats["power"])
    stats["precision_base"] = (buffs.base_precision
                               + profession.additional_precision() + stats["precision"])
    stats["vitality_base"] = (buffs.base_vitality + buffs.jade_bot
                              + profession.additional_vitality() + stats["vitality"])
    # power feeds healing (Vigorous Shouts / Wellspring) before conversions
    stats["healing_raw"] = (profession.additional_healing()
                            + stats["healing_rune"] + stats["healing_food"]
                            + stats["sigil_healing"] + stats["healing_inf"])
    stats["healing_base"] = stats["healing_raw"] + heal_from_power * stats["power_base"]

    # attribute concentration is multiplied by percentage-attribute traits;
    # duration percentages (rune/sigil/trait boon duration) are not attributes
    multiplier = profession.attribute_multiplier()
    stats["conc_attr"] = (profession.additional_concentration()
                          + stats["concentration_rune"] + stats["concentration_food"]
                          + stats["sigil_conc"] + stats["relic_conc"] + stats["conc_inf"])
    stats["bd_equiv"] = (profession.boon_duration_pct() * per_pct
                         + stats["boon_pct"] * per_pct + stats["sigil_bd_equiv"])

    # per-oil conversion profiles: each needs its own gear model, because the
    # gear's side stats feed the conversions ("effective" concentration).
    # Only a handful of profiles exist, so everything runs vectorized per oil.
    for name in ("remainder", "overshoot", "healing", "vitality", "power", "precision"):
        stats[name] = 0.0
    stats["exact"] = False
    utilities = stats["utility"].to_numpy()
    for utility in dict.fromkeys(utilities):
        mask = utilities == utility
        conv, toughness_rate = _row_conversions(profession, str(utility))
        gear = BoonGear(build, conv)

        # conversions read pre-conversion (and pre-multiplier) values
        conc_from_base = (conv.conc_equivalent(
            stats.loc[mask, "healing_raw"], stats.loc[mask, "power_base"],
            stats.loc[mask, "precision_base"], stats.loc[mask, "vitality_base"])
            + toughness_rate * toughness)
        remainder = ((target - stats.loc[mask, "bd_equiv"]) / multiplier
                     - stats.loc[mask, "conc_attr"] - conc_from_base).round(6)

        index = gear.query_many(remainder.to_numpy())
        delta = gear.conc_points[index] - remainder
        stats.loc[mask, "remainder"] = remainder
        stats.loc[mask, "overshoot"] = delta * multiplier  # panel points
        stats.loc[mask, "exact"] = abs(delta) <= EXACT_EPSILON
        gear_values = gear.point_value_matrix[index]
        stats.loc[mask, "healing"] = (stats.loc[mask, "healing_base"]
                                      + gear_values[:, 0]) * multiplier
        stats.loc[mask, "vitality"] = (stats.loc[mask, "vitality_base"]
                                       + gear_values[:, 1]) * multiplier
        stats.loc[mask, "power"] = (stats.loc[mask, "power_base"]
                                    + gear_values[:, 2]) * multiplier
        stats.loc[mask, "precision"] = (stats.loc[mask, "precision_base"]
                                        + gear_values[:, 3]) * multiplier

    stats["concentration_total"] = target + stats["overshoot"]

    # outgoing healing stacks additively in GW2
    stats["outgoing"] = (profession.outgoing_heal_pct()
                         + stats["outgoing_pct"] + stats["sigil_outgoing"]
                         + stats["relic_outgoing"])
    bountiful = (stats["utility"] == "bountiful").astype(float)
    stats["outgoing"] += bountiful * (stats["healing"] * float(buffs.bountiful_healing_pct)
                                      + stats["concentration_total"]
                                      * float(buffs.bountiful_concentration_pct))

    # a relic-less winner just means no stat relic earned the slot
    stats.loc[stats["relic"] == "none", "relic"] = "utility"

    stats["relic_prio"] = stats["relic"].map(RELIC_PRIO).fillna(0)  # type: ignore
    # the cap is never given up: rows at or above 100% boon duration ("capped",
    # their overcap already priced into the stat totals) beat rows below it
    stats["capped"] = stats["overshoot"] >= -EXACT_EPSILON
    stats["shortfall"] = np.where(stats["capped"], 0.0, -stats["overshoot"])
    stats["miss"] = abs(stats["overshoot"])
    return stats


def _rank(stats: pd.DataFrame, first: str, second: str) -> pd.DataFrame:
    """Hitting the cap exactly is the point of the tool; a forced overcap
    (never an undershoot) is priced into the stats and only breaks late ties.
    The remaining keys implement the agreed stat order."""
    by, ascending = zip(
        ("exact", False),
        ("capped", False),
        ("shortfall", True),
        (first, False),
        (second, False),
        ("vitality", False),
        ("power", False),
        ("precision", False),
        ("miss", True),
        ("conc_infusions", True),
        ("sigil_prio", True),
        ("relic_prio", True),
    )
    return stats.sort_values(by=list(by), ascending=list(ascending))


def gear_totals(profession: Profession, build: BuildConstraints, row: pd.Series) -> dict:
    """The gear assignment behind a rendered row: equipment groups (with the
    (harrier, magi, 0) split per group) and the gear model's bounds."""
    conv, _ = _row_conversions(profession, str(row["utility"]))
    gear = BoonGear(build, conv)
    _, _, _, choices = gear.query(float(row["remainder"]))  # type: ignore
    groups = [(label, count, meta[choice]) for (label, count), meta, choice
              in zip(gear.groups, gear.option_meta, choices)]
    return {
        "groups": groups,
        "conc_floor": gear.conc_floor(),
        "conc_ceiling": gear.conc_ceiling(),
    }


def calc_boon(profession: Profession, build: BuildConstraints,
              ranking: str = "healing", k: float = 2000.0) -> dict:
    """One ranking of the candidate set. `ranking` picks the objective once
    the cap is met: "healing" ranks by healing power (outgoing % as the
    tie-breaker), "outgoing" the other way around, and "k" by the effective
    healing index (K + healing power) x (1 + outgoing%), where K is the
    base-to-coefficient ratio of a reference healing skill - the two named
    rankings are exactly its K->0 and K->infinity edges.

    The stable backup avoids kill-stack sigils when the best build relies on
    one (stacks are unrecoverable after a downstate without new kills). The
    Herald relic needs no backup: its stacks rebuild within seconds of boon
    pulsing, and its checkbox removes it from the pool entirely."""
    stats = _boon_solve(profession, build)
    if ranking == "k":
        stats["effective_healing"] = ((k + stats["healing"])
                                      * (1 + stats["outgoing"] / 100))
        order = ("effective_healing", "healing")
    elif ranking == "outgoing":
        order = ("outgoing", "healing")
    else:
        order = ("healing", "outgoing")

    ranked = _rank(stats, *order)
    best = ranked.iloc[0]
    backup = None
    if best["sigil_stacking"]:
        stable = ranked.loc[~ranked["sigil_stacking"]]
        if not stable.empty:
            backup = stable.iloc[0]
    return {"best": best, "stable_fallback": backup}
