# -*- coding: utf-8 -*-
"""
Created on Sun Apr  7 13:36:23 2024

@author: Xarthisius
"""
# %% libraries
import pandas as pd
import numpy as np
from itertools import combinations
from tqdm import tqdm
from collections import defaultdict

# %% set variables
gear_environment = False  # True ist DPS, False ist open world
weapon_type = False  # True ist 1h, False ist 2h
weapon_rarity = False  # True ist exotic, False ist mit legendary weapon

food = True
utility = True

get_fury = True
get_might = True

get_zephyrs_speed = True
get_signet_of_fire = True
get_empowering_flame = True
get_power_overwhelming = True
get_arcane_power = True
get_raging_storm = True
get_aeromancers_training = True
get_fresh_air = True
get_arcane_lightning = True
get_ferocious_winds = True
get_superior_elements = True
get_elements_of_rage = True
get_elemental_polyphony = True
# masters_fortitude is missing

name_filter_1 = True  # sinvolle Anzahl von S/G/B und Access
name_filter_2 = True  # sivolle Juwelenanzahl
name_filter_3 = True  # ohne Infusionen

# %% set class specific variable values
get_ele_buffs = pd.read_excel('ele_scripts/ele_buffs.xlsx')
zephyrs_speed = get_ele_buffs.iloc[0, 1] if get_zephyrs_speed else 0
signet_of_fire = get_ele_buffs.iloc[1, 1] if get_signet_of_fire else 0
empowering_flame = get_ele_buffs.iloc[2, 1] if get_empowering_flame else 0
if get_might:
    power_overwhelming = get_ele_buffs.iloc[3, 1] if get_power_overwhelming else 0
else:
    power_overwhelming = 0
arcane_power = get_ele_buffs.iloc[4, 1] if get_arcane_power else 0
if get_fury:
    raging_storm = get_ele_buffs.iloc[5, 1] if get_raging_storm else 0
else:
    raging_storm = 0
aeromancers_training = get_ele_buffs.iloc[6, 1] if get_aeromancers_training else 0
fresh_air = get_ele_buffs.iloc[7, 1] if get_fresh_air else 0
if arcane_power:
    arcane_lightning = get_ele_buffs.iloc[8, 1] if get_arcane_lightning else 0
else:
    arcane_lightning = 0
ferocious_winds = get_ele_buffs.iloc[9, 1] if get_ferocious_winds else 0
superior_elements = get_ele_buffs.iloc[10, 1] if get_superior_elements else 0
elements_of_rage = get_ele_buffs.iloc[11, 1] if get_elements_of_rage else 0
elemental_polyphony_1 = get_ele_buffs.iloc[12, 1] if get_elemental_polyphony else 0
elemental_polyphony_2 = get_ele_buffs.iloc[13, 1] if get_elemental_polyphony else 0

# %% import general_data
with open('../general_scripts/general_data.py') as file1:
    exec(file1.read())

# %% import ele_food_runes
with open('ele_scripts/ele_PoF_runes_food.py') as file2:
    exec(file2.read())

# %% import print_stats
with open('../general_scripts/print_stats.py') as file3:
    exec(file3.read())

# %% import whole_numbers
with open('ele_scripts/ele_PoF_whole_numbers_fast.py') as file4:
    exec(file4.read())

# %% import general_combinations
with open('../general_scripts/general_combinations.py') as file5:
    exec(file5.read())
