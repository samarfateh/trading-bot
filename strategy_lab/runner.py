import sys
import os
import json
import logging
import time
import argparse
import requests
from datetime import datetime
from typing import Dict, List, Any

# Add parent dir to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from strategy_lab.data.yfinance_engine import YFinanceEngine
from strategy_lab.paper_trader import PaperTrader
from strategy_lab.core import StrategyValidator
from strategy_lab.scanner import StrategyScanner
from strategy_lab.market_features import MarketFeatureEngine
from strategy_lab.judge import TheJudge
from strategy_lab.social_sentiment import RedditEngine
from strategy_lab.history_helper import get_backtest_history, get_backtest_stats

# Auto-Trading Modules
from strategy_lab.risk_manager import RiskManager
from strategy_lab.kill_switch import KillSwitch
from strategy_lab.config import AUTO_TRADE_ENABLED, DRY_RUN_MODE
try:
    from strategy_lab.alpaca_broker import AlpacaBroker, DryRunBroker
    ALPACA_AVAILABLE = True
except ImportError:
    ALPACA_AVAILABLE = False
    print("⚠️  Alpaca SDK not available (auto-trading disabled)")

DISCORD_WEBHOOK = 'https://discord.com/api/webhooks/1467339178701230122/MnWqFuFNUTO4HGMHfZA7eQEsZFjdGvUWIdA-WMb_jqiFVEtNkWpA85d93QaZ8FR6HkB2' 

# Global State
LAST_ALERT = {"strategy": None, "time": 0}

def send_discord_alert(bet, verdict):
    if not DISCORD_WEBHOOK: return

    color = 5763719 # Green
    if bet['direction'] == 'BEARISH': color = 15548997 # Red

    embed = {
        "title": f"🤖 AI SIGNAL: {bet['strategy_name']}",
        "description": f"**Direction:** {bet['direction']}\n**Target:** ${bet['prediction']['target_price']}\n**Verdict:** {verdict}\n**Confidence:** {bet['prediction']['confidence']}%",
        "color": color,
        "footer": {"text": "Strategy Lab Consultant"}
    }
    
    try:
        requests.post(DISCORD_WEBHOOK, json={"embeds": [embed]})
        print(f"Sent Discord Alert for {bet['strategy_name']}")
    except Exception as e:
        print(f"Failed to send alert: {e}")

def send_trade_opened_alert(trade, entry_price, context):
    """Send Discord alert when a trade is opened"""
    if not DISCORD_WEBHOOK:
        return
    
    embed = {
        "title": f"🟢 TRADE OPENED: {trade['strategy_name']}",
        "description": f"**Symbol:** {context.get('symbol', 'AMD')}\n**Direction:** {trade['direction']}\n**Entry Price:** ${entry_price:.2f}\n**Confidence:** {trade.get('prediction', {}).get('confidence', 85)}%",
        "color": 5763719,  # Green
        "fields": [
            {"name": "IV", "value": f"{context.get('current_iv', 0)*100:.0f}%", "inline": True},
            {"name": "VIX", "value": f"{context.get('vix', 0):.1f}", "inline": True},
            {"name": "Trend", "value": context.get('spy_trend', 'UNKNOWN'), "inline": True}
        ],
        "footer": {"text": "Strategy Lab • Paper Trading"}
    }
    
    try:
        requests.post(DISCORD_WEBHOOK, json={"embeds": [embed]})
        print(f"📤 Discord: Trade opened notification sent")
    except Exception as e:
        print(f"Failed to send trade opened alert: {e}")

def send_trade_closed_alert(trade, exit_price, pnl, pnl_pct):
    """Send Discord alert when a trade is closed"""
    if not DISCORD_WEBHOOK:
        return
    
    is_win = pnl > 0
    color = 5763719 if is_win else 15548997  # Green or Red
    status_emoji = "✅" if is_win else "❌"
    
    embed = {
        "title": f"{'📈' if is_win else '📉'} TRADE CLOSED: {trade.get('strategy_id', 'Unknown')}",
        "description": f"**Entry:** ${trade.get('entry_price', 0):.2f}\n**Exit:** ${exit_price:.2f}\n**P&L:** ${pnl:.2f} ({pnl_pct:+.2f}%)\n**Status:** {status_emoji} {'WIN' if is_win else 'LOSS'}",
        "color": color,
        "footer": {"text": "Strategy Lab • Paper Trading"}
    }
    
    try:
        requests.post(DISCORD_WEBHOOK, json={"embeds": [embed]})
        print(f"📤 Discord: Trade closed notification sent")
    except Exception as e:
        print(f"Failed to send trade closed alert: {e}")

def send_daily_summary(portfolio_stats):
    """Send daily P&L summary to Discord"""
    if not DISCORD_WEBHOOK:
        return
    
    total_pnl = portfolio_stats.get('total_pnl', 0)
    win_rate = portfolio_stats.get('win_rate', 0)
    total_trades = portfolio_stats.get('total_trades', 0)
    open_trades = len(portfolio_stats.get('open_trades', []))
    
    color = 5763719 if total_pnl >= 0 else 15548997
    
    embed = {
        "title": "📊 DAILY REPORT",
        "description": f"**Total P&L:** ${total_pnl:.2f}\n**Win Rate:** {win_rate:.1f}%\n**Total Trades:** {total_trades}\n**Open Positions:** {open_trades}",
        "color": color,
        "footer": {"text": f"Strategy Lab • {datetime.now().strftime('%Y-%m-%d')}"}
    }
    
    try:
        requests.post(DISCORD_WEBHOOK, json={"embeds": [embed]})
        print(f"📤 Discord: Daily summary sent")
    except Exception as e:
        print(f"Failed to send daily summary: {e}")

def send_risk_alert(reason):
    """Send Discord alert when risk limits are hit"""
    if not DISCORD_WEBHOOK:
        return
    
    embed = {
        "title": "⚠️ RISK LIMIT HIT",
        "description": f"**Reason:** {reason}\n**Action:** Trading auto-paused\n**Recovery:** Delete TRADING_PAUSED.txt to resume",
        "color": 15105570,  # Orange
        "footer": {"text": "Strategy Lab • Risk Manager"}
    }
    
    try:
        requests.post(DISCORD_WEBHOOK, json={"embeds": [embed]})
        print(f"📤 Discord: Risk alert sent")
    except Exception as e:
        print(f"Failed to send risk alert: {e}")

def check_and_send_alert(bet, verdict):
    """
    Smart Deduplication: Only alert if new strategy or > 30 mins since last.
    """
    if not bet or not DISCORD_WEBHOOK:
        return
    
    global LAST_ALERT
    now = time.time()
    
    # Logic: Alert if it's a NEW strategy OR it's been > 30 mins
    is_new_strat = bet['strategy_name'] != LAST_ALERT['strategy']
    is_timeout = (now - LAST_ALERT['time']) > 1800 # 30 mins

    if is_new_strat or is_timeout:
        clean_verdict = verdict.replace("VERDICT: ", "")
        send_discord_alert(bet, clean_verdict)
        
        # Update State
        LAST_ALERT['strategy'] = bet['strategy_name']
        LAST_ALERT['time'] = now
    else:
        print(f"Skipping Duplicate Alert (Last Sent: {int(now - LAST_ALERT['time'])}s ago)")

def run_cycle(engine, strategies, symbol="AMD", auto_trade=False, broker=None, risk_mgr=None, kill_switch=None):
    print(f"\n--- ⏳ Scan Cycle: {datetime.now().strftime('%H:%M:%S')} ---")
    
    # 0. Kill Switch Check (Safety First)
    if kill_switch and kill_switch.is_trading_halted():
        reason = kill_switch.get_halt_reason()
        print(f"🛑 TRADING HALTED: {reason}")
        print("⏩ Monitoring only mode (no execution)")
        auto_trade = False  # Override to monitoring mode
    
    # --- DATA PHASE (UNLIMITED FUEL) ---
    # 1. Macro Sixth Sense (Safety First)
    macro = engine.fetch_macro_stats()
    vix = macro.get('vix', 0)
    spy_change = macro.get('spy_change', 0)
    print(f"🌍 Macro Check: SPY={macro['spy_trend']} | VIX={vix:.2f} ({'PANIC' if vix>30 else 'SAFE'})")

    print(f"⚡ Fetching Market Data (YFinance)...")
    
    snapshot = engine.fetch_snapshot(symbol)
    if not snapshot or not snapshot.get("closes"):
        print("❌ Data Fetch Failed. Retrying next cycle.")
        return

    closes = snapshot["closes"]
    print(f"✅ Data Acquired: {len(closes)} candles. Price: ${snapshot.get('current_price', 0):.2f}")

    # 4. Social Sentiment
    print("Scraping Reddit Sentiment...")
    hype_data = RedditEngine.fetch_hype(symbol)
    print(f"Reddit Hype: {hype_data['score']}/100 ({hype_data['direction']})")
    snapshot['sentiment'] = hype_data

    # 0. Self-Learning (Reflection)
    # Check if any open trades need closing
    pt = PaperTrader()
    if closes:
        pt.update_positions(closes[-1])

    # 5. Analysis
    # 5. Analysis
    features = MarketFeatureEngine.analyze_snapshot(snapshot)
    verdict = TheJudge.delimit_verdict(features, macro=macro)
    
    print(f"--- 👨‍⚖️ The Judge: {verdict}")
    
    scanner = StrategyScanner()
    signals = scanner.scan(strategies, snapshot)
    
    # Get Stats
    portfolio = pt.get_portfolio_stats()

    # 6. AI Selection & Auto-Trading Logic
    best_bet = None
    if signals and "BLOCKED" not in verdict: # Safety Check
        best_bet = signals[0] 
        
        daily_move_pct = (0.45 / 16) * 100 
        target_price = closes[-1] * (1 + (daily_move_pct/100)) if best_bet['direction'] == 'BULLISH' else closes[-1] * (1 - (daily_move_pct/100))
        
        best_bet["prediction"] = {
            "move_pct": round(daily_move_pct, 1),
            "target_price": round(target_price, 2),
            "confidence": 85 
        }
        
        # Trigger Smart Alert & Trade Execution
        check_and_send_alert(best_bet, verdict)
        
        # Auto-Trade High Confidence
        if best_bet["prediction"]["confidence"] >= 80:
             is_open = any(t['strategy_id'] == best_bet['strategy_name'] for t in portfolio['open_trades'])
             if not is_open:
                 print(f"📝 Opening Paper Trade: {best_bet['strategy_name']}")
                 # Context: Signal + Macro
                 context_lite = {k: v for k, v in snapshot.items() if k not in ['closes', 'htf_closes', 'sector_closes']}
                 context_lite.update(macro)
                 pt.open_trade(best_bet, closes[-1], context=context_lite)
                 
                 # Send Discord notification for trade opened
                 send_trade_opened_alert(best_bet, closes[-1], context_lite)
                 
                 # REAL BROKER EXECUTION (if enabled)
                 if auto_trade and broker and risk_mgr:
                     print("\n🤖 AUTO-TRADE MODE: Evaluating execution...")
                     
                     # Get account info
                     account = broker.get_account()
                     if account:
                         account_value = account.get('portfolio_value', 0)
                         buying_power = account.get('buying_power', 0)
                         current_positions = len(broker.get_open_positions())
                         
                         # Risk Manager Check
                         can_trade, reason = risk_mgr.can_trade(
                             account_value=account_value,
                             current_positions=current_positions,
                             vix=vix,
                             spy_change=spy_change
                         )
                         
                         if can_trade:
                             # Calculate safe position size
                             qty = risk_mgr.calculate_position_size(account_value, buying_power)
                             
                             if qty > 0:
                                 # Submit order
                                 side = "BUY" if best_bet['direction'] == 'BULLISH' else "SELL"
                                 order_id = broker.submit_market_order(symbol, qty, side)
                                 
                                 if order_id:
                                     print(f"✅ TRADE EXECUTED: {side} {qty} {symbol} (Order: {order_id})")
                                 else:
                                     print(f"❌ Order submission failed")
                             else:
                                 print(f"⚠️  Position size = 0 (insufficient buying power)")
                         else:
                             print(f"🚫 Trade blocked by risk manager: {reason}")
                     else:
                         print("❌ Failed to fetch account info")


    # 7. Export
    market_stats = {
        "price": round(snapshot.get("current_price", 0), 2),
        "change_pct": round(snapshot.get("change_pct", 0), 2),
        "day_high": round(snapshot.get("day_high", 0), 2),
        "day_low": round(snapshot.get("day_low", 0), 2),
        "volume": int(snapshot.get("volume", 0)),  # Convert numpy int64 to Python int
        "panic_score": round(snapshot.get("current_iv", 0), 2),
        "vix": round(macro.get('vix', 0), 2),
        "spy_trend": macro.get('spy_trend', 'Unknown')
    }

    
    # 8. Fetch Backtest History (for History Lab UI)
    try:
        backtest_history = get_backtest_history(limit=50)  # Last 50 decisions
        backtest_stats = get_backtest_stats()
    except:
        backtest_history = []
        backtest_stats = {'total_decisions': 0, 'strategies': [], 'regimes': {}}
    
    output_data = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "symbol": symbol,
        "market_stats": market_stats,
        "signals": signals,
        "portfolio": portfolio, 
        "best_bet": best_bet,
        "judge_verdict": verdict,
        "backtest_history": backtest_history,
        "backtest_stats": backtest_stats
    }
    
    js_content = f"window.STRATEGY_DATA = {json.dumps(output_data, indent=2)};"
    try:
        js_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'js', 'strategy_data.js')
        with open(js_path, 'w') as f:
            f.write(js_content)
        print("UI Updated.")
    except Exception as e:
        print(f"Export Failed: {e}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--live", action="store_true", help="Run in continuous loop")
    parser.add_argument("--auto-trade", action="store_true", help="Enable auto-trading (requires Alpaca keys)")
    parser.add_argument("--dry-run", action="store_true", help="Dry-run mode (log orders without executing)")
    args = parser.parse_args()

    print("--- Strategy Lab: Learning Layer ---")
    library_path = os.path.join(os.path.dirname(__file__), 'library')
    strategies = StrategyValidator.load_library(library_path)
    print(f"Loaded {len(strategies)} strategies.")

    engine = YFinanceEngine()
    
    # Initialize Auto-Trading Components (if enabled)
    broker = None
    risk_mgr = None
    kill_switch = KillSwitch()
    auto_trade = False
    
    if args.auto_trade or args.dry_run:
        print("\n🤖 AUTO-TRADING MODE")
        risk_mgr = RiskManager()
        
        if args.dry_run:
            broker = DryRunBroker()
            auto_trade = True
            print("🔷 Dry-run enabled (orders will be logged, not executed)")
        else:
            if not ALPACA_AVAILABLE:
                print("❌ Alpaca SDK not installed. Run: pip install alpaca-py")
                return
            
            # Check for .env configuration
            if not os.path.exists(".env"):
                print("❌ .env file not found! Copy .env.example and add your Alpaca keys.")
                print("   Get free paper trading keys at: https://alpaca.markets")
                return
            
            try:
                broker = AlpacaBroker(paper_trading=True)
                auto_trade = True
                print("✅ Connected to Alpaca Paper Trading")
                
                # Show account status
                account = broker.get_account()
                if account:
                    print(f"💼 Account Value: ${account['portfolio_value']:,.2f}")
                    print(f"💵 Buying Power: ${account['buying_power']:,.2f}")
            except Exception as e:
                print(f"❌ Failed to connect to Alpaca: {e}")
                print("   Check your .env file and API keys")
                return
        
        # Show kill switch status
        if kill_switch.is_trading_halted():
            print(f"🛑 Kill Switch Active: {kill_switch.get_halt_reason()}")
        else:
            print("✅ Kill Switch: Ready (create STOP_TRADING.txt to halt)")
    
    if args.live:
        print("🚀 LIVE MODE ACTIVATED. Auto-Pilot engaged.")
        while True:
            try:
                run_cycle(engine, strategies, auto_trade=auto_trade, broker=broker, risk_mgr=risk_mgr, kill_switch=kill_switch)
                print("Waiting 60s for next scan...")
                time.sleep(60)
            except KeyboardInterrupt:
                print("\nStopping Live Mode.")
                break
            except Exception as e:
                print(f"Cycle Error: {e}")
                time.sleep(60)
    else:
        run_cycle(engine, strategies, auto_trade=auto_trade, broker=broker, risk_mgr=risk_mgr, kill_switch=kill_switch)

if __name__ == "__main__":
    main()
