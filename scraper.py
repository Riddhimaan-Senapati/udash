from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from bs4 import BeautifulSoup
import json
import time

def setup_driver():
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Chrome(options=options)
    return driver

def get_available_dates(driver, base_url):
    print(f"Fetching available dates from {base_url}...")
    driver.get(base_url)
    
    wait = WebDriverWait(driver, 10)
    dropdown_element = wait.until(
        EC.presence_of_element_located((By.ID, "upcoming-foodpro"))
    )
    
    select = Select(dropdown_element)
    dates = []
    for option in select.options:
        date_value = option.get_attribute('value')
        date_text = option.text
        dates.append((date_value, date_text))
    
    print(f"Found {len(dates)} available dates")
    return dates

def parse_menu_from_html(html_content, date_str, location_name):
    soup = BeautifulSoup(html_content, 'html.parser')
    
    menu_data = {
        'date': date_str,
        'location': location_name,
        'meals': {}
    }
    
    location_header = soup.select_one('.singlepage-content-padding h1')
    if location_header:
        detected_location = location_header.get_text(strip=True)
        if detected_location:
            menu_data['location'] = detected_location
    
    meal_divs = soup.find_all('div', id=lambda x: x and '_menu' in x)
    
    for meal_div in meal_divs:
        meal_type = meal_div.get('id').replace('_menu', '')
        meal_header = meal_div.find('h2')
        meal_name = meal_header.get_text(strip=True) if meal_header else meal_type
        
        menu_data['meals'][meal_name] = {}
        
        content_div = meal_div.find('div', {'id': 'content_text'})
        
        if content_div:
            categories = content_div.find_all('h2', {'class': 'menu_category_name'})
            
            for category in categories:
                category_name = category.get_text(strip=True)
                menu_data['meals'][meal_name][category_name] = []
                
                current = category.find_next_sibling()
                
                while current:
                    if current.name == 'h2' and 'menu_category_name' in current.get('class', []):
                        break
                    
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

def get_menu_for_date(driver, date_value, date_text, location_name):
    print(f"Fetching menu for {date_text} at {location_name}...")
    
    try:
        dropdown_element = driver.find_element(By.ID, "upcoming-foodpro")
        select = Select(dropdown_element)
        select.select_by_value(date_value)
        
        time.sleep(3)
        
        html_content = driver.page_source
        menu_data = parse_menu_from_html(html_content, date_text, location_name)
        
        return menu_data
        
    except Exception as e:
        print(f"Error fetching menu for {date_text} at {location_name}: {e}")
        return None

def get_all_menus_for_dining_hall(driver, base_url, location_name):
    print(f"\nScraping menus for: {location_name}")
    
    try:
        available_dates = get_available_dates(driver, base_url)
        
        if not available_dates:
            print(f"No dates found for {location_name}")
            return []
        
        hall_menus = []
        
        for i, (date_value, date_text) in enumerate(available_dates, 1):
            print(f"Processing {i}/{len(available_dates)}: {date_text}")
            
            menu_data = get_menu_for_date(driver, date_value, date_text, location_name)
            
            if menu_data:
                hall_menus.append(menu_data)
            
            time.sleep(1)
        
        return hall_menus
        
    except Exception as e:
        print(f"Error scraping {location_name}: {e}")
        return []

def get_all_dining_hall_menus():
    dining_halls = {
        "Berkshire": "https://umassdining.com/menu/berkshire-grab-n-go-menu",
        "Worcester": "https://umassdining.com/menu/worcester-grab-n-go", 
        "Franklin": "https://umassdining.com/menu/franklin-grab-n-go",
        "Hampshire": "https://umassdining.com/menu/hampshire-grab-n-go"
    }
    
    driver = setup_driver()
    all_menus = {}
    
    try:
        for hall_name, hall_url in dining_halls.items():
            menus = get_all_menus_for_dining_hall(driver, hall_url, hall_name)
            all_menus[hall_name] = menus
            
        return all_menus
        
    finally:
        driver.quit()

def save_menus_to_json(menus, filename='all_dining_halls_menus.json'):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(menus, f, indent=2, ensure_ascii=False)
    print(f"Menu data saved to {filename}")

def print_summary(all_menus):
    print(f"\n{'='*60}")
    print("OVERALL SUMMARY")
    print(f"{'='*60}")
    
    for hall_name, menus in all_menus.items():
        print(f"\n{hall_name}: {len(menus)} days")


if __name__ == "__main__":
    print("UMass Dining Menu Scraper - All 4 Dining Halls")
    
    all_menus = get_all_dining_hall_menus()
    
    if all_menus:
        print_summary(all_menus)
        save_menus_to_json(all_menus)
    else:
        print("No menus were scraped.")