"""
Order Block Detection
- Bullish/Bearish Order Blocks
- Mitigation
- Entry levels
"""

from typing import Dict, List, Optional


def detect_order_block(candles: List[Dict]) -> Optional[Dict]:
    """
    Detect Order Blocks
    OB = Last candle before impulsive move
    """
    if len(candles) < 10:
        return None
    
    # Find impulsive moves
    for i in range(len(candles) - 5, 3, -1):
        current = candles[i]
        prev = candles[i-1]
        next_candles = candles[i:i+3]
        
        # Calculate move size
        avg_range = np.mean([c['high'] - c['low'] for c in candles[i-10:i]])
        
        # Bullish OB (large bullish candle after small consolidation)
        if current['close'] > current['open']:  # Bullish candle
            move_up = next_candles[0]['high'] - current['high']
            if move_up > avg_range * 1.5:  # Impulsive move
                return {
                    'type': 'bullish',
                    'top': current['high'],
                    'bottom': current['low'],
                    'entry': current['high'] - (current['high'] - current['low']) * 0.5,
                    'time': current['time'],
                    'range': f"{current['low']:.2f} - {current['high']:.2f}"
                }
        
        # Bearish OB (large bearish candle after small consolidation)
        else:
            move_down = current['low'] - next_candles[0]['low']
            if abs(move_down) > avg_range * 1.5:
                return {
                    'type': 'bearish',
                    'top': current['high'],
                    'bottom': current['low'],
                    'entry': current['low'] + (current['high'] - current['low']) * 0.5,
                    'time': current['time'],
                    'range': f"{current['low']:.2f} - {current['high']:.2f}"
                }
    
    return None


def validate_ob(ob: Dict, current_price: float) -> bool:
    """
    Check if Order Block is still valid (not mitigated)
    """
    if ob['type'] == 'bullish':
        # Price shouldn't break below OB low
        return current_price > ob['bottom']
    else:
        # Price shouldn't break above OB high
        return current_price < ob['top']