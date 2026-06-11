CREATE DATABASE IF NOT EXISTS agriweather_db;
USE agriweather_db;

CREATE TABLE IF NOT EXISTS regions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    province VARCHAR(100),
    latitude FLOAT,
    longitude FLOAT
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

INSERT INTO regions (id, name, province, latitude, longitude) VALUES
(1, 'Bandung', 'Jawa Barat', -6.9175, 107.6191),
(2, 'Garut', 'Jawa Barat', -7.2157, 107.9010)
ON DUPLICATE KEY UPDATE
name = VALUES(name),
province = VALUES(province),
latitude = VALUES(latitude),
longitude = VALUES(longitude);

INSERT INTO agriculture_data (region_id, year, rainfall, temperature, harvest_area, production) VALUES
(1, 2024, 2500, 27.5, 1200, 7200),
(2, 2024, 2800, 26.8, 1500, 9000);