"""
Setup script for the Calorie Tracker application
This script helps with initial setup and data population
Using Supabase (PostgreSQL) for database storage
"""

import os
import sys
from datetime import datetime


def check_environment():
    """Check if .env file exists"""
    if not os.path.exists(".env"):
        print("❌ .env file not found")
        print("   Please create a .env file with your Supabase credentials")
        print("   See .env.example for reference")
        return False
    print("✅ .env file exists")
    return True


def check_database_connection():
    """Test database connection"""
    try:
        from database import Database
        db = Database()
        print("✅ Supabase database connected")
        return db
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return None


def check_tables(db):
    """Check if database tables are accessible"""
    try:
        # Check if tables exist and are accessible
        users = db.get_all_users()
        print("✅ Users table accessible")
        
        foods = db.get_all_food_items()
        print("✅ Food items table accessible")
        
        print("✅ Meal entries table accessible")
        
        return True
    except Exception as e:
        print(f"❌ Database tables check failed: {e}")
        print("   Make sure you've run the init_database.sql script in Supabase")
        return False


def load_food_data(db):
    """Load food data from JSON file"""
    json_path = "../backend/all_dining_halls_menus.json"
    
    if not os.path.exists(json_path):
        print(f"❌ Food data file not found: {json_path}")
        return False
    
    print(f"✅ Found food data file")
    
    # Check if data already loaded
    try:
        foods = db.get_all_food_items()
        
        if len(foods) > 0:
            print(f"ℹ️  Database already contains {len(foods)} food items")
            response = input("   Do you want to reload the data? (y/n): ")
            if response.lower() != 'y':
                return True
    except:
        pass
    
    print("\n📥 Loading food data into database...")
    print("   This may take a few minutes...")
    
    try:
        from data_loader import populate_database_from_json
        populate_database_from_json(json_path, db)
        print("✅ Food data loaded successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to load food data: {e}")
        return False


def create_demo_user(db):
    """Create a demo user"""
    try:
        from models import User
        
        # Check if demo user already exists
        existing = db.get_user_by_username("demo_user")
        if existing:
            print("ℹ️  Demo user already exists")
            return True
        
        demo_user = User(
            id=None,
            username="demo_user",
            age=25,
            sex="M",
            height_cm=175.0,
            weight_kg=70.0,
            activity_level="moderate"
        )
        
        db.create_user(demo_user)
        print("✅ Demo user created (username: demo_user)")
        print(f"   BMR: {demo_user.bmr:.0f} kcal/day")
        print(f"   TDEE: {demo_user.tdee:.0f} kcal/day")
        return True
    except Exception as e:
        print(f"❌ Failed to create demo user: {e}")
        return False


def main():
    print("=" * 60)
    print("🍽️  Calorie Tracker Setup (Supabase)")
    print("=" * 60)
    print()
    
    # Step 1: Check environment
    print("Step 1: Checking environment configuration...")
    if not check_environment():
        return
    print()
    
    # Step 2: Check database connection
    print("Step 2: Connecting to Supabase...")
    db = check_database_connection()
    if not db:
        return
    print()
    
    # Step 3: Check tables
    print("Step 3: Checking database tables...")
    if not check_tables(db):
        return
    print()
    
    # Step 4: Load food data
    print("Step 4: Loading food data...")
    if not load_food_data(db):
        print("⚠️  Warning: Food data not loaded. You can load it later using data_loader.py")
    print()
    
    # Step 5: Create demo user
    print("Step 5: Creating demo user...")
    response = input("   Do you want to create a demo user? (y/n): ")
    if response.lower() == 'y':
        create_demo_user(db)
    print()
    
    # Done
    print("=" * 60)
    print("✨ Setup complete!")
    print("=" * 60)
    print()
    print("📝 Using Supabase (PostgreSQL) for data storage")
    print("   Data is automatically synced across all devices")
    print()
    print("🚀 To start the application, run:")
    print("   streamlit run streamlit_app.py")
    print()


if __name__ == "__main__":
    main()
