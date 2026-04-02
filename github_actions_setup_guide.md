# GitHub Actions: Run Your Scraper Automatically ($0 Cost)

## Overview
GitHub Actions lets you run code on GitHub's servers for FREE. Your scraper runs automatically on schedule and stores results in your repo.

---

## SETUP (5 minutes)

### Step 1: Create GitHub Account (if you don't have one)
- Go to github.com
- Sign up (free)
- Create new repository called `web-scraper-bot`

### Step 2: Upload Your Files to GitHub
In your new repository:
1. Click "Add file" → "Create new file"
2. Name: `scraper.py`
3. Paste your scraper code (from the templates)
4. Click "Commit changes"

### Step 3: Create Workflow Directory
1. Click "Add file" → "Create new file"
2. Path: `.github/workflows/scraper.yml`
3. Paste the configuration below:

```yaml
name: Daily Web Scraper

on:
  schedule:
    - cron: '0 9 * * *'  # Run every day at 9 AM UTC
  workflow_dispatch:      # Allow manual trigger from GitHub UI

jobs:
  scrape:
    runs-on: ubuntu-latest
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install requests beautifulsoup4 lxml
    
    - name: Run scraper
      run: python scraper.py
    
    - name: Commit and push results
      run: |
        git config --local user.email "github-actions@github.com"
        git config --local user.name "GitHub Actions Bot"
        git add -A
        git commit -m "Auto: Scraped data updated - $(date -u +'%Y-%m-%d %H:%M:%S UTC')" || true
        git push
      env:
        GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

4. Click "Commit changes"

### Step 4: Verify It's Working
1. Go to your repo's "Actions" tab
2. Click the "Daily Web Scraper" workflow
3. Click "Run workflow" → "Run workflow"
4. Wait 30 seconds and refresh
5. You should see it running (yellow circle)
6. When complete, it turns green (✓)
7. Your repo now has the scraped data

---

## SCHEDULE OPTIONS

Change the cron time in `.github/workflows/scraper.yml`:

```yaml
schedule:
  - cron: '0 9 * * *'        # Daily at 9 AM UTC
  - cron: '0 */6 * * *'      # Every 6 hours
  - cron: '0 0 * * 0'        # Weekly on Sunday at midnight
  - cron: '0 0 1 * *'        # Monthly on 1st at midnight
  - cron: '*/30 * * * *'     # Every 30 minutes
```

**Note:** GitHub time is in UTC. Convert to your timezone.

---

## STORING DATA

### Option 1: Save to CSV/JSON (Git commits)
Your scraper saves data to `data.json` or `data.csv`. GitHub Actions commits it each time.

**Pros:** Simple, free, data versioned in Git history
**Cons:** 1GB limit per repo

```python
# In your scraper.py
import json

def save_data(data):
    with open('data.json', 'w') as f:
        json.dump(data, f)
```

### Option 2: Save to Google Drive (Free)
Send scraped data to Google Drive for unlimited storage.

**Setup:**
1. Create Google Service Account (5 mins)
2. Store credentials in GitHub Secrets
3. Use `pydrive` library to upload

```python
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
import json

# Authenticate with service account
gauth = GoogleAuth()
gauth.auth_mechanism = 'service_account'
gauth.ServiceAuth()
drive = GoogleDrive(gauth)

# Upload file
file = drive.CreateFile({'title': 'scraped_data.json'})
file.SetContentFile('data.json')
file.Upload()
```

### Option 3: Save to Free Database
Use MongoDB Atlas (free tier: 512MB storage)

```python
from pymongo import MongoClient

client = MongoClient('YOUR_MONGODB_CONNECTION_STRING')
db = client['scraped_data']
collection = db['products']

collection.insert_many(data)  # Your scraped data
```

---

## ADVANCED: Adding Secret Credentials

If your scraper needs API keys or authentication:

1. Go to repo Settings → Secrets and variables → Actions
2. Click "New repository secret"
3. Name: `API_KEY`
4. Value: Your actual API key
5. Click "Add secret"

In your scraper, access it:

```python
import os

api_key = os.getenv('API_KEY')
```

In workflow:

```yaml
env:
  API_KEY: ${{ secrets.API_KEY }}
```

---

## HANDLING ERRORS & DEBUGGING

### View Logs
1. Go to "Actions" tab
2. Click the run
3. Click the "Run scraper" step
4. See full error messages

### Common Issues

**Issue:** Scraper times out
```yaml
- name: Run scraper
  timeout-minutes: 20  # Increase timeout
  run: python scraper.py
```

**Issue:** "File not found" error
```yaml
- name: Check files
  run: ls -la
```

**Issue:** Dependencies not installing
```yaml
- name: Install dependencies
  run: |
    pip install --upgrade pip
    pip install requests beautifulsoup4 lxml
```

---

## PUSHING DATA TO YOUR SERVER

Once you have scraped data, you might want to send it somewhere:

### Option A: Webhook (Notify server of new data)
```python
import requests

# After scraping, notify your server
response = requests.post(
    'https://your-api.com/webhook',
    json={'data': scraped_data}
)
```

### Option B: Upload to S3 (AWS Free Tier)
```python
import boto3

s3 = boto3.client('s3')
s3.put_object(
    Bucket='your-bucket',
    Key='data.json',
    Body=json.dumps(scraped_data)
)
```

---

## COMPLETE EXAMPLE: E-COMMERCE PRICE SCRAPER

Save this as `scraper.py`:

```python
import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime

def scrape_amazon_prices():
    """Scrape product prices from a website"""
    
    # Example: Scrape laptop prices
    url = 'https://example-shop.com/laptops'
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        products = []
        
        # Adjust these selectors to match your target site
        for item in soup.find_all('div', class_='product')[:100]:
            try:
                name = item.find('h2').text.strip()
                price = item.find('span', class_='price').text.strip()
                
                products.append({
                    'name': name,
                    'price': price,
                    'timestamp': datetime.now().isoformat()
                })
            except:
                continue
        
        return products
    
    except Exception as e:
        print(f"Error: {e}")
        return []

if __name__ == '__main__':
    print("Starting scraper...")
    data = scrape_amazon_prices()
    
    # Save to file
    with open('data.json', 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"Scraped {len(data)} products")
```

Save as `.github/workflows/scraper.yml`:

```yaml
name: Daily Price Scraper

on:
  schedule:
    - cron: '0 9 * * *'
  workflow_dispatch:

jobs:
  scrape:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        pip install requests beautifulsoup4
    
    - name: Run scraper
      run: python scraper.py
    
    - name: Commit results
      run: |
        git config user.email "bot@github.com"
        git config user.name "Scraper Bot"
        git add data.json
        git commit -m "Daily scrape" || true
        git push
```

---

## LIMITS & QUOTAS

- **Execution time:** 6 hours per job (but 35 minutes is typical before timeout)
- **Monthly runs:** 2,000 free minutes/month (enough for daily runs)
- **Storage:** 1GB per repo
- **Concurrent jobs:** 20 simultaneous

For serious scale, upgrade to GitHub Pro ($4/month) for 3,000 minutes/month.

---

## NEXT STEPS

1. Create repository
2. Add `scraper.py` with your code
3. Add `.github/workflows/scraper.yml` workflow
4. Test manually (Run workflow button)
5. Let it run daily automatically
6. Check data.json in repo for results
7. Share with customers

You now have a completely automated scraper running for $0. 🚀

