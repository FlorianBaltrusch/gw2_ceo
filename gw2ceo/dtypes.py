from dataclasses import dataclass
from typing import Literal

import numpy as np
import pandas as pd


@dataclass
class BuildSuggestion:
    ep: float
    use_sigil: bool
    used_rune: str
    used_food: str
    target: float
    base_gear: str
    high_gear: pd.Series
    low_gear: pd.Series

@dataclass
class BuildConstraints:
    gear_environment: Literal["3p", "4p"]
    weapon_type: Literal["1h", "2h"]
    num_ascended: np.ndarray

    food: bool
    # allow sharpening stones in the utility slot (independent of writs)
    utility: bool

    fury: bool
    might: int

    # allow Perception/Bloodlust (25-stack sigils) in the second sigil slot;
    # off for content where stacks are unrealistic (raids, frequent downs)
    stacking_sigils: bool = True

    # allow the +200 writs (active above 90% health) in the utility slot
    writs: bool = True

    # only one sigil slot is free for stat/damage sigils (the other is
    # reserved, e.g. Energy on Mirage): candidates then compete against
    # Force's 5% instead of the second-slot 3% damage sigil
    single_sigil: bool = False

    # open-world mode: fix the food to Omnomberry Pie (+70 precision plus
    # lifesteal on crit, which the model does not price); overrides the
    # normal food contest
    omnomberry_pie: bool = False

    # boon mode: allow Relic of the Herald (stacking +250 concentration on
    # boon application, modeled at max stacks - fragile like stacking sigils)
    herald_relic: bool = True

    # boon mode: the relic slot is reserved for a proc relic the model cannot
    # price (Karakosa's blast heal ...) - no stat relic competes
    relic_reserved: bool = False

    # boon mode: allow the ascended feasts in the food pool (untick for the
    # Fine/Masterwork alternatives)
    ascended_food: bool = True

    # boon mode: toughness becomes desirable (tank aggro is wanted): Giver's
    # pieces, toughness runes and Freshwater Pearl upgrades enter the pool,
    # and toughness ranks right after the healing objective
    tank: bool = False

    # Elementalist/Engineer cannot weapon-swap in combat, so a stacking sigil
    # parked in the stowed weapon set keeps its stacks: a third sigil joins
    # the optimization next to a non-stacking active pair
    stowed_stacking: bool = False