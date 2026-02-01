import threading
import os
import sys
import logging
from flask import Flask, send_from_directory, jsonify

# Add Flask to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from strategy_lab.runner import main as run_bot

app = Flask(__name__, static_folder='.')

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("RailwayServer")

@app.route('/')
def home():
    """Serve the main dashboard"""
    return send_from_directory('.', 'index.html')

@app.route('/<path:path>')
def send_static(path):
    """Serve static files (css, js, html)"""
    return send_from_directory('.', path)

@app.route('/health')
def health():
    return jsonify({"status": "healthy", "service": "strategy-lab"})

def start_bot_thread():
    """Run the bot in a background thread"""
    logger.info("🚀 Starting Strategy Lab Bot in Background Thread...")
    
    # Simulate command line arguments for the bot
    # We force --live and --auto-trade for the cloud instance
    # The bot handles the logic of checking keys/safety itself
    sys.argv = ["runner.py", "--live", "--auto-trade"]
    
    try:
        run_bot()
    except Exception as e:
        logger.error(f"❌ Bot crashed: {e}")

# Start the bot thread when the app starts (only in the main process)
if os.environ.get("WERKZEUG_RUN_MAIN") != "true":
    t = threading.Thread(target=start_bot_thread)
    t.daemon = True
    t.start()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
