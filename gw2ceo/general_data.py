import numpy as np
import pandas as pd

# the site's one profession order: light, medium, heavy armor, alphabetical
# within each class (static/professions.js carries the same list for the pages)
PROFESSION_ORDER = [
    "Elementalist", "Mesmer", "Necromancer",   # light
    "Engineer", "Ranger", "Thief",             # medium
    "Guardian", "Revenant", "Warrior",         # heavy
]

traits = pd.read_csv("assets/traits.csv")
specializations = pd.read_csv("assets/specializations.csv")
try:
    # per-piece rune bonuses; optional - enables the mixed-rune rescue
    rune_tiers = pd.read_csv("assets/rune_tiers.csv")
except FileNotFoundError:
    rune_tiers = None
general_buffs = pd.read_csv("assets/general_buffs.csv", index_col=0).wert
gear_stats = pd.read_csv("assets/gear_stats.csv", index_col=[0, 1, 2, 3]).value
runes = pd.read_csv("assets/runes.csv", index_col=0)
food = pd.read_csv("assets/food.csv", index_col=0)
boon_runes = pd.read_csv("assets/boon_runes.csv", index_col=0)
boon_food = pd.read_csv("assets/boon_food.csv", index_col=0)
heal_skills = pd.read_csv("assets/heal_skills.csv")
names = [
    "Chest",
    "L/R",
    "Head",
    "S/G/B",
    "S/G/B",
    "S/G/B",
    "Am/W2",
    "L/R",
    "L/R",
    "Access",
    "Access",
    "Back",
    "Jew",
    "Jew",
    "Jew",
    "Jew",
    "Jew",
    "Jew",
    "W1",
    "Am/W2",
    "Infu",
    "Infu",
]


def full_armor(majmin, asc_count, param_env, weapon):

    if weapon == "1h":
        full_armor = np.array([2, 0, 1, 1, 1, 1, 1, 1, 1, 2, 2, 1])
    else:
        full_armor = np.array([0, 1, 1, 1, 1, 1, 1, 1, 1, 2, 2, 1])

    asc_armor = np.minimum(asc_count, full_armor)
    ex_armor = full_armor - asc_armor
    num_jewels = ex_armor[8:12].sum()
    total = gear_stats["Asc", param_env, majmin][:12] * asc_armor
    total += gear_stats["Ex", param_env, majmin][:12] * ex_armor
    return total.sum() + num_jewels * gear_stats["Ex", param_env, majmin].iloc[12]


def num_infusions(asc_count, weapon):
    if weapon == "1h":
        full_armor = np.array([2, 0, 1, 1, 1, 1, 1, 1, 1, 2, 2, 1])
    else:
        full_armor = np.array([0, 1, 1, 1, 1, 1, 1, 1, 1, 2, 2, 1])
    asc_armor = np.minimum(asc_count, full_armor)
    return np.dot(asc_armor, [1, 2, 1, 1, 1, 1, 1, 1, 0, 3, 1, 2])
