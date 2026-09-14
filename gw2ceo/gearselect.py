import numpy as np
import pandas as pd
from functools import cache

from gw2ceo.general_data import gear_stats
from gw2ceo.dtypes import BuildConstraints


class GearSelect:

    def __init__(self, build: BuildConstraints):
        self.constraints = build

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
           

        # options per slot group, and parallel (label, piece count) metadata so
        # a chosen assignment can be reported back as concrete gear pieces
        self.equipment = []
        self.groups = []

        def add_group(label, count, options):
            self.equipment.append(options)
            self.groups.append((label, count))

        def spread(gear, slot, count):
            """all splits of `count` pieces of one slot into Maj/Min variants"""
            return [gear["Maj", slot] * i + gear["Min", slot] * (count - i)
                    for i in range(count + 1)]

        # Weapon
        if build.weapon_type == "1h":
            add_group("Weapons (ascended)", num_asc["One-handed"],
                      spread(ascend, "One-handed", num_asc["One-handed"]))
            add_group("Weapons (exotic)", num_ex["One-handed"],
                      spread(exotic, "One-handed", num_ex["One-handed"]))
        else:
            if num_asc["Two-handed"] == 0:
                add_group("", 0, [0])
            add_group("Weapon", 1, [min_gear["Two-handed"], maj_gear["Two-handed"]])
            if num_ex["Two-handed"] == 0:
                add_group("", 0, [0])

        # Chest, Legs, Head
        add_group("Chest", 1, [min_gear["Chest"], maj_gear["Chest"]])
        add_group("Legs", 1, [min_gear["Legs"], maj_gear["Legs"]])
        add_group("Head", 1, [min_gear["Head"], maj_gear["Head"]])

        # Shoulders/Gloves/Boots share their stat values and are interchangeable
        asc_sgb = num_asc[["Shoulders", "Gloves", "Boots"]].sum()
        add_group("Shoulders/Gloves/Boots (ascended)", asc_sgb, spread(ascend, "Shoulders", asc_sgb))
        ex_sgb = num_ex[["Shoulders", "Gloves", "Boots"]].sum()
        add_group("Shoulders/Gloves/Boots (exotic)", ex_sgb, spread(exotic, "Shoulders", ex_sgb))

        # Trinkets
        add_group("Amulet", 1, [min_gear["Amulet"], maj_gear["Amulet"]])
        add_group("Rings (ascended)", num_asc["Ring"], spread(ascend, "Ring", num_asc["Ring"]))
        add_group("Rings (exotic)", num_ex["Ring"], spread(exotic, "Ring", num_ex["Ring"]))
        add_group("Accessories (ascended)", num_asc["Accessory"], spread(ascend, "Accessory", num_asc["Accessory"]))
        add_group("Accessories (exotic)", num_ex["Accessory"], spread(exotic, "Accessory", num_ex["Accessory"]))
        add_group("Back item", 1, [min_gear["Back item"], maj_gear["Back item"]])

        # Jewels (upgrade slots of exotic trinkets)
        num_jewels = num_ex.values[8:12].sum()
        add_group("Jewels (in exotic trinkets)", num_jewels, spread(exotic, "Jewel", num_jewels))

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