import unittest
from strategy_lab.scanner import StrategyScanner

class TestScanner(unittest.TestCase):

    def setUp(self):
        self.bull_strat = {
            "id": "bull_call",
            "name": "Bull Call",
            "entry_rules": { "trend": "UP", "min_iv_rank": 0, "max_iv_rank": 50 }
        }
        self.bear_strat = {
            "id": "bear_put",
            "name": "Bear Put",
            "entry_rules": { "trend": "DOWN" }
        }

    def test_applicability_logic(self):
        # Scenario 1: Uptrend, Low IV (Should match Bull)
        features = { "trend": "UP", "iv_rank": 20 }
        
        self.assertTrue(StrategyScanner.is_applicable(self.bull_strat, features))
        self.assertFalse(StrategyScanner.is_applicable(self.bear_strat, features))

        # Scenario 2: Uptrend, HIGH IV (Should fail Bull due to IV limit)
        features_high_vol = { "trend": "UP", "iv_rank": 80 }
        self.assertFalse(StrategyScanner.is_applicable(self.bull_strat, features_high_vol))

    def test_full_scan(self):
        scanner = StrategyScanner()
        strategies = [self.bull_strat, self.bear_strat]
        
        # Mock Market Data that produces UP Trend and Low IV
        # We cheat a bit here by knowing analyze_snapshot calls calculate_trend/iv_rank
        # But for this test, let's trust the unit integration or just mock features 
        # Actually scanner.scan calls analyze_snapshot, so we need valid inputs for that.
        
        market_data = {
            "closes": [100 + i for i in range(60)], # Uptrend
            "current_iv": 0.20,
            "iv_history": [0.10, 0.50] # Rank will be ~ low
        }
        
        signals = scanner.scan(strategies, market_data)
        
        self.assertEqual(len(signals), 1)
        self.assertEqual(signals[0]['strategy_id'], 'bull_call')

if __name__ == '__main__':
    unittest.main()
