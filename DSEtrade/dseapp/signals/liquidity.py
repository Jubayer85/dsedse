def detect_liquidity(candles):
    if len(candles) < 3:
        return False

    highs = [c["high"] for c in candles[-5:]]
    lows = [c["low"] for c in candles[-5:]]

    # simple liquidity sweep example
    if max(highs) == candles[-1]["high"]:
        return True

    return False
