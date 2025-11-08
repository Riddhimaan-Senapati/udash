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
    
    print("Fetching available dates...")
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
    
    print(f"Found {len(dates)} available dates")
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
    
    print(f"Fetching menu for {date_text}...")
    
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
        print(f"Error fetching menu for {date_text}: {e}")
        return None


def get_all_available_menus(base_url):
    """
    Scrape menus for all available dates
    
    Args:
        base_url: Base URL of the menu page
        
    Returns:
        list: List of menu data dictionaries
    """
    
    driver = setup_driver()
    
    try:
        # Get available dates
        available_dates = get_available_dates(driver, base_url)
        
        if not available_dates:
            print("No dates found. Exiting.")
            return []
        
        all_menus = []
        
        for i, (date_value, date_text) in enumerate(available_dates, 1):
            print(f"\nProcessing {i}/{len(available_dates)}: {date_text}")
            
            menu_data = get_menu_for_date(driver, date_value, date_text)
            
            if menu_data:
                all_menus.append(menu_data)
            
            # Small delay between requests
            time.sleep(1)
        
        return all_menus
        
    finally:
        driver.quit()


def save_menus_to_json(menus, filename='all_menus.json'):
    """Save scraped menu data to JSON file"""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(menus, f, indent=2, ensure_ascii=False)
    print(f"\nMenu data saved to {filename}")


def print_menu_summary(menus):
    """Print a summary of all menus"""
    print(f"\n{'='*60}")
    print(f"MENU SUMMARY FOR ALL AVAILABLE DATES")
    print(f"{'='*60}\n")
    
    for day_menu in menus:
        print(f"\n{day_menu['date']} - {day_menu['location']}")
        print("-" * 60)
        
        for meal, categories in day_menu['meals'].items():
            total_items = sum(len(items) for items in categories.values())
            if total_items > 0:
                print(f"  {meal}: {total_items} items")
                
                for category, items in categories.items():
                    if items:
                        print(f"    • {category}: {len(items)} items")


# Example usage
if __name__ == "__main__":
    # Base URL for menu page
    base_url = "https://umassdining.com/menu/berkshire-grab-n-go-menu"
    # base_url = "https://umassdining.com/menu/worcester-menu"
    # base_url = "https://umassdining.com/menu/franklin-menu"
    # base_url = "https://umassdining.com/menu/hampshire-menu"
    
    print("="*60)
    print("UMass Dining Menu Scraper (Selenium)")
    print("="*60)
    print("\nNote: This will open a Chrome browser in the background.")
    print("Make sure you have Chrome and chromedriver installed.\n")
    
    # Scrape all available menus
    all_menus = get_all_available_menus(base_url)
    
    if all_menus:
        # Print summary
        print_menu_summary(all_menus)
        
        # Save to JSON
        save_menus_to_json(all_menus)
        
        # Print overall statistics
        print(f"\n{'='*60}")
        print(f"OVERALL STATISTICS")
        print(f"{'='*60}")
        print(f"Total days scraped: {len(all_menus)}")
        
        total_items = 0
        for day_menu in all_menus:
            for meal, categories in day_menu['meals'].items():
                total_items += sum(len(items) for items in categories.values())
        
        print(f"Total menu items (all dates): {total_items}")
        if len(all_menus) > 0:
            print(f"Average items per day: {total_items / len(all_menus):.1f}")


    else:
        print("\nNo menus were scraped. Please check the URL and try again.")