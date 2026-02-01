from typing import List, Dict, Any
from strategy_lab.core import StrategyValidator
from strategy_lab.market_features import MarketFeatureEngine

class StrategyScanner:
    """
    The Matchmaker.
    Checks if a Strategy's entry rules match the current Market Features.
    """

    @staticmethod
    def is_applicable(strategy: Dict, features: Dict) -> bool:
        rules = strategy.get("entry_rules", {})
        
        # 1. Check Trend
        req_trend = rules.get("trend")
        if req_trend and req_trend != features.get("trend"):
            return False

        # 2. Check IV Rank Logic
        current_iv_rank = features.get("iv_rank", 50)
        min_iv = rules.get("min_iv_rank", 0)
        max_iv = rules.get("max_iv_rank", 100)
        
        if not (min_iv <= current_iv_rank <= max_iv):
            return False

        # 3. Check Multi-Timeframe Confluence (The Pro Rule)
        strat_dir = strategy.get("direction")
        htf_trend = features.get("htf_trend", "UNKNOWN")

        if htf_trend != "UNKNOWN":
            # Don't buy in a downtrend
            if strat_dir == "BULLISH" and htf_trend == "DOWN":
                return False
            # Don't short in an uptrend
            if strat_dir == "BEARISH" and htf_trend == "UP":
                return False

        return True

    def scan(self, strategies: List[Dict], market_snapshot: Dict) -> List[Dict]:
        """
        Runs the full scan.
        Returns a list of 'Signal' objects (dicts) for applicable strategies.
        """
        features = MarketFeatureEngine.analyze_snapshot(market_snapshot)
        signals = []

        for strat in strategies:
            if self.is_applicable(strat, features):
                signals.append({
                    "strategy_id": strat.get("id"),
                    "strategy_name": strat.get("name"),
                    "direction": strat.get("direction"),
                    "features_matched": features,
                    "legs": strat.get("legs") # In a real app, we'd resolve strikes here
                })
        
        return signals
