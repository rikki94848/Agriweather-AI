CREATE TABLE regions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    province VARCHAR(100)
);

CREATE TABLE agriculture_data (
    id INT AUTO_INCREMENT PRIMARY KEY,
    region_id INT,
    year INT,
    rainfall FLOAT,
    temperature FLOAT,
    harvest_area FLOAT,
    production FLOAT
);

CREATE TABLE predictions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    region_id INT,
    year INT,
    predicted_production FLOAT,
    risk_level VARCHAR(20),
    recommendation TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);