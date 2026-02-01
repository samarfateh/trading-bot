import threading
import os
import sys
import logging
from flask import Flask, send_from_directory, jsonify
from waitress import serve

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
