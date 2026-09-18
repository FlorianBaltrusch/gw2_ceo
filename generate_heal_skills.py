"""Generate assets/heal_skills.csv from the GW2 API and the wiki.

The boon optimizer's healing-profile slider ranks builds by the effective
healing index (K + healing power) x (1 + outgoing%), where K is a healing
skill's base-to-coefficient ratio: total heal = base + coefficient x healing
power, so K = base / coefficient is the point where one percent of outgoing
healing is worth exactly as much as one percent more healing power. This
script collects K for the healing (and barrier) skills of every profession,
so the website can offer "pick the K of this skill".

Skill names come from three sources: the heal/utility/elite skills and all
weapon skills of each profession (GW2 API, shared disk cache), filtered to
those carrying a healing fact, plus a hand-curated list of profession-
mechanic skills (celestial avatar, tomes, legends ...) the API does not
enumerate per profession. The numbers come from the wiki's
{{skill fact|healing|BASE|coefficient=C|game mode = pve}} templates; skills
whose wiki page cannot be parsed are reported and skipped - add their page
title to EXTRA_SKILLS or fix the name if they matter.

Usage:  python generate_heal_skills.py   (run from the repository root)
"""

import re

import pandas as pd
import requests

from gw2ceo.api import get_api_data, get_api_data_bulk

WIKI_API = "https://wiki.guildwars2.com/api.php"

# profession-mechanic healing skills the API's per-profession lists miss
EXTRA_SKILLS = {
    "Guardian": ["Chapter 1: Desert Bloom", "Chapter 3: Azure Sun",
                 "Chapter 4: Shining River", "Epilogue: Eternal Oasis",
                 "Wings of Resolve", "Virtue of Resolve"],
    "Ranger": ["Cosmic Ray", "Seed of Life", "Lunar Impact", "Rejuvenating Tides"],
    "Elementalist": ["Overload Water"],
    "Engineer": ["Med Blaster", "Vital Burst"],
    "Revenant": ["Project Tranquility", "Ventari's Will", "Natural Harmony",
                 "Purifying Essence"],
    "Necromancer": ["Sand Cascade", "Transfusion"],
    "Thief": ["Siphon"],
}

# the regeneration boon is available to everyone and defines the
# coefficient-heavy end of the spectrum (130 + 0.125 x healing power per second)
UNIVERSAL_ROWS = [
    {"profession": "", "skill": "Regeneration (boon, per second)",
     "kind": "healing", "base": 130, "coefficient": 0.125},
]

SKILL_FACT = re.compile(r"\{\{skill fact\|([^{}]*)}}", re.IGNORECASE)


def healing_skill_names(profession: dict) -> list[str]:
    """Names of the profession's heal/utility/elite and weapon skills that
    carry a healing amount in their API facts."""
    ids = [s["id"] for s in profession.get("skills", [])]
    for weapon in profession.get("weapons", {}).values():
        ids += [s["id"] for s in weapon.get("skills", [])]
    names = []
    for skill in get_api_data_bulk("skills", list(dict.fromkeys(ids))):
        for fact in skill.get("facts", []):
            if fact.get("type") == "AttributeAdjust" and fact.get("target") == "Healing":
                names.append(skill["name"])
                break
    return names


def fetch_wikitexts(titles: list[str]) -> dict[str, str]:
    """Raw wikitext per page title, 50 titles per request, redirects followed."""
    texts: dict[str, str] = {}
    for start in range(0, len(titles), 50):
        chunk = titles[start:start + 50]
        response = requests.get(WIKI_API, params={
            "action": "query", "format": "json", "prop": "revisions",
            "rvprop": "content", "rvslots": "main", "redirects": 1,
            "titles": "|".join(chunk),
        }, timeout=30).json()
        redirected = {r["to"]: r["from"] for r in response["query"].get("redirects", [])}
        normalized = {n["to"]: n["from"] for n in response["query"].get("normalized", [])}
        for page in response["query"]["pages"].values():
            revisions = page.get("revisions")
            if not revisions:
                continue
            title = page["title"]
            original = redirected.get(title, title)
            original = normalized.get(original, original)
            texts[original] = revisions[0]["slots"]["main"]["*"]
    return texts


def parse_heal_facts(wikitext: str) -> list[tuple]:
    """All (label, kind, base, coefficient) healing/barrier facts of a page,
    PvE values only (or unsplit). One skill can heal in several distinct ways
    (initial hit vs per second ...) with different K - each becomes a row,
    labeled by the template's alt text."""
    facts = []
    for content in SKILL_FACT.findall(wikitext):
        params = [p.strip() for p in content.split("|")]
        if not params or params[0].lower() not in ("healing", "barrier"):
            continue
        kind = params[0].lower()
        base = coefficient = None
        label, mode = "", ""
        for param in params[1:]:
            if "=" in param:
                key, _, value = param.partition("=")
                key = key.strip().lower().replace(" ", "")
                if key == "coefficient":
                    try:
                        coefficient = float(value.strip())
                    except ValueError:
                        pass
                elif key == "alt":
                    label = value.strip()
                elif key == "gamemode":
                    mode = value.strip().lower()
            elif base is None:
                try:
                    base = float(param.replace(",", ""))
                except ValueError:
                    pass
        if base is None or not coefficient or coefficient <= 0:
            continue
        if mode and "pve" not in mode:
            continue  # pvp/wvw split value
        facts.append((label, kind, base, coefficient))
    return list(dict.fromkeys(facts))


def main():
    rows = list(UNIVERSAL_ROWS)
    for prof_name in get_api_data("professions"):
        profession = get_api_data(f"professions/{prof_name}")
        names = healing_skill_names(profession) + EXTRA_SKILLS.get(prof_name, [])
        names = list(dict.fromkeys(names))
        texts = fetch_wikitexts(names)
        missing = []
        for name in names:
            facts = parse_heal_facts(texts.get(name, ""))
            if not facts:
                missing.append(name)
                continue
            for label, kind, base, coefficient in facts:
                skill = f"{name} ({label})" if label else name
                rows.append({"profession": prof_name, "skill": skill, "kind": kind,
                             "base": base, "coefficient": coefficient})
        print(f"{prof_name}: {len(names) - len(missing)} healing skills"
              + (f", no wiki numbers for: {missing}" if missing else ""))

    df = pd.DataFrame(rows)
    df = df.loc[df["coefficient"] > 0]
    df["k"] = (df["base"] / df["coefficient"]).round().astype(int)
    df = df.sort_values(by=["profession", "k"])
    df.to_csv("assets/heal_skills.csv", index=False)
    print(f"\ntotal rows: {len(df)} -> assets/heal_skills.csv")
    print(f"K range: {df['k'].min()} .. {df['k'].max()}")


if __name__ == "__main__":
    main()
