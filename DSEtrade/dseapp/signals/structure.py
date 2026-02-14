def detect_structure(candles):
    if not candles:
        return None

    last = candles[-1]
    prev = candles[-2] if len(candles) > 1 else last

    if last["close"] > prev["close"]:
        return "bullish"
    elif last["close"] < prev["close"]:
        return "bearish"

    return None
