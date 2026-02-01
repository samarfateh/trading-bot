#!/bin/bash

# Navigate to the script's directory (assuming script is in root of project)
cd "$(dirname "$0")"

# Aesthetics
clear
echo -e "\033[32m" # Green Text
echo "==========================================="
echo "   🧬 STRATEGY LAB: ARTIFICIAL INTELLIGENCE   "
echo "==========================================="
echo -e "\033[0m"

# 1. Kill any existing bot processes
echo "🛑 Stopping old processes..."
pkill -9 -f "python3.*runner.py" 2>/dev/null
sleep 1

# 2. Clear Python cache to force reload of updated code
echo "🧹 Clearing Python cache..."
find strategy_lab -name "*.pyc" -delete 2>/dev/null
find strategy_lab -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null

# 3. Start the Brain
echo "🚀 Initializing Engine..."
echo ""
python3 strategy_lab/runner.py --live

# Pause on exit (so user sees errors)
read -p "Press Enter to close..."
