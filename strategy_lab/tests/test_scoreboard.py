import unittest
import os
import sqlite3
from strategy_lab.scoreboard import ScoreKeeper

class TestScoreboard(unittest.TestCase):
    
    def setUp(self):
        self.test_db = "test_stats.db"
        conn = sqlite3.connect(self.test_db)
        c = conn.cursor()
        c.execute('CREATE TABLE trades (id INTEGER PRIMARY KEY, strategy_id TEXT, status TEXT, pnl REAL)')
        
        # Insert Mock Data
        # Strategy A: 1 Win, 1 Loss
        c.execute("INSERT INTO trades (strategy_id, status, pnl) VALUES ('strat_a', 'CLOSED', 100)")
        c.execute("INSERT INTO trades (strategy_id, status, pnl) VALUES ('strat_a', 'CLOSED', -50)")
        
        # Strategy B: 2 Wins
        c.execute("INSERT INTO trades (strategy_id, status, pnl) VALUES ('strat_b', 'CLOSED', 10)")
        c.execute("INSERT INTO trades (strategy_id, status, pnl) VALUES ('strat_b', 'CLOSED', 20)")
        
        conn.commit()
        conn.close()
        
        self.keeper = ScoreKeeper(db_path=self.test_db)

    def tearDown(self):
        if os.path.exists(self.test_db):
            os.remove(self.test_db)

    def test_stats_aggregation(self):
        stats = self.keeper.get_strategy_stats()
        
        # Sort by ID to ensure order
        stats.sort(key=lambda x: x['strategy_id'])
        
        # Strat A (50% Win Rate)
        self.assertEqual(stats[0]['strategy_id'], 'strat_a')
        self.assertEqual(stats[0]['win_rate'], 50.0)
        self.assertEqual(stats[0]['total_pnl'], 50.0)
        
        # Strat B (100% Win Rate)
        self.assertEqual(stats[1]['strategy_id'], 'strat_b')
        self.assertEqual(stats[1]['win_rate'], 100.0)
        self.assertEqual(stats[1]['status'], 'ACTIVE')

if __name__ == '__main__':
    unittest.main()
