#!/bin/bash

# Kill Switch CLI
# Quick way to stop/resume trading from command line

cd "$(dirname "$0")"

case "$1" in
    stop)
        python3 strategy_lab/kill_switch.py stop "${@:2}"
        ;;
    resume)
        python3 strategy_lab/kill_switch.py resume
        ;;
    status)
        python3 strategy_lab/kill_switch.py status
        ;;
    *)
        echo "Usage: ./Kill_Switch.command [stop|resume|status]"
        echo ""
        echo "Examples:"
        echo "  ./Kill_Switch.command stop           # Emergency stop"
        echo "  ./Kill_Switch.command stop \"Bad market\" # Stop with reason"
        echo "  ./Kill_Switch.command resume         # Resume trading"
        echo "  ./Kill_Switch.command status         # Check status"
        ;;
esac

read -p "Press Enter to close..."
