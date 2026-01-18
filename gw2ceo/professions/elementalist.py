from gw2ceo.profession import Profession
from gw2ceo.traits import Trait

ZEPHYRS_SPEED = 105
SIGNET_OF_FIRE = 180
FEROCIOUS_WINDS = 0.07

class Elementalist(Profession):

    def additional_crit_chance(self):
        return ZEPHYRS_SPEED * (Trait.zephyrs_speed in self.traits)

    def additional_precision(self):
        return SIGNET_OF_FIRE * (Trait.signet_of_fire in self.traits)
    
    def stat_conversion(self, vitality, power, precision, ferocity):
        if Trait.ferocious_winds in self.traits:
            ferocity += precision * FEROCIOUS_WINDS
        return vitality, power, ferocity