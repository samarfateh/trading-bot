#!/bin/bash

# Navigate to the script's directory
cd "$(dirname "$0")"

# Aesthetics
clear
echo -e "\033[34m" # Blue Text
echo "==========================================="
echo "   📊 STRATEGY LAB: DASHBOARD SERVER   "
echo "==========================================="
echo -e "\033[0m"

echo "🌐 Starting web server on port 8000..."
echo "📱 Opening dashboard in browser..."
echo ""
echo "Dashboard URL: http://localhost:8000"
echo ""
echo "⚠️  Keep this window open while using the dashboard"
echo "Press CTRL+C to stop the server"
echo ""

# Open browser after a short delay
sleep 2 && open http://localhost:8000 &

# Start Python web server
python3 -m http.server 8000
