import unittest
from strategy_lab.market_features import MarketFeatureEngine

class TestMarketFeatures(unittest.TestCase):

    def test_trend_detection(self):
        # Create a bullish sequence (Price > SMA20 > SMA50)
        # 50 candles, steadily increasing from 100 to 150
        closes = [100 + i for i in range(50)] 
        
        trend = MarketFeatureEngine.calculate_trend(closes)
        self.assertEqual(trend, "UP")

        # Create a bearish sequence
        closes_down = [150 - i for i in range(50)]
        trend_down = MarketFeatureEngine.calculate_trend(closes_down)
        self.assertEqual(trend_down, "DOWN")

    def test_iv_rank(self):
        history = [0.20, 0.30, 0.40, 0.50, 0.60] # Low 0.20, High 0.60
        current = 0.40 # Exactly middle
        
        rank = MarketFeatureEngine.calculate_iv_rank(current, history)
        self.assertEqual(rank, 50)
        
        # Test Max
        rank_high = MarketFeatureEngine.calculate_iv_rank(0.60, history)
        self.assertEqual(rank_high, 100)

if __name__ == '__main__':
    unittest.main()
