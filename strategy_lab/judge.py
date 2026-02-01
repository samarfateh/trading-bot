from typing import Dict

class TheJudge:
    """
    The Arbitrator.
    Translates technical feature tags into a human-readable Verdict.
    """

    @staticmethod
    def delimit_verdict(features: Dict, macro: Dict = {}) -> str:
        """
        Input: Feature Dictionary (Trend, Key Levels, Divergence, Sector)
        Output: A formatted string explanation.
        """
        verdict = []
        score = 0
        
        # --- 🛡️ SAFETY SHIELD ---
        # 0. MACRO SIXTH SENSE (Global Safety)
        vix = macro.get('vix', 20)
        spy_trend = macro.get('spy_trend', 'BULLISH')
        
        if vix > 30:
            return "VERDICT: BLOCKED | 🛑 The market is in full panic mode. It's safer to sit this one out."
            
        if spy_trend == 'BEARISH' and features.get('sector_trend') == 'BEARISH':
             return "VERDICT: CAUTION | ⚠️ Both the overall market and tech sector are falling. Not a good time for standard plays."

        # 1. IV Lock (Volatility Protection)
        iv = features.get("current_iv", 0) 
        if iv > 0.80:
             return "VERDICT: BLOCKED | 🛑 Options are way too expensive right now. Prices could crash suddenly."

        # 2. Trend Lock (200 SMA)
        # Don't catch falling knives.
        price = features.get("current_price", 0)
        sma200 = features.get("sma_200", 0)
        if sma200 > 0 and price < sma200:
             verdict.append("🔒 Stock is in a major downtrend. Only quick scalps recommended.")
             if score > 0: score = 0 # Nullify bullish bias
             
        # 3. News Veto (Sentiment)
        sentiment = features.get("sentiment", {})
        if sentiment.get("direction") == "BEARISH" and sentiment.get("score") > 80:
             return "VERDICT: BLOCKED | 🛑 Social media is extremely negative. The crowd is dumping this stock."
        # --- END SHIELD ---
        
        # 1. Trend Analysis
        trend = features.get("trend", "UNKNOWN")
        htf_trend = features.get("htf_trend", "UNKNOWN")
        
        if trend == "UP" and htf_trend == "UP":
            verdict.append("Market is in a STRONG UPTREND (Confluence).")
            score += 2
        elif trend == "DOWN" and htf_trend == "DOWN":
            verdict.append("Market is in a STRONG DOWNTREND (Confluence).")
            score -= 2
        elif trend != htf_trend:
            verdict.append("Trend is Conflicted (5m vs 1H). Caution advised.")

        # 2. Key Levels
        level = features.get("key_level", "MIDDLE")
        if level == "AT_SUPPORT":
            verdict.append("Price is testing SUPPORT (Bounce Watch).")
            score += 1
        elif level == "AT_RESISTANCE":
            verdict.append("Price is hitting RESISTANCE (Rejection Watch).")
            score -= 1

        # 3. Divergence (The X-Factor)
        div = features.get("divergence", "NONE")
        if div == "BULL_DIV":
            verdict.append("⚠️ BULLISH DIVERGENCE detected (Momemtum shifting Up).")
            score += 2
        elif div == "BEAR_DIV":
            verdict.append("⚠️ BEARISH DIVERGENCE detected (Momentum fading).")
            score -= 2

        # 4. The Tide (Sector)
        sector = features.get("sector_correlation", "UNKNOWN")
        if sector == "AGAINST_SECTOR":
            verdict.append("Note: Stock is fighting the Sector Trend (QQQ). Reduced probability.")

        # 5. Social Hype (The Meme Factor)
        sentiment = features.get("sentiment", {})
        hype_score = sentiment.get("score", 0)
        hype_dir = sentiment.get("direction", "NEUTRAL")

        if hype_score > 50:
            if hype_dir == "BULLISH":
                verdict.append(f"🔥 HIGH HYPE {hype_score}/100 (WSB is Bullish). Momentum Warning.")
                score += 1 # Crowd Momentum
            elif hype_dir == "BEARISH":
                verdict.append(f"🩸 FEAR DETECTED {hype_score}/100 (WSB is Bearish). Contrarian Watch.")
                
        # Final Decision
        final_decision = "NEUTRAL"
        if score >= 3: final_decision = "STRONG BUY"
        elif score >= 1: final_decision = "BUY"
        elif score <= -3: final_decision = "STRONG SELL"
        elif score <= -1: final_decision = "SELL"
        
        explanation = " ".join(verdict)
        return f"VERDICT: {final_decision} | {explanation}"
