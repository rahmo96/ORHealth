-- ORHealth migration 0001: users table + link daily_logs to users.
-- Run once in the Supabase SQL editor.

CREATE TABLE IF NOT EXISTS users (
    id                  bigserial PRIMARY KEY,
    display_name        text NOT NULL UNIQUE,
    daily_calorie_goal  integer NOT NULL CHECK (daily_calorie_goal > 0) DEFAULT 1800,
    pin_hash            text,                       -- NULL = not set yet
    created_at          timestamptz NOT NULL DEFAULT now()
);

INSERT INTO users (display_name, daily_calorie_goal) VALUES
    ('רחמים', 1800),
    ('אורלי', 1600)
ON CONFLICT (display_name) DO NOTHING;

ALTER TABLE daily_logs
    ADD COLUMN IF NOT EXISTS user_id bigint REFERENCES users(id);

UPDATE daily_logs dl
SET user_id = u.id
FROM users u
WHERE dl.user_id IS NULL AND dl.user_name = u.display_name;

CREATE INDEX IF NOT EXISTS idx_daily_logs_user_id_meal_date
    ON daily_logs (user_id, meal_date DESC);
