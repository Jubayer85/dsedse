"""
Advanced Institutional Liquidity Detection
- Liquidity sweeps with strength scoring
- Volume-confirmed stop hunts
- Wick dominance filter
- Multi-touch liquidity zones
"""

from typing import Dict, List
from statistics import mean
from .utils import find_swing_points


# --------------------------------------------------
# SWEEP STRENGTH DETECTION
# --------------------------------------------------

def detect_liquidity_sweep_strength(candles: List[Dict]) -> Dict:
    """
    Detect liquidity sweep and return strength score (0–100)
    """

    if len(candles) < 20:
        return {"detected": False, "strength": 0, "direction": None}

    last = candles[-1]
    prev = candles[-20:-1]

    prev_high = max(c["high"] for c in prev)
    prev_low = min(c["low"] for c in prev)

    body = abs(last["close"] - last["open"])
    total_range = last["high"] - last["low"]

    if total_range == 0:
        return {"detected": False, "strength": 0, "direction": None}

    wick_ratio = 1 - (body / total_range)

    # Bullish sweep (took sell stops)
    if last["low"] < prev_low and last["close"] > prev_low:
        strength = round(wick_ratio * 100, 2)
        return {
            "detected": True,
            "direction": "bullish",
            "strength": strength
        }

    # Bearish sweep (took buy stops)
    if last["high"] > prev_high and last["close"] < prev_high:
        strength = round(wick_ratio * 100, 2)
        return {
            "detected": True,
            "direction": "bearish",
            "strength": strength
        }

    return {"detected": False, "strength": 0, "direction": None}


# --------------------------------------------------
# VOLUME CONFIRMED SWEEP
# --------------------------------------------------

def volume_confirmed_sweep(candles: List[Dict], period: int = 20) -> Dict:
    """
    Confirm sweep with abnormal volume
    """

    sweep = detect_liquidity_sweep_strength(candles)

    if not sweep["detected"]:
        return sweep

    volumes = [c["volume"] for c in candles[-period:]]

    if len(volumes) < period:
        return sweep

    avg_volume = mean(volumes[:-1])
    last_volume = volumes[-1]

    if avg_volume == 0:
        return sweep

    volume_ratio = last_volume / avg_volume

    sweep["volume_ratio"] = round(volume_ratio, 2)

    # Add bonus strength
    if volume_ratio > 1.3:
        sweep["strength"] += 15

    sweep["strength"] = min(100, sweep["strength"])

    return sweep


# --------------------------------------------------
# LIQUIDITY LEVEL STRENGTH RANKING
# --------------------------------------------------

def detect_liquidity_levels_ranked(candles: List[Dict]) -> Dict:
    """
    Rank liquidity levels by number of touches
    """

    levels = {
        "buy_stops": [],
        "sell_stops": []
    }

    if len(candles) < 30:
        return levels

    swings = find_swing_points(candles, left_bars=5, right_bars=5)

    highs = [s["price"] for s in swings["swing_highs"]]
    lows = [s["price"] for s in swings["swing_lows"]]

    for high in highs:
        touches = sum(1 for c in candles if abs(c["high"] - high) / high < 0.002)
        levels["buy_stops"].append({
            "price": round(high * 1.001, 2),
            "touches": touches,
            "strength": "strong" if touches >= 3 else "normal"
        })

    for low in lows:
        touches = sum(1 for c in candles if abs(c["low"] - low) / low < 0.002)
        levels["sell_stops"].append({
            "price": round(low * 0.999, 2),
            "touches": touches,
            "strength": "strong" if touches >= 3 else "normal"
        })

    return levels


# --------------------------------------------------
# DISPLACEMENT CONFIRMATION
# --------------------------------------------------

def displacement_after_sweep(candles: List[Dict]) -> bool:
    """
    Confirm strong displacement candle after liquidity grab
    """

    if len(candles) < 3:
        return False

    last = candles[-1]
    prev = candles[-2]

    body = abs(last["close"] - last["open"])
    prev_body = abs(prev["close"] - prev["open"])

    return body > prev_body * 1.5