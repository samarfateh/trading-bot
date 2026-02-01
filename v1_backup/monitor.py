import time
import requests
import json
import random
from datetime import datetime

# --- CONFIGURATION ---
API_KEY = 'd5v9d99r01qjj9jinsogd5v9d99r01qjj9jinsp0' # Your Finnhub Key
DISCORD_WEBHOOK = 'https://discord.com/api/webhooks/1467339178701230122/MnWqFuFNUTO4HGMHfZA7eQEsZFjdGvUWIdA-WMb_jqiFVEtNkWpA85d93QaZ8FR6HkB2' # <--- PASTE WEBHOOK HERE
SYMBOL = 'AMD'

class MarketData:
    def __init__(self):
        self.price = 0
        self.iv = 0.45

    def get_quote(self):
        try:
            url = f"https://finnhub.io/api/v1/quote?symbol={SYMBOL}&token={API_KEY}"
            r = requests.get(url)
            data = r.json()
            if 'c' in data and data['c'] > 0:
                self.price = data['c']
                return self.price
            else:
                return self.mock_quote()
        except Exception as e:
            print(f"Error fetching data: {e}")
            return self.mock_quote()

    def mock_quote(self):
        # Fallback if API fails or mock mode
        change = (random.random() - 0.5) * 1.5
        if self.price == 0: self.price = 175.50
        self.price += change
        return self.price

class StrategyEngine:
    def __init__(self):
        self.history = []

    def calculate_sma(self, period):
        if len(self.history) < period: return None
        return sum(self.history[-period:]) / period

    def calculate_rsi(self, period=14):
        if len(self.history) < period + 1: return 50
        gains = 0
        losses = 0
        for i in range(1, period + 1):
            diff = self.history[-i] - self.history[-(i+1)]
            if diff >= 0: gains += diff
            else: losses += abs(diff)
        
        if losses == 0: return 100
        rs = gains / losses
        return 100 - (100 / (1 + rs))

    def analyze(self, current_price):
        self.history.append(current_price)
        if len(self.history) > 100: self.history.pop(0)

        sma20 = self.calculate_sma(20)
        sma50 = self.calculate_sma(50)
        
        if not sma20 or not sma50: return None

        # TREND STRATEGY
        if current_price > sma20 and sma20 > sma50:
            return {
                "type": "BUY",
                "strategy": "TREND (Call Debit Spread)",
                "price": current_price,
                "reason": f"Breakout: Price ${current_price:.2f} > SMA20"
            }
        
        # RANGE STRATEGY
        deviation = abs((current_price - sma50) / sma50) * 100
        if deviation < 1.0:
            return {
                "type": "SELL",
                "strategy": "RANGE (Iron Condor)",
                "price": current_price,
                "reason": f"Chop: Price pinned to SMA50"
            }

        return {"type": "WAIT", "price": current_price}

def send_discord_alert(signal):
    if DISCORD_WEBHOOK == 'YOUR_DISCORD_WEBHOOK_URL_HERE':
        print("!! Discord Webhook not set. Skipping alert.")
        return

    color = 5763719 # Green
    if signal['type'] == 'SELL': color = 15548997 # Red
    if signal['type'] == 'WAIT': color = 9807270 # Grey

    embed = {
        "title": f"🚨 {signal['type']} SIGNAL: {SYMBOL}",
        "description": f"**Strategy:** {signal.get('strategy', 'Hold')}\n**Price:** ${signal['price']:.2f}\n**Reason:** {signal.get('reason', 'Consolidating')}",
        "color": color,
        "footer": {"text": "AMD Strategy Pro Bot"}
    }
    
    data = {"embeds": [embed]}
    try:
        requests.post(DISCORD_WEBHOOK, json=data)
        print(f"Sent Discord Alert: {signal['type']}")
    except Exception as e:
        print(f"Failed to send Discord alert: {e}")

# --- MAIN LOOP ---
if __name__ == "__main__":
    print(f"Starting AMD Monitor for {SYMBOL}...")
    market = MarketData()
    engine = StrategyEngine()

    # Send Startup Message
    print("Sending Startup Notification...")
    send_discord_alert({
        "type": "ONLINE",
        "strategy": "System Startup",
        "price": market.get_quote(),
        "reason": "Bot started successfully. Monitoring active."
    })

    # Seed history
    print("Seeding historical data...")
    for _ in range(50):
        engine.analyze(market.mock_quote())

    print("Live Monitoring Active (Ctrl+C to stop)")
    while True:
        price = market.get_quote()
        signal = engine.analyze(price)
        
        if signal:
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"[{timestamp}] ${price:.2f} -> {signal['type']}")
            
            # Rate limit alerts (only alert on BUY/SELL changes usually, but for demo we alert active signals)
            if signal['type'] != 'WAIT':
                send_discord_alert(signal)
        
        time.sleep(300) # 5 Minutes
