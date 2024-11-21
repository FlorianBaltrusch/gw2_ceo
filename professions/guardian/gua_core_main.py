import common.general_data as gd
import numpy as np
import pandas as pd
from common.types import BuildSuggestion, BuildConstraints

def calc_ep(food, build: BuildConstraints):

    target_start_value = 2995 - gd.general_buffs.base_precision - gd.general_buffs.fury * build.fury  # 1000 + 100*21 - 5*21 = 2995
    test_target_0 = target_start_value - gd.food.loc[food, "precision"] * build.food - gd.general_buffs.sigil_accuracy  # type:ignore  # und modifier
    
    low_gear = gd.gear_stats[build.gear_environment, "Min", build.weapon_rarity, build.weapon_type]
    high_gear = gd.gear_stats[build.gear_environment, "Maj", build.weapon_rarity, build.weapon_type]

    test_target_1 = test_target_0 - sum(high_gear)
    test_target_2 = test_target_0 - sum(low_gear)

    if build.gear_environment == "3p":
        base_gear = 'Berserker'
        test_target = test_target_2
    elif abs(test_target_1) < abs(test_target_2):
        base_gear = 'Marauder'
        test_target = test_target_1
    else:
        base_gear = 'Dragon'
        test_target = test_target_2

    # swap sigil if necessary
    if (base_gear == 'Berserker' and test_target < 0) or (base_gear == 'Dragon' and test_target < 0):
        test_target += gd.general_buffs.sigil_accuracy
        used_sigil = False
    else:
        used_sigil = True

    # calculate stats
    stat_vitality = gd.general_buffs.base_vitality + gd.general_buffs.jade_bot
    stat_power = gd.general_buffs.base_power + build.might + sum(high_gear) + gd.food.loc[food, "power"] * build.food  # type: ignore
    stat_precision = gd.general_buffs.base_precision + test_target + gd.food.loc[food, "precision"] * build.food  # type: ignore
    stat_ferocity =  gd.food.loc[food, "ferocity"] * build.food  # type: ignore

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

    stat_power += stat_precision * gd.general_buffs.stones_prec * build.utility + stat_ferocity * gd.general_buffs.stones_fero * build.utility
    ferocity_equivalent = stat_ferocity

    # choose rune
    # (Power + 1)*(1.5 + Ferocity/1500) = Power*(1.5 + (Ferocity + 1)/1500)
    # ansatz: d/dPower(Average Damage) = d/dFerocity(Average Damge)
    # => Power = Ferocity + 2250
    effective_power = stat_power - ferocity_equivalent - 2250  # negativ = zu wenig Kraft

    if build.gear_environment == "3p":
        runes_power = gd.runes["power"] + gd.runes["ferocity"] * gd.general_buffs.stones_fero * build.utility
        food_power = gd.food["power"] + gd.food["ferocity"] * gd.general_buffs.stones_fero * build.utility
        runes_ep_mod = runes_power + gd.runes["precision"] - gd.runes["ferocity"]
        food_ep_mod = food_power + gd.food["precision"] - gd.food["ferocity"]
    else:
        runes_power = gd.runes["power"] + (gd.runes["precision"] + gd.runes["ferocity"]) * gd.general_buffs.stones_fero * build.utility
        food_power = gd.food["power"] + (gd.food["precision"] + gd.food["ferocity"]) * gd.general_buffs.stones_fero * build.utility
        runes_ep_mod = runes_power - gd.runes["precision"] - gd.runes["ferocity"]
        food_ep_mod = food_power - gd.food["precision"] - gd.food["ferocity"]

    if not build.food:
        food_power = 0
        food_ep_mod = 0

    runes_list = []

    if base_gear == 'Berserker':
        if test_target < gd.runes.loc["gole","precision"]:
            runes_list = ['scholar', 'dragonh']  # nur 0 präzi Runen
        elif test_target < gd.runes.loc["deadeye","precision"]:
            runes_list = ['scholar', 'gole']  # dragonh = gole
        elif test_target < gd.runes.loc["eagle","precision"]:
            runes_list = ['scholar', 'gole', 'deadeye']
        elif test_target < gd.runes.loc["infil","precision"]:
            runes_list = ['gole', 'deadeye', 'eagle']  # scholar = eagle
        elif test_target < gd.runes.loc["ranger","precision"]:
            runes_list = ['gole', 'deadeye', 'eagle', 'infil']
        else:
            runes_list = ['gole', 'eagle', 'infil', 'ranger']  # deadeye = ranger
    elif base_gear == 'Marauder':
        if test_target <= gd.runes.loc["scholar","precision"]:
            runes_list = ['scholar', 'dragonh', 'gole']
        elif test_target <= gd.runes.loc["gole","precision"]:
            runes_list = ['gole', 'deadeye']  # dragonh zu wenig präzi, scholar = deadeye
        elif test_target <= gd.runes.loc["deadeye","precision"]:
            runes_list = ['deadeye', 'eagle']  # gole = eagle
        elif test_target <= gd.runes.loc["eagle","precision"]:
            runes_list = ['eagle', 'infil']  # deadeye = infil
        elif test_target <= gd.runes.loc["infil","precision"]:
            runes_list = ['infil', 'ranger']  # eagle = ranger
        elif test_target <= gd.runes.loc["ranger","precision"]:
            runes_list = ['ranger']  # nur ranger hat noch genug präzi
        else:
            runes_list = []
    elif base_gear == 'Dragon':
        if test_target < gd.runes.loc["scholar","precision"]:
            runes_list = []
        elif test_target < gd.runes.loc["gole","precision"]:
            runes_list = ['scholar', 'dragonh']
        elif test_target < gd.runes.loc["deadeye","precision"]:
            runes_list = ['scholar', 'dragonh', 'gole']
        elif test_target < gd.runes.loc["eagle","precision"]:
            runes_list = ['dragonh', 'gole', 'deadeye']  # scholar = deadeye
        elif test_target < gd.runes.loc["infil","precision"]:
            runes_list = ['dragonh', 'deadeye', 'eagle']  # gole = eagle
        elif test_target < gd.runes.loc["ranger","precision"]:
            runes_list = ['dragonh', 'eagle', 'infil']
        elif test_target:
            runes_list = ['dragonh', 'infil', 'ranger']
    else:
        raise Exception

    filtered_runes_ep_mod = runes_ep_mod.loc[runes_list]
    min_index = np.argmin(abs(effective_power + filtered_runes_ep_mod.values))
    used_rune = filtered_runes_ep_mod.index[min_index]

    return BuildSuggestion(
        ep=effective_power + filtered_runes_ep_mod.iloc[min_index],
        use_sigil=used_sigil,
        used_rune=used_rune,
        used_food=food,
        target=round(test_target - gd.runes.loc[used_rune, "precision"], 2),
        base_gear=base_gear,
        low_gear=low_gear,
        high_gear=high_gear
    )


def calculate_gua(constraints: BuildConstraints):

    butternut = calc_ep("butternut", constraints)
    truffle = calc_ep("truffle", constraints)
    curry = calc_ep("curry", constraints)

    suggestions = pd.DataFrame([butternut, truffle, curry], index=["butternut", "truffle", "curry"])

    best = np.lexsort((abs(suggestions["ep"]),~suggestions["use_sigil"]))[0]
    return [butternut, truffle, curry][best]