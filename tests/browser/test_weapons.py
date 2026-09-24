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
    check("Enhanced Potency listed", "Enhanced Potency" in text)
    check("familiar caption", "familiar:" in text, text[:400])
    chips = {c.text: c for c in driver.find_elements(
        By.XPATH, "//label[.//span[contains(text(),'Enhanced Potency')]]"
        "/following-sibling::div[contains(@class,'trait-options')][1]//button")}
    check("familiars in element order fire/water/air/earth",
          list(chips) == ["Fox", "Otter", "Hare", "Toad"], str(list(chips)))
    check("hare chip default active", "active" in str(chips["Hare"].get_attribute("class")))
    # radio behaviour: picking another familiar replaces the hare
    driver.find_element(By.XPATH, "//label[.//span[contains(text(),'Enhanced Potency')]]"
                        "/input").click()  # tick the trait so the warning can appear
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
    check("stowed checkbox hidden for guardian", not visible(driver, "stowed-label"))
finally:
    driver.quit()

finish()
