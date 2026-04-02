"""
Web Scraper Bot - Complete Code Templates
Copy and adapt these for your specific use case
All examples are free to run
"""

# ============================================================================
# TEMPLATE 1: SIMPLE BEAUTIFULSOUP SCRAPER (EASIEST TO START)
# ============================================================================

"""
Use this for quick, simple scrapers of single websites
Best for: Blog posts, product listings, simple data
"""

import requests
from bs4 import BeautifulSoup
import csv
from datetime import datetime
import time

class SimpleProductScraper:
    def __init__(self, output_file='products.csv'):
        self.output_file = output_file
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
    
    def scrape_products(self, url):
        """
        Example: Scrape product listings
        Adapt the selectors (h2, .price, etc) to match your target website
        """
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            products = []
            
            # CHANGE THESE SELECTORS TO MATCH YOUR TARGET SITE
            for item in soup.find_all('div', class_='product-item')[:50]:  # Limit to 50 items
                try:
                    name = item.find('h2', class_='product-name')
                    price = item.find('span', class_='price')
                    url_link = item.find('a', class_='product-link')
                    
                    if name and price:
                        products.append({
                            'name': name.get_text(strip=True),
                            'price': price.get_text(strip=True),
                            'url': url_link['href'] if url_link else 'N/A',
                            'scraped_at': datetime.now().isoformat()
                        })
                except Exception as e:
                    print(f"Error parsing item: {e}")
                    continue
            
            return products
        
        except requests.exceptions.RequestException as e:
            print(f"Error fetching {url}: {e}")
            return []
    
    def save_to_csv(self, products):
        """Save scraped data to CSV file"""
        if not products:
            print("No products to save")
            return
        
        try:
            with open(self.output_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=products[0].keys())
                writer.writeheader()
                writer.writerows(products)
            print(f"Saved {len(products)} products to {self.output_file}")
        except Exception as e:
            print(f"Error saving CSV: {e}")
    
    def run(self, url):
        """Main execution"""
        print(f"Scraping {url}...")
        products = self.scrape_products(url)
        self.save_to_csv(products)
        return products


# USAGE EXAMPLE:
# scraper = SimpleProductScraper('my_products.csv')
# products = scraper.run('https://example-site.com/products')


# ============================================================================
# TEMPLATE 2: ADVANCED SCRAPER WITH ERROR HANDLING & RETRIES
# ============================================================================

"""
Use this for production scrapers that need reliability
Handles errors, retries, delays, proxies
"""

import requests
from bs4 import BeautifulSoup
import json
import logging
from datetime import datetime
import time
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class RobustScraper:
    def __init__(self, output_file='data.json'):
        self.output_file = output_file
        self.session = self.create_session()
    
    def create_session(self):
        """Create requests session with retry strategy"""
        session = requests.Session()
        
        # Retry strategy
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET"]
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # Headers to avoid being blocked
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Referer': 'https://www.google.com/',
        })
        
        return session
    
    def fetch_page(self, url, delay=2):
        """Fetch page with delays to be respectful"""
        try:
            time.sleep(delay)  # Be respectful - add delay between requests
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            logger.info(f"Successfully fetched {url}")
            return response
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch {url}: {e}")
            return None
    
    def parse_data(self, html_content, selectors):
        """
        Parse HTML using CSS selectors
        
        selectors = {
            'items': 'div.product',
            'name': 'h2.name',
            'price': 'span.price',
            'url': 'a.link'
        }
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        data = []
        
        try:
            items = soup.select(selectors['items'])
            logger.info(f"Found {len(items)} items")
            
            for item in items:
                record = {'scraped_at': datetime.now().isoformat()}
                
                for field, selector in selectors.items():
                    if field == 'items':
                        continue
                    
                    try:
                        element = item.select_one(selector)
                        if element:
                            record[field] = element.get_text(strip=True)
                        else:
                            record[field] = None
                    except Exception as e:
                        logger.warning(f"Error extracting {field}: {e}")
                        record[field] = None
                
                data.append(record)
        
        except Exception as e:
            logger.error(f"Error parsing data: {e}")
        
        return data
    
    def save_json(self, data):
        """Save to JSON file"""
        try:
            with open(self.output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.info(f"Saved {len(data)} records to {self.output_file}")
        except Exception as e:
            logger.error(f"Error saving JSON: {e}")
    
    def run(self, url, selectors):
        """Execute the scraping"""
        logger.info(f"Starting scrape of {url}")
        
        response = self.fetch_page(url)
        if not response:
            logger.error("Failed to fetch page, exiting")
            return []
        
        data = self.parse_data(response.content, selectors)
        self.save_json(data)
        
        return data


# USAGE EXAMPLE:
# scraper = RobustScraper('my_data.json')
# 
# selectors = {
#     'items': 'div.product-card',
#     'name': 'h3.product-name',
#     'price': 'span.product-price',
#     'url': 'a.product-link'
# }
# 
# data = scraper.run('https://example.com/products', selectors)


# ============================================================================
# TEMPLATE 3: MULTI-PAGE SCRAPER
# ============================================================================

"""
Scrape multiple pages/URLs in sequence
Perfect for pagination scenarios
"""

class MultiPageScraper(RobustScraper):
    def scrape_multiple_pages(self, urls, selectors):
        """
        Scrape multiple URLs and combine results
        urls = ['https://example.com/page1', 'https://example.com/page2', ...]
        """
        all_data = []
        
        for url in urls:
            logger.info(f"Scraping page: {url}")
            response = self.fetch_page(url, delay=3)  # 3 second delay between pages
            
            if response:
                page_data = self.parse_data(response.content, selectors)
                all_data.extend(page_data)
                logger.info(f"Got {len(page_data)} items from this page")
        
        self.save_json(all_data)
        logger.info(f"Total items scraped: {len(all_data)}")
        return all_data


# ============================================================================
# TEMPLATE 4: DATA STORAGE (Save to Multiple Formats)
# ============================================================================

"""
Store scraped data in different formats
Choose based on what your customers need
"""

import sqlite3
import json
import csv

class DataStorage:
    @staticmethod
    def save_json(data, filename='data.json'):
        """Save as JSON"""
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
    
    @staticmethod
    def save_csv(data, filename='data.csv'):
        """Save as CSV"""
        if not data:
            return
        
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)
    
    @staticmethod
    def save_sqlite(data, db_file='data.db', table_name='scraped_data'):
        """Save to SQLite database"""
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        
        if not data:
            return
        
        # Create table based on first record
        keys = list(data[0].keys())
        columns = ', '.join([f'{k} TEXT' for k in keys])
        cursor.execute(f'CREATE TABLE IF NOT EXISTS {table_name} ({columns})')
        
        # Insert data
        placeholders = ', '.join(['?' for _ in keys])
        for record in data:
            values = tuple(str(record.get(k, '')) for k in keys)
            cursor.execute(f'INSERT INTO {table_name} VALUES ({placeholders})', values)
        
        conn.commit()
        conn.close()
        print(f"Saved {len(data)} records to {db_file}")


# ============================================================================
# TEMPLATE 5: GITHUB ACTIONS AUTOMATION CONFIGURATION
# ============================================================================

"""
Save this as .github/workflows/scraper.yml in your GitHub repo

This will run your scraper automatically every day and save results
"""

GITHUB_ACTIONS_CONFIG = """
name: Daily Scraper

on:
  schedule:
    - cron: '0 9 * * *'  # Run daily at 9 AM UTC
  workflow_dispatch:      # Allow manual trigger

jobs:
  scrape:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.9'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install requests beautifulsoup4 lxml
    
    - name: Run scraper
      run: python scraper.py
    
    - name: Commit and push changes
      run: |
        git config --local user.email "action@github.com"
        git config --local user.name "GitHub Action"
        git add -A
        git commit -m "Update scraped data - $(date)"
        git push
      env:
        github_token: ${{ secrets.GITHUB_TOKEN }}
"""

# ============================================================================
# TEMPLATE 6: QUICK START EXAMPLE (COPY THIS TO GET STARTED)
# ============================================================================

"""
This is a complete example you can run immediately.
Just replace the URL and CSS selectors with your target site.
"""

if __name__ == "__main__":
    # STEP 1: Replace these with your actual website
    TARGET_URL = "https://example-ecommerce.com/products"
    
    # STEP 2: Inspect the website and find these selectors
    # Use browser DevTools (F12) to find CSS classes/IDs
    SELECTORS = {
        'items': 'div.product-item',           # Container for each product
        'name': 'h2.product-name',              # Product name
        'price': 'span.product-price',          # Product price
        'url': 'a.product-link'                 # Product URL
    }
    
    # STEP 3: Run the scraper
    print("Starting web scraper...")
    scraper = RobustScraper('my_scraped_data.json')
    data = scraper.run(TARGET_URL, SELECTORS)
    
    print(f"\n✓ Successfully scraped {len(data)} items")
    print(f"✓ Data saved to my_scraped_data.json")
    print("\nFirst item:")
    if data:
        print(json.dumps(data[0], indent=2))

