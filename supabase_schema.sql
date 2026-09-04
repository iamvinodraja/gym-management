-- =========================================================
-- Supabase PostgreSQL Schema & Seed
-- Pakistani Gym Management System
-- =========================================================

-- Enable UUID extension if needed
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. Users Table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(100) NOT NULL,
    role VARCHAR(20) NOT NULL DEFAULT 'receptionist',
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 2. Trainers Table
CREATE TABLE IF NOT EXISTS trainers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    phone VARCHAR(20) NOT NULL,
    specialization VARCHAR(100) DEFAULT 'General Fitness',
    salary NUMERIC(10,2) DEFAULT 0.00,
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 3. Staff Table
CREATE TABLE IF NOT EXISTS staff (
    id SERIAL PRIMARY KEY,
    staff_id VARCHAR(20) NOT NULL UNIQUE,
    name VARCHAR(100) NOT NULL,
    phone VARCHAR(20) NOT NULL,
    cnic VARCHAR(20) NULL,
    role VARCHAR(50) NOT NULL,
    salary NUMERIC(10,2) DEFAULT 0.00,
    joining_date DATE NOT NULL,
    status VARCHAR(20) DEFAULT 'Active',
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 4. Membership Plans Table
CREATE TABLE IF NOT EXISTS membership_plans (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    duration_days INT NOT NULL,
    price NUMERIC(10,2) NOT NULL,
    description TEXT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 5. Members Table
CREATE TABLE IF NOT EXISTS members (
    id SERIAL PRIMARY KEY,
    member_id VARCHAR(20) NOT NULL UNIQUE,
    full_name VARCHAR(100) NOT NULL,
    father_name VARCHAR(100) NULL,
    cnic VARCHAR(20) NULL,
    phone VARCHAR(20) NOT NULL,
    emergency_contact VARCHAR(20) NULL,
    gender VARCHAR(10) DEFAULT 'Male',
    dob DATE NULL,
    address TEXT NULL,
    join_date DATE NOT NULL,
    photo_url VARCHAR(255) NULL,
    notes TEXT NULL,
    trainer_id INT NULL REFERENCES trainers(id) ON DELETE SET NULL,
    current_plan_id INT NULL REFERENCES membership_plans(id) ON DELETE SET NULL,
    start_date DATE NULL,
    expiry_date DATE NULL,
    monthly_fee NUMERIC(10,2) NOT NULL DEFAULT 0.00,
    discount NUMERIC(10,2) DEFAULT 0.00,
    outstanding_amount NUMERIC(10,2) NOT NULL DEFAULT 0.00,
    status VARCHAR(20) DEFAULT 'Active',
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes on members
CREATE INDEX IF NOT EXISTS idx_members_phone ON members(phone);
CREATE INDEX IF NOT EXISTS idx_members_code ON members(member_id);
CREATE INDEX IF NOT EXISTS idx_members_expiry ON members(expiry_date);

-- 6. Memberships History Table
CREATE TABLE IF NOT EXISTS memberships (
    id SERIAL PRIMARY KEY,
    member_id INT NOT NULL REFERENCES members(id) ON DELETE CASCADE,
    plan_id INT NULL REFERENCES membership_plans(id) ON DELETE SET NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    fee NUMERIC(10,2) NOT NULL,
    discount NUMERIC(10,2) DEFAULT 0.00,
    amount_paid NUMERIC(10,2) NOT NULL DEFAULT 0.00,
    remaining_balance NUMERIC(10,2) NOT NULL DEFAULT 0.00,
    notes VARCHAR(255) NULL,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 7. Payments Table
CREATE TABLE IF NOT EXISTS payments (
    id SERIAL PRIMARY KEY,
    payment_id VARCHAR(30) NOT NULL UNIQUE,
    member_id INT NOT NULL REFERENCES members(id) ON DELETE CASCADE,
    amount NUMERIC(10,2) NOT NULL,
    discount NUMERIC(10,2) DEFAULT 0.00,
    payment_date DATE NOT NULL,
    payment_method VARCHAR(30) NOT NULL DEFAULT 'Cash',
    description VARCHAR(255) NULL,
    received_by VARCHAR(100) NOT NULL DEFAULT 'Reception',
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 8. Attendance Table
CREATE TABLE IF NOT EXISTS attendance (
    id SERIAL PRIMARY KEY,
    member_id INT NOT NULL REFERENCES members(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    check_in_time TIME NOT NULL,
    check_out_time TIME NULL,
    status VARCHAR(20) DEFAULT 'Checked In',
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 9. Expenses Table
CREATE TABLE IF NOT EXISTS expenses (
    id SERIAL PRIMARY KEY,
    category VARCHAR(50) NOT NULL,
    amount NUMERIC(10,2) NOT NULL,
    date DATE NOT NULL,
    description TEXT NULL,
    paid_by VARCHAR(100) NULL,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 10. Activity Logs Table
CREATE TABLE IF NOT EXISTS activity_logs (
    id SERIAL PRIMARY KEY,
    action VARCHAR(50) NOT NULL,
    description TEXT NOT NULL,
    performed_by VARCHAR(100) NOT NULL DEFAULT 'System',
    timestamp TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 11. Gym Settings Table
CREATE TABLE IF NOT EXISTS gym_settings (
    id SERIAL PRIMARY KEY,
    key_name VARCHAR(50) NOT NULL UNIQUE,
    key_value TEXT NOT NULL,
    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- =========================================================
-- Initial Seed Data for Supabase
-- =========================================================

INSERT INTO gym_settings (key_name, key_value) VALUES
('gym_name', 'Power Fitness Gym'),
('gym_address', 'Plot 14-C, Main Boulevard, Gulberg III, Lahore, Pakistan'),
('gym_phone', '0300-1234567'),
('currency_symbol', 'Rs.'),
('currency_code', 'PKR'),
('default_fee', '2500'),
('warning_days', '7'),
('receipt_footer', 'Thank you for choosing Power Fitness Gym! Fee once paid is non-refundable.')
ON CONFLICT (key_name) DO NOTHING;

INSERT INTO membership_plans (name, duration_days, price, description, is_active) VALUES
('Monthly Regular', 30, 2500.00, 'Full cardio & weight room access for 1 month', TRUE),
('3 Months Saver', 90, 6500.00, 'Save Rs. 1,000 on quarterly membership', TRUE),
('6 Months Pro', 180, 11000.00, 'Save Rs. 4,000 on half-yearly package', TRUE),
('Yearly Elite', 365, 18000.00, 'Best value! 12 months full facility access', TRUE),
('Admission / Registration', 0, 1000.00, 'One-time registration fee for new joiners', TRUE)
ON CONFLICT DO NOTHING;
