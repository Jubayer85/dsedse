"""
Fair Value Gap (FVG) Detection
- Bullish/Bearish FVG
- FVG validation
- Entry levels
- Complete error handling
"""

from typing import Dict, List, Optional, Union, Any


def detect_fvg(candles: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """
    Detect Fair Value Gaps
    FVG = Gap between candle1's low and candle3's high (bullish)
          or candle1's high and candle3's low (bearish)
    
    Args:
        candles: List of candle dictionaries with 'high', 'low', 'close', 'time'
    
    Returns:
        Dictionary with FVG details or None
    """
    try:
        if len(candles) < 3:
            return None
        
        fvg_list = []
        
        for i in range(len(candles) - 2):
            c1 = candles[i]      # First candle
            c2 = candles[i+1]    # Middle candle
            c3 = candles[i+2]    # Third candle
            
            # Validate candles are dictionaries
            if not all(isinstance(c, dict) for c in [c1, c2, c3]):
                continue
            
            # Extract values safely
            c1_high = float(c1.get('high', 0))
            c1_low = float(c1.get('low', 0))
            c2_high = float(c2.get('high', 0))
            c2_low = float(c2.get('low', 0))
            c3_high = float(c3.get('high', 0))
            c3_low = float(c3.get('low', 0))
            c2_time = c2.get('time', i)
            
            # Calculate ranges
            c2_range = c2_high - c2_low
            c1_range = c1_high - c1_low
            c3_range = c3_high - c3_low
            avg_range = (c1_range + c3_range) / 2 if (c1_range + c3_range) > 0 else 1.0
            
            # Check if middle candle is small (indecision)
            if c2_range > avg_range * 0.5:
                continue  # Middle candle too large
            
            # Bullish FVG (c3 low > c1 high)
            if c3_low > c1_high:
                gap_size = c3_low - c1_high
                fvg = {
                    'type': 'bullish',
                    'top': float(c3_low),
                    'bottom': float(c1_high),
                    'mid': float((c3_low + c1_high) / 2),
                    'entry': float(c1_high + gap_size * 0.382),  # 38.2% retrace
                    'time': c2_time,
                    'range': float(gap_size),
                    'price': float(c3.get('close', 0)),
                    'index': i
                }
                fvg_list.append(fvg)
            
            # Bearish FVG (c3 high < c1 low)
            elif c3_high < c1_low:
                gap_size = c1_low - c3_high
                fvg = {
                    'type': 'bearish',
                    'top': float(c1_low),
                    'bottom': float(c3_high),
                    'mid': float((c1_low + c3_high) / 2),
                    'entry': float(c1_low - gap_size * 0.382),
                    'time': c2_time,
                    'range': float(gap_size),
                    'price': float(c3.get('close', 0)),
                    'index': i
                }
                fvg_list.append(fvg)
        
        # Return the most recent FVG
        return fvg_list[-1] if fvg_list else None
        
    except Exception as e:
        print(f"Error in detect_fvg: {e}")
        return None


def validate_fvg(fvg: Optional[Union[Dict, float]], current_price: float) -> bool:
    """
    Validate if FVG is still valid (not mitigated)
    
    Args:
        fvg: FVG dictionary or None
        current_price: Current market price
    
    Returns:
        True if valid, False if mitigated
    """
    if fvg is None or not isinstance(fvg, dict):
        return False
    
    try:
        fvg_type = fvg.get('type', '')
        bottom = float(fvg.get('bottom', 0))
        top = float(fvg.get('top', 0))
        
        if fvg_type == 'bullish':
            # For bullish FVG, price should be above the bottom
            return current_price > bottom
        else:
            # For bearish FVG, price should be below the top
            return current_price < top
            
    except (TypeError, ValueError, AttributeError):
        return False


def get_fvg_entry(fvg: Optional[Union[Dict, float]]) -> Optional[float]:
    """
    Get entry price for FVG
    
    Args:
        fvg: FVG dictionary or None
    
    Returns:
        Entry price or None
    """
    if fvg is None or not isinstance(fvg, dict):
        return None
    
    try:
        # If entry is provided, use it
        if fvg.get('entry') is not None:
            return float(fvg['entry'])
        
        # Calculate entry based on type
        fvg_type = fvg.get('type', '')
        bottom = float(fvg.get('bottom', 0))
        top = float(fvg.get('top', 0))
        
        if fvg_type == 'bullish':
            return bottom + (top - bottom) * 0.382
        else:
            return top - (top - bottom) * 0.382
            
    except (TypeError, ValueError, AttributeError):
        return None


def get_fvg_stop_loss(fvg: Optional[Union[Dict, float]]) -> Optional[float]:
    """
    Get stop loss for FVG
    
    Args:
        fvg: FVG dictionary or None
    
    Returns:
        Stop loss price or None
    """
    if fvg is None or not isinstance(fvg, dict):
        return None
    
    try:
        fvg_type = fvg.get('type', '')
        bottom = float(fvg.get('bottom', 0))
        top = float(fvg.get('top', 0))
        gap_size = top - bottom if fvg_type == 'bullish' else bottom - top
        
        if fvg_type == 'bullish':
            return bottom - gap_size * 0.5
        else:
            return top + gap_size * 0.5
            
    except (TypeError, ValueError, AttributeError):
        return None


def is_fvg_mitigated(fvg: Optional[Union[Dict, float]], candles: List[Dict]) -> bool:
    """
    Check if FVG has been mitigated by price
    
    Args:
        fvg: FVG dictionary or None
        candles: Recent price candles
    
    Returns:
        True if mitigated, False otherwise
    """
    if fvg is None or not isinstance(fvg, dict) or not candles:
        return False
    
    try:
        recent_candles = candles[-10:]
        fvg_type = fvg.get('type', '')
        bottom = float(fvg.get('bottom', 0))
        top = float(fvg.get('top', 0))
        
        for candle in recent_candles:
            if not isinstance(candle, dict):
                continue
                
            candle_low = float(candle.get('low', 0))
            candle_high = float(candle.get('high', 0))
            
            if fvg_type == 'bullish':
                # Price entered the bullish FVG zone
                if candle_low <= top and candle_high >= bottom:
                    return True
            else:
                # Price entered the bearish FVG zone
                if candle_high >= bottom and candle_low <= top:
                    return True
                    
    except (TypeError, ValueError, AttributeError):
        return False
    
    return False


def find_nearest_fvg(candles: List[Dict], current_price: float, lookback: int = 50) -> Optional[Dict]:
    """
    Find the nearest FVG to current price
    
    Args:
        candles: List of candle dictionaries
        current_price: Current market price
        lookback: Number of candles to look back
    
    Returns:
        Nearest FVG or None
    """
    try:
        if len(candles) < lookback:
            return None
        
        recent_candles = candles[-lookback:]
        all_fvgs = []
        
        # Detect all FVGs in recent candles
        for i in range(len(recent_candles) - 2):
            fvg = detect_fvg(recent_candles[i:i+3])
            if fvg and isinstance(fvg, dict):
                all_fvgs.append(fvg)
        
        if not all_fvgs:
            return None
        
        # Find FVG closest to current price
        def price_distance(fvg):
            try:
                entry = float(fvg.get('entry', 0))
                return abs(entry - current_price)
            except (TypeError, ValueError):
                return float('inf')
        
        return min(all_fvgs, key=price_distance)
        
    except Exception as e:
        print(f"Error in find_nearest_fvg: {e}")
        return None


def get_fvg_strength(fvg: Optional[Union[Dict, float]]) -> str:
    """
    Get the strength of FVG based on gap size
    
    Args:
        fvg: FVG dictionary or None
    
    Returns:
        Strength: 'weak', 'medium', 'strong'
    """
    if fvg is None or not isinstance(fvg, dict):
        return 'weak'
    
    try:
        gap_size = float(fvg.get('range', 0))
        price = float(fvg.get('price', 1))
        
        if price == 0:
            return 'weak'
        
        gap_percentage = (gap_size / price) * 100
        
        if gap_percentage < 0.1:
            return 'weak'
        elif gap_percentage < 0.3:
            return 'medium'
        else:
            return 'strong'
            
    except (TypeError, ValueError, ZeroDivisionError):
        return 'weak'