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
    utility: bool

    fury: bool
    might: int