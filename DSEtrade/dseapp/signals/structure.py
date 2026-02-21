"""
Market Structure Detection
- Swing Highs/Lows
- Market Structure Shifts (MSS)
- Trend Analysis
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
from .utils import find_swing_points 


def find_swing_points(candles: List[Dict], left_bars: int = 5, right_bars: int = 5) -> Dict:
    """
    Find swing highs and lows
    """
    highs = [c['high'] for c in candles]
    lows = [c['low'] for c in candles]
    
    swing_highs = []
    swing_lows = []
    
    for i in range(left_bars, len(candles) - right_bars):
        # Swing High
        if all(highs[i] > highs[i-j] for j in range(1, left_bars+1)) and \
           all(highs[i] > highs[i+j] for j in range(1, right_bars+1)):
            swing_highs.append({
                'index': i,
                'price': highs[i],
                'time': candles[i]['time']
            })
        
        # Swing Low
        if all(lows[i] < lows[i-j] for j in range(1, left_bars+1)) and \
           all(lows[i] < lows[i+j] for j in range(1, right_bars+1)):
            swing_lows.append({
                'index': i,
                'price': lows[i],
                'time': candles[i]['time']
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