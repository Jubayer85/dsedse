"""
Market Structure Detection
- Swing Highs/Lows
- Market Structure Shifts (MSS)
- Trend Analysis
"""

from typing import Dict, List, Optional


def find_swing_points(candles: List[Dict], left_bars: int = 5, right_bars: int = 5) -> Dict:
    """
    Find swing highs and lows
    """
    if len(candles) < left_bars + right_bars + 1:
        return {'swing_highs': [], 'swing_lows': []}
    
    highs = [c['high'] for c in candles]
    lows = [c['low'] for c in candles]
    
    swing_highs = []
    swing_lows = []
    
    for i in range(left_bars, len(candles) - right_bars):
        # Swing High
        is_swing_high = True
        for j in range(1, left_bars + 1):
            if highs[i] <= highs[i - j]:
                is_swing_high = False
                break
        if is_swing_high:
            for j in range(1, right_bars + 1):
                if highs[i] <= highs[i + j]:
                    is_swing_high = False
                    break
        
        if is_swing_high:
            swing_highs.append({
                'index': i,
                'price': highs[i],
                'time': candles[i].get('time', i)
            })
        
        # Swing Low
        is_swing_low = True
        for j in range(1, left_bars + 1):
            if lows[i] >= lows[i - j]:
                is_swing_low = False
                break
        if is_swing_low:
            for j in range(1, right_bars + 1):
                if lows[i] >= lows[i + j]:
                    is_swing_low = False
                    break
        
        if is_swing_low:
            swing_lows.append({
                'index': i,
                'price': lows[i],
                'time': candles[i].get('time', i)
            })
    
    return {
        'swing_highs': swing_highs,
        'swing_lows': swing_lows
    }


def detect_structure(candles: List[Dict]) -> str:
    """
    Detect current market structure
    Returns: 'bullish', 'bearish', 'ranging', 'accumulation', 'distribution'
    """
    if len(candles) < 10:
        return 'ranging'
    
    swings = find_swing_points(candles, left_bars=3, right_bars=3)
    
    if len(swings['swing_highs']) < 2 or len(swings['swing_lows']) < 2:
        return 'ranging'
    
    recent_highs = swings['swing_highs'][-3:]
    recent_lows = swings['swing_lows'][-3:]
    
    # Bullish Structure (Higher Highs + Higher Lows)
    if len(recent_highs) >= 2 and len(recent_lows) >= 2:
        if recent_highs[-1]['price'] > recent_highs[-2]['price'] and \
           recent_lows[-1]['price'] > recent_lows[-2]['price']:
            return 'bullish'
    
    # Bearish Structure (Lower Highs + Lower Lows)
    if len(recent_highs) >= 2 and len(recent_lows) >= 2:
        if recent_highs[-1]['price'] < recent_highs[-2]['price'] and \
           recent_lows[-1]['price'] < recent_lows[-2]['price']:
            return 'bearish'
    
    # Accumulation (Sideways after downtrend)
    if len(swings['swing_lows']) > 0:
        last_low = swings['swing_lows'][-1]['price']
        if abs(candles[-1]['close'] - last_low) / last_low < 0.02:
            return 'accumulation'
    
    # Distribution (Sideways after uptrend)
    if len(swings['swing_highs']) > 0:
        last_high = swings['swing_highs'][-1]['price']
        if abs(candles[-1]['close'] - last_high) / last_high < 0.02:
            return 'distribution'
    
    return 'ranging'


def detect_mss(candles: List[Dict]) -> bool:
    """
    Detect Market Structure Shift
    - Bullish MSS: Price breaks above previous high
    - Bearish MSS: Price breaks below previous low
    """
    if len(candles) < 10:
        return False
    
    swings = find_swing_points(candles, left_bars=3, right_bars=3)
    
    if len(swings['swing_highs']) < 2 or len(swings['swing_lows']) < 2:
        return False
    
    current_price = candles[-1]['close']
    prev_high = swings['swing_highs'][-2]['price']
    prev_low = swings['swing_lows'][-2]['price']
    
    # Check for breakout
    if current_price > prev_high * 1.001:  # 0.1% above previous high
        return True
    if current_price < prev_low * 0.999:  # 0.1% below previous low
        return True
    
    return False