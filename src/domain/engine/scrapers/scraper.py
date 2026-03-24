import asyncio
import logging
from playwright.async_api import async_playwright

logger = logging.getLogger(__name__)
import pandas as pd
import sqlite3
import os
import time
import re
import json
import sys
import argparse

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


class GoogleMapsScraper:
    """
    Scraper for Google Maps business listings via Playwright.
    Methods to search, scroll feed, extract details (Name, Address, Phone), and save data.
    """
    def __init__(self, headless_override=None, session_id=None, db_path='data/leads.db'):
        self.results = []
        self.known_leads = {} # Cache for existing DB records: {(name, zone): data_dict}
        self.seen_names = set() # Global session cache for names
        self.seen_phones = set() # Global session cache for phones
        self.session_id = session_id
        self.db_path = db_path
        self.config = self.load_config()
        if headless_override is not None:
            self.headless = headless_override
        else:
            self.headless = self.config['search']['headless'] # Set config headless mode
        self.load_known_leads()

    def load_config(self):
        """Loads configuration from config.json, providing defaults if missing."""
        config_path = "config.json"
        defaults = {
            "segmentation": {
                "micro_max_reviews": 20,
                "good_rating_threshold": 3.5
            },
            "search": {
                "headless": False
            }
        }
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    loaded = json.load(f)
                    # Merge defaults with loaded to avoid KeyErrors
                    defaults['segmentation'].update(loaded.get('segmentation', {}))
                    defaults['search'].update(loaded.get('search', {}))
            except Exception as e:
                logger.info(f"[WARN] Could not load config.json ({e}). Using defaults.")
        return defaults

    def load_known_leads(self):
        """
        Loads existing leads from the database into memory to avoid re-scraping.
        """
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
            
        if not os.path.exists(self.db_path) and self.db_path != ':memory:':
            return

        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row # Access columns by name
            c = conn.cursor()
            
            # Check if table exists
            c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='leads'")
            if not c.fetchone():
                conn.close()
                return

            c.execute("SELECT * FROM leads")
            rows = c.fetchall()
            
            for row in rows:
                # Create a dictionary from the row
                data = dict(row)
                # Key: (name, zone) - Normalized slightly (strip)
                key = (data.get('name', '').strip(), data.get('zone', '').strip())
                if key[0]: # Ensure name is not empty
                    self.known_leads[key] = data
            
            conn.close()
            logger.info(f"[CACHE] Loaded {len(self.known_leads)} existing leads from database.")
        except Exception as e:
            logger.info(f"[CACHE] Error loading cache: {e}")

    async def scrape(self, zones, categories):
        """
        Main scraping loop.
        Iterates through all combinations of zones and categories.
        """
        async with async_playwright() as p:
            # Init browser
            # We use chromium. Launch options can be adjusted.
            browser = await p.chromium.launch(headless=self.headless)
            context = await browser.new_context(
                viewport={"width": 1280, "height": 800},
                locale="es-MX",
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
            )
            page = await context.new_page()

            # Clear session cache at the start of a new run
            self.seen_names = set()
            self.seen_phones = set()
            
            for zone in zones:
                for category in categories:
                    search_query = f"{category} en {zone}"
                    logger.info(f"\n--- Searching for: {search_query} ---")
                    
                    try:
                        await self.search_and_extract(page, search_query)
                    except Exception as e:
                        logger.info(f"Error scraping {search_query}: {e}")

            await browser.close()
            return self.results

    async def search_and_extract(self, page, query):
        """
        Performs the search on Google Maps, scrolls the results feed to load all items,
        and extracts details for each listing.
        """
        await page.goto("https://www.google.com/maps", timeout=60000)
        
        # Search input interaction
        # We wait for the search box, fill it, and press Enter to search.
        # Adding networkidle wait to ensure page loads fully
        try:
            await page.wait_for_load_state("networkidle", timeout=10000)
        except:
            pass # Continue even if network not idle

        search_box_selector = 'input#searchboxinput, input[name="q"], #searchboxinput'
        
        try:
            await page.wait_for_selector(search_box_selector, timeout=20000)
            await page.fill(search_box_selector, query)
            await page.press(search_box_selector, 'Enter')
        except Exception as e:
            logger.info(f"Could not find search box: {e}")
            # Check for consent page or other blockers?
            return
        
        # Wait for results feed to appear
        # The results list is usually contained in a div with role="feed"
        try:
             await page.wait_for_selector('div[role="feed"]', timeout=10000)
        except:
            logger.info(f"No results found for {query} or layout changed.")
            return

        # Scroll to load all results
        # We find the feed element and scroll it repeatedly.
        feed_selector = 'div[role="feed"]'
        
        logger.info("Scrolling results...")
        previous_height = 0
        scroll_attempts = 0
        max_scroll_attempts = 5  # Increased retries for stability

        while True:
            # JavaScript evaluation to scroll the specific feed element
            await page.evaluate(f'''
                (selector) => {{
                    const feed = document.querySelector(selector);
                    if (feed) feed.scrollTo(0, feed.scrollHeight);
                }}
            ''', feed_selector)
            
            # Wait for dynamic content loading - randomized slightly
            await page.wait_for_timeout(3000) 
            
            # Check if we reached the bottom by comparing scrollHeight
            try:
                new_height = await page.evaluate(f'''
                    (selector) => {{
                        const feed = document.querySelector(selector);
                        return feed ? feed.scrollHeight : 0;
                    }}
                ''', feed_selector)
            except:
                new_height = previous_height

            if new_height == previous_height:
                scroll_attempts += 1
                if scroll_attempts >= max_scroll_attempts:
                    logger.info("Reached end of list or no new items loaded.")
                    break
                logger.info(f"No new items... retrying ({scroll_attempts}/{max_scroll_attempts})")
            else:
                scroll_attempts = 0 # Reset attempts if we found new content
                previous_height = new_height
            
            # Extract current number of loaded items for progress logging
            items = await page.evaluate(f'''
                (selector) => {{
                    const feed = document.querySelector(selector);
                     return feed ? feed.querySelectorAll("div > div[role='article']").length : 0;
                }}
            ''', feed_selector)
            logger.info(f"Loaded {items} items...")

        logger.info(f"\nFinished scrolling. extracting details...")

        # Select all listing items
        listings = await page.query_selector_all(f'{feed_selector} > div > div[role="article"]')
        logger.info(f"Found {len(listings)} listings to process.")
        
        for i, listing in enumerate(listings):
            data = {}
            data['source'] = 'Google Maps' # Default source
            
            # Name extraction
            try:
                raw_label = await listing.get_attribute("aria-label")
                name = raw_label.strip() if raw_label else ""
                data['name'] = name
            except:
                continue
            
            if not name:
                continue

            # CHECK FOR CLOSED STATUS (Red text usually)
            # We check the full text of the listing card
            try:
                full_text = await listing.inner_text()
                if self.is_business_closed(full_text):
                    logger.info(f"[{i+1}/{len(listings)}] [SKIPPED] Closed: {name}")
                    continue
            except:
                pass

            # SMART CACHE CHECK
            # If this lead is already in our DB for this zone, skip scraping.
            cache_key = (name, query.strip())
            if cache_key in self.known_leads:
                # Load from Cache
                cached_data = self.known_leads[cache_key]
                # Update current data dict with cached values
                data.update(cached_data)
                data['_from_cache'] = True # Flag to avoid re-saving to DB
                
                self.results.append(data)
                logger.info(f"[{i+1}/{len(listings)}] [CACHE] Loaded from DB: {name}")
                continue

            # Process detail extraction (If not in cache)
            try:
                await listing.click()
                await page.wait_for_timeout(2000) # Increased wait for stability
                
                # Extract details
                # Address
                address_el = await page.query_selector('button[data-item-id="address"]')
                if address_el:
                        addr_text = await address_el.get_attribute("aria-label")
                        data['address'] = addr_text.replace("Address: ", "").replace("Dirección: ", "").strip()
                else:
                    data['address'] = "N/A"
                    
                # Phone
                phone_el = await page.query_selector('button[data-item-id^="phone"]')
                if phone_el:
                        phone_text = await phone_el.get_attribute("aria-label")
                        data['phone'] = phone_text.replace("Phone: ", "").replace("Teléfono: ", "").strip()
                else:
                    data['phone'] = "N/A"

                # Website
                website_el = await page.query_selector('a[data-item-id="authority"]')
                if website_el:
                    data['website'] = await website_el.get_attribute("href")
                else:
                    data['website'] = "N/A"

                try:
                    js_data = await self._extract_listing_data_via_js(page, name)
                    data['stars'] = js_data.get('stars', 0.0)
                    data['reviews'] = js_data.get('reviews', 0)

                except Exception as e:
                    logger.info(f"Error extracting reviews via JS: {e}")
                    data['stars'] = 0.0
                    data['reviews'] = 0

                # DEDUPLICATION CHECK (SESSION LEVEL) - AGGRESSIVE
                # Prioritize Phone for uniqueness, then Name
                norm_phone = re.sub(r'\D', '', str(data.get('phone', '')))
                if len(norm_phone) >= 10: 
                    norm_phone = norm_phone[-10:]
                    if norm_phone in self.seen_phones:
                        logger.info(f"  [SKIPPED] Phone {norm_phone} already processed: {data['name']}")
                        continue
                    self.seen_phones.add(norm_phone)
                else:
                    # If no valid phone, fallback to normalized name
                    norm_name = "".join(filter(str.isalnum, data['name'].lower()))
                    if norm_name in self.seen_names:
                        logger.info(f"  [SKIPPED] Name '{data['name']}' already processed (no phone).")
                        continue
                    self.seen_names.add(norm_name)
                
                # MAP URL
                data['map_url'] = page.url

            except Exception as ex:
                logger.info(f"Error extracting details for {data['name']}: {ex}")
                data['phone'] = "Error"
                data['address'] = "Error"
                data['map_url'] = page.url

            # FACEBOOK FALLBACK (DISABLED FOR SPEED - DEFERRED ENRICHMENT)
            # if phone is N/A or empty, we mark it but do NOT search now.
            if data.get('phone') in ["N/A", "Error", None, ""]:
                # logger.info(f"  Phone missing for {data['name']}. Trying Facebook fallback (via Bing)...")
                # fb_phone, fb_email, fb_url = await self.get_facebook_contact(page.context, data['name'], query)
                
                # Skipping fallback to speed up scraping
                data['source'] = 'Google Maps (No Phone)'
                logger.info(f"  [SKIPPED] Phone missing. Marked for pending lookup.")
                
                # Logic below is commented out for now
                # if fb_phone: ...
            else:
                 # Ensure email key exists
                 if 'email' not in data:
                     data['email'] = "N/A"

            data['zone'] = query
            self.results.append(data)
            logger.info(f"[{i+1}/{len(listings)}] Extracted: {data['name']} - Stars: {data.get('stars')} - Revs: {data.get('reviews')}")

    async def get_facebook_contact(self, context, business_name, zone):
        # ... (Method remains for future use) ...
        return None, None, "Skipped"

    @staticmethod
    def is_chain(name):
        blacklist = ['OXXO', '7-ELEVEN', 'WALMART', 'OFFICE DEPOT', 'HEB', 'SORIANA', 'FARMACIAS GUADALAJARA', 'FARMACIAS DEL AHORRO', 'COSTCO', 'HOME DEPOT']
        name_upper = str(name).upper()
        return any(brand in name_upper for brand in blacklist)

    def classify_lead(self, row):
        stars = float(row.get('stars', 0))
        reviews = int(row.get('reviews', 0))
        name = row.get('name', '')
        
        micro_limit = self.config['segmentation']['micro_max_reviews']
        good_rating = self.config['segmentation']['good_rating_threshold']
        
        if self.is_chain(name):
            return 'Corporate'
        
        # Corporate signal: > micro_limit reviews
        if reviews > micro_limit: 
            return 'Corporate'
        
        # Micro signal: <= micro_limit reviews (including 0)
        if reviews <= micro_limit:
            if reviews == 0:
                return 'Micro' # New or unreviewed business
            elif stars >= good_rating:
                return 'Micro' # Reviewed and okay/good rating
        
        return 'Other'

    @staticmethod
    def is_business_closed(full_text):
        """
        Checks if the business listing text indicates it is closed.
        Returns True if closed, False otherwise.
        """
        if not full_text:
            return False
        
        # Check against known keywords
        keywords = [
            "Temporarily closed",
            "Permanently closed",
            "Cerrado temporalmente",
            "Cerrado permanentemente"
        ]
        
        for kw in keywords:
            if kw in full_text:
                return True
        return False

    async def _extract_listing_data_via_js(self, page, business_name):
        """
        Isolated JS extraction logic for stars and reviews.
        """
        return await page.evaluate(rf'''
            (name) => {{
                // Safe selector: find by role and then filter by attribute in JS
                const articles = Array.from(document.querySelectorAll('div[role="article"]'));
                const article = articles.find(a => a.getAttribute('aria-label') === name);
                
                if (!article) return {{stars: 0, reviews: 0}};
                
                // Find all spans with aria-label containing stars/estrellas or reviews/opiniones
                const spans = Array.from(article.querySelectorAll('span[aria-label], button[aria-label]'));
                let stars = 0;
                let reviews = 0;
                
                for (const s of spans) {{
                    const label = s.getAttribute('aria-label');
                    if (!label) continue;
                    
                    // Stars check
                    if (label.includes('stars') || label.includes('estrellas')) {{
                        const sMatch = label.match(/(\d+([.,]\d+)?)/);
                        if (sMatch) stars = parseFloat(sMatch[1].replace(',', '.'));
                    }}
                    
                    // Reviews check (match the number explicitly BEFORE the word)
                    if (label.includes('reviews') || label.includes('opiniones') || label.includes('Reviews') || label.includes('Opiniones')) {{
                        // Match format "XX opiniones" or "XX reviews"
                        const rMatch = label.match(/([\d,.]+)\s*(opiniones|reviews)/i);
                        if (rMatch) reviews = parseInt(rMatch[1].replace(/[.,]/g, ''));
                        else {{
                            // Fallback if the layout is different but the word is there
                            const rMatchAny = label.match(/([\d,.]+)/g);
                            // If there are multiple numbers (e.g. rating and reviews), reviews is usually the last/largest one
                            if (rMatchAny && rMatchAny.length > 1) {{
                                reviews = parseInt(rMatchAny[rMatchAny.length - 1].replace(/[.,]/g, ''));
                            }} else if (rMatchAny) {{
                                 // If only one number but we know it's a review span (e.g. separate from rating span)
                                if (!label.includes('stars') && !label.includes('estrellas')) {{
                                    reviews = parseInt(rMatchAny[0].replace(/[.,]/g, ''));
                                }}
                            }}
                        }}
                    }}
                }}
                
                // Fallback for reviews: text inside parentheses (e.g., "(161)")
                if (reviews === 0) {{
                    const textMatch = article.innerText.match(/\(([\d,.]+)\)/);
                    if (textMatch) reviews = parseInt(textMatch[1].replace(/[.,]/g, ''));
                }}
                
                return {{stars, reviews}};
            }}
        ''', business_name)

    # ... (rest of class) ...

    def save_to_db(self):
        """
        Saves the results to a SQLite database 'data/leads.db'.
        Enforces PRIMARY KEY (name, zone) to prevent duplicates.
        """
        if not self.results:
            return

        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # Create table if not exists with PRIMARY KEY constraint
        # Added stars (real), reviews (int), and map_url (text)
        c.execute('''CREATE TABLE IF NOT EXISTS leads 
                     (name text, phone text, address text, website text, zone text, email text, source text, stars real, reviews integer, map_url text,
                     PRIMARY KEY (name, zone))''')
        
        # Get all keys from the first result to determine columns (or use fixed list)
        columns = ['name', 'phone', 'address', 'website', 'zone', 'email', 'source', 'stars', 'reviews', 'map_url']
        
        column_names = ", ".join(columns)
        placeholders = ", ".join(["?"] * len(columns))
        
        # Use INSERT OR IGNORE to skip duplicates automatically
        insert_sql = f"INSERT OR IGNORE INTO leads ({column_names}) VALUES ({placeholders})"


        new_count = 0
        for item in self.results:
            # Skip if loaded from cache (double check, though DB handles it now too)
            if item.get('_from_cache'):
                continue
                
            values = []
            for col in columns:
                if col == 'stars':
                    val = item.get(col, 0.0)
                elif col == 'reviews':
                    val = item.get(col, 0)
                else:
                    val = item.get(col, "N/A")
                values.append(val)
            
            c.execute(insert_sql, values)
            if c.rowcount > 0: # Check if a row was actually inserted
                new_count += 1

        conn.commit()
        conn.close()
        logger.info(f"Data saved to database ({self.db_path}) - {new_count} new rows added (duplicates ignored).")

    def save_data(self):
        """
        Saves the accumulated results to Excel and SQLite database.
        
        Outputs:
        1. leads_google_maps.xlsx: Master list of leads with Phones.
        2. leads_pending_lookup.xlsx: Leads without Phones (for enrichment).
        3. leads_micro.xlsx: Specialized list for "Micro/Personal" targets (Son).
        4. leads_corporate.xlsx: Specialized list for "Corporate/SMB" targets (Accountant).
        """
        if not self.results:
            logger.info("No data collected to save.")
            return

        df = pd.DataFrame(self.results)
        
        # 1. DATA CLEANING & NORMALIZATION (Global)
        desired_columns = ['source', 'name', 'phone', 'email', 'address', 'website', 'map_url', 'zone', 'stars', 'reviews']
        
        # Ensure columns exist
        for col in desired_columns:
            if col not in df.columns:
                if col in ['stars', 'reviews']:
                    df[col] = 0
                else:
                    df[col] = "N/A"

        # REORDER
        df = df[desired_columns]

        # CLEAN PHONES (MEXICO 10 DIGITS)
        def clean_phone(p):
            if pd.isna(p) or str(p).strip().upper() in ["N/A", "ERROR", "NAN", ""]:
                return "N/A"
            # Keep only digits
            cleaned = re.sub(r'\D', '', str(p))
            # Handle Mexico prefixes (52, 521, etc.)
            if cleaned.startswith('521') and len(cleaned) > 10:
                cleaned = cleaned[3:]
            elif cleaned.startswith('52') and len(cleaned) > 10:
                cleaned = cleaned[2:]
            
            # Return last 10 digits if it's longer, else keep as is for validation
            if len(cleaned) >= 10:
                return cleaned[-10:]
            return "N/A" # If less than 10 digits, it's not a valid Mexico phone for our needs

        df['phone'] = df['phone'].apply(clean_phone)

        # 2. DEDUPLICATION (Priorities: Phone and Name)
        # We want to keep unique entries across all files
        df.drop_duplicates(subset=['name', 'phone'], keep='first', inplace=True)

        # FILL N/A GLOBALLY
        df.fillna("N/A", inplace=True)
        # Ensure numeric fields are actually numeric
        df['stars'] = pd.to_numeric(df['stars'], errors='coerce').fillna(0)
        df['reviews'] = pd.to_numeric(df['reviews'], errors='coerce').fillna(0)

        # 3. STRICT SEPARATION: PHONE VS NO PHONE
        # DATAFRAME FOR MASTER / MICRO / CORPORATE (MUST HAVE PHONE)
        df_valid = df[df['phone'] != "N/A"].copy()
        
        # DATAFRAME FOR PENDING LOOKUP (NO PHONE)
        df_pending = df[df['phone'] == "N/A"].copy()
        
        logger.info(f"[INFO] Processing: {len(df)} unique items. {len(df_valid)} valid phones. {len(df_pending)} pending.")

        # 4. SEGMENTATION STRATEGY (Applied only to df_valid)
        if not df_valid.empty:
            df_valid['segment'] = df_valid.apply(lambda row: self.classify_lead(row), axis=1)
            # Remove any residual duplicates just in case before splitting
            df_valid.drop_duplicates(subset=['name', 'phone'], inplace=True)
            
            # Calculate discarded leads (Poor reviews)
            discarded_count = len(df_valid[df_valid['segment'] == 'Other'])
            if discarded_count > 0:
                logger.info(f"[INFO] Discarded {discarded_count} leads due to poor Google ratings (< {self.config['segmentation']['good_rating_threshold']} stars).")
            
            # Update Master List (df_valid) to ONLY include Micro and Corporate
            df_valid = df_valid[df_valid['segment'].isin(['Micro', 'Corporate'])].copy()
            
            df_micro = df_valid[df_valid['segment'] == 'Micro'].copy()
            df_corporate = df_valid[df_valid['segment'] == 'Corporate'].copy()
        else:
            df_micro = pd.DataFrame(columns=desired_columns)
            df_corporate = pd.DataFrame(columns=desired_columns)

        # 5. EXPORTS (No duplicates, no missing phones in master/micro/corporate)
        
        from src.infrastructure.database.storage_service import StorageService
        logger.info(f"\n📁 Guardando todos los archivos exportados usando StorageService...")
        
        # A. Master List (Valid Phones Only)
        try:
            if not df_valid.empty:
                file_path = StorageService.guardar_excel(df_valid.drop(columns=['segment'], errors='ignore'), self.session_id, "leads_google_maps.xlsx")
                logger.info(f"[SUCCESS] Exported {len(df_valid)} unique leads to {file_path}")
        except Exception as e:
            logger.info(f"[ERROR] Master Export: {e}")

        # B. Micro List (Valid Phones Only)
        try:
            if not df_micro.empty:
                file_path = StorageService.guardar_excel(df_micro.drop(columns=['segment'], errors='ignore'), self.session_id, "leads_micro.xlsx")
                logger.info(f"[SUCCESS] Exported {len(df_micro)} unique MICRO leads to {file_path}")
        except Exception as e:
             logger.info(f"[ERROR] Micro Export: {e}")

        # C. Corporate List (Valid Phones Only)
        try:
            if not df_corporate.empty:
                file_path = StorageService.guardar_excel(df_corporate.drop(columns=['segment'], errors='ignore'), self.session_id, "leads_corporate.xlsx")
                logger.info(f"[SUCCESS] Exported {len(df_corporate)} unique CORPORATE leads to {file_path}")
        except Exception as e:
             logger.info(f"[ERROR] Corporate Export: {e}")
             
        # D. Pending List (No Phones)
        try:
            if not df_pending.empty:
                file_path = StorageService.guardar_excel(df_pending, self.session_id, "leads_pending_lookup.xlsx")
                logger.info(f"[SUCCESS] Exported {len(df_pending)} unique pending leads to {file_path}")
        except Exception as e:
             logger.info(f"[ERROR] Pending Export: {e}")

        # 5. Save to DB All Data (Valid + Pending)
        try:
            self.save_to_db()
        except Exception as e:
            logger.info(f"[ERROR] Could not save to Database: {e}")

async def main():
    parser = argparse.ArgumentParser(description="Google Maps Leads Scraper")
    parser.add_argument('--zones', type=str, help="Zones/cities separated by semicolon")
    parser.add_argument('--categories', type=str, help="Categories separated by semicolon")
    parser.add_argument('--session-id', type=str, help="Session ID to save the results")
    args = parser.parse_args()

    logger.info("Welcome to the Google Maps Leads Scraper")
    logger.info("----------------------------------------")
    
    is_agent = False
    if args.zones and args.categories:
        zones_input = args.zones
        cats_input = args.categories
        is_agent = True
    else:
        # User Input
        logger.info("Enter the zones/cities (separated by semicolon). Example: Monterrey; Santiago, Nuevo Leon")
        zones_input = input("Zones: ")
        
        logger.info("Enter the categories (separated by semicolon). Example: Tiendas de abarrotes; Farmacias")
        cats_input = input("Categories: ")
    
    # Process inputs
    zones = [z.strip() for z in zones_input.split(";") if z.strip()]
    categories = [c.strip() for c in cats_input.split(";") if c.strip()]
    
    if not zones or not categories:
        logger.info("Error: You must provide at least one zone and one category.")
        return

    scraper = GoogleMapsScraper(headless_override=True if is_agent else None, session_id=args.session_id)
    await scraper.scrape(zones, categories)
    
    # Save Results
    scraper.save_data()
    logger.info("\nJob Completed.")

if __name__ == "__main__":
    asyncio.run(main())
