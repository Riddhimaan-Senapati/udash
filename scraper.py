from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from bs4 import BeautifulSoup
import json
import time

def setup_driver():
    """Setup Chrome driver with options"""
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    
    driver = webdriver.Chrome(options=options)
    return driver


def get_available_dates(driver, base_url):
    """
    Extract available dates from the dropdown menu
    
    Args:
        driver: Selenium WebDriver
        base_url: Base URL of the menu page
        
    Returns:
        list: List of tuples (date_value, date_text)
    """
    
    print(f"  Fetching available dates from {base_url}...")
    driver.get(base_url)
    
    # Wait for dropdown to load
    wait = WebDriverWait(driver, 10)
    dropdown_element = wait.until(
        EC.presence_of_element_located((By.ID, "upcoming-foodpro"))
    )
    
    # Get the dropdown
    select = Select(dropdown_element)
    
    # Extract all options
    dates = []
    for option in select.options:
        date_value = option.get_attribute('value')
        date_text = option.text
        dates.append((date_value, date_text))
    
    print(f"  Found {len(dates)} available dates")
    return dates


def parse_menu_from_html(html_content, date_str):
    """
    Parse menu data from HTML content
    
    Args:
        html_content: HTML string
        date_str: Date string for the menu
        
    Returns:
        dict: Menu data
    """
    
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Initialize result structure
    menu_data = {
        'date': date_str,
        'location': None,
        'meals': {}
    }
    
    # Extract location name
    location_header = soup.select_one('.singlepage-content-padding h1')
    if location_header:
        menu_data['location'] = location_header.get_text(strip=True)
    
    # Find all meal periods (breakfast, lunch, etc.)
    meal_divs = soup.find_all('div', id=lambda x: x and '_menu' in x)
    
    for meal_div in meal_divs:
        # Get meal type
        meal_type = meal_div.get('id').replace('_menu', '')
        meal_header = meal_div.find('h2')
        meal_name = meal_header.get_text(strip=True) if meal_header else meal_type
        
        menu_data['meals'][meal_name] = {}
        
        # Find the content div
        content_div = meal_div.find('div', {'id': 'content_text'})
        
        if content_div:
            # Find all category headers
            categories = content_div.find_all('h2', {'class': 'menu_category_name'})
            
            for category in categories:
                category_name = category.get_text(strip=True)
                menu_data['meals'][meal_name][category_name] = []
                
                # Find all items until the next category
                current = category.find_next_sibling()
                
                while current:
                    # Stop if we hit another category
                    if current.name == 'h2' and 'menu_category_name' in current.get('class', []):
                        break
                    
                    # Look for menu items
                    if current.name == 'li' and 'lightbox-nutrition' in current.get('class', []):
                        link = current.find('a')
                        if link:
                            item_data = {
                                'name': link.get_text(strip=True),
                                'nutrition': {
                                    'calories': link.get('data-calories', ''),
                                    'calories_from_fat': link.get('data-calories-from-fat', ''),
                                    'total_fat': link.get('data-total-fat', ''),
                                    'sat_fat': link.get('data-sat-fat', ''),
                                    'trans_fat': link.get('data-trans-fat', ''),
                                    'cholesterol': link.get('data-cholesterol', ''),
                                    'sodium': link.get('data-sodium', ''),
                                    'total_carb': link.get('data-total-carb', ''),
                                    'dietary_fiber': link.get('data-dietary-fiber', ''),
                                    'sugars': link.get('data-sugars', ''),
                                    'protein': link.get('data-protein', ''),
                                    'serving_size': link.get('data-serving-size', '')
                                },
                                'allergens': link.get('data-allergens', ''),
                                'diet': link.get('data-clean-diet-str', ''),
                                'carbon_rating': link.get('data-carbon-list', ''),
                                'healthfulness': link.get('data-healthfulness', ''),
                                'ingredients': link.get('data-ingredient-list', '')
                            }
                            
                            menu_data['meals'][meal_name][category_name].append(item_data)
                    
                    current = current.find_next_sibling()
    
    return menu_data


def get_menu_for_date(driver, date_value, date_text):
    """
    Get menu for a specific date by selecting it in the dropdown
    
    Args:
        driver: Selenium WebDriver
        date_value: Date value to select (e.g., "11/07/2025")
        date_text: Human-readable date text
        
    Returns:
        dict: Menu data
    """
    
    print(f"    Fetching menu for {date_text}...")
    
    try:
        # Find and select the dropdown option
        dropdown_element = driver.find_element(By.ID, "upcoming-foodpro")
        select = Select(dropdown_element)
        select.select_by_value(date_value)
        
        # Wait for content to load (adjust time as needed)
        time.sleep(3)
        
        # Get the page source after content loads
        html_content = driver.page_source
        
        # Parse the menu
        menu_data = parse_menu_from_html(html_content, date_text)
        
        return menu_data
        
    except Exception as e:
        print(f"    Error fetching menu for {date_text}: {e}")
        return None


def get_all_menus_for_location(base_url, location_name):
    """
    Scrape menus for all available dates at one location
    
    Args:
        base_url: Base URL of the menu page
        location_name: Name of the location (for display)
        
    Returns:
        list: List of menu data dictionaries
    """
    
    driver = setup_driver()
    
    try:
        # Get available dates
        available_dates = get_available_dates(driver, base_url)
        
        if not available_dates:
            print(f"  No dates found for {location_name}. Skipping.")
            return []
        
        location_menus = []
        
        for i, (date_value, date_text) in enumerate(available_dates, 1):
            print(f"    Processing {i}/{len(available_dates)}: {date_text}")
            
            menu_data = get_menu_for_date(driver, date_value, date_text)
            
            if menu_data:
                location_menus.append(menu_data)
            
            # Small delay between requests
            time.sleep(1)
        
        return location_menus
        
    finally:
        driver.quit()


def scrape_all_dining_halls():
    """
    Scrape menus from all 4 dining halls
    
    Returns:
        dict: Dictionary with location names as keys and menu lists as values
    """
    
    dining_halls = {
        'Berkshire': 'https://umassdining.com/menu/berkshire-grab-n-go-menu',
        'Worcester': 'https://umassdining.com/menu/worcester-menu',
        'Franklin': 'https://umassdining.com/menu/franklin-menu',
        'Hampshire': 'https://umassdining.com/menu/hampshire-menu'
    }
    
    all_dining_hall_menus = {}
    
    for location_name, url in dining_halls.items():
        print(f"\n{'='*60}")
        print(f"Scraping {location_name} Dining Hall")
        print(f"{'='*60}")
        
        menus = get_all_menus_for_location(url, location_name)
        all_dining_hall_menus[location_name] = menus
        
        print(f"✓ Completed {location_name}: {len(menus)} days scraped")
    
    return all_dining_hall_menus


def save_all_menus_to_json(all_menus, filename='all_dining_halls_menus.json'):
    """Save all scraped menu data to JSON file"""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(all_menus, f, indent=2, ensure_ascii=False)
    print(f"\nAll menu data saved to {filename}")


def save_menus_by_location(all_menus):
    """Save each location's menus to separate JSON files"""
    for location_name, menus in all_menus.items():
        filename = f"{location_name.lower()}_menus.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(menus, f, indent=2, ensure_ascii=False)
        print(f"  {location_name} menu saved to {filename}")


def print_overall_summary(all_menus):
    """Print a summary of all scraped menus"""
    print(f"\n{'='*60}")
    print(f"OVERALL SUMMARY - ALL DINING HALLS")
    print(f"{'='*60}\n")
    
    for location_name, menus in all_menus.items():
        print(f"\n{location_name} Dining Hall:")
        print("-" * 60)
        
        if not menus:
            print("  No menus scraped")
            continue
        
        print(f"  Total days: {len(menus)}")
        
        total_items = 0
        for day_menu in menus:
            for meal, categories in day_menu['meals'].items():
                total_items += sum(len(items) for items in categories.values())
        
        print(f"  Total menu items: {total_items}")
        if len(menus) > 0:
            print(f"  Average items per day: {total_items / len(menus):.1f}")
        
        # Show date range
        if menus:
            first_date = menus[0]['date']
            last_date = menus[-1]['date']
            print(f"  Date range: {first_date} to {last_date}")



# Example usage
if __name__ == "__main__":
    print("="*60)
    print("UMass Dining Menu Scraper - ALL DINING HALLS")
    print("="*60)
    print("\nThis will scrape menus from:")
    print("  1. Berkshire Dining Hall")
    print("  2. Worcester Dining Hall")
    print("  3. Franklin Dining Hall")
    print("  4. Hampshire Dining Hall")
    print("\nNote: This will take several minutes to complete.")
    print("="*60)
    
    # Scrape all dining halls
    all_menus = scrape_all_dining_halls()
    
    # Print overall summary
    print_overall_summary(all_menus)
    
    # Save all menus to one JSON file
    print("\n" + "="*60)
    print("SAVING DATA")
    print("="*60)
    save_all_menus_to_json(all_menus)
    
    # Save each location to separate files
    print("\nSaving individual location files:")
    save_menus_by_location(all_menus)

    
    print("\n" + "="*60)
    print("SCRAPING COMPLETE!")
    print("="*60)
    