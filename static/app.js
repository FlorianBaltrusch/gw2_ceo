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

// the uncropped paintings; same filenames but lowercase extension
const professionOriginal = (profession) =>
  `/profession-images/originals/${PROFESSIONS.find(p => p.name === profession).img.replace(".PNG", ".png")}`;

const state = { profession: null, spec: null };

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
    background: professionOriginal(profession),
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
  overlay.classList.add("closing");
  const hide = () => overlay.classList.add("hidden");
  overlay.addEventListener("animationend", hide, { once: true });
  setTimeout(hide, 350);  // fallback: reduced motion / browsers that skip the animation

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

function effectText(row) {
  const condition = row.note ? ` — ${row.note}` : "";
  switch (row.effect) {
    case "crit_chance":     return `+${row.value}% critical chance${condition}`;
    case "crit_damage_pct": return `+${row.value}% critical damage${condition}`;
    case "all_stats_pct":   return `+${row.value}% all attributes${condition}`;
    case "all_stats_flat":  return `+${row.value} all attributes${condition}`;
    case "power_per_might": return `+${row.value} power per might stack${condition}`;
    default:
      if (row.source) {
        return `+${Math.round(row.value * 100)}% of ${row.source} as ${row.effect}${condition}`;
      }
      return `+${row.value} ${row.effect}${condition}`;
  }
}

async function loadBuilder() {
  state.selectedTraits = new Set();
  el("result").classList.add("hidden");
  el("calc-error").classList.add("hidden");

  const [traits, specs] = await Promise.all([
    fetch(`/traits?profession=${encodeURIComponent(state.profession)}`).then(r => r.json()),
    fetch(`/specializations?profession=${encodeURIComponent(state.profession)}`).then(r => r.json()),
  ]);

  // core lines are always available; of the elite lines only the chosen one
  const coreSpecs = specs.filter(s => !s.elite).map(s => s.name);
  const allowed = new Set(coreSpecs);
  if (!state.spec.coreArt) allowed.add(state.spec.name);
  const rows = traits.filter(r => !r.specialization || allowed.has(r.specialization));

  // one entry per trait/skill id, with all its effect rows
  const byId = new Map();
  for (const row of rows) {
    if (!byId.has(row.id)) {
      byId.set(row.id, { ...row, effects: [] });
    }
    byId.get(row.id).effects.push(row);
  }
  const entries = [...byId.values()];

  // sections: chosen elite spec first, then core lines, then skills
  const sections = [];
  if (!state.spec.coreArt) sections.push(state.spec.name);
  sections.push(...coreSpecs);

  const container = el("trait-groups");
  container.innerHTML = "";
  const specByName = new Map(specs.map(s => [s.name, s]));

  for (const section of sections) {
    const sectionEntries = entries.filter(e => e.kind === "trait" && e.specialization === section);
    if (sectionEntries.length) {
      container.append(traitGroup(section, specByName.get(section)?.icon, sectionEntries));
    }
  }
  const skills = entries.filter(e => e.kind === "skill");
  if (skills.length) {
    container.append(traitGroup("Skills", `/icons/tango_${state.profession}.png`, skills));
  }
  state.pendingIds = null;
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
});

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
  "no food": "none",
};

async function optimize() {
  const params = new URLSearchParams();
  params.set("profession", state.profession);
  for (const id of state.selectedTraits) params.append("traits[]", id);
  params.set("parameters", gear.env);
  params.set("handedness", gear.weapon);
  for (const key of gear.ascended) params.append("armor[]", key);
  params.set("fury", el("opt-fury").checked);
  params.set("might", el("opt-might").value);
  params.set("food", el("opt-food").checked);
  params.set("utility", el("opt-utility").checked);

  const response = await fetch(`/calculate?${params}`);
  const errorBox = el("calc-error");
  const resultBox = el("result");

  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    errorBox.textContent = body.error || `The optimizer failed (${response.status}).`;
    errorBox.classList.remove("hidden");
    resultBox.classList.add("hidden");
    return;
  }
  errorBox.classList.add("hidden");
  renderResult(await response.json(), gear.env);
}

// which stat combination a precision-major / precision-minor piece is
const PREFIX_NAMES = {
  "3p": { major: "Assassin's", minor: "Berserker's" },
  "4p": { major: "Marauder", minor: "Dragon's" },
  jewels: { major: "precision", minor: "power" },
};

function equipmentLine(group, names) {
  const parts = [];
  if (group.precision_major > 0) parts.push(`${group.precision_major}× ${names.major}`);
  const minor = group.pieces - group.precision_major;
  if (minor > 0) parts.push(`${minor}× ${names.minor}`);
  if (group.pieces === 1) return group.precision_major ? names.major : names.minor;
  return parts.join(", ");
}

function renderResult(r, env) {
  const resultBox = el("result");
  resultBox.innerHTML = "";

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
    ["Rune", RUNE_NAMES[r.rune] || capitalize(r.rune)],
    ["Food", FOOD_NAMES[r.food] || capitalize(r.food)],
    ["Sigil of Accuracy", r.sigil ? "yes" : "no"],
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

  resultBox.append(ep, list, stats);

  if (r.equipment) {
    const heading = document.createElement("h3");
    heading.className = "equipment-heading";
    heading.textContent = "Equipment";
    const equipmentList = document.createElement("dl");
    for (const group of r.equipment) {
      const names = group.slot.startsWith("Jewels") ? PREFIX_NAMES.jewels : PREFIX_NAMES[env];
      const dt = document.createElement("dt");
      dt.textContent = group.slot;
      const dd = document.createElement("dd");
      dd.textContent = equipmentLine(group, names);
      equipmentList.append(dt, dd);
    }
    resultBox.append(heading, equipmentList);
  }

  if (r.absolute_overshoot > 0) {
    const warning = document.createElement("p");
    warning.className = "warning";
    warning.textContent = `No gear split hits the crit cap exactly here — closest overshoot: ${Math.round(r.absolute_overshoot)} precision.`;
    resultBox.append(warning);
  }

  const copyButton = document.createElement("button");
  copyButton.type = "button";
  copyButton.className = "ghost-button copy-link";
  copyButton.textContent = "Copy build template chat link";
  copyButton.addEventListener("click", async () => {
    const params = new URLSearchParams({ profession: state.profession });
    for (const id of state.selectedTraits) params.append("traits[]", id);
    const response = await fetch(`/chatlink/encode?${params}`);
    const body = await response.json();
    if (!response.ok) {
      copyButton.textContent = body.error;
      return;
    }
    await navigator.clipboard.writeText(body.link);
    copyButton.textContent = `Copied: ${body.link}`;
  });
  resultBox.append(copyButton);

  resultBox.classList.remove("hidden");
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
