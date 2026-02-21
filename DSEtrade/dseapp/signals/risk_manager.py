"""
Professional Risk Management
- Position sizing
- Stop Loss placement
- Take Profit levels
- Risk/Reward calculation
"""

from typing import Dict, Tuple
import math


class RiskManager:
    """
    Professional Risk Management System
    """
    
    def __init__(self, 
                 account_balance: float,
                 risk_percent: float = 1.0,
                 commission: float = 0.001,
                 slippage: float = 0.0005):
        
        self.account_balance = account_balance
        self.risk_percent = risk_percent / 100
        self.commission = commission
        self.slippage = slippage
        
        self.max_risk_amount = account_balance * self.risk_percent
        self.max_position_size = account_balance * 0.2  # Max 20% per position
        
    def calculate_position_size(self, 
                               entry_price: float,
                               stop_loss: float,
                               current_price: float) -> float:
        """
        Calculate position size based on risk
        """
        # Risk amount in currency
        risk_amount = self.account_balance * self.risk_percent
        
        # Price distance to SL
        if entry_price > stop_loss:  # Long
            sl_distance = entry_price - stop_loss
        else:  # Short
            sl_distance = stop_loss - entry_price
        
        if sl_distance <= 0:
            return 0
        
        # Position size (units)
        position_size = risk_amount / sl_distance
        
        # Apply commission and slippage
        adjusted_size = position_size * (1 - self.commission - self.slippage)
        
        # Check max position limit
        max_units = self.max_position_size / entry_price
        adjusted_size = min(adjusted_size, max_units)
        
        return round(adjusted_size, 4)
    
    def calculate_risk_reward(self,
                             entry: float,
                             stop: float,
                             targets: List[float]) -> List[float]:
        """
        Calculate Risk/Reward ratios for multiple targets
        """
        risk = abs(entry - stop)
        
        rr_ratios = []
        for target in targets:
            reward = abs(target - entry)
            if risk > 0:
                rr_ratios.append(round(reward / risk, 2))
            else:
                rr_ratios.append(0)
        
        return rr_ratios
    
    def should_trade(self, 
                    confidence: int,
                    rr_ratio: float,
                    min_confidence: int = 60,
                    min_rr: float = 1.5) -> Tuple[bool, str]:
        """
        Decide whether to take the trade
        """
        if confidence < min_confidence:
            return False, f"Confidence too low: {confidence}% < {min_confidence}%"
        
        if rr_ratio < min_rr:
            return False, f"Risk/Reward too low: 1:{rr_ratio} < 1:{min_rr}"
        
        return True, "Trade approved"
    
    def calculate_trade_cost(self, position_size: float, entry_price: float) -> Dict:
        """
        Calculate total trade cost including commission
        """
        trade_value = position_size * entry_price
        commission_cost = trade_value * self.commission
        slippage_cost = trade_value * self.slippage
        
        return {
            'trade_value': trade_value,
            'commission': commission_cost,
            'slippage': slippage_cost,
            'total_cost': commission_cost + slippage_cost,
            'net_value': trade_value - commission_cost - slippage_cost
        }