from scraper.session_handler import init_driver

if __name__ == "__main__":
    driver = init_driver()
    driver.get("https://example.com")
    print("Page title is:", driver.title)
    driver.quit()
