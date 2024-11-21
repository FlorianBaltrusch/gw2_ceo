import numpy as np
import random
from functools import cache
import common.general_data as gd

class GearSelect:

    def __init__(self, constraints):
        self.constraints = constraints
        if constraints.gear_environment == "3p":
            self.equipment = gd.

    # equipment = []

    # for i in range(50):
    #     r = random.randint(1, 100)
    #     r2 = random.randint(6, 10)
    #     equipment.append([5 * r, r2 * r])
    # print("equipment", np.array(equipment))
    # gears = np.array(equipment).sum(0)
    # print("gear sums", gears)


    @cache
    def overshoot_values(self, target, i=None):
        if i is None:
            i = len(self.equipment)
        if target <= 0:
            min_equip = sum(min(slot) for slot in equipment[:i])
            min_overshoot = -target + min_equip
            return np.array([0 if min_overshoot == 0 else np.infty, min_overshoot])
        if i == 0:
            return np.array([target, np.infty])
        return np.min(
            [overshoot_values(target - stat, i - 1) for stat in equipment[i - 1]], axis=0
        )


    def get_equipment(target, i=len(equipment)):
        if overshoot_values(target, i)[0] != 0:
            return
        if i == 0:
            yield []
            return
        for j, option in enumerate(equipment[i - 1]):
            for equip in get_equipment(target - option, i - 1):
                yield equip.copy() + [["L", "H"][j]]


    # target = np.floor(np.average(gears))
    # print("solution", target, overshoot_values(target))
    # i = 0
    # for solution in get_equipment(target):
    #     print(i, solution)
    #     i += 1
    # print(np.array(equipment))