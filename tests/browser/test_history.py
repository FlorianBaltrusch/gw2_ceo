"""History navigation including the optimizer mode in the URL."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _common import BASE, By, WebDriverWait, check, finish, make_driver, visible
from selenium.common.exceptions import TimeoutException

driver = make_driver(1500, 1100)
wait = WebDriverWait(driver, 15)


def wait_url(fragment, absent=None, timeout=10):
    try:
        WebDriverWait(driver, timeout).until(
            lambda d: fragment in d.current_url
            and (absent is None or absent not in d.current_url))
        return True
    except TimeoutException:
        return False


try:
    driver.get(BASE + "/")
    wait.until(lambda d: len(d.find_elements(By.CSS_SELECTOR, "#prof-grid .prof-char")) == 9)
    check("landing URL clean", "?" not in driver.current_url)
    driver.find_element(By.XPATH, "//button[contains(@class,'prof-char')][.//span[text()='Guardian']]").click()
    check("profession in URL", wait_url("?profession=Guardian"))
    wait.until(lambda d: any(e.text == "Firebrand" for e in d.find_elements(By.CSS_SELECTOR, "#spec-grid .name")))
    driver.find_element(By.XPATH, "//button[contains(@class,'spec-tile')][.//span[text()='Firebrand']]").click()
    check("spec in URL", wait_url("spec=Firebrand"))
    wait.until(lambda d: visible(d, "main"))
    check("crit URL carries mode=crit", wait_url("mode=crit"))

    driver.find_element(By.CSS_SELECTOR, "#mode-choice button[data-value='boon']").click()
    check("boon mode in URL", wait_url("mode=boon"))
    check("boon controls shown", visible(driver, "herald-label"))
    driver.back()
    check("back returns to mode=crit", wait_url("mode=crit", absent="mode=boon"))
    wait.until(lambda d: visible(d, "row-env"))
    check("back restores crit controls", visible(driver, "row-env"))
    driver.forward()
    check("forward restores boon", wait_url("mode=boon"))
    wait.until(lambda d: not visible(d, "row-env"))

    driver.back()
    driver.back()
    check("back to spec picker URL", wait_url("?profession=Guardian", absent="spec="))
    wait.until(lambda d: visible(d, "spec-picker"))
    driver.back()
    wait.until(lambda d: visible(d, "profession-picker"))
    check("back to landing", "?" not in driver.current_url)

    driver.get(BASE + "/?profession=Elementalist&spec=Catalyst&mode=power")
    wait.until(lambda d: visible(d, "main"))
    wait.until(lambda d: len(d.find_elements(By.CSS_SELECTOR, "#trait-groups .trait-group")) > 0)
    active = driver.find_element(By.CSS_SELECTOR, "#mode-choice button.active")
    check("deep link activates power mode", active.get_attribute("data-value") == "power")
    check("power: K row hidden", not visible(driver, "row-ranking"))
    check("power: env row shown", visible(driver, "row-env"))

    driver.get(BASE + "/?profession=Ranger&spec=Druid&mode=boon")
    wait.until(lambda d: visible(d, "main"))
    wait.until(lambda d: not visible(d, "row-env"))
    active = driver.find_element(By.CSS_SELECTOR, "#mode-choice button.active")
    check("deep link activates boon mode", active.get_attribute("data-value") == "boon")
    check("boon traits filtered", "Lingering Magic" in driver.find_element(By.ID, "trait-groups").text)

    driver.find_element(By.ID, "change-selection").click()
    check("Change pushes clean URL", wait_url(BASE, absent="profession="))
    driver.back()
    check("browser back returns to boon builder", wait_url("mode=boon"))
    wait.until(lambda d: visible(d, "main"))
finally:
    driver.quit()

finish()
