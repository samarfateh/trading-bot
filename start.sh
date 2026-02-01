#!/bin/bash

# Start the trading bot in the background
echo "🚀 Starting Strategy Lab Bot..."
python3 strategy_lab/runner.py --live --auto-trade &

# Start the web server in the foreground
# The web server just serves the static files that the bot updates
echo "🌍 Starting Web Dashboard..."
gunicorn app:app --workers 1 --log-file - --bind 0.0.0.0:$PORT
