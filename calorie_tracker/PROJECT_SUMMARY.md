# 7-Day Calorie Tracker - Project Summary

## 🎯 Project Overview

A comprehensive multi-user calorie tracking application with persistent storage, featuring a rolling 7-day meal history, automatic BMR/TDEE calculations, and integration with dining hall menu data.

## ✅ Completed Features

### Core Functionality
- ✅ **Multi-user support** with unique profiles
- ✅ **Persistent userbase** using Supabase (PostgreSQL)
- ✅ **7-day rolling meal history** per user
- ✅ **Meal categorization** (Breakfast, Lunch, Dinner)
- ✅ **Comprehensive nutritional tracking**:
  - Serving Size
  - Calories
  - Total Fat (g)
  - Sodium (mg)
  - Total Carbohydrate (g)
  - Dietary Fiber (g)
  - Sugars (g)
  - Protein (g)

### User Health Metrics
- ✅ **Automatic BMR calculation** (Mifflin-St Jeor equation)
- ✅ **Automatic TDEE calculation** (activity level based)
- ✅ **User profile fields**:
  - Username
  - Age
  - Sex (M/F)
  - Height (cm)
  - Weight (kg)
  - Activity Level (5 levels: sedentary to very active)

### Streamlit Dashboard
- ✅ **User Dashboard**
  - View 7-day meal history
  - Daily calorie totals vs TDEE target
  - Interactive macronutrient charts (Plotly)
  - Health metrics display (BMR, TDEE, weight, height)
  - Expandable day views with meal breakdowns

- ✅ **Browse Foods**
  - Filter by dining hall location
  - Filter by date (past 7 days)
  - View foods by meal type
  - Complete nutritional information display

- ✅ **Add Food to Tracker**
  - User selection dropdown
  - Food search functionality
  - Meal category selection
  - Customizable servings
  - Date selection for meal entry

- ✅ **Manage Users**
  - Create new users
  - View all users
  - Edit user information
  - Delete users
  - View calculated BMR/TDEE

- ✅ **View All Food Items**
  - Complete database food listing
  - Search/filter functionality
  - Sortable data table

### Database & Backend
- ✅ **Supabase integration** with Row Level Security
- ✅ **Three main tables**:
  - `users` - User profiles and metrics
  - `food_items` - All available foods with nutrition
  - `meal_entries` - User meal tracking records
- ✅ **Database indexes** for performance
- ✅ **Data loader** for dining hall JSON import
- ✅ **CRUD operations** for all entities

### Data Models
- ✅ **User model** with BMR/TDEE calculation methods
- ✅ **FoodItem model** with all nutritional fields
- ✅ **MealEntry model** with serving size support

## 📁 Project Structure

```
calorie_tracker/
├── .env.example              # Environment variables template
├── .gitignore               # Git ignore file
├── requirements.txt         # Python dependencies
├── README.md               # Full documentation
├── QUICKSTART.md           # Quick start guide
├── PROJECT_SUMMARY.md      # This file
├── init_database.sql       # SQL initialization script
├── setup.py                # Automated setup script
├── models.py               # Data models (User, FoodItem, MealEntry)
├── database.py             # Supabase database interface
├── data_loader.py          # JSON to database loader
└── streamlit_app.py        # Main application (426 lines)
```

## 🔧 Technologies Used

| Technology | Purpose | Version |
|------------|---------|---------|
| Python | Core language | 3.8+ |
| Streamlit | Web dashboard | 1.29.0 |
| Supabase | PostgreSQL backend | 2.3.0 |
| Plotly | Interactive charts | 5.18.0 |
| Pandas | Data manipulation | 2.1.3 |
| python-dotenv | Environment config | 1.0.0 |

## 🧮 BMR & TDEE Calculations

### Basal Metabolic Rate (Mifflin-St Jeor)
```
Men:   BMR = (10 × weight_kg) + (6.25 × height_cm) - (5 × age) + 5
Women: BMR = (10 × weight_kg) + (6.25 × height_cm) - (5 × age) - 161
```

### Total Daily Energy Expenditure
```
TDEE = BMR × Activity Multiplier

Activity Multipliers:
- Sedentary (little/no exercise): 1.2
- Light (1-3 days/week): 1.375
- Moderate (3-5 days/week): 1.55
- Active (6-7 days/week): 1.725
- Very Active (physical job + exercise): 1.9
```

## 📊 Database Schema

### Users Table
```sql
- id (BIGSERIAL PRIMARY KEY)
- username (TEXT UNIQUE)
- age (INTEGER)
- sex (TEXT: M/F)
- height_cm (NUMERIC)
- weight_kg (NUMERIC)
- activity_level (TEXT: 5 options)
- bmr (NUMERIC, calculated)
- tdee (NUMERIC, calculated)
- created_at (TIMESTAMPTZ)
```

### Food Items Table
```sql
- id (BIGSERIAL PRIMARY KEY)
- name (TEXT)
- serving_size (TEXT)
- calories (INTEGER)
- total_fat (NUMERIC)
- sodium (NUMERIC)
- total_carb (NUMERIC)
- dietary_fiber (NUMERIC)
- sugars (NUMERIC)
- protein (NUMERIC)
- location (TEXT)
- date (TEXT)
- meal_type (TEXT)
- created_at (TIMESTAMPTZ)
- UNIQUE(name, location, date, meal_type)
```

### Meal Entries Table
```sql
- id (BIGSERIAL PRIMARY KEY)
- user_id (BIGINT → users.id)
- food_item_id (BIGINT → food_items.id)
- entry_date (DATE)
- meal_category (TEXT: Breakfast/Lunch/Dinner)
- servings (NUMERIC, default 1.0)
- created_at (TIMESTAMPTZ)
```

## 🎨 User Interface Features

### Interactive Elements
- Dropdown menus for user/location/date selection
- Search bars with real-time filtering
- Expandable date sections (accordions)
- Data tables with sorting
- Forms for user creation and food entry
- Progress bars for calorie tracking
- Metric cards for health data

### Visualizations
- Bar charts for macronutrients (Plotly)
- Daily calorie progress indicators
- Color-coded nutrition metrics
- Tabular meal entry displays

## 🔐 Security Features

- Environment variables for credentials
- Row Level Security (RLS) in Supabase
- .gitignore for sensitive files
- Input validation on all user inputs
- SQL injection prevention (parameterized queries)

## 📈 Data Flow

1. **Food Data Import**
   - JSON file (`all_dining_halls_menus.json`) → `data_loader.py` → Supabase `food_items` table

2. **User Creation**
   - Streamlit form → `models.User` → `database.create_user()` → Supabase `users` table
   - BMR & TDEE automatically calculated

3. **Meal Tracking**
   - User searches food → Selects from results → Creates meal entry
   - `MealEntry` → `database.create_meal_entry()` → Supabase `meal_entries` table

4. **Dashboard Display**
   - Select user → Query 7 days of meals → Join with food data → Display with charts

## 🚀 Setup Process

1. **Prerequisites**: Python 3.8+, Supabase account
2. **Install**: `pip install -r requirements.txt`
3. **Configure**: Create `.env` with Supabase credentials
4. **Initialize DB**: Run `init_database.sql` in Supabase SQL Editor
5. **Setup**: Run `python setup.py` (loads data, creates demo user)
6. **Launch**: `streamlit run streamlit_app.py`

## 📝 Key Implementation Details

### Data Persistence
- All data stored in Supabase (PostgreSQL)
- Automatic timestamps on all records
- Foreign key relationships with CASCADE delete
- Unique constraints to prevent duplicates

### Performance Optimizations
- Database indexes on frequently queried columns
- Caching of database connection (`@st.cache_resource`)
- Batch loading of food items (100 at a time)
- Limited result sets (20 foods per search)

### User Experience
- Intuitive navigation with sidebar
- Clear section headers and instructions
- Helpful error messages
- Loading indicators for long operations
- Responsive layout (wide mode)

## 🎯 Requirements Met

✅ **All original requirements implemented:**
1. ✅ Multi-user support with persistent userbase
2. ✅ Unique profile per user
3. ✅ Rolling 7-day history
4. ✅ Meals categorized into Breakfast/Lunch/Dinner
5. ✅ All 8 nutritional fields tracked (no more, no less)
6. ✅ Streamlit dashboard for testing
7. ✅ View all available food items
8. ✅ User selection dropdown
9. ✅ Display complete 7-day meal history by day and meal type
10. ✅ Browse foods by location and date (past 7 days)
11. ✅ User health metrics (weight, age, height, sex, TDEE, BMR, activity)
12. ✅ Supabase database integration
13. ✅ Automatic BMR and TDEE calculations

## 📖 Documentation Provided

- ✅ `README.md` - Comprehensive documentation (200+ lines)
- ✅ `QUICKSTART.md` - Step-by-step setup guide
- ✅ `PROJECT_SUMMARY.md` - This summary document
- ✅ `init_database.sql` - Commented SQL script
- ✅ `.env.example` - Environment template
- ✅ Inline code comments throughout all Python files

## 🌟 Highlights

- **Clean Architecture**: Separated concerns (models, database, UI)
- **Type Hints**: Used throughout for better code clarity
- **Error Handling**: Graceful error messages and fallbacks
- **Extensible Design**: Easy to add new features or modify existing ones
- **Professional UI**: Modern, clean interface with charts and metrics
- **Complete Documentation**: Multiple guides for different use cases

## 🔮 Potential Enhancements (Not Implemented)

Future additions could include:
- User authentication (login/logout)
- Goal setting and tracking
- Weekly/monthly reports
- Food favorites/recent items
- Custom food entry
- Export data (CSV/PDF)
- Mobile responsiveness improvements
- Meal planning features
- Social features (sharing, friends)

---

**Project Status**: ✅ **COMPLETE**

All requested features have been implemented and tested. The application is ready for deployment and use.
