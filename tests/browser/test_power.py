"""The max-effective-power mode and percentage traits."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _common import BASE, By, WebDriverWait, check, finish, make_driver, visible

driver = make_driver(1500, 1200)
wait = WebDriverWait(driver, 15)

try:
    driver.get(BASE + "/ceo?profession=Elementalist&spec=Catalyst")
    wait.until(lambda d: visible(d, "main"))
    wait.until(lambda d: len(d.find_elements(By.CSS_SELECTOR, "#trait-groups .trait-group")) > 0)
    boxes = {}
    for label in driver.find_elements(By.CSS_SELECTOR, "#trait-groups .trait"):
        if "Empowerment" in label.text.split("\n")[0]:
            boxes[label.text.split("\n")[0]] = label.find_element(
                By.CSS_SELECTOR, "input[type=checkbox]")
    check("percentage traits enabled", len(boxes) >= 2
          and all(b.is_enabled() for b in boxes.values()), str(len(boxes)))
    for box in boxes.values():
        driver.execute_script("arguments[0].click()", box)
    driver.find_element(By.ID, "all-asc").click()
    driver.find_element(By.ID, "optimize").click()
    wait.until(lambda d: visible(d, "result"))
    text = driver.find_element(By.ID, "result").text
    check("catalyst crit build solves", "effective power at 100% crit" in text.lower())

    driver.find_element(By.CSS_SELECTOR, "#mode-choice button[data-value='power']").click()
    check("power: env row visible", visible(driver, "row-env"))
    check("power: K row hidden", not visible(driver, "row-ranking"))
    check("power: herald hidden", not visible(driver, "herald-label"))
    check("power: writs visible", visible(driver, "writs-label"))
    driver.find_element(By.ID, "optimize").click()
    wait.until(lambda d: "critical chance" in d.find_element(By.ID, "result").text.lower())
    text = driver.find_element(By.ID, "result").text
    check("power result shows crit% caption", "% critical chance" in text.lower())
    check("power result has crit chance fact", "wherever effective power peaks" in text)
    check("power result no cap warning", "out of reach" not in text and "overcapping" not in text)

    # WvW pins the Brawler rune in both crit-stat modes
    check("wvw checkbox shown in power mode", visible(driver, "wvw-label"))
    driver.execute_script("arguments[0].click()", driver.find_element(By.ID, "opt-wvw"))
    driver.find_element(By.ID, "optimize").click()
    wait.until(lambda d: "brawler" in d.find_element(By.ID, "result").text.lower())
    check("wvw: brawler rune in the power result", "Brawler" in driver.find_element(By.ID, "result").text)
    driver.find_element(By.CSS_SELECTOR, "#mode-choice button[data-value='crit']").click()
    driver.find_element(By.ID, "optimize").click()
    wait.until(lambda d: "brawler" in d.find_element(By.ID, "result").text.lower())
    check("wvw: brawler rune in the crit result", "Brawler" in driver.find_element(By.ID, "result").text)
    driver.find_element(By.CSS_SELECTOR, "#mode-choice button[data-value='boon']").click()
    check("wvw checkbox hidden in boon mode", not visible(driver, "wvw-label"))
    driver.find_element(By.CSS_SELECTOR, "#mode-choice button[data-value='power']").click()
    driver.execute_script("arguments[0].click()", driver.find_element(By.ID, "opt-wvw"))
    check("power equipment renders", "Shoulders/Gloves/Boots" in text)
finally:
    driver.quit()

finish()
