"""
Risk Management Engine
Enforces safety limits before every trade
"""
from typing import Dict, Optional, Tuple
from datetime import datetime, time
from strategy_lab.config import RISK_LIMITS
import os

class RiskManager:
    def __init__(self, db_path="trading.db"):
        self.limits = RISK_LIMITS
        self.db_path = db_path
        self.daily_stats = {
            "trades_today": 0,
            "pnl_today": 0.0,
            "consecutive_losses": 0,
            "last_reset": datetime.now().date()
        }
    
    def can_trade(self, account_value: float, current_positions: int, vix: float, spy_change: float) -> Tuple[bool, str]:
        """
        Master risk check - returns (can_trade, reason)
        """
        # Reset daily counters if new day
        self._reset_if_new_day()
        
        # 1. Check kill switch
        if self._is_kill_switch_active():
            return False, "🛑 Kill switch active (STOP_TRADING.txt exists)"
        
        # 2. Check daily trade limit
        if self.daily_stats["trades_today"] >= self.limits["max_trades_per_day"]:
            return False, f"🚫 Daily trade limit reached ({self.limits['max_trades_per_day']} trades)"
        
        # 3. Check daily loss limit
        loss_pct = (self.daily_stats["pnl_today"] / account_value) * 100 if account_value > 0 else 0
        if loss_pct < -self.limits["max_daily_loss_pct"]:
            self._trigger_auto_pause("daily_loss_limit")
            return False, f"🚫 Daily loss limit hit ({loss_pct:.1f}% < -{self.limits['max_daily_loss_pct']}%)"
        
        # 4. Check consecutive losses
        if self.daily_stats["consecutive_losses"] >= self.limits["consecutive_loss_limit"]:
            self._trigger_auto_pause("consecutive_losses")
            return False, f"🚫 Too many losses in a row ({self.daily_stats['consecutive_losses']})"
        
        # 5. Check position limit
        if current_positions >= self.limits["max_open_positions"]:
            return False, f"🚫 Max positions reached ({current_positions}/{self.limits['max_open_positions']})"
        
        # 6. Check market panic (VIX)
        if vix > self.limits["vix_panic_threshold"]:
            return False, f"🚫 Market panic mode (VIX={vix:.1f} > {self.limits['vix_panic_threshold']})"
        
        # 7. Check market crash (SPY)
        if spy_change < self.limits["spy_crash_threshold"]:
            return False, f"🚫 Market crashing (SPY {spy_change:.1f}% < {self.limits['spy_crash_threshold']}%)"
        
        # 8. Check trading hours
        if not self._is_valid_trading_time():
            return False, "🚫 Outside valid trading hours (avoid first/last 15min)"
        
        # All checks passed
        return True, "✅ Risk checks passed"
    
    def calculate_position_size(self, account_value: float, buying_power: float) -> int:
        """
        Calculate safe position size based on account value
        Returns: Number of contracts to trade (usually 1)
        """
        max_size = self.limits["max_position_size_usd"]
        
        # Ensure we have enough buying power
        if buying_power < max_size:
            return 0
        
        # For options, typically trade 1 contract at a time
        # Each contract = 100 shares, so cost varies by strike price
        return 1
    
    def record_trade_outcome(self, pnl: float):
        """
        Update daily stats after a trade closes
        """
        self.daily_stats["trades_today"] += 1
        self.daily_stats["pnl_today"] += pnl
        
        if pnl < 0:
            self.daily_stats["consecutive_losses"] += 1
        else:
            self.daily_stats["consecutive_losses"] = 0
    
    def _reset_if_new_day(self):
        """Reset counters at start of new trading day"""
        today = datetime.now().date()
        if self.daily_stats["last_reset"] != today:
            self.daily_stats = {
                "trades_today": 0,
                "pnl_today": 0.0,
                "consecutive_losses": 0,
                "last_reset": today
            }
    
    def _is_kill_switch_active(self) -> bool:
        """Check if manual kill switch file exists"""
        kill_switch_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "STOP_TRADING.txt")
        pause_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "TRADING_PAUSED.txt")
        return os.path.exists(kill_switch_path) or os.path.exists(pause_path)
    
    def _trigger_auto_pause(self, reason: str):
        """Create pause file to halt trading"""
        pause_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "TRADING_PAUSED.txt")
        with open(pause_path, 'w') as f:
            f.write(f"Auto-paused: {reason}\n")
            f.write(f"Time: {datetime.now()}\n")
            f.write(f"To resume: Delete this file\n")
        print(f"⚠️  AUTO-PAUSE TRIGGERED: {reason}")
    
    def _is_valid_trading_time(self) -> bool:
        """Check if current time is within safe trading hours"""
        now = datetime.now().time()
        
        # Market hours: 9:30 AM - 4:00 PM ET
        # Safe window: 9:45 AM - 3:45 PM ET (avoiding first/last 15min)
        market_open = time(9, 45)  # 9:45 AM
        market_close = time(15, 45)  # 3:45 PM
        
        # Note: This assumes system clock is in ET
        # For production, should convert to ET timezone
        return market_open <= now <= market_close
    
    def get_risk_summary(self) -> Dict:
        """Get current risk status for dashboard"""
        return {
            "trades_today": self.daily_stats["trades_today"],
            "pnl_today": self.daily_stats["pnl_today"],
            "consecutive_losses": self.daily_stats["consecutive_losses"],
            "kill_switch_active": self._is_kill_switch_active(),
            "limits": self.limits
        }
