"""
Liquidity Detection
- Stop hunts
- Liquidity sweeps
- Volume confirmed sweeps
- Key liquidity levels
- Complete error handling
"""

from typing import Dict, List, Optional, Union, Any


def detect_liquidity(candles: List[Dict[str, Any]], lookback: int = 50) -> bool:
    """
    Detect if liquidity sweep occurred
    
    Args:
        candles: List of candle dictionaries
        lookback: Number of candles to look back
    
    Returns:
        True if liquidity sweep detected, False otherwise
    """
    try:
        if not candles or len(candles) < lookback:
            return False
        
        recent_candles = candles[-20:]
        old_candles = candles[-lookback:-20]
        
        if len(old_candles) == 0:
            return False
        
        # Calculate old highs and lows safely
        old_highs = []
        old_lows = []
        for c in old_candles:
            if isinstance(c, dict):
                old_highs.append(c.get('high', 0))
                old_lows.append(c.get('low', 0))
        
        if not old_highs or not old_lows:
            return False
            
        old_high = max(old_highs)
        old_low = min(old_lows)
        
        # Check recent candles for sweeps
        for candle in recent_candles:
            if not isinstance(candle, dict):
                continue
                
            candle_high = candle.get('high', 0)
            candle_low = candle.get('low', 0)
            candle_close = candle.get('close', 0)
            
            # Sweep above old high (bullish liquidity grab)
            if candle_high > old_high * 1.001 and candle_close < old_high:
                return True
            
            # Sweep below old low (bearish liquidity grab)
            if candle_low < old_low * 0.999 and candle_close > old_low:
                return True
        
        return False
        
    except Exception as e:
        print(f"Error in detect_liquidity: {e}")
        return False


def detect_liquidity_sweep(candles: List[Dict[str, Any]]) -> bool:
    """
    Detect explicit liquidity sweep with wick
    
    Args:
        candles: List of candle dictionaries
    
    Returns:
        True if liquidity sweep detected, False otherwise
    """
    try:
        if not candles or len(candles) < 10:
            return False
        
        last_candle = candles[-1]
        if not isinstance(last_candle, dict):
            return False
        
        prev_candles = candles[-10:-1]
        if len(prev_candles) == 0:
            return False
        
        # Calculate previous highs and lows
        prev_highs = []
        prev_lows = []
        for c in prev_candles:
            if isinstance(c, dict):
                prev_highs.append(c.get('high', 0))
                prev_lows.append(c.get('low', 0))
        
        if not prev_highs or not prev_lows:
            return False
            
        prev_high = max(prev_highs)
        prev_low = min(prev_lows)
        
        last_high = last_candle.get('high', 0)
        last_low = last_candle.get('low', 0)
        last_close = last_candle.get('close', 0)
        
        # Bullish liquidity sweep (wick above resistance, close below)
        if last_high > prev_high and last_close < prev_high:
            return True
        
        # Bearish liquidity sweep (wick below support, close above)
        if last_low < prev_low and last_close > prev_low:
            return True
        
        return False
        
    except Exception as e:
        print(f"Error in detect_liquidity_sweep: {e}")
        return False


def volume_confirmed_sweep(candles: List[Dict[str, Any]]) -> bool:
    """
    Detect liquidity sweep confirmed by volume
    
    Args:
        candles: List of candle dictionaries with volume data
    
    Returns:
        True if volume-confirmed sweep detected, False otherwise
    """
    try:
        if not candles or len(candles) < 20:
            return False
        
        # Check if volume data exists
        has_volume = any('volume' in c for c in candles[-10:] if isinstance(c, dict))
        
        # First detect if there's a sweep
        sweep_detected = detect_liquidity_sweep(candles)
        
        if not sweep_detected:
            return False
        
        # If no volume data, return sweep detection only
        if not has_volume:
            return sweep_detected
        
        # Check volume confirmation
        last_candle = candles[-1]
        prev_candles = candles[-10:-1]
        
        if not isinstance(last_candle, dict):
            return False
        
        last_volume = last_candle.get('volume', 0)
        
        # Calculate average volume of previous candles
        volumes = []
        for c in prev_candles:
            if isinstance(c, dict):
                vol = c.get('volume', 0)
                if vol > 0:
                    volumes.append(vol)
        
        if not volumes:
            return sweep_detected
        
        avg_volume = sum(volumes) / len(volumes)
        
        # Volume should be at least 1.5x average to confirm sweep
        return last_volume > avg_volume * 1.5
        
    except Exception as e:
        print(f"Error in volume_confirmed_sweep: {e}")
        return False


def detect_liquidity_levels(candles: List[Dict[str, Any]]) -> Dict[str, List[float]]:
    """
    Detect all major liquidity levels
    
    Args:
        candles: List of candle dictionaries
    
    Returns:
        Dictionary with liquidity levels
    """
    try:
        levels = {
            'buy_stops': [],  # Above swing highs
            'sell_stops': [],  # Below swing lows
            'double_tops': [],
            'double_bottoms': []
        }
        
        if not candles or len(candles) < 20:
            return levels
        
        from .utils import find_swing_points
        swings = find_swing_points(candles, left_bars=5, right_bars=5)
        
        if not swings or not isinstance(swings, dict):
            return levels
        
        # Buy Stops (above swing highs)
        for high in swings.get('swing_highs', []):
            if isinstance(high, dict):
                price = high.get('price', 0)
                if price > 0:
                    levels['buy_stops'].append(round(price * 1.001, 2))
        
        # Sell Stops (below swing lows)
        for low in swings.get('swing_lows', []):
            if isinstance(low, dict):
                price = low.get('price', 0)
                if price > 0:
                    levels['sell_stops'].append(round(price * 0.999, 2))
        
        # Double Tops
        swing_highs = swings.get('swing_highs', [])
        if len(swing_highs) >= 2:
            last_two = swing_highs[-2:]
            if len(last_two) == 2 and all(isinstance(h, dict) for h in last_two):
                price1 = last_two[0].get('price', 0)
                price2 = last_two[1].get('price', 0)
                if price1 > 0 and price2 > 0:
                    price_diff = abs(price1 - price2)
                    avg_price = (price1 + price2) / 2
                    if price_diff / avg_price < 0.005:  # 0.5% difference
                        levels['double_tops'].append(round(avg_price, 2))
        
        # Double Bottoms
        swing_lows = swings.get('swing_lows', [])
        if len(swing_lows) >= 2:
            last_two = swing_lows[-2:]
            if len(last_two) == 2 and all(isinstance(l, dict) for l in last_two):
                price1 = last_two[0].get('price', 0)
                price2 = last_two[1].get('price', 0)
                if price1 > 0 and price2 > 0:
                    price_diff = abs(price1 - price2)
                    avg_price = (price1 + price2) / 2
                    if price_diff / avg_price < 0.005:
                        levels['double_bottoms'].append(round(avg_price, 2))
        
        return levels
        
    except Exception as e:
        print(f"Error in detect_liquidity_levels: {e}")
        return {'buy_stops': [], 'sell_stops': [], 'double_tops': [], 'double_bottoms': []}


def detect_liquidity_grab(candles: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Detect liquidity grab with direction
    
    Args:
        candles: List of candle dictionaries
    
    Returns:
        Dictionary with liquidity grab details
    """
    try:
        result = {'detected': False, 'direction': None, 'price': None, 'type': None}
        
        if not candles or len(candles) < 20:
            return result
        
        last_candle = candles[-1]
        if not isinstance(last_candle, dict):
            return result
        
        prev_candles = candles[-20:-1]
        if len(prev_candles) < 5:
            return result
        
        # Calculate key levels
        key_highs = []
        key_lows = []
        for c in prev_candles:
            if isinstance(c, dict):
                key_highs.append(c.get('high', 0))
                key_lows.append(c.get('low', 0))
        
        if not key_highs or not key_lows:
            return result
            
        key_high = max(key_highs)
        key_low = min(key_lows)
        
        last_low = last_candle.get('low', 0)
        last_high = last_candle.get('high', 0)
        last_close = last_candle.get('close', 0)
        
        # Bullish grab (took out sell stops)
        if last_low < key_low:
            if last_close > key_low:
                return {
                    'detected': True,
                    'direction': 'bullish',
                    'price': key_low,
                    'type': 'sell_stops'
                }
        
        # Bearish grab (took out buy stops)
        if last_high > key_high:
            if last_close < key_high:
                return {
                    'detected': True,
                    'direction': 'bearish',
                    'price': key_high,
                    'type': 'buy_stops'
                }
        
        return result
        
    except Exception as e:
        print(f"Error in detect_liquidity_grab: {e}")
        return {'detected': False, 'direction': None, 'price': None, 'type': None}


def get_liquidity_zones(candles: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """
    Get major liquidity zones
    
    Args:
        candles: List of candle dictionaries
    
    Returns:
        Dictionary with liquidity zones
    """
    try:
        zones = {'buy_zones': [], 'sell_zones': []}
        
        if not candles or len(candles) < 30:
            return zones
        
        from .utils import find_swing_points
        swings = find_swing_points(candles, left_bars=5, right_bars=5)
        
        if not swings or not isinstance(swings, dict):
            return zones
        
        # Buy zones (above swing highs)
        swing_highs = swings.get('swing_highs', [])
        for high in swing_highs[-3:]:
            if isinstance(high, dict):
                price = high.get('price', 0)
                if price > 0:
                    is_strong = price == max([h.get('price', 0) for h in swing_highs if isinstance(h, dict)] or [0])
                    zones['buy_zones'].append({
                        'price': round(price * 1.001, 2),
                        'strength': 'strong' if is_strong else 'normal'
                    })
        
        # Sell zones (below swing lows)
        swing_lows = swings.get('swing_lows', [])
        for low in swing_lows[-3:]:
            if isinstance(low, dict):
                price = low.get('price', 0)
                if price > 0:
                    is_strong = price == min([l.get('price', 0) for l in swing_lows if isinstance(l, dict)] or [float('inf')])
                    zones['sell_zones'].append({
                        'price': round(price * 0.999, 2),
                        'strength': 'strong' if is_strong else 'normal'
                    })
        
        return zones
        
    except Exception as e:
        print(f"Error in get_liquidity_zones: {e}")
        return {'buy_zones': [], 'sell_zones': []}