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
  const core = document.createElement("button");
  core.className = "spec-tile core";
  core.type = "button";
  const coreArt = document.createElement("img");
  coreArt.className = "core-art";
  coreArt.src = professionImage(profession);
  coreArt.alt = "";
  const coreLabel = specLabel(null, `Core ${profession}`, "no elite spec");
  core.append(coreArt, coreLabel);
  core.addEventListener("click", () => selectSpec({ name: `Core ${profession}`, icon: null }));
  grid.append(core);

  for (const spec of eliteSpecs) {
    const tile = document.createElement("button");
    tile.className = "spec-tile";
    tile.type = "button";
    tile.style.backgroundImage = `url("${spec.background}")`;
    tile.append(specLabel(spec.icon, spec.name, "elite spec"));
    tile.addEventListener("click", () => selectSpec(spec));
    grid.append(tile);
  }
}

function specLabel(iconSrc, name, kind) {
  const label = document.createElement("span");
  label.className = "label";
  if (iconSrc) {
    const icon = document.createElement("img");
    icon.src = iconSrc;
    icon.alt = "";
    label.append(icon);
  }
  const nameSpan = document.createElement("span");
  nameSpan.className = "name";
  nameSpan.textContent = name;
  const kindSpan = document.createElement("span");
  kindSpan.className = "kind";
  kindSpan.textContent = kind;
  label.append(nameSpan, kindSpan);
  return label;
}

function selectSpec(spec) {
  state.spec = spec;
  finishSelection();
}

// ---------- hand over to the main app ----------

function finishSelection() {
  el("topbar-title").textContent = `${state.spec.name} (${state.profession})`;
  const icon = el("topbar-spec-icon");
  if (state.spec.icon) {
    icon.src = state.spec.icon;
    icon.classList.remove("hidden");
  } else {
    icon.classList.add("hidden");
  }

  const overlay = el("overlay");
  overlay.classList.add("closing");
  overlay.addEventListener("animationend", () => overlay.classList.add("hidden"),
                           { once: true });

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

renderProfessionGrid();

// deep link: /?profession=Elementalist jumps straight to its spec picker
const preselected = new URLSearchParams(location.search).get("profession");
if (preselected) {
  const match = PROFESSIONS.find(p => p.name.toLowerCase() === preselected.toLowerCase());
  if (match) selectProfession(match.name);
}
