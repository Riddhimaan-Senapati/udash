import json
import os
from typing import List, Optional, Dict
from datetime import datetime, timedelta
from models import User, FoodItem, MealEntry


class JSONDatabase:
    """Local JSON file-based database for testing before Supabase implementation"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.users_file = os.path.join(data_dir, "users.json")
        self.food_items_file = os.path.join(data_dir, "food_items.json")
        self.meal_entries_file = os.path.join(data_dir, "meal_entries.json")
        
        # Create data directory if it doesn't exist
        os.makedirs(data_dir, exist_ok=True)
        
        # Initialize files if they don't exist
        self._init_file(self.users_file, [])
        self._init_file(self.food_items_file, [])
        self._init_file(self.meal_entries_file, [])
    
    def _init_file(self, filepath: str, default_data):
        """Initialize a JSON file if it doesn't exist"""
        if not os.path.exists(filepath):
            with open(filepath, 'w') as f:
                json.dump(default_data, f, indent=2)
    
    def _load_json(self, filepath: str) -> list:
        """Load data from JSON file"""
        with open(filepath, 'r') as f:
            return json.load(f)
    
    def _save_json(self, filepath: str, data: list):
        """Save data to JSON file"""
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2, default=str)
    
    def _get_next_id(self, data: list) -> int:
        """Get next available ID"""
        if not data:
            return 1
        return max(item.get('id', 0) for item in data) + 1
    
    # ==================== USER OPERATIONS ====================
    
    def create_user(self, user: User) -> User:
        """Create a new user"""
        user.update_calculations()
        
        users = self._load_json(self.users_file)
        
        # Check if username already exists
        if any(u['username'] == user.username for u in users):
            raise ValueError(f"Username '{user.username}' already exists")
        
        user.id = self._get_next_id(users)
        user.created_at = datetime.now()
        
        user_dict = {
            "id": user.id,
            "username": user.username,
            "age": user.age,
            "sex": user.sex,
            "height_cm": user.height_cm,
            "weight_kg": user.weight_kg,
            "activity_level": user.activity_level,
            "bmr": user.bmr,
            "tdee": user.tdee,
            "created_at": user.created_at.isoformat()
        }
        
        users.append(user_dict)
        self._save_json(self.users_file, users)
        
        return user
    
    def get_user(self, user_id: int) -> Optional[User]:
        """Get user by ID"""
        users = self._load_json(self.users_file)
        
        for user_data in users:
            if user_data['id'] == user_id:
                return User(
                    id=user_data['id'],
                    username=user_data['username'],
                    age=user_data['age'],
                    sex=user_data['sex'],
                    height_cm=user_data['height_cm'],
                    weight_kg=user_data['weight_kg'],
                    activity_level=user_data['activity_level'],
                    bmr=user_data['bmr'],
                    tdee=user_data['tdee'],
                    created_at=datetime.fromisoformat(user_data['created_at'])
                )
        return None
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        users = self._load_json(self.users_file)
        
        for user_data in users:
            if user_data['username'] == username:
                return User(
                    id=user_data['id'],
                    username=user_data['username'],
                    age=user_data['age'],
                    sex=user_data['sex'],
                    height_cm=user_data['height_cm'],
                    weight_kg=user_data['weight_kg'],
                    activity_level=user_data['activity_level'],
                    bmr=user_data['bmr'],
                    tdee=user_data['tdee'],
                    created_at=datetime.fromisoformat(user_data['created_at'])
                )
        return None
    
    def get_all_users(self) -> List[User]:
        """Get all users"""
        users = self._load_json(self.users_file)
        
        return [
            User(
                id=user_data['id'],
                username=user_data['username'],
                age=user_data['age'],
                sex=user_data['sex'],
                height_cm=user_data['height_cm'],
                weight_kg=user_data['weight_kg'],
                activity_level=user_data['activity_level'],
                bmr=user_data['bmr'],
                tdee=user_data['tdee'],
                created_at=datetime.fromisoformat(user_data['created_at'])
            )
            for user_data in users
        ]
    
    def update_user(self, user: User) -> User:
        """Update user information"""
        user.update_calculations()
        
        users = self._load_json(self.users_file)
        
        for i, user_data in enumerate(users):
            if user_data['id'] == user.id:
                users[i] = {
                    "id": user.id,
                    "username": user.username,
                    "age": user.age,
                    "sex": user.sex,
                    "height_cm": user.height_cm,
                    "weight_kg": user.weight_kg,
                    "activity_level": user.activity_level,
                    "bmr": user.bmr,
                    "tdee": user.tdee,
                    "created_at": user.created_at.isoformat() if user.created_at else datetime.now().isoformat()
                }
                self._save_json(self.users_file, users)
                return user
        
        raise ValueError(f"User with ID {user.id} not found")
    
    def delete_user(self, user_id: int):
        """Delete a user"""
        users = self._load_json(self.users_file)
        users = [u for u in users if u['id'] != user_id]
        self._save_json(self.users_file, users)
        
        # Also delete all meal entries for this user
        meal_entries = self._load_json(self.meal_entries_file)
        meal_entries = [m for m in meal_entries if m['user_id'] != user_id]
        self._save_json(self.meal_entries_file, meal_entries)
    
    # ==================== FOOD ITEM OPERATIONS ====================
    
    def create_food_item(self, food: FoodItem) -> FoodItem:
        """Create a new food item"""
        food_items = self._load_json(self.food_items_file)
        
        # Check if duplicate exists (same name, location, date, meal_type)
        for existing_food in food_items:
            if (existing_food['name'] == food.name and
                existing_food.get('location') == food.location and
                existing_food.get('date') == food.date and
                existing_food.get('meal_type') == food.meal_type):
                # Return existing food with its ID
                food.id = existing_food['id']
                return food
        
        food.id = self._get_next_id(food_items)
        
        food_dict = {
            "id": food.id,
            "name": food.name,
            "serving_size": food.serving_size,
            "calories": food.calories,
            "total_fat": food.total_fat,
            "sodium": food.sodium,
            "total_carb": food.total_carb,
            "dietary_fiber": food.dietary_fiber,
            "sugars": food.sugars,
            "protein": food.protein,
            "location": food.location,
            "date": food.date,
            "meal_type": food.meal_type
        }
        
        food_items.append(food_dict)
        self._save_json(self.food_items_file, food_items)
        
        return food
    
    def get_food_item(self, food_id: int) -> Optional[FoodItem]:
        """Get food item by ID"""
        food_items = self._load_json(self.food_items_file)
        
        for food_data in food_items:
            if food_data['id'] == food_id:
                return FoodItem(
                    id=food_data['id'],
                    name=food_data['name'],
                    serving_size=food_data['serving_size'],
                    calories=food_data['calories'],
                    total_fat=food_data['total_fat'],
                    sodium=food_data['sodium'],
                    total_carb=food_data['total_carb'],
                    dietary_fiber=food_data['dietary_fiber'],
                    sugars=food_data['sugars'],
                    protein=food_data['protein'],
                    location=food_data.get('location'),
                    date=food_data.get('date'),
                    meal_type=food_data.get('meal_type')
                )
        return None
    
    def get_all_food_items(self) -> List[FoodItem]:
        """Get all food items"""
        food_items = self._load_json(self.food_items_file)
        
        return [
            FoodItem(
                id=food_data['id'],
                name=food_data['name'],
                serving_size=food_data['serving_size'],
                calories=food_data['calories'],
                total_fat=food_data['total_fat'],
                sodium=food_data['sodium'],
                total_carb=food_data['total_carb'],
                dietary_fiber=food_data['dietary_fiber'],
                sugars=food_data['sugars'],
                protein=food_data['protein'],
                location=food_data.get('location'),
                date=food_data.get('date'),
                meal_type=food_data.get('meal_type')
            )
            for food_data in food_items
        ]
    
    def get_foods_by_location_and_date(self, location: str, date: str) -> Dict[str, List[FoodItem]]:
        """Get foods grouped by meal type for a specific location and date"""
        food_items = self._load_json(self.food_items_file)
        
        foods_by_meal = {"Breakfast": [], "Lunch": [], "Dinner": []}
        
        for food_data in food_items:
            if food_data.get('location') == location and food_data.get('date') == date:
                food = FoodItem(
                    id=food_data['id'],
                    name=food_data['name'],
                    serving_size=food_data['serving_size'],
                    calories=food_data['calories'],
                    total_fat=food_data['total_fat'],
                    sodium=food_data['sodium'],
                    total_carb=food_data['total_carb'],
                    dietary_fiber=food_data['dietary_fiber'],
                    sugars=food_data['sugars'],
                    protein=food_data['protein'],
                    location=food_data.get('location'),
                    date=food_data.get('date'),
                    meal_type=food_data.get('meal_type')
                )
                meal_type = food_data.get('meal_type', 'Lunch')
                if meal_type in foods_by_meal:
                    foods_by_meal[meal_type].append(food)
        
        return foods_by_meal
    
    def search_food_items(self, query: str) -> List[FoodItem]:
        """Search food items by name (case-insensitive)"""
        food_items = self._load_json(self.food_items_file)
        query_lower = query.lower()
        
        matching_foods = []
        for food_data in food_items:
            if query_lower in food_data['name'].lower():
                matching_foods.append(FoodItem(
                    id=food_data['id'],
                    name=food_data['name'],
                    serving_size=food_data['serving_size'],
                    calories=food_data['calories'],
                    total_fat=food_data['total_fat'],
                    sodium=food_data['sodium'],
                    total_carb=food_data['total_carb'],
                    dietary_fiber=food_data['dietary_fiber'],
                    sugars=food_data['sugars'],
                    protein=food_data['protein'],
                    location=food_data.get('location'),
                    date=food_data.get('date'),
                    meal_type=food_data.get('meal_type')
                ))
        
        return matching_foods
    
    # ==================== MEAL ENTRY OPERATIONS ====================
    
    def create_meal_entry(self, entry: MealEntry) -> MealEntry:
        """Add a meal entry for a user"""
        meal_entries = self._load_json(self.meal_entries_file)
        
        entry.id = self._get_next_id(meal_entries)
        entry.created_at = datetime.now()
        
        # Get food item details
        food_item = self.get_food_item(entry.food_item_id)
        if food_item:
            entry.food_name = food_item.name
            entry.serving_size = food_item.serving_size
            entry.calories = food_item.calories
            entry.total_fat = food_item.total_fat
            entry.sodium = food_item.sodium
            entry.total_carb = food_item.total_carb
            entry.dietary_fiber = food_item.dietary_fiber
            entry.sugars = food_item.sugars
            entry.protein = food_item.protein
        
        entry_dict = {
            "id": entry.id,
            "user_id": entry.user_id,
            "food_item_id": entry.food_item_id,
            "entry_date": entry.entry_date,
            "meal_category": entry.meal_category,
            "servings": entry.servings,
            "created_at": entry.created_at.isoformat()
        }
        
        meal_entries.append(entry_dict)
        self._save_json(self.meal_entries_file, meal_entries)
        
        return entry
    
    def get_user_meals_for_date(self, user_id: int, date: str) -> Dict[str, List[MealEntry]]:
        """Get all meals for a user on a specific date, grouped by meal category"""
        meal_entries = self._load_json(self.meal_entries_file)
        
        meals_by_category = {"Breakfast": [], "Lunch": [], "Dinner": []}
        
        for entry_data in meal_entries:
            if entry_data['user_id'] == user_id and entry_data['entry_date'] == date:
                # Get food item details
                food_item = self.get_food_item(entry_data['food_item_id'])
                
                entry = MealEntry(
                    id=entry_data['id'],
                    user_id=entry_data['user_id'],
                    food_item_id=entry_data['food_item_id'],
                    entry_date=entry_data['entry_date'],
                    meal_category=entry_data['meal_category'],
                    servings=entry_data['servings'],
                    created_at=datetime.fromisoformat(entry_data['created_at'])
                )
                
                if food_item:
                    entry.food_name = food_item.name
                    entry.serving_size = food_item.serving_size
                    entry.calories = food_item.calories
                    entry.total_fat = food_item.total_fat
                    entry.sodium = food_item.sodium
                    entry.total_carb = food_item.total_carb
                    entry.dietary_fiber = food_item.dietary_fiber
                    entry.sugars = food_item.sugars
                    entry.protein = food_item.protein
                
                meals_by_category[entry.meal_category].append(entry)
        
        return meals_by_category
    
    def get_user_meals_7_days(self, user_id: int) -> Dict[str, Dict[str, List[MealEntry]]]:
        """Get 7 days of meal history for a user"""
        today = datetime.now().date()
        seven_days_ago = today - timedelta(days=6)
        
        result = {}
        current_date = seven_days_ago
        
        while current_date <= today:
            date_str = current_date.strftime("%Y-%m-%d")
            result[date_str] = self.get_user_meals_for_date(user_id, date_str)
            current_date += timedelta(days=1)
        
        return result
    
    def delete_meal_entry(self, entry_id: int):
        """Delete a meal entry"""
        meal_entries = self._load_json(self.meal_entries_file)
        meal_entries = [m for m in meal_entries if m['id'] != entry_id]
        self._save_json(self.meal_entries_file, meal_entries)
    
    def get_daily_totals(self, user_id: int, date: str) -> Dict[str, float]:
        """Calculate total nutrition for a user on a specific date"""
        meals = self.get_user_meals_for_date(user_id, date)
        
        totals = {
            "calories": 0,
            "total_fat": 0,
            "sodium": 0,
            "total_carb": 0,
            "dietary_fiber": 0,
            "sugars": 0,
            "protein": 0
        }
        
        for category in meals.values():
            for entry in category:
                servings = entry.servings or 1.0
                totals["calories"] += (entry.calories or 0) * servings
                totals["total_fat"] += (entry.total_fat or 0) * servings
                totals["sodium"] += (entry.sodium or 0) * servings
                totals["total_carb"] += (entry.total_carb or 0) * servings
                totals["dietary_fiber"] += (entry.dietary_fiber or 0) * servings
                totals["sugars"] += (entry.sugars or 0) * servings
                totals["protein"] += (entry.protein or 0) * servings
        
        return totals
