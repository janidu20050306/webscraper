# 🏠 Real Estate Data Scraper Bot

> **Automated daily rental listing feeds for real estate agents and investors.**  
> Scrapes Craigslist across multiple cities, detects new listings & price changes,  
> and delivers clean CSV + JSON data every morning — automatically.

---

## ✅ What This Does

- Scrapes **300–500 fresh apartment listings per day** per city
- Detects **new listings** that weren't in yesterday's feed
- Detects **price changes** on existing listings
- Outputs **CSV** (for agents using Excel) and **JSON** (for developers / APIs)
- Supports **7 major US cities** out of the box
- Runs **automatically every morning** via GitHub Actions — fully free

---

## 🚀 Quick Start

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Run a scrape (New York, 3 pages ≈ 360 listings)
```bash
python real_estate_scraper.py
```

### 3. Filter by city and price range
```bash
python real_estate_scraper.py --city chicago --minprice 1000 --maxprice 3500
```

### 4. Scrape more pages (more listings)
```bash
python real_estate_scraper.py --city newyork --maxpages 10
```

---

## 📦 Output Files

| File | Description |
|------|-------------|
| `output/latest_listings.csv` | Always contains today's full results — send this to clients |
| `output/newyork_20260402_164634.csv` | Timestamped archive of each run |
| `output/newyork_20260402_164634.json` | JSON version for API / developer use |
| `scraper_log.txt` | Full run log with new listing & price change alerts |

### CSV Columns
| Column | Example |
|--------|---------|
| `id` | `7925106101` |
| `title` | `SPACIOUS 2 BEDROOM FOR RENT` |
| `price` | `$2,500` |
| `neighborhood` | `Brownsville` |
| `url` | `https://newyork.craigslist.org/...` |
| `scraped_at` | `2026-04-02 16:46:34` |

---

## 🌆 Supported Cities

| Key | City |
|-----|------|
| `newyork` | New York, NY |
| `chicago` | Chicago, IL |
| `losangeles` | Los Angeles, CA |
| `houston` | Houston, TX |
| `miami` | Miami, FL |
| `boston` | Boston, MA |
| `seattle` | Seattle, WA |

---

## ⚙️ Automation (GitHub Actions — Free)

The `.github/workflows/scraper.yml` file runs this scraper **every morning at 6 AM UTC** and automatically commits the new data to this repository.

**Steps to activate:**
1. Push this project to a GitHub repository
2. Go to the **Actions** tab → Enable workflows
3. Click **Run workflow** to test it manually
4. After that, it runs automatically every day — no manual work needed

---

## 💰 Business Model

Use the data to build a recurring revenue stream:

| Plan | What you offer | Price |
|------|----------------|-------|
| Starter | Daily CSV for 1 city, emailed | $150/week |
| Pro | 3 cities + alerts + JSON | $300/week |
| Agency | Unlimited cities + API + custom filters | $500+/week |

See **`outreach_templates.md`** for LinkedIn DM scripts, cold email templates, and objection-handling scripts.

---

## ⚖️ Legal & Ethics

- Only scrapes **publicly visible** Craigslist listings
- Respects server load with 2-second delays between requests
- Data is used for research and delivery to paying clients
- Always check the target site's `robots.txt` before expanding to new sources

---

## 📁 Project Structure

```
web-scraper-bot/
├── real_estate_scraper.py      # Main scraper
├── requirements.txt            # Python dependencies
├── outreach_templates.md       # Sales scripts for finding clients
├── scraper_code_templates.py   # Additional code reference templates
├── output/
│   ├── latest_listings.csv     # Today's data (send this to clients)
│   └── ...                     # Timestamped archives
├── scraper_log.txt             # Run logs & alerts
└── .github/
    └── workflows/
        └── scraper.yml         # Daily automation
```
