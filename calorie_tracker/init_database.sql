-- ========================================
-- Calorie Tracker Database Initialization
-- ========================================
-- Run this script in your Supabase SQL Editor
-- (Dashboard > SQL Editor > New Query)
-- ========================================
-- IMPORTANT: This assumes you already have a 'profiles' table for authentication
-- The 'users' table stores additional user details and references profiles
-- ========================================

-- Drop existing tables to start fresh (REQUIRED to fix UUID -> BIGSERIAL)
-- This will delete all existing data!
DROP TABLE IF EXISTS meal_entries CASCADE;
DROP TABLE IF EXISTS food_items CASCADE;
DROP TABLE IF EXISTS users CASCADE;

-- ========================================
-- Users Table (references profiles table)
-- ========================================
CREATE TABLE users (
    id BIGSERIAL PRIMARY KEY,
    profile_id UUID REFERENCES profiles(id) ON DELETE CASCADE,
    username TEXT UNIQUE NOT NULL,
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
CREATE TABLE food_items (
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
CREATE TABLE meal_entries (
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
CREATE INDEX IF NOT EXISTS idx_meal_entries_profile_date ON meal_entries(profile_id, entry_date DESC);
CREATE INDEX IF NOT EXISTS idx_meal_entries_profile_id ON meal_entries(profile_id);
CREATE INDEX IF NOT EXISTS idx_food_items_location_date ON food_items(location, date);
CREATE INDEX IF NOT EXISTS idx_food_items_name ON food_items(name);
CREATE INDEX IF NOT EXISTS idx_profiles_email ON profiles(email);

-- ========================================
-- Row Level Security (Optional but Recommended)
-- ========================================
-- Enable RLS on tables (profiles RLS is already managed by Supabase Auth)
ALTER TABLE food_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE meal_entries ENABLE ROW LEVEL SECURITY;

-- Drop existing policies if they exist (to allow re-running this script)
DROP POLICY IF EXISTS "Allow anonymous access to food_items" ON food_items;
DROP POLICY IF EXISTS "Allow anonymous access to meal_entries" ON meal_entries;

-- Allow anonymous access for now (you can customize this later)
CREATE POLICY "Allow anonymous access to food_items"
    ON food_items FOR ALL
    TO anon
    USING (true)
    WITH CHECK (true);

CREATE POLICY "Allow anonymous access to meal_entries"
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
AND table_name IN ('profiles', 'food_items', 'meal_entries');

-- Check profiles table structure
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'profiles'
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
