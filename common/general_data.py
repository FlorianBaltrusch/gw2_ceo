# -*- coding: utf-8 -*-
"""
Created on Sun Apr  7 13:40:51 2024

@author: Xarthisius
"""

import pandas as pd
from argparse import Namespace
import numpy as np

general_buffs = Namespace(**pd.read_excel('general_tables/general_buffs.xlsx', index_col=0)["Buffwert"].to_dict())

# gear_stats = pd.read_excel("general_tables/gear_stats.xlsx", index_col=0)
# armor_types = list(gear_stats.index)
# gear_stats = gear_stats.melt()["value"]
# gear_stats.index = pd.MultiIndex.from_product([["3p", "4p"], ["Maj", "Min"], ["c", "l"], ["1h", "2h"], armor_types])

gear_stats = pd.read_excel("general_tables/gear_stats_new.xlsx", index_col=0, header=None)
armor_types = list(gear_stats.index)
gear_stats = gear_stats.melt()["value"]
gear_stats.index = pd.MultiIndex.from_product([["Asc", "Ex"], ["3p", "4p"], ["Maj", "Min"], armor_types])

def full_armor(majmin, asc_count, param_env, weapon):

    if weapon == "1h":
        full_armor = np.array([2,0,1,1,1,1,1,1,1,2,2,1])
    else:
        full_armor = np.array([0,1,1,1,1,1,1,1,1,2,2,1])

    asc_armor = np.minimum(asc_count, full_armor)
    ex_armor = full_armor - asc_armor
    num_jewels = ex_armor[8:12].sum()
    total = gear_stats["Asc", param_env, majmin][:12] * asc_armor
    total += gear_stats["Ex", param_env, majmin][:12] * ex_armor
    return total.sum() + num_jewels * gear_stats["Ex", param_env, majmin][12]

def num_infusions(asc_count, weapon):
    if weapon == "1h":
        full_armor = np.array([2,0,1,1,1,1,1,1,1,2,2,1])
    else:
        full_armor = np.array([0,1,1,1,1,1,1,1,1,2,2,1])
    asc_armor = np.minimum(asc_count, full_armor)
    return np.dot(asc_armor, [1,2,1,1,1,1,1,1,0,3,1,2])


runes = pd.read_excel('general_tables/runes.xlsx', index_col=0)
runes.index.name = 'rune'
food = pd.read_excel('general_tables/food.xlsx', index_col=0)

names = pd.read_excel('general_tables/names.xlsx')['names'].tolist()