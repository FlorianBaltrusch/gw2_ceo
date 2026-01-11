from gw.traits import Trait


class Profession:

    def __init__(self, traits: list[Trait]):
        self.traits = traits

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
        return vitality, power, ferocity
    
    def ferocity_equivalent(self, ferocity):
        return ferocity

    def vit_prec_conversion(self):
        return 0