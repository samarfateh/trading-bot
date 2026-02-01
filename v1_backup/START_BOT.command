#!/bin/bash
cd "$(dirname "$0")"
nohup python3 monitor.py > bot.log 2>&1 &
echo "✅ AMD Bot Started in Background!"
echo "You can close this window."
exit 0
