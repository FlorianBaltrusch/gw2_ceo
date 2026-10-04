# Curated builds

One TOML file per build. The file name (without `.toml`) is the build's URL
slug: `builds/ow-tempest.toml` is shown at `/builds/ow-tempest`. The server
re-reads the folder whenever a file changes, so editing a build while the
dev server runs needs no restart. A broken file fails loudly with its name
and the offending key.

## Adding a build

1. **Chat link, or the build in words.** In the game, open the build
   template and copy its chat link: it carries the profession, the three
   trait lines with the chosen traits, all ten skills (land and underwater)
   and the equipped weapon types. Paste it into `chatlink`. Without the
   game at hand, write the same things in words instead (see "Without a
   chat link" below); the server assembles the chat link from them and
   shows it on the page like a pasted one.
2. **Optimizer link.** Set the build up in the optimizer (traits, gear
   toggles, mode) and press "Copy optimizer link" under the result. Paste
   it into `optimizer`. The build page runs the same calculation and lists
   the result per slot: stat prefix and rarity of every piece, rune, sigils,
   relic, food, utility and infusions. The character card next to the
   skills shows the resulting attributes with their in-game meaning
   (critical chance, critical damage, health, boon duration). The weapon
   sets come from the chat link's weapon types.
3. **Name, category, text.** Exactly one category, optional tags, a
   summary and notes.

That is a complete build file:

```toml
name = "Open World Tempest"
category = "openworld"          # exactly one of: openworld | raid | support | wvw
                                # ("raid" is shown as Instanced PvE, "wvw" as World vs. World)
tags = ["event"]                # optional extra labels shown next to the category
summary = "One or two sentences shown on the build's page header."
chatlink = "[&DQYfHSkvMBvHEscSywClEr4BwxJyAHQSJgCZEgAAAAAAAAAAAAAAAAAAAAADWQBWAGcAAA==]"
optimizer = "/ceo?profession=Elementalist&spec=Tempest&mode=crit&traits=320,334&env=4p&..."
notes = """
Free text. Blank lines separate paragraphs.
"""
```

Only the path and query of the optimizer link are needed; the domain can
be dropped. Without an optimizer link the page shows whatever gear the
file lists (see below) and nothing else.

## Without a chat link

Leave `chatlink` out and write the build in words. Names are matched
case-insensitively, punctuation does not matter, and a wrong name fails
with the valid options listed.

```toml
profession = "Elementalist"
traitlines = [                  # one to three lines, core or elite, in any order
  { line = "Fire",    traits = ["Burning Precision", "Power Overwhelming", "Persisting Flames"] },
  { line = "Air",     traits = ["Ferocious Winds", 2, "Fresh Air"] },   # 1-3 = top to bottom
  { line = "Tempest", traits = ["Unstable Conduit", "Harmonious Conduit", "Transcendent Tempest"] },
]
skills = ["Wash the Pain Away!", "Signet of Fire", "Glyph of Storms", "Glyph of Lesser Elementals", "Glyph of Elementals"]
aquatic_skills = ["Wash the Pain Away!", "Flash-Freeze!", "Feel the Burn!", "Aftershock!", "Rebound!"]
weapons = ["Scepter", "Warhorn", "Staff"]
```

- `traits` lists the adept, master and grandmaster pick of that line; a
  tier you leave open is `0`.
- `skills` is heal, three utilities, elite. `aquatic_skills` is optional:
  without it each land skill is used underwater where the game allows it.
- `weapons` is optional: without it the types of the gear's `set1`/`set2`
  entries are used. Each type is listed once, as in the game's links.
- A Ranger names `pets = ["Fanged Iboga", "Jungle Stalker"]` (and
  `aquatic_pets`); a Revenant names `legends = ["Alliance", "Assassin"]`
  (active first; `aquatic_legends` when they differ) and leaves `skills`
  out - the legend's skills are shown. Both land in the chat link's
  profession block and under the skills on the page.
- A file may still carry `chatlink`; then that link wins and the words are
  ignored.

## An alternative trait line

A build may name one (or more) alternative trait lines. Each
`[[alternatives]]` entry is a line that stands in for one of the build's
three lines; the page draws it under the build's lines like them, with its
own chat link to copy.

```toml
[[alternatives]]
replaces = "Earth"              # which of the build's lines it stands in for
traitline = { line = "Arcane", traits = ["Arcane Restoration", "Arcane Resurrection", "Evasive Arcana"] }
note = "Arcane can be taken instead of Earth."     # optional, shown under the panel
optimizer = "/ceo?...&traits=1938,2004&..."        # optional: the alternative's own gear
```

- `replaces` may be left out when the alternative is the same line with
  other picks.
- Without `optimizer` the alternative uses the build's gear. With one, the
  page runs it too; when the result differs from the build's gear, the
  Gear and Character sections get a second tab ("with Arcane") showing it.
  Set the alternative up in the optimizer with its line ticked and paste
  its "Copy optimizer link", as for the build itself.

## Refining the gear

A `[gear]` section adds what the solver cannot know or overrides single
slots. Every key is optional; anything not given keeps the derived value.

```toml
[gear]
relic = "Relic of Karakosa"     # overrides the derived consumables by name:
food = "..."                    # rune, relic, food, utility, infusions, jade_core

[gear.armor]                    # head shoulders chest gloves legs boots
head = { skin = "Tempest Gaze Helm Skin" }
chest = { prefix = "Marauder", rarity = "exotic" }   # a deliberate deviation

[gear.trinkets]                 # back accessory1 accessory2 amulet ring1 ring2
ring1 = { infusions = "+9 Agony Infusion" }

[gear.weapons]                  # set1 set2 aquatic - a list of weapons each
aquatic = [{ type = "Trident", prefix = "Marauder", rarity = "exotic",
             sigils = ["Superior Sigil of Force", "Superior Sigil of Accuracy"] }]
set2 = [{ type = "Staff", prefix = "Marauder", sigils = ["Superior Sigil of Force"] }]
```

Per-slot tables accept `prefix`, `rarity` (`exotic`, `ascended` or
`legendary`), `skin`, `icon` (an image URL for the slot's icon square;
until then the square shows the slot name), `rune`, `sigil` or `sigils`,
`infusions`, `upgrade` (a trinket's jewel) and `note`. Weapons additionally
need `type`. A weapon set named in the file replaces the derived set of
that name entirely; `aquatic` is always yours to add, since chat links do
not carry underwater weapons.

## What the derivation assumes

- The optimizer prices one weapon set (two one-handers or one two-hander).
  The other set gets the majority prefix of the optimized one and the same
  sigils, marked "not optimized separately"; override it if it differs.
- When a slot family mixes prefixes (one Marauder and two Dragon's among
  shoulders, gloves and boots), the pieces are assigned in a fixed order.
  Which physical piece gets which prefix does not matter for the stats.
- Two one-handers in the chat link are paired main hand with off hand in
  the order the link lists them; a lone dual-wieldable type pairs with
  itself (Sword/Sword). Weapon types are listed once per link, so this is
  the best guess; a `set1`/`set2` entry in the file settles it.
