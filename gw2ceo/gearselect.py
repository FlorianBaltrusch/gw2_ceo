from functools import cache

import numpy as np
import pandas as pd

from gw2ceo.dtypes import BuildConstraints
from gw2ceo.general_data import gear_stats


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
        # behind equipment[i][j], and groups[i] the (label, piece count)
        self.equipment = []
        self.groups = []
        self.option_meta = []

        def add_group(label, count, options, meta):
            self.equipment.append(options)
            self.groups.append((label, count))
            self.option_meta.append(meta)

        def spread(gear, slot, count):
            """all splits of `count` pieces of one slot across the variants"""
            options, meta = [], []
            for none_count in (range(count + 1) if self.valkyrie else [0]):
                for major in range(count - none_count + 1):
                    minor = count - none_count - major
                    options.append(gear["Maj", slot] * major + gear["Min", slot] * minor)
                    meta.append((major, minor, none_count))
            return options, meta

        def single(label, min_value, maj_value):
            options = [min_value, maj_value]
            meta = [(0, 1, 0), (1, 0, 0)]
            if self.valkyrie:
                options.append(0)
                meta.append((0, 0, 1))
            add_group(label, 1, options, meta)

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

        # Chest, Legs, Head
        single("Chest", min_gear["Chest"], maj_gear["Chest"])
        single("Legs", min_gear["Legs"], maj_gear["Legs"])
        single("Head", min_gear["Head"], maj_gear["Head"])

        # Shoulders/Gloves/Boots share their stat values and are interchangeable
        asc_sgb = num_asc[["Shoulders", "Gloves", "Boots"]].sum()
        add_group("Shoulders/Gloves/Boots (ascended)", asc_sgb, *spread(ascend, "Shoulders", asc_sgb))
        ex_sgb = num_ex[["Shoulders", "Gloves", "Boots"]].sum()
        add_group("Shoulders/Gloves/Boots (exotic)", ex_sgb, *spread(exotic, "Shoulders", ex_sgb))

        # Trinkets
        single("Amulet", min_gear["Amulet"], maj_gear["Amulet"])
        add_group("Rings (ascended)", num_asc["Ring"], *spread(ascend, "Ring", num_asc["Ring"]))
        add_group("Rings (exotic)", num_ex["Ring"], *spread(exotic, "Ring", num_ex["Ring"]))
        add_group("Accessories (ascended)", num_asc["Accessory"], *spread(ascend, "Accessory", num_asc["Accessory"]))
        add_group("Accessories (exotic)", num_ex["Accessory"], *spread(exotic, "Accessory", num_ex["Accessory"]))
        single("Back item", min_gear["Back item"], maj_gear["Back item"])

        # Jewels (upgrade slots of exotic trinkets)
        num_jewels = int(num_ex.iloc[8:12].sum())
        add_group("Jewels (in exotic trinkets)", num_jewels, *spread(exotic, "Jewel", num_jewels))

        # memoize per instance (a class-level @cache would keep every
        # instance alive for the lifetime of the server)
        self.overshoot_values = cache(self._overshoot_values)


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


    def get_equipment(self, target, i=None):
        if i is None:
            i = len(self.equipment)
        if self.overshoot_values(target, i)[0] != 0:
            return
        if i == 0:
            yield []
            return
        for j, option in enumerate(self.equipment[i - 1]):
            for equip in self.get_equipment(target - option, i - 1):
                yield equip.copy() + [j]