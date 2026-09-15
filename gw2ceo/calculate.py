import numpy as np
import pandas as pd

import gw2ceo.general_data as gd
from gw2ceo.dtypes import BuildConstraints
from gw2ceo.gearselect import GearSelect
from gw2ceo.profession import Profession


def calc_ep(profession: Profession, build: BuildConstraints):

    # target_start_value = 2995 - gd.general_buffs.base_precision - gd.general_buffs.fury * build.fury  # 1000 + 100*21 - 5*21 = 2995
    # test_target_0 = target_start_value - gd.food.loc[food, "precision"] * build.food - gd.general_buffs.sigil_accuracy  # type:ignore  # und modifier
    min_stats = gd.full_armor("Min", build.num_ascended, build.gear_environment, build.weapon_type)
    maj_stats = gd.full_armor("Maj", build.num_ascended, build.gear_environment, build.weapon_type)     

    if build.food:
        food = gd.food
    else:
        food = pd.DataFrame(data={"power": [0], "precision": [0], "ferocity": [0]}, index=["no food"])
        food.index.name = "food"

    # candidates for the second sigil slot (the first holds a damage sigil like
    # Force, which multiplies every option equally and cancels out of the
    # comparison); the stacking sigils are modeled at their 25-stack maximum
    sigils = pd.DataFrame(data={
        "sigil": ["none", "accuracy", "perception", "bloodlust"],
        "chance": [0.0, float(gd.general_buffs.sigil_accuracy), 0.0, 0.0],
        "sigil_precision": [0.0, 0.0, float(gd.general_buffs.sigil_perception), 0.0],
        "sigil_power": [0.0, 0.0, 0.0, float(gd.general_buffs.sigil_bloodlust)],
    })
    if not build.stacking_sigils:
        sigils = sigils.loc[~sigils["sigil"].isin(["perception", "bloodlust"])]
    num_infusions = gd.num_infusions(build.num_ascended, build.weapon_type)
    infusions = pd.DataFrame(data={"prec_infusions": list(range(num_infusions+1)), "precision_inf": [5*i for i in range(num_infusions+1)], "power_inf": [5*(num_infusions-i) for i in range(num_infusions+1)], "ferocity_inf": [0]*(num_infusions+1)})

    food_rune_options = pd.merge(food.reset_index(), gd.runes.reset_index(), how="cross", suffixes=("_food", "_rune"))
    food_rune_options = pd.merge(sigils, food_rune_options, how="cross", suffixes=("_sigil", ""))
    food_rune_options = pd.merge(infusions, food_rune_options, how="cross", suffixes=("_inf", ""))

    food_rune_options[["power", "precision", "ferocity"]] = food_rune_options[["power_rune", "precision_rune", "ferocity_rune"]].values + food_rune_options[["power_food", "precision_food", "ferocity_food"]].values + food_rune_options[["power_inf", "precision_inf", "ferocity_inf"]].values  # type: ignore
    stats = food_rune_options[["prec_infusions", "sigil", "sigil_precision", "sigil_power", "food", "rune", "power", "precision", "chance", "ferocity"]]
    stats.precision = stats.precision.astype(float)
    stats.power = stats.power.astype(float)
    stats.ferocity = stats.ferocity.astype(float)
    stats.chance = stats.chance.astype(float)

    NUM_OPTIONS = food_rune_options.shape[0]

    TARGET = 2995
    stats["precision"] += gd.general_buffs.base_precision + stats["sigil_precision"]
    stats["chance"] += profession.additional_crit_chance()
    if build.fury: stats["chance"] += gd.general_buffs.fury
    stats["precision"] += profession.additional_precision()
    
    # calculate stats
    stats["power"] += gd.general_buffs.base_power + gd.general_buffs.might * build.might/25 + profession.additional_power() + profession.power_per_might() * build.might + stats["sigil_power"] # type: ignore
    stats["ferocity"] += profession.additional_ferocity() # type: ignore
    stats["vitality"] = gd.general_buffs.base_vitality + gd.general_buffs.jade_bot + profession.additional_vitality()

    #stats = np.row_stack(np.broadcast(stat_power, stat_precision, stat_ferocity, stat_vitality)) # type: ignore

    vit_prec_conversion = profession.vit_prec_conversion()

    stats["precision"] += stats["vitality"] * vit_prec_conversion

    stats["remainder"] = TARGET - stats["precision"] - stats["chance"]
    stats["precision"] += stats["remainder"]
    stats["armor_precision"] = 0

    for i in range(NUM_OPTIONS):
        if build.gear_environment == "3p":
            stats.loc[i, "ferocity"] += min_stats
            if stats.loc[i, "remainder"] > min_stats:
                stats.loc[i, "armor_precision"] = stats.loc[i, "remainder"]
                stats.loc[i, "power"] += min_stats + maj_stats - stats.loc[i, "armor_precision"]
            else:
                stats.loc[i, "armor_precision"] = (stats.loc[i, "remainder"] - min_stats * vit_prec_conversion) / (1 - vit_prec_conversion)
                stats.loc[i, "power"] += maj_stats
                stats.loc[i, "vitality"] += min_stats - stats.loc[i, "armor_precision"]
        else:
            stats.loc[i, "armor_precision"] = stats.loc[i, "remainder"] - min_stats * vit_prec_conversion
            stats.loc[i, "power"] += maj_stats
            stats.loc[i, "ferocity"] += min_stats + maj_stats - stats.loc[i, "armor_precision"]
            stats.loc[i, "vitality"] += min_stats

        stats.loc[i, "vitality"], stats.loc[i, "power"], stats.loc[i, "ferocity"] = profession.stat_conversion(stats.loc[i, "vitality"], stats.loc[i, "power"], stats.loc[i, "precision"], stats.loc[i, "ferocity"]) # type: ignore


    if build.utility:
        stats["power"] += stats["precision"] * gd.general_buffs.stones_prec
        stats["power"] += stats["ferocity"] * gd.general_buffs.stones_fero

    stats["ferocity_equivalent"] = profession.ferocity_equivalent(stats["ferocity"])

    stats["effective_power"] = stats["power"] * (1.5 + stats["ferocity_equivalent"] / 1500)

    gs = GearSelect(build)
    stats["overshoot"] = [gs.overshoot_values(remainder) for remainder in stats["armor_precision"]]

    stats["absolute_remainder"] = np.minimum(abs(stats["armor_precision"] - min_stats), abs(stats["armor_precision"] - maj_stats))

    stats["food_prio"] = 0
    stats.loc[:,"food_prio"] += (stats["food"] == "truffle") * 1
    stats.loc[:,"food_prio"] += (stats["food"] == "curry") * 2
    stats.loc[:,"food_prio"] += (stats["food"] == "butternut") * 2

    
    stats["absolute_overshoot"] = [min(overshoot) for overshoot in stats["overshoot"]]

    # the sigil-less rows become the "3% damage sigil" branch (Impact by day,
    # Night at night - identical 3% baseline): same gear solution, EP scaled
    impact = stats.loc[stats["sigil"] == "none"].copy()
    impact["sigil"] = "impact"
    impact["effective_power"] *= 1 + gd.general_buffs.sigil_impact
    stats = pd.concat([stats.loc[stats["sigil"] != "none"], impact], ignore_index=True)

    by, ascending = zip(
        ("effective_power", False),
        ("absolute_overshoot", True),
        ("prec_infusions", True),
        ("absolute_remainder", True),
        ("food_prio", True),
    )

    stats.sort_values(by=list(by), ascending=list(ascending), inplace=True) # type: ignore
    best = stats.iloc[0]

    # a stacking sigil assumes 25 stacks; offer the best stack-independent
    # option as well, so a downstate does not silently cost the crit cap
    fallback = None
    if best["sigil"] in ("perception", "bloodlust"):
        stable = stats.loc[stats["sigil"].isin(["accuracy", "impact"])]
        if not stable.empty:
            fallback = stable.iloc[0]
    return best, fallback
