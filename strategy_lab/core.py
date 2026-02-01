import json
import os
from typing import List, Dict, Optional
from dataclasses import dataclass

@dataclass
class StrategyLeg:
    action: str  # BUY/SELL
    type: str    # CALL/PUT
    strike_logic: str # ATM, ATM+1, DELTA_30, etc.
    quantity: int = 1

@dataclass
class StrategyDef:
    id: str
    name: str
    type: str # VERTICAL, CONDOR, ETC.
    direction: str # BULLISH, BEARISH, NEUTRAL
    legs: List[StrategyLeg]
    entry_rules: Dict
    exit_rules: Dict

class StrategyValidator:
    """Validates Strategy JSON files against the required schema."""

    REQUIRED_FIELDS = ["id", "name", "type", "direction", "legs", "entry_rules"]
    VALID_DIRECTIONS = ["BULLISH", "BEARISH", "NEUTRAL", "ANY"]

    @staticmethod
    def validate(data: Dict) -> bool:
        # Check required fields
        for field in StrategyValidator.REQUIRED_FIELDS:
            if field not in data:
                raise ValueError(f"Missing required field: {field}")

        # Check Direction
        if data["direction"] not in StrategyValidator.VALID_DIRECTIONS:
            raise ValueError(f"Invalid direction: {data['direction']}")

        # Validate Legs
        if not isinstance(data["legs"], list) or len(data["legs"]) == 0:
            raise ValueError("Strategy must have at least one leg")

        for leg in data["legs"]:
            if "action" not in leg or leg["action"] not in ["BUY", "SELL"]:
                raise ValueError(f"Invalid leg action: {leg.get('action')}")
            if "type" not in leg or leg["type"] not in ["CALL", "PUT"]:
                raise ValueError(f"Invalid leg type: {leg.get('type')}")
        
        return True

    @staticmethod
    def load_library(path: str) -> List[Dict]:
        """Loads and validates all JSON strategies in a directory."""
        strategies = []
        if not os.path.exists(path):
            return []

        for filename in os.listdir(path):
            if filename.endswith(".json"):
                full_path = os.path.join(path, filename)
                try:
                    with open(full_path, 'r') as f:
                        data = json.load(f)
                        StrategyValidator.validate(data)
                        strategies.append(data)
                except Exception as e:
                    print(f"FAILED to load {filename}: {e}")
        
        return strategies
