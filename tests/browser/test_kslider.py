"""The K slider and skill picker in boon mode."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _common import BASE, By, WebDriverWait, check, finish, make_driver, visible

driver = make_driver(1500, 1200)
wait = WebDriverWait(driver, 15)


def set_slider(value):
    driver.execute_script("""
      const s = document.getElementById('k-slider');
      s.value = arguments[0];
      s.dispatchEvent(new Event('input'));
      s.dispatchEvent(new Event('change'));
    """, value)


try:
    driver.get(BASE + "/?profession=Ranger&spec=Druid")
    wait.until(lambda d: visible(d, "main"))
    wait.until(lambda d: len(d.find_elements(By.CSS_SELECTOR, "#trait-groups .trait-group")) > 0)
    check("crit: slider row hidden", not visible(driver, "row-ranking"))

    driver.find_element(By.CSS_SELECTOR, "#mode-choice button[data-value='boon']").click()
    wait.until(lambda d: visible(d, "row-ranking"))
    check("default label = healing power",
          "healing power" in driver.find_element(By.ID, "k-label").text)

    driver.find_element(By.ID, "all-asc").click()
    driver.find_element(By.ID, "optimize").click()
    wait.until(lambda d: visible(d, "result"))
    result = lambda: driver.find_element(By.ID, "result").text
    check("result notes healing ranking", "ranked by healing power" in result().lower())

    set_slider(100)
    wait.until(lambda d: "ranked by outgoing healing" in result().lower())
    check("right edge re-optimizes to outgoing", True)

    set_slider(50)
    wait.until(lambda d: "ranked by effective healing at k" in result().lower())
    check("middle position ranks by K", True)
    check("K label shows value", "K = " in driver.find_element(By.ID, "k-label").text)

    driver.find_element(By.ID, "k-from-skill").click()
    wait.until(lambda d: visible(d, "skill-popup"))
    rows = driver.find_elements(By.CSS_SELECTOR, "#skill-list .skill-row")
    texts = [r.text for r in rows]
    check("popup lists skills", len(rows) > 10, f"{len(rows)} rows")
    check("popup has Regeneration", any("Regeneration" in t for t in texts))
    check("popup has Cosmic Ray", any("Cosmic Ray" in t for t in texts))
    target = next(r for r in rows if "Cosmic Ray" in r.text)
    target.click()
    wait.until(lambda d: not visible(d, "skill-popup"))
    label = driver.find_element(By.ID, "k-label").text
    check("picked skill in label", "Cosmic Ray" in label and "493" in label, label)
    wait.until(lambda d: "k = 493" in result().lower())
    check("re-optimized with skill K", True)

    tabs = driver.find_elements(By.CSS_SELECTOR, "#result .result-tabs button")
    if tabs:
        for tab in tabs:
            if "backup" in tab.text.lower():
                tab.click()
                break
        check("backup mentions downstate reason",
              "kill stacks vanish on downstate" in result().lower())
finally:
    driver.quit()

finish()
