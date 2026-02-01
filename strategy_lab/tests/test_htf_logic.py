import unittest
from strategy_lab.scanner import StrategyScanner

class TestHTFConfluence(unittest.TestCase):

    def setUp(self):
        self.bull_strat = {
            "id": "bull_call",
            "direction": "BULLISH",
            "entry_rules": { "trend": "UP" }
        }
        self.bear_strat = {
            "id": "bear_put",
            "direction": "BEARISH",
            "entry_rules": { "trend": "DOWN" }
        }

    def test_htf_filtering(self):
        # Scenario 1: 5m UP, 1H UP (Golden Setup) -> ALLOW
        # Note: 'htf_trend' is pre-calculated by feature engine
        features_aligned = { "trend": "UP", "htf_trend": "UP", "iv_rank": 20 }
        self.assertTrue(StrategyScanner.is_applicable(self.bull_strat, features_aligned))

        # Scenario 2: 5m UP, 1H DOWN (Trap) -> BLOCK
        features_trap = { "trend": "UP", "htf_trend": "DOWN", "iv_rank": 20 }
        self.assertFalse(StrategyScanner.is_applicable(self.bull_strat, features_trap))

        # Scenario 3: 5m DOWN, 1H DOWN (Aligned Bear) -> ALLOW
        features_bear = { "trend": "DOWN", "htf_trend": "DOWN", "iv_rank": 20 }
        self.assertTrue(StrategyScanner.is_applicable(self.bear_strat, features_bear))

        # Scenario 4: 5m DOWN, 1H UP (Contra) -> BLOCK
        features_contra = { "trend": "DOWN", "htf_trend": "UP", "iv_rank": 20 }
        self.assertFalse(StrategyScanner.is_applicable(self.bear_strat, features_contra))

if __name__ == '__main__':
    unittest.main()
