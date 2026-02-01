import requests
import sqlite3
import time
import json
import logging
import statistics
from datetime import datetime
from typing import Dict, Any, Optional

# --- CONFIGURATION ---
# Replace with your actual Alpha Vantage Key
API_KEY = "POPZN5W6J3DCL2WE"
DB_PATH = "data_lake.db"

# Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AlphaVantageEngine:
    """
    Professional-grade data engine for Alpha Vantage.
    Features:
    - Automatic Rate Limiting / Retries
    - Raw Data Persistence (SQLite)
    - Anti-Gravity Analytics
    """

    def __init__(self, api_key: str, db_path: str = DB_PATH):
        self.api_key = api_key
        self.db_path = db_path
        self.base_url = "https://www.alphavantage.co/query"
        self._initialize_db()

    def _initialize_db(self):
        """Creates the raw persistence layer if it doesn't exist."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # Raw Data Table: Stores exact JSON responses for replay/audit
        c.execute('''
            CREATE TABLE IF NOT EXISTS raw_market_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                function_name TEXT,
                symbol TEXT,
                data JSON
            )
        ''')
        
        # Processed Analysis Table (Optional, for caching consensus)
        c.execute('''
            CREATE TABLE IF NOT EXISTS consensus_forecasts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                symbol TEXT,
                score REAL,
                details JSON
            )
        ''')

        # Strategy Lab: Signals
        c.execute('''
            CREATE TABLE IF NOT EXISTS signals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                strategy_id TEXT,
                symbol TEXT,
                direction TEXT,
                features JSON,
                processed BOOLEAN DEFAULT 0
            ) 
        ''')

        # Strategy Lab: Trades
        c.execute('''
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                signal_id INTEGER,
                strategy_id TEXT,
                symbol TEXT,
                status TEXT, -- OPEN, CLOSED
                entry_price REAL,
                exit_price REAL,
                pnl REAL,
                pnl_pct REAL,
                entry_date DATETIME,
                exit_date DATETIME
            )
        ''')
        
        conn.commit()
        conn.close()

    def _save_raw(self, function: str, symbol: str, data: Dict):
        """Saves raw API response to SQLite."""
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute(
                "INSERT INTO raw_market_data (function_name, symbol, data) VALUES (?, ?, ?)",
                (function, symbol, json.dumps(data))
            )
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Failed to save raw data: {e}")

    def _request(self, function: str, symbol: str, **kwargs) -> Optional[Dict]:
        """
        Robust API Request wrapper with Retries and Backoff.
        """
        params = {
            "function": function,
            "symbol": symbol,
            "apikey": self.api_key,
            **kwargs
        }

        retries = 3
        backoff = 2

        for attempt in range(retries):
            try:
                response = requests.get(self.base_url, params=params, timeout=10)
                response.raise_for_status()
                data = response.json()

                # Check for API Error Messages
                if "Error Message" in data:
                    logger.error(f"API Error for {function}: {data['Error Message']}")
                    return None
                if "Note" in data:
                    # Often means rate limit hit
                    logger.warning(f"API Limit Hint: {data['Note']}")
                    time.sleep(10) # Cooldown
                    continue

                # Success - Persist and Return
                self._save_raw(function, symbol, data)
                return data

            except requests.exceptions.RequestException as e:
                logger.warning(f"Request failed (Attempt {attempt+1}/{retries}): {e}")
                time.sleep(backoff ** attempt)
        
        logger.error(f"Max retries reached for {function}")
        return None

    # --- DATA STREAMS ---

    def fetch_intraday(self, symbol: str) -> Dict:
        """Fetches Minute-by-Minute OHLCV."""
        logger.info(f"Fetching Intraday Data for {symbol}...")
        return self._request("TIME_SERIES_INTRADAY", symbol, interval="1min", outputsize="full")

    def fetch_hourly(self, symbol: str) -> Dict:
        """Fetches Hourly OHLCV for Higher Timeframe trend."""
        logger.info(f"Fetching Hourly Data for {symbol}...")
        return self._request("TIME_SERIES_INTRADAY", symbol, interval="60min", outputsize="full")

    def fetch_sentiment(self, symbol: str) -> Dict:
        """Fetches News Sentiment Scores."""
        logger.info(f"Fetching News Sentiment for {symbol}...")
        return self._request("NEWS_SENTIMENT", symbol, tickers=symbol, limit=50)

    def fetch_earnings(self, symbol: str) -> Dict:
        """Fetches Earnings Data."""
        logger.info(f"Fetching Earnings for {symbol}...")
        return self._request("EARNINGS", symbol)

    # --- ANTI-GRAVITY ANALYTICS ---

    def calculate_technical_score(self, intraday_data: Dict) -> float:
        """
        Calculates a technical score (0-100) based on Intraday Trend.
        Returns 50 if neutral/no data.
        """
        try:
            ts = intraday_data.get("Time Series (1min)", {})
            if not ts: return 50.0

            closes = [float(v["4. close"]) for k, v in list(ts.items())[:50]]
            if not closes: return 50.0
            
            # Simple Moving Average Logic
            current = closes[0]
            avg = statistics.mean(closes)
            
            if current > avg * 1.01: return 75.0 # Bullish
            if current < avg * 0.99: return 25.0 # Bearish
            return 50.0
        except Exception as e:
            logger.error(f"Tech Calc Error: {e}")
            return 50.0

    def calculate_sentiment_score(self, sentiment_data: Dict) -> float:
        """
        Parses News Sentiment API response into a 0-100 score.
        """
        try:
            feed = sentiment_data.get("feed", [])
            if not feed: return 50.0

            scores = []
            for item in feed:
                # AlphaVantage gives 'overall_sentiment_score' (-0.35 to +0.35 usually)
                s = float(item.get("overall_sentiment_score", 0))
                scores.append(s)
            
            avg_score = statistics.mean(scores)
            # Normalize -0.5...0.5 to 0...100
            normalized = (avg_score + 0.5) * 100
            return max(0, min(100, normalized))

        except Exception as e:
            logger.error(f"Sentiment Calc Error: {e}")
            return 50.0

    def get_consensus_forecast(self, symbol: str) -> Dict:
        """
        The 'Anti-Gravity' Master Function.
        Combines Technicals + Sentiment + Earnings into a single Weighted Score.
        """
        # 1. Gather Data
        intraday = self.fetch_intraday(symbol)
        sentiment = self.fetch_sentiment(symbol)
        # earnings = self.fetch_earnings(symbol) # Optional inclusion

        # 2. Compute Component Scores
        tech_score = self.calculate_technical_score(intraday)
        sent_score = self.calculate_sentiment_score(sentiment)
        
        # 3. Weighted Consensus
        # Weights: Technicals (40%), Sentiment (40%), Institutional Gravity (20% - Bias)
        gravity_bias = 55.0 # Assumes slight institutional long bias
        
        consensus = (tech_score * 0.4) + (sent_score * 0.4) + (gravity_bias * 0.2)
        
        decision = "HOLD"
        if consensus > 65: decision = "BUY"
        if consensus < 35: decision = "SELL"

        result = {
            "symbol": symbol,
            "consensus_score": round(consensus, 2),
            "decision": decision,
            "components": {
                "technical": round(tech_score, 2),
                "sentiment": round(sent_score, 2),
                "gravity": round(gravity_bias, 2)
            },
            "timestamp": datetime.now().isoformat()
        }
        
        # Cache Result
        logger.info(f"Consensus Generated: {decision} ({consensus})")
        return result

# --- EXECUTION ---
if __name__ == "__main__":
    print("--- Professional Data Architect ---")
    
    # Initialize Engine
    engine = AlphaVantageEngine(api_key=API_KEY)
    
    # Test Run (Using a Demo Symbol if key is missing/demo, or user's key)
    TARGET = "AMD"
    
    print(f"Running Anti-Gravity Analysis for {TARGET}...")
    forecast = engine.get_consensus_forecast(TARGET)
    
    print("\nFINAL FORECAST:")
    print(json.dumps(forecast, indent=2))
    print(f"\nRaw Data saved to: {DB_PATH}")
