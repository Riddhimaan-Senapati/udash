-- ========================================
-- Calorie Tracker Database Initialization
-- ========================================
-- Run this script in your Supabase SQL Editor
-- (Dashboard > SQL Editor > New Query)
-- ========================================

-- Drop existing tables if you want to start fresh (CAUTION: This will delete all data!)
-- Uncomment the lines below only if you want to reset everything
-- DROP TABLE IF EXISTS meal_entries CASCADE;
-- DROP TABLE IF EXISTS food_items CASCADE;
-- DROP TABLE IF EXISTS users CASCADE;

-- ========================================
-- Users Table
-- ========================================
CREATE TABLE IF NOT EXISTS users (
    id BIGSERIAL PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    age INTEGER NOT NULL CHECK (age >= 13 AND age <= 120),
    sex TEXT NOT NULL CHECK (sex IN ('M', 'F')),
    height_cm NUMERIC(5,2) NOT NULL CHECK (height_cm >= 100 AND height_cm <= 250),
    weight_kg NUMERIC(5,2) NOT NULL CHECK (weight_kg >= 30 AND weight_kg <= 300),
    activity_level TEXT NOT NULL CHECK (activity_level IN ('sedentary', 'light', 'moderate', 'active', 'very_active')),
    bmr NUMERIC(7,2),
    tdee NUMERIC(7,2),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ========================================
-- Food Items Table
-- ========================================
CREATE TABLE IF NOT EXISTS food_items (
    id BIGSERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    serving_size TEXT NOT NULL,
    calories INTEGER NOT NULL CHECK (calories >= 0),
    total_fat NUMERIC(6,2) NOT NULL CHECK (total_fat >= 0),
    sodium NUMERIC(7,2) NOT NULL CHECK (sodium >= 0),
    total_carb NUMERIC(6,2) NOT NULL CHECK (total_carb >= 0),
    dietary_fiber NUMERIC(6,2) NOT NULL CHECK (dietary_fiber >= 0),
    sugars NUMERIC(6,2) NOT NULL CHECK (sugars >= 0),
    protein NUMERIC(6,2) NOT NULL CHECK (protein >= 0),
    location TEXT,
    date TEXT,
    meal_type TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(name, location, date, meal_type)
);

-- ========================================
-- Meal Entries Table
-- ========================================
CREATE TABLE IF NOT EXISTS meal_entries (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    food_item_id BIGINT NOT NULL REFERENCES food_items(id) ON DELETE CASCADE,
    entry_date DATE NOT NULL,
    meal_category TEXT NOT NULL CHECK (meal_category IN ('Breakfast', 'Lunch', 'Dinner')),
    servings NUMERIC(4,2) DEFAULT 1.0 CHECK (servings > 0),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ========================================
-- Indexes for Performance
-- ========================================
CREATE INDEX IF NOT EXISTS idx_meal_entries_user_date ON meal_entries(user_id, entry_date DESC);
CREATE INDEX IF NOT EXISTS idx_meal_entries_user_id ON meal_entries(user_id);
CREATE INDEX IF NOT EXISTS idx_food_items_location_date ON food_items(location, date);
CREATE INDEX IF NOT EXISTS idx_food_items_name ON food_items(name);
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);

-- ========================================
-- Row Level Security (Optional but Recommended)
-- ========================================
-- Enable RLS on all tables
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE food_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE meal_entries ENABLE ROW LEVEL SECURITY;

-- Allow anonymous access for now (you can customize this later)
CREATE POLICY IF NOT EXISTS "Allow anonymous access to users"
    ON users FOR ALL
    TO anon
    USING (true)
    WITH CHECK (true);

CREATE POLICY IF NOT EXISTS "Allow anonymous access to food_items"
    ON food_items FOR ALL
    TO anon
    USING (true)
    WITH CHECK (true);

CREATE POLICY IF NOT EXISTS "Allow anonymous access to meal_entries"
    ON meal_entries FOR ALL
    TO anon
    USING (true)
    WITH CHECK (true);

-- ========================================
-- Verification Queries
-- ========================================
-- Run these to verify the tables were created successfully

-- Check if tables exist
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name IN ('users', 'food_items', 'meal_entries');

-- Check table structures
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'users'
ORDER BY ordinal_position;

SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'food_items'
ORDER BY ordinal_position;

SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'meal_entries'
ORDER BY ordinal_position;

-- ========================================
-- Success!
-- ========================================
-- If you see no errors above, your database is ready!
-- Next steps:
-- 1. Create a .env file with your Supabase credentials
-- 2. Run: python setup.py
-- 3. Run: streamlit run streamlit_app.py
-- ========================================
