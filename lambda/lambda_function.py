"""
AWS Lambda Function: UMass Dining Hall Menu Scraper
Scrapes dining hall menus weekly and loads data into Supabase
Runs every Saturday at 11:00 AM via EventBridge
"""

import json
import os
import asyncio
from datetime import datetime
from typing import Dict
from supabase import create_client, Client
from scraper_utils import scrape_all_dining_halls

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

    print(f"[SUCCESS] Successfully loaded {inserted_count} food items to Supabase")
    return inserted_count


def lambda_handler(event, context):
    """
    AWS Lambda handler function
    Triggered by EventBridge on Saturdays at 11:00 AM
    """
    import subprocess  # Import at function level for both Lambda and error handling

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

        # Playwright browsers are in Lambda layer
        print("\n[INFO] Using Playwright from Lambda layer")

        # Scrape all dining halls
        print("\n[SCRAPE] Starting menu scraping...")
        print(f"Time remaining: {context.get_remaining_time_in_millis()}ms")
        menu_data = asyncio.run(scrape_all_dining_halls())

        # Validate scraped data
        total_items = sum(len(entries) for entries in menu_data.values())
        print(f"\n[DATA] Scraped {total_items} menu entries from {len(menu_data)} dining halls")

        if total_items == 0:
            print("[WARNING] No menu items were scraped")

        # Load to Supabase
        print("\n[UPLOAD] Loading data to Supabase...")
        print(f"Time remaining: {context.get_remaining_time_in_millis()}ms")
        item_count = load_to_supabase(menu_data)

        # Calculate execution time
        execution_time = (datetime.now() - start_time).total_seconds()
        print(f"\n[TIMER] Total execution time: {execution_time:.2f} seconds")

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

        print(f"\n[SUCCESS] Lambda execution completed successfully")
        print(f"Items loaded: {item_count}")
        return response

    except subprocess.TimeoutExpired as e:
        error_msg = f"Playwright installation timeout after {e.timeout} seconds"
        print(f"\n[ERROR] {error_msg}")
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
        print(f"\n[ERROR] {error_msg}")
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
        print(f"\n[ERROR] Lambda execution failed: {str(e)}")
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
    class MockContext:
        request_id = "local-test"
        function_name = "local-test"
        memory_limit_in_mb = 512
        def get_remaining_time_in_millis(self):
            return 900000
    
    lambda_handler({}, MockContext())
