"""
Order Block Detection
- Bullish/Bearish Order Blocks
- Mitigation
- Entry levels
- Complete validation
"""

from typing import Dict, List, Optional, Union, Any
import numpy as np


def detect_order_block(candles: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
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
    
    results = []
    
    # Find impulsive moves (looking back from recent to older)
    for i in range(len(candles) - 5, 3, -1):
        try:
            current = candles[i]
            next_candles = candles[i+1:i+4]  # Next 3 candles after current
            
            if len(next_candles) < 2:  # Need at least 2 candles for confirmation
                continue
            
            # Calculate average range of previous candles
            prev_candles = candles[max(0, i-10):i]
            if len(prev_candles) < 5:
                continue
                
            avg_range = float(np.mean([c['high'] - c['low'] for c in prev_candles]))
            
            # Bullish OB (large bullish candle followed by impulsive move up)
            if current['close'] > current['open']:  # Bullish candle
                max_next_high = max(c['high'] for c in next_candles[:2])
                move_up = max_next_high - current['high']
                
                if move_up > avg_range * 1.2:  # Impulsive move (slightly reduced threshold)
                    ob_range = current['high'] - current['low']
                    entry_price = current['low'] + ob_range * 0.382  # 38.2% retrace
                    
                    result = {
                        'type': 'bullish',
                        'top': float(current['high']),
                        'bottom': float(current['low']),
                        'entry': float(entry_price),
                        'price': float(current['close']),
                        'time': current.get('time', i),
                        'range': float(ob_range),
                        'move_size': float(move_up),
                        'confidence': 'high' if move_up > avg_range * 2.0 else 'medium'
                    }
                    results.append(result)
                    
                    # Return the most recent significant OB
                    if move_up > avg_range * 1.5:
                        return result
            
            # Bearish OB (large bearish candle followed by impulsive move down)
            else:  # Bearish candle
                min_next_low = min(c['low'] for c in next_candles[:2])
                move_down = current['low'] - min_next_low
                
                if abs(move_down) > avg_range * 1.2:
                    ob_range = current['high'] - current['low']
                    entry_price = current['high'] - ob_range * 0.382
                    
                    result = {
                        'type': 'bearish',
                        'top': float(current['high']),
                        'bottom': float(current['low']),
                        'entry': float(entry_price),
                        'price': float(current['close']),
                        'time': current.get('time', i),
                        'range': float(ob_range),
                        'move_size': float(abs(move_down)),
                        'confidence': 'high' if abs(move_down) > avg_range * 2.0 else 'medium'
                    }
                    results.append(result)
                    
                    if abs(move_down) > avg_range * 1.5:
                        return result
                        
        except (KeyError, IndexError, TypeError) as e:
            print(f"Error in OB detection: {e}")
            continue
    
    # Return the most recent OB if found
    return results[-1] if results else None


def detect_order_block_v2(candles: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """
    Alternative Order Block detection method
    Based on imbalance and liquidity
    
    Args:
        candles: List of candle dictionaries
    
    Returns:
        Dictionary with order block details or None
    """
    if len(candles) < 20:
        return None
    
    results = []
    
    # Look for large candles with small wicks (strong momentum)
    for i in range(len(candles) - 10, 5, -1):
        try:
            current = candles[i]
            
            # Calculate candle body and wicks
            body = abs(current['close'] - current['open'])
            total_range = current['high'] - current['low']
            
            if total_range == 0:
                continue
                
            # Strong candle with small wicks (>60% body)
            body_ratio = body / total_range
            if body_ratio > 0.6:
                # Check if this candle was followed by continuation
                next_candles = candles[i+1:i+4]
                if len(next_candles) < 2:
                    continue
                    
                avg_next_move = np.mean([c['high'] - c['low'] for c in next_candles])
                
                if avg_next_move > total_range * 0.5:
                    if current['close'] > current['open']:  # Bullish
                        result = {
                            'type': 'bullish',
                            'top': float(current['high']),
                            'bottom': float(current['low']),
                            'entry': float(current['low'] + total_range * 0.382),
                            'price': float(current['low']),
                            'time': current.get('time', i),
                            'range': float(total_range),
                            'body_ratio': float(body_ratio),
                            'confidence': 'high' if body_ratio > 0.8 else 'medium'
                        }
                        results.append(result)
                        
                    else:  # Bearish
                        result = {
                            'type': 'bearish',
                            'top': float(current['high']),
                            'bottom': float(current['low']),
                            'entry': float(current['high'] - total_range * 0.382),
                            'price': float(current['high']),
                            'time': current.get('time', i),
                            'range': float(total_range),
                            'body_ratio': float(body_ratio),
                            'confidence': 'high' if body_ratio > 0.8 else 'medium'
                        }
                        results.append(result)
                        
        except (KeyError, IndexError, TypeError) as e:
            print(f"Error in OB V2 detection: {e}")
            continue
    
    return results[-1] if results else None


def validate_ob(ob: Optional[Union[Dict, float]], current_price: float) -> bool:
    """
    Check if Order Block is still valid (not mitigated)
    
    Args:
        ob: Order block dictionary or None
        current_price: Current market price
    
    Returns:
        True if still valid, False if mitigated
    """
    # Check if ob is None or not a dictionary
    if ob is None or not isinstance(ob, dict):
        return False
    
    # Check if required keys exist
    if 'type' not in ob or 'bottom' not in ob or 'top' not in ob:
        return False
    
    try:
        if ob['type'] == 'bullish':
            # For bullish OB, price shouldn't break below OB low
            return current_price > float(ob['bottom'])
        else:
            # For bearish OB, price shouldn't break above OB high
            return current_price < float(ob['top'])
    except (TypeError, ValueError):
        return False


def get_ob_entry(ob: Optional[Union[Dict, float]], current_price: float) -> Optional[float]:
    """
    Get entry price for Order Block
    
    Args:
        ob: Order block dictionary or None
        current_price: Current market price
    
    Returns:
        Entry price or None
    """
    if ob is None or not isinstance(ob, dict):
        return None
    
    try:
        # If OB has entry field, use it
        if ob.get('entry') is not None:
            return float(ob['entry'])
        
        # Otherwise calculate based on type
        if ob.get('type') == 'bullish':
            bottom = float(ob.get('bottom', 0))
            top = float(ob.get('top', 0))
            return bottom + (top - bottom) * 0.382
        else:
            bottom = float(ob.get('bottom', 0))
            top = float(ob.get('top', 0))
            return top - (top - bottom) * 0.382
            
    except (TypeError, ValueError, KeyError):
        return None


def get_ob_stop_loss(ob: Optional[Union[Dict, float]]) -> Optional[float]:
    """
    Get stop loss for Order Block
    
    Args:
        ob: Order block dictionary or None
    
    Returns:
        Stop loss price or None
    """
    if ob is None or not isinstance(ob, dict):
        return None
    
    try:
        if ob.get('type') == 'bullish':
            bottom = float(ob.get('bottom', 0))
            top = float(ob.get('top', 0))
            return bottom - (top - bottom) * 0.5
        else:
            bottom = float(ob.get('bottom', 0))
            top = float(ob.get('top', 0))
            return top + (top - bottom) * 0.5
            
    except (TypeError, ValueError, KeyError):
        return None


def is_ob_mitigated(ob: Optional[Union[Dict, float]], candles: List[Dict]) -> bool:
    """
    Check if Order Block has been mitigated by price
    
    Args:
        ob: Order block dictionary or None
        candles: Recent price candles
    
    Returns:
        True if mitigated, False otherwise
    """
    if ob is None or not isinstance(ob, dict) or not candles:
        return False
    
    try:
        recent_candles = candles[-10:]
        ob_type = ob.get('type', '')
        ob_bottom = float(ob.get('bottom', 0))
        ob_top = float(ob.get('top', 0))
        
        for candle in recent_candles:
            if ob_type == 'bullish':
                # Price entered the OB zone
                if candle['low'] <= ob_top and candle['high'] >= ob_bottom:
                    return True
            else:
                if candle['high'] >= ob_bottom and candle['low'] <= ob_top:
                    return True
                    
    except (TypeError, ValueError, KeyError):
        return False
    
    return False


def find_nearest_ob(candles: List[Dict], current_price: float, lookback: int = 50) -> Optional[Dict]:
    """
    Find the nearest Order Block to current price
    
    Args:
        candles: List of candle dictionaries
        current_price: Current market price
        lookback: Number of candles to look back
    
    Returns:
        Nearest order block or None
    """
    if len(candles) < lookback:
        return None
    
    recent_candles = candles[-lookback:]
    all_obs = []
    
    for i in range(len(recent_candles) - 10, 5, -1):
        ob = detect_order_block(recent_candles[:i+5])
        if ob and isinstance(ob, dict):
            all_obs.append(ob)
    
    if not all_obs:
        return None
    
    # Find OB closest to current price
    def price_distance(ob):
        try:
            entry = ob.get('entry', 0)
            return abs(entry - current_price)
        except (TypeError, ValueError):
            return float('inf')
    
    return min(all_obs, key=price_distance)