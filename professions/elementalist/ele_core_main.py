import common.general_data as gd
import numpy as np
import pandas as pd
from common.types import BuildSuggestion, BuildConstraints
from common.calculate import Profession
from argparse import Namespace

class Elementalist(Profession):
    def __init__(self):
        self.general_buffs = pd.read_excel('professions/elementalist/ele_buffs.xlsx', index_col=0)["Buffwert"].to_dict()

    def additional_crit_chance(self, build):
        return self.general_buffs["zephyrs_speed"] * build.zephyrs_speed

    def additional_precision(self, build):
        return self.general_buffs["signet_of_fire"] * build.signet_of_fire
    
    def stat_conversion(self, build, vitality, power, precision, ferocity):
        ferocity += precision * self.general_buffs["ferocious_winds"] * build.ferocious_winds
        return vitality, power, precision, ferocity