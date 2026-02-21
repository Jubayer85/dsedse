"""
Utility Functions for SMC Engine
"""

import numpy as np
from typing import List, Dict


def calculate_atr(candles: List[Dict], period: int = 14) -> float:
    """
    Calculate Average True Range
    """
    if len(candles) < period + 1:
        return 0
    
    tr_values = []
    
    for i in range(1, len(candles)):
        high = candles[i]['high']
        low = candles[i]['low']
        prev_close = candles[i-1]['close']
        
        tr = max(
            high - low,
            abs(high - prev_close),
            abs(low - prev_close)
        )
        tr_values.append(tr)
    
    if len(tr_values) < period:
        return 0
    
    atr = np.mean(tr_values[-period:])
    return atr


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


def calculate_pivot_points(candles: List[Dict]) -> Dict:
    """
    Calculate pivot points for key levels
    """
    last = candles[-1]
    
    pivot = (last['high'] + last['low'] + last['close']) / 3
    
    return {
        'pivot': pivot,
        'r1': 2 * pivot - last['low'],
        's1': 2 * pivot - last['high'],
        'r2': pivot + (last['high'] - last['low']),
        's2': pivot - (last['high'] - last['low'])
    }


def normalize_data(data: List[float]) -> List[float]:
    """
    Normalize data for machine learning features
    """
    if not data:
        return data
    
    min_val = min(data)
    max_val = max(data)
    
    if max_val - min_val == 0:
        return [0.5 for _ in data]
    
    return [(x - min_val) / (max_val - min_val) for x in data]