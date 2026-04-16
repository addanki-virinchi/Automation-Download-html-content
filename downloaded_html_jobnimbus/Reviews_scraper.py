import argparse
import csv
import re
import time
from typing import List, Dict, Optional

import undetected_chromedriver as uc
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


DEFAULT_BASE_URL = "https://www.trustpilot.com/review/jobnimbus.com?page={page}"


def _extract_star_rating(card) -> Optional[int]:
    rating_attr = card.select_one("[data-service-review-rating]")
    if rating_attr and rating_attr.has_attr("data-service-review-rating"):
        try:
            return int(rating_attr["data-service-review-rating"])
        except ValueError:
            pass

    alt_img = card.select_one("img[alt*='out of 5']")
    if alt_img and alt_img.has_attr("alt"):
        match = re.search(r"Rated\s+(\d)\s+out of 5", alt_img["alt"])
        if match:
            return int(match.group(1))

    return None


def _extract_review_text(card) -> str:
    title = card.select_one("[data-service-review-title-typography]")
    body = card.select_one("[data-service-review-text-typography]")
    title_text = title.get_text(strip=True) if title else ""
    body_text = body.get_text(" ", strip=True) if body else ""

    if title_text and body_text:
        return f"{title_text} - {body_text}"
    if body_text:
        return body_text
    return title_text


def _extract_reviews(html: str) -> List[Dict[str, str]]:
    soup = BeautifulSoup(html, "html.parser")
    cards = soup.select("article[data-service-review-card-paper='true']")
    results: List[Dict[str, str]] = []

    for card in cards:
        name_el = card.select_one("[data-consumer-name-typography]")
        country_el = card.select_one("[data-consumer-country-typography]")

        name = name_el.get_text(strip=True) if name_el else ""
        region = country_el.get_text(strip=True) if country_el else ""
        review = _extract_review_text(card)
        stars = _extract_star_rating(card)

        results.append(
            {
                "name": name,
                "region": region,
                "review": review,
                "stars": "" if stars is None else str(stars),
            }
        )

    return results


def _build_driver(headless: bool) -> uc.Chrome:
    options = uc.ChromeOptions()
    if headless:
        options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    return uc.Chrome(options=options)


def _get_page_html(url: str, headless: bool) -> str:
    driver = _build_driver(headless)
    try:
        driver.get(url)
        WebDriverWait(driver, 20).until(
            EC.presence_of_all_elements_located(
                (By.CSS_SELECTOR, "article[data-service-review-card-paper='true']")
            )
        )
        time.sleep(1)
        return driver.page_source
    finally:
        driver.quit()


def _has_next_page(html: str) -> bool:
    soup = BeautifulSoup(html, "html.parser")
    return soup.select_one("a[rel='next'][data-pagination-button-next-link='true']") is not None


def scrape_reviews(base_url: str, start_page: int, headless: bool) -> List[Dict[str, str]]:
    all_rows: List[Dict[str, str]] = []
    page = start_page

    while True:
        url = base_url.format(page=page)
        html = _get_page_html(url, headless)
        rows = _extract_reviews(html)

        if not rows:
            break

        all_rows.extend(rows)

        if not _has_next_page(html):
            break

        page += 1

    return all_rows


def write_csv(rows: List[Dict[str, str]], output_path: str) -> None:
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["name", "region", "review", "stars"])
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Scrape Trustpilot reviews to CSV.")
    parser.add_argument(
        "--base-url",
        default=DEFAULT_BASE_URL,
        help="Base URL with {page} placeholder.",
    )
    parser.add_argument(
        "--start-page",
        type=int,
        default=1,
        help="First page number to scrape.",
    )
    parser.add_argument(
        "--output",
        default="jobnimbus_reviews.csv",
        help="CSV output path.",
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run Chrome in headless mode.",
    )
    args = parser.parse_args()

    rows = scrape_reviews(args.base_url, args.start_page, args.headless)
    write_csv(rows, args.output)
    print(f"Wrote {len(rows)} reviews to {args.output}")


if __name__ == "__main__":
    main()
         