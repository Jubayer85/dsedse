"""
Professional Risk Management
- Position sizing
- Stop Loss placement
- Take Profit levels
- Risk/Reward calculation
"""

from typing import Dict, Tuple, List  # ✅ List ইম্পোর্ট যোগ করুন


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
                               current_price: float = None) -> float:
        """
        Calculate position size based on risk
        
        Args:
            entry_price: Entry price for the trade
            stop_loss: Stop loss price
            current_price: Current market price (optional)
        
        Returns:
            Position size in units
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
        
        Args:
            entry: Entry price
            stop: Stop loss price
            targets: List of take profit targets
        
        Returns:
            List of risk/reward ratios for each target
        """
        risk = abs(entry - stop)
        
        rr_ratios = []
        for target in targets:
            reward = abs(target - entry)
            if risk > 0:
                rr_ratios.append(round(reward / risk, 2))
            else:
                rr_ratios.append(0.0)
        
        return rr_ratios
    
    def should_trade(self, 
                    confidence: int,
                    rr_ratio: float,
                    min_confidence: int = 60,
                    min_rr: float = 1.5) -> Tuple[bool, str]:
        """
        Decide whether to take the trade
        
        Args:
            confidence: Confidence score (0-100)
            rr_ratio: Risk/Reward ratio
            min_confidence: Minimum confidence required
            min_rr: Minimum risk/reward required
        
        Returns:
            Tuple of (decision, reason)
        """
        if confidence < min_confidence:
            return False, f"❌ Confidence too low: {confidence}% < {min_confidence}%"
        
        if rr_ratio < min_rr:
            return False, f"❌ Risk/Reward too low: 1:{rr_ratio} < 1:{min_rr}"
        
        return True, f"✅ Trade approved (Confidence: {confidence}%, RR: 1:{rr_ratio})"
    
    def calculate_trade_cost(self, position_size: float, entry_price: float) -> Dict:
        """
        Calculate total trade cost including commission
        
        Args:
            position_size: Position size in units
            entry_price: Entry price
        
        Returns:
            Dictionary with trade cost details
        """
        trade_value = position_size * entry_price
        commission_cost = trade_value * self.commission
        slippage_cost = trade_value * self.slippage
        
        return {
            'trade_value': round(trade_value, 2),
            'commission': round(commission_cost, 2),
            'slippage': round(slippage_cost, 2),
            'total_cost': round(commission_cost + slippage_cost, 2),
            'net_value': round(trade_value - commission_cost - slippage_cost, 2)
        }
    
    def calculate_stop_loss(self, entry: float, atr: float, multiplier: float = 1.5, direction: str = 'long') -> float:
        """
        Calculate stop loss based on ATR
        
        Args:
            entry: Entry price
            atr: Average True Range
            multiplier: ATR multiplier
            direction: 'long' or 'short'
        
        Returns:
            Stop loss price
        """
        if direction.lower() == 'long':
            return entry - (atr * multiplier)
        else:
            return entry + (atr * multiplier)
    
    def calculate_take_profit(self, entry: float, stop: float, risk_reward: float = 2.0) -> float:
        """
        Calculate take profit based on risk/reward ratio
        
        Args:
            entry: Entry price
            stop: Stop loss price
            risk_reward: Risk/Reward ratio (e.g., 2.0 for 1:2)
        
        Returns:
            Take profit price
        """
        risk = abs(entry - stop)
        
        if entry > stop:  # Long
            return entry + (risk * risk_reward)
        else:  # Short
            return entry - (risk * risk_reward)
    
    def calculate_multiple_take_profits(self, entry: float, stop: float, rrs: List[float] = [2, 3, 5]) -> List[float]:
        """
        Calculate multiple take profit levels
        
        Args:
            entry: Entry price
            stop: Stop loss price
            rrs: List of risk/reward ratios
        
        Returns:
            List of take profit prices
        """
        risk = abs(entry - stop)
        tps = []
        
        for rr in rrs:
            if entry > stop:  # Long
                tp = entry + (risk * rr)
            else:  # Short
                tp = entry - (risk * rr)
            tps.append(round(tp, 2))
        
        return tps


# ব্যবহারের উদাহরণ
if __name__ == "__main__":
    # Risk Manager তৈরি করুন
    rm = RiskManager(
        account_balance=10000,
        risk_percent=1.0,
        commission=0.001,
        slippage=0.0005
    )
    
    # উদাহরণ ডেটা
    entry = 50000
    stop = 49000
    targets = [52000, 53000, 55000]
    
    # পজিশন সাইজ ক্যালকুলেশন
    position_size = rm.calculate_position_size(entry, stop)
    print(f"Position Size: {position_size} units")
    
    # Risk/Reward ক্যালকুলেশন
    rr_ratios = rm.calculate_risk_reward(entry, stop, targets)
    print(f"Risk/Reward Ratios: {rr_ratios}")
    
    # ট্রেড ডিসিশন
    decision, reason = rm.should_trade(confidence=75, rr_ratio=rr_ratios[0])
    print(f"Trade Decision: {reason}")
    
    # ট্রেড কস্ট
    costs = rm.calculate_trade_cost(position_size, entry)
    print(f"Trade Costs: {costs}")