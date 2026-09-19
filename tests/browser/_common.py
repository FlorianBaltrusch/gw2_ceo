"""Shared plumbing for the browser click-through suites.

Run a local server first (any port), then e.g.:
    CEO_BASE=http://127.0.0.1:5028 .venv/bin/python tests/browser/test_boon.py

Needs Firefox plus a geckodriver binary; the driver is looked up via
$GECKODRIVER, falling back to /tmp/geckodriver (download: github.com/mozilla/
geckodriver/releases, untar, chmod +x). Selenium comes from the venv and is
deliberately not part of requirements.txt (dev-only).
"""

import os
import sys

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.support.ui import WebDriverWait  # noqa: F401

BASE = os.environ.get("CEO_BASE", "http://127.0.0.1:5001")
failures: list[str] = []


def check(name, condition, detail=""):
    print(f"{'PASS' if condition else 'FAIL'}  {name}"
          + (f"  [{detail}]" if detail and not condition else ""))
    if not condition:
        failures.append(name)


def make_driver(width=1500, height=1300):
    options = Options()
    options.add_argument("--headless")
    options.set_preference("ui.prefersReducedMotion", 1)
    service = Service(os.environ.get("GECKODRIVER", "/tmp/geckodriver"))
    driver = webdriver.Firefox(options=options, service=service)
    driver.set_window_size(width, height)
    return driver


def visible(driver, element_id):
    return "hidden" not in driver.find_element(By.ID, element_id).get_attribute("class")


def finish():
    print()
    if failures:
        print(f"{len(failures)} FAILURES: {failures}")
        sys.exit(1)
    print("ALL CHECKS PASSED")
