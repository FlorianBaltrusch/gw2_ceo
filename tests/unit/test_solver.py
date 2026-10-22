"""The rules the optimizer promises, one test each."""
import numpy as np
import pytest

import gw2ceo.profession as profession_module
from gw2ceo import calculate
from gw2ceo.dtypes import BuildConstraints
from gw2ceo.gearselect import GearSelect
from gw2ceo.solve import solve
from tests.unit.conftest import build_args


def test_crit_constants():
    assert calculate.TARGET == 2995 and calculate.CRIT_FLOOR == 895   # (2995 - 895) / 21 = 100%


def test_crit_mode_hits_the_cap_exactly():
    for slug in ("raid-power-deadeye", "ow-event-power-daredevil", "raid-power-chronomancer"):
        result = solve(build_args(slug))
        assert result["exact"] is True, slug
        assert abs(result["crit_pct"] - 100) < 1e-6, slug
        assert abs(result["absolute_overshoot"]) < 1e-3, slug


def test_free_crit_mode_uses_the_games_crit_formula():
    """crit chance = (precision - 895) / 21 % plus the percentage sources."""
    for slug in ("ow-event-power-daredevil", "wvw-power-ranger", "raid-power-tempest"):
        result = solve(build_args(slug, mode="power"))
        expected = (result["precision"] - calculate.CRIT_FLOOR + result["chance"]) / 21
        assert abs(result["crit_pct"] - expected) < 1e-6, slug


def test_crit_above_the_cap_is_worth_nothing():
    """With every crit-chance trait a Thief is over 100% before any gear:
    the solver then buys no precision at all, but reports the real chance."""
    import pandas as pd
    from werkzeug.datastructures import MultiDict
    traits = pd.read_csv("assets/traits.csv")
    ids = sorted({int(i) for i in traits[(traits.profession == "Thief") & (traits.effect == "crit_chance")
                                         & (traits.kind == "trait")].id})
    args = MultiDict([("mode", "power"), ("profession", "Thief"), ("parameters", "4p"), ("handedness", "2h"),
                      ("fury", "true"), ("stacking", "true"), ("writs", "true")]
                     + [("traits[]", str(i)) for i in ids]
                     + [("armor[]", k) for k in ["twohanded", "chest", "legs", "head", "shoulders", "gloves",
                                                 "boots", "amulet", "ring1", "ring2", "accessory1",
                                                 "accessory2", "back-item"]])
    result = solve(args)
    assert result["crit_pct"] > 100
    assert result["prec_infusions"] == 0
    assert all(group["precision_major"] == 0 for group in result["equipment"])


def _all_ascended_3p_2h():
    return BuildConstraints(gear_environment="3p", weapon_type="2h",
                            num_ascended=np.array([0, 1, 1, 1, 1, 1, 1, 1, 1, 2, 2, 1]),
                            food=True, utility=True, fury=True, might=25)


def test_slot_priority_for_stat_identical_splits():
    """Head, shoulders, chest, gloves, legs, boots, weapons, back item,
    accessories, amulet, rings, jewels: the earlier piece turns Assassin's
    first when several pieces could."""
    gear = GearSelect(_all_ascended_3p_2h())
    labels = [label for label, count in gear.groups if count]
    assert labels[:6] == ["Head", "Shoulders", "Chest", "Gloves", "Legs", "Boots"]
    assert labels[6:] == ["Weapon", "Back item", "Accessories (ascended)", "Amulet", "Rings (ascended)"]
    floor = sum(min(options) for options in gear.equipment)
    index = {label: i for i, (label, _) in enumerate(gear.groups)}
    delta = gear.equipment[index["Shoulders"]][1] - gear.equipment[index["Shoulders"]][0]
    assert delta == gear.equipment[index["Gloves"]][1] - gear.equipment[index["Gloves"]][0]  # same stats

    one = gear.get_best_equipment(floor + delta)       # one of shoulders/gloves/boots
    major = lambda assignment, label: gear.option_meta[index[label]][assignment[index[label]]][0]  # noqa: E731
    assert (major(one, "Shoulders"), major(one, "Gloves"), major(one, "Boots")) == (1, 0, 0)
    two = gear.get_best_equipment(floor + 2 * delta)
    assert (major(two, "Shoulders"), major(two, "Gloves"), major(two, "Boots")) == (1, 1, 0)


def test_wvw_pins_the_brawler_rune():
    result = solve(build_args("ow-event-power-daredevil", wvw="1"))
    assert result["rune"] == "brawler"


def test_wasted_concentration_sigil_gives_way_to_water(monkeypatch):
    """When traits (and food, rune, infusions) plus the Concentration sigil
    exceed the cap even with the lowest-concentration gear, the sigil is
    dropped: Transference stays, the other slot is Water ("free")."""
    original = profession_module.Profession.boon_duration_pct
    best = solve(build_args("support-tempest"))["best"]
    assert best["sigil"] == "transference+concentration" and best["exact"]
    monkeypatch.setattr(profession_module.Profession, "boon_duration_pct", lambda self: original(self) + 85)
    best = solve(build_args("support-tempest"))["best"]
    assert best["sigil"] == "transference+free"
