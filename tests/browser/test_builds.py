"""Landing page, builds list with filters, one build's page, and the
optimizer link that reopens a build in the optimizer."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _common import BASE, By, WebDriverWait, check, finish, make_driver, visible

driver = make_driver(1400, 1100)
wait = WebDriverWait(driver, 20)


def count(css):
    return len(driver.find_elements(By.CSS_SELECTOR, css))


try:
    # landing: two doors
    driver.get(BASE + "/")
    wait.until(lambda d: count(".door") == 2)
    hrefs = [a.get_attribute("href") for a in driver.find_elements(By.CSS_SELECTOR, ".door")]
    check("doors lead to /ceo and /builds",
          hrefs[0].endswith("/ceo") and hrefs[1].endswith("/builds"), str(hrefs))
    check("landing asks the question",
          "create your own build or browse ours" in driver.find_element(By.CSS_SELECTOR, ".question").text)

    check("landing links to the legal notice",
          any(a.get_attribute("href").endswith("/impressum") for a in driver.find_elements(By.CSS_SELECTOR, ".site-footer a")))
    driver.get(BASE + "/impressum")
    wait.until(lambda d: count(".legal") == 1)
    check("legal page serves the Impressum and the privacy policy, not in the main navigation",
          "Legal Notice" in driver.title and count("#impressum") == 1 and count("#privacy") == 1
          and count(".site-nav") == 0 and driver.find_element(By.ID, "legal-back").text.endswith("Back"))
    driver.find_element(By.ID, "legal-back").click()
    wait.until(lambda d: count(".door") == 2)
    check("back button returns to the page you came from", driver.current_url.rstrip("/").endswith(BASE.rstrip("/")), driver.current_url)

    # old optimizer deep links still work
    driver.get(BASE + "/?profession=Guardian&spec=Firebrand&mode=crit")
    wait.until(lambda d: visible(d, "main"))
    check("root deep link redirects to /ceo", "/ceo?" in driver.current_url, driver.current_url)

    # the list: Florian's builds, light-to-heavy professions, Elementalist first
    driver.get(BASE + "/builds")
    wait.until(lambda d: count(".build-card") >= 20)
    total = count(".build-card")
    check("all build files listed", total == 28, str(total))
    card = driver.find_element(By.CSS_SELECTOR, ".build-card")
    check("card row one: spec + profession (Tempest first: HoT before the newer specs)",
          card.find_element(By.CSS_SELECTOR, ".card-spec").text == "Tempest"
          and card.find_element(By.CSS_SELECTOR, ".card-prof").text.lower() == "elementalist")
    check("instanced build before the open-world one of the same spec",
          "instanced" in card.find_element(By.CSS_SELECTOR, ".badge").text.lower()
          and "Dagger / Dagger" in card.find_element(By.CSS_SELECTOR, ".card-weapons").text
          and "Fire · Air · Tempest" in card.find_element(By.CSS_SELECTOR, ".card-lines").text)
    specs = [c.find_element(By.CSS_SELECTOR, ".card-spec").text for c in driver.find_elements(By.CSS_SELECTOR, ".build-card")]
    check("expansion order inside a profession", specs.index("Tempest") < specs.index("Weaver") < specs.index("Evoker")
          and specs.index("Necromancer") < specs.index("Reaper") < specs.index("Scourge")
          and specs.index("Guardian") < specs.index("Dragonhunter") < specs.index("Willbender"), str(specs))

    home = driver.find_element(By.CSS_SELECTOR, ".site-bar .ghost-button")
    check("builds page has a Home button", home.text.endswith("Home") and home.get_attribute("href").rstrip("/") == BASE.rstrip("/"),
          home.get_attribute("href"))

    # category filter
    groups = driver.find_elements(By.CSS_SELECTOR, ".filter-group .control-label")
    check("profession filter comes first", groups[0].text.lower() == "profession", str([g.text for g in groups]))
    driver.find_element(By.CSS_SELECTOR, "#category-filter button[data-value='raid']").click()
    wait.until(lambda d: count(".build-card") == 6)
    check("raid filter keeps the six raid builds", count(".build-card") == 6
          and all("instanced" in b.text.lower() for b in driver.find_elements(By.CSS_SELECTOR, ".build-card .badge")))
    check("filter in URL", "cat=raid" in driver.current_url, driver.current_url)

    # profession dropdown: counts follow the category
    driver.find_element(By.ID, "profession-toggle").click()
    wait.until(lambda d: not d.find_element(By.ID, "profession-menu").get_attribute("class").count("hidden"))
    options = driver.find_elements(By.CSS_SELECTOR, "#profession-menu button")
    check("dropdown lists all nine professions plus 'all'", len(options) == 10, str(len(options)))
    names = [o.text.split("\n")[0] for o in options[1:]]
    check("dropdown in light/medium/heavy order", names == ["Elementalist", "Mesmer", "Necromancer", "Engineer", "Ranger", "Thief", "Guardian", "Revenant", "Warrior"], str(names))
    by_name = {o.text.split("\n")[0]: o for o in options}
    check("necromancer disabled under raid", not by_name["Necromancer"].is_enabled())
    check("mesmer shows its raid count", by_name["Mesmer"].text.endswith("2"), by_name["Mesmer"].text)
    by_name["Mesmer"].click()
    wait.until(lambda d: count(".build-card") == 2)
    check("profession in URL", "prof=Mesmer" in driver.current_url, driver.current_url)
    driver.find_element(By.CSS_SELECTOR, "#category-filter button[data-value='']").click()
    wait.until(lambda d: count(".build-card") == 6)
    check("all categories + mesmer: six mesmer builds", count(".build-card") == 6)

    # the build page
    driver.find_element(By.CSS_SELECTOR, "a.build-card[href$='/builds/raid-power-chronomancer']").click()
    wait.until(lambda d: count(".traitline") == 3)
    check("detail URL", driver.current_url.endswith("/builds/raid-power-chronomancer"), driver.current_url)
    check("three trait lines", count(".traitline") == 3)
    check("nine minors, 27 majors", count(".minor") == 9 and count(".major") == 27,
          f"{count('.minor')} / {count('.major')}")
    check("nine chosen majors", count(".major.selected") == 9, str(count(".major.selected")))
    check("five connector lines per panel", count(".trait-lines line") == 15, str(count(".trait-lines line")))
    check("one art hexagon per panel", count(".traitline-hex") == 3)
    picks = [p.text for p in driver.find_elements(By.CSS_SELECTOR, ".traitline-picks")]
    check("chosen traits named", "Chronophantasma" in picks[2], picks[2])
    check("ten skill slots, land and underwater", count(".skill") == 10 and count(".skill img") >= 5,
          f"{count('.skill')} / {count('.skill img')}")
    names = [f.text for f in driver.find_elements(By.CSS_SELECTOR, ".skill figcaption")]
    check("land skills from the file", "Well of Calamity" in names and "Gravity Well" in names, str(names))
    check("gear: 6 armor + 6 trinkets + 3 weapons", count(".gear-slot") == 15, str(count(".gear-slot")))
    check("gear shows the rune per armor piece",
          "Superior Rune of" in driver.find_element(By.CSS_SELECTOR, ".gear-column .gear-slot .gear-sub").text)
    check("character card with headline and derived effects",
          count(".character-headline") == 1 and count(".attribute") >= 4
          and count(".attribute .effect") >= 3)
    effects = [e.text for e in driver.find_elements(By.CSS_SELECTOR, ".attribute .effect")]
    check("crit chance and health derived", any("Critical chance" in e and "100.00%" in e for e in effects)
          and any("Health" in e for e in effects), str(effects))
    check("no gear warning", count(".gear-warning") == 0)
    labels = [d.text for d in driver.find_elements(By.CSS_SELECTOR, ".consumables dt")]
    check("consumables listed", {"Rune", "Relic", "Food", "Utility", "Infusions"} <= set(labels), str(labels))
    check("chat link shown", driver.find_element(By.CSS_SELECTOR, ".linkbox code").text.startswith("[&DQ"))
    optimizer_link = driver.find_element(By.CSS_SELECTOR, ".cta-link").get_attribute("href")
    check("optimizer link present", "/ceo?" in optimizer_link and "traits=" in optimizer_link)

    # back keeps the filters
    driver.find_element(By.CSS_SELECTOR, ".back-link").click()
    wait.until(lambda d: count(".build-card") == 6)
    check("back to filtered list", "prof=Mesmer" in driver.current_url, driver.current_url)

    # an alternative trait line: drawn under the build's lines, its gear in a second tab
    driver.get(BASE + "/builds/support-tempest")
    wait.until(lambda d: count(".traitline") == 4)
    check("alternative line drawn as a fourth panel", count(".alternatives .traitline") == 1
          and count(".alternatives .major.selected") == 3)
    head = driver.find_element(By.CSS_SELECTOR, ".alternative-head").text
    check("alternative caption names both lines", "Arcane" in head and "Earth" in head, head)
    check("alternative has its own chat link button", count(".alternative-row .ghost-button") == 1)
    hint = driver.find_element(By.CSS_SELECTOR, ".alternative-row .hint").text
    check("alternative points to its gear tab", "Different gear" in hint, hint)
    tabs = driver.find_elements(By.CSS_SELECTOR, ".variant-tabs")
    check("gear and character carry synced tabs", len(tabs) == 2
          and all(len(t.find_elements(By.TAG_NAME, "button")) == 2 for t in tabs), str(len(tabs)))
    labels = [b.text for b in tabs[0].find_elements(By.TAG_NAME, "button")]
    check("tabs named after the lines", labels == ["with Earth", "with Arcane"], str(labels))
    main_gear = driver.find_element(By.CSS_SELECTOR, ".variant-pane[data-variant='0'] .gear-panel").text
    tabs[-1].find_elements(By.TAG_NAME, "button")[1].click()
    wait.until(lambda d: all(p.is_displayed() for p in d.find_elements(By.CSS_SELECTOR, ".variant-pane[data-variant='1']")))
    check("second tab shows both panes and hides the first",
          all(not p.is_displayed() for p in driver.find_elements(By.CSS_SELECTOR, ".variant-pane[data-variant='0']"))
          and all(t.find_elements(By.TAG_NAME, "button")[1].get_attribute("class") == "active" for t in tabs))
    alt_gear = driver.find_element(By.CSS_SELECTOR, ".variant-pane[data-variant='1'] .gear-panel").text
    check("alternative gear differs from the main gear", alt_gear != main_gear and "Harrier's" in alt_gear + main_gear)

    # an alternative without its own gear: no tabs
    driver.get(BASE + "/builds/wvw-condi-necromancer")
    wait.until(lambda d: count(".traitline") == 4)
    check("alternative without optimizer link: same gear, no tabs", count(".variant-tabs") == 0
          and "Same gear" in driver.find_element(By.CSS_SELECTOR, ".alternative-row .hint").text)

    # the card names the alternative
    driver.get(BASE + "/builds?cat=support")
    wait.until(lambda d: count(".build-card") == 4)
    alts = [a.text for a in driver.find_elements(By.CSS_SELECTOR, ".card-lines .alt")]
    check("cards mark the alternative lines", alts == ["or Arcane", "or Skirmishing"], str(alts))

    # a Revenant: skills from the active legend, legends shown; a Ranger: pets shown
    driver.get(BASE + "/builds/ow-power-vindicator")
    wait.until(lambda d: count(".traitline") == 3)
    names = [f.text for f in driver.find_elements(By.CSS_SELECTOR, ".skill figcaption")]
    check("revenant skills come from the active legend",
          "Selfish Spirit" in names and "Spear of Archemorus" in names, str(names))
    legends = [c.text for c in driver.find_elements(By.CSS_SELECTOR, ".companions .companion")]
    check("legends shown under the skills", legends == ["Alliance", "Assassin"], str(legends))
    driver.get(BASE + "/builds/support-druid")
    wait.until(lambda d: count(".traitline") == 4)
    pets = [c.text for c in driver.find_elements(By.CSS_SELECTOR, ".companions .companion")]
    check("pets shown under the skills", pets == ["Fanged Iboga", "Jungle Stalker"], str(pets))
    driver.get(BASE + "/builds/ow-event-power-scrapper")
    wait.until(lambda d: count(".traitline") == 4)
    check("every tier chosen: nine majors in the build's lines plus three in the Alchemy alternative",
          count(".major.selected") == 12, str(count(".major.selected")))

    # unknown build
    driver.get(BASE + "/builds/does-not-exist")
    wait.until(lambda d: count(".not-found") == 1)
    check("unknown slug says so", True)

    # the optimizer link restores the panel and optimizes
    driver.get(optimizer_link)
    wait.until(lambda d: visible(d, "main"))
    wait.until(lambda d: visible(d, "result"), "the optimizer did not produce a result")
    expected = len(optimizer_link.split("traits=")[1].split("&")[0].split("%2C"))
    checked = count("#trait-groups input:checked")
    check("optimizer link ticks the build's traits", checked == expected, f"{checked} vs {expected}")
    check("optimizer link sets 3-stat gear",
          driver.find_element(By.CSS_SELECTOR, "#env-choice button.active").get_attribute("data-value") == "3p")
    check("optimizer link sets the two-handed weapon (greatsword first)",
          driver.find_element(By.CSS_SELECTOR, "#weapon-choice button.active").get_attribute("data-value") == "2h")
    check("optimizer link unticks stacking sigils",
          not driver.find_element(By.ID, "opt-stacking").is_selected())
    check("all pieces ascended", count("#slot-grid .slot-chip.asc") == count("#slot-grid .slot-chip"))
    check("URL normalized after loading", "traits=" not in driver.current_url, driver.current_url)
    # and the copy button exists next to the chat link button
    check("copy optimizer link button", count(".copy-link") == 2, str(count(".copy-link")))
finally:
    driver.quit()

finish()
