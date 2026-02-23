"""
Order Block Detection
- Bullish/Bearish Order Blocks
- Mitigation
- Entry levels
"""

from typing import Dict, List, Optional
import numpy as np  # ✅ NumPy ইম্পোর্ট যোগ করুন


def detect_order_block(candles: List[Dict]) -> Optional[Dict]:
    """
    Detect Order Blocks
    OB = Last candle before impulsive move
    
    Args:
        candles: List of candle dictionaries with 'open', 'high', 'low', 'close', 'time'
    
    Returns:
        Dictionary with order block details or None
    """
    if len(candles) < 10:
        return None
    
    # Find impulsive moves (looking back from recent to older)
    for i in range(len(candles) - 5, 3, -1):
        current = candles[i]
        next_candles = candles[i+1:i+4]  # Next 3 candles after current
        
        if len(next_candles) < 3:
            continue
        
        # Calculate average range of previous candles
        prev_candles = candles[max(0, i-10):i]
        if len(prev_candles) < 5:
            continue
            
        avg_range = np.mean([c['high'] - c['low'] for c in prev_candles])
        
        # Bullish OB (large bullish candle followed by impulsive move up)
        if current['close'] > current['open']:  # Bullish candle
            move_up = next_candles[0]['high'] - current['high']
            if move_up > avg_range * 1.5:  # Impulsive move
                return {
                    'type': 'bullish',
                    'top': current['high'],
                    'bottom': current['low'],
                    'entry': current['high'] - (current['high'] - current['low']) * 0.5,
                    'price': current['low'] + (current['high'] - current['low']) * 0.382,  # 38.2% retrace
                    'time': current['time'],
                    'range': f"{current['low']:.2f} - {current['high']:.2f}"
                }
        
        # Bearish OB (large bearish candle followed by impulsive move down)
        else:  # Bearish candle
            move_down = current['low'] - next_candles[0]['low']
            if abs(move_down) > avg_range * 1.5:
                return {
                    'type': 'bearish',
                    'top': current['high'],
                    'bottom': current['low'],
                    'entry': current['low'] + (current['high'] - current['low']) * 0.5,
                    'price': current['high'] - (current['high'] - current['low']) * 0.382,
                    'time': current['time'],
                    'range': f"{current['low']:.2f} - {current['high']:.2f}"
                }
    
    return None


def detect_order_block_v2(candles: List[Dict]) -> Optional[Dict]:
    """
    Alternative Order Block detection method
    Based on imbalance and liquidity
    """
    if len(candles) < 20:
        return None
    
    # Look for large candles with small wicks (strong momentum)
    for i in range(len(candles) - 10, 5, -1):
        current = candles[i]
        
        # Calculate candle body and wicks
        body = abs(current['close'] - current['open'])
        total_range = current['high'] - current['low']
        
        if total_range == 0:
            continue
            
        # Strong candle with small wicks (>60% body)
        if body / total_range > 0.6:
            # Check if this candle was followed by continuation
            next_candles = candles[i+1:i+4]
            if len(next_candles) < 3:
                continue
                
            avg_next_move = np.mean([c['high'] - c['low'] for c in next_candles])
            
            if avg_next_move > total_range * 0.5:
                if current['close'] > current['open']:  # Bullish
                    return {
                        'type': 'bullish',
                        'top': current['high'],
                        'bottom': current['low'],
                        'entry': current['low'] + total_range * 0.382,
                        'price': current['low'],
                        'time': current['time']
                    }
                else:  # Bearish
                    return {
                        'type': 'bearish',
                        'top': current['high'],
                        'bottom': current['low'],
                        'entry': current['high'] - total_range * 0.382,
                        'price': current['high'],
                        'time': current['time']
                    }
    
    return None


def validate_ob(ob: Dict, current_price: float) -> bool:
    """
    Check if Order Block is still valid (not mitigated)
    
    Args:
        ob: Order block dictionary
        current_price: Current market price
    
    Returns:
        True if still valid, False if mitigated
    """
    if not ob:
        return False
    
    if ob['type'] == 'bullish':
        # For bullish OB, price shouldn't break below OB low
        return current_price > ob['bottom']
    else:
        # For bearish OB, price shouldn't break above OB high
        return current_price < ob['top']


def get_ob_entry(ob: Dict, current_price: float) -> Optional[float]:
    """
    Get entry price for Order Block
    
    Args:
        ob: Order block dictionary
        current_price: Current market price
    
    Returns:
        Entry price or None
    """
    if not ob:
        return None
    
    # If OB has entry field, use it
    if ob.get('entry'):
        return ob['entry']
    
    # Otherwise calculate based on type
    if ob['type'] == 'bullish':
        return ob['bottom'] + (ob['top'] - ob['bottom']) * 0.382
    else:
        return ob['top'] - (ob['top'] - ob['bottom']) * 0.382


def get_ob_stop_loss(ob: Dict) -> Optional[float]:
    """
    Get stop loss for Order Block
    
    Args:
        ob: Order block dictionary
    
    Returns:
        Stop loss price or None
    """
    if not ob:
        return None
    
    if ob['type'] == 'bullish':
        return ob['bottom'] - (ob['top'] - ob['bottom']) * 0.5
    else:
        return ob['top'] + (ob['top'] - ob['bottom']) * 0.5


def is_ob_mitigated(ob: Dict, candles: List[Dict]) -> bool:
    """
    Check if Order Block has been mitigated by price
    
    Args:
        ob: Order block dictionary
        candles: Recent price candles
    
    Returns:
        True if mitigated, False otherwise
    """
    if not ob or not candles:
        return False
    
    recent_candles = candles[-10:]
    
    for candle in recent_candles:
        if ob['type'] == 'bullish':
            # Price entered the OB zone
            if candle['low'] <= ob['top'] and candle['high'] >= ob['bottom']:
                return True
        else:
            if candle['high'] >= ob['bottom'] and candle['low'] <= ob['top']:
                return True
    
    return False