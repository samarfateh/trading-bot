import requests
import re
from typing import Dict, List

class RedditEngine:
    """
    Scrapes 'Alternative Data' from Reddit to gauge retail sentiment.
    Method: Uses public .json feed (respectful scraping).
    """
    
    SUBREDDITS = ["wallstreetbets", "stocks", "options", "investing"]
    
    @staticmethod
    def fetch_hype(symbol: str) -> Dict:
        """
        Scans subreddits for symbol mentions.
        Returns: { 'score': 0-100, 'mentions': int, 'sentiment': 'BULLISH'/'BEARISH' }
        """
        total_mentions = 0
        bullish_hits = 0
        bearish_hits = 0
        
        headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'}
        
        for sub in RedditEngine.SUBREDDITS:
            try:
                url = f"https://www.reddit.com/r/{sub}/new.json?limit=50"
                r = requests.get(url, headers=headers, timeout=5)
                
                if r.status_code != 200:
                    continue
                    
                data = r.json()
                children = data['data']['children']
                
                for post in children:
                    title = post['data']['title'].upper()
                    selftext = post['data']['selftext'].upper()
                    content = title + " " + selftext
                    
                    # Check for Symbol Mention
                    if re.search(fr'\b{symbol}\b', content):
                        total_mentions += 1
                        
                        # Sentiment Keyword Check
                        if any(x in content for x in ["MOON", "CALLS", "YOLO", "BUY", "ROCKET", "💎"]):
                            bullish_hits += 1
                        if any(x in content for x in ["PUTS", "CRASH", "RIP", "SELL", "DUMP", "🔻"]):
                            bearish_hits += 1
                            
            except Exception as e:
                print(f"Skipping r/{sub}: {e}")
                
        # Calculate Score
        # Hype Score = Scaling factor based on mentions (cap at 10 mentions = 100 hype for small scale)
        # In prod: Normalize against average volume
        hype_score = min(100, total_mentions * 10) 
        
        sentiment = "NEUTRAL"
        if bullish_hits > bearish_hits: sentiment = "BULLISH"
        elif bearish_hits > bullish_hits: sentiment = "BEARISH"
        
        return {
            "score": hype_score,
            "mentions": total_mentions,
            "direction": sentiment
        }
