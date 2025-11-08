import json
from typing import Dict, List
from models import FoodItem
from database import Database  # Using Supabase database


def parse_nutrition_value(value: str) -> float:
    """Extract numeric value from nutrition string (e.g., '25.9g' -> 25.9)"""
    if not value:
        return 0.0
    # Remove units and convert to float
    numeric_str = ''.join(c for c in value if c.isdigit() or c == '.')
    try:
        return float(numeric_str) if numeric_str else 0.0
    except ValueError:
        return 0.0


def load_dining_hall_menus(json_path: str) -> List[FoodItem]:
    """
    Load food items from the dining hall menus JSON file
    Returns a list of FoodItem objects
    """
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    food_items = []
    
    # Iterate through each dining hall location
    for location, entries in data.items():
        for entry in entries:
            date = entry.get("date", "")
            meals = entry.get("meals", {})
            
            # Process each meal type (Breakfast, Lunch, Dinner)
            for meal_type, meal_sections in meals.items():
                # Each meal type has sections (like "Grab n'Go Breakfast", "Entree", etc.)
                for section_name, items in meal_sections.items():
                    for item in items:
                        nutrition = item.get("nutrition", {})
                        
                        # Create FoodItem with the required nutritional fields
                        food_item = FoodItem(
                            id=None,
                            name=item.get("name", "Unknown"),
                            serving_size=nutrition.get("serving_size", "1 serving"),
                            calories=int(parse_nutrition_value(nutrition.get("calories", "0"))),
                            total_fat=parse_nutrition_value(nutrition.get("total_fat", "0g")),
                            sodium=parse_nutrition_value(nutrition.get("sodium", "0mg")),
                            total_carb=parse_nutrition_value(nutrition.get("total_carb", "0g")),
                            dietary_fiber=parse_nutrition_value(nutrition.get("dietary_fiber", "0g")),
                            sugars=parse_nutrition_value(nutrition.get("sugars", "0g")),
                            protein=parse_nutrition_value(nutrition.get("protein", "0g")),
                            location=location,
                            date=date,
                            meal_type=meal_type
                        )
                        food_items.append(food_item)
    
    return food_items


def populate_database_from_json(json_path: str, db: Database):
    """
    Load all food items from JSON and insert them into the database
    """
    print("Loading food items from JSON...")
    food_items = load_dining_hall_menus(json_path)
    print(f"Found {len(food_items)} food items")
    
    print("Inserting food items into database...")
    success_count = 0
    for i, food_item in enumerate(food_items):
        try:
            db.create_food_item(food_item)
            success_count += 1
            if (i + 1) % 100 == 0:
                print(f"Processed {i + 1}/{len(food_items)} items...")
        except Exception as e:
            print(f"Error inserting {food_item.name}: {e}")
    
    print(f"Successfully inserted {success_count}/{len(food_items)} food items")


def get_available_dates(json_path: str) -> List[str]:
    """Get list of available dates from the JSON file"""
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    dates = set()
    for location, entries in data.items():
        for entry in entries:
            date = entry.get("date", "")
            if date:
                dates.add(date)
    
    return sorted(list(dates))


def get_available_locations(json_path: str) -> List[str]:
    """Get list of available dining hall locations from the JSON file"""
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    return sorted(list(data.keys()))


if __name__ == "__main__":
    # Example usage: populate database from JSON
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    # Initialize database connection (using Supabase)
    db = Database()
    
    # Path to the JSON file
    json_file = "../backend/all_dining_halls_menus.json"
    
    if os.path.exists(json_file):
        populate_database_from_json(json_file, db)
    else:
        print(f"JSON file not found: {json_file}")
