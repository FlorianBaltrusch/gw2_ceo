"""Build template chat links: a real game link survives decode -> words ->
encode byte for byte, and the words form matches what it decodes to."""
import tomllib

from gw2ceo import builds

# the Open World Tempest link from builds/README.md, copied from the game
GAME_LINK = "[&DQYfHSkvMBvHEscSywClEr4BwxJyAHQSJgCZEgAAAAAAAAAAAAAAAAAAAAADWQBWAGcAAA==]"


def words_of(decoded):
    """The build in words, as a build file would state it."""
    return {
        "profession": decoded["profession"],
        "traitlines": [{"line": line["name"], "traits": list(line["selected"])} for line in decoded["lines"]],
        "skills": [skill["name"] if skill else 0 for skill in decoded["skills"]["land"]],
        "aquatic_skills": [skill["name"] if skill else 0 for skill in decoded["skills"]["aquatic"]],
        "weapons": decoded["weapons"],
    }


def test_game_link_round_trips():
    decoded = builds.decode_template(GAME_LINK)
    assert decoded["profession"] == "Elementalist"
    assert [line["name"] for line in decoded["lines"]] == ["Fire", "Air", "Tempest"]
    assert builds.encode_template(words_of(decoded), "test") == GAME_LINK


def test_words_match_their_link(root):
    for slug in ("raid-power-chronomancer", "support-druid", "ow-power-vindicator"):
        raw = tomllib.load(open(root / "builds" / f"{slug}.toml", "rb"))
        link = builds.encode_template(raw, slug)
        decoded = builds.decode_template(link)
        assert [line["name"] for line in decoded["lines"]] == [entry["line"] for entry in raw["traitlines"]]
        for line, entry in zip(decoded["lines"], raw["traitlines"]):
            picked = [line["majors"][tier][choice - 1]["name"] if choice else 0
                      for tier, choice in enumerate(line["selected"])]
            assert picked == [name if isinstance(name, str) else 0 for name in entry["traits"]]
        assert decoded["weapons"] == raw["weapons"]
        words = words_of(decoded)
        if "legends" in raw:        # a Revenant's skills follow from its legends, they are not named
            words = {k: v for k, v in words.items() if k not in ("skills", "aquatic_skills")} | {"legends": raw["legends"]}
        if "pets" in raw:
            words["pets"] = raw["pets"]
        assert builds.encode_template(words, slug) == link


def test_wrong_names_fail_loudly():
    import pytest
    raw = {"profession": "Thief", "traitlines": [{"line": "Trickery", "traits": ["Not A Trait", 0, 0]}]}
    with pytest.raises(ValueError, match="Trickery adept trait"):
        builds.encode_template(raw, "test")
