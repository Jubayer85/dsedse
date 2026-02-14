# dseapp/signals/breaker.py

def detect_breaker(candles):
    """
    Simple breaker detection logic.
    Assumes structure shift already happened.
    """

    if len(candles) < 5:
        return False

    # Last 5 candles
    recent = candles[-5:]

    # Find last opposite candle before displacement
    last = recent[-1]
    prev = recent[-2]

    # Bearish breaker condition (simple example)
    if last["close"] < prev["low"]:
        return True

    # Bullish breaker condition
    if last["close"] > prev["high"]:
        return True

    return False
