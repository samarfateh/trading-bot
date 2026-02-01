#!/bin/bash
cd "$(dirname "$0")"

echo "☕️ STARTING AMD BOT (NO-SLEEP MODE) ☕️"
echo "This script prevents your Mac from sleeping while the bot is active."
echo "Press Ctrl+C to stop the bot and allow sleep again."
echo "---------------------------------------------------"

# caffeinate -i prevents idle sleep while the command runs
caffeinate -i python3 monitor.py
