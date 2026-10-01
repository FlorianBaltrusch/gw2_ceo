"""Ascended-food checkbox, tank toggle, fire-attunement variant chips."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _common import BASE, By, WebDriverWait, check, finish, make_driver

driver = make_driver(1500, 1400)
wait = WebDriverWait(driver, 20)
result = lambda: driver.find_element(By.ID, "result").text

try:
    driver.get(BASE + "/ceo?profession=Guardian&spec=Firebrand&mode=boon")
    wait.until(lambda d: len(d.find_elements(By.CSS_SELECTOR, "#trait-groups .trait-group")) > 0)
    check("ascended-food checkbox visible", "hidden" not in str(driver.find_element(
        By.ID, "ascended-food-label").get_attribute("class")))
    driver.find_element(By.ID, "all-asc").click()
    box = driver.find_element(By.ID, "opt-ascended-food")
    driver.execute_script("arguments[0].click()", box)
    driver.find_element(By.ID, "optimize").click()
    wait.until(lambda d: "hidden" not in str(d.find_element(By.ID, "result").get_attribute("class")))
    check("non-ascended food in result", "Rice Ball" in result() or "Eggs Benedict" in result(),
          result()[:400])
    driver.execute_script("arguments[0].click()", box)

    tank = driver.find_element(By.ID, "opt-tank")
    driver.execute_script("arguments[0].click()", tank)
    driver.find_element(By.ID, "optimize").click()
    wait.until(lambda d: "Giver's" in result() or "TOUGHNESS" in result().upper())
    text = result()
    check("tank result uses Giver's", "Giver's" in text, text[-600:])
    check("tank grid shows toughness", "TOUGHNESS" in text.upper())

    driver.get(BASE + "/ceo?profession=Elementalist&spec=Tempest&mode=crit")
    wait.until(lambda d: len(d.find_elements(By.CSS_SELECTOR, "#trait-groups .trait-group")) > 0)
    fire_chips = [c for c in driver.find_elements(By.CSS_SELECTOR, ".variant-chip")
                  if c.text == "Fire"]
    check("fire chips on both fire traits", len(fire_chips) == 2, str(len(fire_chips)))
    check("fire chips default active",
          all("active" in str(c.get_attribute("class")) for c in fire_chips))
    for label in driver.find_elements(By.CSS_SELECTOR, "#trait-groups .trait"):
        name = label.text.split("\n")[0]
        if name.startswith(("Power Overwhelming", "Empowering Flame")):
            driver.execute_script("arguments[0].click()",
                                  label.find_element(By.CSS_SELECTOR, "input"))
    driver.find_element(By.ID, "all-asc").click()
    driver.find_element(By.ID, "optimize").click()
    wait.until(lambda d: "hidden" not in str(d.find_element(By.ID, "result").get_attribute("class")))
    ep_fire = driver.find_element(By.CSS_SELECTOR, "#result .ep .value").text
    for chip in fire_chips:
        chip.click()
    driver.find_element(By.ID, "optimize").click()
    wait.until(lambda d: d.find_element(By.CSS_SELECTOR, "#result .ep .value").text != ep_fire)
    ep_nofire = driver.find_element(By.CSS_SELECTOR, "#result .ep .value").text
    check("fire attunement changes EP",
          int(ep_nofire.replace(",", "")) < int(ep_fire.replace(",", "")),
          f"{ep_nofire} vs {ep_fire}")
    warnings = driver.find_element(By.ID, "build-warnings").text
    check("unattuned fire traits warned", "no attunement option is chosen" in warnings, warnings)
finally:
    driver.quit()

finish()
