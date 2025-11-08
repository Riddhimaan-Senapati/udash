from dataclasses import dataclass
from typing import Optional
from datetime import datetime


@dataclass
class User:
    """User profile with health metrics (maps to profiles table)"""
    id: Optional[str]  # UUID from profiles table
    email: Optional[str] = None
    full_name: Optional[str] = None
    age: Optional[int] = None
    sex: Optional[str] = None  # 'M' or 'F'
    height_cm: Optional[float] = None
    weight_kg: Optional[float] = None
    activity_level: Optional[str] = None  # sedentary, light, moderate, active, very_active
    bmr: Optional[float] = None
    tdee: Optional[float] = None
    created_at: Optional[datetime] = None
    
    def calculate_bmr(self) -> float:
        """
        Calculate Basal Metabolic Rate using Mifflin-St Jeor Equation
        BMR = (10 × weight in kg) + (6.25 × height in cm) - (5 × age in years) + s
        where s = +5 for males and -161 for females
        """
        bmr = (10 * self.weight_kg) + (6.25 * self.height_cm) - (5 * self.age)
        if self.sex.upper() == 'M':
            bmr += 5
        else:
            bmr -= 161
        return round(bmr, 2)
    
    def calculate_tdee(self) -> float:
        """
        Calculate Total Daily Energy Expenditure based on activity level
        """
        activity_multipliers = {
            'sedentary': 1.2,      # Little or no exercise
            'light': 1.375,        # Light exercise 1-3 days/week
            'moderate': 1.55,      # Moderate exercise 3-5 days/week
            'active': 1.725,       # Heavy exercise 6-7 days/week
            'very_active': 1.9     # Very heavy exercise, physical job
        }
        
        bmr = self.calculate_bmr()
        multiplier = activity_multipliers.get(self.activity_level.lower(), 1.2)
        tdee = bmr * multiplier
        return round(tdee, 2)
    
    def update_calculations(self):
        """Update BMR and TDEE based on current metrics"""
        self.bmr = self.calculate_bmr()
        self.tdee = self.calculate_tdee()


@dataclass
class FoodItem:
    """Nutritional information for a food item"""
    id: Optional[int]
    name: str
    serving_size: str
    calories: int
    total_fat: float
    sodium: float
    total_carb: float
    dietary_fiber: float
    sugars: float
    protein: float
    location: Optional[str] = None
    date: Optional[str] = None
    meal_type: Optional[str] = None  # Breakfast, Lunch, Dinner from dining hall


@dataclass
class MealEntry:
    """A meal entry linking a profile to a food item"""
    id: Optional[int]
    profile_id: str  # UUID reference to profiles table
    food_item_id: int
    entry_date: str  # Format: YYYY-MM-DD
    meal_category: str  # Breakfast, Lunch, or Dinner
    servings: float = 1.0
    created_at: Optional[datetime] = None
    
    # Food item details (joined from FoodItem)
    food_name: Optional[str] = None
    serving_size: Optional[str] = None
    calories: Optional[int] = None
    total_fat: Optional[float] = None
    sodium: Optional[float] = None
    total_carb: Optional[float] = None
    dietary_fiber: Optional[float] = None
    sugars: Optional[float] = None
    protein: Optional[float] = None
