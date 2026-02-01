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
        if not session.get('authenticated'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

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
