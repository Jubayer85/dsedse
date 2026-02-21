"""
Fair Value Gap (FVG) Detection
- Bullish/Bearish FVG
- FVG validation
- Entry levels
"""

from typing import Dict, List, Optional


def detect_fvg(candles: List[Dict]) -> Optional[Dict]:
    """
    Detect Fair Value Gaps
    FVG = Gap between candle1's low and candle3's high (bullish)
          or candle1's high and candle3's low (bearish)
    """
    if len(candles) < 3:
        return None
    
    fvg_list = []
    
    for i in range(len(candles) - 2):
        c1 = candles[i]    # First candle
        c2 = candles[i+1]  # Middle candle (body should be small)
        c3 = candles[i+2]  # Third candle
        
        # Check if middle candle is small (indecision)
        c2_range = c2['high'] - c2['low']
        avg_range = (c1['high'] - c1['low'] + c3['high'] - c3['low']) / 2
        
        if c2_range > avg_range * 0.5:
            continue  # Middle candle too large
        
        # Bullish FVG (c3 low > c1 high)
        if c3['low'] > c1['high']:
            fvg = {
                'type': 'bullish',
                'top': c3['low'],
                'bottom': c1['high'],
                'mid': (c3['low'] + c1['high']) / 2,
                'entry': c1['high'] + (c3['low'] - c1['high']) * 0.382,  # 38.2% retrace
                'time': c2['time'],
                'range': f"{c1['high']:.2f} - {c3['low']:.2f}"
            }
            fvg_list.append(fvg)
        
        # Bearish FVG (c3 high < c1 low)
        elif c3['high'] < c1['low']:
            fvg = {
                'type': 'bearish',
                'top': c1['low'],
                'bottom': c3['high'],
                'mid': (c1['low'] + c3['high']) / 2,
                'entry': c1['low'] - (c1['low'] - c3['high']) * 0.382,
                'time': c2['time'],
                'range': f"{c3['high']:.2f} - {c1['low']:.2f}"
            }
            fvg_list.append(fvg)
    
    return fvg_list[-1] if fvg_list else None


def validate_fvg(fvg: Dict, current_price: float) -> bool:
    """
    Validate if FVG is still valid (not mitigated)
    """
    if fvg['type'] == 'bullish':
        # Price should be above FVG bottom
        return current_price > fvg['bottom']
    else:
        # Price should be below FVG top
        return current_price < fvg['top']