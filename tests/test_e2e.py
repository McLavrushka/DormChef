"""End-to-end Selenium tests for DormChef Streamlit UI.

Prerequisites:
    - Backend running on http://localhost:8000
    - Frontend running on http://localhost:8501
    - Chrome + chromedriver installed

Run:
    poetry run pytest tests/test_e2e.py -v
"""

from __future__ import annotations

import time

import pytest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

FRONTEND_URL = "http://localhost:8501"
WAIT_TIMEOUT = 15


@pytest.fixture(scope="module")
def driver():
    """Create a headless Chrome driver for the test session."""
    opts = Options()
    opts.add_argument("--headless")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    browser = webdriver.Chrome(options=opts)
    browser.implicitly_wait(5)
    yield browser
    browser.quit()


def _wait_for_streamlit(driver: webdriver.Chrome) -> None:
    """Wait until Streamlit app is fully loaded."""
    WebDriverWait(driver, WAIT_TIMEOUT).until(
        EC.presence_of_element_located(
            (By.CSS_SELECTOR, "[data-testid='stAppViewContainer']"),
        ),
    )


def _click_sidebar_page(driver: webdriver.Chrome, label: str) -> None:
    """Click a radio option in the sidebar."""
    sidebar = driver.find_element(
        By.CSS_SELECTOR, "[data-testid='stSidebar']",
    )
    options = sidebar.find_elements(By.TAG_NAME, "label")
    for option in options:
        if label.lower() in option.text.lower():
            option.click()
            time.sleep(1)
            return
    raise ValueError(f"Sidebar option '{label}' not found")


# ------------------------------------------------------------------
# E2E 1: Add a recipe via the form
# ------------------------------------------------------------------

def test_add_recipe_via_form(driver: webdriver.Chrome) -> None:
    """Fill and submit the 'Add recipe' form, verify success."""
    driver.get(FRONTEND_URL)
    _wait_for_streamlit(driver)
    _click_sidebar_page(driver, "Add recipe")
    time.sleep(1)

    title_input = driver.find_element(
        By.CSS_SELECTOR,
        "input[aria-label='Title']",
    )
    title_input.clear()
    title_input.send_keys("Selenium Pasta")

    textareas = driver.find_elements(By.TAG_NAME, "textarea")
    # Description
    textareas[0].send_keys("E2E test recipe")
    # Ingredients
    textareas[1].send_keys("pasta\nsalt\nwater")
    # Steps
    textareas[2].send_keys("Boil water\nCook pasta\nDrain")

    submit = driver.find_element(
        By.CSS_SELECTOR,
        "button[kind='secondaryFormSubmit']",
    )
    submit.click()

    WebDriverWait(driver, WAIT_TIMEOUT).until(
        EC.presence_of_element_located(
            (By.XPATH, "//*[contains(text(), 'Recipe created')]"),
        ),
    )


# ------------------------------------------------------------------
# E2E 2: Search for a recipe by ingredient
# ------------------------------------------------------------------

def test_search_recipe_by_ingredient(driver: webdriver.Chrome) -> None:
    """Search by ingredient and verify results appear."""
    driver.get(FRONTEND_URL)
    _wait_for_streamlit(driver)
    _click_sidebar_page(driver, "Search by ingredients")
    time.sleep(1)

    search_input = driver.find_element(
        By.CSS_SELECTOR,
        "input[aria-label='Ingredients']",
    )
    search_input.clear()
    search_input.send_keys("pasta")

    search_btn = driver.find_element(
        By.XPATH,
        "//button[contains(., 'Search')]",
    )
    search_btn.click()

    WebDriverWait(driver, WAIT_TIMEOUT).until(
        EC.presence_of_element_located(
            (By.XPATH, "//*[contains(text(), 'matching recipe')]"),
        ),
    )
