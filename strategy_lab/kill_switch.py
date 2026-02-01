"""
Kill Switch System
Emergency controls to halt trading
"""
import os
from datetime import datetime
from typing import Optional

class KillSwitch:
    """Manages emergency trading halts"""
    
    def __init__(self, base_dir=None):
        if base_dir is None:
            base_dir = os.path.dirname(os.path.dirname(__file__))
        self.base_dir = base_dir
        self.manual_stop_file = os.path.join(base_dir, "STOP_TRADING.txt")
        self.auto_pause_file = os.path.join(base_dir, "TRADING_PAUSED.txt")
    
    def is_trading_halted(self) -> bool:
        """Check if any kill switch is active"""
        return os.path.exists(self.manual_stop_file) or os.path.exists(self.auto_pause_file)
    
    def get_halt_reason(self) -> Optional[str]:
        """Get the reason trading is halted"""
        if os.path.exists(self.manual_stop_file):
            try:
                with open(self.manual_stop_file, 'r') as f:
                    return f"Manual Stop: {f.read().strip()}"
            except:
                return "Manual Stop (STOP_TRADING.txt exists)"
        
        if os.path.exists(self.auto_pause_file):
            try:
                with open(self.auto_pause_file, 'r') as f:
                    return f.read().strip()
            except:
                return "Auto-Paused (TRADING_PAUSED.txt exists)"
        
        return None
    
    def trigger_manual_stop(self, reason="Manual emergency stop"):
        """Create manual kill switch file"""
        with open(self.manual_stop_file, 'w') as f:
            f.write(f"{reason}\n")
            f.write(f"Triggered: {datetime.now()}\n")
            f.write(f"\nTo resume trading:\n")
            f.write(f"1. Review the situation\n")
            f.write(f"2. Delete this file: STOP_TRADING.txt\n")
        print(f"🛑 MANUAL KILL SWITCH ACTIVATED: {reason}")
    
    def trigger_auto_pause(self, reason: str):
        """Create auto-pause file"""
        with open(self.auto_pause_file, 'w') as f:
            f.write(f"Auto-Paused: {reason}\n")
            f.write(f"Time: {datetime.now()}\n")
            f.write(f"\nTo resume trading:\n")
            f.write(f"1. Fix the issue that triggered this pause\n")
            f.write(f"2. Delete this file: TRADING_PAUSED.txt\n")
            f.write(f"3. Bot will resume on next scan cycle\n")
        print(f"⚠️  AUTO-PAUSE TRIGGERED: {reason}")
    
    def resume_trading(self):
        """Remove all kill switch files (requires manual action)"""
        removed = []
        if os.path.exists(self.manual_stop_file):
            os.remove(self.manual_stop_file)
            removed.append("Manual Stop")
        if os.path.exists(self.auto_pause_file):
            os.remove(self.auto_pause_file)
            removed.append("Auto-Pause")
        
        if removed:
            print(f"✅ Trading resumed (removed: {', '.join(removed)})")
        else:
            print("ℹ️  No kill switches were active")
    
    def get_status(self) -> dict:
        """Get current kill switch status for dashboard"""
        return {
            "halted": self.is_trading_halted(),
            "reason": self.get_halt_reason(),
            "manual_stop_active": os.path.exists(self.manual_stop_file),
            "auto_pause_active": os.path.exists(self.auto_pause_file)
        }


if __name__ == "__main__":
    # CLI for testing
    import sys
    
    ks = KillSwitch()
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "stop":
            reason = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else "Manual emergency stop"
            ks.trigger_manual_stop(reason)
        
        elif command == "resume":
            ks.resume_trading()
        
        elif command == "status":
            status = ks.get_status()
            if status["halted"]:
                print(f"🛑 Trading HALTED: {status['reason']}")
            else:
                print("✅ Trading ACTIVE (no kill switches)")
        
        else:
            print("Usage: python kill_switch.py [stop|resume|status]")
    else:
        # Show current status
        status = ks.get_status()
        print(f"Trading Status: {'HALTED' if status['halted'] else 'ACTIVE'}")
        if status["reason"]:
            print(f"Reason: {status['reason']}")
