CREATE DATABASE IF NOT EXISTS agriweather_db;
USE agriweather_db;

CREATE TABLE IF NOT EXISTS regions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    province VARCHAR(100)
);

CREATE TABLE IF NOT EXISTS agriculture_data (
    id INT AUTO_INCREMENT PRIMARY KEY,
    region_id INT,
    year INT,
    rainfall FLOAT,
    temperature FLOAT,
    harvest_area FLOAT,
    production FLOAT,
    FOREIGN KEY (region_id) REFERENCES regions(id)
);

CREATE TABLE IF NOT EXISTS predictions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    region_id INT,
    year INT,
    predicted_production FLOAT,
    risk_level VARCHAR(20),
    recommendation TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (region_id) REFERENCES regions(id)
);

INSERT INTO regions (name, province) VALUES
('Bandung', 'Jawa Barat'),
('Garut', 'Jawa Barat')
ON DUPLICATE KEY UPDATE name = name;

INSERT INTO agriculture_data (region_id, year, rainfall, temperature, harvest_area, production) VALUES
(1, 2024, 2500, 27.5, 1200, 7200),
(2, 2024, 2800, 26.8, 1500, 9000);