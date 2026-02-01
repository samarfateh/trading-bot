import unittest
import os
from strategy_lab.core import StrategyValidator

class TestStrategyLibrary(unittest.TestCase):
    
    def setUp(self):
        self.library_path = os.path.join(os.path.dirname(__file__), '../library')

    def test_load_strategies(self):
        """Test that we can load and validate all strategies in the library."""
        strategies = StrategyValidator.load_library(self.library_path)
        
        # We expect at least 2 strategies (Bull Call, Iron Condor)
        self.assertTrue(len(strategies) >= 2)
        
        # Verify Bull Call Spread specifics
        bull_call = next((s for s in strategies if s['id'] == 'bull_call_spread_trend'), None)
        self.assertIsNotNone(bull_call)
        self.assertEqual(bull_call['type'], 'VERTICAL_SPREAD')
        self.assertEqual(len(bull_call['legs']), 2)

    def test_validation_logic(self):
        """Test that invalid strategies raise errors."""
        bad_strategy = {
            "name": "Broken Strategy",
            "type": "UNKNOWN",
            "direction": "INVALID_DIR", # This should fail
            "legs": []
        }
        
        with self.assertRaises(ValueError):
            StrategyValidator.validate(bad_strategy)

if __name__ == '__main__':
    unittest.main()
