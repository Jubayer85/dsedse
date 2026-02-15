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

        confidence = 0

        # Structure weight
        if structure in ["bullish", "bearish"]:
            confidence += 40

        # Liquidity weight
        if liquidity:
            confidence += 30

        # Breaker weight
        if breaker:
            confidence += 30

        # Final Signal Decision
        if confidence >= 70:
            if structure == "bullish":
                signal = "BUY"
            elif structure == "bearish":
                signal = "SELL"
            else:
                signal = "NO_TRADE"
        else:
            signal = "NO_TRADE"

        return {
            "signal": signal,
            "structure": structure,
            "confidence": confidence
        }