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