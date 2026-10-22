"""Every build file loads, decodes and solves; the list keeps its order."""
import os

import gw2ceo.general_data as gd
from gw2ceo import builds


def test_every_build_file_loads(catalogue, root):
    files = sorted(name for name in os.listdir(root / "builds") if name.endswith(".toml"))
    assert [b["slug"] for b in sorted(catalogue, key=lambda b: b["slug"])] == [f[:-5] for f in files]
    assert len(catalogue) >= 28


def test_builds_are_complete(catalogue):
    for build in catalogue:
        assert build["category"] in builds.CATEGORIES, build["slug"]
        assert 1 <= len(build["lines"]) <= 3, build["slug"]
        for line in build["lines"]:
            assert len(line["minors"]) == 3 and len(line["majors"]) == 3
            assert all(0 <= choice <= 3 for choice in line["selected"])
        assert len(build["skills"]["land"]) == 5 and len(build["skills"]["aquatic"]) == 5
        assert build["chatlink"].startswith("[&DQ") and build["chatlink"].endswith("]")
        if build["optimizer"]:
            assert build["gear_warning"] is None, (build["slug"], build["gear_warning"])
            assert len(build["gear"]["armor"]) == 6 and len(build["gear"]["trinkets"]) == 6, build["slug"]
            assert build["character"]["headline"]["value"] > 0, build["slug"]


def test_alternatives_decode_and_keep_skills(catalogue):
    seen = 0
    for build in catalogue:
        line_names = [line["name"] for line in build["lines"]]
        for alt in build["alternatives"]:
            seen += 1
            assert alt["replaces"] in line_names, build["slug"]
            assert sum(1 for choice in alt["line"]["selected"] if choice) == 3, build["slug"]
            decoded = builds.decode_template(alt["chatlink"])
            assert [s and s["name"] for s in decoded["skills"]["land"]] == \
                   [s and s["name"] for s in build["skills"]["land"]], build["slug"]
            assert decoded["weapons"] == build["template_weapons"], build["slug"]
            assert alt["line"]["name"] in [line["name"] for line in decoded["lines"]]
            if alt["gear_differs"]:
                assert alt["gear"] and alt["character"], build["slug"]
    assert seen >= 6


def test_list_order(catalogue):
    """Profession order, then core before the elite specs in expansion order,
    then instanced, open world, support, WvW."""
    keys = [(gd.PROFESSION_ORDER.index(b["profession"]), b["spec_id"],
             builds.CATEGORY_ORDER.index(b["category"]), b["name"]) for b in catalogue]
    assert keys == sorted(keys)
    assert catalogue[0]["profession"] == "Elementalist"


def test_pets_and_legends(catalogue):
    by_slug = {b["slug"]: b for b in catalogue}
    druid = by_slug["support-druid"]
    assert [p["name"] for p in druid["pets"]["land"]] == ["Fanged Iboga", "Jungle Stalker"]
    vindicator = by_slug["ow-power-vindicator"]
    assert [l["name"] for l in vindicator["legends"]["land"]] == ["Alliance", "Assassin"]
    assert vindicator["skills"]["land"][0]["name"] == "Selfish Spirit"


def test_card_summary_keys(catalogue):
    summary = builds.summary(catalogue[0])
    for key in ("slug", "name", "category_label", "profession", "title", "subtitle",
                "spec_icon", "weapon_summary", "traitlines", "alternatives"):
        assert key in summary
