"""
Mitigation Detection for SMC
- Order Block Mitigation
- FVG Mitigation
- Breaker Mitigation
"""

from typing import Dict, List, Optional
from .utils import find_swing_points


def detect_mitigation(candles: List[Dict]) -> bool:
    """
    Detect if any key level has been mitigated
    Mitigation = Price returned to and interacted with a key level
    """
    if len(candles) < 20:
        return False
    
    # Recent price action
    recent_candles = candles[-10:]
    current_price = candles[-1]['close']
    
    # Find key levels from older data
    older_candles = candles[-30:-10]
    if len(older_candles) < 5:
        return False
    
    swings = find_swing_points(older_candles, left_bars=3, right_bars=3)
    
    # Check mitigation of swing highs
    for high in swings['swing_highs']:
        # Price came back to swing high level
        if abs(current_price - high['price']) / high['price'] < 0.005:  # 0.5% proximity
            # Check if price interacted with this level recently
            for candle in recent_candles:
                if abs(candle['high'] - high['price']) / high['price'] < 0.003:
                    if candle['close'] < high['price']:  # Rejection
                        return True
    
    # Check mitigation of swing lows
    for low in swings['swing_lows']:
        if abs(current_price - low['price']) / low['price'] < 0.005:
            for candle in recent_candles:
                if abs(candle['low'] - low['price']) / low['price'] < 0.003:
                    if candle['close'] > low['price']:  # Rejection
                        return True
    
    return False


def detect_order_block_mitigation(candles: List[Dict], order_block: Dict) -> bool:
    """
    Check if a specific Order Block has been mitigated
    """
    if not order_block:
        return False
    
    recent_candles = candles[-5:]
    ob_price = order_block.get('entry', 0)
    
    for candle in recent_candles:
        if order_block['type'] == 'bullish':
            # Price dipped into OB and rejected
            if candle['low'] <= ob_price <= candle['high']:
                if candle['close'] > ob_price:
                    return True
        else:
            # Price rose into OB and rejected
            if candle['low'] <= ob_price <= candle['high']:
                if candle['close'] < ob_price:
                    return True
    
    return False


def detect_fvg_mitigation(candles: List[Dict], fvg: Dict) -> bool:
    """
    Check if a specific FVG has been mitigated
    """
    if not fvg:
        return False
    
    recent_candles = candles[-5:]
    
    for candle in recent_candles:
        if fvg['type'] == 'bullish':
            # Price entered bullish FVG
            if candle['low'] <= fvg['top'] and candle['high'] >= fvg['bottom']:
                return True
        else:
            # Price entered bearish FVG
            if candle['high'] >= fvg['bottom'] and candle['low'] <= fvg['top']:
                return True
    
    return False


def detect_liquidity_mitigation(candles: List[Dict], level: float) -> bool:
    """
    Check if a specific liquidity level has been mitigated
    """
    recent_candles = candles[-3:]
    
    for candle in recent_candles:
        if abs(candle['close'] - level) / level < 0.002:  # 0.2% proximity
            return True
    
    return False