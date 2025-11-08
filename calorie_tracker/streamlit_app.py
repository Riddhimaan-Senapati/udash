import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from database_json import JSONDatabase  # Using JSON database for testing
from models import User, FoodItem, MealEntry
from data_loader import get_available_dates, get_available_locations
import os

# Page configuration
st.set_page_config(
    page_title="7-Day Calorie Tracker",
    page_icon="🍽️",
    layout="wide"
)

# Initialize database connection
@st.cache_resource
def get_database():
    """Initialize JSON database (switch to Supabase later)"""
    return JSONDatabase(data_dir="data")

db = get_database()

# Custom CSS
st.markdown("""
    <style>
    .metric-card {
        background-color: #f0f2f6;
        padding: 15px;
        border-radius: 10px;
        margin: 10px 0;
    }
    .meal-category {
        font-size: 20px;
        font-weight: bold;
        color: #1f77b4;
        margin-top: 20px;
    }
    </style>
""", unsafe_allow_html=True)


def display_user_metrics(user: User):
    """Display user health metrics in a nice format"""
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("BMR", f"{user.bmr:.0f} kcal/day")
    with col2:
        st.metric("TDEE", f"{user.tdee:.0f} kcal/day")
    with col3:
        st.metric("Weight", f"{user.weight_kg:.1f} kg")
    with col4:
        st.metric("Height", f"{user.height_cm:.0f} cm")
    
    st.info(f"**Profile:** {user.age} years old, {user.sex}, Activity Level: {user.activity_level.replace('_', ' ').title()}")


def display_nutrition_chart(daily_totals: dict, user_tdee: float):
    """Display nutrition information with progress bars and metrics"""
    if daily_totals["calories"] == 0:
        st.info("No meals logged for this day")
        return
    
    # Create progress bar for calories vs TDEE
    calorie_percent = (daily_totals["calories"] / user_tdee) * 100
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.metric("Total Calories", f"{daily_totals['calories']:.0f} kcal", 
                 f"{calorie_percent:.1f}% of TDEE")
        st.progress(min(calorie_percent / 100, 1.0))
    
    with col2:
        st.metric("TDEE Target", f"{user_tdee:.0f} kcal")
    
    # Macronutrients display with bar chart
    st.markdown("### Macronutrients")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Protein", f"{daily_totals['protein']:.1f}g")
        # Visual bar for protein (assuming ~2g per kg body weight as target)
        protein_target = 140  # Default target
        protein_percent = min((daily_totals['protein'] / protein_target) * 100, 100)
        st.progress(protein_percent / 100)
    
    with col2:
        st.metric("Carbs", f"{daily_totals['total_carb']:.1f}g")
        # Visual bar for carbs (assuming ~45-65% of calories)
        carb_calories = daily_totals['total_carb'] * 4
        carb_percent = min((carb_calories / user_tdee) * 100, 100)
        st.progress(carb_percent / 100)
    
    with col3:
        st.metric("Fat", f"{daily_totals['total_fat']:.1f}g")
        # Visual bar for fat (assuming ~20-35% of calories)
        fat_calories = daily_totals['total_fat'] * 9
        fat_percent = min((fat_calories / user_tdee) * 100, 100)
        st.progress(fat_percent / 100)
    
    # Additional nutrients
    st.markdown("### Other Nutrients")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Fiber", f"{daily_totals['dietary_fiber']:.1f}g")
    with col2:
        st.metric("Sugars", f"{daily_totals['sugars']:.1f}g")
    with col3:
        st.metric("Sodium", f"{daily_totals['sodium']:.0f}mg")


def display_meal_entries(meals: list[MealEntry]):
    """Display meal entries in a formatted table"""
    if not meals:
        st.write("No meals logged")
        return
    
    data = []
    for entry in meals:
        servings = entry.servings or 1.0
        data.append({
            "Food": entry.food_name,
            "Serving Size": entry.serving_size,
            "Servings": f"{servings:.1f}",
            "Calories": f"{int((entry.calories or 0) * servings)}",
            "Protein": f"{(entry.protein or 0) * servings:.1f}g",
            "Carbs": f"{(entry.total_carb or 0) * servings:.1f}g",
            "Fat": f"{(entry.total_fat or 0) * servings:.1f}g",
            "Entry ID": entry.id
        })
    
    df = pd.DataFrame(data)
    st.dataframe(df, use_container_width=True, hide_index=True)


def create_user_form():
    """Form to create a new user"""
    with st.form("create_user_form"):
        st.subheader("Create New User")
        
        col1, col2 = st.columns(2)
        
        with col1:
            username = st.text_input("Username*")
            age = st.number_input("Age*", min_value=13, max_value=120, value=25)
            sex = st.selectbox("Sex*", ["M", "F"])
            height_cm = st.number_input("Height (cm)*", min_value=100.0, max_value=250.0, value=170.0, step=0.5)
        
        with col2:
            weight_kg = st.number_input("Weight (kg)*", min_value=30.0, max_value=300.0, value=70.0, step=0.1)
            activity_level = st.selectbox("Activity Level*", [
                "sedentary",
                "light",
                "moderate",
                "active",
                "very_active"
            ])
        
        submitted = st.form_submit_button("Create User")
        
        if submitted:
            if not username:
                st.error("Username is required")
            else:
                try:
                    user = User(
                        id=None,
                        username=username,
                        age=age,
                        sex=sex,
                        height_cm=height_cm,
                        weight_kg=weight_kg,
                        activity_level=activity_level
                    )
                    created_user = db.create_user(user)
                    st.success(f"User '{username}' created successfully!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error creating user: {e}")


def main():
    st.title("🍽️ 7-Day Calorie Tracker")
    
    # Sidebar navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Go to", [
        "User Dashboard",
        "Browse Foods",
        "Add Food to Tracker",
        "Manage Users",
        "View All Food Items"
    ])
    
    if page == "User Dashboard":
        st.header("User Dashboard")
        
        # User selection
        users = db.get_all_users()
        if not users:
            st.warning("No users found. Please create a user first.")
            return
        
        user_options = {user.username: user for user in users}
        selected_username = st.selectbox("Select User", list(user_options.keys()))
        
        if selected_username:
            user = user_options[selected_username]
            
            # Display user metrics
            display_user_metrics(user)
            
            st.markdown("---")
            st.subheader("7-Day Meal History")
            
            # Get 7 days of meals
            meals_7_days = db.get_user_meals_7_days(user.id)
            
            # Display each day
            for date_str in sorted(meals_7_days.keys(), reverse=True):
                with st.expander(f"📅 {date_str} ({datetime.strptime(date_str, '%Y-%m-%d').strftime('%A')})", expanded=(date_str == datetime.now().strftime("%Y-%m-%d"))):
                    meals_by_category = meals_7_days[date_str]
                    
                    # Calculate daily totals
                    daily_totals = db.get_daily_totals(user.id, date_str)
                    
                    # Display nutrition chart
                    display_nutrition_chart(daily_totals, user.tdee)
                    
                    st.markdown("---")
                    
                    # Display meals by category
                    for category in ["Breakfast", "Lunch", "Dinner"]:
                        st.markdown(f"### {category}")
                        display_meal_entries(meals_by_category[category])
    
    elif page == "Browse Foods":
        st.header("Browse Available Foods")
        
        st.info("View available foods from dining halls by date and location for the past 7 days")
        
        # Get available dates and locations
        json_path = "../backend/all_dining_halls_menus.json"
        
        if os.path.exists(json_path):
            dates = get_available_dates(json_path)
            locations = get_available_locations(json_path)
            
            # Get last 7 days
            today = datetime.now().date()
            last_7_days = [(today - timedelta(days=i)).strftime("%A %B %d, %Y") for i in range(7)]
            available_last_7 = [d for d in dates if any(d.startswith(day.split()[0]) for day in last_7_days)]
            
            col1, col2 = st.columns(2)
            
            with col1:
                selected_date = st.selectbox("Select Date", available_last_7 if available_last_7 else dates)
            
            with col2:
                selected_location = st.selectbox("Select Location", locations)
            
            if selected_date and selected_location:
                # Get foods for this location and date
                foods_by_meal = db.get_foods_by_location_and_date(selected_location, selected_date)
                
                for meal_type in ["Breakfast", "Lunch", "Dinner"]:
                    st.markdown(f"### {meal_type}")
                    foods = foods_by_meal[meal_type]
                    
                    if not foods:
                        st.write(f"No {meal_type.lower()} items available")
                    else:
                        food_data = []
                        for food in foods:
                            food_data.append({
                                "Name": food.name,
                                "Serving Size": food.serving_size,
                                "Calories": food.calories,
                                "Protein": f"{food.protein}g",
                                "Carbs": f"{food.total_carb}g",
                                "Fat": f"{food.total_fat}g",
                                "Fiber": f"{food.dietary_fiber}g",
                                "Sodium": f"{food.sodium}mg"
                            })
                        
                        df = pd.DataFrame(food_data)
                        st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.error("Dining hall menus file not found. Please load the data first.")
    
    elif page == "Add Food to Tracker":
        st.header("Add Food to Calorie Tracker")
        
        # User selection
        users = db.get_all_users()
        if not users:
            st.warning("No users found. Please create a user first.")
            return
        
        user_options = {user.username: user for user in users}
        selected_username = st.selectbox("Select User", list(user_options.keys()))
        
        if selected_username:
            user = user_options[selected_username]
            
            # Search for food
            search_query = st.text_input("Search for food", placeholder="Enter food name...")
            
            if search_query:
                foods = db.search_food_items(search_query)
                
                if foods:
                    st.write(f"Found {len(foods)} items")
                    
                    # Display foods and allow selection
                    for food in foods[:20]:  # Limit to 20 results
                        with st.container():
                            col1, col2, col3 = st.columns([3, 2, 1])
                            
                            with col1:
                                st.write(f"**{food.name}**")
                                st.caption(f"{food.location} - {food.date}")
                            
                            with col2:
                                st.write(f"{food.calories} kcal | {food.serving_size}")
                                st.caption(f"P: {food.protein}g | C: {food.total_carb}g | F: {food.total_fat}g")
                            
                            with col3:
                                with st.form(f"add_food_{food.id}"):
                                    meal_category = st.selectbox("Meal", ["Breakfast", "Lunch", "Dinner"], key=f"meal_{food.id}")
                                    servings = st.number_input("Servings", min_value=0.1, max_value=10.0, value=1.0, step=0.1, key=f"servings_{food.id}")
                                    entry_date = st.date_input("Date", value=datetime.now(), key=f"date_{food.id}")
                                    
                                    if st.form_submit_button("Add"):
                                        entry = MealEntry(
                                            id=None,
                                            user_id=user.id,
                                            food_item_id=food.id,
                                            entry_date=entry_date.strftime("%Y-%m-%d"),
                                            meal_category=meal_category,
                                            servings=servings
                                        )
                                        db.create_meal_entry(entry)
                                        st.success(f"Added {food.name} to {meal_category}!")
                            
                            st.markdown("---")
                else:
                    st.info("No foods found matching your search")
    
    elif page == "Manage Users":
        st.header("Manage Users")
        
        tab1, tab2 = st.tabs(["Create User", "View/Edit Users"])
        
        with tab1:
            create_user_form()
        
        with tab2:
            users = db.get_all_users()
            
            if not users:
                st.info("No users found")
            else:
                for user in users:
                    with st.expander(f"👤 {user.username}"):
                        col1, col2 = st.columns([3, 1])
                        
                        with col1:
                            st.write(f"**Age:** {user.age}")
                            st.write(f"**Sex:** {user.sex}")
                            st.write(f"**Height:** {user.height_cm} cm")
                            st.write(f"**Weight:** {user.weight_kg} kg")
                            st.write(f"**Activity Level:** {user.activity_level}")
                            st.write(f"**BMR:** {user.bmr:.0f} kcal/day")
                            st.write(f"**TDEE:** {user.tdee:.0f} kcal/day")
                        
                        with col2:
                            if st.button("Delete", key=f"delete_{user.id}"):
                                db.delete_user(user.id)
                                st.success(f"Deleted user {user.username}")
                                st.rerun()
    
    elif page == "View All Food Items":
        st.header("All Food Items Database")
        
        st.info("This shows all food items loaded in the database")
        
        # Search functionality
        search = st.text_input("Filter by name", placeholder="Type to filter...")
        
        foods = db.get_all_food_items() if not search else db.search_food_items(search)
        
        if foods:
            st.write(f"Showing {len(foods)} items")
            
            food_data = []
            for food in foods:
                food_data.append({
                    "ID": food.id,
                    "Name": food.name,
                    "Location": food.location,
                    "Date": food.date,
                    "Meal Type": food.meal_type,
                    "Serving Size": food.serving_size,
                    "Calories": food.calories,
                    "Protein (g)": food.protein,
                    "Carbs (g)": food.total_carb,
                    "Fat (g)": food.total_fat,
                    "Fiber (g)": food.dietary_fiber,
                    "Sodium (mg)": food.sodium
                })
            
            df = pd.DataFrame(food_data)
            st.dataframe(df, use_container_width=True, hide_index=True, height=600)
        else:
            st.info("No food items found in database. Please load data using data_loader.py")


if __name__ == "__main__":
    main()
