# backend/app.py
from flask import Flask, jsonify
from flask_cors import CORS
import yfinance as yf
import pandas as pd
import psycopg2
from psycopg2.extras import RealDictCursor
import os
import logging
from datetime import datetime, timedelta
import numpy as np
from config import Config

app = Flask(__name__)
CORS(app)

# Configure logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
logging.basicConfig(level = LOG_LEVEL)
logger = logging.getLogger (__name__)

# Database connection
DB_HOST = Config.DB_HOST
DB_PORT = Config.DB_PORT
DB_NAME = Config.DB_NAME
DB_USER = Config.DB_USER
DB_PASSWORD = Config.DB_PASSWORD
                           
def get_db_connection():
    """Get database connection"""
    try:
        conn = psycopg2.connect(
            host = DB_HOST,
            port = DB_PORT,
            database = DB_NAME,
            user = DB_USER,
            password = DB_PASSWORD
        )
        return conn
    except Exception as e:
        logger.error(f"Database Connection failed: {e}")
        return None
    
def init_db():
    """Finalize database tables"""
    conn = get_db_connection()
    if not conn:
        logger.warning("Cannot initiate DB - not connected")
        return
    
    cur = conn.cursor()
    
    try:
        # Create extension for TimescaleDB (if available)
        cur.execute("CREATE EXTENSION IF NOT EXISTS timescaledb;")

        # Create hypertable for stock prices
        cur.execute("""
            CREATE TABLE IF NOT EXISTS stock_prices (
                time TIMESTAMPZ NOT NULL,
                ticker TEXT NOT NULL,
                open FLOAT,
                high FLOAT,
                low FLOAT,
                close FLOAT,
                volume BIGINT
            );
        """)

        # Create hypertable if TimescaleDB available
        try:
            cur.execute("""
                SELECT create_hypertable('stock_prices', 'time' if_not_exists => TRUE);
            """)

        except:
            logger.info("TimescaleDB not available using regular table")
        
        # Create index
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_stock_prices_ticker_time ON stock_prices (ticker, time DESC);
        """)

        conn.commit()
        logger.info("Database initialized successfully")
    
    except Exception as e:
        logger.error(f"Database initialization error: {e}")
    finally:
        cur.close()
        conn.close()

@app.route("/health")
def health():
    """Health check endpoint"""
    return jsonify({"status": "healthy"}), 200

@app.route("/ready")
def ready():
    """Readiness check - verify database connection"""
    conn = get_db_connection()
    if conn:
        conn.close()
        return jsonify({"status": "ready"}), 200
    return jsonify({"status": "not ready"})

@app.route("/api/fetch/<ticker>")
def fetch_stock(ticker):
    """Fetch stock data from Yahoo Finance and store in database"""
    try:
        logger.info(f"Fetching data for {ticker}")

        # Fetch last 100 days of data
        stock = yf.Ticker(ticker)
        df = stock.history(period = "1y")

        if df.empty:
            return jsonify({"error": f"No data found for {ticker}"}), 404
        
        # Store in database
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Database connection failed"}), 500
        
        cur = conn.cursor()

        for idx, row in df.iterrows():
            cur.execute("""
                INSERT INTO stock_prices
                        (time, ticker, open, high, low, close, volume)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT DO NOTHING;
            """, (
                idx,
                ticker.upper(),
                float(row["Open"]),
                float(row["High"]),
                float(row["Low"]),
                float(row["Close"]),
                float(row["Volume"])
            ))
        
        conn.commit()
        cur.close()
        conn.close()

        return jsonify({
            "ticker": ticker.upper(),
            "rows_imported": len(df),
            "date_range": f"{df.index[0].date()} to {df.index[-1].date()}"
        })
    
    except Exception as e:
        logger.error(f"Error fetching {ticker}: {e}")
        return jsonify({"error": str(e)}), 500
    

@app.route("/api/indicators/<ticker>")
def get_indicators(ticker):
    """Get stock data with Bollinger Bands and SMAs"""
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Database connection failed"}), 500
        
        cur = conn.cursor(cursor_factory=RealDictCursor)

        # Fetch last 1 year of data
        cur.execute("""
            SELECT time, ticker, close, volume
            FROM stock_prices
            WHERE ticker = %s
            ORDER BY time ASC;
        """, (ticker.upper(),))

        rows = cur.fetchall()
        cur.close()
        conn.close()

        if not rows:
            return jsonify({"error": f"No data for {ticker}"})
        
        # Convert to pandas for calculations
        df = pd.DataFrame(rows)
        df["time"] = pd.to_datetime(df["time"])
        df = df.sort_values("time")

        # Calculate indicators
        df["sma_20"] = df["close"].rolling(window=20).mean()
        df["sma_50"] = df["close"].rolling(window=50).mean()
        df["sma_100"] = df["close"].rolling(window=100).mean()

        # Bollinger bands (20 day SMA, 2 std dev)
        df["bb_mid"] = df["close"].rolling(window=20).mean()
        df["bb_std"] = df["close"].rolling(window=20).std()
        df["bb_upper"] = df["bb_mid"] + (df["bb_std"] * 2)
        df["bb_lower"] = df["bb_mid"] - (df["bb_std"] * 2)

        # Return last 50 rows (most recent)
        result = df.to_dict("records")

        return jsonify({
            "ticker": ticker.upper(),
            "data": result
        })
    
    except Exception as e:
        logger.error(f"Error getting indicators for {ticker}: {e}")
        return jsonify({"error": str(e)}), 500
    
@app.route("/api/tickers")
def get_tickers():
    """Get list of tickers with data"""
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Database connection failed"}), 500
        
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("""
            SELECT DISTINCT ticker,
                    COUNT(*) as data_points,
                    MAX(time) as last_updated
            FROM stock_prices
            GROUP BY ticker
            ORDER BY last_updated DESC;
        """)

        rows = cur.fetchall()
        cur.close()
        conn.close()

        return jsonify({"tickers": rows})
    
    except Exception as e:
        logger.error(f"Error getting tickers: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    # Initialize database
    init_db()
    app.run(host="0.0.0.0", port = 5000, debug = False)