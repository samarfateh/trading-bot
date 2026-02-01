import sqlite3
from typing import List, Dict

class ScoreKeeper:
    """
    Computes performance metrics for strategies based on closed trades.
    """
    
    def __init__(self, db_path: str = "data_lake.db"):
        self.db_path = db_path

    def get_strategy_stats(self) -> List[Dict]:
        """
        Returns a list of stats per strategy.
        """
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # Aggregate Stats
        c.execute('''
            SELECT 
                strategy_id,
                COUNT(*) as total_trades,
                SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) as wins,
                AVG(pnl) as avg_pnl,
                SUM(pnl) as total_pnl
            FROM trades
            WHERE status = 'CLOSED'
            GROUP BY strategy_id
        ''')
        
        stats = []
        for row in c.fetchall():
            strat_id, total, wins, avg_pnl, total_pnl = row
            win_rate = (wins / total) * 100 if total > 0 else 0
            
            stats.append({
                "strategy_id": strat_id,
                "total_trades": total,
                "win_rate": round(win_rate, 1),
                "avg_pnl": round(avg_pnl, 2) if avg_pnl else 0.0,
                "total_pnl": round(total_pnl, 2) if total_pnl else 0.0,
                "status": "ACTIVE" if win_rate >= 50 else "REVIEW" # Self-Improvement Logic
            })
            
        conn.close()
        return stats
