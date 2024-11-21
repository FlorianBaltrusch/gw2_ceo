# -*- coding: utf-8 -*-
"""
Created on Sun Apr  7 13:40:51 2024

@author: Xarthisius
"""
# %% import general data
get_general_buffs = pd.read_excel('../general_tables/general_buffs.xlsx')
get_gear_stats = pd.read_excel('../general_tables/gear_stats.xlsx')
get_runes = pd.read_excel('../general_tables/runes.xlsx')
get_food = pd.read_excel('../general_tables/food.xlsx')
get_names = pd.read_excel('../general_tables/names.xlsx')

# %% set gear
Pc3Maj1h = get_gear_stats['3pcMaj1h'] * cat_mod
Pc3Maj2h = get_gear_stats['3pcMaj2h'] * cat_mod
Pc3Maj1hL = get_gear_stats['3pcMaj1hL'] * cat_mod
Pc3Maj2hL = get_gear_stats['3pcMaj2hL'] * cat_mod

Pc3Min1h = get_gear_stats['3pcMin1h'] * cat_mod
Pc3Min2h = get_gear_stats['3pcMin2h'] * cat_mod
Pc3Min1hL = get_gear_stats['3pcMin1hL'] * cat_mod
Pc3Min2hL = get_gear_stats['3pcMin2hL'] * cat_mod

Pc4Maj1h = get_gear_stats['4pcMaj1h'] * cat_mod
Pc4Maj2h = get_gear_stats['4pcMaj2h'] * cat_mod
Pc4Maj1hL = get_gear_stats['4pcMaj1hL'] * cat_mod
Pc4Maj2hL = get_gear_stats['4pcMaj2hL'] * cat_mod

Pc4Min1h = get_gear_stats['4pcMin1h'] * cat_mod
Pc4Min2h = get_gear_stats['4pcMin2h'] * cat_mod
Pc4Min1hL = get_gear_stats['4pcMin1hL'] * cat_mod
Pc4Min2hL = get_gear_stats['4pcMin2hL'] * cat_mod

names = get_names['names'].tolist()

# %% set general variable values
base_power = get_general_buffs.iloc[0, 1] * cat_mod
base_precision = get_general_buffs.iloc[1, 1] * cat_mod
base_crit_dmg = get_general_buffs.iloc[2, 1]
base_vitality = get_general_buffs.iloc[5, 1] * cat_mod
jade_bot = get_general_buffs.iloc[6, 1] * cat_mod
sigil_accuracy = get_general_buffs.iloc[7, 1]

# food
food_power = get_food['power'] * cat_mod
food_precision = get_food['precision'] * cat_mod
food_ferocity = get_food['ferocity'] * cat_mod

butternut_power = get_food.iloc[0, 1] * cat_mod if food else 0
butternut_precision = get_food.iloc[0, 2] * cat_mod if food else 0
butternut_ferocity = get_food.iloc[0, 3] * cat_mod if food else 0
truffle_power = get_food.iloc[1, 1] * cat_mod if food else 0
truffle_precision = get_food.iloc[1, 2] * cat_mod if food else 0
truffle_ferocity = get_food.iloc[1, 3] * cat_mod if food else 0
curry_power = get_food.iloc[2, 1] * cat_mod if food else 0
curry_precision = get_food.iloc[2, 2] * cat_mod if food else 0
curry_ferocity = get_food.iloc[2, 3] * cat_mod if food else 0

# runes
runes_power = get_runes['power'] * cat_mod
runes_precision = get_runes['precision'] * cat_mod
runes_ferocity = get_runes['ferocity'] * cat_mod

scholar_power = get_runes.iloc[0, 1] * cat_mod
scholar_precision = get_runes.iloc[0, 2] * cat_mod
scholar_ferocity = get_runes.iloc[0, 3] * cat_mod
dragonh_power = get_runes.iloc[1, 1] * cat_mod
dragonh_precision = get_runes.iloc[1, 2] * cat_mod
dragonh_ferocity = get_runes.iloc[1, 3] * cat_mod
gole_power = get_runes.iloc[2, 1] * cat_mod
gole_precision = get_runes.iloc[2, 2] * cat_mod
gole_ferocity = get_runes.iloc[2, 3] * cat_mod
deadeye_power = get_runes.iloc[3, 1] * cat_mod
deadeye_precision = get_runes.iloc[3, 2] * cat_mod
deadeye_ferocity = get_runes.iloc[3, 3] * cat_mod
eagle_power = get_runes.iloc[4, 1] * cat_mod
eagle_precision = get_runes.iloc[4, 2] * cat_mod
eagle_ferocity = get_runes.iloc[4, 3] * cat_mod
infil_power = get_runes.iloc[5, 1] * cat_mod
infil_precision = get_runes.iloc[5, 2] * cat_mod
infil_ferocity = get_runes.iloc[5, 3] * cat_mod
ranger_power = get_runes.iloc[6, 1] * cat_mod
ranger_precision = get_runes.iloc[6, 2] * cat_mod
ranger_ferocity = get_runes.iloc[6, 3] * cat_mod

fury = get_general_buffs.iloc[3, 1] if get_fury else 0
might = get_general_buffs.iloc[4, 1] * cat_mod if get_might else 0
sharpening_stones_precision = get_general_buffs.iloc[8, 1] if utility else 0
sharpening_stones_ferocity = get_general_buffs.iloc[9, 1] if utility else 0

# %% select high- and lowgear
if gear_environment:
    if weapon_type:
        high_gear = Pc3Maj1h if weapon_rarity else Pc3Maj1hL
        low_gear = Pc3Min1h if weapon_rarity else Pc3Min1hL
    else:
        high_gear = Pc3Maj2h if weapon_rarity else Pc3Maj2hL
        low_gear = Pc3Min2h if weapon_rarity else Pc3Min2hL
else:
    if weapon_type:
        high_gear = Pc4Maj1h if weapon_rarity else Pc4Maj1hL
        low_gear = Pc4Min1h if weapon_rarity else Pc4Min1hL
    else:
        high_gear = Pc4Maj2h if weapon_rarity else Pc4Maj2hL
        low_gear = Pc4Min2h if weapon_rarity else Pc4Min2hL
