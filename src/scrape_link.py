"""
Philippine Rental Property Link Scraper
Scrapes property listing URLs from search pages
"""
import pandas as pd
import time
import re
import random
import concurrent.futures
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

# ========== CONFIGURATION ==========
CITIES = [
    'mandaluyong',
    'quezon-city',
    'makati',         
    'pasay',                  
    'marikina',
    'pasig',
    'san-juan'
]

PROPERTY_TYPES = [
    'condo',
    'apartment',
]

REGION = 'metro-manila'
OUTPUT_PATH = 'C:/Users/anhpd/OneDrive/Desktop/projects/phillipine-rental-price/data'
MAX_WORKERS = 3
HEADLESS = True
PAGE_LOAD_WAIT = 5

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
    
    # Suppress QUIC errors
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
    
    # Execute CDP commands
    driver.execute_cdp_cmd('Network.setUserAgentOverride', {
        "userAgent": user_agent,
        "platform": "Windows"
    })
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    return driver

def extract_links_from_soup(soup, city, prop_type):
    """Extract property links from search results page."""
    property_data = []
    
    # Find all property listing containers
    snippets = soup.find_all('div', class_='snippet')
    print(f"   Found {len(snippets)} property snippets")
    
    for snippet in snippets:
        # Get property link
        link_elem = snippet.find('a', href=re.compile(r'/property/'))
        if not link_elem:
            continue
        
        href = link_elem.get('href')
        if href.startswith('/'):
            href = f'https://www.lamudi.com.ph{href}'
        
        # Get property ID from data attributes
        prop_id = snippet.get('data-idanuncio') or snippet.get('data-alternateid')
        
        # Get title
        title_elem = snippet.find('span', class_='snippet__content__title')
        title = title_elem.get_text(strip=True) if title_elem else None
        
        # Get location
        location_elem = snippet.find('span', attrs={'data-test': 'snippet-content-location'})
        location = location_elem.get_text(strip=True) if location_elem else None
        
        # Get price
        price_elem = snippet.find('div', class_='snippet__content__price')
        price_text = price_elem.get_text(strip=True) if price_elem else None
        
        # Extract numeric price
        price = None
        if price_text:
            price_match = re.search(r'₱\s*([\d,]+)', price_text)
            if price_match:
                price = int(price_match.group(1).replace(',', ''))
        
        # Get bedrooms
        bedrooms_elem = snippet.find('span', class_='bedrooms', attrs={'data-test': 'bedrooms-value'})
        bedrooms = bedrooms_elem.get_text(strip=True) if bedrooms_elem else None
        
        # Get bathrooms
        bathrooms_elem = snippet.find('span', class_='bathrooms', attrs={'data-test': 'full-bathrooms-value'})
        bathrooms = bathrooms_elem.get_text(strip=True) if bathrooms_elem else None
        
        property_data.append({
            'property_id': prop_id,
            'url': href,
            'title': title,
            'location': location,
            'price_preview': price,
            'bedrooms_preview': bedrooms,
            'bathrooms_preview': bathrooms,
            'city': city,
            'property_type': prop_type
        })
    
    return pd.DataFrame(property_data)

def get_page_range(city, prop_type):
    """Detect pagination range for a city/property combination."""
    url = f'https://www.lamudi.com.ph/rent/{REGION}/{city}/{prop_type}/'
    print(f"🔍 Detecting page range: {city}/{prop_type}")
    
    driver = None
    try:
        driver = create_driver()
        driver.get(url)
        time.sleep(PAGE_LOAD_WAIT)
        
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        # Look for pagination text: "Page 1 of 41"
        pagination_div = soup.find('div', class_='pagination__pages')
        
        if pagination_div:
            sort_text = pagination_div.find('div', class_='sort-text')
            if sort_text:
                text = sort_text.get_text(strip=True)
                # Extract max page from "Page 1 of 41"
                match = re.search(r'Page\s+\d+\s+of\s+(\d+)', text, re.I)
                if match:
                    max_page = int(match.group(1))
                    print(f"   ✅ Pages: 1 to {max_page}")
                    return (1, max_page)
        
        # Fallback: Look for any text matching "Page X of Y"
        page_text = soup.find(text=re.compile(r'Page\s+\d+\s+of\s+\d+', re.I))
        if page_text:
            match = re.search(r'Page\s+\d+\s+of\s+(\d+)', page_text, re.I)
            if match:
                max_page = int(match.group(1))
                print(f"   ✅ Pages: 1 to {max_page}")
                return (1, max_page)
        
        print(f"   ℹ️  No pagination found - single page only")
        return (1, 1)
    
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return (1, 1)
    finally:
        if driver:
            driver.quit()

def scrape_links_from_page(city, prop_type, page_number):
    """Scrape property links from a single search results page."""
    if page_number == 1:
        url = f'https://www.lamudi.com.ph/rent/{REGION}/{city}/{prop_type}/'
    else:
        url = f'https://www.lamudi.com.ph/rent/{REGION}/{city}/{prop_type}/?page={page_number}'
    
    print(f"🚀 Scraping: {city}/{prop_type} - Page {page_number}")
    
    driver = None
    try:
        driver = create_driver()
        driver.get(url)
        time.sleep(PAGE_LOAD_WAIT)
        
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        df = extract_links_from_soup(soup, city, prop_type)
        
        if not df.empty:
            print(f"   ✅ Found {len(df)} properties")
            return df
        else:
            print(f"   ⚠️  No properties found")
            return pd.DataFrame()
    
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return pd.DataFrame()
    finally:
        if driver:
            driver.quit()

# ========== MAIN EXECUTION ==========
def main():
    """Main link scraping workflow."""
    print("=" * 70)
    print("PHILIPPINE RENTAL PROPERTY LINK SCRAPER")
    print("=" * 70)
    print(f"\n📍 Cities: {', '.join(CITIES)}")
    print(f"🏢 Types: {', '.join(PROPERTY_TYPES)}\n")
    
    start_time = time.time()
    
    # Detect page ranges
    task_ranges = {}
    for city in CITIES:
        for prop_type in PROPERTY_TYPES:
            min_page, max_page = get_page_range(city, prop_type)
            task_ranges[(city, prop_type)] = (min_page, max_page)
            time.sleep(2)
    
    # Create task list
    tasks = []
    for (city, prop_type), (min_page, max_page) in task_ranges.items():
        for page_num in range(min_page, max_page + 1):
            tasks.append((city, prop_type, page_num))
    
    random.shuffle(tasks)
    print(f"\n📋 Total tasks: {len(tasks)}\n")
    
    # Execute scraping
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        results = executor.map(lambda p: scrape_links_from_page(*p), tasks)
        df_list = [df for df in results if df is not None and not df.empty]
    
    # Combine results
    if df_list:
        links_df = pd.concat(df_list, ignore_index=True)
        links_df = links_df.drop_duplicates(subset=['url']).reset_index(drop=True)
        
        print(f"\n✅ Total unique properties: {len(links_df)}")
        
        # Save links
        links_file = f"{OUTPUT_PATH}/property_links_raw_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        links_df.to_csv(links_file, index=False, encoding='utf-8-sig')
        print(f"💾 Saved: {links_file}")
        
        # Print summary by city
        print(f"\n📊 LINKS BY CITY:")
        for city in CITIES:
            count = len(links_df[links_df['city'] == city])
            if count > 0:
                print(f"   {city}: {count}")
    else:
        print("\n⚠️  No links collected")
        return
    
    elapsed = time.time() - start_time
    print(f"\n⏱️  Total time: {elapsed:.2f} seconds")
    print("\n" + "=" * 70)
    print("✅ LINK SCRAPING COMPLETE!")
    print("=" * 70)

if __name__ == '__main__':
    main()