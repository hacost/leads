import asyncio
from playwright.async_api import async_playwright
import pandas as pd
import os
import re
import sys

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


class EnrichmentScraper:
    def __init__(self, input_file="leads_pending_lookup.xlsx", output_file="leads_pending_lookup.xlsx"):
        self.input_file = input_file
        self.output_file = output_file
        self.results = []
        
    async def process_leads(self):
        if not os.path.exists(self.input_file):
            print(f"Input file {self.input_file} not found.")
            return

        # Load as string to avoid type issues with N/A values
        df = pd.read_excel(self.input_file, dtype=str)
        print(f"Loaded {len(df)} pending leads.")
        
        # Normalize columns to avoid "nan" string issues
        df.replace("nan", "N/A", inplace=True)
        df.replace("NaN", "N/A", inplace=True)
        
        async with async_playwright() as p:
            # HEADFUL MODE: Visible browser for manual intervention
            browser = await p.chromium.launch(headless=False)
            context = await browser.new_context()
            page = await context.new_page()
            
            for index, row in df.iterrows():
                # Skip if already has phone (just in case)
                # Check for "N/A", "nan", "None", "", or "Error"
                phone_curr = str(row.get('phone', 'N/A')).strip()
                if phone_curr not in ["N/A", "nan", "Error", "None", ""]:
                    continue
                
                # Skip if we already checked it (marked as Enriched)
                source_curr = str(row.get('source', '')).strip()
                if "Enriched" in source_curr:
                     print(f"[{index+1}/{len(df)}] Skipping {row['name']} (Already Enriched)")
                     continue
                
                print(f"\n[{index+1}/{len(df)}] Processing: {row['name']} ({row['zone']})")
                
                try:
                    # Google Search
                    query = f"Facebook {row['name']} {row['zone']}"
                    await page.goto("https://www.google.com")
                    
                    # Handle Consent Popup (if any)
                    try:
                        # Common selectors for "Accept all" or "Rechazar todo"
                        consent_button = await page.query_selector('button:has-text("Aceptar todo"), button:has-text("Accept all")')
                        if consent_button:
                            print("  [INFO] Clicking Google Consent...")
                            await consent_button.click()
                            await page.wait_for_timeout(1000)
                    except:
                        pass

                    # Wait for search box - standard now is usually textarea, but we try both
                    search_box = await page.wait_for_selector('textarea[name="q"], input[name="q"]', state="visible", timeout=15000)
                    await search_box.fill(query)
                    await search_box.press("Enter")
                    
                    # Wait for results while allowing manual Captcha solving
                    print("  [WAIT] Waiting up to 60s for results (or solve Captcha manually)...")
                    found_results = False
                    for i in range(12): # 12 * 5s = 60s
                        try:
                            # Check if ANY result-like element is visible (e.g., headers or search container)
                            # Checking for common result indicators: h3, #search, #rso
                            if await page.query_selector('#search') or await page.query_selector('h3'):
                                found_results = True
                                print("  [INFO] Results page detected! Continuing...")
                                break
                        except Exception as e:
                            # Context destroyed means page navigated (good sign), retry next loop.
                            pass
                        
                        # Wait 5 seconds before checking again
                        print(f"  ...waiting ({i+1}/12 checks)...")
                        await page.wait_for_timeout(5000)
                    
                    if not found_results:
                         print("  [WARN] No results found after 60s (or Captcha not solved).")

                    # Extract Best Facebook Result
                    # 1. Get all links
                    # 2. Filter for facebook.com
                    # 3. Take the first valid one
                    links = await page.query_selector_all('a[href*="facebook.com"]')
                    fb_url = None
                    
                    for link in links:
                        href = await link.get_attribute('href')
                        if href and "facebook.com" in href and "google.com" not in href and "search?" not in href:
                             fb_url = href
                             break
                    
                    if fb_url:
                        print(f"  Found FB URL: {fb_url}")
                        # Ensure we don't overwrite map_url by mistake
                        # df.at[index, 'map_url'] = fb_url # Removed to preserve original Google Maps URL
                        
                        await page.goto(fb_url)
                        await page.wait_for_timeout(4000)
                        
                        # Close generic login popups if possible (optional try)
                        try:
                            close_btn = await page.query_selector('div[aria-label="Close"], div[aria-label="Cerrar"]')
                            if close_btn:
                                await close_btn.click()
                        except:
                            pass

                        # --- DUAL STRATEGY: PAGE PROFILE + POSTS ---
                        found_phone = None
                        
                        # 1. Post-to-Page Navigation: If we landed on a specific post, try to go to the main page first
                        is_post = any(x in fb_url.lower() for x in ["/posts/", "/photos/", "/videos/", "/permalink/", "/fbid="])
                        if is_post:
                            print("  [INFO] landed on a post. Attempting to navigate to Page Profile for full info...")
                            try:
                                page_links = await page.query_selector_all('strong a, h1 a, h2 a, a[role="link"]:has-text("")')
                                for pl in page_links:
                                    href_pl = await pl.get_attribute('href')
                                    if href_pl and "facebook.com" in href_pl and not any(x in href_pl.lower() for x in ["/posts/", "/photos/", "/videos/"]):
                                        await pl.click()
                                        await page.wait_for_timeout(3000)
                                        print(f"  [INFO] Navigated to Page: {page.url}")
                                        break
                            except:
                                pass

                        # --- STRATEGY A: INTRO SECTION ---
                        # Target Introduction/About sidebar specifically, fallback to body
                        intro_text = ""
                        try:
                            # Typically the Intro section has this structure on modern FB
                            intro_element = await page.query_selector('div:has-text("Intro"), div:has-text("Información")')
                            if intro_element:
                                # Get parent or just evaluate for text to be safe
                                intro_text = await page.evaluate('(el) => el.innerText', intro_element)
                        except:
                            pass
                            
                        # If we couldn't isolate Intro, grab visible text (as fallback, but limited to avoid massive noise)
                        if len(intro_text) < 20:
                             intro_text = await page.inner_text('body')

                        # Extract Email First (High priority)
                        email_pattern = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')
                        email_matches = email_pattern.findall(intro_text)
                        valid_emails = [e for e in email_matches if "example.com" not in e and ".png" not in e and ".jpg" not in e]
                        if valid_emails:
                            email = valid_emails[0].strip()
                            print(f"  [SUCCESS] Found Email: {email}")
                            df.at[index, 'email'] = str(email)

                        # Search for 'tel:' links in Profile
                        tel_link = await page.query_selector('a[href^="tel:"]')
                        if tel_link:
                            href_tel = await tel_link.get_attribute('href')
                            raw_tel = re.sub(r'[^\d]', '', href_tel)
                            if len(raw_tel) >= 10:
                                found_phone = raw_tel[-10:]
                                print(f"  [SUCCESS] Found Phone (via Profile tel: link): {found_phone}")

                        # Regex on Intro Text
                        if not found_phone:
                            phone_pattern = re.compile(r'(\+?\d{1,4}?[-.\s]?\(?\d{2,3}?\)?[-.\s]?\d{3,4}[-.\s]?\d{4})')
                            matches = phone_pattern.findall(intro_text)
                            for m in matches:
                                clean_num = re.sub(r'[^\d]', '', m)
                                if len(clean_num) >= 10:
                                    if clean_num.startswith('521') and len(clean_num) > 10: clean_num = clean_num[3:]
                                    elif clean_num.startswith('52') and len(clean_num) > 10: clean_num = clean_num[2:]
                                    
                                    if len(clean_num) >= 10:
                                        final_num = clean_num[-10:]
                                        if not final_num.startswith("1000"):
                                            found_phone = final_num
                                            print(f"  [SUCCESS] Found Phone (via Intro text): {found_phone}")
                                            break

                        # --- STRATEGY B: POSTS (First 3 only) ---
                        if not found_phone:
                            print("  [INFO] Phone not found in Intro, searching first 3 posts...")
                            try:
                                # Facebook often uses elements with role="article" for posts
                                posts = await page.query_selector_all('div[role="article"]')
                                # Take up to first 3
                                text_to_scan = ""
                                for i in range(min(3, len(posts))):
                                    post_text = await page.evaluate('(el) => el.innerText', posts[i])
                                    text_to_scan += " " + (post_text or "")
                                
                                # Check WA Links inside these posts or globally
                                wa_links = await page.query_selector_all('a[href*="wa.me"], a[href*="whatsapp.com/send"]')
                                for wa in wa_links:
                                    wa_href = await wa.get_attribute('href')
                                    wa_match = re.search(r'(?:phone=|wa\.me/|send\?phone=)(\d+)', wa_href)
                                    if wa_match:
                                        wa_num = wa_match.group(1)
                                        if len(wa_num) >= 10:
                                            found_phone = wa_num[-10:]
                                            print(f"  [SUCCESS] Found Phone (via WhatsApp link): {found_phone}")
                                            break
                                            
                                # If no WA link, check the aggregated text of the first 3 posts
                                if not found_phone and text_to_scan:
                                    matches = phone_pattern.findall(text_to_scan)
                                    for m in matches:
                                        clean_num = re.sub(r'[^\d]', '', m)
                                        if len(clean_num) >= 10:
                                            if clean_num.startswith('521') and len(clean_num) > 10: clean_num = clean_num[3:]
                                            elif clean_num.startswith('52') and len(clean_num) > 10: clean_num = clean_num[2:]
                                            
                                            if len(clean_num) >= 10:
                                                final_num = clean_num[-10:]
                                                if not final_num.startswith("1000"):
                                                    found_phone = final_num
                                                    print(f"  [SUCCESS] Found Phone (via Post text): {found_phone}")
                                                    break
                            except Exception as e:
                                print(f"  [WARN] Error scanning posts: {e}")

                        # Save Final Result (Ensure "N/A" if nothing found)
                        if found_phone:
                            df.at[index, 'phone'] = str(found_phone)
                            df.at[index, 'source'] = 'Enriched (FB Phone Captured)'
                        else:
                            print(f"  [Partial] FB found but no valid 10-digit phone found.")
                            df.at[index, 'phone'] = "N/A"
                            df.at[index, 'source'] = 'Enriched (FB Contact Info Missing)'
                    else:
                         print(f"  No Facebook link found in results.")
                         # df.at[index, 'source'] = 'Enriched (Not Found)'
                except Exception as e:
                    print(f"  Error: {e}")
                
                # Save progress row by row
                df.to_excel(self.output_file, index=False)
                
            await browser.close()
            print("\nEnrichment Complete.")

if __name__ == "__main__":
    enricher = EnrichmentScraper()
    asyncio.run(enricher.process_leads())
