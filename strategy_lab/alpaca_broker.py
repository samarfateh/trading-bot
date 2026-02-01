"""
Alpaca Broker Interface
Handles order execution and position monitoring
"""
from typing import Dict, List, Optional
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

try:
    from alpaca.trading.client import TradingClient
    from alpaca.trading.requests import MarketOrderRequest, LimitOrderRequest
    from alpaca.trading.enums import OrderSide, TimeInForce
    ALPACA_AVAILABLE = True
except ImportError:
    ALPACA_AVAILABLE = False
    print("⚠️  Alpaca SDK not installed. Run: pip install alpaca-py")


class AlpacaBroker:
    def __init__(self, paper_trading=True):
        if not ALPACA_AVAILABLE:
            raise ImportError("Alpaca SDK not available. Install with: pip install alpaca-py")
        
        # Load credentials from .env
        api_key = os.getenv("ALPACA_API_KEY")
        secret_key = os.getenv("ALPACA_SECRET_KEY")
        
        if not api_key or not secret_key or api_key == "your_paper_key_here":
            raise ValueError("Alpaca API keys not configured in .env file")
        
        # Initialize trading client
        self.client = TradingClient(api_key, secret_key, paper=paper_trading)
        self.paper_trading = paper_trading
        
        print(f"✅ Alpaca {'Paper' if paper_trading else 'LIVE'} Trading Connected")
    
    def get_account(self) -> Dict:
        """Get account information"""
        try:
            account = self.client.get_account()
            return {
                "cash": float(account.cash),
                "portfolio_value": float(account.portfolio_value),
                "buying_power": float(account.buying_power),
                "equity": float(account.equity)
            }
        except Exception as e:
            print(f"❌ Error fetching account: {e}")
            return {}
    
    def get_open_positions(self) -> List[Dict]:
        """Get all open positions"""
        try:
            positions = self.client.get_all_positions()
            return [{
                "symbol": p.symbol,
                "qty": int(p.qty),
                "avg_entry_price": float(p.avg_entry_price),
                "current_price": float(p.current_price),
                "unrealized_pl": float(p.unrealized_pl),
                "unrealized_plpc": float(p.unrealized_plpc)
            } for p in positions]
        except Exception as e:
            print(f"❌ Error fetching positions: {e}")
            return []
    
    def submit_market_order(self, symbol: str, qty: int, side: str) -> Optional[str]:
        """
        Submit a market order
        Returns: Order ID if successful, None if failed
        """
        try:
            order_side = OrderSide.BUY if side.upper() == "BUY" else OrderSide.SELL
            
            order_data = MarketOrderRequest(
                symbol=symbol,
                qty=qty,
                side=order_side,
                time_in_force=TimeInForce.DAY
            )
            
            order = self.client.submit_order(order_data)
            print(f"✅ Order submitted: {side} {qty} {symbol} (ID: {order.id})")
            return str(order.id)
            
        except Exception as e:
            print(f"❌ Order failed: {e}")
            return None
    
    def close_position(self, symbol: str) -> bool:
        """Close an open position"""
        try:
            self.client.close_position(symbol)
            print(f"✅ Position closed: {symbol}")
            return True
        except Exception as e:
            print(f"❌ Failed to close {symbol}: {e}")
            return False
    
    def close_all_positions(self) -> int:
        """Emergency: Close all open positions"""
        try:
            positions = self.get_open_positions()
            count = 0
            for pos in positions:
                if self.close_position(pos["symbol"]):
                    count += 1
            print(f"✅ Closed {count}/{len(positions)} positions")
            return count
        except Exception as e:
            print(f"❌ Error closing all positions: {e}")
            return 0


# Dry-run version for testing (doesn't actually submit orders)
class DryRunBroker:
    """Simulated broker that logs orders but doesn't execute them"""
    
    def __init__(self):
        self.paper_trading = True
        self.mock_account = {
            "cash": 100000.0,
            "portfolio_value": 100000.0,
            "buying_power": 100000.0,
            "equity": 100000.0
        }
        self.mock_positions = []
        print("✅ Dry-Run Mode Active (orders will be logged, not executed)")
    
    def get_account(self) -> Dict:
        return self.mock_account
    
    def get_open_positions(self) -> List[Dict]:
        return self.mock_positions
    
    def submit_market_order(self, symbol: str, qty: int, side: str) -> Optional[str]:
        order_id = f"DRY-RUN-{len(self.mock_positions)+1}"
        print(f"🔷 DRY-RUN ORDER: {side} {qty} {symbol} (ID: {order_id})")
        return order_id
    
    def close_position(self, symbol: str) -> bool:
        print(f"🔷 DRY-RUN CLOSE: {symbol}")
        return True
    
    def close_all_positions(self) -> int:
        count = len(self.mock_positions)
        print(f"🔷 DRY-RUN CLOSE ALL: {count} positions")
        self.mock_positions = []
        return count
