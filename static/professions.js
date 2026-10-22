// The one profession order of the site: light, medium, heavy armor, and
// alphabetical within each armor class. Every list of professions (the
// optimizer's picker, the builds filter, the build list) follows it; the
// server keeps the same order in gw2ceo/general_data.py.
const PROFESSION_ORDER = [
  "Elementalist", "Mesmer", "Necromancer",   // light
  "Engineer", "Ranger", "Thief",             // medium
  "Guardian", "Revenant", "Warrior",         // heavy
];

// the browser's own chrome (status bar, address bar) follows the page's
// background: whenever the theme changes, the theme-color meta takes the
// colour the html element resolved for --bg
function syncThemeColor() {
  const meta = document.querySelector('meta[name="theme-color"]');
  if (!meta) return;
  meta.content = pageBackground();
}

// --bg is the theme's dark colour at --alpha-soft (30%) over black (style.css);
// computed here as plain hex, which every phone browser accepts for theme-color
function pageBackground() {
  const dark = getComputedStyle(document.documentElement).getPropertyValue("--theme-dark").trim();
  const match = /^#([0-9a-f]{6})/i.exec(dark);
  if (!match) return "#00081f";
  return "#" + [0, 2, 4].map(i => Math.round(parseInt(match[1].slice(i, i + 2), 16) * 0.30)
    .toString(16).padStart(2, "0")).join("");
}

// the professions' descriptions from guildwars2.com/the-game/professions
// (ArenaNet's text), shown once a profession is chosen
const PROFESSION_LORE = {
  Elementalist: "Elementalists are multifaceted spellcasters who channel elemental forces, making fire, air, earth, and water do their bidding. What they lack in physical toughness, they make up for in versatility and the ability to inflict massive damage.",
  Mesmer: "Mesmers are magical duelists who wield deception as a weapon. Using powerful illusions, clones, and phantasmal magic to ensure that their enemies can\u2019t believe their own eyes, mesmers tip the balance of every fight in their favor.",
  Necromancer: "Practitioners of the dark arts, necromancers summon minions, wield the power of ritual, and heal themselves with blood magic. Necromancers feed on life force, which they can leverage offensively or use to delay their own demise.",
  Engineer: "Masters of mechanical mayhem, engineers love to tinker with explosives, elixirs, and all manner of hazardous gadgets. They support their allies with alchemic weaponry, deploy ingenious inventions, or lay waste to foes with a wide array of mines, bombs, and grenades.",
  Ranger: "Rangers rely on a keen eye, a steady hand, and the power of nature itself. Unparalleled survivalists with traps, nature spirits, and a stable of loyal pets at their command, rangers can adapt to any situation.",
  Thief: "Experts at stealth and surprise, thieves move through the shadows, vanish into thin air, or steal items from their opponents and use them as weapons. Thieves practice an agile, acrobatic fighting style, which makes them very hard to hit.",
  Guardian: "Guardians are devoted fighters who protect their allies and smite their enemies by drawing from the power of their virtues. True guardians are brilliant tacticians and selfless defenders who know how to empower their allies to achieve victory.",
  Revenant: "Heavily armored and equipped with the otherworldly powers of the Mists, revenants channel Tyria\u2019s legends to slaughter foes, unleash chaos on the battlefield, and support their allies.",
  Warrior: "Warriors are masters of weaponry who rely on speed, strength, toughness, and heavy armor to survive in battle. Adrenaline fuels their offensive power\u2014the longer warriors stay in a fight, the more dangerous they become.",
};
