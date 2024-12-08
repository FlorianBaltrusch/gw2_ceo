import common.general_data as gd
from professions.guardian.gua_core_main import calculate_gua
from common.types import BuildSuggestion, BuildConstraints
from common.general_combinations import print_combinations
import professions.elementalist.ele_core_main as ele
from common.calculate import Calculation
import pandas as pd
from argparse import Namespace
import numpy as np
from common.gearselect import GearSelect

pd.options.mode.chained_assignment = None

constraints = BuildConstraints(
    gear_environment='3p',
    weapon_type='1h',
    
    num_ascended=np.array([1,0,0,0,0,0,0,0,0,0,0,0]),  # One-handed, Two-handed, Chest, Legs, Head, Shoulders, Gloves, Boots, Amulet, Ring, Accessory, Back item
#    num_ascended=np.full(12, 2),

    food=True,
    utility=True,

    fury=True,
    might=True
)

# gs = GearSelect(constraints)
# for i in range(3000):
#     print(i, gs.overshoot_values(i))

ele_constraints = ele.BuildConstraints()

calculation = Calculation() 
calculation.profession = ele.Elementalist(ele_constraints)
suggestion = calculation.calculate(constraints)

print(suggestion)

# suggestion = calculate_gua(constraints)


# print('Rune:', suggestion.used_rune)
# print('Sigil:', suggestion.use_sigil)
# print('Food:', suggestion.used_food)
# print('Gear:', suggestion.base_gear)
# print('Target:', suggestion.target)

# if suggestion.target >= 0:
#     numbers = (suggestion.high_gear - suggestion.low_gear).tolist()
# else:
#     if suggestion.base_gear == 'Berserker':
#         numbers = (-suggestion.low_gear).tolist()
#     else:
#         numbers = (suggestion.low_gear - suggestion.high_gear).tolist()

# if constraints.weapon_rarity == 'l':
#     numbers += [5] if constraints.weapon_type=='1h' else [5, 5]

# print_combinations(numbers, suggestion, True, True, True)