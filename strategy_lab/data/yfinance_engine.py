import yfinance as yf
import pandas as pd
from typing import Dict, List, Optional
import time

class YFinanceEngine:
    """
    Unlimited Fuel Engine.
    Fetches live market data using Yahoo Finance.
    No Rate Limits. Real-time(ish).
    """

    def fetch_snapshot(self, symbol: str) -> Dict:
        """
        Fetches EVERYTHING in one go to minimize network calls.
        Returns:
            {
                "symbol": str,
                "price": float,
                "closes": List[float],    # 1-min closes (last 100)
                "htf_closes": List[float], # Hourly closes (last 100)
                "sma_200": float,
                "current_iv": float,       # Estimated from options
                "sector_closes": List[float] # QQQ closes
            }
        """
        print(f"⚡ YF: Fetching Snapshot for {symbol}...")
        
        try:
            # 1. Main Ticker
            ticker = yf.Ticker(symbol)
            
            # Fetch Intraday (1m) & HTF (1h) & Daily (for SMA)
            # YFinance allows fetching multiple periods, or we just fetch 1mo 1h and 1y 1d separately.
            # Efficient pattern:
            
            # A. Intraday (1d, 1m)
            df_intraday = ticker.history(period="5d", interval="1m")
            if df_intraday.empty:
                print("⚠️ YF: No Intraday Data Found")
                return {}
            
            closes = df_intraday['Close'].tolist()
            current_price = closes[-1]
            
            # Rich Stats (Calculated from available data to save API calls)
            # Assuming df_intraday covers at least the current trading day
            day_high = df_intraday['High'].max()
            day_low = df_intraday['Low'].min()
            volume_accumulated = df_intraday['Volume'].sum()
            day_open = df_intraday['Open'].iloc[0]
            change_pct_day = ((current_price - day_open) / day_open) * 100 if day_open else 0
            
            # B. HTF (1mo, 1h)
            df_htf = ticker.history(period="1mo", interval="1h")
            htf_closes = df_htf['Close'].tolist()
            
            # C. Daily (1y, 1d) for SMA200
            df_daily = ticker.history(period="1y", interval="1d")
            daily_closes = df_daily['Close'].tolist()
            sma_200 = sum(daily_closes[-200:]) / 200 if len(daily_closes) >= 200 else 0
            
            # D. IV Estimation (Volatility)
            # We grab the nearest expiration option chain
            current_iv = 0.50 # Default fallback
            try:
                exps = ticker.options
                if exps:
                    # Get front month chain (approx 30 days out usually ideal, but nearest is fine for 'current' state)
                    chain = ticker.option_chain(exps[0])
                    # Average IV of slightly OTM calls/puts?
                    # Simplify: YF provides 'impliedVolatility' column in the chain DataFrame
                    calls = chain.calls
                    # Filter for near-the-money
                    # strike ~ current_price
                    atm_calls = calls.iloc[(calls['strike'] - current_price).abs().argsort()[:5]]
                    iv_avg = atm_calls['impliedVolatility'].mean()
                    if iv_avg > 0: current_iv = iv_avg
            except Exception as e:
                print(f"⚠️ YF: Options Data Error: {e}")

            # E. Sector Data (QQQ)
            # We can cache this or fetch every time (it's fast)
            qqq = yf.Ticker("QQQ")
            df_qqq = qqq.history(period="5d", interval="1m")
            sector_closes = df_qqq['Close'].tolist()

            return {
                "symbol": symbol,
                "current_price": float(current_price),
                "day_high": float(day_high),
                "day_low": float(day_low),
                "day_open": float(day_open),
                "change_pct": float(change_pct_day),
                "volume": int(volume_accumulated),
                "closes": closes,
                "htf_closes": htf_closes,
                "sma_200": float(sma_200),
                "current_iv": float(current_iv),
                "sector_closes": sector_closes
            }

        except Exception as e:
            print(f"❌ YF Engine Error: {e}")
            return {}


    def fetch_macro_stats(self) -> Dict:
        """
        Fetches Global Macro Context (SPY, VIX).
        """
        try:
            # 1. VIX (Fear)
            vix = yf.Ticker("^VIX")
            vix_hist = vix.history(period="1d")
            current_vix = vix_hist['Close'].iloc[-1] if not vix_hist.empty else 20.0
            
            # 2. SPY (Market Trend)
            spy = yf.Ticker("SPY")
            spy_hist = spy.history(period="1y") # Need long period for SMA200
            if spy_hist.empty: return {"vix": current_vix, "spy_trend": "BULLISH", "spy_price": 0}
            
            spy_closes = spy_hist['Close'].tolist()
            
            spy_sma200 = sum(spy_closes[-200:]) / 200 if len(spy_closes) >= 200 else spy_closes[0]
            current_spy = spy_closes[-1]
            
            spy_trend = "BULLISH" if current_spy > spy_sma200 else "BEARISH"
            
            return {
                "vix": current_vix,
                "spy_price": current_spy,
                "spy_trend": spy_trend
            }
        except Exception as e:
            print(f"⚠️ Error fetching Macro Stats: {e}")
            return {"vix": 20.0, "spy_trend": "BULLISH"} # Default to safe/neutral

if __name__ == "__main__":
    # Test
    yf_engine = YFinanceEngine()
    data = yf_engine.fetch_snapshot("AMD")
    print("\n--- SNAPSHOT ---")
    print(f"Price: {data.get('current_price')}")
    print(f"SMA200: {data.get('sma_200')}")
    print(f"IV: {data.get('current_iv')}")
    print(f"Closes: {len(data.get('closes', []))} candles")
    
    macro = yf_engine.fetch_macro_stats()
    print("\n--- MACRO ---")
    print(macro)
