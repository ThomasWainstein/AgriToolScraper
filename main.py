import os
import time
from typing import List

from bs4 import BeautifulSoup
from tqdm import tqdm
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By


START_URL = "https://www.franceagrimer.fr/Accompagner/Dispositifs-par-filiere/Aides-nationales"


def init_driver(headless: bool = True) -> webdriver.Chrome:
    """Initialize a Chrome webdriver using the bundled chromedriver."""

    options = Options()
    if headless:
        # use the newer headless mode which is more stable
        options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    # Large window to avoid hidden pagination buttons
    options.add_argument("--window-size=1920,1080")

    service = Service(executable_path="./chromedriver/chromedriver")
    driver = webdriver.Chrome(service=service, options=options)
    return driver


def extract_links(page_source: str) -> List[str]:
    """Extract potential subsidy detail page links from HTML source."""

    soup = BeautifulSoup(page_source, "lxml")
    links: List[str] = []
    for a in soup.select("a[href]"):
        href = a.get("href")
        if not href or href.startswith("javascript:") or href.startswith("#"):
            continue

        # Convert relative URLs to absolute
        if href.startswith("/"):
            href = "https://www.franceagrimer.fr" + href

        if href.startswith("https://www.franceagrimer.fr") and "Aides-nationales" not in href:
            # Heuristic filter for detail pages
            if "Accompagner" in href:
                links.append(href)

    return links


def find_next(driver: webdriver.Chrome):
    """Return the WebElement for the next page button or None."""

    selectors = [
        "a[rel='next']",
        ".pagination a.next",
        "li.next a",
        "a.next",
        "button[rel='next']",
    ]

    for sel in selectors:
        elems = driver.find_elements(By.CSS_SELECTOR, sel)
        if elems:
            btn = elems[0]
            if "disabled" in (btn.get_attribute("class") or "").lower():
                return None
            return btn
    return None


def main() -> None:
    driver = init_driver(headless=True)
    all_links: List[str] = []

    try:
        driver.get(START_URL)
        time.sleep(2)

        page_count = 1
        pbar = tqdm(total=0, position=0, leave=True)

        while True:
            pbar.set_description(f"Page {page_count}")

            links = extract_links(driver.page_source)
            all_links.extend(links)
            pbar.update(len(links))

            next_btn = find_next(driver)
            if not next_btn:
                break

            try:
                driver.execute_script("arguments[0].click();", next_btn)
            except Exception:
                next_btn.click()

            time.sleep(2)
            page_count += 1

    finally:
        driver.quit()

    # Remove duplicates while preserving order
    seen = set()
    unique_links = []
    for url in all_links:
        if url not in seen:
            seen.add(url)
            unique_links.append(url)

    print(f"Total URLs collected: {len(unique_links)}")

    os.makedirs("data", exist_ok=True)
    with open("data/raw_urls.txt", "w") as f:
        for url in unique_links:
            f.write(url + "\n")


if __name__ == "__main__":
    main()

