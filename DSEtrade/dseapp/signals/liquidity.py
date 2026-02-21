"""
Liquidity Detection
- Stop hunts
- Liquidity sweeps
- Key liquidity levels
"""

from typing import Dict, List, Tuple, Optional
import numpy as np


def detect_liquidity(candles: List[Dict], lookback: int = 50) -> bool:
    """
    Detect if liquidity sweep occurred
    """
    if len(candles) < lookback:
        return False
    
    recent_candles = candles[-20:]
    old_candles = candles[-lookback:-20]
    
    if len(old_candles) == 0:
        return False
    
    # Find key levels
    old_high = max(c['high'] for c in old_candles)
    old_low = min(c['low'] for c in old_candles)
    
    # Check for sweeps
    for candle in recent_candles:
        # Sweep above old high (bullish liquidity grab)
        if candle['high'] > old_high * 1.001:
            if candle['close'] < old_high:  # Wicked above but closed below
                return True
        
        # Sweep below old low (bearish liquidity grab)
        if candle['low'] < old_low * 0.999:
            if candle['close'] > old_low:  # Wicked below but closed above
                return True
    
    return False


def detect_liquidity_levels(candles: List[Dict]) -> Dict:
    """
    Detect all major liquidity levels
    """
    levels = {
        'buy_stops': [],  # Above swing highs
        'sell_stops': [],  # Below swing lows
        'double_tops': [],
        'double_bottoms': []
    }
    
    swings = find_swing_points(candles, left_bars=5, right_bars=5)
    
    # Buy Stops (above swing highs)
    for high in swings['swing_highs']:
        levels['buy_stops'].append(high['price'] * 1.001)
    
    # Sell Stops (below swing lows)
    for low in swings['swing_lows']:
        levels['sell_stops'].append(low['price'] * 0.999)
    
    # Double Tops/Bottoms
    if len(swings['swing_highs']) >= 2:
        if abs(swings['swing_highs'][-1]['price'] - swings['swing_highs'][-2]['price']) / \
           swings['swing_highs'][-2]['price'] < 0.005:
            levels['double_tops'].append(swings['swing_highs'][-1]['price'])
    
    if len(swings['swing_lows']) >= 2:
        if abs(swings['swing_lows'][-1]['price'] - swings['swing_lows'][-2]['price']) / \
           swings['swing_lows'][-2]['price'] < 0.005:
            levels['double_bottoms'].append(swings['swing_lows'][-1]['price'])
    
    return levels