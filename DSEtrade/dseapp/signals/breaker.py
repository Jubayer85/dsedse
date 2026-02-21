"""
Breaker Block Detection for SMC
- Bullish Breaker Blocks
- Bearish Breaker Blocks
- Breaker validation
"""

from typing import Dict, List, Optional
from .utils import find_swing_points, calculate_atr


def detect_breaker_block(candles: List[Dict]) -> Optional[Dict]:
    """
    Detect Breaker Blocks
    Breaker Block = Last candle before a strong move that gets mitigated
    
    Returns:
        Dict with breaker block information or None
    """
    if len(candles) < 20:
        return None
    
    # Find recent swings
    swings = find_swing_points(candles, left_bars=3, right_bars=3)
    
    if len(swings['swing_highs']) < 2 or len(swings['swing_lows']) < 2:
        return None
    
    atr = calculate_atr(candles, period=14)
    if atr == 0:
        atr = 10  # Default if ATR calculation fails
    
    current_price = candles[-1]['close']
    
    # Check for bullish breaker (price swept low then reversed)
    if len(swings['swing_lows']) >= 2:
        recent_low = swings['swing_lows'][-1]['price']
        prev_low = swings['swing_lows'][-2]['price']
        
        # Check if price swept below previous low and reversed
        for candle in candles[-10:]:
            if candle['low'] < prev_low * 0.999:  # Swept below previous low
                if current_price > prev_low:  # Reversed back above
                    # Find potential breaker block
                    for i in range(len(candles) - 10, len(candles) - 3):
                        if candles[i]['low'] <= prev_low <= candles[i]['high']:
                            return {
                                'type': 'bullish',
                                'price': prev_low,
                                'low': candles[i]['low'],
                                'high': candles[i]['high'],
                                'entry': prev_low + atr * 0.5,
                                'time': candles[i]['time'],
                                'confidence': 'high'
                            }
    
    # Check for bearish breaker (price swept high then reversed)
    if len(swings['swing_highs']) >= 2:
        recent_high = swings['swing_highs'][-1]['price']
        prev_high = swings['swing_highs'][-2]['price']
        
        # Check if price swept above previous high and reversed
        for candle in candles[-10:]:
            if candle['high'] > prev_high * 1.001:  # Swept above previous high
                if current_price < prev_high:  # Reversed back below
                    # Find potential breaker block
                    for i in range(len(candles) - 10, len(candles) - 3):
                        if candles[i]['low'] <= prev_high <= candles[i]['high']:
                            return {
                                'type': 'bearish',
                                'price': prev_high,
                                'low': candles[i]['low'],
                                'high': candles[i]['high'],
                                'entry': prev_high - atr * 0.5,
                                'time': candles[i]['time'],
                                'confidence': 'high'
                            }
    
    return None


def detect_breaker_block_v2(candles: List[Dict]) -> Optional[Dict]:
    """
    Alternative Breaker Block detection method
    Based on Order Flow and Mitigation
    """
    if len(candles) < 15:
        return None
    
    # Look for impulsive moves
    for i in range(len(candles) - 10, len(candles) - 3):
        # Bullish Breaker
        if candles[i]['close'] > candles[i]['open']:  # Bullish candle
            # Check if this candle was part of a breakout
            if i > 5 and candles[i]['high'] > max(c['high'] for c in candles[i-5:i]):
                # Look for mitigation (price came back to this candle)
                for j in range(i + 1, len(candles)):
                    if candles[j]['low'] <= candles[i]['high'] <= candles[j]['high']:
                        return {
                            'type': 'bullish',
                            'price': candles[i]['high'],
                            'low': candles[i]['low'],
                            'high': candles[i]['high'],
                            'entry': candles[i]['high'] - (candles[i]['high'] - candles[i]['low']) * 0.5,
                            'time': candles[i]['time'],
                            'confidence': 'medium'
                        }
        
        # Bearish Breaker
        else:  # Bearish candle
            if i > 5 and candles[i]['low'] < min(c['low'] for c in candles[i-5:i]):
                for j in range(i + 1, len(candles)):
                    if candles[j]['high'] >= candles[i]['low'] >= candles[j]['low']:
                        return {
                            'type': 'bearish',
                            'price': candles[i]['low'],
                            'low': candles[i]['low'],
                            'high': candles[i]['high'],
                            'entry': candles[i]['low'] + (candles[i]['high'] - candles[i]['low']) * 0.5,
                            'time': candles[i]['time'],
                            'confidence': 'medium'
                        }
    
    return None


def validate_breaker(breaker: Dict, current_price: float) -> bool:
    """
    Validate if Breaker Block is still valid
    """
    if not breaker:
        return False
    
    if breaker['type'] == 'bullish':
        # For bullish breaker, price should be above breaker price
        return current_price > breaker['price']
    else:
        # For bearish breaker, price should be below breaker price
        return current_price < breaker['price']


def get_breaker_entry(breaker: Dict, current_price: float) -> Optional[float]:
    """
    Get entry price for Breaker Block
    """
    if not breaker:
        return None
    
    if breaker.get('entry'):
        return breaker['entry']
    
    # Default entry logic
    if breaker['type'] == 'bullish':
        return breaker['price'] + (breaker['high'] - breaker['low']) * 0.382
    else:
        return breaker['price'] - (breaker['high'] - breaker['low']) * 0.382


def get_breaker_stop_loss(breaker: Dict) -> Optional[float]:
    """
    Get stop loss for Breaker Block
    """
    if not breaker:
        return None
    
    if breaker['type'] == 'bullish':
        return breaker['low'] - (breaker['high'] - breaker['low']) * 0.5
    else:
        return breaker['high'] + (breaker['high'] - breaker['low']) * 0.5