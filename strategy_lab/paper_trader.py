import sqlite3
import json
from datetime import datetime
from typing import Dict, Optional

class PaperTrader:
    """
    Simulates execution of trades based on Signals.
    Tracks Entry, Exit, and P&L.
    Now includes 'The Teacher' (Post-Mortem Analysis).
    And 'Realism' (Slippage Simulation).
    """
    
    SLIPPAGE = 0.001 # 0.1% Friction per leg
    
    def __init__(self, db_path: str = "data_lake.db"):
        self.db_path = db_path
        self._migrate_db()
        
    def _apply_slippage(self, price: float, action: str) -> float:
        """
        Simulates Bid/Ask Spread.
        action: 'BUY' (Ask) or 'SELL' (Bid)
        """
        if action == 'BUY':
            return price * (1 + self.SLIPPAGE) # Pay more
        else: # SELL
            return price * (1 - self.SLIPPAGE) # Receive less

    def _migrate_db(self):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # Original Schema + New Columns
        c.execute('''
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                signal_id INTEGER,
                strategy_id TEXT,
                symbol TEXT,
                direction TEXT,
                status TEXT,
                entry_price REAL,
                exit_price REAL,
                entry_date TEXT,
                exit_date TEXT,
                pnl REAL,
                pnl_pct REAL,
                context TEXT, 
                lesson TEXT
            )
        ''')
        
        # Signal Table (Dependency)
        c.execute('''
            CREATE TABLE IF NOT EXISTS signals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                strategy_id TEXT,
                symbol TEXT,
                direction TEXT,
                features TEXT,
                timestamp TEXT
            )
        ''')

        # Auto-Migration: Add context/lesson if missing
        try:
            c.execute("ALTER TABLE trades ADD COLUMN context TEXT")
        except: pass
        try:
            c.execute("ALTER TABLE trades ADD COLUMN lesson TEXT")
        except: pass
        
        conn.commit()
        conn.close()

    def record_signal(self, signal: Dict) -> int:
        """Logs a signal to DB. Returns the signal_id."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute('''
            INSERT INTO signals (strategy_id, symbol, direction, features, timestamp)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            signal["strategy_id"], 
            "AMD", 
            signal["direction"], 
            json.dumps(signal["features_matched"]),
            datetime.now()
        ))
        
        signal_id = c.lastrowid
        conn.commit()
        conn.close()
        return signal_id

    def open_trade(self, signal: Dict, current_price: float, context: Dict = {}) -> int:
        """
        Opens a trade and saves the Entry Context (The 'Why').
        Applies SLIPPAGE (Realism).
        """
        signal_id = self.record_signal(signal)
        direction = signal["direction"]
        
        # Calculate Real Entry Price (w/ Friction)
        entry_price = current_price
        if direction == "BULLISH":
             # Long: Buy at Ask
             entry_price = self._apply_slippage(current_price, 'BUY')
        elif direction == "BEARISH":
             # Short: Sell at Bid
             entry_price = self._apply_slippage(current_price, 'SELL')
        
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute('''
            INSERT INTO trades (signal_id, strategy_id, symbol, status, entry_price, entry_date, context)
            VALUES (?, ?, ?, 'OPEN', ?, ?, ?)
        ''', (
            signal_id,
            signal['strategy_id'],
            "AMD",
            entry_price, # Slippage Applied
            datetime.now(),
            json.dumps(context)
        ))
        
        trade_id = c.lastrowid
        conn.commit()
        conn.close()
        return trade_id

    def generate_lesson(self, pnl_pct: float, direction: str, context: Dict) -> str:
        """
        The Teacher: Explains WHY the trade won or lost.
        """
        # Win
        if pnl_pct > 0:
            return "✅ Market Matched Strategy. Good execution."
            
        # Loss
        # 1. Check IV
        iv = context.get("current_iv", 0)
        if iv > 0.60:
            return "❌ IV CRUSH: You bought expensive options in high volatility."
            
        # 2. Check Panic
        if "panic" in str(context).lower():
             return "❌ FOUGHT FEAR: Market was in panic mode."
             
        # 3. Default
        return "⚠️ TIMING: Direction was right, but entry was too early."

    def close_trade(self, trade_id: int, current_market_price: float):
        """
        Closes a trade, calculates P&L, and writes the Lesson.
        Applies SLIPPAGE on Exit.
        """
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # Get Trade Info
        c.execute("SELECT trades.entry_price, trades.strategy_id, signals.direction, trades.context FROM trades JOIN signals ON trades.signal_id = signals.id WHERE trades.id = ?", (trade_id,))
        row = c.fetchone()
        if not row: return
        
        entry_price, strat_id, direction, context_json = row
        context = json.loads(context_json) if context_json else {}
        
        # Calculate Real Exit Price (Slippage)
        exit_price = current_market_price
        if direction == "BULLISH":
            # Selling to Close (Hit Bid)
            exit_price = self._apply_slippage(current_market_price, 'SELL')
        elif direction == "BEARISH":
            # Buying to Cover (Hit Ask)
            exit_price = self._apply_slippage(current_market_price, 'BUY')
        
        # Calculate P&L
        pnl = 0.0
        if direction == "BULLISH":
            pnl = exit_price - entry_price
        elif direction == "BEARISH":
            pnl = entry_price - exit_price
        
        pnl_pct = (pnl / entry_price) * 100 if entry_price else 0
        
        # Generate Lesson
        lesson = self.generate_lesson(pnl_pct, direction, context)

        c.execute('''
            UPDATE trades 
            SET status = 'CLOSED', exit_price = ?, exit_date = ?, pnl = ?, pnl_pct = ?, lesson = ?
            WHERE id = ?
        ''', (exit_price, datetime.now(), pnl, pnl_pct, lesson, trade_id))
        
        conn.commit()
        conn.close()

    def get_portfolio_stats(self) -> Dict:
        """Returns stats including the lesson history."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        # Stats
        c.execute("SELECT sum(pnl), count(*) FROM trades WHERE status='CLOSED'")
        row = c.fetchone()
        if row:
            total_pnl, total_closed = row
        else:
            total_pnl, total_closed = 0, 0
            
        total_pnl = total_pnl if total_pnl else 0
        
        if total_closed and total_closed > 0:
             c.execute("SELECT count(*) FROM trades WHERE status='CLOSED' AND pnl > 0")
             wins = c.fetchone()[0]
             win_rate = round((wins / total_closed * 100), 1)
        else:
             win_rate = 0
        
        # Open Trades
        c.execute('''
            SELECT t.id, t.symbol, t.entry_price, t.strategy_id, s.direction, t.entry_date
            FROM trades t JOIN signals s ON t.signal_id = s.id
            WHERE t.status = 'OPEN'
        ''')
        open_trades = [dict(row) for row in c.fetchall()]

        # Closed History (For Lessons)
        c.execute('''
            SELECT t.id, t.strategy_id, t.pnl, t.lesson, t.exit_date
            FROM trades t
            WHERE t.status = 'CLOSED'
            ORDER BY t.exit_date DESC LIMIT 5
        ''')
        history = [dict(row) for row in c.fetchall()]
        
        conn.close()
        return {
            "total_pnl": round(total_pnl, 2),
            "win_rate": win_rate,
            "total_trades": total_closed,
            "open_trades": open_trades,
            "history": history
        }

    def update_positions(self, current_price: float):
        """
        Runs the 'Reflection' loop.
        Closes trades if they hit Target (+2%) or Stop Loss (-1%).
        """
        stats = self.get_portfolio_stats()
        open_trades = stats['open_trades']
        
        for trade in open_trades:
            entry = trade['entry_price']
            direction = trade['direction']
            
            # Simple MVP Exit Rules
            target_pct = 0.02 # 2% Gain
            stop_pct = 0.01   # 1% Loss
            
            should_close = False
            
            if direction == 'BULLISH':
                if current_price >= entry * (1 + target_pct): should_close = True # Win
                elif current_price <= entry * (1 - stop_pct): should_close = True # Loss
            elif direction == 'BEARISH':
                if current_price <= entry * (1 - target_pct): should_close = True # Win
                elif current_price >= entry * (1 + stop_pct): should_close = True # Loss
                
            if should_close:
                print(f"💰 Closing Trade #{trade['id']} ({trade['strategy_id']}) at ${current_price}")
                self.close_trade(trade['id'], current_price)
