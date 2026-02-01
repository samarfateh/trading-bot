import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from strategy_lab.data.yfinance_engine import YFinanceEngine
from strategy_lab.market_features import MarketFeatureEngine
from strategy_lab.judge import TheJudge
from strategy_lab.scanner import StrategyScanner
from strategy_lab.core import StrategyValidator
import sqlite3
import json
from datetime import datetime, timedelta
import yfinance as yf

class HistoricalBacktester:
    """
    Time Machine: Simulates what the bot would have recommended
    over the past 6 months and stores it as a learning dataset.
    """
    
    def __init__(self, db_path="data_lake.db"):
        self.db_path = db_path
        self._init_backtest_db()
        
    def _init_backtest_db(self):
        """Create backtest history table"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute('''
            CREATE TABLE IF NOT EXISTS backtest_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                symbol TEXT,
                price REAL,
                day_high REAL,
                day_low REAL,
                volume INTEGER,
                iv REAL,
                vix REAL,
                spy_trend TEXT,
                sector_trend TEXT,
                verdict TEXT,
                recommended_strategy TEXT,
                strategy_direction TEXT,
                confidence REAL,
                outcome_1d REAL,
                outcome_3d REAL,
                outcome_7d REAL,
                market_regime TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
        print("✅ Backtest database initialized")
        
    def fetch_historical_macro(self, date):
        """Fetch VIX and SPY trend for a specific historical date"""
        try:
            # Get VIX
            vix = yf.Ticker("^VIX")
            vix_df = vix.history(start=date - timedelta(days=5), end=date + timedelta(days=1))
            current_vix = float(vix_df['Close'].iloc[-1]) if not vix_df.empty else 20.0
            
            # Get SPY trend
            spy = yf.Ticker("SPY")
            spy_df = spy.history(start=date - timedelta(days=250), end=date + timedelta(days=1))
            
            if len(spy_df) >= 200:
                spy_closes = spy_df['Close'].tolist()
                spy_sma200 = sum(spy_closes[-200:]) / 200
                current_spy = spy_closes[-1]
                spy_trend = "BULLISH" if current_spy > spy_sma200 else "BEARISH"
            else:
                spy_trend = "BULLISH"
                
            return {"vix": current_vix, "spy_trend": spy_trend}
        except Exception as e:
            print(f"⚠️  Macro fetch error for {date}: {e}")
            return {"vix": 20.0, "spy_trend": "BULLISH"}
    
    def run_backtest(self, symbol="AMD", months=6):
        """
        Main backtest loop: Go back 6 months and simulate daily decisions
        """
        print(f"\n🕰️  Starting Historical Backtest ({months} months)")
        print(f"Symbol: {symbol}")
        print("=" * 50)
        
        # Fetch historical data
        ticker = yf.Ticker(symbol)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=months * 30)
        
        print(f"Date Range: {start_date.strftime('%Y-%m-%d')} → {end_date.strftime('%Y-%m-%d')}")
        print("Fetching historical data...")
        
        # Get daily data
        daily_df = ticker.history(start=start_date, end=end_date, interval="1d")
        
        if daily_df.empty:
            print("❌ No historical data found")
            return
            
        print(f"✅ Loaded {len(daily_df)} trading days")
        
        # Load strategies
        validator = StrategyValidator()
        library_path = os.path.join(os.path.dirname(__file__), "library")
        strategies = validator.load_library(library_path)
        print(f"✅ Loaded {len(strategies)} strategies")
        
        # Process each day
        decisions_count = 0
        
        for idx in range(len(daily_df) - 7):  # Leave 7 days for outcome calculation
            date = daily_df.index[idx]
            row = daily_df.iloc[idx]
            
            # Build snapshot (simplified - using daily data)
            current_price = float(row['Close'])
            day_high = float(row['High'])
            day_low = float(row['Low'])
            volume = int(row['Volume'])
            
            # Estimate IV (simplified - using historical volatility as proxy)
            if idx >= 20:
                returns = daily_df['Close'].pct_change().iloc[idx-20:idx]
                historical_vol = float(returns.std() * (252 ** 0.5))  # Annualized
                current_iv = min(historical_vol, 2.0)  # Cap at 200%
            else:
                current_iv = 0.50
                
            # Fetch macro context for this date
            macro = self.fetch_historical_macro(date)
            
            # Build simplified snapshot
            snapshot = {
                "symbol": symbol,
                "current_price": current_price,
                "day_high": day_high,
                "day_low": day_low,
                "volume": volume,
                "current_iv": current_iv,
                "closes": daily_df['Close'].iloc[max(0, idx-100):idx+1].tolist(),
                "htf_closes": daily_df['Close'].iloc[max(0, idx-50):idx+1].tolist(),
                "sma_200": float(daily_df['Close'].iloc[max(0, idx-200):idx+1].mean()),
                "sector_closes": []  # Skip QQQ for performance
            }
            
            # Run analysis
            try:
                features = MarketFeatureEngine.analyze_snapshot(snapshot)
                verdict = TheJudge.delimit_verdict(features, macro=macro)
                
                scanner = StrategyScanner()
                signals = scanner.scan(strategies, snapshot)
                
                best_strategy = signals[0] if signals else None
                
                # Calculate outcomes (what happened next)
                outcome_1d = float(((daily_df['Close'].iloc[idx+1] - current_price) / current_price) * 100)
                outcome_3d = float(((daily_df['Close'].iloc[idx+3] - current_price) / current_price) * 100)
                outcome_7d = float(((daily_df['Close'].iloc[idx+7] - current_price) / current_price) * 100)
                
                # Determine market regime
                if outcome_7d > 3:
                    regime = "BULL_RUN"
                elif outcome_7d < -3:
                    regime = "BEAR_CRASH"
                else:
                    regime = "SIDEWAYS"
                    
                # Store decision
                self._store_decision(
                    timestamp=date.strftime("%Y-%m-%d %H:%M:%S"),  # Convert pandas Timestamp to string
                    symbol=symbol,
                    price=current_price,
                    day_high=day_high,
                    day_low=day_low,
                    volume=volume,
                    iv=current_iv,
                    vix=macro['vix'],
                    spy_trend=macro['spy_trend'],
                    sector_trend=features.get('sector_trend', 'UNKNOWN'),
                    verdict=verdict,
                    recommended_strategy=best_strategy['strategy_name'] if best_strategy else None,
                    strategy_direction=best_strategy['direction'] if best_strategy else None,
                    confidence=85 if best_strategy else 0,  # Simplified
                    outcome_1d=outcome_1d,
                    outcome_3d=outcome_3d,
                    outcome_7d=outcome_7d,
                    market_regime=regime
                )
                
                decisions_count += 1
                
                if decisions_count % 10 == 0:
                    print(f"  Processed {decisions_count} days... (Latest: {date.strftime('%Y-%m-%d')})")
                    
            except Exception as e:
                print(f"⚠️  Error processing {date}: {e}")
                continue
                
        print(f"\n✅ Backtest Complete!")
        print(f"Total Decisions Recorded: {decisions_count}")
        print(f"Database: {self.db_path}")
        
    def _store_decision(self, **kwargs):
        """Store a historical decision point"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute('''
            INSERT INTO backtest_history (
                timestamp, symbol, price, day_high, day_low, volume,
                iv, vix, spy_trend, sector_trend, verdict,
                recommended_strategy, strategy_direction, confidence,
                outcome_1d, outcome_3d, outcome_7d, market_regime
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            kwargs['timestamp'],
            kwargs['symbol'],
            kwargs['price'],
            kwargs['day_high'],
            kwargs['day_low'],
            kwargs['volume'],
            kwargs['iv'],
            kwargs['vix'],
            kwargs['spy_trend'],
            kwargs['sector_trend'],
            kwargs['verdict'],
            kwargs['recommended_strategy'],
            kwargs['strategy_direction'],
            kwargs['confidence'],
            kwargs['outcome_1d'],
            kwargs['outcome_3d'],
            kwargs['outcome_7d'],
            kwargs['market_regime']
        ))
        
        conn.commit()
        conn.close()
        
    def get_insights(self):
        """Analyze the backtest results"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        print("\n📊 BACKTEST INSIGHTS")
        print("=" * 50)
        
        # Total decisions
        c.execute("SELECT COUNT(*) FROM backtest_history")
        total = c.fetchone()[0]
        print(f"Total Historical Decisions: {total}")
        
        # Strategy performance
        print("\n🎯 Strategy Win Rates (7-day outcomes):")
        c.execute('''
            SELECT recommended_strategy, 
                   COUNT(*) as times_recommended,
                   AVG(outcome_7d) as avg_outcome,
                   SUM(CASE WHEN outcome_7d > 0 THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as win_rate
            FROM backtest_history
            WHERE recommended_strategy IS NOT NULL
            GROUP BY recommended_strategy
            ORDER BY win_rate DESC
        ''')
        
        for row in c.fetchall():
            strat, count, avg_outcome, win_rate = row
            print(f"  {strat}: {win_rate:.1f}% wins | Avg: {avg_outcome:+.2f}% | Used {count}x")
            
        # Market regime analysis
        print("\n🌍 Market Regime Distribution:")
        c.execute('''
            SELECT market_regime, COUNT(*) as days
            FROM backtest_history
            GROUP BY market_regime
        ''')
        
        for row in c.fetchall():
            regime, days = row
            print(f"  {regime}: {days} days")
            
        # IV effectiveness
        print("\n⚡ High IV Block Effectiveness:")
        c.execute('''
            SELECT 
                COUNT(*) as times_blocked,
                AVG(outcome_7d) as avg_market_move
            FROM backtest_history
            WHERE verdict LIKE '%expensive%' OR verdict LIKE '%BLOCKED%'
        ''')
        
        row = c.fetchone()
        if row[0] > 0:
            print(f"  Blocked {row[0]} times | Avg market move: {row[1]:+.2f}%")
            print(f"  (Negative = correctly avoided drops)")
            
        conn.close()

if __name__ == "__main__":
    print("🚀 Historical Backtest Runner")
    print("Building 6-month learning dataset...\n")
    
    backtester = HistoricalBacktester()
    backtester.run_backtest(symbol="AMD", months=6)
    backtester.get_insights()
    
    print("\n✅ Learning dataset ready for AI training!")
