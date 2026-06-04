CREATE TABLE regions (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    province VARCHAR(100)
);

CREATE TABLE agriculture_data (
    id SERIAL PRIMARY KEY,
    region_id INT,
    year INT,
    rainfall FLOAT,
    temperature FLOAT,
    harvest_area FLOAT,
    production FLOAT
);

CREATE TABLE predictions (
    id SERIAL PRIMARY KEY,
    region_id INT,
    year INT,
    predicted_production FLOAT,
    risk_level VARCHAR(20),
    recommendation TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
