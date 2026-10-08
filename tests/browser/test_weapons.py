"""Weapon-gated traits, wielding chips, Evoker familiar, stowed stacking sigil."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _common import BASE, By, WebDriverWait, check, finish, make_driver, visible

driver = make_driver(1500, 1400)
wait = WebDriverWait(driver, 20)


def tick(name):
    for label in driver.find_elements(By.CSS_SELECTOR, "#trait-groups .trait"):
        if label.text.split("\n")[0].startswith(name):
            driver.execute_script("arguments[0].click()",
                                  label.find_element(By.CSS_SELECTOR, "input"))
            return


try:
    # Right-Hand Strength: aureus hint appears with a two-handed weapon
    driver.get(BASE + "/ceo?profession=Guardian&spec=Firebrand&mode=crit")
    wait.until(lambda d: len(d.find_elements(By.CSS_SELECTOR, "#trait-groups .trait-group")) > 0)
    hints = lambda: " ".join(h.text for h in driver.find_elements(
        By.CSS_SELECTOR, ".trait-condition:not(.hidden)"))
    check("RHS hint with 2h weapon", "two one-handed weapons" in hints(), hints())
    driver.find_element(By.CSS_SELECTOR, "#weapon-choice button[data-value='1h']").click()
    check("RHS hint clears with 1h", "two one-handed weapons" not in hints())
    driver.find_element(By.CSS_SELECTOR, "#weapon-choice button[data-value='2h']").click()

    # wielding chip + gear contradiction warning (Zealous Blade is greatsword)
    zealous = None
    for label in driver.find_elements(By.CSS_SELECTOR, "#trait-groups .trait"):
        if label.text.split("\n")[0].startswith("Zealous Blade"):
            zealous = label
    check("Zealous Blade listed", zealous is not None)
    tick("Zealous Blade")
    chips = [c for c in driver.find_elements(By.CSS_SELECTOR, ".variant-chip")
             if c.text == "Greatsword"]
    check("greatsword chip present and active", len(chips) == 1
          and "active" in str(chips[0].get_attribute("class")))
    warnings = lambda: driver.find_element(By.ID, "build-warnings").text
    check("no conflict with 2h gear", "needs a greatsword" not in warnings())
    driver.find_element(By.CSS_SELECTOR, "#weapon-choice button[data-value='1h']").click()
    check("conflict warning on 1h gear", "needs a greatsword" in warnings(), warnings())

    # Evoker: Enhanced Potency with the hare familiar chip
    driver.get(BASE + "/ceo?profession=Elementalist&spec=Evoker&mode=crit")
    wait.until(lambda d: len(d.find_elements(By.CSS_SELECTOR, "#trait-groups .trait-group")) > 0)
    text = driver.find_element(By.ID, "trait-groups").text

    # the chosen elite line's minor traits start ticked, core minors do not
    def minors_checked(group_name):
        for group in driver.find_elements(By.CSS_SELECTOR, "#trait-groups .trait-group"):
            if group.find_element(By.CSS_SELECTOR, ".trait-group-header .name").text == group_name:
                labels = [l for l in group.find_elements(By.CSS_SELECTOR, ".trait")
                          if l.find_element(By.CSS_SELECTOR, ".slot-tag").text.lower() == "minor"]
                return [l.find_element(By.CSS_SELECTOR, "input").is_selected() for l in labels]
        return None
    evoker_minors = minors_checked("Evoker")
    check("elite minors auto-ticked", bool(evoker_minors) and all(evoker_minors), str(evoker_minors))
    fire_minors = minors_checked("Fire")
    check("core minors stay unticked", fire_minors is not None and not any(fire_minors), str(fire_minors))
    check("Enhanced Potency listed", "Enhanced Potency" in text)
    check("familiar caption", "familiar:" in text, text[:400])
    chips = {c.text: c for c in driver.find_elements(
        By.XPATH, "//label[.//span[contains(text(),'Enhanced Potency')]]"
        "/following-sibling::div[contains(@class,'trait-options')][1]//button")}
    check("familiars in element order fire/water/air/earth",
          list(chips) == ["Fox", "Otter", "Hare", "Toad"], str(list(chips)))
    check("hare chip default active", "active" in str(chips["Hare"].get_attribute("class")))
    # radio behaviour: picking another familiar replaces the hare
    potency = driver.find_element(By.XPATH, "//label[.//span[contains(text(),'Enhanced Potency')]]/input")
    check("Enhanced Potency (an Evoker minor) starts ticked", potency.is_selected())
    if not potency.is_selected():
        potency.click()  # the warning needs the trait ticked
    chips["Toad"].click()
    check("toad replaces hare", "active" in str(chips["Toad"].get_attribute("class"))
          and "active" not in str(chips["Hare"].get_attribute("class")))
    check("no-bonus familiar warns", "contributes nothing"
          in driver.find_element(By.ID, "build-warnings").text,
          driver.find_element(By.ID, "build-warnings").text)
    chips["Toad"].click()
    check("clicking the active familiar keeps it", "active" in str(chips["Toad"].get_attribute("class")))
    chips["Hare"].click()
    check("hare selectable again, warning gone",
          "active" in str(chips["Hare"].get_attribute("class"))
          and "contributes nothing" not in driver.find_element(By.ID, "build-warnings").text)

    # Thief: Revealed Training's revealed state is a yes/no radio
    driver.get(BASE + "/ceo?profession=Thief&spec=Deadeye&mode=crit")
    wait.until(lambda d: len(d.find_elements(By.CSS_SELECTOR, "#trait-groups .trait-group")) > 0)
    row = "//label[.//span[contains(text(),'Revealed Training')]]"
    state = {c.text: c for c in driver.find_elements(
        By.XPATH, row + "/following-sibling::div[contains(@class,'trait-options')][1]//button")}
    check("revealed state chips", list(state) == ["Revealed", "Not revealed"], str(list(state)))
    check("revealed is the default", "active" in str(state["Revealed"].get_attribute("class")))
    driver.find_element(By.XPATH, row + "/input").click()
    state["Not revealed"].click()
    check("not revealed replaces revealed",
          "active" in str(state["Not revealed"].get_attribute("class"))
          and "active" not in str(state["Revealed"].get_attribute("class")))
    check("no warning for an explicit 'not revealed'",
          "contributes nothing" not in driver.find_element(By.ID, "build-warnings").text,
          driver.find_element(By.ID, "build-warnings").text)

    def chips_of(trait):
        return {c.text: c for c in driver.find_elements(
            By.XPATH, f"//label[.//span[contains(text(),'{trait}')]]"
            "/following-sibling::div[contains(@class,'trait-options')][1]//button")}
    keen = chips_of("Keen Observer")
    check("Keen Observer health chips", list(keen) == ["Above 50% health", "Below 50% health"], str(list(keen)))
    check("above 50% health is the default", "active" in str(keen["Above 50% health"].get_attribute("class")))
    fangs = chips_of("Twin Fangs")
    check("Twin Fangs target chips", list(fangs) == ["Flanking or defiant", "From the front"], str(list(fangs)))
    fangs["From the front"].click()
    check("from the front replaces flanking",
          "active" in str(fangs["From the front"].get_attribute("class"))
          and "active" not in str(fangs["Flanking or defiant"].get_attribute("class")))

    driver.get(BASE + "/ceo?profession=Elementalist&spec=Evoker&mode=crit")
    wait.until(lambda d: len(d.find_elements(By.CSS_SELECTOR, "#trait-groups .trait-group")) > 0)
    # Crescent Wind (hammer air 3): a weapon skill with a hammer wielding chip
    text = driver.find_element(By.ID, "trait-groups").text
    check("Crescent Wind listed for the Elementalist", "Crescent Wind" in text)
    headers = [h.text for h in driver.find_elements(By.CSS_SELECTOR, ".trait-group-header .name")]
    check("skill groups named Utility skills and Weapon skills",
          "Utility skills" in headers and headers[-1] == "Weapon skills", str(headers))
    cw = "//label[.//span[contains(text(),'Crescent Wind')]]"
    cw_box = driver.find_element(By.XPATH, cw + "/input")
    check("Crescent Wind unticked by default", not cw_box.is_selected())
    check("no wielding chip on a weapon skill", not driver.find_elements(
        By.XPATH, cw + "/following-sibling::div[contains(@class,'trait-options')][1]//button"))
    driver.execute_script("arguments[0].click()", cw_box)
    driver.find_element(By.CSS_SELECTOR, "#weapon-choice button[data-value='1h']").click()
    hint = driver.find_element(By.XPATH, cw + "//span[contains(@class,'trait-condition')]")
    check("Crescent Wind marked ineffective with two one-handed weapons",
          "needs a two-handed weapon" in hint.text and "hidden" not in hint.get_attribute("class"), hint.text)
    driver.find_element(By.CSS_SELECTOR, "#weapon-choice button[data-value='2h']").click()
    check("hint gone with a two-handed weapon", "hidden" in hint.get_attribute("class"))
    # the WvW toggle shows the split value and keeps the ticks
    row_text = lambda: driver.find_element(By.XPATH, cw).text
    check("PvE value shown", "+15% critical chance" in row_text(), row_text())
    driver.execute_script("arguments[0].click()", driver.find_element(By.ID, "opt-wvw"))
    wait.until(lambda d: "+12% critical chance" in d.find_element(By.XPATH, cw).text)
    check("WvW value shown with the toggle", "+12% critical chance" in row_text(), row_text())
    check("tick survives the re-render", driver.find_element(By.XPATH, cw + "/input").is_selected())
    driver.execute_script("arguments[0].click()", driver.find_element(By.ID, "opt-wvw"))
    wait.until(lambda d: "+15% critical chance" in d.find_element(By.XPATH, cw).text)

    # stowed stacking sigil: visible for Elementalist, three sigils in result
    check("stowed checkbox visible for ele", visible(driver, "stowed-label"))
    stowed = driver.find_element(By.ID, "opt-stowed")
    driver.execute_script("arguments[0].click()", stowed)
    driver.find_element(By.ID, "all-asc").click()
    driver.find_element(By.ID, "optimize").click()
    wait.until(lambda d: "hidden" not in str(d.find_element(By.ID, "result").get_attribute("class")))
    sigil_line = driver.find_element(By.ID, "result").text.split("Sigils")[1][:120]
    check("three sigils in result", sigil_line.count(" + ") >= 2, sigil_line)

    # hidden for professions with a weapon swap
    driver.get(BASE + "/ceo?profession=Guardian&spec=Firebrand&mode=crit")
    wait.until(lambda d: len(d.find_elements(By.CSS_SELECTOR, "#trait-groups .trait-group")) > 0)
    check("stowed checkbox shown for guardian too", visible(driver, "stowed-label"))
finally:
    driver.quit()

finish()
