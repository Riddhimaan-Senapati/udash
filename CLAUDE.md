# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

DoorSmashOrPass is a smart nutrition tracking app for UMass dining hall students (HackUMass 2025). It combines a DoorDash-like ordering experience with calorie tracking, menu scraping, and AI-powered meal recommendations.

**Key Features:**
- Real-time dining hall menu scraping (4 locations: Berkshire, Worcester, Franklin, Hampshire)
- Multi-user calorie tracking with 7-day rolling history
- AI chatbot for order assistance using PydanticAI + Gemini
- Automatic BMR/TDEE calculations based on user health metrics
- Streamlit dashboards for calorie tracking and testing

## Tech Stack

**Backend:**
- Python 3.8+ with FastAPI
- PydanticAI with Gemini (google-gla:gemini-2.5-flash)
- Supabase (PostgreSQL) for data persistence
- Playwright for web scraping (headless browser)
- BeautifulSoup4 for HTML parsing

**Frontend:**
- Next.js (planned, not yet implemented)
- Streamlit (current UI for testing)

**MCP Context:**
- Use Context7 MCP server for accessing latest documentation for all project technologies

## Project Structure

```
udash/
├── backend/                          # FastAPI services and scraping
│   ├── scraper.py                   # Playwright-based menu scraper for 4 dining halls
│   ├── chatbot_api.py               # PydanticAI agent with Gemini (port 8002)
│   ├── orders_api.py                # Mock orders API (port 8001)
│   ├── streamlit_app.py             # Chat interface for testing chatbot
│   ├── all_dining_halls_menus.json  # Scraped menu data
│   ├── requirements.txt
│   ├── .env                         # GOOGLE_API_KEY
│   └── SETUP_AGENT.md               # Agent setup docs
├── calorie_tracker/                 # Nutrition tracking system
│   ├── models.py                    # User, FoodItem, MealEntry dataclasses
│   ├── database.py                  # Supabase database interface
│   ├── data_loader.py               # JSON → Supabase loader
│   ├── streamlit_app.py             # Multi-user calorie tracking dashboard
│   ├── setup.py                     # Automated setup script
│   ├── init_database.sql            # Database schema
│   ├── requirements.txt
│   ├── .env.example                 # SUPABASE_URL, SUPABASE_KEY
│   └── PROJECT_SUMMARY.md           # Detailed feature documentation
└── README.md                        # Project overview
```

## Development Commands

### Web Scraping
```bash
cd backend
python scraper.py  # Scrapes all 4 dining halls for all available dates
```

### AI Chatbot (Agentic Order Assistant)
```bash
# Terminal 1: Start mock orders API
cd backend
fastapi run orders_api.py --port 8001

# Terminal 2: Start chatbot API with Gemini agent
python chatbot_api.py  # Runs on port 8002

# Terminal 3: Launch Streamlit chat interface
streamlit run streamlit_app.py  # Port 8501
```

**Agent Tools Available:**
- `search_orders(status)` - Search/filter orders
- `get_order_details(order_id)` - Get specific order info
- `confirm_order(order_id)` - Confirm an order

### Calorie Tracker
```bash
cd calorie_tracker

# First-time setup (run SQL in Supabase, then load data)
python setup.py  # Loads JSON data + creates demo user

# Run dashboard
streamlit run streamlit_app.py  # Port 8501
```

**Dashboard Pages:**
1. User Dashboard - 7-day meal history, calorie tracking vs TDEE
2. Browse Foods - Filter by location/date/meal type
3. Add Food to Tracker - Search foods, add to meal entries
4. Manage Users - CRUD operations for user profiles
5. View All Food Items - Complete database listing

## Architecture Details

### Menu Scraping (scraper.py)
- Uses Playwright with Chromium headless browser
- Navigates to UMass dining URLs and scrapes date dropdown options
- For each date, selects option and extracts menu HTML
- Parses with BeautifulSoup to extract nutrition data (calories, fat, carbs, protein, sodium, fiber, sugars)
- Outputs to `all_dining_halls_menus.json` with structure:
  ```json
  {
    "DiningHall": [
      {
        "date": "...",
        "location": "...",
        "meals": {
          "Breakfast": {"category": [items...]},
          "Lunch": {...},
          "Dinner": {...}
        }
      }
    ]
  }
  ```

### AI Chatbot Architecture (chatbot_api.py + orders_api.py)
- **orders_api.py**: FastAPI mock database (port 8001) with 3 hardcoded orders
- **chatbot_api.py**: FastAPI server (port 8002) with PydanticAI Agent
  - Agent uses Gemini 2.5 Flash model
  - Decorated with `@agent.tool_plain` functions that call orders API
  - Agent autonomously decides which tools to use based on user message
  - POST `/chat` endpoint accepts message, returns agent response

### Calorie Tracking Architecture
**Data Models** (models.py):
- `User`: username, age, sex, height_cm, weight_kg, activity_level, bmr, tdee
  - Methods: `calculate_bmr()` (Mifflin-St Jeor), `calculate_tdee()`, `update_calculations()`
- `FoodItem`: name, serving_size, calories, fat, sodium, carbs, fiber, sugars, protein, location, date, meal_type
- `MealEntry`: user_id, food_item_id, entry_date, meal_category, servings (with joined food details)

**Database Layer** (database.py):
- Supabase client with connection pooling
- Three tables: `users`, `food_items`, `meal_entries`
- Foreign keys with CASCADE delete
- Indexes on `meal_entries(user_id, entry_date)` and `food_items(location, date)`
- Methods for CRUD operations, daily totals, 7-day history

**Data Loading** (data_loader.py):
- Parses `all_dining_halls_menus.json` from scraper
- Extracts numeric values from strings ("25.9g" → 25.9)
- Bulk inserts into Supabase with duplicate handling
- Provides utility functions: `get_available_dates()`, `get_available_locations()`

## Health Calculations

**BMR (Basal Metabolic Rate)** - Mifflin-St Jeor Equation:
- Men: `BMR = (10 × weight_kg) + (6.25 × height_cm) - (5 × age) + 5`
- Women: `BMR = (10 × weight_kg) + (6.25 × height_cm) - (5 × age) - 161`

**TDEE (Total Daily Energy Expenditure)** - BMR × Activity Multiplier:
- Sedentary: 1.2
- Light (1-3 days/week): 1.375
- Moderate (3-5 days/week): 1.55
- Active (6-7 days/week): 1.725
- Very Active (physical job): 1.9

## Database Setup

**First-time Supabase setup:**
1. Create Supabase project
2. Run `calorie_tracker/init_database.sql` in Supabase SQL Editor
3. Create `.env` files with credentials:
   - `backend/.env`: `GOOGLE_API_KEY=...`
   - `calorie_tracker/.env`: `SUPABASE_URL=...` and `SUPABASE_KEY=...`
4. Run `cd calorie_tracker && python setup.py` to populate database

## Environment Variables

**backend/.env:**
```
GOOGLE_API_KEY=your_google_api_key_here
```

**calorie_tracker/.env:**
```
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_service_role_key_here
```

## Important Implementation Notes

### When Working on Scraper:
- Always use `async_playwright` context manager
- Include `wait_until='networkidle'` for dynamic content
- Add small delays (`asyncio.sleep(1)`) between requests to avoid rate limiting
- Parse nutrition data carefully - values come as strings with units
- Use the date dropdown (`#upcoming-foodpro`) to navigate dates

### When Working on AI Agent:
- The agent must call external Orders API at `http://localhost:8001`
- Use `@agent.tool_plain` decorator for synchronous tools (not `@agent.tool`)
- System prompt is critical for agent behavior
- Agent runs asynchronously: `result = await agent.run(message)`
- Test with mock orders: ORD001 (Burger), ORD002 (Pizza), ORD003 (Salad)

### When Working on Calorie Tracker:
- Always call `user.update_calculations()` before saving to update BMR/TDEE
- Use `get_user_meals_for_date()` which returns dict grouped by meal category
- Servings default to 1.0 but can be fractional (0.5, 2.0, etc.)
- When adding food entries, use `entry_date` format: "YYYY-MM-DD"
- Food items have UNIQUE constraint on (name, location, date, meal_type)

### Streamlit Best Practices Used:
- Use `@st.cache_resource` for database connection (singleton pattern)
- Session state for user selections across pages
- `st.expander()` for collapsible 7-day history
- `st.metric()` for health stats display
- `st.progress()` for calorie/macro tracking bars

## Future Development

**Planned but not implemented:**
- Next.js frontend to replace Streamlit
- Real ordering system (currently just mock API)
- User authentication
- Meal planning and recommendations using AI
- Social features (sharing meals with friends)
- Mobile app

**Frontend Stack (when implemented):**
- Framework: Next.js with TypeScript
- State Management: React Context or Zustand
- Styling: TailwindCSS
- API calls: fetch/axios to FastAPI endpoints

## Testing

**Manual testing approach (no automated tests yet):**
1. Scraper: Run and verify JSON output structure
2. Chatbot: Use Streamlit chat UI to test agent responses
3. Calorie Tracker: Use dashboard to create users, add meals, view history

## Dependencies Management

Always install from requirements.txt in respective directories:
- `backend/requirements.txt` - Includes FastAPI, PydanticAI, Playwright, BeautifulSoup
- `calorie_tracker/requirements.txt` - Includes Streamlit, Supabase, Pandas

## Git Workflow

- Main branch: `main`
- License: MIT
- Keep `.env` files in `.gitignore`
- Never commit API keys or credentials
