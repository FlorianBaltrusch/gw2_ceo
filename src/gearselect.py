import numpy as np
import pandas as pd
from functools import cache

from src.general_data import gear_stats
from src.types import BuildConstraints


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
           

        self.equipment = []
        self.descriptions = ["Ascended Weapons", "Exotic Weapon", "Chest", "Legs", "Head", "Ascended S/G/B", "Exotic S/G/B", "Amulet", "Ascended Rings", "Exotic Rings", "Ascended Accessories", "Exotic Accessories", "Back item", "Jewels"]
        
        # Ascended Weapon
        if build.weapon_type == "1h":
            asc_weapon = num_asc["One-handed"]
            self.equipment.append([ascend["Maj", "One-handed"]*i + ascend["Min", "One-handed"]*(asc_weapon-i) for i in range(asc_weapon+1)])
            ex_weapon = num_ex["One-handed"]
            self.equipment.append([exotic["Maj", "One-handed"]*i + exotic["Min", "One-handed"]*(ex_weapon-i) for i in range(ex_weapon+1)])
        else:
            if num_asc["Two-handed"] == 0:
                self.equipment.append([0])
            self.equipment.append([min_gear["Two-handed"] , maj_gear["Two-handed"]])
            if num_ex["Two-handed"] == 0:
                self.equipment.append([0])

        # Chest, Legs, Head
        self.equipment.append([min_gear["Chest"] , maj_gear["Chest"]])

        self.equipment.append([min_gear["Legs"] , maj_gear["Legs"]])

        self.equipment.append([min_gear["Head"] , maj_gear["Head"]])

        # Ascended S/G/B
        asc_sgb = num_asc[["Shoulders", "Gloves", "Boots"]].sum()
        self.equipment.append([ascend["Maj", "Shoulders"]*i + ascend["Min", "Shoulders"]*(asc_sgb-i) for i in range(asc_sgb+1)])
        # Exotic S/G/B
        ex_sgb = num_ex[["Shoulders", "Gloves", "Boots"]].sum()
        self.equipment.append([exotic["Maj", "Shoulders"]*i + exotic["Min", "Shoulders"]*(ex_sgb-i) for i in range(ex_sgb+1)])

        # Amulet
        self.equipment.append([min_gear["Amulet"] , maj_gear["Amulet"]])

        # Ascended Rings
        asc_ring = num_asc["Ring"]
        self.equipment.append([ascend["Maj", "Ring"]*i + ascend["Min", "Ring"]*(asc_ring-i) for i in range(asc_ring+1)])
        # Exotic Rings 
        ex_ring = num_ex["Ring"]
        self.equipment.append([exotic["Maj", "Ring"]*i + exotic["Min", "Ring"]*(ex_ring-i) for i in range(ex_ring+1)])

        # Ascended Accessories
        asc_acc = num_asc["Accessory"]
        self.equipment.append([ascend["Maj", "Accessory"]*i + ascend["Min", "Accessory"]*(asc_acc-i) for i in range(asc_acc+1)])
        # Exotic Accessories
        ex_acc = num_ex["Accessory"]
        self.equipment.append([exotic["Maj", "Accessory"]*i + exotic["Min", "Accessory"]*(ex_acc-i) for i in range(ex_acc+1)])

        # Back item
        self.equipment.append([min_gear["Back item"] , maj_gear["Back item"]])

        # Jewels
        num_jewels = num_ex.values[8:12].sum()
        self.equipment.append([exotic["Maj", "Jewel"]*i + exotic["Min", "Jewel"]*(num_jewels-i) for i in range(num_jewels+1)])
        return


    @cache
    def overshoot_values(self, target, i=None):
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