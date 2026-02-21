"""
Imbalance Detection for SMC
- Volume Imbalance
- Delta Imbalance
- Order Flow Imbalance
"""

from typing import Dict, List, Optional
import math


def detect_imbalance(candles: List[Dict]) -> bool:
    """
    Detect market imbalance
    Imbalance = Strong buying/selling pressure
    """
    if len(candles) < 10:
        return False
    
    # Recent candles
    recent = candles[-5:]
    
    # Calculate buying/selling pressure
    buying_pressure = 0
    selling_pressure = 0
    
    for candle in recent:
        body = abs(candle['close'] - candle['open'])
        upper_wick = candle['high'] - max(candle['close'], candle['open'])
        lower_wick = min(candle['close'], candle['open']) - candle['low']
        
        if candle['close'] > candle['open']:  # Bullish candle
            buying_pressure += body
            selling_pressure += upper_wick
        else:  # Bearish candle
            selling_pressure += body
            buying_pressure += lower_wick
    
    # Check for imbalance
    total = buying_pressure + selling_pressure
    if total == 0:
        return False
    
    buying_ratio = buying_pressure / total
    selling_ratio = selling_pressure / total
    
    # Strong imbalance (70% or more)
    if buying_ratio > 0.7:
        return True  # Bullish imbalance
    if selling_ratio > 0.7:
        return True  # Bearish imbalance
    
    return False


def detect_volume_imbalance(candles: List[Dict]) -> bool:
    """
    Detect volume imbalance
    """
    if len(candles) < 10:
        return False
    
    # Check if volume has 'volume' field
    has_volume = 'volume' in candles[0]
    
    if not has_volume:
        # Use candle size as proxy for volume
        return detect_imbalance(candles)
    
    recent = candles[-5:]
    older = candles[-10:-5]
    
    avg_recent_volume = sum(c.get('volume', 0) for c in recent) / len(recent)
    avg_older_volume = sum(c.get('volume', 0) for c in older) / len(older)
    
    if avg_older_volume == 0:
        return False
    
    volume_ratio = avg_recent_volume / avg_older_volume
    
    return volume_ratio > 1.5  # 50% higher volume