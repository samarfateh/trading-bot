# Trading Configuration
# IMPORTANT: Keep risk limits conservative for paper trading learning

RISK_LIMITS = {
    # Position Sizing
    "max_position_size_usd": 100,  # Maximum $ per trade
    "max_portfolio_pct_per_position": 0.25,  # Max 25% of portfolio in one position
    "max_open_positions": 5,  # Maximum concurrent trades
    
    # Daily Limits
    "max_daily_loss_pct": 5,  # Auto-pause if lose 5% in one day
    "max_trades_per_day": 10,  # Prevent overtrading
    "consecutive_loss_limit": 3,  # Pause after 3 losses in a row
    
    # Market Condition Filters
    "vix_panic_threshold": 40,  # No trading if VIX > 40
    "spy_crash_threshold": -3,  # Exit all if SPY drops >3% intraday
    "min_buying_power_pct": 20,  # Keep 20% cash reserve
    
    # Time-Based Rules
    "market_open_buffer_mins": 15,  # No trading first 15min
    "market_close_buffer_mins": 15,  # No trading last 15min
}

# Trading Modes
AUTO_TRADE_ENABLED = False  # Set to True to enable live execution
DRY_RUN_MODE = True  # Log orders but don't submit (for testing)

# Alpaca Settings (loaded from .env for security)
ALPACA_PAPER_TRADING = True  # NEVER set to False without explicit user action
