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

# %% set variables
gear_environment = True  # True ist DPS, False ist open world
weapon_type = True  # True ist 1h, False ist 2h
weapon_rarity = True  # True ist exotic, False ist mit legendary weapon

food = True
utility = True

get_fury = True
get_might = True

get_superiority_complex = True
get_fencers_finesse = True
quiet_intensity = True

name_filter_1 = True  # sinvolle Anzahl von S/G/B und Access
name_filter_2 = True  # sivolle Juwelenanzahl
name_filter_3 = True  # ohne Infusionen

# %% set class specific variable values
get_mes_buffs = pd.read_excel('mes_scripts/mes_buffs.xlsx')
superiority_complex = get_mes_buffs.iloc[0, 1] if get_superiority_complex else 0
fencers_finesse = get_mes_buffs.iloc[1, 1] if get_fencers_finesse else 0
quiet_intensity_1 = get_mes_buffs.iloc[4, 1] if quiet_intensity else 0
quiet_intensity_2 = get_mes_buffs.iloc[5, 1] if quiet_intensity else 0

# %% import general_data
with open('../general_scripts/general_data.py') as file1:
    exec(file1.read())

# %% import mes_food_runes
with open('mes_scripts/mes_EoD_runes_food.py') as file2:
    exec(file2.read())

# %% import print_stats
with open('../general_scripts/print_stats.py') as file3:
    exec(file3.read())

# %% import general_combinations
with open('../general_scripts/general_combinations.py') as file4:
    exec(file4.read())
