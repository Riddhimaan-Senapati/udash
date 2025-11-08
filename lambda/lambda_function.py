"""
AWS Lambda Function: UMass Dining Hall Menu Scraper
Scrapes dining hall menus weekly and loads data into Supabase
Runs every Saturday at 11:00 AM via EventBridge
"""

import json
import os
import asyncio
from datetime import datetime
from typing import List, Dict
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
from supabase import create_client, Client


# Supabase Configuration
SUPABASE_URL = os.environ['SUPABASE_URL']
SUPABASE_KEY = os.environ['SUPABASE_KEY']
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


def parse_nutrition_value(value: str) -> float:
    """Extract numeric value from nutrition string (e.g., '25.9g' -> 25.9)"""
    if not value:
        return 0.0
    numeric_str = ''.join(c for c in value if c.isdigit() or c == '.')
    try:
        return float(numeric_str) if numeric_str else 0.0
    except ValueError:
        return 0.0


async def get_available_dates(page, base_url):
    """Extract available dates from the dropdown menu"""
    print(f"Fetching available dates from {base_url}...")
    await page.goto(base_url, wait_until='networkidle', timeout=60000)

    await page.wait_for_selector('#upcoming-foodpro', timeout=10000)

    dates = await page.evaluate('''() => {
        const select = document.getElementById('upcoming-foodpro');
        const options = Array.from(select.options);
        return options.map(option => ({
            value: option.value,
            text: option.text
        }));
    }''')

    print(f"Found {len(dates)} available dates")
    return [(d['value'], d['text']) for d in dates]


def parse_menu_from_html(html_content, date_str, location_name):
    """Parse menu data from HTML content"""
    soup = BeautifulSoup(html_content, 'html.parser')
    menu_data = {
        "date": date_str,
        "location": location_name,
        "meals": {}
    }

    # Find all menu sections
    menu_sections = soup.find_all('div', class_='menu-block')

    for section in menu_sections:
        # Get meal type from header
        meal_header = section.find('div', class_='menu-block__header')
        if not meal_header:
            continue

        meal_type = meal_header.get_text(strip=True)

        # Skip if not a main meal
        if meal_type not in ['Breakfast', 'Lunch', 'Dinner']:
            continue

        if meal_type not in menu_data["meals"]:
            menu_data["meals"][meal_type] = {}

        # Get menu items for this section
        menu_items = section.find_all('button', class_='menu-item')

        current_category = "Main"
        for item_button in menu_items:
            item_name_div = item_button.find('div', class_='menu-item__name')
            if not item_name_div:
                continue

            item_name = item_name_div.get_text(strip=True)

            # Try to extract nutrition info
            nutrition = {}
            nutrition_div = item_button.find('div', class_='menu-item__nutrition')
            if nutrition_div:
                nutrition_text = nutrition_div.get_text(strip=True)
                # Parse nutrition (basic extraction)
                nutrition['serving_size'] = '1 serving'

                # Extract values from nutrition string if available
                if 'Calories' in nutrition_text:
                    parts = nutrition_text.split('|')
                    for part in parts:
                        part = part.strip()
                        if 'Calories' in part:
                            nutrition['calories'] = part.replace('Calories', '').strip()
                        elif 'Fat' in part:
                            nutrition['total_fat'] = part.replace('Total Fat', '').strip()
                        elif 'Carb' in part:
                            nutrition['total_carb'] = part.replace('Total Carb.', '').strip()
                        elif 'Protein' in part:
                            nutrition['protein'] = part.replace('Protein', '').strip()
                        elif 'Sodium' in part:
                            nutrition['sodium'] = part.replace('Sodium', '').strip()

            if current_category not in menu_data["meals"][meal_type]:
                menu_data["meals"][meal_type][current_category] = []

            menu_data["meals"][meal_type][current_category].append({
                "name": item_name,
                "nutrition": nutrition
            })

    return menu_data


async def scrape_dining_hall(base_url, location_name):
    """Scrape a single dining hall's menus"""
    async with async_playwright() as p:
        print(f"Launching browser for {location_name}...")
        browser = await p.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-dev-shm-usage']
        )
        page = await browser.new_page()

        try:
            # Get available dates
            dates = await get_available_dates(page, base_url)

            location_data = []

            for date_value, date_text in dates:
                print(f"Scraping {location_name} for {date_text}...")

                # Select the date
                await page.select_option('#upcoming-foodpro', value=date_value)
                await asyncio.sleep(2)  # Wait for page to update

                # Get the menu content
                html = await page.content()
                menu_data = parse_menu_from_html(html, date_text, location_name)
                location_data.append(menu_data)

            return location_data

        finally:
            await browser.close()


async def scrape_all_dining_halls():
    """Scrape all dining hall menus"""
    dining_halls = {
        "Worcester": "https://umassdining.com/locations-menus/worcester/menu",
        "Berkshire": "https://umassdining.com/locations-menus/berkshire/menu",
        "Franklin": "https://umassdining.com/locations-menus/franklin/menu",
        "Hampshire": "https://umassdining.com/locations-menus/hampshire/menu"
    }

    all_menus = {}

    for location_name, url in dining_halls.items():
        try:
            print(f"\n{'='*50}")
            print(f"Scraping {location_name}...")
            print(f"{'='*50}")

            menus = await scrape_dining_hall(url, location_name)
            all_menus[location_name] = menus

        except Exception as e:
            print(f"Error scraping {location_name}: {e}")
            all_menus[location_name] = []

    return all_menus


def load_to_supabase(menu_data: Dict):
    """Load scraped menu data into Supabase food_items table"""
    food_items = []

    # Parse menu data into food items
    for location, entries in menu_data.items():
        for entry in entries:
            date = entry.get("date", "")
            meals = entry.get("meals", {})

            for meal_type, meal_sections in meals.items():
                for section_name, items in meal_sections.items():
                    for item in items:
                        nutrition = item.get("nutrition", {})

                        food_item = {
                            "name": item.get("name", "Unknown"),
                            "serving_size": nutrition.get("serving_size", "1 serving"),
                            "calories": int(parse_nutrition_value(nutrition.get("calories", "0"))),
                            "total_fat": parse_nutrition_value(nutrition.get("total_fat", "0g")),
                            "sodium": parse_nutrition_value(nutrition.get("sodium", "0mg")),
                            "total_carb": parse_nutrition_value(nutrition.get("total_carb", "0g")),
                            "dietary_fiber": parse_nutrition_value(nutrition.get("dietary_fiber", "0g")),
                            "sugars": parse_nutrition_value(nutrition.get("sugars", "0g")),
                            "protein": parse_nutrition_value(nutrition.get("protein", "0g")),
                            "location": location,
                            "date": date,
                            "meal_type": meal_type
                        }

                        food_items.append(food_item)

    print(f"\nLoading {len(food_items)} food items to Supabase...")

    # Batch insert to Supabase (handle duplicates)
    batch_size = 100
    inserted_count = 0

    for i in range(0, len(food_items), batch_size):
        batch = food_items[i:i+batch_size]
        try:
            # Use upsert to handle duplicates
            result = supabase.table("food_items").upsert(
                batch,
                on_conflict="name,location,date,meal_type"
            ).execute()
            inserted_count += len(batch)
            print(f"Inserted batch {i//batch_size + 1}: {len(batch)} items")
        except Exception as e:
            print(f"Error inserting batch {i//batch_size + 1}: {e}")

    print(f"✅ Successfully loaded {inserted_count} food items to Supabase")
    return inserted_count


def lambda_handler(event, context):
    """
    AWS Lambda handler function
    Triggered by EventBridge on Saturdays at 11:00 AM
    """
    start_time = datetime.now()
    print(f"Lambda execution started at {start_time.isoformat()}")
    print(f"Event: {json.dumps(event)}")
    print(f"AWS Request ID: {context.request_id}")
    print(f"Function Name: {context.function_name}")
    print(f"Memory Limit: {context.memory_limit_in_mb}MB")
    print(f"Time Remaining: {context.get_remaining_time_in_millis()}ms")

    try:
        # Verify environment variables
        if not SUPABASE_URL or not SUPABASE_KEY:
            raise ValueError("Missing SUPABASE_URL or SUPABASE_KEY environment variables")

        print(f"Supabase URL configured: {SUPABASE_URL[:30]}...")

        # Install Playwright browsers (required for Lambda)
        import subprocess
        print("\n📦 Installing Playwright Chromium...")
        install_result = subprocess.run(
            ['playwright', 'install', 'chromium'],
            capture_output=True,
            text=True,
            check=True,
            timeout=300  # 5 minute timeout for installation
        )
        print(f"Playwright installation output: {install_result.stdout}")
        print(f"Playwright Chromium installed successfully")

        # Scrape all dining halls
        print("\n🔍 Starting menu scraping...")
        print(f"Time remaining: {context.get_remaining_time_in_millis()}ms")
        menu_data = asyncio.run(scrape_all_dining_halls())

        # Validate scraped data
        total_items = sum(len(entries) for entries in menu_data.values())
        print(f"\n📊 Scraped {total_items} menu entries from {len(menu_data)} dining halls")

        if total_items == 0:
            print("⚠️ Warning: No menu items were scraped")

        # Load to Supabase
        print("\n📤 Loading data to Supabase...")
        print(f"Time remaining: {context.get_remaining_time_in_millis()}ms")
        item_count = load_to_supabase(menu_data)

        # Calculate execution time
        execution_time = (datetime.now() - start_time).total_seconds()
        print(f"\n⏱️ Total execution time: {execution_time:.2f} seconds")

        response = {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Menu scraping and database update completed successfully',
                'timestamp': datetime.now().isoformat(),
                'items_loaded': item_count,
                'dining_halls_scraped': len(menu_data),
                'execution_time_seconds': execution_time,
                'request_id': context.request_id
            })
        }

        print(f"\n✅ Lambda execution completed successfully")
        print(f"Items loaded: {item_count}")
        return response

    except subprocess.TimeoutExpired as e:
        error_msg = f"Playwright installation timeout after {e.timeout} seconds"
        print(f"\n❌ {error_msg}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'message': 'Playwright installation timeout',
                'error': error_msg,
                'timestamp': datetime.now().isoformat(),
                'request_id': context.request_id
            })
        }

    except ValueError as e:
        error_msg = f"Configuration error: {str(e)}"
        print(f"\n❌ {error_msg}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'message': 'Configuration error',
                'error': error_msg,
                'timestamp': datetime.now().isoformat(),
                'request_id': context.request_id
            })
        }

    except Exception as e:
        print(f"\n❌ Lambda execution failed: {str(e)}")
        import traceback
        traceback.print_exc()

        execution_time = (datetime.now() - start_time).total_seconds()

        return {
            'statusCode': 500,
            'body': json.dumps({
                'message': 'Menu scraping failed',
                'error': str(e),
                'error_type': type(e).__name__,
                'timestamp': datetime.now().isoformat(),
                'execution_time_seconds': execution_time,
                'request_id': context.request_id
            })
        }


# For local testing
if __name__ == "__main__":
    lambda_handler({}, {})
