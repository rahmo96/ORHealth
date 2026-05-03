-- ORHealth: catalog table foods_master (matches app FoodItem + repository INSERT).
-- Table name in DB is foods_master (plural). Run in Supabase SQL editor if missing.

CREATE TABLE IF NOT EXISTS foods_master (
    food_name         text        NOT NULL,
    default_calories  integer     NOT NULL CHECK (default_calories > 0 AND default_calories <= 10000),
    PRIMARY KEY (food_name)
);
