"""
Breaker Block Detection for SMC
- Bullish Breaker Blocks
- Bearish Breaker Blocks
- Breaker validation
- Complete error handling
"""

from typing import Dict, List, Optional, Union, Any
from .utils import find_swing_points, calculate_atr


def detect_breaker(candles: List[Dict[str, Any]]) -> bool:
    """
    Simple breaker detection (backward compatibility)
    
    Args:
        candles: List of candle dictionaries
    
    Returns:
        True if breaker detected, False otherwise
    """
    try:
        if len(candles) < 20:
            return False
        
        swings = find_swing_points(candles, left_bars=3, right_bars=3)
        
        if not swings or not isinstance(swings, dict):
            return False
        
        swing_lows = swings.get('swing_lows', [])
        if len(swing_lows) < 2:
            return False
        
        # Get previous low safely
        prev_low_data = swing_lows[-2]
        if not isinstance(prev_low_data, dict):
            return False
        
        prev_low = prev_low_data.get('price', 0)
        current_price = candles[-1].get('close', 0)
        
        # Check for bullish breaker (price above previous low after sweep)
        return current_price > prev_low
        
    except Exception as e:
        print(f"Error in detect_breaker: {e}")
        return False


def detect_breaker_block(candles: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """
    Detect Breaker Blocks
    
    Args:
        candles: List of candle dictionaries
    
    Returns:
        Dictionary with breaker block information or None
    """
    try:
        if len(candles) < 20:
            return None
        
        swings = find_swing_points(candles, left_bars=3, right_bars=3)
        
        if not swings or not isinstance(swings, dict):
            return None
        
        swing_highs = swings.get('swing_highs', [])
        swing_lows = swings.get('swing_lows', [])
        
        if len(swing_highs) < 2 or len(swing_lows) < 2:
            return None
        
        atr = calculate_atr(candles, period=14)
        if atr == 0 or atr is None:
            atr = 10.0
        
        current_price = candles[-1].get('close', 0)
        current_time = candles[-1].get('time', '')
        
        # Bullish Breaker (price swept low then reversed)
        if len(swing_lows) >= 2:
            recent_low_data = swing_lows[-1]
            prev_low_data = swing_lows[-2]
            
            if isinstance(recent_low_data, dict) and isinstance(prev_low_data, dict):
                recent_low = recent_low_data.get('price', 0)
                prev_low = prev_low_data.get('price', 0)
                
                # Check if price swept below previous low
                swept = False
                for candle in candles[-10:]:
                    if isinstance(candle, dict) and candle.get('low', 0) < prev_low:
                        swept = True
                        break
                
                if swept and current_price > prev_low:
                    # Calculate entry (38.2% retrace of the breaker range)
                    breaker_range = abs(prev_low - recent_low)
                    entry = prev_low + (breaker_range * 0.382)
                    
                    return {
                        'type': 'bullish',
                        'price': float(prev_low),
                        'low': float(min(prev_low, recent_low)),
                        'high': float(max(prev_low, recent_low)),
                        'entry': float(entry),
                        'time': current_time,
                        'confidence': 'high' if swept else 'medium',
                        'atr': float(atr)
                    }
        
        # Bearish Breaker (price swept high then reversed)
        if len(swing_highs) >= 2:
            recent_high_data = swing_highs[-1]
            prev_high_data = swing_highs[-2]
            
            if isinstance(recent_high_data, dict) and isinstance(prev_high_data, dict):
                recent_high = recent_high_data.get('price', 0)
                prev_high = prev_high_data.get('price', 0)
                
                # Check if price swept above previous high
                swept = False
                for candle in candles[-10:]:
                    if isinstance(candle, dict) and candle.get('high', 0) > prev_high:
                        swept = True
                        break
                
                if swept and current_price < prev_high:
                    # Calculate entry (38.2% retrace of the breaker range)
                    breaker_range = abs(prev_high - recent_high)
                    entry = prev_high - (breaker_range * 0.382)
                    
                    return {
                        'type': 'bearish',
                        'price': float(prev_high),
                        'low': float(min(prev_high, recent_high)),
                        'high': float(max(prev_high, recent_high)),
                        'entry': float(entry),
                        'time': current_time,
                        'confidence': 'high' if swept else 'medium',
                        'atr': float(atr)
                    }
        
        return None
        
    except Exception as e:
        print(f"Error in detect_breaker_block: {e}")
        return None


def detect_breaker_block_v2(candles: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """
    Alternative Breaker Block detection method
    Based on Order Flow and Mitigation
    """
    try:
        if len(candles) < 15:
            return None
        
        # Look for impulsive moves
        for i in range(len(candles) - 10, len(candles) - 3):
            if i < 0 or i >= len(candles):
                continue
                
            current = candles[i]
            if not isinstance(current, dict):
                continue
            
            current_high = current.get('high', 0)
            current_low = current.get('low', 0)
            current_close = current.get('close', 0)
            current_open = current.get('open', 0)
            current_time = current.get('time', '')
            
            # Bullish Breaker
            if current_close > current_open:  # Bullish candle
                # Check if this candle was part of a breakout
                if i > 5:
                    prev_highs = []
                    for c in candles[i-5:i]:
                        if isinstance(c, dict):
                            prev_highs.append(c.get('high', 0))
                    
                    if prev_highs and current_high > max(prev_highs):
                        # Look for mitigation (price came back to this candle)
                        for j in range(i + 1, min(i + 10, len(candles))):
                            if j < len(candles):
                                candle_j = candles[j]
                                if isinstance(candle_j, dict):
                                    if candle_j.get('low', 0) <= current_high <= candle_j.get('high', 0):
                                        candle_range = current_high - current_low
                                        return {
                                            'type': 'bullish',
                                            'price': float(current_high),
                                            'low': float(current_low),
                                            'high': float(current_high),
                                            'entry': float(current_high - candle_range * 0.382),
                                            'time': current_time,
                                            'confidence': 'medium'
                                        }
            
            # Bearish Breaker
            else:  # Bearish candle
                if i > 5:
                    prev_lows = []
                    for c in candles[i-5:i]:
                        if isinstance(c, dict):
                            prev_lows.append(c.get('low', 0))
                    
                    if prev_lows and current_low < min(prev_lows):
                        for j in range(i + 1, min(i + 10, len(candles))):
                            if j < len(candles):
                                candle_j = candles[j]
                                if isinstance(candle_j, dict):
                                    if candle_j.get('high', 0) >= current_low >= candle_j.get('low', 0):
                                        candle_range = current_high - current_low
                                        return {
                                            'type': 'bearish',
                                            'price': float(current_low),
                                            'low': float(current_low),
                                            'high': float(current_high),
                                            'entry': float(current_low + candle_range * 0.382),
                                            'time': current_time,
                                            'confidence': 'medium'
                                        }
        
        return None
        
    except Exception as e:
        print(f"Error in detect_breaker_block_v2: {e}")
        return None


def validate_breaker(breaker: Optional[Union[Dict, float]], current_price: float) -> bool:
    """
    Validate if Breaker Block is still valid
    
    Args:
        breaker: Breaker block dictionary or None
        current_price: Current market price
    
    Returns:
        True if still valid, False if mitigated
    """
    if breaker is None or not isinstance(breaker, dict):
        return False
    
    try:
        breaker_type = breaker.get('type', '')
        breaker_price = breaker.get('price', 0)
        
        if breaker_type == 'bullish':
            return current_price > float(breaker_price)
        else:
            return current_price < float(breaker_price)
            
    except (TypeError, ValueError, AttributeError):
        return False


def get_breaker_entry(breaker: Optional[Union[Dict, float]], current_price: float) -> Optional[float]:
    """
    Get entry price for Breaker Block
    
    Args:
        breaker: Breaker block dictionary or None
        current_price: Current market price
    
    Returns:
        Entry price or None
    """
    if breaker is None or not isinstance(breaker, dict):
        return None
    
    try:
        # If entry is provided, use it
        if breaker.get('entry') is not None:
            return float(breaker['entry'])
        
        # Default entry logic
        breaker_type = breaker.get('type', '')
        breaker_price = breaker.get('price', 0)
        low = breaker.get('low', 0)
        high = breaker.get('high', 0)
        
        if breaker_type == 'bullish':
            return float(breaker_price + (high - low) * 0.382)
        else:
            return float(breaker_price - (high - low) * 0.382)
            
    except (TypeError, ValueError, AttributeError):
        return None


def get_breaker_stop_loss(breaker: Optional[Union[Dict, float]]) -> Optional[float]:
    """
    Get stop loss for Breaker Block
    
    Args:
        breaker: Breaker block dictionary or None
    
    Returns:
        Stop loss price or None
    """
    if breaker is None or not isinstance(breaker, dict):
        return None
    
    try:
        low = breaker.get('low', 0)
        high = breaker.get('high', 0)
        
        if breaker.get('type') == 'bullish':
            return float(low - (high - low) * 0.5)
        else:
            return float(high + (high - low) * 0.5)
            
    except (TypeError, ValueError, AttributeError):
        return None


def is_breaker_mitigated(breaker: Optional[Union[Dict, float]], candles: List[Dict]) -> bool:
    """
    Check if Breaker Block has been mitigated
    
    Args:
        breaker: Breaker block dictionary or None
        candles: Recent price candles
    
    Returns:
        True if mitigated, False otherwise
    """
    if breaker is None or not isinstance(breaker, dict) or not candles:
        return False
    
    try:
        recent_candles = candles[-10:]
        breaker_type = breaker.get('type', '')
        low = breaker.get('low', 0)
        high = breaker.get('high', 0)
        
        for candle in recent_candles:
            if not isinstance(candle, dict):
                continue
                
            candle_low = candle.get('low', 0)
            candle_high = candle.get('high', 0)
            
            if breaker_type == 'bullish':
                # Price entered the breaker zone
                if candle_low <= high and candle_high >= low:
                    return True
            else:
                if candle_high >= low and candle_low <= high:
                    return True
                    
    except (TypeError, ValueError, AttributeError):
        return False
    
    return False