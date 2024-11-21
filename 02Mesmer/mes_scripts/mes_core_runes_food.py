# -*- coding: utf-8 -*-
"""
Created on Sun Apr  7 13:50:12 2024

@author: Xarthisius
"""
# %% calculate testtarget with butternut food (100 power, 70 ferocity)
target_start_value = 2995 - base_precision - fury  # 1000 + 100*21 - 5*21 = 2995
test_target_0 = target_start_value - butternut_precision - sigil_accuracy  # und modifier
test_target_1 = test_target_0 - sum(high_gear)
test_target_2 = test_target_0 - sum(low_gear)

if gear_environment:
    base_gear = 'Berserker'
    test_target = test_target_2
elif abs(test_target_1) < abs(test_target_2):
    base_gear = 'Marauder'
    test_target = test_target_1
else:
    base_gear = 'Dragon'
    test_target = test_target_2

# %% swap sigil if necessary
if (base_gear == 'Berserker' and test_target < 0) or (base_gear == 'Dragon' and test_target < 0):
    test_target += sigil_accuracy
    used_sigil_butternut = False
else:
    used_sigil_butternut = True

# %% calculate stats
stat_vitality = base_vitality + jade_bot
stat_power = base_power + might + sum(high_gear) + butternut_power
stat_precision = base_precision + test_target + butternut_precision
stat_ferocity = fencers_finesse + butternut_ferocity

if base_gear == 'Berserker':
    stat_vitality -= min(0, test_target)
    stat_power -= max(0, test_target)
    stat_precision += sum(low_gear)
    stat_ferocity += sum(low_gear)
elif base_gear == 'Marauder':
    stat_vitality += sum(low_gear)
    stat_precision += sum(high_gear)
    stat_ferocity += sum(low_gear) - test_target
elif base_gear == 'Dragon':
    stat_vitality += sum(low_gear)
    stat_precision += sum(low_gear)
    stat_ferocity += sum(high_gear) - test_target

stat_power += stat_precision * sharpening_stones_precision + stat_ferocity * sharpening_stones_ferocity
ferocity_equivalent = (stat_ferocity + base_crit_dmg) * superiority_complex + stat_ferocity

# %% choose rune
# (Power + 1)*(1.5 + Ferocity/1500) = Power*(1.5 + (Ferocity + 1)/1500)
# => Power = Ferocity + 2250
effective_power = stat_power - ferocity_equivalent - 2250  # negativ = zu wenig Kraft

if gear_environment:
    runes_power_butternut = runes_power + runes_ferocity * sharpening_stones_ferocity
    food_power_butternut = food_power + food_ferocity * sharpening_stones_ferocity
    runes_ferocity_butternut = runes_ferocity * (superiority_complex + 1)  # Mesmer special
    food_ferocity_butternut = food_ferocity * (superiority_complex + 1)  # Mesmer special
    runes_ep_mod_butternut = runes_power_butternut + runes_precision - runes_ferocity_butternut
    food_ep_mod_butternut = food_power_butternut + food_precision - food_ferocity_butternut
else:
    runes_power_butternut = runes_power + (runes_precision + runes_ferocity) * sharpening_stones_ferocity
    food_power_butternut = food_power + (food_precision + food_ferocity) * sharpening_stones_ferocity
    runes_ferocity_butternut = runes_ferocity + (runes_precision + runes_ferocity) * superiority_complex  # Mesmer special
    food_ferocity_butternut = food_ferocity + (food_precision + food_ferocity) * superiority_complex  # Mesmer special
    runes_ep_mod_butternut = runes_power_butternut - runes_precision - runes_ferocity_butternut
    food_ep_mod_butternut = food_power_butternut - food_precision - food_ferocity_butternut

# %%
runes_list_butternut = []

if base_gear == 'Berserker':
    if test_target < gole_precision:
        runes_list_butternut = ['scholar', 'dragonh']  # nur 0 präzi Runen
    elif gole_precision <= test_target < deadeye_precision:
        runes_list_butternut = ['scholar', 'gole']  # dragonh = gole
    elif deadeye_precision <= test_target < eagle_precision:
        runes_list_butternut = ['scholar', 'gole', 'deadeye']
    elif eagle_precision <= test_target < infil_precision:
        runes_list_butternut = ['gole', 'deadeye', 'eagle']  # scholar = eagle
    elif infil_precision <= test_target < ranger_precision:
        runes_list_butternut = ['gole', 'deadeye', 'eagle', 'infil']
    elif ranger_precision <= test_target:
        runes_list_butternut = ['gole', 'eagle', 'infil', 'ranger']  # deadeye = ranger
elif base_gear == 'Marauder':
    if test_target <= scholar_precision:
        runes_list_butternut = ['scholar', 'dragonh', 'gole']
    elif scholar_precision < test_target <= gole_precision:
        runes_list_butternut = ['gole', 'deadeye']  # dragonh zu wenig präzi, scholar = deadeye
    elif gole_precision < test_target <= deadeye_precision:
        runes_list_butternut = ['deadeye', 'eagle']  # gole = eagle
    elif deadeye_precision < test_target <= eagle_precision:
        runes_list_butternut = ['eagle', 'infil']  # deadeye = infil
    elif eagle_precision < test_target <= infil_precision:
        runes_list_butternut = ['infil', 'ranger']  # eagle = ranger
    elif infil_precision < test_target <= ranger_precision:
        runes_list_butternut = ['ranger']  # nur ranger hat noch genug präzi
elif base_gear == 'Dragon':
    if scholar_precision <= test_target < gole_precision:
        runes_list_butternut = ['scholar', 'dragonh']
    elif gole_precision <= test_target < deadeye_precision:
        runes_list_butternut = ['scholar', 'dragonh', 'gole']
    elif deadeye_precision <= test_target < eagle_precision:
        runes_list_butternut = ['dragonh', 'gole', 'deadeye']  # scholar = deadeye
    elif eagle_precision <= test_target < infil_precision:
        runes_list_butternut = ['dragonh', 'deadeye', 'eagle']  # gole = eagle
    elif infil_precision <= test_target < ranger_precision:
        runes_list_butternut = ['dragonh', 'eagle', 'infil']
    elif ranger_precision <= test_target:
        runes_list_butternut = ['dragonh', 'infil', 'ranger']

get_runes['runes_ep_mod_butternut'] = runes_ep_mod_butternut  # remember that power in get_runes may be increased due to utility
get_food['food_ep_mod_butternut'] = food_ep_mod_butternut
filtered_runes_butternut = get_runes[get_runes['runes'].isin(runes_list_butternut)]
filtered_runes_ep_mod_butternut = filtered_runes_butternut['runes_ep_mod_butternut']

min_index = np.argmin(abs(effective_power + filtered_runes_ep_mod_butternut.values))
best_ep_butternut = effective_power + filtered_runes_ep_mod_butternut.iloc[min_index]


# %% calculate testtarget with truffle food (100 power, 70 precision)
target_start_value = 2995 - base_precision - fury  # 1000 + 100*21 - 5*21 = 2995
test_target_0 = target_start_value - truffle_precision - sigil_accuracy  # und modifier
test_target_1 = test_target_0 - sum(high_gear)
test_target_2 = test_target_0 - sum(low_gear)

if gear_environment:
    base_gear = 'Berserker'
    test_target = test_target_2
elif abs(test_target_1) < abs(test_target_2):
    base_gear = 'Marauder'
    test_target = test_target_1
else:
    base_gear = 'Dragon'
    test_target = test_target_2

# %% swap sigil if necessary
if (base_gear == 'Berserker' and test_target < 0) or (base_gear == 'Dragon' and test_target < 0):
    test_target += sigil_accuracy
    used_sigil_truffle = False
else:
    used_sigil_truffle = True

# %% calculate stats
stat_vitality = base_vitality + jade_bot
stat_power = base_power + might + sum(high_gear) + truffle_power
stat_precision = base_precision + test_target + truffle_precision
stat_ferocity = fencers_finesse + truffle_ferocity

if base_gear == 'Berserker':
    stat_vitality -= min(0, test_target)
    stat_power -= max(0, test_target)
    stat_precision += sum(low_gear)
    stat_ferocity += sum(low_gear)
elif base_gear == 'Marauder':
    stat_vitality += sum(low_gear)
    stat_precision += sum(high_gear)
    stat_ferocity += sum(low_gear) - test_target
elif base_gear == 'Dragon':
    stat_vitality += sum(low_gear)
    stat_precision += sum(low_gear)
    stat_ferocity += sum(high_gear) - test_target

stat_power += stat_precision * sharpening_stones_precision + stat_ferocity * sharpening_stones_ferocity
ferocity_equivalent = (stat_ferocity + base_crit_dmg) * superiority_complex + stat_ferocity

# %% choose rune
# (Power + 1)*(1.5 + Ferocity/1500) = Power*(1.5 + (Ferocity + 1)/1500)
# => Power = Ferocity + 2250
effective_power = stat_power - ferocity_equivalent - 2250  # negativ = zu wenig Kraft

if gear_environment:
    runes_power_truffle = runes_power + runes_ferocity * sharpening_stones_ferocity
    food_power_truffle = food_power + food_ferocity * sharpening_stones_ferocity
    runes_ferocity_truffle = runes_ferocity * (superiority_complex + 1)  # Mesmer special
    food_ferocity_truffle = food_ferocity * (superiority_complex + 1)  # Mesmer special
    runes_ep_mod_truffle = runes_power_truffle + runes_precision - runes_ferocity_truffle
    food_ep_mod_truffle = food_power_truffle + food_precision - food_ferocity_truffle
else:
    runes_power_truffle = runes_power + (runes_precision + runes_ferocity) * sharpening_stones_ferocity
    food_power_truffle = food_power + (food_precision + food_ferocity) * sharpening_stones_ferocity
    runes_ferocity_truffle = runes_ferocity + (runes_precision + runes_ferocity) * superiority_complex  # Mesmer special
    food_ferocity_truffle = food_ferocity + (food_precision + food_ferocity) * superiority_complex  # Mesmer special
    runes_ep_mod_truffle = runes_power_truffle - runes_precision - runes_ferocity_truffle
    food_ep_mod_truffle = food_power_truffle - food_precision - food_ferocity_truffle

# %%
runes_list_truffle = []

if base_gear == 'Berserker':
    if test_target < gole_precision:
        runes_list_truffle = ['scholar', 'dragonh']  # nur 0 präzi Runen
    elif gole_precision <= test_target < deadeye_precision:
        runes_list_truffle = ['scholar', 'gole']  # dragonh = gole
    elif deadeye_precision <= test_target < eagle_precision:
        runes_list_truffle = ['scholar', 'gole', 'deadeye']
    elif eagle_precision <= test_target < infil_precision:
        runes_list_truffle = ['gole', 'deadeye', 'eagle']  # scholar = eagle
    elif infil_precision <= test_target < ranger_precision:
        runes_list_truffle = ['gole', 'deadeye', 'eagle', 'infil']
    elif ranger_precision <= test_target:
        runes_list_truffle = ['gole', 'eagle', 'infil', 'ranger']  # deadeye = ranger
elif base_gear == 'Marauder':
    if test_target <= scholar_precision:
        runes_list_truffle = ['scholar', 'dragonh', 'gole']
    elif scholar_precision < test_target <= gole_precision:
        runes_list_truffle = ['gole', 'deadeye']  # dragonh zu wenig präzi, scholar = deadeye
    elif gole_precision < test_target <= deadeye_precision:
        runes_list_truffle = ['deadeye', 'eagle']  # gole = eagle
    elif deadeye_precision < test_target <= eagle_precision:
        runes_list_truffle = ['eagle', 'infil']  # deadeye = infil
    elif eagle_precision < test_target <= infil_precision:
        runes_list_truffle = ['infil', 'ranger']  # eagle = ranger
    elif infil_precision < test_target <= ranger_precision:
        runes_list_truffle = ['ranger']  # nur ranger hat noch genug präzi
elif base_gear == 'Dragon':
    if scholar_precision <= test_target < gole_precision:
        runes_list_truffle = ['scholar', 'dragonh']
    elif gole_precision <= test_target < deadeye_precision:
        runes_list_truffle = ['scholar', 'dragonh', 'gole']
    elif deadeye_precision <= test_target < eagle_precision:
        runes_list_truffle = ['dragonh', 'gole', 'deadeye']  # scholar = deadeye
    elif eagle_precision <= test_target < infil_precision:
        runes_list_truffle = ['dragonh', 'deadeye', 'eagle']  # gole = eagle
    elif infil_precision <= test_target < ranger_precision:
        runes_list_truffle = ['dragonh', 'eagle', 'infil']
    elif ranger_precision <= test_target:
        runes_list_truffle = ['dragonh', 'infil', 'ranger']

get_runes['runes_ep_mod_truffle'] = runes_ep_mod_truffle  # remember that power in get_runes may be increased due to utility
get_food['food_ep_mod_truffle'] = food_ep_mod_truffle
filtered_runes_truffle = get_runes[get_runes['runes'].isin(runes_list_truffle)]
filtered_runes_ep_mod_truffle = filtered_runes_truffle['runes_ep_mod_truffle']

min_index = np.argmin(abs(effective_power + filtered_runes_ep_mod_truffle.values))
best_ep_truffle = effective_power + filtered_runes_ep_mod_truffle.iloc[min_index]

# %% calculate testtarget with curry food (100 precision, 70 ferocity)
target_start_value = 2995 - base_precision - fury  # 1000 + 100*21 - 5*21 = 2995
test_target_0 = target_start_value - curry_precision - sigil_accuracy  # und modifier
test_target_1 = test_target_0 - sum(high_gear)
test_target_2 = test_target_0 - sum(low_gear)

if gear_environment:
    base_gear = 'Berserker'
    test_target = test_target_2
elif abs(test_target_1) < abs(test_target_2):
    base_gear = 'Marauder'
    test_target = test_target_1
else:
    base_gear = 'Dragon'
    test_target = test_target_2

# %% swap sigil if necessary
if (base_gear == 'Berserker' and test_target < 0) or (base_gear == 'Dragon' and test_target < 0):
    test_target += sigil_accuracy
    used_sigil_curry = False
else:
    used_sigil_curry = True

# %% calculate stats
stat_vitality = base_vitality + jade_bot
stat_power = base_power + might + sum(high_gear) + curry_power
stat_precision = base_precision + test_target + curry_precision
stat_ferocity = fencers_finesse + curry_ferocity

if base_gear == 'Berserker':
    stat_vitality -= min(0, test_target)
    stat_power -= max(0, test_target)
    stat_precision += sum(low_gear)
    stat_ferocity += sum(low_gear)
elif base_gear == 'Marauder':
    stat_vitality += sum(low_gear)
    stat_precision += sum(high_gear)
    stat_ferocity += sum(low_gear) - test_target
elif base_gear == 'Dragon':
    stat_vitality += sum(low_gear)
    stat_precision += sum(low_gear)
    stat_ferocity += sum(high_gear) - test_target

stat_power += stat_precision * sharpening_stones_precision + stat_ferocity * sharpening_stones_ferocity
ferocity_equivalent = (stat_ferocity + base_crit_dmg) * superiority_complex + stat_ferocity

# %% choose rune
# (Power + 1)*(1.5 + Ferocity/1500) = Power*(1.5 + (Ferocity + 1)/1500)
# => Power = Ferocity + 2250
effective_power = stat_power - ferocity_equivalent - 2250  # negativ = zu wenig Kraft

if gear_environment:
    runes_power_curry = runes_power + runes_ferocity * sharpening_stones_ferocity
    food_power_curry = food_power + food_ferocity * sharpening_stones_ferocity
    runes_ferocity_curry = runes_ferocity * (superiority_complex + 1)  # Mesmer special
    food_ferocity_curry = food_ferocity * (superiority_complex + 1)  # Mesmer special
    runes_ep_mod_curry = runes_power_curry + runes_precision - runes_ferocity_curry
    food_ep_mod_curry = food_power_curry + food_precision - food_ferocity_curry
else:
    runes_power_curry = runes_power + (runes_precision + runes_ferocity) * sharpening_stones_ferocity
    food_power_curry = food_power + (food_precision + food_ferocity) * sharpening_stones_ferocity
    runes_ferocity_curry = runes_ferocity + (runes_precision + runes_ferocity) * superiority_complex  # Mesmer special
    food_ferocity_curry = food_ferocity + (food_precision + food_ferocity) * superiority_complex  # Mesmer special
    runes_ep_mod_curry = runes_power_curry - runes_precision - runes_ferocity_curry
    food_ep_mod_curry = food_power_curry - food_precision - food_ferocity_curry

# %%
runes_list_curry = []

if base_gear == 'Berserker':
    if test_target < gole_precision:
        runes_list_curry = ['scholar', 'dragonh']  # nur 0 präzi Runen
    elif gole_precision <= test_target < deadeye_precision:
        runes_list_curry = ['scholar', 'gole']  # dragonh = gole
    elif deadeye_precision <= test_target < eagle_precision:
        runes_list_curry = ['scholar', 'gole', 'deadeye']
    elif eagle_precision <= test_target < infil_precision:
        runes_list_curry = ['gole', 'deadeye', 'eagle']  # scholar = eagle
    elif infil_precision <= test_target < ranger_precision:
        runes_list_curry = ['gole', 'deadeye', 'eagle', 'infil']
    elif ranger_precision <= test_target:
        runes_list_curry = ['gole', 'eagle', 'infil', 'ranger']  # deadeye = ranger
elif base_gear == 'Marauder':
    if test_target <= scholar_precision:
        runes_list_curry = ['scholar', 'dragonh', 'gole']
    elif scholar_precision < test_target <= gole_precision:
        runes_list_curry = ['gole', 'deadeye']  # dragonh zu wenig präzi, scholar = deadeye
    elif gole_precision < test_target <= deadeye_precision:
        runes_list_curry = ['deadeye', 'eagle']  # gole = eagle
    elif deadeye_precision < test_target <= eagle_precision:
        runes_list_curry = ['eagle', 'infil']  # deadeye = infil
    elif eagle_precision < test_target <= infil_precision:
        runes_list_curry = ['infil', 'ranger']  # eagle = ranger
    elif infil_precision < test_target <= ranger_precision:
        runes_list_curry = ['ranger']  # nur ranger hat noch genug präzi
elif base_gear == 'Dragon':
    if scholar_precision <= test_target < gole_precision:
        runes_list_curry = ['scholar', 'dragonh']
    elif gole_precision <= test_target < deadeye_precision:
        runes_list_curry = ['scholar', 'dragonh', 'gole']
    elif deadeye_precision <= test_target < eagle_precision:
        runes_list_curry = ['dragonh', 'gole', 'deadeye']  # scholar = deadeye
    elif eagle_precision <= test_target < infil_precision:
        runes_list_curry = ['dragonh', 'deadeye', 'eagle']  # gole = eagle
    elif infil_precision <= test_target < ranger_precision:
        runes_list_curry = ['dragonh', 'eagle', 'infil']
    elif ranger_precision <= test_target:
        runes_list_curry = ['dragonh', 'infil', 'ranger']

get_runes['runes_ep_mod_curry'] = runes_ep_mod_curry  # remember that power in get_runes may be increased due to utility
get_food['food_ep_mod_curry'] = food_ep_mod_curry
filtered_runes_curry = get_runes[get_runes['runes'].isin(runes_list_curry)]
filtered_runes_ep_mod_curry = filtered_runes_curry['runes_ep_mod_curry']

min_index = np.argmin(abs(effective_power + filtered_runes_ep_mod_curry.values))
best_ep_curry = effective_power + filtered_runes_ep_mod_curry.iloc[min_index]

# swap < and <= to prefer butternut over curry in elifs after and
if used_sigil_butternut == used_sigil_truffle == used_sigil_curry:
    if abs(best_ep_truffle) <= abs(best_ep_butternut) and abs(best_ep_truffle) <= abs(best_ep_curry):
        used_food = 'truffle'
        selected_food_power = truffle_power
        selected_food_precision = truffle_precision
        selected_food_ferocity = truffle_ferocity
    elif abs(best_ep_curry) < abs(best_ep_truffle) and abs(best_ep_curry) <= abs(best_ep_butternut):
        used_food = 'curry'
        selected_food_power = curry_power
        selected_food_precision = curry_precision
        selected_food_ferocity = curry_ferocity
    elif abs(best_ep_butternut) < abs(best_ep_truffle) and abs(best_ep_butternut) < abs(best_ep_curry):
        used_food = 'butternut'
        selected_food_power = butternut_power
        selected_food_precision = butternut_precision
        selected_food_ferocity = butternut_ferocity
elif used_sigil_butternut and used_sigil_truffle and not used_sigil_curry:
    if abs(best_ep_truffle) <= abs(best_ep_butternut):
        used_food = 'truffle'
        selected_food_power = truffle_power
        selected_food_precision = truffle_precision
        selected_food_ferocity = truffle_ferocity
    else:
        used_food = 'butternut'
        selected_food_power = butternut_power
        selected_food_precision = butternut_precision
        selected_food_ferocity = butternut_ferocity
elif used_sigil_butternut and not used_sigil_truffle and not used_sigil_curry:
    used_food = 'butternut'
    selected_food_power = butternut_power
    selected_food_precision = butternut_precision
    selected_food_ferocity = butternut_ferocity

# %% calculate testtarget with selected food
target_start_value = 2995 - base_precision - fury  # 1000 + 100*21 - 5*21 = 2995
test_target_0 = target_start_value - selected_food_precision - sigil_accuracy  # und modifier
test_target_1 = test_target_0 - sum(high_gear)
test_target_2 = test_target_0 - sum(low_gear)

if gear_environment:
    base_gear = 'Berserker'
    test_target = test_target_2
elif abs(test_target_1) < abs(test_target_2):
    base_gear = 'Marauder'
    test_target = test_target_1
else:
    base_gear = 'Dragon'
    test_target = test_target_2

# %% swap sigil if necessary
if (base_gear == 'Berserker' and test_target < 0) or (base_gear == 'Dragon' and test_target < 0):
    test_target += sigil_accuracy
    used_sigil = 'impact/night'
else:
    used_sigil = 'accuracy'

# %% calculate stats
stat_vitality = base_vitality + jade_bot
stat_power = base_power + might + sum(high_gear) + selected_food_power
stat_precision = base_precision + test_target + selected_food_precision
stat_ferocity = fencers_finesse + selected_food_ferocity

if base_gear == 'Berserker':
    stat_vitality -= min(0, test_target)
    stat_power -= max(0, test_target)
    stat_precision += sum(low_gear)
    stat_ferocity += sum(low_gear)
elif base_gear == 'Marauder':
    stat_vitality += sum(low_gear)
    stat_precision += sum(high_gear)
    stat_ferocity += sum(low_gear) - test_target
elif base_gear == 'Dragon':
    stat_vitality += sum(low_gear)
    stat_precision += sum(low_gear)
    stat_ferocity += sum(high_gear) - test_target

stat_power += stat_precision * sharpening_stones_precision + stat_ferocity * sharpening_stones_ferocity
ferocity_equivalent = (stat_ferocity + base_crit_dmg) * superiority_complex + stat_ferocity

# %% choose rune
# (Power + 1)*(1.5 + Ferocity/1500) = Power*(1.5 + (Ferocity + 1)/1500)
# => Power = Ferocity + 2250
effective_power = stat_power - ferocity_equivalent - 2250  # negativ = zu wenig Kraft

if gear_environment:
    runes_power += runes_ferocity * sharpening_stones_ferocity
    food_power += food_ferocity * sharpening_stones_ferocity
    runes_ferocity *= (superiority_complex + 1)  # Mesmer special, *= ist bewusst
    food_ferocity *= (superiority_complex + 1)  # Mesmer special, *= ist bewusst
    runes_ep_mod = runes_power + runes_precision - runes_ferocity
    food_ep_mod = food_power + food_precision - food_ferocity
else:
    runes_power += (runes_precision + runes_ferocity) * sharpening_stones_ferocity
    food_power += (food_precision + food_ferocity) * sharpening_stones_ferocity
    runes_ferocity += (runes_precision + runes_ferocity) * superiority_complex  # Mesmer special
    food_ferocity += (food_precision + food_ferocity) * superiority_complex  # Mesmer special
    runes_ep_mod = runes_power - runes_precision - runes_ferocity
    food_ep_mod = food_power - food_precision - food_ferocity

get_runes['runes_ep_mod'] = runes_ep_mod  # remember that power in get_runes may be increased due to utility
get_food['food_ep_mod'] = food_ep_mod

# %%
runes_list = []

if base_gear == 'Berserker':
    if test_target < gole_precision:
        runes_list = ['scholar', 'dragonh']  # nur 0 präzi Runen
    elif gole_precision <= test_target < deadeye_precision:
        runes_list = ['scholar', 'gole']  # dragonh = gole
    elif deadeye_precision <= test_target < eagle_precision:
        runes_list = ['scholar', 'gole', 'deadeye']
    elif eagle_precision <= test_target < infil_precision:
        runes_list = ['gole', 'deadeye', 'eagle']  # scholar = eagle
    elif infil_precision <= test_target < ranger_precision:
        runes_list = ['gole', 'deadeye', 'eagle', 'infil']
    elif ranger_precision <= test_target:
        runes_list = ['gole', 'eagle', 'infil', 'ranger']  # deadeye = ranger
elif base_gear == 'Marauder':
    if test_target <= scholar_precision:
        runes_list = ['scholar', 'dragonh', 'gole']
    elif scholar_precision < test_target <= gole_precision:
        runes_list = ['gole', 'deadeye']  # dragonh zu wenig präzi, scholar = deadeye
    elif gole_precision < test_target <= deadeye_precision:
        runes_list = ['deadeye', 'eagle']  # gole = eagle
    elif deadeye_precision < test_target <= eagle_precision:
        runes_list = ['eagle', 'infil']  # deadeye = infil
    elif eagle_precision < test_target <= infil_precision:
        runes_list = ['infil', 'ranger']  # eagle = ranger
    elif infil_precision < test_target <= ranger_precision:
        runes_list = ['ranger']  # nur ranger hat noch genug präzi
elif base_gear == 'Dragon':
    if scholar_precision <= test_target < gole_precision:
        runes_list = ['scholar', 'dragonh']
    elif gole_precision <= test_target < deadeye_precision:
        runes_list = ['scholar', 'dragonh', 'gole']
    elif deadeye_precision <= test_target < eagle_precision:
        runes_list = ['dragonh', 'gole', 'deadeye']  # scholar = deadeye
    elif eagle_precision <= test_target < infil_precision:
        runes_list = ['dragonh', 'deadeye', 'eagle']  # gole = eagle
    elif infil_precision <= test_target < ranger_precision:
        runes_list = ['dragonh', 'eagle', 'infil']
    elif ranger_precision <= test_target:
        runes_list = ['dragonh', 'infil', 'ranger']

filtered_runes = get_runes[get_runes['runes'].isin(runes_list)]
filtered_runes_ep_mod = filtered_runes['runes_ep_mod']

min_index = np.argmin(abs(effective_power + filtered_runes_ep_mod.values))
best_ep = effective_power + filtered_runes_ep_mod.iloc[min_index]
