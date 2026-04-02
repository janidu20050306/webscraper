"""
Real Estate Scraper Bot
=======================
Scrapes apartment listings from Craigslist New York daily.
Outputs: CSV (for agents), JSON (for APIs), and detects new listings & price changes.

Usage:
    python real_estate_scraper.py                          # Scrape NYC (default)
    python real_estate_scraper.py --city chicago           # Scrape Chicago
    python real_estate_scraper.py --maxpages 5             # Scrape 5 pages
    python real_estate_scraper.py --minprice 1000 --maxprice 3500  # Filter by price
"""

import requests
from bs4 import BeautifulSoup
import json
import csv
import logging
import time
import os
import argparse
import smtplib
from email.mime.text import MIMEText
from datetime import datetime
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# ──────────────────────────────────────────────────────────────────────────────
# CONFIGURATION  (edit these values to customize behaviour)
# ──────────────────────────────────────────────────────────────────────────────

CITY_URLS = {
    "newyork":    "https://newyork.craigslist.org/search/apa",
    "chicago":    "https://chicago.craigslist.org/search/apa",
    "losangeles": "https://losangeles.craigslist.org/search/apa",
    "houston":    "https://houston.craigslist.org/search/apa",
    "miami":      "https://miami.craigslist.org/search/apa",
    "boston":     "https://boston.craigslist.org/search/apa",
    "seattle":    "https://seattle.craigslist.org/search/apa",
}

OUTPUT_DIR      = "output"
LOG_FILE        = "scraper_log.txt"
REQUEST_DELAY   = 2        # seconds between page requests (be respectful)
MAX_PAGES       = 3        # max pages to scrape per run (120 listings/page)
DEFAULT_CITY    = "newyork"

# ──────────────────────────────────────────────────────────────────────────────
# LOGGING SETUP
# ──────────────────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────────────────────
# SCRAPER CLASS
# ──────────────────────────────────────────────────────────────────────────────

class RealEstateScraper:
    """
    Customer-facing real estate scraper with:
      - Multi-page support (pagination)
      - Price range filtering
      - New listing & price-change detection
      - Dual-format output: CSV (agents) + JSON (devs/API)
      - Professional retry & error handling
    """

    def __init__(self, output_dir=OUTPUT_DIR):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        self.session = self._create_session()

    # ── Session ─────────────────────────────────────────────────────────────

    def _create_session(self):
        session = requests.Session()
        retry = Retry(
            total=5,
            backoff_factor=2,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET"],
        )
        session.mount("https://", HTTPAdapter(max_retries=retry))
        session.mount("http://",  HTTPAdapter(max_retries=retry))
        session.headers.update({
            "User-Agent":      "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                               "AppleWebKit/537.36 (KHTML, like Gecko) "
                               "Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept":          "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Referer":         "https://www.google.com/",
        })
        return session

    # ── Fetch ────────────────────────────────────────────────────────────────

    def _fetch(self, url):
        """Fetch a single page. Returns raw bytes or None on failure."""
        try:
            logger.info(f"  GET {url}")
            time.sleep(REQUEST_DELAY)
            r = self.session.get(url, timeout=15)
            r.raise_for_status()
            return r.content
        except Exception as e:
            logger.error(f"  Failed to fetch {url}: {e}")
            return None

    # ── Parse ────────────────────────────────────────────────────────────────

    def _parse_page(self, html):
        """Parse one Craigslist search-results page. Returns list of dicts."""
        soup = BeautifulSoup(html, "html.parser")

        # Try both old and new Craigslist layouts
        cards = soup.select("li.cl-static-search-result") \
             or soup.select(".result-row") \
             or soup.select(".cl-search-result")

        results = []
        for card in cards:
            try:
                # Title + URL
                link = card.select_one(".titlestring") or card.select_one("a[href]")
                if not link:
                    continue
                title = link.get_text(strip=True)
                url   = link.get("href", "")

                # Price – may be embedded in the title on new Craigslist layout
                price_el = card.select_one(".priceinfo") or card.select_one(".result-price")
                if price_el:
                    price = price_el.get_text(strip=True)
                else:
                    # Fallback: find first '$…' sequence in the title text
                    import re
                    m = re.search(r'\$[\d,]+', title)
                    price = m.group() if m else "N/A"

                # neighbourhood / meta
                meta_el = card.select_one(".meta") or card.select_one(".result-hood")
                neighborhood = meta_el.get_text(strip=True) if meta_el else ""

                listing_id = url.split("/")[-1].replace(".html", "") if url else ""

                results.append({
                    "id":           listing_id,
                    "title":        title,
                    "price":        price,
                    "neighborhood": neighborhood,
                    "url":          url,
                    "scraped_at":   datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                })
            except Exception as exc:
                logger.debug(f"  Skipped card: {exc}")

        return results

    # ── Filter ───────────────────────────────────────────────────────────────

    @staticmethod
    def _parse_price(price_str):
        """Convert '$2,500mo' or '$2500' → 2500. Returns None if unparseable."""
        import re
        m = re.search(r'[\d,]+', price_str.replace(",", ""))
        return int(m.group().replace(",", "")) if m else None

    def _filter(self, listings, minprice=None, maxprice=None):
        """Filter listings by price range."""
        if minprice is None and maxprice is None:
            return listings
        filtered = []
        for row in listings:
            p = self._parse_price(row["price"])
            if p is None:
                filtered.append(row)   # keep unknown prices
                continue
            if minprice and p < minprice:
                continue
            if maxprice and p > maxprice:
                continue
            filtered.append(row)
        return filtered

    # ── Alerts ───────────────────────────────────────────────────────────────

    def detect_alerts(self, new_listings):
        """Compare new data with the previous run. Log new listings & price changes."""
        latest = os.path.join(self.output_dir, "latest_listings.csv")
        if not os.path.exists(latest):
            logger.info("  No previous data found – skipping alert comparison.")
            return

        old = {}
        with open(latest, encoding="utf-8") as f:
            for row in csv.DictReader(f):
                old[row.get("url", "")] = row

        new_count     = 0
        price_changes = 0
        for item in new_listings:
            if item["url"] not in old:
                new_count += 1
                logger.info(f"  🆕 NEW LISTING: {item['title'][:60]}  [{item['price']}]")
            else:
                op = old[item["url"]].get("price", "")
                if item["price"] != op and item["price"] != "N/A":
                    price_changes += 1
                    logger.info(
                        f"  💰 PRICE CHANGE: {item['title'][:40]}"
                        f"  {op} → {item['price']}"
                    )

        logger.info(
            f"  Alert summary: {new_count} new listings, "
            f"{price_changes} price changes detected."
        )

    # ── Save ─────────────────────────────────────────────────────────────────

    def save_data(self, data, city="newyork"):
        """
        Saves three files:
          1. Timestamped JSON  →  output/newyork_20260402_164634.json
          2. Timestamped CSV   →  output/newyork_20260402_164634.csv
          3. Rolling latest    →  output/latest_listings.csv   (overwrites each run)
        """
        if not data:
            logger.warning("  No data to save.")
            return

        ts = datetime.now().strftime("%Y%m%d_%H%M%S")

        json_path   = os.path.join(self.output_dir, f"{city}_{ts}.json")
        csv_path    = os.path.join(self.output_dir, f"{city}_{ts}.csv")
        latest_path = os.path.join(self.output_dir, "latest_listings.csv")

        # JSON
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

        # Timestamped CSV + rolling latest
        for path in (csv_path, latest_path):
            with open(path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=data[0].keys())
                writer.writeheader()
                writer.writerows(data)

        logger.info(
            f"  Saved {len(data)} listings → "
            f"{os.path.basename(csv_path)} & {os.path.basename(json_path)}"
        )
        return csv_path

    # ── Main run ─────────────────────────────────────────────────────────────

    def run(self, city=DEFAULT_CITY, maxpages=MAX_PAGES, minprice=None, maxprice=None):
        """
        Full scrape pipeline:
          fetch → parse → filter → alert → save
        """
        base_url = CITY_URLS.get(city.lower())
        if not base_url:
            logger.error(f"Unknown city '{city}'. Available: {list(CITY_URLS)}")
            return

        logger.info(f"{'='*60}")
        logger.info(f" Real Estate Scraper — {city.upper()}  ({datetime.now():%Y-%m-%d %H:%M})")
        logger.info(f"{'='*60}")

        all_listings = []

        for page in range(maxpages):
            offset = page * 120          # Craigslist paginates every 120 results
            url    = f"{base_url}?s={offset}" if offset else base_url

            html = self._fetch(url)
            if not html:
                break

            page_listings = self._parse_page(html)
            if not page_listings:
                logger.info(f"  Page {page+1}: No listings found – stopping pagination.")
                break

            logger.info(f"  Page {page+1}: found {len(page_listings)} listings.")
            all_listings.extend(page_listings)

        if not all_listings:
            logger.warning("No listings collected. The website layout may have changed.")
            return

        # Deduplicate by URL
        seen = set()
        unique = []
        for item in all_listings:
            if item["url"] not in seen:
                seen.add(item["url"])
                unique.append(item)

        logger.info(f"  Total unique listings before filter: {len(unique)}")

        # Price filter
        filtered = self._filter(unique, minprice, maxprice)
        logger.info(f"  Total listings after price filter:   {len(filtered)}")

        # Alerts (compare with previous run)
        self.detect_alerts(filtered)

        # Save outputs
        self.save_data(filtered, city=city)

        logger.info("  ✅ Daily update complete.")
        return filtered


# ──────────────────────────────────────────────────────────────────────────────
# CLI ENTRY-POINT
# ──────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Real Estate Scraper Bot")
    parser.add_argument(
        "--city",
        default=DEFAULT_CITY,
        choices=list(CITY_URLS.keys()),
        help=f"City to scrape (default: {DEFAULT_CITY})",
    )
    parser.add_argument(
        "--maxpages",
        type=int,
        default=MAX_PAGES,
        help=f"Max pages to scrape per run (default: {MAX_PAGES})",
    )
    parser.add_argument("--minprice", type=int, default=None, help="Minimum price filter ($)")
    parser.add_argument("--maxprice", type=int, default=None, help="Maximum price filter ($)")
    args = parser.parse_args()

    scraper = RealEstateScraper()
    scraper.run(
        city=args.city,
        maxpages=args.maxpages,
        minprice=args.minprice,
        maxprice=args.maxprice,
    )
