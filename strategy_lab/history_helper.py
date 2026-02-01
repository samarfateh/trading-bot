import sqlite3
from typing import List, Dict

def get_backtest_history(db_path="data_lake.db", limit=100) -> List[Dict]:
    """
    Fetch backtest history for UI display
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # Return rows as dictionaries
    c = conn.cursor()
    
    c.execute(f'''
        SELECT 
            timestamp,
            symbol,
            price,
            day_high,
            day_low,
            volume,
            iv,
            vix,
            spy_trend,
            sector_trend,
            verdict,
            recommended_strategy,
            strategy_direction,
            confidence,
            outcome_1d,
            outcome_3d,
            outcome_7d,
            market_regime
        FROM backtest_history
        ORDER BY timestamp DESC
        LIMIT {limit}
    ''')
    
    rows = c.fetchall()
    conn.close()
    
    # Convert to list of dicts
    return [dict(row) for row in rows]

def get_backtest_stats(db_path="data_lake.db") -> Dict:
    """
    Get summary statistics for backtest history
    """
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    stats = {}
    
    # Total decisions
    c.execute("SELECT COUNT(*) FROM backtest_history")
    stats['total_decisions'] = c.fetchone()[0]
    
    # Strategy performance
    c.execute('''
        SELECT 
            recommended_strategy,
            COUNT(*) as count,
            ROUND(AVG(outcome_7d), 2) as avg_outcome,
            ROUND(SUM(CASE WHEN outcome_7d > 0 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) as win_rate
        FROM backtest_history
        WHERE recommended_strategy IS NOT NULL
        GROUP BY recommended_strategy
        ORDER BY win_rate DESC
    ''')
    
    stats['strategies'] = []
    for row in c.fetchall():
        stats['strategies'].append({
            'name': row[0],
            'count': row[1],
            'avg_outcome': row[2],
            'win_rate': row[3]
        })
    
    # Regime distribution
    c.execute('''
        SELECT market_regime, COUNT(*) as days
        FROM backtest_history
        GROUP BY market_regime
    ''')
    
    stats['regimes'] = {}
    for row in c.fetchall():
        stats['regimes'][row[0]] = row[1]
    
    conn.close()
    return stats
