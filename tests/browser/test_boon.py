"""Boon mode: trait filtering, controls, result rendering, crit regression."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _common import BASE, By, WebDriverWait, check, finish, make_driver, visible

driver = make_driver(1500, 1100)
wait = WebDriverWait(driver, 15)

try:
    driver.get(BASE + "/?profession=Guardian&spec=Firebrand")
    wait.until(lambda d: visible(d, "main"))
    wait.until(lambda d: len(d.find_elements(By.CSS_SELECTOR, "#trait-groups .trait-group")) > 0)

    trait_names = lambda: {e.text for e in driver.find_elements(
        By.CSS_SELECTOR, "#trait-groups .trait-name")}
    crit_traits = trait_names()
    check("crit mode lists Righteous Instincts", any("Righteous Instincts" in t for t in crit_traits))
    check("crit mode hides Honorable Staff", not any("Honorable Staff" in t for t in crit_traits))
    check("crit: env row visible", visible(driver, "row-env"))
    check("crit: herald hidden", not visible(driver, "herald-label"))

    driver.find_element(By.CSS_SELECTOR, "#mode-choice button[data-value='boon']").click()
    wait.until(lambda d: not visible(d, "row-env"))
    boon_traits = trait_names()
    check("boon mode lists Honorable Staff", any("Honorable Staff" in t for t in boon_traits))
    check("boon mode lists Signet of Mercy", any("Signet of Mercy" in t for t in boon_traits))
    check("boon mode lists Imbued Haste", any("Imbued Haste" in t for t in boon_traits))
    check("boon mode hides Righteous Instincts", not any("Righteous Instincts" in t for t in boon_traits))
    check("boon: fury hidden", not visible(driver, "fury-label"))
    check("boon: writs hidden", not visible(driver, "writs-label"))
    check("boon: pie hidden", not visible(driver, "pie-label"))
    check("boon: herald visible", visible(driver, "herald-label"))
    check("boon: oils label", driver.find_element(By.ID, "utility-name").text == "Maintenance oils")

    for label in driver.find_elements(By.CSS_SELECTOR, "#trait-groups .trait"):
        if "Honorable Staff" in label.text or "Signet of Mercy" in label.text:
            box = label.find_element(By.CSS_SELECTOR, "input[type=checkbox]")
            driver.execute_script("arguments[0].click()", box)
    driver.find_element(By.ID, "all-asc").click()
    driver.find_element(By.ID, "optimize").click()
    wait.until(lambda d: visible(d, "result"))
    result = driver.find_element(By.ID, "result")
    wait.until(lambda d: "boon duration" in result.text.lower())
    text = result.text
    check("boon result shows healing caption", "healing power at 100% boon duration" in text.lower())
    check("boon result shows Harrier's or Magi's", "Harrier's" in text or "Magi's" in text)
    check("boon result shows a sigil pair", " + " in text.split("Sigils")[1][:90])
    check("boon result shows outgoing total", "Outgoing healing" in text)
    check("boon result shows concentration stat", "Concentration" in text)
    note = driver.find_elements(By.CSS_SELECTOR, ".rank-note")
    check("ranking note present", len(note) == 1 and "ranked by" in note[0].text.lower())

    inner_tabs = driver.find_elements(By.CSS_SELECTOR, "#result .result-tabs button")
    if inner_tabs:
        check("backup tab labeled", any("backup" in t.text.lower() for t in inner_tabs))
        for tab in inner_tabs:
            if "backup" in tab.text.lower():
                tab.click()
                break
        check("backup pane explains itself", "keeps 100% boon duration"
              in driver.find_element(By.ID, "result").text)

    box = driver.find_element(By.ID, "opt-herald")
    driver.execute_script("arguments[0].click()", box)
    driver.find_element(By.ID, "optimize").click()
    wait.until(lambda d: visible(d, "result"))
    wait.until(lambda d: "Herald" not in d.find_element(By.ID, "result").text)
    check("herald excluded when unticked", "Herald" not in driver.find_element(By.ID, "result").text)

    driver.find_element(By.CSS_SELECTOR, "#mode-choice button[data-value='crit']").click()
    wait.until(lambda d: visible(d, "row-env"))
    check("crit traits restored", any("Righteous Instincts" in t for t in trait_names()))
    driver.find_element(By.ID, "optimize").click()
    wait.until(lambda d: "effective power at 100% crit" in d.find_element(By.ID, "result").text.lower())
    check("crit result renders again", True)
finally:
    driver.quit()

finish()
