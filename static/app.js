// Step 1: profession selection, Step 2: elite specialization selection.
// The rest of the flow (traits, gear, result) plugs in after finishSelection().

const PROFESSIONS = [
  { name: "Guardian",     img: "01_guardian.PNG" },
  { name: "Revenant",     img: "02_revenant.PNG" },
  { name: "Warrior",      img: "03_warrior.PNG" },
  { name: "Engineer",     img: "04_engineer.PNG" },
  { name: "Ranger",       img: "05_ranger.PNG" },
  { name: "Thief",        img: "06_thief.PNG" },
  { name: "Elementalist", img: "07_elementalist.PNG" },
  { name: "Mesmer",       img: "08_mesmer.PNG" },
  { name: "Necromancer",  img: "09_necromancer.PNG" },
];

const professionImage = (profession) =>
  `/profession-images/freigestellt/${PROFESSIONS.find(p => p.name === profession).img}`;

const state = { profession: null, spec: null, mode: "crit" };

const el = (id) => document.getElementById(id);

// ---------- step 1: professions ----------

function renderProfessionGrid() {
  const grid = el("prof-grid");
  grid.innerHTML = "";
  for (const prof of PROFESSIONS) {
    const tile = document.createElement("button");
    tile.className = "prof-char";
    tile.type = "button";

    const img = document.createElement("img");
    img.src = professionImage(prof.name);
    img.alt = prof.name;

    const name = document.createElement("span");
    name.className = "name";
    name.textContent = prof.name;

    tile.append(img, name);
    tile.addEventListener("click", () => selectProfession(prof.name));
    grid.append(tile);
  }
}

async function selectProfession(profession) {
  state.profession = profession;
  state.spec = null;

  const response = await fetch(`/specializations?profession=${encodeURIComponent(profession)}`);
  const specs = await response.json();

  renderSpecGrid(profession, specs.filter(s => s.elite));
  el("profession-picker").classList.add("hidden");
  el("spec-picker").classList.remove("hidden");
  el("spec-question-prof").textContent = profession;
  window.scrollTo({ top: 0 });
}

// ---------- step 2: elite specializations ----------

function renderSpecGrid(profession, eliteSpecs) {
  const grid = el("spec-grid");
  grid.innerHTML = "";

  // playing without an elite specialization is a valid choice
  grid.append(specTile({
    name: `Core ${profession}`,
    icon: `/icons/tango_${profession}.png`,
    background: `/icons/tango_${profession}.png`,  // emblem card: the tango crest itself
    coreArt: true,
  }));

  for (const spec of eliteSpecs) grid.append(specTile(spec));
}

function specTile(spec) {
  const tile = document.createElement("button");
  tile.className = "spec-tile";
  tile.type = "button";

  const art = document.createElement("span");
  art.className = spec.coreArt ? "art core-art" : "art";
  const artImage = document.createElement("img");
  artImage.src = spec.background;
  artImage.alt = "";
  art.append(artImage);

  const label = document.createElement("span");
  label.className = "label";
  const icon = document.createElement("img");
  icon.src = spec.icon;
  icon.alt = "";
  const name = document.createElement("span");
  name.className = "name";
  name.textContent = spec.name;
  label.append(icon, name);

  tile.append(art, label);
  tile.addEventListener("click", () => selectSpec(spec));
  return tile;
}

function selectSpec(spec) {
  state.spec = spec;
  finishSelection();
  loadBuilder();
}

// ---------- hand over to the main app ----------

function finishSelection() {
  el("topbar-title").textContent = `${state.spec.name} (${state.profession})`;
  const icon = el("topbar-spec-icon");
  icon.src = state.spec.icon;
  icon.classList.remove("hidden");

  const overlay = el("overlay");
  const hide = () => overlay.classList.add("hidden");
  if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
    hide();
  } else {
    overlay.classList.add("closing");
    overlay.addEventListener("animationend", hide, { once: true });
    setTimeout(hide, 350);  // fallback for browsers that skip the animation
  }

  el("topbar").classList.remove("hidden");
  el("main").classList.remove("hidden");
}

function reopenSelection() {
  const overlay = el("overlay");
  overlay.classList.remove("hidden", "closing");
  el("spec-picker").classList.add("hidden");
  el("profession-picker").classList.remove("hidden");
  el("topbar").classList.add("hidden");
  el("main").classList.add("hidden");
}

el("back-to-professions").addEventListener("click", () => {
  el("spec-picker").classList.add("hidden");
  el("profession-picker").classList.remove("hidden");
});
el("change-selection").addEventListener("click", reopenSelection);

// ---------- builder: traits ----------

const capitalize = (word) => word.charAt(0).toUpperCase() + word.slice(1);

// fact labels that merely restate the stat add nothing next to "+200 power"
const REDUNDANT_NOTES = new Set([
  "power", "precision", "ferocity", "vitality", "concentration",
  "power increase", "precision increase", "ferocity increase", "vitality increase",
  "attribute conversion", "critical chance increase", "critical damage increase",
  "pve value", "unconditional", "unconditional (pve value)",
  "permanent conversion (pve value)",
]);

// which trait effects matter per optimizer mode: the builder only lists
// entries carrying at least one relevant effect
const MODE_EFFECTS = {
  crit: new Set(["power", "precision", "ferocity", "vitality", "crit_chance",
                 "crit_damage_pct", "all_stats_flat", "all_stats_pct", "power_per_might"]),
  boon: new Set(["concentration", "healing", "boon_duration_pct", "outgoing_heal_pct",
                 "all_stats_flat", "all_stats_pct"]),
};

const ATTRIBUTE_LABELS = { healing: "healing power" };

function effectText(row) {
  const meaningful = row.note && !REDUNDANT_NOTES.has(row.note.toLowerCase());
  const condition = meaningful ? ` — ${row.note}` : "";
  if (row.source) {  // attribute conversion, e.g. "+6.5% of power as healing power"
    const source = ATTRIBUTE_LABELS[row.source] || row.source;
    const target = ATTRIBUTE_LABELS[row.effect] || row.effect;
    return `+${Math.round(row.value * 1000) / 10}% of ${source} as ${target}${condition}`;
  }
  switch (row.effect) {
    case "crit_chance":      return `+${row.value}% critical chance${condition}`;
    case "crit_damage_pct":  return `+${row.value}% critical damage${condition}`;
    case "all_stats_pct":    return `+${row.value}% all attributes${condition}`;
    case "all_stats_flat":   return `+${row.value} all attributes${condition}`;
    case "power_per_might":  return `+${row.value} power per might stack${condition}`;
    case "healing":          return `+${row.value} healing power${condition}`;
    case "boon_duration_pct": return `+${row.value}% boon duration${condition}`;
    case "outgoing_heal_pct": return `+${row.value}% outgoing healing${condition}`;
    default:
      return `+${row.value} ${row.effect}${condition}`;
  }
}

async function loadBuilder() {
  el("result").classList.add("hidden");
  el("calc-error").classList.add("hidden");

  const [traits, specs] = await Promise.all([
    fetch(`/traits?profession=${encodeURIComponent(state.profession)}`).then(r => r.json()),
    fetch(`/specializations?profession=${encodeURIComponent(state.profession)}`).then(r => r.json()),
  ]);
  state.traitRows = traits;
  state.specRows = specs;
  renderTraitGroups();
}

function renderTraitGroups() {
  if (!state.traitRows) return;
  state.selectedTraits = new Set();
  state.conditionHints = [];
  const traits = state.traitRows;
  const specs = state.specRows;

  // core lines are always available; of the elite lines only the chosen one
  const coreSpecs = specs.filter(s => !s.elite).map(s => s.name);
  const allowed = new Set(coreSpecs);
  if (!state.spec.coreArt) allowed.add(state.spec.name);
  const rows = traits.filter(r => !r.specialization || allowed.has(r.specialization));

  // one entry per trait/skill id, with all its effect rows; the mode decides
  // which entries are listed (crit stats vs concentration/healing)
  const byId = new Map();
  for (const row of rows) {
    if (!byId.has(row.id)) {
      byId.set(row.id, { ...row, effects: [] });
    }
    byId.get(row.id).effects.push(row);
  }
  const relevant = MODE_EFFECTS[state.mode];
  const entries = [...byId.values()]
    .filter(e => e.effects.some(effect => relevant.has(effect.effect)));
  state.entries = byId;

  // sections: core lines first, the chosen elite spec last, then skills
  const sections = [...coreSpecs];
  if (!state.spec.coreArt) sections.push(state.spec.name);

  const container = el("trait-groups");
  container.innerHTML = "";
  const specByName = new Map(specs.map(s => [s.name, s]));

  // order like the in-game trait tree: tiers left to right, within a tier
  // the minor first, then the major choices top to bottom
  const byTraitTree = (a, b) =>
    (Number(a.tier) || 0) - (Number(b.tier) || 0)
    || (a.slot === "Minor" ? 0 : 1) - (b.slot === "Minor" ? 0 : 1)
    || (Number(a.position) || 0) - (Number(b.position) || 0);

  for (const section of sections) {
    const sectionEntries = entries
      .filter(e => e.kind === "trait" && e.specialization === section)
      .sort(byTraitTree);
    if (sectionEntries.length) {
      container.append(traitGroup(section, specByName.get(section)?.icon, sectionEntries));
    }
  }
  const SKILL_SLOT_ORDER = { Heal: 0, Utility: 1, Elite: 2 };
  const skills = entries.filter(e => e.kind === "skill")
    .sort((a, b) => (SKILL_SLOT_ORDER[a.slot] ?? 9) - (SKILL_SLOT_ORDER[b.slot] ?? 9)
                    || a.name.localeCompare(b.name));
  if (skills.length) {
    container.append(traitGroup("Skills", `/icons/tango_${state.profession}.png`, skills));
  }
  state.pendingIds = null;
  updateBuildWarnings();
  updateConditionHints();
}

// mirror the solver's gating (requires fury / might >= 10) in the trait list
function updateConditionHints() {
  const furyOn = el("opt-fury").checked;
  const might = Number(el("opt-might").value);
  for (const hint of state.conditionHints || []) {
    const unmet = [];
    if (hint.requiresSet.has("fury") && !furyOn) unmet.push("Fury");
    if (hint.requiresSet.has("might") && might < 10) unmet.push("≥10 might");
    if (unmet.length) {
      const scope = hint.gated === hint.total ? "Ineffective" : "Partly ineffective";
      hint.span.textContent = `⚠ ${scope} with current settings — needs ${unmet.join(" and ")}.`;
      hint.span.classList.remove("hidden");
    } else {
      hint.span.classList.add("hidden");
    }
  }
}

// in-game constraints the optimizer itself does not enforce: only one major
// trait per tier of a line, at most three trait lines per build, and one
// heal / three utility / one elite skill slot
const TIER_NAMES = { 1: "adept", 2: "master", 3: "grandmaster" };
const SKILL_SLOTS = { Heal: ["heal", 1], Utility: ["utility", 3], Elite: ["elite", 1] };

const joinNames = (names) =>
  names.length > 1
    ? `${names.slice(0, -1).join(", ")} and ${names.at(-1)}`
    : names[0];

function updateBuildWarnings() {
  const warnings = [];
  const majorsPerTier = new Map();
  const lines = new Set();
  const skillsPerSlot = new Map();

  for (const id of state.selectedTraits) {
    const entry = state.entries?.get(id);
    if (!entry) continue;
    if (entry.kind === "skill") {
      if (!skillsPerSlot.has(entry.slot)) skillsPerSlot.set(entry.slot, []);
      skillsPerSlot.get(entry.slot).push(entry.name);
      continue;
    }
    lines.add(entry.specialization);
    if (entry.slot === "Major" && entry.tier) {
      const key = `${entry.specialization}|${Number(entry.tier)}`;
      if (!majorsPerTier.has(key)) majorsPerTier.set(key, []);
      majorsPerTier.get(key).push(entry.name);
    }
  }

  for (const [key, names] of majorsPerTier) {
    if (names.length > 1) {
      const [spec, tier] = key.split("|");
      warnings.push(`${joinNames(names)} are competing ${spec} ${TIER_NAMES[tier] || ""} ` +
                    "choices — the game lets you slot only one of them.");
    }
  }
  if (lines.size > 3) {
    warnings.push(`Your traits span ${lines.size} trait lines ` +
                  `(${[...lines].join(", ")}) — a build holds only three.`);
  }
  for (const [slot, [label, limit]] of Object.entries(SKILL_SLOTS)) {
    const names = skillsPerSlot.get(slot) || [];
    if (names.length > limit) {
      warnings.push(`${joinNames(names)} are ${names.length} ${label} skills — ` +
                    `a build has only ${limit === 1 ? "one" : limit} ${label} slot${limit > 1 ? "s" : ""}.`);
    }
  }

  const box = el("build-warnings");
  box.innerHTML = "";
  for (const text of warnings) {
    const paragraph = document.createElement("p");
    paragraph.textContent = text;
    box.append(paragraph);
  }
  box.classList.toggle("hidden", warnings.length === 0);
}

// import a build template chat link: select profession, spec and known traits
async function loadChatlink() {
  const link = el("chatlink-input").value.trim();
  const errorBox = el("chatlink-error");
  if (!link) return;

  const response = await fetch(`/chatlink/decode?link=${encodeURIComponent(link)}`);
  const body = await response.json();
  if (!response.ok) {
    errorBox.textContent = body.error;
    errorBox.classList.remove("hidden");
    return;
  }
  errorBox.classList.add("hidden");

  state.pendingIds = new Set(body.selectable_ids);
  await selectProfession(body.profession);
  if (body.elite_spec) {
    const specs = await fetch(`/specializations?profession=${encodeURIComponent(body.profession)}`)
      .then(r => r.json());
    selectSpec(specs.find(s => s.name === body.elite_spec));
  } else {
    selectSpec({
      name: `Core ${body.profession}`,
      icon: `/icons/tango_${body.profession}.png`,
      coreArt: true,
    });
  }
}

el("chatlink-load").addEventListener("click", loadChatlink);
el("chatlink-input").addEventListener("keydown", (event) => {
  if (event.key === "Enter") loadChatlink();
});

function traitGroup(title, iconSrc, groupEntries) {
  const group = document.createElement("div");
  group.className = "trait-group";

  const header = document.createElement("div");
  header.className = "trait-group-header";
  if (iconSrc) {
    const icon = document.createElement("img");
    icon.src = iconSrc;
    icon.alt = "";
    header.append(icon);
  }
  const name = document.createElement("span");
  name.className = "name";
  name.textContent = title;
  header.append(name);
  group.append(header);

  for (const entry of groupEntries) {
    const unsolvable = entry.effects.some(e => e.effect === "all_stats_pct");

    const label = document.createElement("label");
    label.className = unsolvable ? "trait disabled" : "trait";

    const box = document.createElement("input");
    box.type = "checkbox";
    box.disabled = unsolvable;
    if (!unsolvable && state.pendingIds?.has(entry.id)) {
      box.checked = true;
      state.selectedTraits.add(entry.id);
    }
    box.addEventListener("change", () => {
      if (box.checked) state.selectedTraits.add(entry.id);
      else state.selectedTraits.delete(entry.id);
      updateBuildWarnings();
    });

    const icon = document.createElement("img");
    icon.src = `/icons/${entry.id}.png`;
    icon.alt = "";
    icon.loading = "lazy";

    const info = document.createElement("span");
    const nameLine = document.createElement("span");
    nameLine.className = "trait-name";
    nameLine.textContent = entry.name;
    const slotTag = document.createElement("span");
    slotTag.className = "slot-tag";
    slotTag.textContent = unsolvable ? "percentage bonus — cannot hit exactly 100%" : (entry.slot || "");
    nameLine.append(slotTag);
    const effects = document.createElement("span");
    effects.className = "trait-effects";
    effects.textContent = entry.effects.map(effectText).join(" · ");
    info.append(nameLine, effects);

    // live hint when fury/might settings deactivate (part of) this trait
    const requiresSet = new Set(entry.effects.map(e => e.requires).filter(Boolean));
    if (requiresSet.size) {
      const hint = document.createElement("span");
      hint.className = "trait-condition hidden";
      info.append(hint);
      state.conditionHints.push({
        span: hint,
        requiresSet,
        gated: entry.effects.filter(e => e.requires).length,
        total: entry.effects.length,
      });
    }

    label.append(box, icon, info);
    group.append(label);
  }
  return group;
}

// ---------- builder: gear ----------

const gear = { env: "3p", weapon: "2h", ascended: new Set() };

const ARMOR_TRINKET_SLOTS = [
  ["chest", "Chest"], ["legs", "Legs"], ["head", "Head"], ["shoulders", "Shoulders"],
  ["gloves", "Gloves"], ["boots", "Boots"], ["amulet", "Amulet"],
  ["ring1", "Ring 1"], ["ring2", "Ring 2"],
  ["accessory1", "Accessory 1"], ["accessory2", "Accessory 2"], ["back-item", "Back item"],
];

function weaponSlots() {
  return gear.weapon === "2h"
    ? [["twohanded", "Weapon"]]
    : [["onehanded1", "Weapon 1"], ["onehanded2", "Weapon 2"]];
}

function renderSlotGrid() {
  const grid = el("slot-grid");
  grid.innerHTML = "";
  for (const [key, name] of [...weaponSlots(), ...ARMOR_TRINKET_SLOTS]) {
    const chip = document.createElement("button");
    chip.type = "button";
    chip.className = gear.ascended.has(key) ? "slot-chip asc" : "slot-chip";
    chip.textContent = name;
    chip.title = "Click to toggle ascended / exotic";
    chip.addEventListener("click", () => {
      if (gear.ascended.has(key)) gear.ascended.delete(key);
      else gear.ascended.add(key);
      chip.classList.toggle("asc");
    });
    grid.append(chip);
  }
}

function setupSegmented(id, onChange) {
  const seg = el(id);
  seg.addEventListener("click", (event) => {
    const button = event.target.closest("button");
    if (!button) return;
    seg.querySelectorAll("button").forEach(b => b.classList.remove("active"));
    button.classList.add("active");
    onChange(button.dataset.value);
  });
}

setupSegmented("env-choice", value => { gear.env = value; });
setupSegmented("weapon-choice", value => {
  gear.weapon = value;
  ["twohanded", "onehanded1", "onehanded2"].forEach(key => gear.ascended.delete(key));
  renderSlotGrid();
});

// ---------- optimizer mode (crit vs boon duration) ----------

function setMode(mode) {
  state.mode = mode;
  const boon = mode === "boon";
  el("row-env").classList.toggle("hidden", boon);       // boon mode is 3-stat only
  el("fury-label").classList.toggle("hidden", boon);    // fury only affects crit
  el("pie-label").classList.toggle("hidden", boon);
  el("writs-label").classList.toggle("hidden", boon);   // no concentration writ exists
  el("herald-label").classList.toggle("hidden", !boon);
  el("utility-name").textContent = boon ? "Maintenance oils" : "Sharpening stones";
  el("utility-note").textContent = boon ? "(Magnanimous / Lucent / Toxic / Bountiful)" : "";
  el("stacking-note").textContent = boon
    ? "(Bounty/Life/Benevolence — kill stacks, lost on downstate)"
    : "(Perception/Bloodlust — lost on downstate)";
  el("single-sigil-note").textContent = boon
    ? "(the other slot is yours, e.g. a proc sigil — only one slot is optimized)"
    : "(the other slot is yours, e.g. Energy — only one slot is optimized)";
  el("reserve-relic-label").classList.toggle("hidden", !boon);
  el("row-ranking").classList.toggle("hidden", !boon);
  el("result").classList.add("hidden");
  el("calc-error").classList.add("hidden");
  if (boon) loadHealSkills();
  renderTraitGroups();
}

setupSegmented("mode-choice", setMode);

// ---------- boon mode: healing-profile slider (the K value) ----------
// slider position 0 and 100 are the analytical edges (rank purely by healing
// power resp. purely by outgoing healing %); positions in between pick a K
// for the index (K + healing power) x (1 + outgoing%). The interior spans
// exactly the K range of the profession's own healing skills (regeneration
// included), on a log scale because that range covers two orders of magnitude

let kBounds = { min: 100, max: 40000 };

async function loadHealSkills() {
  if (state.healSkillsFor === state.profession) return state.healSkills;
  state.healSkills = await fetch(
    `/heal-skills?profession=${encodeURIComponent(state.profession)}`).then(r => r.json());
  state.healSkillsFor = state.profession;
  const ks = state.healSkills.map(s => s.k);
  kBounds = { min: Math.min(...ks), max: Math.max(...ks) };
  updateKLabel();
  return state.healSkills;
}

function kFromSlider(position) {
  return Math.round(kBounds.min * Math.pow(kBounds.max / kBounds.min, (position - 1) / 98));
}

function sliderFromK(k) {
  const position = 1 + 98 * Math.log(k / kBounds.min) / Math.log(kBounds.max / kBounds.min);
  return Math.min(99, Math.max(1, Math.round(position)));
}

function currentRanking() {
  const position = Number(el("k-slider").value);
  if (position === 0) return { ranking: "healing" };
  if (position === 100) return { ranking: "outgoing" };
  return { ranking: "k", k: state.k || kFromSlider(position) };
}

function updateKLabel() {
  const { ranking, k } = currentRanking();
  el("k-label").textContent =
    ranking === "healing" ? "ranking by healing power"
    : ranking === "outgoing" ? "ranking by outgoing healing %"
    : `K = ${k.toLocaleString("en-US")}${state.kSkill ? ` (${state.kSkill})` : ""}`;
}

function reoptimizeIfShown() {
  if (!el("result").classList.contains("hidden")) optimize();
}

el("k-slider").addEventListener("input", () => {
  state.k = null;  // dragging leaves the picked skill
  state.kSkill = null;
  state.k = kFromSlider(Number(el("k-slider").value));
  updateKLabel();
});
el("k-slider").addEventListener("change", reoptimizeIfShown);

// the skill picker popup: every healing skill of the profession with its K
async function openSkillPopup() {
  const list = el("skill-list");
  list.innerHTML = "";
  const skills = [...await loadHealSkills()];
  skills.sort((a, b) => a.k - b.k);
  for (const skill of skills) {
    const row = document.createElement("button");
    row.type = "button";
    row.className = "skill-row";
    const name = document.createElement("span");
    name.className = "skill-name";
    name.textContent = skill.kind === "barrier" ? `${skill.skill} (barrier)` : skill.skill;
    const value = document.createElement("span");
    value.className = "skill-k";
    value.textContent = `K = ${skill.k.toLocaleString("en-US")}`;
    const formula = document.createElement("span");
    formula.className = "skill-formula";
    formula.textContent = `${skill.base} + ${skill.coefficient} × healing power`;
    row.append(name, value, formula);
    row.addEventListener("click", () => {
      state.k = skill.k;
      state.kSkill = skill.skill;
      el("k-slider").value = sliderFromK(skill.k);
      updateKLabel();
      el("skill-popup").classList.add("hidden");
      reoptimizeIfShown();
    });
    list.append(row);
  }
  el("skill-popup").classList.remove("hidden");
}

el("k-from-skill").addEventListener("click", openSkillPopup);
el("skill-popup-close").addEventListener("click", () => el("skill-popup").classList.add("hidden"));
el("skill-popup").addEventListener("click", (event) => {
  if (event.target === el("skill-popup")) el("skill-popup").classList.add("hidden");
});

el("all-asc").addEventListener("click", () => {
  [...weaponSlots(), ...ARMOR_TRINKET_SLOTS].forEach(([key]) => gear.ascended.add(key));
  renderSlotGrid();
});
el("all-exo").addEventListener("click", () => {
  gear.ascended.clear();
  renderSlotGrid();
});

el("opt-might").addEventListener("input", () => {
  el("might-value").textContent = el("opt-might").value;
  updateConditionHints();
});
el("opt-fury").addEventListener("change", updateConditionHints);

renderSlotGrid();

// ---------- builder: optimize ----------

const RUNE_NAMES = {
  scholar: "Scholar", dragonh: "Dragonhunter", gole: "Golemancer", deadeye: "Deadeye",
  eagle: "Eagle", infil: "Infiltration", ranger: "Ranger",
};
const FOOD_NAMES = {
  butternut: "Bowl of Butternut Squash Soup",
  truffle: "Plate of Truffle Steak",
  curry: "Bowl of Curry Butternut Squash Soup",
  omnomberry: "Omnomberry Pie (+70 precision, lifesteal on crit)",
  "no food": "none",
};
const SIGIL_NAMES = {
  accuracy: "Accuracy (+7% crit)",
  perception: "Perception (+250 precision at 25 stacks)",
  bloodlust: "Bloodlust (+250 power at 25 stacks)",
  impact: "Impact (+3%) — or Night, +10% at night",
  force: "Force (+5% damage)",
};
const SIGIL_SHORT = {
  accuracy: "Accuracy",
  perception: "Perception",
  bloodlust: "Bloodlust",
  impact: "Impact (or Night)",
  force: "Force",
};
const UTILITY_NAMES = {
  stones: "Superior Sharpening Stone",
  writ_accuracy: "Writ of Masterful Accuracy (+200 precision above 90% health)",
  writ_strength: "Writ of Masterful Strength (+200 power above 90% health)",
  none: "none",
};
const RELIC_NAMES = {
  mistburn: "Mistburn (+10% crit while at ≥10 might)",
  damage: "damage relic of your choice (Thief, Eagle, Fireworks — ~5% effective)",
};

// sigil pairs look like "force+accuracy"; single-sigil results carry one name
const sigilNames = (pair, map) =>
  pair.split("+").map(name => map[name] || capitalize(name)).join(" + ");

// mixed rune sets from the rescue pass look like "scholar(4)+eagle(2)"
function runeName(rune) {
  if (!rune.includes("(")) return RUNE_NAMES[rune] || capitalize(rune);
  return rune.split("+").map(part => {
    const match = part.match(/(\w+)\((\d)\)/);
    return `${match[2]}× ${RUNE_NAMES[match[1]] || capitalize(match[1])}`;
  }).join(" + ");
}

async function optimize() {
  const button = el("optimize");
  if (button.disabled) return;  // ignore double clicks while a request runs

  const params = new URLSearchParams();
  params.set("mode", state.mode);
  params.set("profession", state.profession);
  for (const id of state.selectedTraits) params.append("traits[]", id);
  params.set("parameters", state.mode === "boon" ? "3p" : gear.env);
  params.set("handedness", gear.weapon);
  for (const key of gear.ascended) params.append("armor[]", key);
  params.set("fury", el("opt-fury").checked);
  params.set("might", el("opt-might").value);
  params.set("food", el("opt-food").checked);
  params.set("utility", el("opt-utility").checked);
  params.set("stacking", el("opt-stacking").checked);
  params.set("writs", el("opt-writs").checked);
  params.set("single_sigil", el("opt-single-sigil").checked);
  params.set("pie", el("opt-pie").checked);
  params.set("herald", el("opt-herald").checked);
  params.set("relic_reserved", el("opt-reserve-relic").checked);
  if (state.mode === "boon") {
    const { ranking, k } = currentRanking();
    params.set("ranking", ranking);
    if (k) params.set("k", k);
  }

  const errorBox = el("calc-error");
  const resultBox = el("result");
  const idleLabel = button.textContent;
  button.disabled = true;
  button.classList.add("busy");
  button.textContent = "Optimizing…";

  try {
    const response = await fetch(`/calculate?${params}`);
    if (!response.ok) {
      const body = await response.json().catch(() => ({}));
      errorBox.textContent = body.error || `The optimizer failed (${response.status}).`;
      errorBox.classList.remove("hidden");
      resultBox.classList.add("hidden");
      return;
    }
    errorBox.classList.add("hidden");
    const data = await response.json();
    if (state.mode === "boon") renderBoonResult(data);
    else renderResult(data, gear.env, el("opt-single-sigil").checked);
  } catch {
    errorBox.textContent = "Could not reach the optimizer — check your connection and try again.";
    errorBox.classList.remove("hidden");
    resultBox.classList.add("hidden");
  } finally {
    button.disabled = false;
    button.classList.remove("busy");
    button.textContent = idleLabel;
  }
}

// which stat combination a precision-major / precision-minor piece is;
// jewels come in the same prefixes, named after their gem
const PREFIX_NAMES = {
  "3p": {
    major: "Assassin's", minor: "Berserker's", none: "Valkyrie",
    jewels: { major: "Assassin's (Opal Jewel)", minor: "Berserker's (Ruby Jewel)",
              none: "Valkyrie (Beryl Jewel)" },
  },
  "4p": {
    major: "Marauder", minor: "Dragon's",
    jewels: { major: "Marauder (Ebony Jewel)", minor: "Dragon's (Jade Jewel)" },
  },
};

function equipmentLine(group, names) {
  const noPrecision = group.no_precision || 0;
  const minor = group.pieces - group.precision_major - noPrecision;
  const parts = [];
  if (group.precision_major > 0) parts.push(`${group.precision_major}× ${names.major}`);
  if (minor > 0) parts.push(`${minor}× ${names.minor}`);
  if (noPrecision > 0) parts.push(`${noPrecision}× ${names.none}`);
  if (group.pieces === 1) return parts[0].replace("1× ", "");
  return parts.join(", ");
}

function renderResult(data, env, singleSigil) {
  const resultBox = el("result");
  resultBox.innerHTML = "";

  const backup = data.stable_fallback;
  const body = document.createElement("div");

  if (backup) {
    // why the backup exists, derived from what the best build relies on
    const reasons = [];
    if (data.sigil.split("+").some(s => ["perception", "bloodlust"].includes(s))) {
      reasons.push("stacking sigil stacks vanish on downstate");
    }
    if (data.utility === "writ_accuracy") reasons.push("the accuracy writ needs >90% health");

    const tabs = document.createElement("div");
    tabs.className = "result-tabs";
    const bestTab = document.createElement("button");
    bestTab.type = "button";
    bestTab.textContent = "Best build";
    const backupTab = document.createElement("button");
    backupTab.type = "button";
    const delta = ((backup.effective_power / data.effective_power - 1) * 100).toFixed(1);
    backupTab.textContent = `Stable backup (${delta}%)`;

    const activate = (tab, r, backupInfo) => {
      for (const button of tabs.children) button.classList.toggle("active", button === tab);
      body.innerHTML = "";
      renderSolutionBody(body, r, env, singleSigil, backupInfo);
    };
    bestTab.addEventListener("click", () => activate(bestTab, data, null));
    backupTab.addEventListener("click", () => activate(backupTab, backup, { reasons }));
    tabs.append(bestTab, backupTab);
    resultBox.append(tabs, body);
    activate(bestTab, data, null);
  } else {
    resultBox.append(body);
    renderSolutionBody(body, data, env, singleSigil, null);
  }

  resultBox.append(chatlinkButton());
  resultBox.classList.remove("hidden");
}

// the trait selection is the same for every result variant, so one link suffices
function chatlinkButton() {
  const copyButton = document.createElement("button");
  copyButton.type = "button";
  copyButton.className = "ghost-button copy-link";
  copyButton.textContent = "Copy build template chat link";
  copyButton.addEventListener("click", async () => {
    const params = new URLSearchParams({ profession: state.profession });
    for (const id of state.selectedTraits) params.append("traits[]", id);
    const response = await fetch(`/chatlink/encode?${params}`);
    const responseBody = await response.json();
    if (!response.ok) {
      copyButton.textContent = responseBody.error;
      return;
    }
    await navigator.clipboard.writeText(responseBody.link);
    copyButton.textContent = `Copied: ${responseBody.link}`;
  });
  return copyButton;
}

function renderSolutionBody(container, r, env, singleSigil, backupInfo) {
  if (backupInfo) {
    const intro = document.createElement("p");
    intro.className = "warning";
    intro.textContent = `This build keeps the crit cap when the best build would lose it ` +
      `(${backupInfo.reasons.join("; ")}).`;
    container.append(intro);
  }

  const ep = document.createElement("div");
  ep.className = "ep";
  const epValue = document.createElement("span");
  epValue.className = "value";
  epValue.textContent = Math.round(r.effective_power).toLocaleString("en-US");
  const epCaption = document.createElement("span");
  epCaption.className = "caption";
  epCaption.textContent = "effective power at 100% crit";
  ep.append(epValue, epCaption);

  const list = document.createElement("dl");
  const facts = [
    ["Rune", runeName(r.rune)],
    ["Food", FOOD_NAMES[r.food] || capitalize(r.food)],
    ["Utility", UTILITY_NAMES[r.utility] || capitalize(String(r.utility))],
    ["Relic", RELIC_NAMES[r.relic] || capitalize(String(r.relic))],
    [singleSigil ? "Sigil (other slot reserved)" : "Sigils",
     sigilNames(String(r.sigil), SIGIL_NAMES)],
    ["Precision infusions", `${r.prec_infusions} of ${r.total_infusions} (rest power)`],
  ];
  for (const [term, value] of facts) {
    const dt = document.createElement("dt");
    dt.textContent = term;
    const dd = document.createElement("dd");
    dd.textContent = value;
    list.append(dt, dd);
  }

  const stats = document.createElement("div");
  stats.className = "stats";
  for (const [name, value] of [
    ["Power", r.power], ["Precision", r.precision + r.chance],
    ["Ferocity", r.ferocity], ["Vitality", r.vitality],
  ]) {
    const cell = document.createElement("div");
    const statValue = document.createElement("span");
    statValue.className = "stat-value";
    statValue.textContent = Math.round(value).toLocaleString("en-US");
    const statName = document.createElement("span");
    statName.className = "stat-name";
    statName.textContent = name;
    cell.append(statValue, statName);
    stats.append(cell);
  }

  container.append(ep, list, stats);

  const heading = document.createElement("h3");
  heading.className = "equipment-heading";
  heading.textContent = "Equipment";
  const equipmentList = document.createElement("dl");
  const addEquipmentRow = (slot, text) => {
    const dt = document.createElement("dt");
    dt.textContent = slot;
    const dd = document.createElement("dd");
    dd.textContent = text;
    equipmentList.append(dt, dd);
  };
  addEquipmentRow("Sigils", singleSigil
    ? `${sigilNames(String(r.sigil), SIGIL_SHORT)} (second slot reserved)`
    : sigilNames(String(r.sigil), SIGIL_SHORT));
  addEquipmentRow("Relic", r.relic === "mistburn" ? "Mistburn" : "Thief / Eagle / Fireworks (free choice)");
  addEquipmentRow("Jade bot core", "Tier 10 (+235 vitality, already counted)");
  if (r.equipment) {
    for (const group of r.equipment) {
      const names = group.slot.startsWith("Jewels") ? PREFIX_NAMES[env].jewels : PREFIX_NAMES[env];
      addEquipmentRow(group.slot, equipmentLine(group, names));
    }
  }
  container.append(heading, equipmentList);

  // severity order: the red cap-miss first, aureus advisories after
  if (r.absolute_overshoot > 0) {
    const overcapped = r.armor_precision < r.armor_floor;
    const warning = document.createElement("p");
    warning.className = "warning cap-miss";
    warning.textContent = overcapped
      ? (env === "4p"
          ? `Crit chance exceeds the cap and 4-stat gear cannot shed precision (every prefix ` +
            `carries it) — switch to the 3-stat environment (Valkyrie pieces) or deselect ` +
            `a crit source. Overshoot: ${Math.round(r.absolute_overshoot)} precision.`
          : `Crit chance exceeds 100% even with zero precision from gear — deselect a crit ` +
            `source (trait, sigil, writ or relic). ` +
            `Overshoot: ${Math.round(r.absolute_overshoot)} precision.`)
      : `No gear split hits the crit cap exactly here — closest overshoot: ` +
        `${Math.round(r.absolute_overshoot)} precision.`;
    container.append(warning);
  }

  if (r.relic === "mistburn") {
    const note = document.createElement("p");
    note.className = "warning";
    note.textContent = "Mistburn's +10% crit is a passive while at ≥10 might — keep might up. " +
      "No backup build needed: swapping to a damage relic never breaks the cap.";
    container.append(note);
  }
}

// ---------- boon-duration mode: result rendering ----------

const BOON_RUNE_NAMES = {
  water: "Water", monk: "Monk", altruism: "Altruism", leadership: "Leadership",
  radiance: "Radiance", sanctuary: "Sanctuary", fireworks: "Fireworks", pack: "Pack",
};
const BOON_FOOD_NAMES = {
  mint_brulee: "Mint Creme Brulee (+100 concentration, +70 healing, +10% outgoing)",
  mint_salad: "Bowl of Fruit Salad with Mint Garnish (+100 healing, +70 concentration, +10% outgoing)",
  "no food": "none",
};
const BOON_SIGIL_NAMES = {
  concentration: "Concentration (+10% boon duration)",
  bounty: "Bounty (+225 concentration at 25 kill stacks)",
  life: "Life (+250 healing at 25 kill stacks)",
  benevolence: "Benevolence (+12.5% outgoing healing at 25 kill stacks)",
  transference: "Transference (+10% outgoing healing)",
  free: "utility sigil of your choice (Water, Renewal, …)",
};
const BOON_SIGIL_SHORT = {
  concentration: "Concentration", bounty: "Bounty", life: "Life",
  benevolence: "Benevolence", transference: "Transference",
  free: "utility sigil of your choice",
};
const BOON_UTILITY_NAMES = {
  magnanimous: "Magnanimous Maintenance Oil (concentration = 3% of vitality + toughness)",
  toxic: "Toxic Maintenance Oil (concentration = 3% of power)",
  lucent: "Potent Lucent Oil (concentration = 3% of power + 3% of precision)",
  bountiful: "Bountiful Maintenance Oil (outgoing healing from healing power + concentration)",
  none: "none",
};
const BOON_RELIC_NAMES = {
  herald: "Herald (+250 concentration on boon application, max stacks)",
  monk: "Monk (+10% outgoing healing at 10 boon-application stacks)",
  castora: "Castora (+25% outgoing to allies below 50% health — effective 12.5%)",
  reserved: "your reserved relic (e.g. Karakosa)",
  utility: "none earned the slot — free choice (Karakosa, Founding, …)",
};
const BOON_RELIC_SHORT = {
  herald: "Herald", monk: "Monk", castora: "Castora",
  reserved: "(your reserved relic)", utility: "free choice",
};

function renderBoonResult(data) {
  const resultBox = el("result");
  resultBox.innerHTML = "";
  const singleSigil = el("opt-single-sigil").checked;

  const note = document.createElement("p");
  note.className = "rank-note";
  note.textContent =
    data.ranking === "healing" ? "ranked by healing power"
    : data.ranking === "outgoing" ? "ranked by outgoing healing %"
    : `ranked by effective healing at K = ${Math.round(data.k).toLocaleString("en-US")}`;
  resultBox.append(note);

  const best = data.best;
  const backup = data.stable_fallback;
  if (!backup) {
    const body = document.createElement("div");
    renderBoonBody(body, best, singleSigil, null);
    resultBox.append(body);
  } else {
    // the backup only guards against kill-stack sigils; the Herald relic
    // recovers within seconds and has its own checkbox instead
    const reasons = ["kill stacks vanish on downstate"];
    const metric = r => data.ranking === "k"
      ? (data.k + r.healing) * (1 + r.outgoing / 100)
      : r[data.ranking];
    const tabs = document.createElement("div");
    tabs.className = "result-tabs";
    const inner = document.createElement("div");
    const bestTab = document.createElement("button");
    bestTab.type = "button";
    bestTab.textContent = "Best build";
    const backupTab = document.createElement("button");
    backupTab.type = "button";
    const delta = ((metric(backup) / metric(best) - 1) * 100).toFixed(1);
    backupTab.textContent = `Stable backup (${delta}%)`;
    const activate = (tab, r, backupInfo) => {
      for (const button of tabs.children) button.classList.toggle("active", button === tab);
      inner.innerHTML = "";
      renderBoonBody(inner, r, singleSigil, backupInfo);
    };
    bestTab.addEventListener("click", () => activate(bestTab, best, null));
    backupTab.addEventListener("click", () => activate(backupTab, backup, { reasons }));
    tabs.append(bestTab, backupTab);
    resultBox.append(tabs, inner);
    activate(bestTab, best, null);
  }

  resultBox.append(chatlinkButton());
  resultBox.classList.remove("hidden");
}

function renderBoonBody(container, r, singleSigil, backupInfo) {
  if (backupInfo) {
    const intro = document.createElement("p");
    intro.className = "warning";
    intro.textContent = `This build keeps 100% boon duration when the best build would lose it ` +
      `(${backupInfo.reasons.join("; ")}).`;
    container.append(intro);
  }

  const ep = document.createElement("div");
  ep.className = "ep";
  const epValue = document.createElement("span");
  epValue.className = "value";
  epValue.textContent = Math.round(r.healing).toLocaleString("en-US");
  const epCaption = document.createElement("span");
  epCaption.className = "caption";
  epCaption.textContent = "healing power at 100% boon duration";
  ep.append(epValue, epCaption);

  const list = document.createElement("dl");
  const facts = [
    ["Rune", BOON_RUNE_NAMES[r.rune] || capitalize(r.rune)],
    ["Food", BOON_FOOD_NAMES[r.food] || capitalize(r.food)],
    ["Utility", BOON_UTILITY_NAMES[r.utility] || capitalize(String(r.utility))],
    ["Relic", BOON_RELIC_NAMES[r.relic] || capitalize(String(r.relic))],
    [singleSigil ? "Sigil (other slot reserved)" : "Sigils",
     sigilNames(String(r.sigil), BOON_SIGIL_NAMES)],
    ["Concentration infusions", `${r.conc_infusions} of ${r.total_infusions} (rest healing)`],
    ["Outgoing healing", `+${r.outgoing.toFixed(1)}% in total (stacks additively)`],
  ];
  for (const [term, value] of facts) {
    const dt = document.createElement("dt");
    dt.textContent = term;
    const dd = document.createElement("dd");
    dd.textContent = value;
    list.append(dt, dd);
  }

  const stats = document.createElement("div");
  stats.className = "stats";
  for (const [name, value] of [
    ["Healing Power", r.healing], ["Concentration", 1500 + r.conc_delta],
    ["Vitality", r.vitality], ["Power", r.power],
  ]) {
    const cell = document.createElement("div");
    const statValue = document.createElement("span");
    statValue.className = "stat-value";
    statValue.textContent = Math.round(value).toLocaleString("en-US");
    const statName = document.createElement("span");
    statName.className = "stat-name";
    statName.textContent = name;
    cell.append(statValue, statName);
    stats.append(cell);
  }

  container.append(ep, list, stats);

  const heading = document.createElement("h3");
  heading.className = "equipment-heading";
  heading.textContent = "Equipment";
  const equipmentList = document.createElement("dl");
  const addEquipmentRow = (slot, text) => {
    const dt = document.createElement("dt");
    dt.textContent = slot;
    const dd = document.createElement("dd");
    dd.textContent = text;
    equipmentList.append(dt, dd);
  };
  addEquipmentRow("Sigils", singleSigil
    ? `${sigilNames(String(r.sigil), BOON_SIGIL_SHORT)} (second slot reserved)`
    : sigilNames(String(r.sigil), BOON_SIGIL_SHORT));
  addEquipmentRow("Relic", BOON_RELIC_SHORT[r.relic] || capitalize(String(r.relic)));
  addEquipmentRow("Jade bot core", "Tier 10 (+235 vitality, already counted)");
  for (const group of r.equipment) {
    const upgrades = group.slot.startsWith("Upgrades");
    const names = upgrades ? ["Platinum Doubloon", "Crest of the Magi"] : ["Harrier's", "Magi's"];
    const parts = [];
    if (group.harrier > 0) parts.push(`${group.harrier}× ${names[0]}`);
    if (group.magi > 0) parts.push(`${group.magi}× ${names[1]}`);
    const text = group.pieces === 1 && parts.length === 1
      ? parts[0].replace("1× ", "") : parts.join(", ");
    addEquipmentRow(group.slot, text);
  }
  container.append(heading, equipmentList);

  // severity order: the red cap-miss first, aureus advisories after
  if (!r.exact) {
    const missPct = (Math.abs(r.conc_delta) / 15).toFixed(2);
    const warning = document.createElement("p");
    warning.className = "warning cap-miss";
    warning.textContent = r.overcapped
      ? `Boon duration exceeds 100% even with full Magi's gear — deselect a concentration ` +
        `source (trait, rune, sigil, food). Overshoot: ${Math.round(r.conc_delta)} ` +
        `concentration (${missPct}%).`
      : (r.conc_delta > 0
          ? `No gear split lands exactly on 100% boon duration here — closest overshoot: ` +
            `${Math.round(r.conc_delta)} concentration (${missPct}%).`
          : `100% boon duration is out of reach: ${Math.round(-r.conc_delta)} concentration ` +
            `missing (${missPct}% boon duration). Allow more sources (food, oils, stacking ` +
            `sigils, Herald relic) or use more ascended pieces.`);
    container.append(warning);
  }

  if (r.rune === "leadership") {
    const note = document.createElement("p");
    note.className = "warning";
    note.textContent = "Rune of Leadership carries +36 toughness — negligible next to a " +
      "tank's, but keep it in mind for your group's aggro setup.";
    container.append(note);
  }
  const RELIC_NOTES = {
    herald: "Herald relic: the +250 concentration assumes 10 stacks — stacks last 3s each " +
      "and rebuild within seconds of boon pulsing. Untick its checkbox to remove it " +
      "from the candidate pool.",
    monk: "Monk relic: the +10% outgoing healing assumes 10 stacks — like Herald, stacks " +
      "last 3s each and rebuild within seconds of boon pulsing.",
    castora: "Castora relic: +25% outgoing healing only while the healed ally is below 50% " +
      "health — modeled at an effective 12.5%, arguably more since heals chase low allies.",
  };
  if (RELIC_NOTES[r.relic]) {
    const note = document.createElement("p");
    note.className = "warning";
    note.textContent = RELIC_NOTES[r.relic];
    container.append(note);
  }
}

el("optimize").addEventListener("click", optimize);

renderProfessionGrid();

// deep links: /?profession=Elementalist opens its spec picker,
// /?profession=Elementalist&spec=Weaver (or spec=core) opens the builder
(async () => {
  const query = new URLSearchParams(location.search);
  const preProfession = query.get("profession");
  if (!preProfession) return;
  const match = PROFESSIONS.find(p => p.name.toLowerCase() === preProfession.toLowerCase());
  if (!match) return;
  await selectProfession(match.name);

  const preSpec = query.get("spec");
  if (!preSpec) return;
  if (preSpec.toLowerCase() === "core") {
    selectSpec({ name: `Core ${match.name}`, icon: `/icons/tango_${match.name}.png`, coreArt: true });
    return;
  }
  const specs = await fetch(`/specializations?profession=${encodeURIComponent(match.name)}`)
    .then(r => r.json());
  const spec = specs.find(s => s.elite && s.name.toLowerCase() === preSpec.toLowerCase());
  if (spec) selectSpec(spec);
})();
