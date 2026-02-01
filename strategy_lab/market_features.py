import statistics
from typing import List, Dict

class MarketFeatureEngine:
    """
    Analyzes raw market data to produce discrete feature tags.
    """

    @staticmethod
    def calculate_trend(closes: List[float]) -> str:
        """
        Determines trend based on SMA alignment.
        UP: Price > SMA20 > SMA50
        DOWN: Price < SMA20 < SMA50
        SIDEWAYS: Any other state
        """
        if len(closes) < 50:
            return "UNKNOWN"

        current_price = closes[-1]
        sma20 = statistics.mean(closes[-20:])
        sma50 = statistics.mean(closes[-50:])

        if current_price > sma20 and sma20 > sma50:
            return "UP"
        if current_price < sma20 and sma20 < sma50:
            return "DOWN"
        
        return "SIDEWAYS"

    @staticmethod
    def calculate_iv_rank(current_iv: float, iv_history: List[float]) -> int:
        """
        Computes IV Rank (0-100) based on 1-year low/high.
        """
        if not iv_history:
            return 50 # Default to mid if no history
        
        low = min(iv_history)
        high = max(iv_history)
        
        if high == low:
            return 50

        rank = ((current_iv - low) / (high - low)) * 100
        return int(max(0, min(100, rank)))

    @staticmethod
    def calculate_rsi(prices: List[float], period: int = 14) -> float:
        """
        Calculates RSI for a given list of prices. Returns 50 if insufficient data.
        """
        if len(prices) < period + 1:
            return 50.0

        deltas = [prices[i] - prices[i-1] for i in range(1, len(prices))]
        gains = [d for d in deltas if d > 0]
        losses = [abs(d) for d in deltas if d < 0]

        avg_gain = sum(gains[-period:]) / period if gains else 0
        avg_loss = sum(losses[-period:]) / period if losses else 0

        if avg_loss == 0:
            return 100.0
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    @staticmethod
    def calculate_key_levels(closes: List[float]) -> str:
        """
        Checks if current price is near Support (Low of last 50) or Resistance (High of last 50).
        """
        if len(closes) < 50:
            return "MIDDLE"
        
        price = closes[-1]
        period = closes[-50:]
        low = min(period)
        high = max(period)
        range_size = high - low
        
        # Buffer of 10% of the range
        buffer = range_size * 0.10

        if price <= low + buffer:
            return "AT_SUPPORT"
        if price >= high - buffer:
            return "AT_RESISTANCE"
        
        return "MIDDLE"

    @staticmethod
    def calculate_rsi_divergence(closes: List[float]) -> str:
        """
        Detects basic divergence between Price and RSI Slope over last 10 candles.
        """
        if len(closes) < 20: 
            return "NONE"

        price_slope = closes[-1] - closes[-10]
        
        # Calculate RSI generally
        rsi_now = MarketFeatureEngine.calculate_rsi(closes)
        rsi_prev = MarketFeatureEngine.calculate_rsi(closes[:-10])
        rsi_slope = rsi_now - rsi_prev

        # Bullish Div: Price Lower, RSI Higher
        if price_slope < 0 and rsi_slope > 0:
            return "BULL_DIV"
        
        # Bearish Div: Price Higher, RSI Lower
        if price_slope > 0 and rsi_slope < 0:
            return "BEAR_DIV"
        
        return "NONE"

    @staticmethod
    def calculate_sector_correlation(stock_closes: List[float], sector_closes: List[float]) -> str:
        """
        Checks if Stock Trend aligns with Sector Trend (QQQ).
        """
        stock_trend = MarketFeatureEngine.calculate_trend(stock_closes)
        sector_trend = MarketFeatureEngine.calculate_trend(sector_closes)

        if stock_trend == sector_trend:
            return "WITH_SECTOR"
        return "AGAINST_SECTOR"

    @staticmethod
    def analyze_snapshot(snapshot: Dict) -> Dict:
        """
        Takes a full market snapshot and returns a feature dictionary.
        snapshot = {
            "closes": [...],
            "htf_closes": [...], # Optional: Hourly Candles
            "current_iv": 0.45,
            "iv_history": [...]
        }
        """
        features = {}
        features["trend"] = MarketFeatureEngine.calculate_trend(snapshot["closes"])
        
        # New: Higher Timeframe Trend
        if "htf_closes" in snapshot and snapshot["htf_closes"]:
            features["htf_trend"] = MarketFeatureEngine.calculate_trend(snapshot["htf_closes"])
        else:
            features["htf_trend"] = "UNKNOWN"

        features["iv_rank"] = MarketFeatureEngine.calculate_iv_rank(
            snapshot["current_iv"], 
            snapshot.get("iv_history", [])
        )

        # Advanced Analytics (The Judge)
        features["key_level"] = MarketFeatureEngine.calculate_key_levels(snapshot["closes"])
        features["divergence"] = MarketFeatureEngine.calculate_rsi_divergence(snapshot["closes"])
        
        if "sector_closes" in snapshot and snapshot["sector_closes"]:
            features["sector_correlation"] = MarketFeatureEngine.calculate_sector_correlation(
                snapshot["closes"], 
                snapshot["sector_closes"]
            )
        else:
            features["sector_correlation"] = "UNKNOWN"

        features["sentiment"] = snapshot.get("sentiment", {"score": 0, "direction": "NEUTRAL"})

        # --- Safety Net Data ---
        features["current_iv"] = snapshot.get("current_iv", 0)
        
        # Calculate SMA200 if possible, else 0
        closes = snapshot["closes"]
        if len(closes) >= 200:
            features["sma_200"] = sum(closes[-200:]) / 200
        else:
            features["sma_200"] = 0
            
        features["current_price"] = closes[-1] if closes else 0

        return features
