import threading
import os
import sys
import logging
from functools import wraps
from flask import Flask, send_from_directory, jsonify, session, request, redirect, url_for, render_template_string
from waitress import serve
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_talisman import Talisman

# Add Flask to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from strategy_lab.runner import main as run_bot

app = Flask(__name__, static_folder='.')

# --- SECURITY CONFIGURATION ---
app.secret_key = os.urandom(24)
AUTH_PASSCODE = "EarninCeo"

# Brute-force protection
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["1000 per day", "100 per hour"],
    storage_uri="memory://"
)

# Security Headers (HTTPS, CSP, etc.)
# force_https=False because Railway handles SSL termination. Setting True causes redirect loops.
Talisman(app, content_security_policy=None, force_https=False)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("RailwayServer")

# --- AUTHENTICATION DECORATOR ---
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Allow API access with header
        if request.headers.get('X-Passcode') == AUTH_PASSCODE:
            return f(*args, **kwargs)
            
        # Standard Session Auth
        if not session.get('authenticated'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

from strategy_lab.scoreboard import ScoreKeeper

@app.route('/api/stats')
@login_required
def api_stats():
    try:
        keeper = ScoreKeeper()
        stats = keeper.get_strategy_stats()
        return jsonify({
            "status": "success", 
            "strategies": stats,
            "summary": {
                "total_pnl": sum(s['total_pnl'] for s in stats),
                "active_count": len([s for s in stats if s['status'] == 'ACTIVE'])
            }
        })
    except Exception as e:
        logger.error(f"API Error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

from trading_architect import AlphaVantageEngine

@app.route('/api/scan')
@login_required
def api_scan():
    """Run a market scan for a specific list of tickers."""
    try:
        # In a real app, this list might come from a DB or config
        watchlist = ["AMD", "NVDA", "SPY", "QQQ", "TSLA"]
        results = []
        
        # We need an API Key. Ideally from env var, defaulting for safety.
        api_key = os.environ.get("ALPHA_VANTAGE_KEY", "POPZN5W6J3DCL2WE")
        engine = AlphaVantageEngine(api_key=api_key)
        
        for symbol in watchlist:
            forecast = engine.get_consensus_forecast(symbol)
            if forecast['decision'] == 'BUY':
                results.append(forecast)
                
        return jsonify({
            "status": "success",
            "signals": results,
            "count": len(results)
        })
    except Exception as e:
        logger.error(f"Scan API Error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/analysis/recent_losses')
@login_required
def api_analysis_losses():
    """Return details of recent losing trades for AI analysis."""
    try:
        import sqlite3
        conn = sqlite3.connect('data_lake.db')
        c = conn.cursor()
        
        # Fetch last 5 losing trades with strategy info
        c.execute('''
            SELECT 
                t.symbol, t.strategy_id, t.entry_price, t.exit_price, t.pnl, t.entry_date
            FROM trades t
            WHERE t.pnl < 0 AND t.status = 'CLOSED'
            ORDER BY t.exit_date DESC
            LIMIT 5
        ''')
        
        losses = []
        columns = [desc[0] for desc in c.description]
        
        for row in c.fetchall():
            losses.append(dict(zip(columns, row)))
            
        conn.close()
        
        return jsonify({
            "status": "success",
            "recent_losses": losses,
            "context": "Analyze these trades to find common failure patterns (e.g., specific symbols or market conditions)."
        })
    except Exception as e:
        logger.error(f"Analysis API Error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

# --- ROUTES ---

@app.route('/login', methods=['GET', 'POST'])
@limiter.limit("5 per minute")  # Prevent brute force
def login():
    error = None
    if request.method == 'POST':
        passcode = request.form.get('passcode')
        if passcode == AUTH_PASSCODE:
            session['authenticated'] = True
            logger.info(f"✅ Successful login from {request.remote_addr}")
            return redirect(url_for('home'))
        else:
            logger.warning(f"❌ Failed login attempt from {request.remote_addr}")
            error = "Access Denied: Invalid Passcode"
    
    # Return the login page
    return send_from_directory('.', 'login.html')

@app.route('/logout')
def logout():
    session.pop('authenticated', None)
    return redirect(url_for('login'))

@app.route('/')
@login_required
def home():
    """Serve the main dashboard (protected)"""
    return send_from_directory('.', 'index.html')

@app.route('/<path:path>')
def send_static(path):
    """Serve static files (css, js, html)"""
    # Allow login.html and static assets to load without auth checks if needed, 
    # but generally we want to protect the core JS that has logic.
    # For now, we only strictly protect the root route to be user-friendly.
    return send_from_directory('.', path)

@app.route('/health')
def health():
    return jsonify({"status": "healthy", "service": "strategy-lab"})

def start_bot_thread():
    """Run the bot in a background thread"""
    logger.info("🚀 Starting Strategy Lab Bot in Background Thread...")
    
    # Simulate command line arguments for the bot
    sys.argv = ["runner.py", "--live", "--auto-trade"]
    
    try:
        run_bot()
    except Exception as e:
        logger.error(f"❌ Bot crashed: {e}")

# Start the bot thread immediately on import
if not any(t.name == "BotThread" for t in threading.enumerate()):
    t = threading.Thread(target=start_bot_thread, name="BotThread")
    t.daemon = True
    t.start()
    logger.info("✅ Bot thread started")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    logger.info(f"🔌 Starting Waitress Server on 0.0.0.0:{port}...")
    serve(app, host='0.0.0.0', port=port)
