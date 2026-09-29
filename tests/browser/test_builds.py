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

    # old optimizer deep links still work
    driver.get(BASE + "/?profession=Guardian&spec=Firebrand&mode=crit")
    wait.until(lambda d: visible(d, "main"))
    check("root deep link redirects to /ceo", "/ceo?" in driver.current_url, driver.current_url)

    # the list
    driver.get(BASE + "/builds")
    wait.until(lambda d: count(".build-card") == 2)
    check("two placeholder builds listed", count(".build-card") == 2)
    card = driver.find_element(By.CSS_SELECTOR, ".build-card")
    check("card row one: spec + profession",
          card.find_element(By.CSS_SELECTOR, ".card-spec").text == "Tempest"
          and card.find_element(By.CSS_SELECTOR, ".card-prof").text.lower() == "elementalist")
    check("card row two: weapons + trait lines",
          "Scepter / Warhorn" in card.find_element(By.CSS_SELECTOR, ".card-weapons").text
          and "Fire · Air · Tempest" in card.find_element(By.CSS_SELECTOR, ".card-lines").text)

    # category filter
    groups = driver.find_elements(By.CSS_SELECTOR, ".filter-group .control-label")
    check("profession filter comes first", groups[0].text.lower() == "profession", str([g.text for g in groups]))
    driver.find_element(By.CSS_SELECTOR, "#category-filter button[data-value='raid']").click()
    wait.until(lambda d: count(".build-card") == 1)
    check("raid filter keeps the chronomancer",
          driver.find_element(By.CSS_SELECTOR, ".card-spec").text == "Chronomancer")
    check("filter in URL", "cat=raid" in driver.current_url, driver.current_url)

    # profession dropdown: counts follow the category
    driver.find_element(By.ID, "profession-toggle").click()
    wait.until(lambda d: not d.find_element(By.ID, "profession-menu").get_attribute("class").count("hidden"))
    options = driver.find_elements(By.CSS_SELECTOR, "#profession-menu button")
    check("dropdown lists all nine professions plus 'all'", len(options) == 10, str(len(options)))
    names = [o.text.split("\n")[0] for o in options[1:]]
    check("dropdown in light/medium/heavy order", names == ["Elementalist", "Mesmer", "Necromancer", "Engineer", "Ranger", "Thief", "Guardian", "Revenant", "Warrior"], str(names))
    by_name = {o.text.split("\n")[0]: o for o in options}
    check("elementalist disabled under raid", not by_name["Elementalist"].is_enabled())
    check("mesmer shows its count", by_name["Mesmer"].text.endswith("1"), by_name["Mesmer"].text)
    by_name["Mesmer"].click()
    wait.until(lambda d: count(".build-card") == 1)
    check("profession in URL", "prof=Mesmer" in driver.current_url, driver.current_url)
    driver.find_element(By.CSS_SELECTOR, "#category-filter button[data-value='']").click()
    wait.until(lambda d: count(".build-card") == 1)
    check("all categories + mesmer still one card", count(".build-card") == 1)

    # the build page
    driver.find_element(By.CSS_SELECTOR, ".build-card").click()
    wait.until(lambda d: count(".traitline") == 3)
    check("detail URL", driver.current_url.endswith("/builds/raid-chronomancer"), driver.current_url)
    check("three trait lines", count(".traitline") == 3)
    check("nine minors, 27 majors", count(".minor") == 9 and count(".major") == 27,
          f"{count('.minor')} / {count('.major')}")
    check("nine chosen majors", count(".major.selected") == 9, str(count(".major.selected")))
    check("five connector lines per panel", count(".trait-lines line") == 15, str(count(".trait-lines line")))
    check("one art hexagon per panel", count(".traitline-hex") == 3)
    picks = [p.text for p in driver.find_elements(By.CSS_SELECTOR, ".traitline-picks")]
    check("chosen traits named", "Chronophantasma" in picks[2], picks[2])
    check("ten skills, land and underwater", count(".skill img") == 10, str(count(".skill img")))
    names = [f.text for f in driver.find_elements(By.CSS_SELECTOR, ".skill figcaption")]
    check("underwater row differs where the build does", "Mirror Images" in names, str(names))
    check("gear: 6 armor + 6 trinkets + 3 weapons", count(".gear-slot") == 15, str(count(".gear-slot")))
    check("gear shows the rune per armor piece",
          "Superior Rune of" in driver.find_element(By.CSS_SELECTOR, ".gear-column .gear-slot .gear-sub").text)
    check("character card with headline and derived effects",
          count(".character-headline") == 1 and count(".attribute") >= 4
          and count(".attribute .effect") >= 3)
    effects = [e.text for e in driver.find_elements(By.CSS_SELECTOR, ".attribute .effect")]
    check("crit chance and health derived", any("Critical chance" in e and "100.00%" in e for e in effects)
          and any("Health" in e for e in effects), str(effects))
    check("skin from the build file shows on the head slot",
          "Placeholder skin name" in driver.find_element(By.CSS_SELECTOR, ".gear-column .gear-slot").text)
    check("no gear warning", count(".gear-warning") == 0)
    labels = [d.text for d in driver.find_elements(By.CSS_SELECTOR, ".consumables dt")]
    check("consumables listed", {"Rune", "Relic", "Food", "Utility", "Infusions"} <= set(labels), str(labels))
    check("chat link shown", driver.find_element(By.CSS_SELECTOR, ".linkbox code").text.startswith("[&DQ"))
    optimizer_link = driver.find_element(By.CSS_SELECTOR, ".cta-link").get_attribute("href")
    check("optimizer link present", "/ceo?" in optimizer_link and "traits=" in optimizer_link)

    # back keeps the filters
    driver.find_element(By.CSS_SELECTOR, ".back-link").click()
    wait.until(lambda d: count(".build-card") == 1)
    check("back to filtered list", "prof=Mesmer" in driver.current_url, driver.current_url)

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
    check("optimizer link sets two one-handed weapons",
          driver.find_element(By.CSS_SELECTOR, "#weapon-choice button.active").get_attribute("data-value") == "1h")
    check("optimizer link unticks stacking sigils",
          not driver.find_element(By.ID, "opt-stacking").is_selected())
    check("all pieces ascended", count("#slot-grid .slot-chip.asc") == count("#slot-grid .slot-chip"))
    check("URL normalized after loading", "traits=" not in driver.current_url, driver.current_url)
    # and the copy button exists next to the chat link button
    check("copy optimizer link button", count(".copy-link") == 2, str(count(".copy-link")))
finally:
    driver.quit()

finish()
