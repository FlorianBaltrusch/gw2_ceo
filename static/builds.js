// Curated builds: /builds lists them with filters, /builds/<slug> shows one.
// Both views live in this page; the URL decides which one renders, so the
// browser's back/forward buttons work like on the optimizer.

const el = (id) => document.getElementById(id);

// the chosen profession recolors the site (theme.css carries one palette
// per profession, keyed by this attribute); no profession = the default
function applyTheme(profession) {
  if (profession) document.documentElement.dataset.profession = profession;
  else delete document.documentElement.dataset.profession;
}

const CATEGORIES = [
  ["", "All"], ["openworld", "Open world"], ["raid", "Instanced PvE"],
  ["support", "Support"], ["wvw", "World vs. World"],
];
const CATEGORY_HINTS = { raid: "Raids, strikes, fractals and dungeons" };
// the site's profession order (static/professions.js): light, medium, heavy
const PROFESSIONS = PROFESSION_ORDER;

const filters = { category: "", profession: "" };
let summaries = null;        // the list JSON, fetched once
let lastListUrl = "/builds"; // where the detail view's back link returns to

// ---------- routing ----------

function route() {
  const match = location.pathname.match(/^\/builds\/([^/]+)\/?$/);
  if (match) {
    showDetail(decodeURIComponent(match[1]));
  } else {
    const query = new URLSearchParams(location.search);
    filters.category = CATEGORIES.some(([key]) => key === query.get("cat")) ? query.get("cat") || "" : "";
    filters.profession = PROFESSIONS.includes(query.get("prof")) ? query.get("prof") : "";
    showList();
  }
}

function navigate(url) {
  history.pushState(null, "", url);
  route();
}

function listUrl() {
  const params = new URLSearchParams();
  if (filters.category) params.set("cat", filters.category);
  if (filters.profession) params.set("prof", filters.profession);
  const query = params.toString();
  return "/builds" + (query ? `?${query}` : "");
}

window.addEventListener("popstate", route);

// links inside the page stay in the page
document.addEventListener("click", (event) => {
  const link = event.target.closest("a[data-local]");
  if (!link || event.metaKey || event.ctrlKey || event.shiftKey || event.button !== 0) return;
  event.preventDefault();
  navigate(link.getAttribute("href"));
});

// ---------- list view ----------

async function showList() {
  el("detail-view").classList.add("hidden");
  el("list-view").classList.remove("hidden");
  document.title = "Builds — GW2 Critical Effect Optimizer";
  if (!summaries) {
    const response = await fetch("/api/builds");
    summaries = response.ok ? await response.json() : [];
  }
  lastListUrl = listUrl();
  applyTheme(filters.profession);
  renderCategoryFilter();
  renderProfessionFilter();
  renderCards();
}

function renderCategoryFilter() {
  const bar = el("category-filter");
  bar.innerHTML = "";
  for (const [key, label] of CATEGORIES) {
    const button = document.createElement("button");
    button.type = "button";
    button.dataset.value = key;
    button.textContent = label;
    if (CATEGORY_HINTS[key]) button.title = CATEGORY_HINTS[key];
    button.classList.toggle("active", filters.category === key);
    button.addEventListener("click", () => {
      filters.category = key;
      history.replaceState(null, "", listUrl());
      lastListUrl = listUrl();
      renderCategoryFilter();
      renderProfessionFilter();  // counts follow the category
      renderCards();
    });
    bar.append(button);
  }
}

function professionIcon(profession) {
  const icon = document.createElement(profession ? "img" : "span");
  icon.className = profession ? "prof-icon" : "prof-icon all";
  if (profession) {
    icon.src = `/icons/tango_${profession}.png`;
    icon.alt = "";
  }
  return icon;
}

function renderProfessionFilter() {
  const toggle = el("profession-toggle");
  const menu = el("profession-menu");
  const counts = new Map(PROFESSIONS.map(p => [p, 0]));
  for (const build of summaries) {
    if (!filters.category || build.category === filters.category) {
      counts.set(build.profession, (counts.get(build.profession) || 0) + 1);
    }
  }

  toggle.innerHTML = "";
  const label = document.createElement("span");
  label.textContent = filters.profession || "All professions";
  const caret = document.createElement("span");
  caret.className = "caret";
  caret.textContent = "▾";
  toggle.append(professionIcon(filters.profession), label, caret);

  menu.innerHTML = "";
  const option = (profession, text, count) => {
    const item = document.createElement("li");
    const button = document.createElement("button");
    button.type = "button";
    button.setAttribute("role", "option");
    button.classList.toggle("active", filters.profession === profession);
    const name = document.createElement("span");
    name.textContent = text;
    button.append(professionIcon(profession), name);
    if (count !== undefined) {
      const number = document.createElement("span");
      number.className = "count";
      number.textContent = count;
      button.append(number);
      button.disabled = count === 0 && filters.profession !== profession;
    }
    button.addEventListener("click", () => {
      filters.profession = profession;
      closeMenu();
      history.replaceState(null, "", listUrl());
      lastListUrl = listUrl();
      applyTheme(profession);
      renderProfessionFilter();
      renderCards();
    });
    item.append(button);
    return item;
  };
  menu.append(option("", "All professions"));
  for (const profession of PROFESSIONS) {
    menu.append(option(profession, profession, counts.get(profession) || 0));
  }
}

function closeMenu() {
  el("profession-menu").classList.add("hidden");
  el("profession-toggle").setAttribute("aria-expanded", "false");
}

el("profession-toggle").addEventListener("click", () => {
  const menu = el("profession-menu");
  const open = menu.classList.toggle("hidden") === false;
  el("profession-toggle").setAttribute("aria-expanded", String(open));
});
document.addEventListener("click", (event) => {
  if (!event.target.closest("#profession-filter")) closeMenu();
});
document.addEventListener("keydown", (event) => {
  if (event.key === "Escape") closeMenu();
});

function badge(text, className, hint) {
  const span = document.createElement("span");
  span.className = `badge ${className}`;
  span.textContent = text;
  if (hint) span.title = hint;
  return span;
}

function renderCards() {
  const list = el("build-list");
  const status = el("list-status");
  list.innerHTML = "";
  const shown = summaries.filter(build =>
    (!filters.category || build.category === filters.category)
    && (!filters.profession || build.profession === filters.profession));

  status.classList.toggle("hidden", shown.length > 0);
  status.textContent = summaries.length
    ? "No build matches these filters yet."
    : "No builds published yet.";

  for (const build of shown) {
    const card = document.createElement("a");
    card.className = "build-card";
    card.href = `/builds/${encodeURIComponent(build.slug)}`;
    card.dataset.local = "";
    if (build.banner) card.style.setProperty("--banner", `url("${build.banner}")`);

    const row1 = document.createElement("span");
    row1.className = "card-row1";
    const icon = document.createElement("img");
    icon.className = "card-spec-icon";
    icon.src = build.spec_icon;
    icon.alt = "";
    const title = document.createElement("span");
    title.className = "card-title";
    const spec = document.createElement("span");
    spec.className = "card-spec";
    spec.textContent = build.title;
    const prof = document.createElement("span");
    prof.className = "card-prof";
    prof.textContent = build.subtitle;
    title.append(spec, prof);
    const badges = document.createElement("span");
    badges.className = "card-badges";
    badges.append(badge(build.category_label, `cat-${build.category}`, build.category_hint));
    for (const tag of build.tags) badges.append(badge(tag, "tag"));
    row1.append(icon, title, badges);

    const row2 = document.createElement("span");
    row2.className = "card-row2";
    const weapons = document.createElement("span");
    weapons.className = "card-weapons";
    build.weapon_summary.forEach((set, index) => {
      if (index) {
        const sep = document.createElement("span");
        sep.className = "sep";
        sep.textContent = "·";
        weapons.append(sep);
      }
      weapons.append(document.createTextNode(set));
    });
    const lines = document.createElement("span");
    lines.className = "card-lines";
    for (const line of build.traitlines) {
      const lineIcon = document.createElement("img");
      lineIcon.src = line.icon;
      lineIcon.alt = "";
      lineIcon.title = line.name;
      lines.append(lineIcon);
    }
    const names = document.createElement("span");
    names.className = "names";
    names.textContent = build.traitlines.map(line => line.name).join(" · ");
    if (build.alternatives?.length) {
      const alt = document.createElement("span");
      alt.className = "alt";
      alt.textContent = `or ${build.alternatives.map(a => a.name).join(" / ")}`;
      alt.title = build.alternatives.map(a => `${a.name} instead of ${a.replaces}`).join("\n");
      names.append(alt);   // flows with the names, wraps with them
    }
    lines.append(names);
    row2.append(weapons, lines);

    card.append(row1, row2);
    list.append(card);
  }
}

// ---------- detail view ----------

async function showDetail(slug) {
  el("list-view").classList.add("hidden");
  const view = el("detail-view");
  view.classList.remove("hidden");
  view.innerHTML = "";

  const response = await fetch(`/api/builds/${encodeURIComponent(slug)}`);
  if (!response.ok) {
    const missing = document.createElement("p");
    missing.className = "not-found";
    missing.textContent = "There is no build under this address.";
    view.append(backLink(), missing);
    return;
  }
  const build = await response.json();
  applyTheme(build.profession);
  document.title = `${build.name} — GW2 Builds`;
  window.scrollTo({ top: 0 });

  const columns = document.createElement("div");
  columns.className = "build-columns";
  const traits = section("Traits", traitLines(build.lines));
  traits.classList.add("col-traits");
  const alternatives = build.alternatives || [];
  if (alternatives.length) traits.append(alternativePanels(alternatives));

  // gear variants: the build's gear, plus one tab per alternative whose
  // optimizer result differs from it
  const differing = alternatives.filter(alt => alt.gear_differs);
  const variants = [
    { label: differing.length === 1 ? `with ${differing[0].replaces}` : "Main build",
      gear: build.gear, warning: build.gear_warning, character: build.character },
    ...differing.map(alt => ({ label: `with ${alt.line.name}`, gear: alt.gear,
                               warning: alt.gear_warning, character: alt.character })),
  ];
  const tabbed = (title, render) => {
    const sec = section(title, variantPanes(variants, render));
    if (variants.length > 1) withTabs(sec, variantTabs(variants));
    return sec;
  };

  const side = document.createElement("div");
  side.className = "col-side";
  const skills = section("Skills", skillBars(build.skills));
  if (build.pets || build.legends) skills.append(companions(build));
  side.append(skills);
  if (build.character) {
    side.append(tabbed("Character", variant => variant.character
      ? characterCard(variant.character) : document.createElement("div")));
  }
  columns.append(traits, side);
  view.append(
    backLink(),
    header(build),
    columns,
    tabbed("Gear", variant => gearPanel(variant.gear, variant.warning)),
    section("Links", links(build)),
  );
  if (build.notes.trim()) view.append(section("Notes", notes(build.notes)));
  requestAnimationFrame(drawAllTraitLines);
}

function backLink() {
  const link = document.createElement("a");
  link.className = "back-link";
  link.href = lastListUrl;
  link.dataset.local = "";
  link.textContent = "← All builds";
  return link;
}

function header(build) {
  const head = document.createElement("header");
  head.className = "build-head";
  if (build.banner) head.style.setProperty("--banner", `url("${build.banner}")`);

  const row = document.createElement("div");
  row.className = "build-head-row";
  const icon = document.createElement("img");
  icon.src = build.spec_icon;
  icon.alt = "";
  const titles = document.createElement("div");
  const title = document.createElement("h1");
  title.textContent = build.name;
  const meta = document.createElement("div");
  meta.className = "build-meta";
  meta.append(document.createTextNode(`${build.profession} · ${build.spec}`));
  meta.append(badge(build.category_label, `cat-${build.category}`, build.category_hint));
  for (const tag of build.tags) meta.append(badge(tag, "tag"));
  titles.append(title, meta);
  row.append(icon, titles);
  head.append(row);

  if (build.summary) {
    const summary = document.createElement("p");
    summary.className = "build-summary";
    summary.textContent = build.summary;
    head.append(summary);
  }
  return head;
}

function section(title, content) {
  const box = document.createElement("section");
  box.className = "build-section";
  const heading = document.createElement("h2");
  heading.textContent = title;
  box.append(heading, content);
  return box;
}

// --- trait lines, drawn like the in-game specialization panel ---

const TIER_LABELS = ["Adept", "Master", "Grandmaster"];

function traitNode(trait, className, tier, extra) {
  const node = document.createElement("span");
  node.className = `trait-node ${className}`;
  node.title = `${trait.name} (${TIER_LABELS[tier]} ${extra})\n\n${trait.description}`;
  const img = document.createElement("img");
  img.src = trait.icon;
  img.alt = trait.name;
  img.loading = "lazy";
  node.append(img);
  return node;
}

function traitLines(lines) {
  const wrap = document.createElement("div");
  for (const line of lines) {
    const panel = document.createElement("div");
    panel.className = "traitline";
    panel.style.setProperty("--panel", `url("${line.background}")`);

    // the big hexagon on the left shows a crop of the line's own banner art
    const hex = document.createElement("div");
    hex.className = "traitline-hex";
    hex.title = line.name;
    const frame = document.createElement("span");
    frame.className = "frame";
    const art = document.createElement("span");
    art.className = "art";
    hex.append(frame, art);

    const tree = document.createElement("div");
    tree.className = "trait-tree";
    for (let tier = 0; tier < 3; tier++) {
      const column = document.createElement("div");
      column.className = "tier";
      column.append(traitNode(line.minors[tier], "minor", tier, "minor"));
      const majors = document.createElement("div");
      majors.className = "majors";
      line.majors[tier].forEach((trait, position) => {
        const selected = line.selected[tier] === position + 1;
        majors.append(traitNode(trait, selected ? "major selected" : "major", tier, "major"));
      });
      column.append(majors);
      tree.append(column);
    }
    const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    svg.classList.add("trait-lines");
    panel.append(hex, svg, tree);   // the lines paint under the icons
    wrap.append(panel);

    // the line's name and its chosen majors in words, below the panel
    const picks = document.createElement("p");
    picks.className = "traitline-picks";
    const icon = document.createElement("img");
    icon.src = line.icon;
    icon.alt = "";
    const name = document.createElement("span");
    name.className = "line-name";
    name.textContent = line.name;
    picks.append(icon, name);
    line.selected.forEach((choice, tier) => {
      if (tier) {
        const sep = document.createElement("span");
        sep.className = "sep";
        sep.textContent = "·";
        picks.append(sep);
      }
      const pick = document.createElement("b");
      pick.textContent = choice ? line.majors[tier][choice - 1].name : "—";
      picks.append(pick);
    });
    wrap.append(picks);
  }
  return wrap;
}

// an alternative trait line, drawn like the build's own lines, with what it
// stands in for, the author's note and the chat link of that variant
function alternativePanels(alternatives) {
  const wrap = document.createElement("div");
  wrap.className = "alternatives";
  for (const alt of alternatives) {
    const head = document.createElement("h3");
    head.className = "alternative-head";
    const name = document.createElement("b");
    name.textContent = alt.line.name;
    head.append("Alternative: ", name,
                alt.replaces === alt.line.name ? " with other picks" : ` instead of ${alt.replaces}`);
    wrap.append(head, traitLines([alt.line]));

    const row = document.createElement("div");
    row.className = "alternative-row";
    const info = document.createElement("p");
    info.className = "hint";
    info.textContent = [
      alt.note,
      alt.gear_differs ? `Different gear: see the "with ${alt.line.name}" tab.`
        : alt.gear_warning || "Same gear as the main build.",
    ].filter(Boolean).join(" ");
    row.append(info, copyButton(alt.chatlink, "Copy chat link"));
    wrap.append(row);
  }
  return wrap;
}

// --- gear variants: one pane per variant, switched by synced tab bars ---

function variantPanes(variants, render) {
  const wrap = document.createElement("div");
  variants.forEach((variant, index) => {
    const pane = document.createElement("div");
    pane.className = index ? "variant-pane hidden" : "variant-pane";
    pane.dataset.variant = index;
    pane.append(render(variant));
    wrap.append(pane);
  });
  return wrap;
}

function variantTabs(variants) {
  const bar = document.createElement("div");
  bar.className = "result-tabs variant-tabs";
  bar.setAttribute("role", "tablist");
  variants.forEach((variant, index) => {
    const tab = document.createElement("button");
    tab.type = "button";
    tab.setAttribute("role", "tab");
    tab.textContent = variant.label;
    if (!index) tab.classList.add("active");
    tab.addEventListener("click", () => selectVariant(index));
    bar.append(tab);
  });
  return bar;
}

function selectVariant(index) {
  for (const bar of document.querySelectorAll(".variant-tabs")) {
    [...bar.children].forEach((tab, i) => tab.classList.toggle("active", i === index));
  }
  for (const pane of document.querySelectorAll(".variant-pane")) {
    pane.classList.toggle("hidden", Number(pane.dataset.variant) !== index);
  }
}

// the section's title row gets the tab bar beside the heading
function withTabs(sec, bar) {
  const heading = sec.querySelector("h2");
  const head = document.createElement("div");
  head.className = "section-head";
  heading.replaceWith(head);
  head.append(heading, bar);
}

// the connectors run minor → chosen major → next minor; measured from the
// rendered layout so every viewport width works, redrawn on resize
function drawTraitLines(panel) {
  const svg = panel.querySelector(".trait-lines");
  if (!svg) return;
  const box = panel.getBoundingClientRect();
  svg.setAttribute("viewBox", `0 0 ${box.width} ${box.height}`);
  svg.innerHTML = "";
  const center = (node) => {
    const rect = node.getBoundingClientRect();
    return [rect.left - box.left + rect.width / 2, rect.top - box.top + rect.height / 2];
  };
  const points = [];
  for (const tier of panel.querySelectorAll(".tier")) {
    points.push(center(tier.querySelector(".minor")));
    const chosen = tier.querySelector(".major.selected");
    if (chosen) points.push(center(chosen));
  }
  for (let i = 1; i < points.length; i++) {
    const line = document.createElementNS("http://www.w3.org/2000/svg", "line");
    line.setAttribute("x1", points[i - 1][0]);
    line.setAttribute("y1", points[i - 1][1]);
    line.setAttribute("x2", points[i][0]);
    line.setAttribute("y2", points[i][1]);
    svg.append(line);
  }
}

function drawAllTraitLines() {
  for (const panel of document.querySelectorAll(".traitline")) drawTraitLines(panel);
}

new ResizeObserver(() => drawAllTraitLines()).observe(document.body);

// --- skills ---

function skillBars(skills) {
  const wrap = document.createElement("div");
  const classes = ["heal", "utility1", "utility2", "utility3", "elite"];
  for (const [label, row] of [["Land", skills.land], ["Underwater", skills.aquatic]]) {
    const bar = document.createElement("div");
    bar.className = "skillbar";
    const caption = document.createElement("span");
    caption.className = "skillbar-label";
    caption.textContent = label;
    const list = document.createElement("div");
    list.className = "skills";
    row.forEach((skill, index) => {
      const figure = document.createElement("figure");
      figure.className = `skill ${classes[index]}`;
      if (skill) {
        const img = document.createElement("img");
        img.src = skill.icon;
        img.alt = skill.name;
        img.title = `${skill.name} (${skill.slot})\n\n${skill.description}`;
        const name = document.createElement("figcaption");
        name.textContent = skill.name.replace(/^"|"$/g, "");
        figure.append(img, name);
      } else {
        const empty = document.createElement("span");
        empty.className = "empty";
        const name = document.createElement("figcaption");
        name.textContent = "—";
        figure.append(empty, name);
      }
      list.append(figure);
    });
    bar.append(caption, list);
    wrap.append(bar);
  }
  return wrap;
}

// a Ranger's pets or a Revenant's legends, under the skill bars
function companions(build) {
  const wrap = document.createElement("div");
  wrap.className = "companions";
  const source = build.pets || build.legends;
  const names = (entries) => entries.map(entry => entry && entry.name).join("|");
  // one row when the underwater pair is the same (or empty), two otherwise
  const groups = [[build.pets ? "Pets" : "Legends", source.land]];
  if (source.aquatic.some(Boolean) && names(source.aquatic) !== names(source.land)) {
    groups.push(["Underwater", source.aquatic]);
  }
  for (const [label, entries] of groups) {
    if (!entries.some(Boolean)) continue;
    const caption = document.createElement("span");
    caption.className = "skillbar-label";
    caption.textContent = label;
    wrap.append(caption);
    const row = document.createElement("div");
    row.className = "companion-row";
    for (const entry of entries) {
      if (!entry) continue;
      const item = document.createElement("span");
      item.className = "companion";
      const img = document.createElement("img");
      img.src = entry.icon;
      img.alt = "";
      if (entry.description) img.title = entry.description;
      const name = document.createElement("span");
      name.textContent = entry.name;
      item.append(img, name);
      row.append(item);
    }
    wrap.append(row);
  }
  return wrap;
}

// --- gear ---

// placeholder labels for the icon squares until the skins' icons arrive
const SLOT_SHORT = {
  head: "Head", shoulders: "Shldr", chest: "Chest", gloves: "Glove", legs: "Legs", boots: "Boots",
  back: "Back", accessory1: "Acc 1", accessory2: "Acc 2", amulet: "Amul", ring1: "Ring 1", ring2: "Ring 2",
};
const WEAPON_SHORT = {
  Greatsword: "GS", Warhorn: "Horn", Scepter: "Scep", Longbow: "LB", Shortbow: "SB",
  Trident: "Trid", Hammer: "Hamr", Dagger: "Dagg", Pistol: "Pist", Shield: "Shld",
  "Harpoon gun": "Harp", Speargun: "Harp",
};

function gearSlot(item, name, subline, shortLabel) {
  const slot = document.createElement("div");
  slot.className = `gear-slot rarity-${item.rarity}`;
  const icon = document.createElement("span");
  icon.className = "gear-icon";
  if (item.icon) {
    const img = document.createElement("img");
    img.src = item.icon;
    img.alt = "";
    icon.append(img);
  } else {
    icon.textContent = shortLabel;  // the place where the skin's icon will go
  }
  const text = document.createElement("span");
  text.className = "gear-text";
  const title = document.createElement("span");
  title.className = "gear-name";
  title.textContent = name;
  text.append(title);
  if (subline) {
    const sub = document.createElement("span");
    sub.className = "gear-sub";
    sub.textContent = subline;
    text.append(sub);
  }
  if (item.skin) {
    const skin = document.createElement("span");
    skin.className = "gear-skin";
    skin.textContent = item.skin;
    text.append(skin);
  }
  if (item.note) {
    const note = document.createElement("span");
    note.className = "gear-note";
    note.textContent = item.note;
    text.append(note);
  }
  slot.title = `${item.rarity} ${name}`;
  slot.append(icon, text);
  return slot;
}

function gearPanel(gear, warning) {
  const wrap = document.createElement("div");

  if (warning) {
    const box = document.createElement("p");
    box.className = "gear-warning";
    box.textContent = warning;
    wrap.append(box);
  }

  const panel = document.createElement("div");
  panel.className = "gear-panel";

  const column = (title, items, subline) => {
    const col = document.createElement("div");
    col.className = "gear-column";
    const heading = document.createElement("div");
    heading.className = "gear-group-title";
    heading.textContent = title;
    col.append(heading);
    for (const item of items) {
      const sub = [subline(item), item.infusions].filter(Boolean).join(" · ");
      col.append(gearSlot(item, `${item.prefix} ${item.label}`.trim(), sub, SLOT_SHORT[item.slot]));
    }
    return col;
  };
  if (gear.armor.length) {
    panel.append(column("Armor", gear.armor, item => item.rune || gear.rune || ""));
  }
  if (gear.trinkets.length) {
    panel.append(column("Trinkets", gear.trinkets, item => item.upgrade || ""));
  }
  wrap.append(panel);

  if (gear.weapon_sets.length) {
    const sets = document.createElement("div");
    sets.className = "weapon-sets";
    for (const weaponSet of gear.weapon_sets) {
      const box = document.createElement("div");
      box.className = "weapon-set";
      const heading = document.createElement("div");
      heading.className = "gear-group-title";
      heading.textContent = weaponSet.label;
      box.append(heading);
      for (const weapon of weaponSet.weapons) {
        const sub = [weapon.sigils.join(" · "), weapon.infusions].filter(Boolean).join(" · ");
        box.append(gearSlot(weapon, `${weapon.prefix} ${weapon.type}`.trim(), sub,
                            WEAPON_SHORT[weapon.type] || weapon.type));
      }
      sets.append(box);
    }
    wrap.append(sets);
  }

  if (gear.consumables.length) {
    const list = document.createElement("dl");
    list.className = "consumables";
    for (const { label, value } of gear.consumables) {
      const dt = document.createElement("dt");
      dt.textContent = label;
      const dd = document.createElement("dd");
      dd.textContent = value;
      list.append(dt, dd);
    }
    wrap.append(list);
  }
  for (const text of gear.notes || []) {
    const note = document.createElement("p");
    note.className = "hint gear-footnote";
    note.textContent = text;
    wrap.append(note);
  }
  return wrap;
}

// --- character card: attributes and what they mean in game ---

const fmt = (value) => typeof value === "number" ? value.toLocaleString("en-US") : value;

function characterCard(character) {
  const wrap = document.createElement("div");
  wrap.className = "character-card";
  if (character.headline) {
    const head = document.createElement("div");
    head.className = "character-headline";
    const value = document.createElement("span");
    value.className = "value";
    value.textContent = fmt(character.headline.value);
    const caption = document.createElement("span");
    caption.className = "caption";
    caption.textContent = character.headline.caption;
    head.append(value, caption);
    wrap.append(head);
  }
  const list = document.createElement("div");
  list.className = "attributes";
  for (const attribute of character.attributes) {
    const row = document.createElement("div");
    row.className = "attribute";
    const name = document.createElement("span");
    name.className = "name";
    name.textContent = attribute.name;
    const value = document.createElement("span");
    value.className = "value";
    value.textContent = fmt(attribute.value);
    row.append(name, value);
    if (attribute.effect) {
      const effect = document.createElement("span");
      effect.className = "effect";
      const label = document.createElement("span");
      label.textContent = attribute.effect;
      const number = document.createElement("b");
      number.textContent = fmt(attribute.effect_value);
      effect.append(label, number);
      row.append(effect);
    }
    list.append(row);
  }
  wrap.append(list);
  return wrap;
}

// --- links ---

function links(build) {
  const wrap = document.createElement("div");
  const hint = document.createElement("p");
  hint.className = "hint";
  hint.textContent = "Paste the chat link into the game chat and click it to load traits, skills and weapons.";
  const box = document.createElement("div");
  box.className = "linkbox";
  const code = document.createElement("code");
  code.textContent = build.chatlink;
  box.append(code, copyButton(build.chatlink, "Copy chat link"));
  wrap.append(hint, box);

  if (build.optimizer) {
    const row = document.createElement("div");
    row.className = "link-row";
    const open = document.createElement("a");
    open.className = "cta-link";
    open.href = build.optimizer;
    open.textContent = "Open in the optimizer";
    row.append(open);
    wrap.append(row);
  }
  return wrap;
}

function copyButton(text, label) {
  const copy = document.createElement("button");
  copy.type = "button";
  copy.className = "ghost-button";
  copy.textContent = label;
  copy.addEventListener("click", async () => {
    try {
      await navigator.clipboard.writeText(text);
      copy.textContent = "Copied";
    } catch {
      copy.textContent = "Select and copy the text";
    }
    setTimeout(() => { copy.textContent = label; }, 2000);
  });
  return copy;
}

function notes(text) {
  const wrap = document.createElement("div");
  wrap.className = "build-notes";
  for (const paragraph of text.trim().split(/\n\s*\n/)) {
    const p = document.createElement("p");
    p.textContent = paragraph.replace(/\s*\n\s*/g, " ");
    wrap.append(p);
  }
  return wrap;
}

route();
