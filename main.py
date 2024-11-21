import common.general_data as gd
from professions.guardian.gua_core_main import calculate_gua
from common.types import BuildSuggestion, BuildConstraints
from common.general_combinations import print_combinations
from professions.elementalist.ele_core_main import Elementalist
from common.calculate import Calculation
import pandas as pd
from argparse import Namespace
from common.gearselect import GearSelect

pd.options.mode.chained_assignment = None

# constraints = BuildConstraints(
#     gear_environment='3p',
#     weapon_type="1h",  # 1h / 2h
#     weapon_rarity="c",  # c / l

#     food=True,
#     utility=True,

#     fury=True,
#     might=True
# )

constraints = Namespace(**{
    "gear_environment": '3p',
    "weapon_type": "1h",  # 1h / 2h
    "weapon_rarity": "c",  # c / l

    "food": True,
    "utility": True,

    "fury": True,
    "might": True,

    "zephyrs_speed": True,
    "signet_of_fire": True,
    "ferocious_winds": True
})

calculation = Calculation() 
calculation.profession = Elementalist()
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