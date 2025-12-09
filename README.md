# Philippine Rental Property Scraper

A web scraper for finding affordable rental properties near Ortigas Center, Mandaluyong, Philippines using Lamudi.com.ph.

## 🎯 Project Goal

Find furnished condo/apartment rentals under ₱20,000/month within commuting distance (< 1 hour) of Ortigas Center for solo living.

## 📋 Target Criteria

- **Location**: Mandaluyong, Pasig, San Juan, Quezon City, Makati, Taguig
- **Property Types**: Condos and Apartments
- **Budget**: Under ₱20,000/month
- **Bedrooms**: Studio and 1-bedroom
- **Furnishing**: Furnished units only
- **Commute**: Within 1 hour to Doña Julia Vargas Ave, Ortigas Center

## 📂 Files

- `Philippine_Rental_Scraper.ipynb` - Main scraper notebook (NEW)
- `Coeds.ipynb` - Original Vietnamese property scraper (REFERENCE ONLY)
- `data/` - Output directory for CSV files

## 🚀 Getting Started

### 1. Install Dependencies

```bash
pip install selenium webdriver-manager beautifulsoup4 pandas numpy
```

### 2. First Run - Identify CSS Selectors

**IMPORTANT**: Before running the full scraper, you MUST identify the correct CSS selectors for Lamudi:

1. Open `Philippine_Rental_Scraper.ipynb` in Jupyter
2. Run cells 1-3 (imports and configuration)
3. **Run the "Test Cell: Inspect Lamudi Page Structure"**
4. Review the output to identify:
   - Property listing container classes
   - Property link selectors
   - Pagination structure
5. Update the CSS selectors in the scraping functions based on findings

### 3. Run the Scraper

The notebook has 4 phases:

**Phase 1: Collect Property Links**
- Scrapes search result pages
- Detects pagination automatically
- Collects all property URLs

**Phase 2: Scrape Property Details**
- Visits each property page
- Extracts detailed information
- Saves raw data

**Phase 3: Clean and Filter**
- Filters by budget (< ₱20,000)
- Filters by furnishing (furnished only)
- Adds commute time estimates
- Exports cleaned CSV

**Phase 4: Explore**
- View and analyze results

### 4. Review Results

Check the `data/` folder for CSV files:
- `property_links_*.csv` - All collected property URLs
- `property_details_raw_*.csv` - Raw scraped data
- `ortigas_rentals_under_20k_*.csv` - **Final filtered results**

## ⚙️ Configuration

Edit these variables in the notebook's configuration cell:

```python
# Target cities
CITIES = ['mandaluyong', 'pasig', 'san-juan', 'quezon-city', 'makati', 'taguig']

# Property types
PROPERTY_TYPES = ['condo', 'apartment']

# Budget limit
MAX_PRICE = 20000  # PHP per month

# Scraping settings
MAX_WORKERS = 3      # Concurrent threads
HEADLESS = True      # Run browser in background
PAGE_LOAD_WAIT = 4   # Seconds to wait for pages
```

## 🛠️ Customization

### Add More Cities

To expand your search area:

```python
CITIES = [
    'mandaluyong', 'pasig', 'san-juan',
    'quezon-city', 'makati', 'taguig',
    'manila',      # Add Manila
    'marikina',    # Add Marikina
]
```

### Change Budget

```python
MAX_PRICE = 25000  # Increase to ₱25,000
```

### Include Houses

```python
PROPERTY_TYPES = ['condo', 'apartment', 'house']
```

### Adjust Workers

```python
MAX_WORKERS = 5  # Increase for faster scraping (but more resource intensive)
```

## 📊 Output Data Fields

The final CSV includes:

| Field | Description |
|-------|-------------|
| `title` | Property title/name |
| `price_php` | Monthly rent in PHP |
| `bedrooms` | Number of bedrooms |
| `bathrooms` | Number of bathrooms |
| `floor_area_sqm` | Floor area in square meters |
| `price_per_sqm` | Rent per square meter |
| `furnishing` | Furnishing status |
| `city` | City location |
| `property_type` | Condo or apartment |
| `commute_estimate` | Estimated commute time to Ortigas |
| `address` | Full address |
| `latitude` | GPS latitude (extracted from page scripts) |
| `longitude` | GPS longitude (extracted from page scripts) |
| `parking` | Parking information |
| `amenities` | Building amenities |
| `description` | Property description |
| `url` | Link to listing |

## 🔧 Troubleshooting

### No Data Scraped

**Problem**: The scraper runs but returns no properties.

**Solution**:
1. Run the test cell to inspect page structure
2. Update CSS selectors in the code
3. Check if Lamudi changed their HTML structure
4. Try setting `HEADLESS = False` to see what the browser sees

### ChromeDriver Issues

**Problem**: "ChromeDriver not found" or version mismatch.

**Solution**:
```bash
pip install --upgrade webdriver-manager
```
The ChromeDriver will auto-download on first run.

### Too Slow

**Problem**: Scraping takes too long.

**Solution**:
- Reduce number of cities
- Increase `MAX_WORKERS` (but be respectful)
- Run during off-peak hours

### Rate Limiting / Blocked

**Problem**: Getting blocked by Lamudi.

**Solution**:
- Decrease `MAX_WORKERS` to 2
- Increase `PAGE_LOAD_WAIT` to 5-6 seconds
- Add longer delays between requests
- Use VPN if IP is blocked

## ⚠️ Important Notes

### Legal & Ethical

- **Respect Terms of Service**: Check Lamudi's ToS before scraping
- **Rate Limiting**: Don't overload their servers
- **Personal Use**: Use data responsibly and ethically
- **No Redistribution**: Don't republish scraped data

### Data Accuracy

- **Verify Information**: Always verify details with the property owner
- **Listings Change**: Properties may be rented before you contact
- **Prices Update**: Some listings may be outdated
- **Contact Directly**: Use the URL to contact through Lamudi

### Maintenance

- **Selectors Change**: Websites update their HTML - selectors need periodic updates
- **Run Regularly**: Listings change frequently, run weekly for best results
- **Backup Data**: Save your CSV files for comparison

## 📈 Next Steps After Scraping

1. **Filter Further**: Open CSV in Excel/Google Sheets for additional filtering
2. **Map Properties**: Use latitude/longitude to visualize on Google Maps
3. **Compare Prices**: Analyze price trends by area
4. **Contact Owners**: Use URLs to inquire about properties
5. **Schedule Viewings**: Visit top candidates in person

## 🗺️ Commute Times Reference

From Ortigas Center to:

| City | Estimated Commute | Transport |
|------|------------------|-----------|
| Mandaluyong | 0-5 min | Walking/Jeep |
| Pasig | 0-10 min | Walking/Jeep |
| San Juan | 5-15 min | Jeep/MRT |
| Quezon City | 10-30 min | MRT-3 |
| Makati | 20-35 min | MRT-3/Bus |
| Taguig | 20-40 min | Bus/Jeep |

*Times are estimates during normal hours. Rush hour may be longer.*

## 📞 Support

For issues or questions:
1. Check the notebook comments and documentation
2. Review the original Vietnamese scraper (`Coeds.ipynb`) for reference
3. Inspect Lamudi's current page structure using browser DevTools

## 🔄 Comparison with Original Scraper

| Feature | Vietnamese Scraper | Philippine Scraper |
|---------|-------------------|-------------------|
| Website | batdongsan.com.vn | lamudi.com.ph |
| Focus | Land & warehouses | Condos & apartments |
| Region | Binh Duong, HCMC | Metro Manila (Ortigas area) |
| Budget Filter | Area range (m²) | Price limit (₱20,000) |
| Furnishing | N/A | Furnished only |
| Commute | N/A | Ortigas-centric |

## 📝 License

This is a personal project for educational and personal use. Use responsibly.

**Status**: Ready for CSS selector configuration and testing

## 🤖 AI Assistance

This project is developed with the assistance of the **Gemini CLI Agent**.
- **Role**: Coding Assistant, Refactoring, Debugging, Documentation
- **Usage**: The agent helps with writing scripts, configuring environments, and analyzing data.

---

**Created**: November 2025
**Purpose**: Finding affordable rentals near Ortigas Center, Manila
