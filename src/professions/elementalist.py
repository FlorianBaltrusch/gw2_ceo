import pandas as pd

from src.calculate import Profession


class Elementalist(Profession):
    def __init__(self, traits: list[str]):
        self.traits = traits
        self.general_buffs = pd.read_excel('professions/elementalist/ele_buffs.xlsx', index_col=0)["Buffwert"].to_dict()

    def additional_crit_chance(self):
        return self.general_buffs["zephyrs_speed"] * ("zephyrs_speed" in self.traits)

    def additional_precision(self):
        return self.general_buffs["signet_of_fire"] * ("signet_of_fire" in self.traits)
    
    def stat_conversion(self, vitality, power, precision, ferocity):
        ferocity += precision * self.general_buffs["ferocious_winds"] * ("ferocious_winds" in self.traits)
        return vitality, power, ferocity