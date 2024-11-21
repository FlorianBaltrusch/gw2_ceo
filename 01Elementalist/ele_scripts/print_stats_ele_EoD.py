# -*- coding: utf-8 -*-
"""
Created on Sun Apr  7 13:54:03 2024

@author: Xarthisius
"""
# %% calculate final target and numbers
# negatives target = overcap
rune_index = filtered_runes.index[min_index]
used_rune = get_runes.loc[rune_index, 'runes']
target = test_target - get_runes.iloc[rune_index, 2]
target = round(target, 2)

print('Rune:', used_rune)
print('Sigil:', used_sigil)
print('Food:', used_food)
print('Gear:', base_gear)
print('Target:', target)

# %% select numbers
if target >= 0:
    numbers = (high_gear - low_gear).tolist()
else:
    if base_gear == 'Berserker':
        numbers = (-low_gear).tolist()
    else:
        numbers = (low_gear - high_gear).tolist()

if not weapon_rarity:
    numbers += [5 * cat_mod] if weapon_type else [5 * cat_mod, 5 * cat_mod]

numbers = [round(num, 2) for num in numbers]
