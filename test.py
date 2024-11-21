from common.types import BuildSuggestion

def func1(gear_environment = "3p",
        weapon_type = "1h",
        weapon_rarity = "c",
        food = True,
        utility = True,
        fury = True,
        might = True,
        custom_1 = True,
        custom_2 = True,
        name_filter_1 = True,
        name_filter_2 = True,
        name_filter_3 = True):
    return None

def func2(gear_environment = "3p",
        weapon_type = "1h",
        weapon_rarity = "c",
        food = True,
        utility = True,
        fury = True,
        might = True,
        custom_2 = True,
        custom_3 = True,
        custom_4 = True,
        name_filter_1 = True,
        name_filter_2 = True,
        name_filter_3 = True):
    return None


options = {
    'gear_environment': "3p",
    'weapon_type': "1h",
    'weapon_rarity': "c",
    'food': True,
    'utility': True,
    'fury': True,
    'might': True,
    'name_filter_1': True,
    'name_filter_2': True,
    'name_filter_3': True
}



customoptions = {
    "custom1": True
}
func1(**options, **customoptions)