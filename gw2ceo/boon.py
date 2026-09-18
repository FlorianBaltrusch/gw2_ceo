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

Attribute conversions (oils, traits) are modeled continuously, while the game
floors each converted amount to whole points. A solution within one point of
concentration (0.07% boon duration) of the cap therefore counts as on-cap:
the in-game integer arithmetic decides that last point, not this model.
Without that slack every conversion oil would be locked out of "exact" by
fractions the game itself never sees.
"""

from dataclasses import dataclass

import numpy as np
import pandas as pd

import gw2ceo.general_data as gd
from gw2ceo.dtypes import BuildConstraints
from gw2ceo.profession import BASE_TOUGHNESS, Profession

# tie preferences (lower preferred): stacking effects are fragile
SIGIL_PRIO = {"transference": 0, "free": 0, "concentration": 0,
              "bounty": 2, "life": 2, "benevolence": 2}
STACKING_SIGILS = ("bounty", "life", "benevolence")
RELIC_PRIO = {"utility": 0, "herald": 1}

CAP_SLACK = 1.0  # one point of concentration; see the module docstring


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
        # the value tuples packed into one float for vectorized argmax
        # (each component stays below 4096, so the packing is collision-free)
        healing, vitality, power, precision = self.point_value_matrix.T
        self.point_scores = ((healing * 4096 + vitality) * 4096 + power) * 4096 + precision

    def conc_floor(self) -> float:
        return float(self.conc_points[0])

    def conc_ceiling(self) -> float:
        return float(self.conc_points[-1])

    def query_many(self, needs: np.ndarray):
        """Best gear point per required effective concentration. Points
        within CAP_SLACK of the need count as exact hits (the best value
        among them wins); otherwise the nearest overshooting point is
        chosen, or the all-Harrier ceiling when even that falls short.
        Returns (exact, point index) arrays."""
        low = np.searchsorted(self.conc_points, needs - CAP_SLACK)
        high = np.searchsorted(self.conc_points, needs + CAP_SLACK, side="right")
        exact = low < high
        nearest = np.minimum(np.searchsorted(self.conc_points, needs),
                             len(self.conc_points) - 1)
        index = np.where(exact, np.minimum(low, len(self.conc_points) - 1), nearest)
        for i in np.flatnonzero(exact & (high - low > 1)):
            index[i] = low[i] + int(np.argmax(self.point_scores[low[i]:high[i]]))
        return exact, index

    def query(self, need: float):
        """(exact, delta, value, choices) for a single required amount."""
        exact, index = self.query_many(np.array([float(need)]))
        i = int(index[0])
        return bool(exact[0]), float(self.conc_points[i]) - need, \
            self.point_values[i], self.point_choices[i]


def _sigil_candidates(build: BuildConstraints) -> pd.DataFrame:
    """Candidates for the second sigil slot (the first holds Transference,
    whose +10% outgoing healing reaches every option equally). Stacking
    sigils are modeled at their 25-stack maximum and end on downstate."""
    buffs = gd.general_buffs
    sigils = pd.DataFrame(data={
        "sigil": ["none", "concentration", "bounty", "life", "benevolence"],
        "sigil_conc": [0.0, float(buffs.sigil_concentration_pct * buffs.conc_per_bd_pct),
                       float(buffs.sigil_bounty), 0.0, 0.0],
        "sigil_healing": [0.0, 0.0, 0.0, float(buffs.sigil_life), 0.0],
        "sigil_outgoing": [0.0, 0.0, 0.0, 0.0, float(buffs.sigil_benevolence_pct)],
    })
    if not build.stacking_sigils:
        sigils = sigils.loc[~sigils["sigil"].isin(STACKING_SIGILS)]
    return sigils


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

    relics = {"relic": ["none"], "relic_conc": [0.0]}
    if build.herald_relic:
        relics = {"relic": ["none", "herald"], "relic_conc": [0.0, float(buffs.relic_herald)]}

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

    stats["conc_flat"] = (profession.additional_concentration()
                          + profession.boon_duration_pct() * per_pct
                          + stats["concentration_rune"] + stats["boon_pct"] * per_pct
                          + stats["concentration_food"] + stats["sigil_conc"]
                          + stats["relic_conc"] + stats["conc_inf"])

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

        # conversions read pre-conversion values, hence healing_raw
        conc_from_base = (conv.conc_equivalent(
            stats.loc[mask, "healing_raw"], stats.loc[mask, "power_base"],
            stats.loc[mask, "precision_base"], stats.loc[mask, "vitality_base"])
            + toughness_rate * toughness)
        remainder = (target - stats.loc[mask, "conc_flat"] - conc_from_base).round(6)

        exact, index = gear.query_many(remainder.to_numpy())
        stats.loc[mask, "remainder"] = remainder
        stats.loc[mask, "overshoot"] = gear.conc_points[index] - remainder
        stats.loc[mask, "exact"] = exact
        gear_values = gear.point_value_matrix[index]
        stats.loc[mask, "healing"] = stats.loc[mask, "healing_base"] + gear_values[:, 0]
        stats.loc[mask, "vitality"] = stats.loc[mask, "vitality_base"] + gear_values[:, 1]
        stats.loc[mask, "power"] = stats.loc[mask, "power_base"] + gear_values[:, 2]
        stats.loc[mask, "precision"] = stats.loc[mask, "precision_base"] + gear_values[:, 3]

    stats["concentration_total"] = target + stats["overshoot"]

    # outgoing healing stacks additively in GW2; Transference occupies the
    # first sigil slot unless that slot is reserved (single-sigil mode)
    stats["outgoing"] = (profession.outgoing_heal_pct()
                         + stats["outgoing_pct"] + stats["sigil_outgoing"])
    bountiful = (stats["utility"] == "bountiful").astype(float)
    stats["outgoing"] += bountiful * (stats["healing"] * float(buffs.bountiful_healing_pct)
                                      + stats["concentration_total"]
                                      * float(buffs.bountiful_concentration_pct))
    if build.single_sigil:
        # the stat sigils compete against Transference itself
        transference = stats.loc[stats["sigil"] == "none"].copy()
        transference["sigil"] = "transference"
        transference["outgoing"] += float(buffs.sigil_transference_pct)
        stats = pd.concat([stats.loc[stats["sigil"] != "none"], transference],
                          ignore_index=True)
    else:
        stats["outgoing"] += float(buffs.sigil_transference_pct)
        stats.loc[stats["sigil"] == "none", "sigil"] = "free"

    # the relic-less rows become the "utility relic of your choice" branch
    utility_relic = stats.loc[stats["relic"] == "none"].copy()
    utility_relic["relic"] = "utility"
    stats = pd.concat([stats.loc[stats["relic"] != "none"], utility_relic],
                      ignore_index=True)

    stats["sigil_prio"] = stats["sigil"].map(SIGIL_PRIO).fillna(0)  # type: ignore
    stats["relic_prio"] = stats["relic"].map(RELIC_PRIO).fillna(0)  # type: ignore
    # sub-point deltas inside the slack are noise, not misses
    stats["miss"] = np.where(stats["exact"], 0.0, abs(stats["overshoot"]))
    return stats


def _rank(stats: pd.DataFrame, first: str, second: str) -> pd.DataFrame:
    """Hitting the cap exactly is the point of the tool; among the misses the
    smallest miss wins. The remaining keys implement the agreed stat order."""
    by, ascending = zip(
        ("exact", False),
        ("miss", True),
        (first, False),
        (second, False),
        ("vitality", False),
        ("power", False),
        ("precision", False),
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


def calc_boon(profession: Profession, build: BuildConstraints) -> dict:
    """Two rankings of the same candidate set: most healing power first and
    most outgoing healing first. Each comes with a stable backup avoiding
    stacking effects (kill-stack sigils, Relic of the Herald) whenever the
    best build relies on one."""
    stats = _boon_solve(profession, build)

    def best_and_backup(first, second):
        ranked = _rank(stats, first, second)
        best = ranked.iloc[0]
        backup = None
        if best["sigil"] in STACKING_SIGILS or best["relic"] == "herald":
            stable = ranked.loc[~ranked["sigil"].isin(STACKING_SIGILS)
                                & (ranked["relic"] != "herald")]
            if not stable.empty:
                backup = stable.iloc[0]
        return {"best": best, "stable_fallback": backup}

    return {"healing": best_and_backup("healing", "outgoing"),
            "outgoing": best_and_backup("outgoing", "healing")}
