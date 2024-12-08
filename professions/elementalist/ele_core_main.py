import pandas as pd
from common.calculate import Profession
from dataclasses import dataclass

@dataclass
class BuildConstraints:
    zephyrs_speed: bool = True
    signet_of_fire: bool = True
    ferocious_winds: bool = True


class Elementalist(Profession):
    def __init__(self, build: BuildConstraints):
        self.build = build
        self.general_buffs = pd.read_excel('professions/elementalist/ele_buffs.xlsx', index_col=0)["Buffwert"].to_dict()

    def additional_crit_chance(self):
        return self.general_buffs["zephyrs_speed"] * self.build.zephyrs_speed

    def additional_precision(self):
        return self.general_buffs["signet_of_fire"] * self.build.signet_of_fire
    
    def stat_conversion(self, vitality, power, precision, ferocity):
        ferocity += precision * self.general_buffs["ferocious_winds"] * self.build.ferocious_winds
        return vitality, power, precision, ferocity