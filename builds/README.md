# Curated builds

One TOML file per build. The file name (without `.toml`) is the build's URL
slug: `builds/ow-tempest.toml` is shown at `/builds/ow-tempest`. The server
re-reads the folder whenever a file changes, so editing a build while the
dev server runs needs no restart. A broken file fails loudly with its name
and the offending key.

Traits, skills (land and underwater) and the equipped weapon types all come
from the in-game build template chat link, so they are never typed by hand:
open the build in the game, copy the template's chat link and paste it into
`chatlink`. Gear is listed explicitly because the optimizer only reports
per-slot-family counts, while the page shows every slot (later with skins).

```toml
name = "Open World Tempest"
category = "openworld"          # exactly one of: openworld | raid | support | wvw
tags = ["event"]                # optional extra labels shown next to the category
summary = "One or two sentences shown on the build's page header."
chatlink = "[&DQYfHSkvMBvHEscSywClEr4BwxJyAHQSJgCZEgAAAAAAAAAAAAAAAAAAAAADWQBWAGcAAA==]"
optimizer = "/ceo?profession=Elementalist&spec=Tempest&mode=crit&traits=..."  # optional
notes = """
Free text. Blank lines separate paragraphs.
"""

[gear]                          # every key optional; shown as a table below the slots
rune = "Superior Rune of the Scholar"   # also printed under each armor piece
relic = "Relic of the Thief"
food = "Bowl of Curry Butternut Squash Soup"
utility = "Superior Sharpening Stone"
infusions = "18 × +5 Power"
jade_core = "Tier 10"

[gear.armor]                    # head shoulders chest gloves legs boots
head = "Marauder"               # a bare string is the stat prefix (ascended)
chest = { prefix = "Marauder", rarity = "exotic", skin = "Tempest Gaze Helm", rune = "..." }

[gear.trinkets]                 # back accessory1 accessory2 amulet ring1 ring2
back = "Marauder"
ring1 = { prefix = "Marauder", infusions = "+5 Power" }

[gear.weapons]                  # set1 set2 aquatic - a list of weapons each
set1 = [
  { type = "Scepter", prefix = "Marauder", sigil = "Superior Sigil of Force" },
  { type = "Warhorn", prefix = "Marauder", sigil = "Superior Sigil of Accuracy" },
]
set2 = [{ type = "Staff", prefix = "Marauder", sigils = ["Superior Sigil of Force", "Superior Sigil of Accuracy"] }]
```

Per-slot tables accept `prefix`, `rarity` (`exotic`, `ascended` - the
default - or `legendary`), `skin`, `icon` (an image URL for the slot's icon
square; until then the square shows the slot name), `rune`, `sigil` or
`sigils`, and `infusions`. Weapons additionally need `type`.

## The optimizer link

`optimizer` is the link the optimizer's result card copies with "Copy
optimizer link": it carries the ticked traits, the stack/attunement
assumptions and every gear toggle, and reopens the builder in that exact
state and runs it. Set the build up in the optimizer once, copy the link,
paste it here. Only the path and query are needed, the domain can be
dropped.
