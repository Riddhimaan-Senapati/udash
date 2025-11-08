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
│   ├── orders_api.py                # Real orders API with Supabase (port 8001)
│   ├── streamlit_app.py             # Chat interface for testing chatbot
│   ├── all_dining_halls_menus.json  # Scraped menu data
│   ├── init_orders_db.sql           # Orders database schema
│   ├── requirements.txt
│   ├── .env                         # GOOGLE_API_KEY, SUPABASE_URL, SUPABASE_KEY
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

### Orders API (Real Supabase Backend)
```bash
cd backend
python orders_api.py  # Runs on port 8001
# Or use: uvicorn orders_api:app --host 0.0.0.0 --port 8001 --reload
```

**Available Endpoints:**
- `POST /orders` - Create new order with items
- `GET /orders` - List all orders (filter by user_id, status)
- `GET /orders/{order_id}` - Get order details with items
- `PATCH /orders/{order_id}` - Update order details
- `PATCH /orders/{order_id}/status` - Update order status
- `POST /orders/{order_id}/items` - Add item to order
- `DELETE /orders/{order_id}/items/{item_id}` - Remove item from order
- `DELETE /orders/{order_id}` - Cancel order
- `GET /users/{user_id}/orders` - Get user's orders
- `GET /docs` - Interactive API documentation

### AI Chatbot (Agentic Order Assistant v3.0.0)
```bash
# Terminal 1: Start chatbot API (no longer needs Orders API!)
cd backend
.venv/Scripts/python.exe chatbot_api.py  # Port 8002

# Terminal 2: Launch Streamlit chat interface
.venv/Scripts/streamlit run streamlit_app.py  # Port 8501

# Note: Orders API (port 8001) is optional - chatbot queries Supabase directly
```

**Agent Tools Available (v3.0.0):**
- `search_food_items(location, meal_type, search_term, date)` - Search Supabase food_items
  - Auto-uses current date if not specified
  - Example: "Show me breakfast at Worcester" → uses today's date
- `create_order(food_item_ids, quantities, delivery_location, delivery_time, special_instructions)` - Create order in Supabase
  - Validates food items exist
  - Calculates nutritional totals
  - Stores in orders + order_items tables
- `get_my_orders(status)` - View user's order history (pending or delivered)
- `get_order_details(order_id)` - Get full order details with nutrition info

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

### Orders API Architecture (orders_api.py)
- **FastAPI + Supabase**: Real order management system (port 8001)
- **Database Tables**:
  - `profiles`: User profiles (id UUID, email, full_name, created_at) - already exists
  - `orders`: Main orders table with delivery info, status, nutritional totals
  - `order_items`: Individual items in each order (references food_items table)
- **Order Status Flow**: pending → preparing → ready → out_for_delivery → delivered → completed
  - Can be cancelled at any stage
- **Auto-calculated Totals**: Uses DB function `calculate_order_totals()` to sum nutritional values
- **Pydantic Models**:
  - `OrderCreate`: Creates order with items list
  - `OrderResponse`: Full order with items and nutritional totals
  - `OrderItemCreate`: Add item to order (food_item_id, quantity)
  - `OrderStatusUpdate`: Update order status
- **Integration**: References existing `food_items` table from calorie_tracker for menu items

### AI Chatbot Architecture (chatbot_api.py v3.0.0)
- **chatbot_api.py**: FastAPI server (port 8002) with PydanticAI Agent + Supabase
  - Agent uses Gemini 2.5 Flash model (google-gla:gemini-2.5-flash)
  - **Direct Supabase Integration** - queries database directly (no Orders API dependency)
  - Uses `@agent.tool` decorator for async tools
  - Agent autonomously decides which tools to use based on user message
  - **Chat History**: Stores all conversations in `chat_history` table
  - **Context-Aware**: Retrieves last 10 messages for conversation context
  - **Current Date Aware**: Auto-uses today's date for food queries
  - POST `/chat` endpoint accepts message + user_id, returns agent response
  - GET `/history/{user_id}` - Retrieve chat history
  - DELETE `/history/{user_id}` - Clear chat history

  **Agent Tools:**
    - `search_food_items(location, meal_type, search_term, date)` - Query Supabase food_items directly
      - Auto-uses current date if date not specified
      - Returns up to 15 items with full nutrition data
    - `create_order(food_item_ids, quantities, delivery_location, delivery_time, special_instructions)`
      - Creates order directly in Supabase orders + order_items tables
      - Validates all food IDs exist
      - Calculates and stores nutritional totals
      - Requires delivery_location
    - `get_my_orders(status)` - Query user's orders from Supabase
    - `get_order_details(order_id)` - Get full order with items

  **System Prompt Features:**
    - Order schema awareness (knows required/optional fields)
    - Current date injection (today's date in system prompt)
    - Conversation context usage (references chat history)
    - Nutritional guidance (encourages healthy choices)

- **streamlit_app.py**: Simple chat interface for testing the agent
  - Connects to chatbot API at port 8002
  - User UUID input in sidebar (default: test user)
  - Displays conversation history with user/assistant messages
  - Shows setup instructions and example queries in sidebar
  - ✅ **Updated**: Now passes user_id to chatbot API

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
1. Create Supabase project (named "doorsmash")
2. Run SQL scripts in Supabase SQL Editor:
   - `calorie_tracker/init_database.sql` - Creates users, food_items, meal_entries tables
   - `backend/init_orders_db.sql` - Creates orders, order_items tables (uses existing profiles table)
3. Create `.env` files with credentials:
   - `backend/.env`: `GOOGLE_API_KEY=...`, `SUPABASE_URL=...`, `SUPABASE_KEY=...`
   - `calorie_tracker/.env`: `SUPABASE_URL=...`, `SUPABASE_KEY=...`
4. Run `cd calorie_tracker && python setup.py` to populate food items database

## Environment Variables

**backend/.env:**
```
GOOGLE_API_KEY=your_google_api_key_here
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_service_role_key_here
```

**calorie_tracker/.env:**
```
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_service_role_key_here
```

**Note:** Both backend and calorie_tracker use the same Supabase project ("doorsmash")

## Supabase Project Information

**Project Details:**
- **Project Name:** Doorsmash
- **Project ID:** btevtyamuxysdmenjsdi
- **Region:** us-east-1
- **Status:** ACTIVE_HEALTHY
- **Database:** PostgreSQL 17.6.1.038
- **Project URL:** https://btevtyamuxysdmenjsdi.supabase.co

**Database Tables:**
- `profiles` - User authentication profiles (managed by Supabase Auth)
- `users` - User health data for calorie tracking
- `food_items` - Menu items from dining halls (740 items, loaded from scraper)
- `meal_entries` - User meal tracking entries
- `orders` - Food delivery orders with nutritional totals
- `order_items` - Individual items in each order with denormalized nutrition data
- `chat_history` - AI chatbot conversation history for all users

**MCP Server Access:**
- Use `mcp__supabase__*` tools to interact with the database
- Use `mcp__context7__*` tools to fetch documentation for libraries

## Important Implementation Notes

### When Working on Scraper:
- Always use `async_playwright` context manager
- Include `wait_until='networkidle'` for dynamic content
- Add small delays (`asyncio.sleep(1)`) between requests to avoid rate limiting
- Parse nutrition data carefully - values come as strings with units
- Use the date dropdown (`#upcoming-foodpro`) to navigate dates

### When Working on Orders API:
- Order IDs are UUIDs (strings), not integers
- Always validate that `food_item_id` exists in `food_items` table before creating order items
- Use `calculate_and_update_order_totals()` after adding/removing items to recalculate nutritional totals
- **Order statuses (simplified for MVP):** `pending` (default) or `delivered`
  - Full schema supports: pending, preparing, ready, out_for_delivery, delivered, completed, cancelled
- `user_id` must reference an existing profile in the `profiles` table (UUID format)
- Nutritional data is denormalized in `order_items` (snapshot at time of order) to preserve historical accuracy
- CORS is enabled for frontend integration - update `allow_origins` in production
- Use FastAPI's auto-generated docs at `/docs` for interactive API testing

**Required Order Fields:**
- `user_id` (UUID) - References profiles table
- `delivery_location` (text, REQUIRED) - Where to deliver (e.g., "Southwest Dorms", "Baker Hall Room 420")
- `delivery_time` (timestamptz, OPTIONAL) - When to deliver
- `special_instructions` (text, OPTIONAL) - Dietary restrictions, allergies, preferences
- Auto-calculated: `total_calories`, `total_protein`, `total_carbs`, `total_fat`

### When Working on AI Agent:
- **Direct Supabase Integration**: Agent now queries Supabase directly (no longer calls Orders API)
- Use `@agent.tool` decorator for async tools that query Supabase
- System prompt is critical for agent behavior - includes order schema details and current date
- Agent runs asynchronously: `result = await agent.run(message, deps=deps)`
- **Chat History**: All conversations stored in `chat_history` table for context
- **Current Date Handling**: Automatically uses today's date for food queries (format: "Fri November 08, 2025")
- **Date Format**: Food items use format "Fri November 08, 2025" in database

**Agent Tools (v3.0.0):**
1. `search_food_items(location, meal_type, search_term, date)` - Query Supabase food_items
   - Auto-uses current date if not specified
   - Returns items with ID, name, location, meal_type, and full nutrition info
2. `create_order(food_item_ids, quantities, delivery_location, delivery_time, special_instructions)`
   - Creates order directly in Supabase
   - Validates all food IDs exist
   - Calculates nutritional totals
   - Requires delivery_location
3. `get_my_orders(status)` - Query user's orders from Supabase
4. `get_order_details(order_id)` - Get full order with items

**Additional Endpoints:**
- `GET /history/{user_id}` - Retrieve chat history
- `DELETE /history/{user_id}` - Clear chat history

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
- User authentication (profiles table exists, need auth flow)
- Payment processing and pricing
- Meal planning and recommendations using AI
- Social features (sharing meals with friends)
- Mobile app
- Real-time order tracking (WebSocket integration)
- Driver assignment and delivery routing

**Frontend Stack (when implemented):**
- Framework: Next.js with TypeScript
- State Management: React Context or Zustand
- Styling: TailwindCSS
- API calls: fetch/axios to FastAPI endpoints

## Testing

**Manual testing approach (no automated tests yet):**
1. Scraper: Run and verify JSON output structure
2. Orders API: Use FastAPI auto-docs at `http://localhost:8001/docs` to test endpoints
3. Chatbot: Use Streamlit chat UI to test agent responses
4. Calorie Tracker: Use dashboard to create users, add meals, view history

**Testing Orders API:**
```bash
# Start the API
cd backend
python orders_api.py

# Open browser to http://localhost:8001/docs
# Use interactive Swagger UI to test all endpoints
```

## Dependencies Management

**Using Virtual Environment (.venv):**
- The project uses `.venv` for virtual environment management
- Install packages using: `.venv/Scripts/python.exe -m pip install <package>`
- Or use uv: `uv pip install <package>`
- Run Python scripts: `.venv/Scripts/python.exe script.py`

**Requirements files:**
- `backend/requirements.txt` - Includes FastAPI, PydanticAI, Supabase, Playwright, BeautifulSoup
- `calorie_tracker/requirements.txt` - Includes Streamlit, Supabase, Pandas

## Complete Application Testing Guide

### Prerequisites
Before testing, ensure:
1. ✅ Supabase project "Doorsmash" is active (btevtyamuxysdmenjsdi)
2. ✅ Database tables created (`init_database.sql` + `init_orders_db.sql`)
3. ✅ Food items loaded from scraper (`python calorie_tracker/setup.py`)
4. ✅ `.env` files configured with GOOGLE_API_KEY, SUPABASE_URL, SUPABASE_KEY
5. ✅ Test user exists in `profiles` table

### Testing the Full Application Stack

**Step 1: Start Required Services (2 Terminals)**

Terminal 1 - Chatbot API (v3.0.0 - Direct Supabase):
```bash
cd backend
.venv/Scripts/python.exe chatbot_api.py
# Should show: "Uvicorn running on http://0.0.0.0:8002"
# Test: Open http://localhost:8002 (should show version 3.0.0)
```

Terminal 2 - Streamlit Chat Interface:
```bash
cd backend
.venv/Scripts/streamlit run streamlit_app.py
# Should show: "Local URL: http://localhost:8501"
# Opens browser automatically to Streamlit app
```

**Optional - Start Orders API (for REST API testing):**
```bash
cd backend
.venv/Scripts/python.exe orders_api.py
# Port 8001 - Not required for chatbot, but useful for direct API testing
# Test: Open http://localhost:8001/docs
```

**Step 2: Test End-to-End with Streamlit Chat**

Once both services are running:

1. **Open Streamlit app** at http://localhost:8501
2. **Verify user_id** in sidebar (default: `10fccccb-4f6c-4a8f-954f-1d88aafeaa37`)
3. **Try example queries:**
   - "Show me breakfast items today" ← Uses current date automatically!
   - "What's available at Worcester for lunch?"
   - "Show me high protein foods"
   - "Create an order with French Toast Sticks, deliver to Southwest Dorms"
   - "Show me my orders"
   - "What's in my latest order?"
   - "Show me pending orders"

**What's New in v3.0.0:**
- Chat history is automatically saved and used for context
- No need to specify date - agent uses today's date by default
- Direct Supabase queries (faster, no Orders API dependency)
- Agent remembers previous conversation context

**Step 3: Test Individual Components**

**Test Orders API directly:**
```bash
# In a new terminal
cd backend
.venv/Scripts/python.exe test_api.py
# Runs comprehensive test suite for all 10 endpoints

# Or use browser: http://localhost:8001/docs
# Interactive Swagger UI to test endpoints manually
```

**Test Chatbot API with curl:**
```bash
# Search for breakfast items (uses today's date automatically)
curl -X POST http://localhost:8002/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Show me breakfast items at Worcester", "user_id": "10fccccb-4f6c-4a8f-954f-1d88aafeaa37"}'

# Create an order
curl -X POST http://localhost:8002/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Order French Toast Sticks, deliver to Baker Hall", "user_id": "10fccccb-4f6c-4a8f-954f-1d88aafeaa37"}'

# Get user orders
curl -X POST http://localhost:8002/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Show me my orders", "user_id": "10fccccb-4f6c-4a8f-954f-1d88aafeaa37"}'

# Get chat history
curl http://localhost:8002/history/10fccccb-4f6c-4a8f-954f-1d88aafeaa37

# Clear chat history
curl -X DELETE http://localhost:8002/history/10fccccb-4f6c-4a8f-954f-1d88aafeaa37
```

**Test Calorie Tracker separately:**
```bash
cd calorie_tracker
.venv/Scripts/streamlit run streamlit_app.py
# Opens multi-page dashboard at http://localhost:8501
# Test: Add users, browse foods, track meals
```

### What's New in v3.0.0

**✅ Chatbot API v3.0.0 Updates:**
- **Chat History**: All conversations stored in `chat_history` table
  - Automatically saves user + assistant messages
  - Retrieves last 10 messages for context
  - New endpoints: GET/DELETE `/history/{user_id}`
- **Direct Supabase Integration**: No longer depends on Orders API
  - Queries `food_items` table directly
  - Creates orders in `orders` + `order_items` tables directly
  - Faster performance, fewer dependencies
- **Current Date Awareness**: Auto-uses today's date for food queries
  - Format: "Fri November 08, 2025" (matches food_items.date format)
  - Users don't need to specify date for "today"
- **Improved System Prompt**: Includes order schema details and current date
- **Better Error Handling**: Validates food IDs, delivery location requirements

**✅ Streamlit App Updated:**
- Now passes `user_id` to chatbot API ✓
- User UUID input in sidebar (default: test user) ✓
- Better example queries ✓

**✅ Database Updates:**
- New table: `chat_history` (id, user_id, role, message, created_at)
- Index on `chat_history(user_id, created_at)` for fast queries

**Test User Accounts:**
- UUID: `10fccccb-4f6c-4a8f-954f-1d88aafeaa37`
- Email: `nkotturu@umass.edu`
- Make sure this user exists in `profiles` table

**Database Notes:**
- The `profiles` table has Row Level Security (RLS) - use service_role key for admin operations
- Food items must exist in `food_items` table (run `calorie_tracker/setup.py` to load)
- Chat history uses same Supabase connection as orders

### Testing Checklist

**Chatbot v3.0.0:**
- [ ] Chatbot API responds at http://localhost:8002 with version 3.0.0
- [ ] Streamlit app loads at http://localhost:8501 with user_id input
- [ ] Can browse food items via chat ("show me breakfast items today")
- [ ] Food queries use current date automatically
- [ ] Can create orders via chat with delivery location
- [ ] Orders appear in Supabase `orders` table with correct nutritional totals
- [ ] Chat history is saved to `chat_history` table
- [ ] Agent remembers previous conversation context
- [ ] Can view order history ("show me my orders")
- [ ] Can get order details by ID
- [ ] GET `/history/{user_id}` returns chat history
- [ ] DELETE `/history/{user_id}` clears chat history

**Optional - Orders API:**
- [ ] Orders API responds at http://localhost:8001 (if running)
- [ ] Can create orders via REST API
- [ ] Order status updates work

**Calorie Tracker:**
- [ ] Calorie tracker dashboard loads
- [ ] Can add meals to tracker

### Debugging Tips

**If Orders API fails:**
- Check Supabase connection: run `backend/debug_supabase.py`
- Verify tables exist: use Supabase MCP tools or SQL Editor
- Check `.env` has SUPABASE_URL and SUPABASE_KEY

**If Chatbot API fails:**
- Check GOOGLE_API_KEY is set in `backend/.env`
- Check SUPABASE_URL and SUPABASE_KEY are set in `backend/.env`
- Verify Supabase connection: test with `mcp__supabase__execute_sql`
- Check that `food_items` table has data (740 items)
- Check that `chat_history` table exists
- Verify user_id exists in `profiles` table
- Check logs for tool execution errors

**If Streamlit chat fails:**
- Ensure both APIs are running first
- Check console for connection errors
- Add user_id parameter (see "Known Issues")

**Use MCP Tools for Debugging:**
```bash
# List all tables
mcp__supabase__list_tables(project_id="btevtyamuxysdmenjsdi")

# Execute SQL to check data
mcp__supabase__execute_sql(
    project_id="btevtyamuxysdmenjsdi",
    query="SELECT COUNT(*) FROM food_items"
)

# Get API logs
mcp__supabase__get_logs(
    project_id="btevtyamuxysdmenjsdi",
    service="api"
)
```

## Git Workflow

- Main branch: `main`
- License: MIT
- Keep `.env` files in `.gitignore`
- Never commit API keys or credentials
