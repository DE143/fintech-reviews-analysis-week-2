-- Database schema for bank reviews analysis

CREATE DATABASE bank_reviews;

\c bank_reviews;

-- Banks table
CREATE TABLE banks (
    bank_id SERIAL PRIMARY KEY,
    bank_name VARCHAR(100) NOT NULL,
    app_name VARCHAR(100) NOT NULL,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Reviews table
CREATE TABLE reviews (
    review_id VARCHAR(100) PRIMARY KEY,
    bank_id INTEGER REFERENCES banks(bank_id),
    review_text TEXT,
    cleaned_text TEXT,
    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
    review_date DATE,
    sentiment_label VARCHAR(20),
    sentiment_score FLOAT,
    theme VARCHAR(50),
    keywords TEXT,
    source VARCHAR(50),
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for better performance
CREATE INDEX idx_reviews_bank_id ON reviews(bank_id);
CREATE INDEX idx_reviews_rating ON reviews(rating);
CREATE INDEX idx_reviews_sentiment ON reviews(sentiment_label);
CREATE INDEX idx_reviews_date ON reviews(review_date);

-- Sample data for banks
INSERT INTO banks (bank_id, bank_name, app_name) VALUES
(1, 'Commercial Bank of Ethiopia', 'CBE Mobile'),
(2, 'Bank of Abyssinia', 'BOA Mobile Banking'),
(3, 'Dashen Bank', 'Dashen Bank Mobile');