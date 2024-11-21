# -*- coding: utf-8 -*-
"""
Created on Sun Apr  7 13:40:51 2024

@author: Xarthisius
"""

import pandas as pd
from argparse import Namespace

general_buffs = Namespace(**pd.read_excel('general_tables/general_buffs.xlsx', index_col=0)["Buffwert"].to_dict())

# gear_stats = pd.read_excel("general_tables/gear_stats.xlsx", index_col=0)
# armor_types = list(gear_stats.index)
# gear_stats = gear_stats.melt()["value"]
# gear_stats.index = pd.MultiIndex.from_product([["3p", "4p"], ["Maj", "Min"], ["c", "l"], ["1h", "2h"], armor_types])

gear_stats = pd.read_excel("general_tables/gear_stats_new.xlsx", index_col=0, header=None)
armor_types = list(gear_stats.index)
gear_stats = gear_stats.melt()["value"]
gear_stats.index = pd.MultiIndex.from_product([["Asc", "Ex"], ["3p", "4p"], ["Maj", "Min"], armor_types])

runes = pd.read_excel('general_tables/runes.xlsx', index_col=0)
runes.index.name = 'rune'
food = pd.read_excel('general_tables/food.xlsx', index_col=0)

names = pd.read_excel('general_tables/names.xlsx')['names'].tolist()