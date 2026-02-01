import unittest
import os
import sqlite3
from strategy_lab.paper_trader import PaperTrader

class TestPaperTrader(unittest.TestCase):
    
    def setUp(self):
        self.test_db = "test_strategies.db"
        # Setup clean DB
        conn = sqlite3.connect(self.test_db)
        c = conn.cursor()
        c.execute('CREATE TABLE signals (id INTEGER PRIMARY KEY, strategy_id TEXT, symbol TEXT, direction TEXT, features JSON, processed BOOLEAN)')
        c.execute('CREATE TABLE trades (id INTEGER PRIMARY KEY, signal_id INTEGER, strategy_id TEXT, symbol TEXT, status TEXT, entry_price REAL, exit_price REAL, pnl REAL, pnl_pct REAL, entry_date DATETIME, exit_date DATETIME)')
        conn.commit()
        conn.close()
        
        self.trader = PaperTrader(db_path=self.test_db)

    def tearDown(self):
        if os.path.exists(self.test_db):
            os.remove(self.test_db)

    def test_trade_lifecycle(self):
        signal = { 
            "strategy_id": "bull_test", 
            "direction": "BULLISH", 
            "features_matched": {} 
        }
        
        # Open Trade at $100
        trade_id = self.trader.open_trade(signal, 100.0)
        self.assertIsNotNone(trade_id)
        
        # Close Trade at $110 (10% Gain)
        self.trader.close_trade(trade_id, 110.0)
        
        # Verify DB
        conn = sqlite3.connect(self.test_db)
        c = conn.cursor()
        c.execute("SELECT pnl, pnl_pct, status FROM trades WHERE id=?", (trade_id,))
        pnl, pct, status = c.fetchone()
        
        self.assertEqual(status, 'CLOSED')
        self.assertAlmostEqual(pnl, 10.0)
        self.assertAlmostEqual(pct, 10.0)

if __name__ == '__main__':
    unittest.main()
