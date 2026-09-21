# Curated builds

One TOML file per build. The file name (without `.toml`) is the build's URL
slug: `builds/ow-tempest.toml` is shown at `/builds/ow-tempest`. The server
re-reads the folder whenever a file changes, so editing a build while the
dev server runs needs no restart. A broken file fails loudly with its name
and the offending key.

## Adding a build

1. **Chat link.** In the game, open the build template and copy its chat
   link. It carries the profession, the three trait lines with the chosen
   traits, all ten skills (land and underwater) and the equipped weapon
   types. Paste it into `chatlink`.
2. **Optimizer link.** Set the build up in the optimizer (traits, gear
   toggles, mode) and press "Copy optimizer link" under the result. Paste
   it into `optimizer`. The build page runs the same calculation and lists
   the result per slot: stat prefix and rarity of every piece, rune, sigils,
   relic, food, utility and infusions, plus the headline numbers. The
   weapon sets come from the chat link's weapon types.
3. **Name, category, text.** Exactly one category, optional tags, a
   summary and notes.

That is a complete build file:

```toml
name = "Open World Tempest"
category = "openworld"          # exactly one of: openworld | raid | support | wvw
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
