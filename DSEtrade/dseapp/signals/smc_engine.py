# dseapp/signals/smc_engine.py

from .structure import detect_structure
from .liquidity import detect_liquidity
from .breaker import detect_breaker

class SMCSignalEngine:

    def __init__(self, candles):
        self.candles = candles

    def analyze(self):
        structure = detect_structure(self.candles)
        liquidity = detect_liquidity(self.candles)
        breaker = detect_breaker(self.candles)

        if structure == "bearish" and liquidity and breaker:
            return {
                "signal": "SELL",
                "confidence": "HIGH"
            }

        if structure == "bullish" and liquidity and breaker:
            return {
                "signal": "BUY",
                "confidence": "HIGH"
            }

        return {"signal": "NO_TRADE"}
