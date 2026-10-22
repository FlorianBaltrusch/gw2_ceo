from functools import cache

import numpy as np
import pandas as pd

from dtypes import BuildConstraints
from general_data import gear_stats


class GearSelect:
    """Achievable armor-precision totals per slot group.

    Each piece normally comes as precision-major (Assassin's/Marauder) or
    precision-minor (Berserker's/Dragon's). With valkyrie=True (3-stat gear
    only) a third option per piece carries no precision at all (Valkyrie:
    the minor precision becomes vitality) - the solver's low-remainder
    branch prices exactly that trade, so the option is only offered there.
    """

    def __init__(self, build: BuildConstraints, valkyrie: bool = False):
        self.constraints = build
        self.valkyrie = valkyrie and build.gear_environment == "3p"

        if build.weapon_type == "1h":
            full_armor = np.array([2,0,1,1,1,1,1,1,1,2,2,1])
        else:
            full_armor = np.array([0,1,1,1,1,1,1,1,1,2,2,1])

        armor_names = ["One-handed", "Two-handed", "Chest", "Legs", "Head", "Shoulders", "Gloves", "Boots", "Amulet", "Ring", "Accessory", "Back item"]

        num_asc = pd.Series(np.minimum(build.num_ascended, full_armor), index=armor_names)
        num_ex: pd.Series = pd.Series(full_armor - num_asc, index=armor_names) # type: ignore

        exotic = gear_stats["Ex", build.gear_environment]
        ascend = gear_stats["Asc", build.gear_environment]

        min_gear = exotic["Min"] * num_ex + ascend["Min"] * num_asc
        maj_gear = exotic["Maj"] * num_ex + ascend["Maj"] * num_asc
           

        # options per slot group with parallel metadata: option_meta[i][j] is
        # the (precision-major, precision-minor, no-precision) piece split
        # behind equipment[i][j], groups[i] the (label, piece count) and
        # group_budgets[i] the (Maj, Min) stat budget of one piece
        self.equipment = []
        self.groups = []
        self.option_meta = []
        self.group_budgets = []

        def add_group(label, count, options, meta, budgets=(0, 0)):
            self.equipment.append(options)
            self.groups.append((label, count))
            self.option_meta.append(meta)
            self.group_budgets.append(budgets)

        def spread(gear, slot, count):
            """all splits of `count` pieces of one slot across the variants"""
            options, meta = [], []
            for none_count in (range(count + 1) if self.valkyrie else [0]):
                for major in range(count - none_count + 1):
                    minor = count - none_count - major
                    options.append(gear["Maj", slot] * major + gear["Min", slot] * minor)
                    meta.append((major, minor, none_count))
            return options, meta, (gear["Maj", slot], gear["Min", slot])

        def single(label, min_value, maj_value):
            options = [min_value, maj_value]
            meta = [(0, 1, 0), (1, 0, 0)]
            if self.valkyrie:
                options.append(0)
                meta.append((0, 0, 1))
            add_group(label, 1, options, meta, (maj_value, min_value))

        # The group order is the tie preference among stat-identical splits
        # (get_equipment): the group listed first takes as many precision-
        # major pieces as any exact split allows, then the next group, and
        # so on. The order follows the in-game panel: head, shoulders, chest,
        # gloves, legs, boots, then the weapons, back item, accessories,
        # amulet, rings, and the jewels last. Which piece carries which
        # prefix never changes the stats (precision trades 1:1 per piece).
        single("Head", min_gear["Head"], maj_gear["Head"])
        single("Shoulders", min_gear["Shoulders"], maj_gear["Shoulders"])
        single("Chest", min_gear["Chest"], maj_gear["Chest"])
        single("Gloves", min_gear["Gloves"], maj_gear["Gloves"])
        single("Legs", min_gear["Legs"], maj_gear["Legs"])
        single("Boots", min_gear["Boots"], maj_gear["Boots"])

        # Weapon
        if build.weapon_type == "1h":
            add_group("Weapons (ascended)", num_asc["One-handed"],
                      *spread(ascend, "One-handed", num_asc["One-handed"]))
            add_group("Weapons (exotic)", num_ex["One-handed"],
                      *spread(exotic, "One-handed", num_ex["One-handed"]))
        else:
            if num_asc["Two-handed"] == 0:
                add_group("", 0, [0], [(0, 0, 0)])
            single("Weapon", min_gear["Two-handed"], maj_gear["Two-handed"])
            if num_ex["Two-handed"] == 0:
                add_group("", 0, [0], [(0, 0, 0)])

        # Trinkets
        single("Back item", min_gear["Back item"], maj_gear["Back item"])
        add_group("Accessories (ascended)", num_asc["Accessory"], *spread(ascend, "Accessory", num_asc["Accessory"]))
        add_group("Accessories (exotic)", num_ex["Accessory"], *spread(exotic, "Accessory", num_ex["Accessory"]))
        single("Amulet", min_gear["Amulet"], maj_gear["Amulet"])
        add_group("Rings (ascended)", num_asc["Ring"], *spread(ascend, "Ring", num_asc["Ring"]))
        add_group("Rings (exotic)", num_ex["Ring"], *spread(exotic, "Ring", num_ex["Ring"]))

        # Jewels (upgrade slots of exotic trinkets)
        num_jewels = int(num_ex.iloc[8:12].sum())
        add_group("Jewels (in exotic trinkets)", num_jewels, *spread(exotic, "Jewel", num_jewels))

        # memoize per instance (a class-level @cache would keep every
        # instance alive for the lifetime of the server)
        self.overshoot_values = cache(self._overshoot_values)
        self.suffix_exact = cache(self._suffix_exact)
        self._point_table = None

    def _preference(self, i):
        """Option indices of group i in the tie preference: the most
        precision-major pieces first, among equal counts the fewest Valkyrie."""
        metas = self.option_meta[i]
        return sorted(range(len(metas)), key=lambda j: (-metas[j][0], metas[j][2]))

    def point_table(self):
        """Every reachable armor-precision total with the best complementary
        stats and the choices behind it: (precision array, (power, ferocity,
        vitality) matrix, choices list), sorted by precision. 3-stat gear
        pays precision from power (ferocity is fixed), 4-stat gear from
        ferocity (power is fixed); "best" maximizes (power + ferocity,
        vitality) - the fixed part cancels within an environment. Built
        lazily: only the no-crit-cap mode needs it."""
        if self._point_table is None:
            four_stats = self.constraints.gear_environment == "4p"
            points = {0.0: ((0.0, 0.0, 0.0), ())}
            for i, ((maj, mino), options, metas) in enumerate(zip(self.group_budgets,
                                                                  self.equipment, self.option_meta)):
                merged = {}
                for prec_sum, (value, choices) in points.items():
                    # equal keys keep the first candidate: the tie preference
                    # order makes that the split favouring the groups listed first
                    for j in self._preference(i):
                        option, (major, minor, none) = options[j], metas[j]
                        if four_stats:
                            power = maj * (major + minor)
                            ferocity = mino * major + maj * minor
                            vitality = mino * (major + minor)
                        else:
                            power = mino * major + maj * (minor + none)
                            ferocity = mino * (major + minor + none)
                            vitality = mino * none
                        key = round(prec_sum + option, 6)
                        candidate = ((value[0] + power, value[1] + ferocity,
                                      value[2] + vitality), choices + (j,))
                        rank = (candidate[0][0] + candidate[0][1], candidate[0][2])
                        if (key not in merged
                                or rank > (merged[key][0][0] + merged[key][0][1],
                                           merged[key][0][2])):
                            merged[key] = candidate
                points = merged
            precision = np.array(sorted(points))
            values = np.array([points[p][0] for p in precision])
            choices = [points[p][1] for p in precision]
            self._point_table = (precision, values, choices)
        return self._point_table


    def _overshoot_values(self, target, i=None):
        if i is None:
            i = len(self.equipment)
        if target <= 0:
            min_equip = sum(min(slot) for slot in self.equipment[:i])
            min_overshoot = -target + min_equip
            return np.array([0 if min_overshoot == 0 else np.inf, min_overshoot])
        if i == 0:
            return np.array([target, np.inf])
        return np.min(
            [self.overshoot_values(target - stat, i - 1) for stat in self.equipment[i - 1]], axis=0
        )


    def _suffix_exact(self, target, i):
        """Can the groups from i on sum to target exactly? (stat values are
        whole points, so a miss is at least one point away)"""
        if i == len(self.equipment):
            return abs(target) <= 1e-6
        return any(self.suffix_exact(target - option, i + 1) for option in self.equipment[i])

    def get_equipment(self, target, i=0):
        """Every exact split of the groups from i on, in the tie preference
        order: the group listed first takes the most precision-major pieces
        any exact split allows, then the next group under that, and so on."""
        if not self.suffix_exact(target, i):
            return
        if i == len(self.equipment):
            yield []
            return
        for j in self._preference(i):
            for rest in self.get_equipment(target - self.equipment[i][j], i + 1):
                yield [j] + rest

    def get_best_equipment(self, target):
        """The exact assignment with the best complementary stats, or None.

        In the normal region every split reaching the same precision has
        identical totals (the major<->minor swap trades 1:1), but with
        Valkyrie pieces they differ: an Assassin's piece paid for with an
        extra Valkyrie loses power. Ranked like point_table: by the stat the
        precision trades against per environment (power in 3-stat gear,
        ferocity in 4-stat gear - their sum, since the other is fixed),
        then vitality."""
        four_stats = self.constraints.gear_environment == "4p"
        best, best_value = None, None
        for assignment in self.get_equipment(target):
            power = ferocity = vitality = 0.0
            for (maj, mino), metas, choice in zip(self.group_budgets,
                                                  self.option_meta, assignment):
                major, minor, none = metas[choice]
                if four_stats:
                    power += maj * (major + minor)
                    ferocity += mino * major + maj * minor
                    vitality += mino * (major + minor)
                else:
                    power += mino * major + maj * (minor + none)
                    ferocity += mino * (major + minor + none)
                    vitality += mino * none
            value = (power + ferocity, vitality)
            if best_value is None or value > best_value:
                best, best_value = assignment, value
        return best