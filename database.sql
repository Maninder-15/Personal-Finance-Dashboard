-- 1. Create the database
CREATE DATABASE IF NOT EXISTS finance_db;

-- 2. Use the database
USE finance_db;

-- 3. Create the transactions table
CREATE TABLE IF NOT EXISTS transactions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    trans_date DATE NOT NULL,
    description VARCHAR(255) NOT NULL,
    amount DECIMAL(10, 2) NOT NULL,
    type ENUM('Income', 'Expense') NOT NULL
);
