# Boon Duration Optimizer (BDO mode) — wiki research, 2026-09-18

Goal: toggle in the builder that switches the objective from
"exactly 100% crit, maximize effective power" to
"exactly 100% boon duration, maximize healing power".
Avoid toughness (tank aggro). Vitality > power/precision as soft extras.

## Verified mechanics

- **15 concentration = 1% boon duration** at level 80 (wiki-confirmed).
- **Boon duration caps at +100%** → target = 1500 concentration-equivalent.
- Concentration and flat "+X% boon duration" sources (runes, sigil, traits)
  **add linearly inside one capped term** → exactly solvable, same math as crit.
  Each 1% BD source = 15 concentration-equivalent.
- Boon-SPECIFIC duration (e.g. Firebrand rune's +30% quickness) adds into the
  same cap but only for that boon → breaks the single-number model; exclude
  from the pool, note in UI.
- Skill-based base-duration multipliers (e.g. Sphere Specialist) are uncapped
  and multiplicative → ignore for the solve (analog of crit_damage_pct).
- Base concentration and base healing power are both 0.

## Gear prefixes (toughness-free)

- **Harrier's** (3-stat): Power major, Healing+Concentration minor
  → the only toughness-free concentration prefix in 3-stat. The "Assassin's" of BDO mode.
- **Magi's** (3-stat): Healing major, Precision+Vitality minor
  → zero concentration, max healing. The "Berserker's" AND the "Valkyrie" (overshoot sink) in one.
- 4-stat with conc, toughness-free: Diviner's (P+Conc major, Prec+Fero — no healing, boon-DPS),
  Plaguedoctor's (Vit+CondDmg major, Heal+Conc minor), Ritualist's (Vit+CondDmg, Conc+Exp),
  Seraph (Prec+CondDmg, Conc+Heal) — all waste a major on condition damage for a healer.
- Banned (toughness): Minstrel's, Giver's, Commander's, Vigilant, Wanderer's, Celestial.

## Runes (six-tier totals; ⚑ = contains toughness)

| Rune                                                                       | Healing                                                  | BD%                          | Other                      |
| -------------------------------------------------------------------------- | -------------------------------------------------------- | ---------------------------- | -------------------------- |
| Water                                                                      | 175                                                      | **25%**                      |                            |
| Monk                                                                       | **300**                                                  | 15%                          |                            |
| Altruism                                                                   | 175                                                      | 15%                          | +125 vitality              |
| Leadership ⚑(36)                                                           | 36                                                       | 25% (+36 conc ≈ 27.4% total) | +36 all stats              |
| Rebirth ⚑(125)                                                             | 175                                                      | 15%                          | +125 toughness (6th)       |
| Radiance                                                                   | –                                                        | 25%                          | +175 vitality              |
| Sanctuary                                                                  | –                                                        | 15%                          | +300 vitality              |
| Fireworks                                                                  | –                                                        | 25%                          | +175 power                 |
| Pack                                                                       | –                                                        | 15%                          | +175 power, +125 precision |
| Surging                                                                    | –                                                        | 15%                          | +175 power, movement       |
| Chronomancer                                                               | –                                                        | 10%                          | +175 power, +100 precision |
| Herald / Durability / Earth / Mercy / Defender / Guardian / Snowfall       | ⚑ toughness lines — banned                               |                              |                            |
| All-stats runes (Tempest, Stars, Traveler, Zephyrite, Revenant, Divinity…) | +36 all (incl. conc, healing, ⚑36 toughness) — dominated |                              |                            |

## Sigils

- **Concentration: flat +10% BD** (= 150 conc-eq), unconditional. The cap-filler.
- **Bounty**: +9 conc/stack on kill, 25 stacks = +225 conc (15% BD), ends on down
  → the Perception analog (stacking-sigil checkbox).
- **Transference: +10% outgoing healing**, no BD → the Force analog (pure secondary).
- Benevolence / Life: stacking outgoing-heal / healing-power on kill — verify at impl.
- Water / Renewal: heal procs, no stats — outside optimization.

## Utility (oil slot)

- **Magnanimous Maintenance Oil**: conc = 3% of vitality + 3% of toughness
  (toughness ≈ 0 for us; vit→conc coupling = Weaver-style circular dependency,
  solver machinery exists). Jade bot +235 vit feeds this!
- **Toxic Maintenance Oil**: conc = 3% of power + 6% of condition damage.
- **Bountiful Maintenance Oil**: outgoing healing = 0.6%/100 healing power
  + 0.8%/100 concentration. No BD — pure secondary, values conc twice.
- Potent/Enhanced Lucent Oil, Peppermint Oil, Furious/Corsair: check values at impl.
- No concentration writ exists.

## Food

- **Bowl of Fruit Salad with Mint Garnish** (ascended): +100 healing, +70 conc,
  **+10% outgoing healing** — the healer food.
- 100-conc foods exist (Green Chile Ice Cream, Soul Pastry, Fried Golden
  Dumpling, Spring Roll…) — secondary stats vary, healing pairings TBD at impl.
- **No +% boon duration food.** (Delectable Birthday Cake myth busted:
  +40 all stats, and since 2023 it cannot even overwrite nourishment.)

## Infusions

- **Concentration WvW Infusion +5** and **Healing WvW Infusion +5** both exist
  (also Mystical +5 agony = conc) → same 18-slot split model as prec/power.

## Relic

- **Relic of the Herald**: +25 conc/stack on boon application, 3s, 10 stacks
  = **+250 conc (≈16.7% BD)**. Near-permanent on a boon healer → the Mistburn
  analog (uptime assumption + stable-backup reasoning). No flat-healing relic
  known → competes against "utility relic of your choice".

## Traits (via generate_traits pipeline extension)

API facts to extract: AttributeAdjust → BoonDuration (= concentration),
BuffConversion → BoonDuration, Buff/percent boon duration, plus Healing facts.
Wiki names to expect: Honorable Staff, Reinforced Potency, Bolstered Bonds,
Roaring Reveille, Inspiring Implements, Compounding Chemicals, Double Helix,
Lingering Magic, Premeditation, Elemental Enchantment, Gathered Focus,
Chaotic Persistence, Fortissimo, Sand Sage, Boon of Creation; conversions:
Life Attunement (heal→conc), Twisted Medicine (vit→conc), Elevated Compassion,
Kinetic Accelerators. Skills: Signet of Mercy (+120 conc passive).

## Open modeling questions

1. Gear pool: v1 = Harrier+Magi only (hide 3p/4p toggle in boon mode)?
2. Toughness strictness: ban only dedicated toughness lines, or also the
   +36 all-stats crumbs (Leadership) / Rebirth's 125-toughness 6th bonus?
3. Outgoing-healing % vs healing power ranking (multiplicative vs additive —
   the crit_damage neutrality argument does NOT transfer here).
4. Tie-break order after healing power: vitality → power → precision?
5. Second sigil default = Transference (Force analog)?
6. Relic of the Herald at full stacks vs free-choice relic?
7. Exotic trinket jewels: no Harrier/Magi exquisite jewels seem to exist
   (Moonstone=Wanderer's, Freshwater Pearl=Minstrel's, Azurite=Sentinel's) —
   ascended-only trinkets in boon mode? Verify Passion Flower et al. at impl.
8. Boon-specific % sources excluded (quickness/might duration runes)?

## Decisions (implemented 2026-09-18, commits d36e521 / 4d6d141 / 60c6e76)

1. Gear pool: Harrier's + Magi's only, env toggle hidden in boon mode.
2. Leadership allowed with an aureus toughness warning; Rebirth stays out.
3. Ranking: two tabs (healing power first / outgoing % first), no K index.
   Tabs collapse when both rankings agree. Tie order per tab:
   exact -> miss -> primary -> secondary -> vitality -> power -> precision.
4. Exotic trinket upgrades one rarity down: Platinum Doubloon (+40 conc)
   vs Crest of the Magi (+20 heal / +14 prec / +14 vit).
5. Herald relic at max stacks behind its own checkbox + aureus warning;
   stable backup avoids kill-stack sigils AND the Herald relic.
6. Outgoing healing stacks ADDITIVELY (wiki-confirmed on Invoking Harmony).
7. Conversions modeled continuously with CAP_SLACK = 1 point of
   concentration (the game floors conversions to integers; without the
   slack every oil would be locked out of "exact").
8. Follow-ups: Enhanced Lucent Oil values unverified (modeled Potent 3%/3%);
   mode is not yet part of the URL (do when merging feat/build-examples).
