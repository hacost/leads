import asyncio
from playwright.async_api import async_playwright
import pandas as pd
import os
import re
import sys
import time
import argparse

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

class FacebookSearchScraper:
    def __init__(self):
        self.results = []
        self.seen_urls = set()
        
    def clean_phone(self, p):
        if pd.isna(p) or p == "N/A" or not str(p).strip():
            return "N/A"
        cleaned = re.sub(r'\D', '', str(p))
        if cleaned.startswith('521') and len(cleaned) > 10:
            cleaned = cleaned[3:]
        elif cleaned.startswith('52') and len(cleaned) > 10:
            cleaned = cleaned[2:]
        if len(cleaned) >= 10:
            return cleaned[-10:]
        return "N/A"

    async def extract_facebook_data(self, page, url):
        """Visits a Facebook page and extracts name, phone, email, and website."""
        data = {
            "name": "N/A",
            "facebook_url": url,
            "phone": "N/A",
            "email": "N/A",
            "website": "N/A"
        }
        
        try:
            print(f"  -> Visiting: {url}")
            await page.goto(url, wait_until="domcontentloaded", timeout=15000)
            await asyncio.sleep(2) # Allow elements to render
            
            # Close login popup if it exists
            try:
                close_btn = page.locator('div[aria-label="Close"], div[aria-label="Cerrar"], i[data-visualcompletion="css-img"]').first
                if await close_btn.is_visible(timeout=2000):
                    await close_btn.click()
                    await asyncio.sleep(1)
            except Exception:
                pass
            
            # Extract Name (often in an h1)
            try:
                name_element = page.locator('h1').first
                if await name_element.is_visible(timeout=3000):
                    data['name'] = await name_element.inner_text()
            except Exception:
                pass
            
            # --- EXTRACT CONTACT INFO ---
            page_text = await page.locator("body").inner_text()
            
            # 1. Extract Email
            email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', page_text)
            if email_match:
                data['email'] = email_match.group(0)
                
            # 2. Extract Website
            # Look for common web patterns not containing facebook
            website_match = re.search(r'(https?://(?:www\.)?(?!facebook\.com)[a-zA-Z0-9-]+\.[a-zA-Z0-9.-]+/?)[\\s\\n]', page_text)
            if website_match:
                 data['website'] = website_match.group(1).strip()
            
            # 3. Extract Phone (Intro / Posts Strategy)
            phone_found = False
            
            # Strategy A: Intro Section
            try:
                intro = page.locator('div:has-text("Intro"), div:has-text("Información")').last
                if await intro.is_visible(timeout=3000):
                    intro_text = await intro.inner_text()
                    phone_match = re.search(r'(?:\+?52)?\s*[\d\s\-\(\)]{10,15}', intro_text)
                    if phone_match:
                        cleaned = self.clean_phone(phone_match.group(0))
                        if cleaned != "N/A":
                            data['phone'] = cleaned
                            phone_found = True
            except Exception:
                pass
                
            # Strategy B: Posts / WhatsApp links
            if not phone_found:
                wa_match = re.search(r'wa\.me/(\d+)', page_text)
                if wa_match:
                    cleaned = self.clean_phone(wa_match.group(1))
                    if cleaned != "N/A":
                        data['phone'] = cleaned
                        phone_found = True
                
                if not phone_found:
                    phone_match = re.search(r'(?:\+?52)?\s*(?:[1-9]\d{1,2}[\s.-]?)?(?:\(\d{2,3}\)[\s.-]?)?\d{3,4}[\s.-]?\d{3,4}', page_text[:5000])
                    if phone_match:
                        cleaned = self.clean_phone(phone_match.group(0))
                        if cleaned != "N/A":
                            data['phone'] = cleaned
                            
        except Exception as e:
            print(f"  [!] Error parsing {url}: {e}")
            
        return data

    async def search_google(self, page, category, zone):
        """Performs Google search and filters Facebook profile URLs."""
        queries = [
            f'site:facebook.com "{category}" "{zone}"',
            f'site:facebook.com/pages "{category}" "{zone}"',
            f'intitle:"{category}" "{zone}" site:facebook.com'
        ]
        
        extracted_fb_urls = []
        
        for query_idx, query in enumerate(queries):
            print(f"\n[SEARCH {query_idx+1}/{len(queries)}] Querying Google: {query}")
            
            url = f"https://www.google.com/search?q={query}"
            await page.goto(url, wait_until="domcontentloaded")
            
            # Give the user time to solve Captcha if it appears
            print("  [WAIT] Waiting up to 60s for results (or solve Captcha manually)...")
            for i in range(12): # 12 * 5s = 60s
                try:
                    if await page.query_selector('#search') or await page.query_selector('h3'):
                        print("  [INFO] Results page detected! Continuing...")
                        break
                except:
                    pass
                await asyncio.sleep(5)
            
            # Scrape Google Results (max 10 pages for now)
            for i in range(10):
                print(f"  Scraping Google Page {i+1} for query {query_idx+1}...")
                # Wait for search results
                try:
                    await page.wait_for_selector('div#search', timeout=5000)
                except:
                    print("  [!] No search results container found. Possibly a Captcha or no results.")
                    break
                    
                # Extract links
                links = await page.locator('a[href*="facebook.com"]').evaluate_all(
                    "elements => elements.map(e => e.href)"
                )
                
                for link in links:
                    # 1. Must be an actual Facebook link, not a Google account link
                    if not ("facebook.com" in link and "google.com" not in link):
                        continue
                    
                    # 2. Extract Base Page URL to avoid /videos, /posts, etc.
                    if "profile.php?id=" in link:
                        match = re.search(r'profile\.php\?id=\d+', link)
                        if match:
                            clean_link = f"https://www.facebook.com/{match.group(0)}"
                        else:
                            continue
                    else:
                        # e.g., https://www.facebook.com/impergari/videos/... -> https://www.facebook.com/impergari
                        clean_link = link.split('?')[0].rstrip('/')
                        parts = clean_link.split('/')
                        if len(parts) >= 4 and 'facebook.com' in parts[2]:
                            page_name = parts[3]
                            # 3. Filter out Facebook system pages
                            garbage_keywords = ['login', 'pages', 'public', 'groups', 'events', 'watch', 'help', 'marketplace', 'directory', 'people']
                            if any(x == page_name.lower() or x in page_name.lower() for x in garbage_keywords):
                                continue
                            clean_link = f"https://www.facebook.com/{page_name}"
                        else:
                            continue
                    
                    if clean_link not in self.seen_urls:
                        self.seen_urls.add(clean_link)
                        extracted_fb_urls.append(clean_link)
                
                # Try to click Next Page
                try:
                    next_btn = page.locator('a#pnnext')
                    if await next_btn.is_visible():
                        await next_btn.click()
                        await asyncio.sleep(3)
                    else:
                        break # No more pages
                except:
                     break
                     
        print(f"  Found {len(extracted_fb_urls)} unique Facebook URLs to process across all queries.")
        return extracted_fb_urls

    async def run(self, categories, zones):
        async with async_playwright() as p:
            # MUST BE HEADFUL to allow manual Captcha solving
            browser = await p.chromium.launch(headless=False)
            context = await browser.new_context()
            page = await context.new_page()
            
            for zone in zones:
                for category in categories:
                    fb_urls = await self.search_google(page, category, zone)
                    
                    for url in fb_urls:
                        data = await self.extract_facebook_data(page, url)
                        data['category'] = category
                        data['zone'] = zone
                        self.results.append(data)
                        
            await browser.close()
            
        self.save_data()
        
    def save_data(self):
        if not self.results:
            print("No results found.")
            return
            
        df = pd.DataFrame(self.results)
        
        # --- DEDUPLICATION LOGIC ---
        initial_len = len(df)
        
        # 1. Drop exact URL duplicates
        df.drop_duplicates(subset=['facebook_url'], keep='first', inplace=True)
        
        # 2. Drop Phone duplicates (Keep first valid one)
        df_valid = df[df['phone'] != "N/A"].copy()
        df_pending = df[df['phone'] == "N/A"].copy()
        df_valid.drop_duplicates(subset=['phone'], keep='first', inplace=True)
        
        df = pd.concat([df_valid, df_pending], ignore_index=True)
        
        if len(df) < initial_len:
            print(f"  [INFO] Filtered out {initial_len - len(df)} duplicate leads before saving.")
        
        timestamp = time.strftime("%Y-%m-%d_%H-%M-%S")
        output_dir = os.path.join("leads", timestamp)
        os.makedirs(output_dir, exist_ok=True)
        
        file_path = os.path.join(output_dir, "facebook_direct_leads.xlsx")
        df.to_excel(file_path, index=False)
        print(f"\n[SUCCESS] Exported {len(df)} Facebook leads to {file_path}")

async def main():
    parser = argparse.ArgumentParser(description="Facebook Direct Search Scraper")
    parser.add_argument('--zones', type=str, help="Zones/cities separated by semicolon")
    parser.add_argument('--categories', type=str, help="Categories separated by semicolon")
    args = parser.parse_args()

    print("Welcome to the Facebook Direct Search Scraper")
    print("---------------------------------------------")
    
    if args.zones and args.categories:
        zones_input = args.zones
        cats_input = args.categories
    else:
        print("Enter the zones/cities (separated by semicolon). Example: Monterrey; San Pedro")
        zones_input = input("Zones: ")
        print("Enter the categories (separated by semicolon). Example: Tiendas de abarrotes; Esteticas")
        cats_input = input("Categories: ")
    
    zones = [z.strip() for z in zones_input.split(";") if z.strip()]
    categories = [c.strip() for c in cats_input.split(";") if c.strip()]
    
    if not zones or not categories:
        print("Error: Provide at least one zone and category.")
        return
        
    scraper = FacebookSearchScraper()
    await scraper.run(categories, zones)

if __name__ == "__main__":
    asyncio.run(main())
