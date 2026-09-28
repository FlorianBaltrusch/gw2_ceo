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

// what the builder panel currently shows - survives navigating away, so
// browser back/forward can return to it without wiping the trait selection
const loaded = { profession: null, spec: null };

const el = (id) => document.getElementById(id);

// the chosen profession recolors the site (theme.css carries one palette
// per profession, keyed by this attribute); no profession = the default
function applyTheme(profession) {
  if (profession) document.documentElement.dataset.profession = profession;
  else delete document.documentElement.dataset.profession;
}

// ---------- URL navigation ----------
// every view has a URL - /, ?profession=X, ?profession=X&spec=Y (or spec=core,
// plus &mode=boon/power off the default) - so the browser's back/forward
// buttons walk the same steps as the in-page ones

function urlForState() {
  const params = new URLSearchParams();
  if (state.profession) {
    params.set("profession", state.profession);
    if (state.spec) {
      params.set("spec", state.spec.coreArt ? "core" : state.spec.name);
      params.set("mode", state.mode);  // explicit for all three, consistently
    }
  }
  const query = params.toString();
  return location.pathname + (query ? `?${query}` : "");
}

function syncUrl(mode) {  // "push" (new history entry) or "replace"
  const url = urlForState();
  if (url !== location.pathname + location.search) {
    history[`${mode}State`](null, "", url);
  }
}

function showOverlay(step) {  // "professions" or "specs"
  const overlay = el("overlay");
  overlay.classList.remove("hidden", "closing");
  el("profession-picker").classList.toggle("hidden", step !== "professions");
  el("spec-picker").classList.toggle("hidden", step !== "specs");
  el("topbar").classList.add("hidden");
  el("main").classList.add("hidden");
}

function showBuilder() {  // instant variant of finishSelection for history jumps
  const overlay = el("overlay");
  overlay.classList.add("hidden");
  overlay.classList.remove("closing");
  el("topbar").classList.remove("hidden");
  el("main").classList.remove("hidden");
}

// render whatever view the current URL names (initial load and back/forward)
async function applyLocation() {
  const query = new URLSearchParams(location.search);
  const professionParam = query.get("profession") || "";
  const match = PROFESSIONS.find(p => p.name.toLowerCase() === professionParam.toLowerCase());

  if (!match) {
    state.profession = null;
    state.spec = null;
    applyTheme(null);
    showOverlay("professions");
    return;
  }

  const specParam = query.get("spec");
  if (!specParam) {
    await selectProfession(match.name);
    return;
  }

  const modeParam = (query.get("mode") || "crit").toLowerCase();
  const mode = ["crit", "boon", "power"].includes(modeParam) ? modeParam : "crit";

  // straight to the builder; when it already shows exactly this profession
  // and spec, only the view switches and the trait selection is kept
  const wantCore = specParam.toLowerCase() === "core";
  const sameBuilder = loaded.profession === match.name && loaded.spec
    && (wantCore ? loaded.spec.coreArt
                 : loaded.spec.name.toLowerCase() === specParam.toLowerCase());
  if (sameBuilder) {
    state.profession = loaded.profession;
    state.spec = loaded.spec;
    showBuilder();
    if (mode !== state.mode) setMode(mode);
    return;
  }

  if (mode !== state.mode) setMode(mode);  // before the builder renders
  const fromLink = query.has("traits");
  if (fromLink) restoreOptimizerLink(query, mode);
  const specs = await selectProfession(match.name);
  let ready = null;
  if (wantCore) {
    ready = selectSpec({ name: `Core ${match.name}`, icon: `/icons/tango_${match.name}.png`, coreArt: true });
  } else {
    const spec = specs.find(s => s.elite && s.name.toLowerCase() === specParam.toLowerCase());
    if (spec) ready = selectSpec(spec);
    // unknown spec name: stay on the spec picker selectProfession opened
  }
  if (fromLink && ready) {
    await ready;
    if (mode === "boon" && query.has("kpos")) {
      await loadHealSkills();  // the slider's K scale comes from the class's skills
      el("k-slider").value = Math.max(0, Math.min(100, Number(query.get("kpos")) || 0));
      el("k-slider").dispatchEvent(new Event("input"));
    }
    optimize();
  }
}

window.addEventListener("popstate", () => { applyLocation(); });

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
    tile.addEventListener("click", async () => {
      await selectProfession(prof.name);
      syncUrl("push");
    });
    grid.append(tile);
  }
}

async function selectProfession(profession) {
  state.profession = profession;
  state.spec = null;
  applyTheme(profession);

  const response = await fetch(`/specializations?profession=${encodeURIComponent(profession)}`);
  const specs = await response.json();

  renderSpecGrid(profession, specs.filter(s => s.elite));
  showOverlay("specs");
  el("spec-question-prof").textContent = profession;
  window.scrollTo({ top: 0 });
  return specs;
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
  tile.addEventListener("click", () => {
    selectSpec(spec);
    syncUrl("push");
  });
  return tile;
}

function selectSpec(spec) {
  state.spec = spec;
  loaded.profession = state.profession;
  loaded.spec = spec;
  finishSelection();
  return loadBuilder();  // resolves once the trait panel is rendered
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
  state.profession = null;
  state.spec = null;
  applyTheme(null);
  showOverlay("professions");
  syncUrl("push");
}

el("back-to-professions").addEventListener("click", reopenSelection);
el("change-selection").addEventListener("click", reopenSelection);

// ---------- builder: traits ----------

const capitalize = (word) => word.charAt(0).toUpperCase() + word.slice(1);

// stat amounts in warnings: sub-point misses (from attribute conversions)
// must not round away to "0 precision"
const pointText = (x) => (Math.round(Math.abs(x) * 10) / 10).toLocaleString("en-US");

// fact labels that merely restate the stat add nothing next to "+200 power"
const REDUNDANT_NOTES = new Set([
  "power", "precision", "ferocity", "vitality", "concentration",
  "power increase", "precision increase", "ferocity increase", "vitality increase",
  "attribute conversion", "critical chance increase", "critical damage increase",
  "pve value", "unconditional", "unconditional (pve value)",
  "permanent conversion (pve value)",
]);

// which trait effects matter per optimizer mode: the builder only lists
// entries carrying at least one relevant effect (the free-crit power mode
// works with the same stats as the capped crit mode)
const CRIT_EFFECTS = new Set(["power", "precision", "ferocity", "vitality", "crit_chance",
                              "crit_damage_pct", "all_stats_flat", "all_stats_pct",
                              "power_per_might"]);
const MODE_EFFECTS = {
  crit: CRIT_EFFECTS,
  power: CRIT_EFFECTS,
  boon: new Set(["concentration", "healing", "boon_duration_pct", "outgoing_heal_pct",
                 "toughness", "all_stats_flat", "all_stats_pct"]),
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
  // a new profession/spec starts fresh - unless a permalink brought a selection
  state.traitMemory = state.pendingMemory || {};
  state.pendingMemory = null;

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
  // only Elementalist and Engineer keep stacks in a stowed weapon set
  el("stowed-label").classList.toggle(
    "hidden", !["Elementalist", "Engineer"].includes(state.profession));
  state.selectedTraits = new Set();
  state.conditionHints = [];
  state.traitStacks = new Map();    // stack-group id -> assumed stacks
  state.traitVariants = new Map();  // trait id -> chosen attunements
  state.stackControls = new Map();  // stack-group id -> its linked sliders
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

// which chip family a variant value belongs to, and each weapon's handedness
// (for the gear-panel consistency warning)
const VARIANT_KIND = {
  fire: "attunement", water: "attunement", air: "attunement", earth: "attunement",
  hare: "familiar", otter: "familiar", fox: "familiar", toad: "familiar",
  revealed: "revealed",
};
// radio kinds: exactly one option is active, picking another replaces it.
// Familiars: an Evoker always has one active, so all four are offered (also
// the ones without a modeled bonus) in the elements' order fire/water/air/
// earth = fox, otter, hare, toad (wiki: Familiar - Ignite/Splash/Zap/Calcify
// are the familiars' skills). Revealed: the state is either on or off; the
// "not revealed" option matches no data row and simply drops the bonus.
const RADIO_OPTIONS = {
  familiar: ["fox", "otter", "hare", "toad"],
  revealed: ["revealed", "not revealed"],
};
const RADIO_CAPTIONS = { familiar: "familiar:", revealed: "state:" };
// options that mean "the conditional part is off" on purpose - no warning
const EXPLICIT_OFF = new Set(["not revealed"]);
const TWO_HANDED = new Set(["greatsword", "staff", "hammer", "rifle", "longbow",
                            "shortbow", "spear"]);
const ONE_HANDED = new Set(["dagger", "sword", "axe", "mace", "pistol", "scepter",
                            "focus", "shield", "torch", "warhorn"]);

// mirror the solver's gating (requires fury / might >= 10 / weapon type) in
// the trait list
function updateConditionHints() {
  const furyOn = el("opt-fury").checked;
  const might = Number(el("opt-might").value);
  for (const hint of state.conditionHints || []) {
    const unmet = [];
    if (hint.requiresSet.has("fury") && !furyOn) unmet.push("Fury");
    if (hint.requiresSet.has("might") && might < 10) unmet.push("≥10 might");
    if (hint.requiresSet.has("weapon_1h") && gear.weapon !== "1h") {
      unmet.push("two one-handed weapons");
    }
    if (hint.requiresSet.has("weapon_2h") && gear.weapon !== "2h") {
      unmet.push("a two-handed weapon");
    }
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
  if (!state.selectedTraits) return;  // gear controls can change before the builder renders
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

  // ticked traits whose current assumptions make them contribute nothing,
  // or whose wielded weapon contradicts the gear panel's weapon choice
  for (const id of state.selectedTraits) {
    const entry = state.entries?.get(id);
    if (!entry) continue;
    const stackRow = entry.effects.find(e => e.max_stacks != null);
    if (stackRow && (state.traitStacks?.get(Number(stackRow.stack_group)) ?? 1) === 0) {
      warnings.push(`${entry.name} is ticked at 0 assumed stacks — it contributes nothing.`);
    }
    if (entry.effects.some(e => e.variant)
        && !(state.traitVariants?.get(id) || []).length) {
      const kind = VARIANT_KIND[entry.effects.find(e => e.variant).variant] || "wielding";
      warnings.push(`${entry.name} is ticked but no ${kind} option is chosen — ` +
                    `its conditional part contributes nothing.`);
    }
    // a chosen variant the data has no bonus for (e.g. the fox familiar on
    // Enhanced Potency): legal in game, but the trait adds no stats then
    const rowVariants = [...new Set(entry.effects.map(e => e.variant).filter(Boolean))];
    const chosenVariants = state.traitVariants?.get(id) || [];
    if (rowVariants.length && chosenVariants.length
        && !rowVariants.some(v => chosenVariants.includes(v))
        && !chosenVariants.every(v => EXPLICIT_OFF.has(v))) {
      const kind = VARIANT_KIND[rowVariants[0]] || "option";
      warnings.push(`${entry.name}'s bonus applies with the ` +
                    `${joinNames(rowVariants.map(capitalize))} ${kind} — with ` +
                    `${chosenVariants.map(capitalize).join(", ")} it contributes nothing.`);
    }
    for (const variant of state.traitVariants?.get(id) || []) {
      if (TWO_HANDED.has(variant) && gear.weapon === "1h") {
        warnings.push(`${entry.name}'s bonus needs a ${variant} — the gear panel ` +
                      `says two one-handed weapons.`);
      }
      if (ONE_HANDED.has(variant) && gear.weapon === "2h") {
        warnings.push(`${entry.name}'s bonus needs a ${variant} (one-handed) — ` +
                      `the gear panel says a two-handed weapon.`);
      }
    }
  }

  // traits can assume more attunements at once than the profession can hold
  const attuned = new Set();
  for (const id of state.selectedTraits) {
    for (const variant of state.traitVariants?.get(id) || []) {
      if (VARIANT_KIND[variant] === "attunement") attuned.add(variant);
    }
  }
  const attunementLimit = state.spec?.name === "Weaver" ? 2 : 1;
  if (attuned.size > attunementLimit) {
    warnings.push(`Your traits assume being attuned to ${[...attuned].join(", ")} at ` +
                  `the same time — only ${attunementLimit === 2
                    ? "two elements are held at once (Weaver)"
                    : "one element is active at a time"}.`);
  }

  // equipping a trait line activates ALL its minor traits automatically, so
  // a selected trait without the line's (relevant) minors is an impossible
  // in-game state - e.g. Empowered Empowerment never comes without
  // Elemental Empowerment
  const relevant = MODE_EFFECTS[state.mode];
  for (const line of lines) {
    const missing = [...state.entries.values()]
      .filter(e => e.kind === "trait" && e.specialization === line
                   && e.slot === "Minor" && !state.selectedTraits.has(e.id)
                   && e.effects.some(effect => relevant.has(effect.effect)))
      .map(e => e.name);
    if (missing.length) {
      warnings.push(`${line}'s minor traits are always active while the line is ` +
                    `equipped — also tick ${joinNames(missing)}.`);
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
  const specs = await selectProfession(body.profession);
  if (body.elite_spec) {
    selectSpec(specs.find(s => s.name === body.elite_spec));
  } else {
    selectSpec({
      name: `Core ${body.profession}`,
      icon: `/icons/tango_${body.profession}.png`,
      coreArt: true,
    });
  }
  syncUrl("push");
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

  const memory = state.traitMemory?.[TRAIT_FAMILY[state.mode]];
  for (const entry of groupEntries) {
    const label = document.createElement("label");
    label.className = "trait";

    const box = document.createElement("input");
    box.type = "checkbox";
    if (state.pendingIds?.has(entry.id) || memory?.selected.has(entry.id)) {
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
    slotTag.textContent = entry.slot || "";
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

    // stack-scaled traits get a slider for the assumed stacks; traits sharing
    // one buff (the two Catalyst Empowerments) get LINKED sliders via their
    // stack_group - moving one moves the others, they always agree
    const stackRow = entry.effects.find(e => e.max_stacks != null);
    if (stackRow) {
      const groupId = Number(stackRow.stack_group);
      const max = Number(stackRow.max_stacks);
      const fallback = stackRow.default_stacks != null ? Number(stackRow.default_stacks) : max;
      const initial = memory?.stacks.has(groupId) ? memory.stacks.get(groupId)
        : (state.traitStacks.has(groupId) ? state.traitStacks.get(groupId) : fallback);
      state.traitStacks.set(groupId, initial);
      const options = document.createElement("div");
      options.className = "trait-options";
      const slider = document.createElement("input");
      slider.type = "range";
      slider.min = "0";
      slider.max = String(max);
      slider.value = String(initial);
      const readout = document.createElement("span");
      readout.textContent = `assumed stacks: ${initial}/${max}`;
      if (!state.stackControls.has(groupId)) state.stackControls.set(groupId, []);
      state.stackControls.get(groupId).push({ slider, readout, max });
      slider.addEventListener("input", () => {
        const count = Number(slider.value);
        state.traitStacks.set(groupId, count);
        for (const control of state.stackControls.get(groupId)) {
          control.slider.value = String(count);
          control.readout.textContent = `assumed stacks: ${count}/${control.max}`;
        }
        updateBuildWarnings();
      });
      options.append(slider, readout);
      group.append(options);
    }

    // attunement-style traits (Elemental Polyphony): pick up to two distinct
    // elements; being fully attuned to one grants its bonus only once.
    // Familiars are a radio choice instead: exactly one of all four is
    // active, picking another replaces it (never "none").
    let offered = [...new Set(entry.effects.map(e => e.variant).filter(Boolean))];
    if (offered.length) {
      const kind = VARIANT_KIND[offered[0]] || "wielding";
      const radio = kind in RADIO_OPTIONS;
      if (radio) offered = RADIO_OPTIONS[kind];
      let chosen = memory?.variants.has(entry.id)
        ? [...memory.variants.get(entry.id)]
        : [...new Set(entry.effects
            .filter(e => e.variant && e.variant_default)
            .map(e => e.variant))];
      if (radio) chosen = chosen.slice(-1);   // exactly one familiar
      state.traitVariants.set(entry.id, chosen);
      const options = document.createElement("div");
      options.className = "trait-options";
      const caption = document.createElement("span");
      caption.textContent = radio ? RADIO_CAPTIONS[kind]
        : offered.length > 1 ? `${kind}s (up to 2):` : `${kind}:`;
      options.append(caption);
      for (const variant of offered) {
        const chip = document.createElement("button");
        chip.type = "button";
        chip.className = chosen.includes(variant) ? "variant-chip active" : "variant-chip";
        chip.textContent = capitalize(variant);
        chip.addEventListener("click", () => {
          const current = state.traitVariants.get(entry.id) || [];
          if (radio) {
            state.traitVariants.set(entry.id, [variant]);
          } else if (current.includes(variant)) {
            state.traitVariants.set(entry.id, current.filter(v => v !== variant));
          } else {
            state.traitVariants.set(entry.id, [...current, variant].slice(-2));
          }
          const active = state.traitVariants.get(entry.id);
          for (const other of options.querySelectorAll(".variant-chip")) {
            other.classList.toggle("active", active.includes(other.textContent.toLowerCase()));
          }
          updateBuildWarnings();
        });
        options.append(chip);
      }
      group.append(options);
    }
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
  const select = (value) => {
    seg.querySelectorAll("button").forEach(b => b.classList.toggle("active", b.dataset.value === value));
    onChange(value);
  };
  seg.addEventListener("click", (event) => {
    const button = event.target.closest("button");
    if (button) select(button.dataset.value);
  });
  return select;  // for setting the control from a permalink
}

const setEnv = setupSegmented("env-choice", value => { gear.env = value; });
const setWeapon = setupSegmented("weapon-choice", value => {
  gear.weapon = value;
  ["twohanded", "onehanded1", "onehanded2"].forEach(key => gear.ascended.delete(key));
  renderSlotGrid();
  updateConditionHints();   // weapon-gated traits (Right-Hand Strength)
  updateBuildWarnings();    // wielding chips vs the chosen weapon type
});

// ---------- optimizer link (the whole builder state in one URL) ----------
// The navigation URLs above only name profession, spec and mode. The
// optimizer link adds everything else - ticked traits, stack/attunement
// assumptions, gear toggles - so a build can be reopened exactly as it was;
// loading one restores the panel and runs the optimizer. The builds pages
// store such links to open a curated build in the optimizer.

const TOGGLES = {  // URL key -> checkbox id
  fury: "opt-fury", food: "opt-food", ascended_food: "opt-ascended-food", pie: "opt-pie",
  utility: "opt-utility", writs: "opt-writs", stacking: "opt-stacking", herald: "opt-herald",
  single_sigil: "opt-single-sigil", relic_reserved: "opt-reserve-relic", stowed: "opt-stowed",
  tank: "opt-tank",
};

function optimizerLink() {
  const params = new URLSearchParams();
  params.set("profession", state.profession);
  params.set("spec", state.spec.coreArt ? "core" : state.spec.name);
  params.set("mode", state.mode);
  params.set("traits", [...state.selectedTraits].join(","));
  const stacks = [...(state.traitStacks || [])].map(([group, count]) => `${group}:${count}`);
  if (stacks.length) params.set("stacks", stacks.join(","));
  const variants = [...(state.traitVariants || [])]
    .filter(([, list]) => list.length)
    .map(([id, list]) => `${id}:${list.join(".")}`);
  if (variants.length) params.set("variants", variants.join(","));
  params.set("env", gear.env);
  params.set("weapon", gear.weapon);
  params.set("asc", [...gear.ascended].join(","));
  for (const [key, id] of Object.entries(TOGGLES)) params.set(key, el(id).checked ? "1" : "0");
  params.set("might", el("opt-might").value);
  if (state.mode === "boon") params.set("kpos", el("k-slider").value);
  return `${location.origin}${location.pathname}?${params}`;
}

// apply the gear side of an optimizer link (before the builder renders) and
// queue the trait side for the builder
function restoreOptimizerLink(query, mode) {
  const list = (key) => (query.get(key) || "").split(",").filter(Boolean);
  const pairs = (key) => list(key).map(item => item.split(":"));

  if (["3p", "4p"].includes(query.get("env"))) setEnv(query.get("env"));
  if (["1h", "2h"].includes(query.get("weapon"))) setWeapon(query.get("weapon"));
  if (query.has("asc")) {
    const all = [...weaponSlots(), ...ARMOR_TRINKET_SLOTS].map(([key]) => key);
    const wanted = query.get("asc") === "all" ? all : list("asc").filter(key => all.includes(key));
    gear.ascended = new Set(wanted);
    renderSlotGrid();
  }
  for (const [key, id] of Object.entries(TOGGLES)) {
    if (!query.has(key)) continue;
    const box = el(id);
    const checked = query.get(key) === "1";
    if (box.checked !== checked) {
      box.checked = checked;
      box.dispatchEvent(new Event("change"));
    }
  }
  if (query.has("might")) {
    el("opt-might").value = Math.max(0, Math.min(25, Number(query.get("might")) || 0));
    el("opt-might").dispatchEvent(new Event("input"));
  }

  state.pendingMemory = {
    [TRAIT_FAMILY[mode]]: {
      selected: new Set(list("traits").map(Number).filter(Number.isFinite)),
      stacks: new Map(pairs("stacks").map(([group, count]) => [Number(group), Number(count)])),
      variants: new Map(pairs("variants")
        .map(([id, chosen]) => [Number(id), (chosen || "").split(".").filter(Boolean)])),
    },
  };
}

function optimizerLinkButton() {
  const copyButton = document.createElement("button");
  copyButton.type = "button";
  copyButton.className = "ghost-button copy-link";
  copyButton.textContent = "Copy optimizer link";
  copyButton.addEventListener("click", async () => {
    const link = optimizerLink();
    try {
      await navigator.clipboard.writeText(link);
      copyButton.textContent = "Copied — this link reopens the builder exactly like this and optimizes";
    } catch {
      copyButton.textContent = link;
    }
  });
  return copyButton;
}

// ---------- optimizer mode (crit vs boon duration) ----------

// tab switches keep the trait panel state per family: the two crit-stat modes
// share one memory, boon duration has its own
const TRAIT_FAMILY = { crit: "crit", power: "crit", boon: "boon" };

function saveTraitMemory() {
  if (!state.traitMemory) state.traitMemory = {};
  state.traitMemory[TRAIT_FAMILY[state.mode]] = {
    selected: new Set(state.selectedTraits || []),
    stacks: new Map(state.traitStacks || []),
    variants: new Map(state.traitVariants || []),
  };
}

function setMode(mode) {
  if (state.selectedTraits) saveTraitMemory();
  state.mode = mode;
  // keep the segmented control in sync when the mode comes from the URL
  for (const button of el("mode-choice").querySelectorAll("button")) {
    button.classList.toggle("active", button.dataset.value === mode);
  }
  const boon = mode === "boon";
  el("row-env").classList.toggle("hidden", boon);       // boon mode is 3-stat only
  el("fury-label").classList.toggle("hidden", boon);    // fury only affects crit
  el("pie-label").classList.toggle("hidden", boon);
  el("ascended-food-label").classList.toggle("hidden", !boon);
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

setupSegmented("mode-choice", (mode) => {
  setMode(mode);
  syncUrl("push");  // the mode is part of the builder's URL
});

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
  for (const [id, count] of state.traitStacks || []) params.append("stacks[]", `${id}:${count}`);
  for (const [id, list] of state.traitVariants || []) {
    params.append("variants[]", `${id}:${list.join(",")}`);
  }
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
  params.set("stowed", el("opt-stowed").checked);
  if (state.mode === "boon") {
    const { ranking, k } = currentRanking();
    params.set("ranking", ranking);
    if (k) params.set("k", k);
    params.set("ascended_food", el("opt-ascended-food").checked);
    params.set("tank", el("opt-tank").checked);
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

  resultBox.append(chatlinkButton(), optimizerLinkButton());
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
  epCaption.textContent = r.crit_pct !== undefined
    ? `effective power at ${r.crit_pct}% critical chance`
    : "effective power at 100% crit";
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
  if (r.crit_pct !== undefined) {
    facts.unshift(["Critical chance", `${r.crit_pct}% — wherever effective power peaks`]);
  }
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
  // (the free-crit mode has no cap and therefore no cap warnings)
  if (!r.exact && !r.no_cap) {
    const overcapped = r.armor_precision < r.armor_floor;
    const warning = document.createElement("p");
    warning.className = "warning cap-miss";
    warning.textContent = !r.capped
      ? `100% critical chance is out of reach: ${pointText(r.absolute_overshoot)} precision ` +
        `missing. Allow more crit sources or use more ascended pieces.`
      : overcapped
      ? (env === "4p"
          ? `Crit chance exceeds the cap and 4-stat gear cannot shed precision (every prefix ` +
            `carries it) — switch to the 3-stat environment (Valkyrie pieces) or deselect ` +
            `a crit source. Overshoot: ${pointText(r.absolute_overshoot)} precision.`
          : `Crit chance exceeds 100% even with zero precision from gear — deselect a crit ` +
            `source (trait, sigil, writ or relic). ` +
            `Overshoot: ${pointText(r.absolute_overshoot)} precision.`)
      : `No gear split hits the crit cap exactly here — overcapping by the least possible: ` +
        `${pointText(r.absolute_overshoot)} precision is wasted, but the cap holds.`;
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
  herald: "Herald (+175 toughness, +25% boon duration)",
  durability: "Durability (+175 toughness, +125 vitality, +15% boon duration)",
  rebirth: "Rebirth (+175 healing, +125 toughness, +15% boon duration)",
  mercy: "Mercy (+225 healing, +175 toughness)",
  guardian: "Guardian (+100 healing, +300 toughness)",
};
const BOON_FOOD_NAMES = {
  mint_brulee: "Mint Creme Brulee (+100 concentration, +70 healing, +10% outgoing)",
  mint_salad: "Bowl of Fruit Salad with Mint Garnish (+100 healing, +70 concentration, +10% outgoing)",
  rice_ball: "Delicious Rice Ball (+100 healing, +10% outgoing — Fine rarity)",
  eggs_benedict: "Plate of Eggs Benedict (+100 concentration, +70 expertise — Masterwork)",
  nopalitos: "Bowl of Nopalitos Sauté (+100 concentration, +70 toughness — Fine rarity)",
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
  const metric = r => data.ranking === "k"
    ? (data.k + r.healing) * (1 + r.outgoing / 100)
    : r[data.ranking];
  const deltaLabel = (label, r) =>
    `${label} (${((metric(r) / metric(best) - 1) * 100).toFixed(1)}%)`;

  // up to three tabs: the best build, the no-kill-stacks backup, and the
  // aggro-safe variant without any toughness source
  const variants = [{ label: "Best build", row: best, info: null }];
  if (data.stable_fallback) {
    variants.push({
      label: deltaLabel("Stable backup", data.stable_fallback),
      row: data.stable_fallback,
      info: { reasons: ["kill stacks vanish on downstate"] },
    });
  }
  if (data.zero_toughness) {
    variants.push({
      label: deltaLabel("Zero added toughness", data.zero_toughness),
      row: data.zero_toughness,
      info: { zeroToughness: true },
    });
  }

  if (variants.length === 1) {
    const body = document.createElement("div");
    renderBoonBody(body, best, singleSigil, null);
    resultBox.append(body);
  } else {
    const tabs = document.createElement("div");
    tabs.className = "result-tabs";
    const inner = document.createElement("div");
    for (const variant of variants) {
      const tab = document.createElement("button");
      tab.type = "button";
      tab.textContent = variant.label;
      tab.addEventListener("click", () => {
        for (const button of tabs.children) button.classList.toggle("active", button === tab);
        inner.innerHTML = "";
        renderBoonBody(inner, variant.row, singleSigil, variant.info);
      });
      tabs.append(tab);
    }
    resultBox.append(tabs, inner);
    tabs.children[0].classList.add("active");
    renderBoonBody(inner, best, singleSigil, null);
  }

  resultBox.append(chatlinkButton(), optimizerLinkButton());
  resultBox.classList.remove("hidden");
}

function renderBoonBody(container, r, singleSigil, backupInfo) {
  if (backupInfo?.reasons) {
    const intro = document.createElement("p");
    intro.className = "warning";
    intro.textContent = `This build keeps 100% boon duration when the best build would lose it ` +
      `(${backupInfo.reasons.join("; ")}).`;
    container.append(intro);
  }
  if (backupInfo?.zeroToughness) {
    const intro = document.createElement("p");
    intro.className = "warning";
    intro.textContent = "This build adds no toughness at all — no Freshwater Pearl, " +
      "Leadership rune or toughness food — so it can never compete for tank aggro.";
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
  const tank = el("opt-tank").checked;
  for (const [name, value] of [
    ["Healing Power", r.healing], ["Concentration", 1500 + r.conc_delta],
    tank ? ["Toughness", r.toughness] : ["Vitality", r.vitality],
    tank ? ["Vitality", r.vitality] : ["Power", r.power],
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
    const names = group.slot.startsWith("Upgrades")
      ? ["Platinum Doubloon", "Brandspark Jewel", "Crest of the Magi",
         "Freshwater Pearl (Minstrel's)"]
      : ["Harrier's", "Magi's", "Giver's"];
    const parts = [];
    group.counts.forEach((count, i) => {
      if (count > 0) parts.push(`${count}× ${names[i]}`);
    });
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
        `source (trait, rune, sigil, food). Overshoot: ${pointText(r.conc_delta)} ` +
        `concentration (${missPct}%).`
      : (r.conc_delta > 0
          ? `No gear split lands exactly on 100% boon duration here — overcapping by the ` +
            `least possible: ${pointText(r.conc_delta)} concentration (${missPct}%) is ` +
            `wasted, but the cap holds.`
          : `100% boon duration is out of reach: ${pointText(r.conc_delta)} concentration ` +
            `missing (${missPct}% boon duration). Allow more sources (food, oils, stacking ` +
            `sigils, Herald relic) or use more ascended pieces.`);
    container.append(warning);
  }

  if (r.rune === "leadership" && !tank) {
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

// initial load: render the view the URL names (deep links included), then
// normalize the address bar (canonical casing, unknown parameters dropped)
(async () => {
  await applyLocation();
  syncUrl("replace");
})();
