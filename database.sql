-- =========================================================
-- Pakistani Gym Management System - Database Schema & Seed
-- Target: MySQL 5.7+ / 8.0+
-- Collation: utf8mb4_unicode_ci
-- Currency: PKR (Pakistani Rupee - Rs.)
-- =========================================================

CREATE DATABASE IF NOT EXISTS gym_management CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE gym_management;

-- 1. Users & Authentication Table
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(100) NOT NULL,
    role ENUM('admin', 'receptionist') NOT NULL DEFAULT 'receptionist',
    status ENUM('active', 'inactive') NOT NULL DEFAULT 'active',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 2. Trainers Table
CREATE TABLE IF NOT EXISTS trainers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    phone VARCHAR(20) NOT NULL,
    specialization VARCHAR(100) DEFAULT 'General Fitness',
    salary DECIMAL(10,2) DEFAULT 0.00,
    status ENUM('active', 'inactive') NOT NULL DEFAULT 'active',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 3. Staff Management Table
CREATE TABLE IF NOT EXISTS staff (
    id INT AUTO_INCREMENT PRIMARY KEY,
    staff_id VARCHAR(20) NOT NULL UNIQUE,
    name VARCHAR(100) NOT NULL,
    phone VARCHAR(20) NOT NULL,
    cnic VARCHAR(20) NULL,
    role ENUM('Owner', 'Manager', 'Receptionist', 'Trainer') NOT NULL,
    salary DECIMAL(10,2) DEFAULT 0.00,
    joining_date DATE NOT NULL,
    status ENUM('Active', 'Inactive') NOT NULL DEFAULT 'Active',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 4. Membership Plans Table
CREATE TABLE IF NOT EXISTS membership_plans (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    duration_days INT NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    description TEXT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 5. Members Table
CREATE TABLE IF NOT EXISTS members (
    id INT AUTO_INCREMENT PRIMARY KEY,
    member_id VARCHAR(20) NOT NULL UNIQUE,
    full_name VARCHAR(100) NOT NULL,
    father_name VARCHAR(100) NULL,
    cnic VARCHAR(20) NULL,
    phone VARCHAR(20) NOT NULL,
    emergency_contact VARCHAR(20) NULL,
    gender ENUM('Male', 'Female', 'Other') DEFAULT 'Male',
    dob DATE NULL,
    address TEXT NULL,
    join_date DATE NOT NULL,
    photo_url VARCHAR(255) NULL,
    notes TEXT NULL,
    trainer_id INT NULL,
    current_plan_id INT NULL,
    start_date DATE NULL,
    expiry_date DATE NULL,
    monthly_fee DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    discount DECIMAL(10,2) DEFAULT 0.00,
    outstanding_amount DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    status ENUM('Active', 'Expiring Soon', 'Expired', 'Inactive') DEFAULT 'Active',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (trainer_id) REFERENCES trainers(id) ON DELETE SET NULL,
    FOREIGN KEY (current_plan_id) REFERENCES membership_plans(id) ON DELETE SET NULL,
    INDEX idx_phone (phone),
    INDEX idx_member_id (member_id),
    INDEX idx_cnic (cnic),
    INDEX idx_expiry (expiry_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 6. Memberships History Table (Keeps complete renewal history)
CREATE TABLE IF NOT EXISTS memberships (
    id INT AUTO_INCREMENT PRIMARY KEY,
    member_id INT NOT NULL,
    plan_id INT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    fee DECIMAL(10,2) NOT NULL,
    discount DECIMAL(10,2) DEFAULT 0.00,
    amount_paid DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    remaining_balance DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    notes VARCHAR(255) NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (member_id) REFERENCES members(id) ON DELETE CASCADE,
    FOREIGN KEY (plan_id) REFERENCES membership_plans(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 7. Fee & Payments Table
CREATE TABLE IF NOT EXISTS payments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    payment_id VARCHAR(30) NOT NULL UNIQUE,
    member_id INT NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    discount DECIMAL(10,2) DEFAULT 0.00,
    payment_date DATE NOT NULL,
    payment_method ENUM('Cash', 'Bank Transfer', 'Easypaisa', 'JazzCash', 'Other') NOT NULL DEFAULT 'Cash',
    description VARCHAR(255) NULL,
    received_by VARCHAR(100) NOT NULL DEFAULT 'Reception',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (member_id) REFERENCES members(id) ON DELETE CASCADE,
    INDEX idx_payment_date (payment_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 8. Attendance Table
CREATE TABLE IF NOT EXISTS attendance (
    id INT AUTO_INCREMENT PRIMARY KEY,
    member_id INT NOT NULL,
    date DATE NOT NULL,
    check_in_time TIME NOT NULL,
    check_out_time TIME NULL,
    status ENUM('Checked In', 'Checked Out') DEFAULT 'Checked In',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (member_id) REFERENCES members(id) ON DELETE CASCADE,
    INDEX idx_member_date (member_id, date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 9. Expenses Table
CREATE TABLE IF NOT EXISTS expenses (
    id INT AUTO_INCREMENT PRIMARY KEY,
    category VARCHAR(50) NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    date DATE NOT NULL,
    description TEXT NULL,
    paid_by VARCHAR(100) NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 10. Activity Logs Table
CREATE TABLE IF NOT EXISTS activity_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    action VARCHAR(50) NOT NULL,
    description TEXT NOT NULL,
    performed_by VARCHAR(100) NOT NULL DEFAULT 'System',
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 11. Gym Settings Table
CREATE TABLE IF NOT EXISTS gym_settings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    key_name VARCHAR(50) NOT NULL UNIQUE,
    key_value TEXT NOT NULL,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- =========================================================
-- SEED DATA (Pakistani Localization)
-- =========================================================

-- Gym Settings
INSERT INTO gym_settings (key_name, key_value) VALUES
('gym_name', 'Power Fitness Gym'),
('gym_address', 'Plot 14-C, Main Boulevard, Gulberg III, Lahore, Pakistan'),
('gym_phone', '0300-1234567'),
('currency_symbol', 'Rs.'),
('currency_code', 'PKR'),
('default_fee', '2500'),
('warning_days', '7'),
('receipt_footer', 'Thank you for choosing Power Fitness Gym! Fee once paid is non-refundable. Please carry your workout towel and clean shoes.')
ON DUPLICATE KEY UPDATE key_value=VALUES(key_value);

-- Users (Default logins: admin / admin123, reception / rec123)
-- PBKDF2-SHA256 hashed passwords
INSERT INTO users (username, password_hash, full_name, role, status) VALUES
('admin', 'pbkdf2:sha256:100000$saltsalt$8444f6f4d22165c5896a603c40fa97607730e7df6504620023a1050a417616ba', 'Malik Tariq (Owner)', 'admin', 'active'),
('reception', 'pbkdf2:sha256:100000$saltsalt$75429ca5eec6f1ec01c70e34c9c2ff1d9551fe66ca2bc5103a8909ba249fef56', 'Asad Ali (Front Desk)', 'receptionist', 'active')
ON DUPLICATE KEY UPDATE username=username;

-- Membership Plans
INSERT INTO membership_plans (name, duration_days, price, description, is_active) VALUES
('Monthly Regular', 30, 2500.00, 'Full cardio & weight room access for 1 month', TRUE),
('3 Months Saver', 90, 6500.00, 'Save Rs. 1,000 on quarterly membership', TRUE),
('6 Months Pro', 180, 11000.00, 'Save Rs. 4,000 on half-yearly package', TRUE),
('Yearly Elite', 365, 18000.00, 'Best value! 12 months full facility access', TRUE),
('Admission / Registration', 0, 1000.00, 'One-time registration fee for new joiners', TRUE)
ON DUPLICATE KEY UPDATE name=name;

-- Trainers
INSERT INTO trainers (name, phone, specialization, salary, status) VALUES
('Ahmed Khan', '0321-4567890', 'Bodybuilding & Heavy Lifting', 45000.00, 'active'),
('Zubair Butt', '0333-7654321', 'Weight Loss & HIIT Cardio', 40000.00, 'active'),
('Shahid Afridi', '0312-9876543', 'Crossfit & Strength Conditioning', 42000.00, 'active')
ON DUPLICATE KEY UPDATE name=name;

-- Staff
INSERT INTO staff (staff_id, name, phone, cnic, role, salary, joining_date, status) VALUES
('STF-01', 'Malik Tariq', '0300-1112233', '35201-1234567-1', 'Owner', 0.00, '2023-01-01', 'Active'),
('STF-02', 'Hamza Qureshi', '0302-2223344', '35201-2345678-3', 'Manager', 55000.00, '2023-03-15', 'Active'),
('STF-03', 'Asad Ali', '0304-3334455', '35202-3456789-5', 'Receptionist', 30000.00, '2024-01-10', 'Active'),
('STF-04', 'Ahmed Khan', '0321-4567890', '35202-4567890-7', 'Trainer', 45000.00, '2023-06-01', 'Active')
ON DUPLICATE KEY UPDATE staff_id=staff_id;
