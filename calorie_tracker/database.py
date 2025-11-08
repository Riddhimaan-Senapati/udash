import os
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from supabase import create_client, Client
from dotenv import load_dotenv
from models import User, FoodItem, MealEntry

# Load environment variables
load_dotenv()


class Database:
    """Database interface for Supabase operations"""
    
    def __init__(self):
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")
        
        if not url or not key:
            raise ValueError(
                "Supabase credentials not found. "
                "Please create a .env file with SUPABASE_URL and SUPABASE_KEY"
            )
        
        self.client: Client = create_client(url, key)
    
    def init_database(self):
        """
        Initialize database tables if they don't exist.
        Run these SQL commands in your Supabase SQL editor:
        
        -- Profiles table (managed by Supabase Auth, extended with health fields)
        ALTER TABLE profiles ADD COLUMN IF NOT EXISTS age INTEGER;
        ALTER TABLE profiles ADD COLUMN IF NOT EXISTS sex TEXT CHECK (sex IN ('M', 'F'));
        ALTER TABLE profiles ADD COLUMN IF NOT EXISTS height_cm NUMERIC(5,2);
        ALTER TABLE profiles ADD COLUMN IF NOT EXISTS weight_kg NUMERIC(5,2);
        ALTER TABLE profiles ADD COLUMN IF NOT EXISTS activity_level INTEGER CHECK (activity_level IN (1, 2, 3, 4, 5));
        ALTER TABLE profiles ADD COLUMN IF NOT EXISTS bmr NUMERIC(7,2);
        ALTER TABLE profiles ADD COLUMN IF NOT EXISTS tdee NUMERIC(7,2);
        
        -- Food items table
        CREATE TABLE IF NOT EXISTS food_items (
            id BIGSERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            serving_size TEXT NOT NULL,
            calories INTEGER NOT NULL,
            total_fat NUMERIC(6,2) NOT NULL,
            sodium NUMERIC(7,2) NOT NULL,
            total_carb NUMERIC(6,2) NOT NULL,
            dietary_fiber NUMERIC(6,2) NOT NULL,
            sugars NUMERIC(6,2) NOT NULL,
            protein NUMERIC(6,2) NOT NULL,
            location TEXT,
            date TEXT,
            meal_type TEXT,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            UNIQUE(name, location, date, meal_type)
        );
        
        -- Meal entries table
        CREATE TABLE IF NOT EXISTS meal_entries (
            id BIGSERIAL PRIMARY KEY,
            profile_id UUID REFERENCES profiles(id) ON DELETE CASCADE,
            food_item_id BIGINT REFERENCES food_items(id) ON DELETE CASCADE,
            entry_date DATE NOT NULL,
            meal_category TEXT NOT NULL CHECK (meal_category IN ('Breakfast', 'Lunch', 'Dinner')),
            servings NUMERIC(4,2) DEFAULT 1.0,
            created_at TIMESTAMPTZ DEFAULT NOW()
        );
        
        -- Indexes for better performance
        CREATE INDEX IF NOT EXISTS idx_meal_entries_profile_date ON meal_entries(profile_id, entry_date);
        CREATE INDEX IF NOT EXISTS idx_food_items_location_date ON food_items(location, date);
        """
        print("Please run the SQL initialization script in your Supabase SQL editor.")
        print("See the init_database() method docstring for the SQL commands.")
    
    # ==================== USER/PROFILE OPERATIONS ====================
    
    def create_user(self, user: User) -> User:
        """Create or update a user profile"""
        user.update_calculations()
        
        data = {
            "age": user.age,
            "sex": user.sex,
            "height_cm": user.height_cm,
            "weight_kg": user.weight_kg,
            "activity_level": user.activity_level,
            "bmr": user.bmr,
            "tdee": user.tdee
        }
        
        # Add optional fields
        if user.email:
            data["email"] = user.email
        if user.full_name:
            data["full_name"] = user.full_name
        
        if user.id:
            # Update existing profile
            response = self.client.table("profiles").update(data).eq("id", user.id).execute()
        else:
            # Insert new profile
            response = self.client.table("profiles").insert(data).execute()
            
        if response.data:
            result = response.data[0]
            user.id = result["id"]
            user.created_at = result.get("created_at")
        return user
    
    def get_user(self, user_id: str) -> Optional[User]:
        """Get user by ID (UUID)"""
        response = self.client.table("profiles").select("*").eq("id", user_id).execute()
        if response.data:
            data = response.data[0]
            return User(
                id=data["id"],
                email=data.get("email"),
                full_name=data.get("full_name"),
                age=data.get("age"),
                sex=data.get("sex"),
                height_cm=data.get("height_cm"),
                weight_kg=data.get("weight_kg"),
                activity_level=data.get("activity_level"),
                bmr=data.get("bmr"),
                tdee=data.get("tdee"),
                created_at=data.get("created_at")
            )
        return None
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        response = self.client.table("profiles").select("*").eq("email", email).execute()
        if response.data:
            data = response.data[0]
            return User(
                id=data["id"],
                email=data.get("email"),
                full_name=data.get("full_name"),
                age=data.get("age"),
                sex=data.get("sex"),
                height_cm=data.get("height_cm"),
                weight_kg=data.get("weight_kg"),
                activity_level=data.get("activity_level"),
                bmr=data.get("bmr"),
                tdee=data.get("tdee"),
                created_at=data.get("created_at")
            )
        return None
    
    def get_all_users(self) -> List[User]:
        """Get all users/profiles"""
        response = self.client.table("profiles").select("*").order("email").execute()
        users = []
        for data in response.data:
            users.append(User(
                id=data["id"],
                email=data.get("email"),
                full_name=data.get("full_name"),
                age=data.get("age"),
                sex=data.get("sex"),
                height_cm=data.get("height_cm"),
                weight_kg=data.get("weight_kg"),
                activity_level=data.get("activity_level"),
                bmr=data.get("bmr"),
                tdee=data.get("tdee"),
                created_at=data.get("created_at")
            ))
        return users
    
    def update_user(self, user: User) -> User:
        """Update user information"""
        user.update_calculations()
        
        data = {
            "age": user.age,
            "sex": user.sex,
            "height_cm": user.height_cm,
            "weight_kg": user.weight_kg,
            "activity_level": user.activity_level,
            "bmr": user.bmr,
            "tdee": user.tdee
        }
        
        if user.email:
            data["email"] = user.email
        if user.full_name:
            data["full_name"] = user.full_name
        
        self.client.table("profiles").update(data).eq("id", user.id).execute()
        return user
    
    def delete_user(self, user_id: str):
        """Delete a user/profile"""
        self.client.table("profiles").delete().eq("id", user_id).execute()
    
    # ==================== FOOD ITEM OPERATIONS ====================
    
    def create_food_item(self, food: FoodItem) -> FoodItem:
        """Create a new food item"""
        data = {
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
        
        # Try to insert, if duplicate exists, get existing
        try:
            response = self.client.table("food_items").insert(data).execute()
            if response.data:
                food.id = response.data[0]["id"]
        except Exception as e:
            # If duplicate, find and return existing
            response = self.client.table("food_items").select("*").match({
                "name": food.name,
                "location": food.location,
                "date": food.date,
                "meal_type": food.meal_type
            }).execute()
            if response.data:
                food.id = response.data[0]["id"]
        
        return food
    
    def get_food_item(self, food_id: int) -> Optional[FoodItem]:
        """Get food item by ID"""
        response = self.client.table("food_items").select("*").eq("id", food_id).execute()
        if response.data:
            data = response.data[0]
            return FoodItem(
                id=data["id"],
                name=data["name"],
                serving_size=data["serving_size"],
                calories=data["calories"],
                total_fat=data["total_fat"],
                sodium=data["sodium"],
                total_carb=data["total_carb"],
                dietary_fiber=data["dietary_fiber"],
                sugars=data["sugars"],
                protein=data["protein"],
                location=data.get("location"),
                date=data.get("date"),
                meal_type=data.get("meal_type")
            )
        return None
    
    def get_all_food_items(self) -> List[FoodItem]:
        """Get all food items"""
        response = self.client.table("food_items").select("*").order("name").execute()
        foods = []
        for data in response.data:
            foods.append(FoodItem(
                id=data["id"],
                name=data["name"],
                serving_size=data["serving_size"],
                calories=data["calories"],
                total_fat=data["total_fat"],
                sodium=data["sodium"],
                total_carb=data["total_carb"],
                dietary_fiber=data["dietary_fiber"],
                sugars=data["sugars"],
                protein=data["protein"],
                location=data.get("location"),
                date=data.get("date"),
                meal_type=data.get("meal_type")
            ))
        return foods
    
    def get_foods_by_location_and_date(self, location: str, date: str) -> Dict[str, List[FoodItem]]:
        """Get foods grouped by meal type for a specific location and date"""
        response = self.client.table("food_items").select("*").match({
            "location": location,
            "date": date
        }).execute()
        
        foods_by_meal = {"Breakfast": [], "Lunch": [], "Dinner": []}
        
        for data in response.data:
            food = FoodItem(
                id=data["id"],
                name=data["name"],
                serving_size=data["serving_size"],
                calories=data["calories"],
                total_fat=data["total_fat"],
                sodium=data["sodium"],
                total_carb=data["total_carb"],
                dietary_fiber=data["dietary_fiber"],
                sugars=data["sugars"],
                protein=data["protein"],
                location=data.get("location"),
                date=data.get("date"),
                meal_type=data.get("meal_type")
            )
            meal_type = data.get("meal_type", "Lunch")
            if meal_type in foods_by_meal:
                foods_by_meal[meal_type].append(food)
        
        return foods_by_meal
    
    def search_food_items(self, query: str) -> List[FoodItem]:
        """Search food items by name"""
        response = self.client.table("food_items").select("*").ilike("name", f"%{query}%").execute()
        foods = []
        for data in response.data:
            foods.append(FoodItem(
                id=data["id"],
                name=data["name"],
                serving_size=data["serving_size"],
                calories=data["calories"],
                total_fat=data["total_fat"],
                sodium=data["sodium"],
                total_carb=data["total_carb"],
                dietary_fiber=data["dietary_fiber"],
                sugars=data["sugars"],
                protein=data["protein"],
                location=data.get("location"),
                date=data.get("date"),
                meal_type=data.get("meal_type")
            ))
        return foods
    
    # ==================== MEAL ENTRY OPERATIONS ====================
    
    def create_meal_entry(self, entry: MealEntry) -> MealEntry:
        """Add a meal entry for a user"""
        data = {
            "profile_id": entry.profile_id,
            "food_item_id": entry.food_item_id,
            "entry_date": entry.entry_date,
            "meal_category": entry.meal_category,
            "servings": entry.servings
        }
        
        response = self.client.table("meal_entries").insert(data).execute()
        if response.data:
            entry.id = response.data[0]["id"]
            entry.created_at = response.data[0]["created_at"]
        return entry
    
    def get_user_meals_for_date(self, profile_id: str, date: str) -> Dict[str, List[MealEntry]]:
        """Get all meals for a profile on a specific date, grouped by meal category"""
        response = self.client.table("meal_entries").select(
            "*, food_items(*)"
        ).eq("profile_id", profile_id).eq("entry_date", date).execute()
        
        meals_by_category = {"Breakfast": [], "Lunch": [], "Dinner": []}
        
        for data in response.data:
            food_data = data["food_items"]
            entry = MealEntry(
                id=data["id"],
                profile_id=data["profile_id"],
                food_item_id=data["food_item_id"],
                entry_date=data["entry_date"],
                meal_category=data["meal_category"],
                servings=data["servings"],
                created_at=data["created_at"],
                food_name=food_data["name"],
                serving_size=food_data["serving_size"],
                calories=food_data["calories"],
                total_fat=food_data["total_fat"],
                sodium=food_data["sodium"],
                total_carb=food_data["total_carb"],
                dietary_fiber=food_data["dietary_fiber"],
                sugars=food_data["sugars"],
                protein=food_data["protein"]
            )
            meals_by_category[entry.meal_category].append(entry)
        
        return meals_by_category
    
    def get_user_meals_7_days(self, profile_id: str) -> Dict[str, Dict[str, List[MealEntry]]]:
        """Get 7 days of meal history for a profile"""
        today = datetime.now().date()
        seven_days_ago = today - timedelta(days=6)
        
        result = {}
        current_date = seven_days_ago
        
        while current_date <= today:
            date_str = current_date.strftime("%Y-%m-%d")
            result[date_str] = self.get_user_meals_for_date(profile_id, date_str)
            current_date += timedelta(days=1)
        
        return result
    
    def delete_meal_entry(self, entry_id: int):
        """Delete a meal entry"""
        self.client.table("meal_entries").delete().eq("id", entry_id).execute()
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """Legacy method - get user by full_name for backward compatibility"""
        response = self.client.table("profiles").select("*").eq("full_name", username).execute()
        if response.data:
            data = response.data[0]
            return User(
                id=data["id"],
                email=data.get("email"),
                full_name=data.get("full_name"),
                age=data.get("age"),
                sex=data.get("sex"),
                height_cm=data.get("height_cm"),
                weight_kg=data.get("weight_kg"),
                activity_level=data.get("activity_level"),
                bmr=data.get("bmr"),
                tdee=data.get("tdee"),
                created_at=data.get("created_at")
            )
        return None
    
    def get_daily_totals(self, profile_id: str, date: str) -> Dict[str, float]:
        """Calculate total nutrition for a profile on a specific date"""
        meals = self.get_user_meals_for_date(profile_id, date)
        
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
