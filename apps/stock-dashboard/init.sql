-- Initialize stock_prices table and indexes
-- This file runs automatically when PostgreSQL container starts

-- Create the main OHLCV table
CREATE TABLE IF NOT EXISTS stock_prices (
    time TIMESTAMPTZ NOT NULL,
    ticker TEXT NOT NULL,
    open FLOAT,
    high FLOAT,
    low FLOAT,
    close FLOAT,
    volume BIGINT,
    PRIMARY KEY (time, ticker)
);

-- Create composite index for fast queries
CREATE INDEX IF NOT EXISTS idx_stock_prices_ticker_time 
    ON stock_prices (ticker, time DESC);

-- Create index for ticker-only queries
CREATE INDEX IF NOT EXISTS idx_stock_prices_ticker 
    ON stock_prices (ticker);

-- Grant privileges to postgres user
GRANT ALL PRIVILEGES ON TABLE stock_prices TO postgres;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO postgres;

-- Log initialization
SELECT 'Stock prices table initialized successfully' as status;
