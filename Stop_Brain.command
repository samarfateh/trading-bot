#!/bin/bash
cd "$(dirname "$0")"

echo -e "\033[31m"
echo "==========================================="
echo "      🛑 STOPPING STRATEGY BRAIN...       "
echo "==========================================="
echo -e "\033[0m"

# Find and Kill the process
pkill -f "strategy_lab/runner.py"

if [ $? -eq 0 ]; then
    echo "✅ Successfully stopped the AI Engine."
else
    echo "⚠️ No running Brain found (or permission denied)."
fi

# Pause
read -p "Press Enter to close..."
