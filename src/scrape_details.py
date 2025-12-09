"""
Philippine Rental Property Details Scraper - Batch Processing
Scrapes detailed information with resume capability
"""
import pandas as pd
import time
import re
import random
import os
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed

# ========== CONFIGURATION ==========
OUTPUT_PATH = 'C:/Users/anhpd/OneDrive/Desktop/projects/phillipine-rental-price/data'
LINKS_FILE = 'C:/Users/anhpd/OneDrive/Desktop/projects/phillipine-rental-price/data/property_links_raw_20251128_143215.csv'  # UPDATE THIS

# Batch settings
BATCH_SIZE = 100  # Process 100 at a time
BATCH_START = 1   # Start from batch 0 (change this to resume)

# Scraping settings
MAX_WORKERS = 5 
HEADLESS = True  
PAGE_LOAD_WAIT = 3  
RETRY_ATTEMPTS = 3  

# ========== HELPER FUNCTIONS ==========
def create_driver(headless=HEADLESS):
    """Create a Chrome WebDriver with anti-detection settings."""
    chrome_options = Options()
    if headless:
        chrome_options.add_argument('--headless=new')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    # Suppress logs
    chrome_options.add_argument('--disable-quic')
    chrome_options.add_argument('--log-level=3')
    chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
    
    # User agent
    user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'
    chrome_options.add_argument(f'user-agent={user_agent}')
    chrome_options.add_argument('--window-size=1920,1080')
    
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=chrome_options
    )
    
    driver.execute_cdp_cmd('Network.setUserAgentOverride', {
        "userAgent": user_agent,
        "platform": "Windows"
    })
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    return driver

def scrape_property_details(url, attempt=1):
    """Scrape detailed information from individual property page."""
    
    driver = None
    try:
        driver = create_driver()
        driver.get(url)
        time.sleep(PAGE_LOAD_WAIT)
        
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        # Extract title - if this fails, the page didn't load properly
        title_elem = soup.find('div', class_='main-title')
        title = title_elem.find('h1').get_text(strip=True) if title_elem and title_elem.find('h1') else None
        
        # If no title found, page didn't load properly
        if not title:
            raise Exception("No title found - page may not have loaded")
        
        # Extract price
        price_elem = soup.find('div', class_='prices-and-fees__price', attrs={'data-test': 'listing-price'})
        price_text = price_elem.get_text(strip=True) if price_elem else None
        price = None
        if price_text:
            price_match = re.search(r'₱\s*([\d,]+)', price_text)
            if price_match:
                price = int(price_match.group(1).replace(',', ''))
        
        # Extract bedrooms
        bedrooms_elem = soup.find('div', class_='details-item-value', attrs={'data-test': 'bedrooms-value'})
        bedrooms_text = bedrooms_elem.get_text(strip=True) if bedrooms_elem else None
        bedrooms = None
        if bedrooms_text:
            bed_match = re.search(r'(\d+)', bedrooms_text)
            if bed_match:
                bedrooms = int(bed_match.group(1))
        
        # Extract bathrooms
        bathrooms_elem = soup.find('div', class_='details-item-value', attrs={'data-test': 'full-bathrooms-value'})
        bathrooms_text = bathrooms_elem.get_text(strip=True) if bathrooms_elem else None
        bathrooms = None
        if bathrooms_text:
            bath_match = re.search(r'(\d+)', bathrooms_text)
            if bath_match:
                bathrooms = int(bath_match.group(1))
        
        # Extract location
        location_elem = soup.find('div', class_='view-map__text')
        location = location_elem.get_text(strip=True) if location_elem else None
        
        # Extract description
        desc_elem = soup.find('div', id='description-text', class_='content')
        description = desc_elem.get_text(strip=True)[:500] if desc_elem else None
        
        # Extract furnishing status
        furnishing = None
        facilities_items = soup.find_all('div', class_='facilities__item')
        for item in facilities_items:
            text = item.get_text(strip=True).lower()
            if 'furnished' in text:
                furnishing = item.get_text(strip=True)
                break
        
        # Extract amenities
        amenities = []
        for item in facilities_items:
            amenity_text = item.get_text(strip=True)
            if amenity_text and amenity_text not in ['Garage', 'Alarm']:
                amenities.append(amenity_text)
        amenities_str = ', '.join(amenities[:10]) if amenities else None
        
        # Extract floor area
        floor_area = None
        floor_items = soup.find_all('div', class_='details-item-value')
        for item in floor_items:
            text = item.get_text(strip=True)
            if 'sqm' in text.lower() or 'm²' in text:
                area_match = re.search(r'([\d,\.]+)\s*(?:sqm|m²)', text, re.I)
                if area_match:
                    floor_area = float(area_match.group(1).replace(',', ''))
                    break
        
        # Extract coordinates
        latitude = None
        longitude = None
        
        scripts = soup.find_all('script')
        for script in scripts:
            if script.string:
                lat_patterns = [
                    r'["\']?lat(?:itude)?["\']?\s*[:=]\s*([\d\.\-]+)',
                    r'lat:\s*([\d\.\-]+)',
                    r'"lat":\s*([\d\.\-]+)',
                ]
                lng_patterns = [
                    r'["\']?lon(?:g|gitude)?["\']?\s*[:=]\s*([\d\.\-]+)',
                    r'lng:\s*([\d\.\-]+)',
                    r'"lng":\s*([\d\.\-]+)',
                ]
                
                for lat_pattern in lat_patterns:
                    lat_match = re.search(lat_pattern, script.string, re.I)
                    if lat_match:
                        latitude = float(lat_match.group(1))
                        break
                
                for lng_pattern in lng_patterns:
                    lng_match = re.search(lng_pattern, script.string, re.I)
                    if lng_match:
                        longitude = float(lng_match.group(1))
                        break
                
                if latitude and longitude:
                    break
        
        if not latitude or not longitude:
            map_elem = soup.find('div', id='map')
            if map_elem:
                latitude = map_elem.get('data-lat') or map_elem.get('data-latitude')
                longitude = map_elem.get('data-lng') or map_elem.get('data-longitude')
                if latitude:
                    latitude = float(latitude)
                if longitude:
                    longitude = float(longitude)
        
        if not latitude or not longitude:
            json_ld = soup.find('script', type='application/ld+json')
            if json_ld:
                try:
                    import json
                    data_json = json.loads(json_ld.string)
                    if isinstance(data_json, dict):
                        if '@graph' in data_json:
                            for item in data_json['@graph']:
                                if isinstance(item, dict) and 'geo' in item:
                                    geo = item.get('geo', {})
                                    latitude = float(geo.get('latitude')) if geo.get('latitude') else None
                                    longitude = float(geo.get('longitude')) if geo.get('longitude') else None
                                    if latitude and longitude:
                                        break
                        else:
                            geo = data_json.get('geo', {})
                            latitude = float(geo.get('latitude')) if geo.get('latitude') else None
                            longitude = float(geo.get('longitude')) if geo.get('longitude') else None
                except:
                    pass
        
        # ADD THIS SUCCESS MESSAGE
        title_preview = title[:40] if title else 'Unknown'
        price_str = f"₱{price:,}" if price else 'N/A'
        coord_str = f"({latitude:.4f},{longitude:.4f})" if latitude and longitude else 'No coords'
        print(f"   ✅ {title_preview}... | {price_str} | {coord_str}")
        
        return {
            'url': url,
            'title': title,
            'price_php': price,
            'bedrooms': bedrooms,
            'bathrooms': bathrooms,
            'floor_area_sqm': floor_area,
            'location': location,
            'latitude': latitude,
            'longitude': longitude,
            'description': description,
            'furnishing': furnishing,
            'amenities': amenities_str,
            'scrape_status': 'success'
        }
    
    except Exception as e:
        # Retry logic
        if attempt < RETRY_ATTEMPTS:
            print(f"   ⚠️  Attempt {attempt} failed, retrying... ({str(e)[:50]})")
            if driver:
                driver.quit()
            time.sleep(3)
            return scrape_property_details(url, attempt + 1)
        else:
            print(f"   ❌ Failed after {RETRY_ATTEMPTS} attempts: {str(e)[:50]}")
            return {
                'url': url,
                'title': None,
                'price_php': None,
                'bedrooms': None,
                'bathrooms': None,
                'floor_area_sqm': None,
                'location': None,
                'latitude': None,
                'longitude': None,
                'description': None,
                'furnishing': None,
                'amenities': None,
                'scrape_status': f'failed: {str(e)[:100]}'
            }
    finally:
        if driver:
            driver.quit()


# ========== MAIN EXECUTION ==========
# ========== MAIN EXECUTION ==========
def main():
    """Main batch scraping workflow with parallel execution."""
    print("=" * 70)
    print("PHILIPPINE RENTAL PROPERTY DETAILS SCRAPER - BATCH MODE")
    print("=" * 70)
    
    # Load links file
    print(f"\n📂 Loading links from: {LINKS_FILE}")
    try:
        links_df = pd.read_csv(LINKS_FILE)
        print(f"✅ Loaded {len(links_df)} property links\n")
    except Exception as e:
        print(f"❌ Error loading file: {e}")
        return
    
    # Randomization
    print("🔀 Randomizing property order...")
    links_df = links_df.sample(frac=1, random_state=42).reset_index(drop=True)
    print("✅ Properties randomized\n")
    
    # Calculate batches
    total_properties = len(links_df)
    total_batches = (total_properties // BATCH_SIZE) + (1 if total_properties % BATCH_SIZE else 0)
    
    print(f"📊 BATCH CONFIGURATION:")
    print(f"   Total properties: {total_properties}")
    print(f"   Batch size: {BATCH_SIZE}")
    print(f"   Total batches: {total_batches}")
    print(f"   Starting from batch: {BATCH_START}")
    print(f"   Parallel workers: {MAX_WORKERS}")
    print(f"   Estimated time per batch: ~{BATCH_SIZE * PAGE_LOAD_WAIT / 60 / MAX_WORKERS:.1f} minutes")
    print(f"   Estimated total time: ~{(total_batches - BATCH_START) * BATCH_SIZE * PAGE_LOAD_WAIT / 3600 / MAX_WORKERS:.1f} hours\n")
    
    # Track all failed URLs across batches
    all_failed_urls = []
    
    # Process batches
    for batch_num in range(BATCH_START, total_batches):
        print("\n" + "=" * 70)
        print(f"BATCH {batch_num + 1}/{total_batches}")
        print("=" * 70)
        
        # Get batch URLs
        start_idx = batch_num * BATCH_SIZE
        end_idx = min(start_idx + BATCH_SIZE, total_properties)
        batch_df = links_df.iloc[start_idx:end_idx].copy()
        urls_to_scrape = batch_df['url'].tolist()
        
        # Shuffle URLs within batch
        random.shuffle(urls_to_scrape)
        
        print(f"Processing properties {start_idx + 1} to {end_idx}")
        
        batch_start_time = time.time()
        details_list = []
        
        # ========== PARALLEL EXECUTION WITH ThreadPoolExecutor ==========
        from concurrent.futures import ThreadPoolExecutor, as_completed
        
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            # Submit all URLs to the thread pool
            future_to_url = {executor.submit(scrape_property_details, url): url for url in urls_to_scrape}
            
            completed = 0
            # Process results as they complete
            for future in as_completed(future_to_url):
                url = future_to_url[future]
                completed += 1
                
                try:
                    result = future.result()
                    details_list.append(result)
                    
                    # Track failed URLs
                    if result['scrape_status'] != 'success':
                        all_failed_urls.append(url)
                        
                except Exception as e:
                    print(f"   ❌ Exception for {url}: {str(e)[:50]}")
                    all_failed_urls.append(url)
                    # Add failed entry
                    details_list.append({
                        'url': url,
                        'title': None,
                        'price_php': None,
                        'bedrooms': None,
                        'bathrooms': None,
                        'floor_area_sqm': None,
                        'location': None,
                        'latitude': None,
                        'longitude': None,
                        'description': None,
                        'furnishing': None,
                        'amenities': None,
                        'scrape_status': f'exception: {str(e)[:100]}'
                    })
                
                # Progress update every 10 completions
                if completed % 10 == 0:
                    elapsed = time.time() - batch_start_time
                    rate = completed / elapsed * 60  # properties per minute
                    remaining = len(urls_to_scrape) - completed
                    eta = remaining / rate if rate > 0 else 0
                    print(f"   ⏱️  Progress: {completed}/{len(urls_to_scrape)} | Rate: {rate:.1f}/min | ETA: {eta:.1f}m")
        # ================================================================
        
        # Save batch results
        batch_details_df = pd.DataFrame(details_list)
        batch_final_df = pd.merge(batch_details_df, batch_df, on='url', how='left')
        
        # Save batch file
        batch_file = f"{OUTPUT_PATH}/property_details_batch_{batch_num:03d}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        batch_final_df.to_csv(batch_file, index=False, encoding='utf-8-sig')
        
        # Save failed URLs from this batch
        batch_failed = batch_final_df[batch_final_df['scrape_status'] != 'success']
        if not batch_failed.empty:
            failed_batch_file = f"{OUTPUT_PATH}/failed_urls_batch_{batch_num:03d}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            batch_failed[['url', 'scrape_status']].to_csv(failed_batch_file, index=False, encoding='utf-8-sig')
            print(f"   💾 Failed URLs saved: {failed_batch_file}")
        
        # Batch summary
        successful = len(batch_final_df[batch_final_df['scrape_status'] == 'success'])
        failed = len(batch_final_df[batch_final_df['scrape_status'] != 'success'])
        
        batch_elapsed = time.time() - batch_start_time
        actual_rate = len(urls_to_scrape) / batch_elapsed * 60
        
        print(f"\n✅ Batch {batch_num + 1} complete!")
        print(f"   Success: {successful}/{len(urls_to_scrape)}")
        print(f"   Failed: {failed}/{len(urls_to_scrape)}")
        print(f"   Time: {batch_elapsed/60:.1f} minutes")
        print(f"   Actual rate: {actual_rate:.1f} properties/min")
        print(f"   Saved: {batch_file}")
        
        # Take a break between batches (except for last batch)
        if batch_num < total_batches - 1:
            break_time = random.uniform(30, 60)
            print(f"\n⏸️  Taking a {break_time/60:.1f} minute break before next batch...")
            time.sleep(break_time)
    
    # Save consolidated list of ALL failed URLs
    if all_failed_urls:
        failed_urls_file = f"{OUTPUT_PATH}/failed_urls_all_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        failed_df = pd.DataFrame({'url': all_failed_urls})
        failed_df = failed_df.drop_duplicates().reset_index(drop=True)
        failed_df.to_csv(failed_urls_file, index=False, encoding='utf-8-sig')
        print(f"\n💾 ALL FAILED URLs saved: {failed_urls_file}")
        print(f"   Total failed: {len(failed_df)}")
    
    print("\n" + "=" * 70)
    print("✅ ALL BATCHES COMPLETE!")
    print("=" * 70)
    print("\nNext steps:")
    print("1. Combine batches: python combine_batches.py")
    print("2. Re-scrape failed: python rescrape_failed.py")

if __name__ == '__main__':
    main()