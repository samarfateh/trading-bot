import unittest
from strategy_lab.judge import TheJudge

class TestTheJudge(unittest.TestCase):

    def test_strong_buy(self):
        # Scenario: Confluence (Trend UP + Support + Div)
        features = {
            "trend": "UP",
            "htf_trend": "UP",         # +2
            "key_level": "AT_SUPPORT", # +1
            "divergence": "BULL_DIV",  # +2
            "sector_correlation": "WITH_SECTOR"
        }
        # Expected Score: 5 -> STRONG BUY
        result = TheJudge.delimit_verdict(features)
        self.assertIn("STRONG BUY", result)
        self.assertIn("BULLISH DIVERGENCE", result)

    def test_strong_sell(self):
        # Scenario: Downtrend + Resistance
        features = {
            "trend": "DOWN",
            "htf_trend": "DOWN",           # -2
            "key_level": "AT_RESISTANCE",  # -1
            "divergence": "NONE"
        }
        # Expected Score: -3 -> STRONG SELL
        result = TheJudge.delimit_verdict(features)
        self.assertIn("STRONG SELL", result)
        self.assertIn("hitting RESISTANCE", result)

    def test_conflict_neutral(self):
        # Scenario: Uptrend but hitting Resistance
        features = {
            "trend": "UP",
            "htf_trend": "UP",            # +2
            "key_level": "AT_RESISTANCE", # -1
            "divergence": "BEAR_DIV"      # -2
        }
        # Expected Score: -1 -> SELL (or Neutral lean)
        # 2 - 1 - 2 = -1
        result = TheJudge.delimit_verdict(features)
        self.assertIn("SELL", result) # Or at least warn

if __name__ == '__main__':
    unittest.main()
