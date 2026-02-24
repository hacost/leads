# Bastion Leads Generation Scraper (Google Maps + Facebook)

This project provides an automated, precise, and highly configurable system for scraping business leads from Google Maps and enriching them with additional contact information from Facebook (Emails and WhatsApp/Phones). It is designed to filter out low-quality leads and categorize businesses based on their review count and ratings.

## 🚀 Features

*   **Google Maps Scraping**: Extracts names, addresses, phones, websites, ratings, and exact review counts of businesses.
*   **Robust Review Extraction**: Uses injected JavaScript to reliably extract the number of reviews (supports both English "reviews" and Spanish "opiniones"), regardless of Google UI changes.
*   **Intelligent Caching & Deduplication**:
    *   **Session Cache**: Prevents duplicate entries when searching across multiple overlapping zones (e.g., adjacent municipalities) in a single run, giving priority to the phone number.
    *   **Database Cache (`leads.db`)**: Saves scraped prospects to avoid re-processing the same business in the future. When searching, it checks the exact search (category + municipality) to reuse existing data, saving API calls and time.
*   **Facebook Enrichment**: Execute a secondary script manually to search Facebook and find missing phones and emails in your extracted leads.
    *   **Dual Strategy**: Prioritizes the "Intro/About" section. If no phone is found there, it strictly scans the **first 3 recent posts** looking for text-based phones and WhatsApp links (`wa.me`).
    *   **Smart Navigation**: If a Google result links directly to a post, the script navigates first to the main profile page.
*   **Strict Phone Validation**: Enforces a strict 10-digit format (specifically designed for Mexico, cleaning prefixes like `+52` or `521`).
*   **Automatic Segmentation**: Automatically classifies and separates valid leads into different Excel files based on configurable thresholds.

## 📂 Output Files

The scraper automatically categorizes leads into distinct Excel files:

1.  `leads_corporate.xlsx`: Businesses with many reviews (e.g., > 20) or known large chains.
2.  `leads_micro.xlsx`: Smaller or newer businesses with fewer reviews (e.g., <= 20) but maintaining a decent rating (>= 3.5 stars).
3.  `leads_google_maps.xlsx`: The master list of ALL extracted leads that have a valid 10-digit phone.
4.  `leads_pending_lookup.xlsx`: Leads that were extracted but *do not* have a valid phone number. These are the target for the verification script (`enrichment_scraper.py`).

## ⚙️ Configuration (`config.json`)

You can customize the lead segmentation rules **without modifying the Python source code**. Just edit the `config.json` file in the main directory:

```json
{
  "segmentation": {
    "micro_max_reviews": 20,
    "good_rating_threshold": 3.5
  },
  "search": {
    "max_scroll_attempts": 5,
    "wait_between_actions_ms": 3000,
    "headless": false
  }
}
```

*   `micro_max_reviews`: Any business with this number of reviews or less (including 0) will be classified as "Micro". Anything exceeding this number will be "Corporate".
*   `good_rating_threshold`: The minimum rating required for a business with few reviews to be saved in "Micro" and not discarded (default 3.5). Businesses with 0 reviews pass automatically.
*   `headless`: If set to `true`, the Google Maps scraper will run in the background (hidden browser).

## 🛠 Usage

### 1. Initial Extraction (Google Maps)
Edit the `zones` and `categories` lists directly at the bottom of the `scraper.py` file, then run with `uv`:
```bash
uv run scraper.py
```
This will generate the base `.xlsx` files and populate the `leads.db` database.

### 2. Enrichment (Facebook)
To try to recover missing phones and emails from businesses that remained in `leads_pending_lookup.xlsx`, make sure you have Chrome open according to the instructions and manually execute the enrichment script:
```bash
uv run enrichment_scraper.py
```
The script will search Facebook for each pending lead, update the record, and generate an enriched Excel file.

## 📋 Requirements and Installation

This project is built to use **`uv`**, the extremely fast Python package and project manager. Because `pyproject.toml` is already included, you don't need to manually install dependencies with `pip`.

1.  Make sure you have `uv` installed.
2.  Sync the project dependencies from the `pyproject.toml` file automatically:
    ```bash
    uv sync
    ```
3.  Install the required browser for Playwright:
    ```bash
    uv run playwright install chromium
    ```
