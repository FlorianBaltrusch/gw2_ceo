import common.general_data as gd
import numpy as np
import pandas as pd
from common.types import BuildSuggestion

class Profession:
    def additional_crit_chance(self, build):
        return 0

    def additional_precision(self, build):
        return 0

    def additional_vitality(self, build):
        return 0

    def additional_power(self, build):
        return 0

    def additional_ferocity(self, build):
        return 0

    def stat_conversion(self, build, vitality, power, precision, ferocity):
        return vitality, power, precision, ferocity
    
    def ferocity_equivalent(self, ferocity):
        return ferocity


class Calculation:
    profession: Profession

    def calc_ep(self, build):

        # target_start_value = 2995 - gd.general_buffs.base_precision - gd.general_buffs.fury * build.fury  # 1000 + 100*21 - 5*21 = 2995
        # test_target_0 = target_start_value - gd.food.loc[food, "precision"] * build.food - gd.general_buffs.sigil_accuracy  # type:ignore  # und modifier
        min_stats = gd.gear_stats[build.gear_environment, "Min", build.weapon_rarity, build.weapon_type]
        maj_stats = gd.gear_stats[build.gear_environment, "Maj", build.weapon_rarity, build.weapon_type]        

        if build.food:
            food = gd.food
        else:
            food = pd.DataFrame(data={"power": [0], "precision": [0], "ferocity": [0]}, index=["no food"])
            food.index.name = "food"

        sigils = pd.DataFrame(data={"sigil": [False, True], "chance": [0, gd.general_buffs.sigil_accuracy]})

        food_rune_options = pd.merge(food.reset_index(), gd.runes.reset_index(), how="cross", suffixes=("_food", "_rune"))
        food_rune_options = pd.merge(sigils, food_rune_options, how="cross", suffixes=("_sigil", ""))
        food_rune_options[["power", "precision", "ferocity"]] = food_rune_options[["power_rune", "precision_rune", "ferocity_rune"]].values + food_rune_options[["power_food", "precision_food", "ferocity_food"]].values
        stats = food_rune_options[["sigil", "food", "rune", "power", "precision", "chance", "ferocity"]]
        

        NUM_OPTIONS = food_rune_options.shape[0]

        TARGET = 2995
        stats["precision"] += gd.general_buffs.base_precision
        stats["chance"] += self.profession.additional_crit_chance(build)
        if build.fury: stats["chance"] += gd.general_buffs.fury
        stats["precision"] += self.profession.additional_precision(build)
        
        # calculate stats
        stats["power"] += gd.general_buffs.base_power + gd.general_buffs.might * build.might + self.profession.additional_power(build) # type: ignore
        stats["ferocity"] += self.profession.additional_ferocity(build) # type: ignore
        stats["vitality"] = gd.general_buffs.base_vitality + gd.general_buffs.jade_bot + self.profession.additional_vitality(build)

        #stats = np.row_stack(np.broadcast(stat_power, stat_precision, stat_ferocity, stat_vitality)) # type: ignore

        stats["remainder"] = TARGET - stats["precision"] - stats["chance"]
        stats["precision"] += stats["remainder"]

        for i in range(NUM_OPTIONS):
            
            if build.gear_environment == "3p":
                stats.loc[i, "ferocity"] += sum(min_stats)  # type: ignore
                if stats.loc[i, "remainder"] > sum(min_stats):  # type: ignore
                    stats.loc[i, "power"] += sum(min_stats) + sum(maj_stats) - stats.loc[i, "remainder"] # type: ignore
                    stats.loc[i, "vitality"] += 0 # type: ignore
                else:
                    stats.loc[i, "power"] += sum(maj_stats) # type: ignore
                    stats.loc[i, "vitality"] += sum(min_stats) - stats.loc[i, "remainder"] # type: ignore
            else:
                stats.loc[i, "power"] += sum(maj_stats) # type: ignore
                stats.loc[i, "ferocity"] += sum(min_stats) + sum(maj_stats) - stats.loc[i, "remainder"] # type: ignore
                stats.loc[i, "vitality"] += sum(min_stats) # type: ignore

            stats.loc[i, "vitality"], stats.loc[i, "power"], stats.loc[i, "precision"], stats.loc[i, "ferocity"] = self.profession.stat_conversion(build, stats.loc[i, "vitality"], stats.loc[i, "power"], stats.loc[i, "precision"], stats.loc[i, "ferocity"]) # type: ignore

        if build.utility:
            stats["power"] += stats["precision"] * gd.general_buffs.stones_prec
            stats["power"] += stats["ferocity"] * gd.general_buffs.stones_fero

        stats["ferocity_equivalent"] = self.profession.ferocity_equivalent(stats["ferocity"])

        stats["effective_power"] = stats["power"] * (1.5 + stats["ferocity_equivalent"] / 1500)

        selection: pd.DataFrame = stats[stats["effective_power"] == stats["effective_power"].max()] # type: ignore
        
        selection["absolute_remainder"] = np.minimum(abs(selection["remainder"] - sum(min_stats)), abs(selection["remainder"] - sum(maj_stats)))
        selection.sort_values("absolute_remainder", inplace=True)
        
        selection["food_prio"] = 0
        selection.loc[:,"food_prio"] += (selection["food"] == "truffle") * 1
        selection.loc[:,"food_prio"] += (selection["food"] == "curry") * 2
        selection.loc[:,"food_prio"] += (selection["food"] == "butternut") * 2
        selection.sort_values("food_prio", inplace=True, kind="stable")

        return selection.iloc[0]
    
    def calculate(self, constraints):
        selection = self.calc_ep(constraints)
        return selection