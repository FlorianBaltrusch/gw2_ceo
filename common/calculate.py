import common.general_data as gd
import numpy as np
import pandas as pd
from common.types import BuildSuggestion, BuildConstraints
from common.gearselect import GearSelect

class Profession:
    def additional_crit_chance(self):
        return 0

    def additional_precision(self):
        return 0

    def additional_vitality(self):
        return 0

    def additional_power(self):
        return 0

    def additional_ferocity(self):
        return 0

    def stat_conversion(self, vitality, power, precision, ferocity):
        return vitality, power, precision, ferocity
    
    def ferocity_equivalent(self, ferocity):
        return ferocity


class Calculation:
    profession: Profession

    def calc_ep(self, build: BuildConstraints):

        # target_start_value = 2995 - gd.general_buffs.base_precision - gd.general_buffs.fury * build.fury  # 1000 + 100*21 - 5*21 = 2995
        # test_target_0 = target_start_value - gd.food.loc[food, "precision"] * build.food - gd.general_buffs.sigil_accuracy  # type:ignore  # und modifier
        min_stats = gd.full_armor("Min", build.num_ascended, build.gear_environment, build.weapon_type)
        maj_stats = gd.full_armor("Maj", build.num_ascended, build.gear_environment, build.weapon_type)     

        if build.food:
            food = gd.food
        else:
            food = pd.DataFrame(data={"power": [0], "precision": [0], "ferocity": [0]}, index=["no food"])
            food.index.name = "food"

        sigils = pd.DataFrame(data={"sigil": [False, True], "chance": [0, gd.general_buffs.sigil_accuracy]})
        num_infusions = gd.num_infusions(build.num_ascended, build.weapon_type)
        infusions = pd.DataFrame(data={"prec_infusions": list(range(num_infusions+1)), "precision_inf": [5*i for i in range(num_infusions+1)], "power_inf": [5*(num_infusions-i) for i in range(num_infusions+1)], "ferocity_inf": [0]*(num_infusions+1)})

        food_rune_options = pd.merge(food.reset_index(), gd.runes.reset_index(), how="cross", suffixes=("_food", "_rune"))
        food_rune_options = pd.merge(sigils, food_rune_options, how="cross", suffixes=("_sigil", ""))
        food_rune_options = pd.merge(infusions, food_rune_options, how="cross", suffixes=("_inf", ""))

        food_rune_options[["power", "precision", "ferocity"]] = food_rune_options[["power_rune", "precision_rune", "ferocity_rune"]].values + food_rune_options[["power_food", "precision_food", "ferocity_food"]].values + food_rune_options[["power_inf", "precision_inf", "ferocity_inf"]].values
        stats = food_rune_options[["prec_infusions", "sigil", "food", "rune", "power", "precision", "chance", "ferocity"]]
        

        NUM_OPTIONS = food_rune_options.shape[0]

        TARGET = 2995
        stats["precision"] += gd.general_buffs.base_precision
        stats["chance"] += self.profession.additional_crit_chance()
        if build.fury: stats["chance"] += gd.general_buffs.fury
        stats["precision"] += self.profession.additional_precision()
        
        # calculate stats
        stats["power"] += gd.general_buffs.base_power + gd.general_buffs.might * build.might + self.profession.additional_power() # type: ignore
        stats["ferocity"] += self.profession.additional_ferocity() # type: ignore
        stats["vitality"] = gd.general_buffs.base_vitality + gd.general_buffs.jade_bot + self.profession.additional_vitality()

        #stats = np.row_stack(np.broadcast(stat_power, stat_precision, stat_ferocity, stat_vitality)) # type: ignore

        stats["remainder"] = TARGET - stats["precision"] - stats["chance"]
        stats["precision"] += stats["remainder"]

        for i in range(NUM_OPTIONS):
            
            if build.gear_environment == "3p":
                stats.loc[i, "ferocity"] += min_stats
                if stats.loc[i, "remainder"] > min_stats:
                    stats.loc[i, "power"] += min_stats + maj_stats - stats.loc[i, "remainder"]
                else:
                    stats.loc[i, "power"] += maj_stats
                    stats.loc[i, "vitality"] += min_stats - stats.loc[i, "remainder"]
            else:
                stats.loc[i, "power"] += maj_stats
                stats.loc[i, "ferocity"] += min_stats + maj_stats - stats.loc[i, "remainder"]
                stats.loc[i, "vitality"] += min_stats

            stats.loc[i, "vitality"], stats.loc[i, "power"], stats.loc[i, "precision"], stats.loc[i, "ferocity"] = self.profession.stat_conversion(stats.loc[i, "vitality"], stats.loc[i, "power"], stats.loc[i, "precision"], stats.loc[i, "ferocity"]) # type: ignore

        if build.utility:
            stats["power"] += stats["precision"] * gd.general_buffs.stones_prec
            stats["power"] += stats["ferocity"] * gd.general_buffs.stones_fero

        stats["ferocity_equivalent"] = self.profession.ferocity_equivalent(stats["ferocity"])

        stats["effective_power"] = stats["power"] * (1.5 + stats["ferocity_equivalent"] / 1500)

        gs = GearSelect(build)
        stats["overshoot"] = [gs.overshoot_values(remainder) for remainder in stats["remainder"]]
        selection: pd.DataFrame = stats[stats["effective_power"] == stats["effective_power"].max()] # type: ignore


        selection["absolute_remainder"] = np.minimum(abs(selection["remainder"] - min_stats), abs(selection["remainder"] - maj_stats))
        selection.sort_values("absolute_remainder", inplace=True, kind="stable")
        
        selection.sort_values("prec_infusions", inplace=True, kind="stable")

        selection["food_prio"] = 0
        selection.loc[:,"food_prio"] += (selection["food"] == "truffle") * 1
        selection.loc[:,"food_prio"] += (selection["food"] == "curry") * 2
        selection.loc[:,"food_prio"] += (selection["food"] == "butternut") * 2
        selection.sort_values("food_prio", inplace=True, kind="stable")

        selection["absolute_overshoot"] = [min(overshoot) for overshoot in selection["overshoot"]]
        selection.sort_values("absolute_overshoot", inplace=True, kind="stable")

        return selection.iloc[0]
    
    def calculate(self, constraints):
        selection = self.calc_ep(constraints)
        return selection