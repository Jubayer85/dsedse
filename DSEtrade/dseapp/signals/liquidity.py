"""
Liquidity Detection
- Stop hunts
- Liquidity sweeps
- Key liquidity levels
"""

from typing import Dict, List, Optional
from .utils import find_swing_points


def detect_liquidity(candles: List[Dict], lookback: int = 50) -> bool:
    """
    Detect if liquidity sweep occurred
    
    Args:
        candles: List of candle dictionaries
        lookback: Number of candles to look back
    
    Returns:
        True if liquidity sweep detected, False otherwise
    """
    if len(candles) < lookback:
        return False
    
    recent_candles = candles[-20:]
    old_candles = candles[-lookback:-20]
    
    if len(old_candles) == 0:
        return False
    
    old_high = max(c['high'] for c in old_candles)
    old_low = min(c['low'] for c in old_candles)
    
    for candle in recent_candles:
        # Sweep above old high (bullish liquidity grab)
        if candle['high'] > old_high * 1.001 and candle['close'] < old_high:
            return True
        
        # Sweep below old low (bearish liquidity grab)
        if candle['low'] < old_low * 0.999 and candle['close'] > old_low:
            return True
    
    return False


def detect_liquidity_sweep(candles: List[Dict]) -> bool:
    """
    Detect explicit liquidity sweep with wick
    
    Args:
        candles: List of candle dictionaries
    
    Returns:
        True if liquidity sweep detected, False otherwise
    """
    if len(candles) < 10:
        return False
    
    last_candle = candles[-1]
    prev_candles = candles[-10:-1]
    
    if len(prev_candles) == 0:
        return False
    
    prev_high = max(c['high'] for c in prev_candles)
    prev_low = min(c['low'] for c in prev_candles)
    
    # Bullish liquidity sweep (wick above resistance, close below)
    if last_candle['high'] > prev_high and last_candle['close'] < prev_high:
        return True
    
    # Bearish liquidity sweep (wick below support, close above)
    if last_candle['low'] < prev_low and last_candle['close'] > prev_low:
        return True
    
    return False


def detect_liquidity_levels(candles: List[Dict]) -> Dict:
    """
    Detect all major liquidity levels
    
    Args:
        candles: List of candle dictionaries
    
    Returns:
        Dictionary with liquidity levels
    """
    levels = {
        'buy_stops': [],  # Above swing highs
        'sell_stops': [],  # Below swing lows
        'double_tops': [],
        'double_bottoms': []
    }
    
    if len(candles) < 20:
        return levels
    
    swings = find_swing_points(candles, left_bars=5, right_bars=5)
    
    # Buy Stops (above swing highs)
    for high in swings['swing_highs']:
        levels['buy_stops'].append(round(high['price'] * 1.001, 2))
    
    # Sell Stops (below swing lows)
    for low in swings['swing_lows']:
        levels['sell_stops'].append(round(low['price'] * 0.999, 2))
    
    # Double Tops/Bottoms
    if len(swings['swing_highs']) >= 2:
        price_diff = abs(swings['swing_highs'][-1]['price'] - swings['swing_highs'][-2]['price'])
        avg_price = (swings['swing_highs'][-1]['price'] + swings['swing_highs'][-2]['price']) / 2
        if price_diff / avg_price < 0.005:  # 0.5% difference
            levels['double_tops'].append(round(avg_price, 2))
    
    if len(swings['swing_lows']) >= 2:
        price_diff = abs(swings['swing_lows'][-1]['price'] - swings['swing_lows'][-2]['price'])
        avg_price = (swings['swing_lows'][-1]['price'] + swings['swing_lows'][-2]['price']) / 2
        if price_diff / avg_price < 0.005:
            levels['double_bottoms'].append(round(avg_price, 2))
    
    return levels


def detect_liquidity_grab(candles: List[Dict]) -> Dict:
    """
    Detect liquidity grab with direction
    
    Args:
        candles: List of candle dictionaries
    
    Returns:
        Dictionary with liquidity grab details
    """
    if len(candles) < 20:
        return {'detected': False, 'direction': None, 'price': None}
    
    last_candle = candles[-1]
    prev_candles = candles[-20:-1]
    
    if len(prev_candles) < 5:
        return {'detected': False, 'direction': None, 'price': None}
    
    key_high = max(c['high'] for c in prev_candles)
    key_low = min(c['low'] for c in prev_candles)
    
    # Bullish grab (took out sell stops)
    if last_candle['low'] < key_low:
        if last_candle['close'] > key_low:
            return {
                'detected': True,
                'direction': 'bullish',
                'price': key_low,
                'type': 'sell_stops'
            }
    
    # Bearish grab (took out buy stops)
    if last_candle['high'] > key_high:
        if last_candle['close'] < key_high:
            return {
                'detected': True,
                'direction': 'bearish',
                'price': key_high,
                'type': 'buy_stops'
            }
    
    return {'detected': False, 'direction': None, 'price': None}


def get_liquidity_zones(candles: List[Dict]) -> Dict:
    """
    Get major liquidity zones
    
    Args:
        candles: List of candle dictionaries
    
    Returns:
        Dictionary with liquidity zones
    """
    if len(candles) < 30:
        return {'buy_zones': [], 'sell_zones': []}
    
    swings = find_swing_points(candles, left_bars=5, right_bars=5)
    
    buy_zones = []
    sell_zones = []
    
    # Buy zones (above swing highs)
    for high in swings['swing_highs'][-3:]:
        buy_zones.append({
            'price': round(high['price'] * 1.001, 2),
            'strength': 'strong' if high['price'] == max(h['price'] for h in swings['swing_highs']) else 'normal'
        })
    
    # Sell zones (below swing lows)
    for low in swings['swing_lows'][-3:]:
        sell_zones.append({
            'price': round(low['price'] * 0.999, 2),
            'strength': 'strong' if low['price'] == min(l['price'] for l in swings['swing_lows']) else 'normal'
        })
    
    return {
        'buy_zones': buy_zones,
        'sell_zones': sell_zones
    }