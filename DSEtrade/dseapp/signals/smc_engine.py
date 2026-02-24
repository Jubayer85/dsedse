"""
Professional SMC Trading Engine
Features:
- Multi-timeframe Analysis
- Order Blocks + Breaker Blocks
- Fair Value Gaps (FVG)
- Liquidity Sweeps
- Market Structure Shifts (MSS)
- Risk Management (SL/TP)
- Position Sizing
- Confidence Scoring
"""

import math
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime

from .structure import detect_structure, detect_mss
from .liquidity import detect_liquidity, detect_liquidity_levels
from .breaker import detect_breaker_block
from .fvg import detect_fvg, validate_fvg
from .order_block import detect_order_block, validate_ob
from .mitigation import detect_mitigation, detect_order_block_mitigation, detect_fvg_mitigation
from .imbalance import detect_imbalance, detect_volume_imbalance
from .utils import calculate_atr, find_swing_points


@dataclass
class SignalResult:
    """Complete Signal Output Structure"""
    signal: str = "NO_TRADE"  # 'BUY', 'SELL', 'NO_TRADE'
    direction: str = "NO_TRADE"  # 'LONG', 'SHORT'
    confidence: int = 0  # 0-100
    entry_price: float = 0.0
    stop_loss: float = 0.0
    take_profit_1: float = 0.0  # 1:2 RR
    take_profit_2: float = 0.0  # 1:3 RR
    take_profit_3: float = 0.0  # 1:5 RR
    risk_reward_ratio: float = 0.0
    position_size: float = 0.0  # in units
    structure: str = "unknown"
    liquidity_swept: bool = False
    order_block: Optional[Dict] = None
    fvg: Optional[Dict] = None
    breaker_block: Optional[Dict] = None
    market_structure_shift: bool = False
    timeframes: Dict = field(default_factory=dict)
    explanation: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)


class ProfessionalSMCEngine:
    """
    Professional SMC Trading Engine with Multi-Timeframe Analysis
    """
    
    def __init__(self, 
                 candles_htf: List[Dict[str, Any]],  # Higher Timeframe (1H/4H)
                 candles_mtf: List[Dict[str, Any]],  # Medium Timeframe (15M/30M)
                 candles_ltf: List[Dict[str, Any]],  # Lower Timeframe (1M/5M)
                 account_balance: float = 10000,
                 risk_percent: float = 1.0,  # 1% risk per trade
                 commission: float = 0.001,  # 0.1% commission
                 slippage: float = 0.0005):  # 0.05% slippage
        
        self.htf_candles = candles_htf
        self.mtf_candles = candles_mtf
        self.ltf_candles = candles_ltf
        
        self.account_balance = account_balance
        self.risk_percent = risk_percent / 100
        self.commission = commission
        self.slippage = slippage
        
        # Calculate ATR for all timeframes
        self.atr_htf = calculate_atr(candles_htf, period=14)
        self.atr_mtf = calculate_atr(candles_mtf, period=14)
        self.atr_ltf = calculate_atr(candles_ltf, period=14)
        
        # Results Storage
        self.last_signal = None
        
    def analyze(self) -> SignalResult:
        """
        Complete Multi-Timeframe SMC Analysis
        """
        
        # Step 1: HTF Analysis (Trend Direction)
        htf_structure = detect_structure(self.htf_candles)
        htf_liquidity = detect_liquidity_levels(self.htf_candles)
        htf_ob = detect_order_block(self.htf_candles)
        htf_mss = detect_mss(self.htf_candles)
        
        # Step 2: MTF Analysis (Setup)
        mtf_structure = detect_structure(self.mtf_candles)
        mtf_liquidity = detect_liquidity(self.mtf_candles)
        mtf_fvg = detect_fvg(self.mtf_candles)
        mtf_breaker = detect_breaker_block(self.mtf_candles)
        mtf_imbalance = detect_imbalance(self.mtf_candles)
        mtf_ob = detect_order_block(self.mtf_candles)  # ✅ This was missing
        
        # Step 3: LTF Analysis (Entry)
        ltf_structure = detect_structure(self.ltf_candles)
        ltf_liquidity = detect_liquidity(self.ltf_candles)
        ltf_fvg = detect_fvg(self.ltf_candles)
        ltf_mitigation = detect_mitigation(self.ltf_candles)
        
        # Step 4: Calculate Current Price
        current_price = self.ltf_candles[-1]['close'] if self.ltf_candles else 0
        
        # Step 5: Determine Trade Direction
        direction = self._determine_direction(
            htf_structure, mtf_structure, ltf_structure
        )
        
        # Step 6: Calculate Confidence Score
        confidence = self._calculate_confidence({
            'htf_structure': htf_structure in ['bullish', 'bearish'],
            'htf_ob': htf_ob is not None,
            'htf_mss': htf_mss,
            'mtf_fvg': mtf_fvg is not None,
            'mtf_breaker': mtf_breaker is not None,
            'mtf_liquidity': mtf_liquidity,
            'ltf_fvg': ltf_fvg is not None,
            'ltf_mitigation': ltf_mitigation,
            'ltf_liquidity': ltf_liquidity,
            'mtf_imbalance': mtf_imbalance,
            'mtf_ob': mtf_ob is not None  # ✅ Added to confidence calculation
        })
        
        # Step 7: Calculate Entry, SL, TP
        entry_data = self._calculate_entry_levels(
            direction, current_price, ltf_fvg, htf_ob, htf_liquidity
        )
        
        # Step 8: Calculate Position Size
        position_size = self._calculate_position_size(
            entry_price=entry_data['entry'],
            stop_loss=entry_data['sl'],
            current_price=current_price
        )
        
        # Step 9: Generate Signal
        signal = self._generate_signal(
            direction=direction,
            confidence=confidence,
            entry_data=entry_data
        )
        
        # Step 10: Build Explanation
        explanation = self._build_explanation(
            direction, confidence, htf_structure, mtf_fvg, ltf_fvg,
            htf_ob, mtf_breaker, htf_mss, mtf_liquidity
        )
        
        # Step 11: Create Result Object
        result = SignalResult(
            signal=signal,
            direction=direction.upper() if direction and direction != "NO_TRADE" else 'NO_TRADE',
            confidence=confidence,
            entry_price=entry_data['entry'],
            stop_loss=entry_data['sl'],
            take_profit_1=entry_data['tp1'],
            take_profit_2=entry_data['tp2'],
            take_profit_3=entry_data['tp3'],
            risk_reward_ratio=entry_data['rr'],
            position_size=position_size,
            structure=f"HTF: {htf_structure} | MTF: {mtf_structure} | LTF: {ltf_structure}",
            liquidity_swept=mtf_liquidity or ltf_liquidity,
            order_block=htf_ob or mtf_ob,
            fvg=mtf_fvg or ltf_fvg,
            breaker_block=mtf_breaker,
            market_structure_shift=htf_mss,
            timeframes={
                'HTF': htf_structure,
                'MTF': mtf_structure,
                'LTF': ltf_structure
            },
            explanation=explanation,
            timestamp=datetime.now()
        )
        
        self.last_signal = result
        return result
    
    def _determine_direction(self, htf: str, mtf: str, ltf: str) -> Optional[str]:
        """
        Determine trade direction based on multi-timeframe alignment
        """
        # Bullish Alignment
        if htf in ['bullish', 'accumulation'] and mtf in ['bullish', 'pullback']:
            if ltf in ['bullish', 'breakout']:
                return 'long'
        
        # Bearish Alignment
        if htf in ['bearish', 'distribution'] and mtf in ['bearish', 'pullback']:
            if ltf in ['bearish', 'breakout']:
                return 'short'
        
        # Strong Bullish (all timeframes aligned)
        if htf == 'bullish' and mtf == 'bullish' and ltf == 'bullish':
            return 'strong_long'
        
        # Strong Bearish (all timeframes aligned)
        if htf == 'bearish' and mtf == 'bearish' and ltf == 'bearish':
            return 'strong_short'
        
        return None
    
    def _calculate_confidence(self, factors: Dict[str, bool]) -> int:
        """
        Calculate confidence score (0-100) based on multiple factors
        """
        weights = {
            'htf_structure': 20,
            'htf_ob': 15,
            'htf_mss': 15,
            'mtf_fvg': 12,
            'mtf_breaker': 12,
            'mtf_liquidity': 8,
            'ltf_fvg': 8,
            'ltf_mitigation': 5,
            'ltf_liquidity': 5,
            'mtf_imbalance': 5,
            'mtf_ob': 10  # ✅ Added weight for MTF Order Block
        }
        
        score = 0
        
        for key, weight in weights.items():
            if factors.get(key, False):
                score += weight
        
        # Bonus for multiple confirmations
        confirmation_count = sum(1 for v in factors.values() if v)
        if confirmation_count >= 5:
            score = min(100, score + 10)
        if confirmation_count >= 7:
            score = min(100, score + 15)
        
        return min(100, score)
    
    def _calculate_entry_levels(self, direction: Optional[str], current_price: float, 
                               ltf_fvg: Optional[Dict], htf_ob: Optional[Dict], 
                               htf_liquidity: Dict) -> Dict[str, float]:
        """
        Calculate Entry, Stop Loss, and Take Profit levels
        """
        atr = self.atr_ltf if self.atr_ltf > 0 else 10  # Use LTF ATR for precision
        
        if not direction or direction == "NO_TRADE":
            return {
                'entry': current_price,
                'sl': current_price,
                'tp1': current_price,
                'tp2': current_price,
                'tp3': current_price,
                'rr': 0
            }
        
        # LONG Trade
        if 'long' in direction.lower():
            # Entry
            if ltf_fvg and ltf_fvg.get('entry'):
                entry = ltf_fvg['entry']
            elif htf_ob and htf_ob.get('entry'):
                entry = htf_ob['entry']
            else:
                entry = current_price
            
            # Stop Loss
            sl_distance = atr * 1.5  # 1.5 ATR stop
            sl = entry - sl_distance
            
            # Take Profits (Multiple Targets)
            tp1_distance = sl_distance * 2  # 1:2 RR
            tp2_distance = sl_distance * 3  # 1:3 RR
            tp3_distance = sl_distance * 5  # 1:5 RR
            
            tp1 = entry + tp1_distance
            tp2 = entry + tp2_distance
            tp3 = entry + tp3_distance
            
            rr = tp1_distance / sl_distance if sl_distance > 0 else 0
            
        # SHORT Trade
        elif 'short' in direction.lower():
            if ltf_fvg and ltf_fvg.get('entry'):
                entry = ltf_fvg['entry']
            elif htf_ob and htf_ob.get('entry'):
                entry = htf_ob['entry']
            else:
                entry = current_price
            
            sl_distance = atr * 1.5
            sl = entry + sl_distance
            
            tp1_distance = sl_distance * 2
            tp2_distance = sl_distance * 3
            tp3_distance = sl_distance * 5
            
            tp1 = entry - tp1_distance
            tp2 = entry - tp2_distance
            tp3 = entry - tp3_distance
            
            rr = tp1_distance / sl_distance if sl_distance > 0 else 0
        
        else:
            return {
                'entry': current_price,
                'sl': current_price,
                'tp1': current_price,
                'tp2': current_price,
                'tp3': current_price,
                'rr': 0
            }
        
        return {
            'entry': entry,
            'sl': sl,
            'tp1': tp1,
            'tp2': tp2,
            'tp3': tp3,
            'rr': round(rr, 2)
        }
    
    def _calculate_position_size(self, entry_price: float, stop_loss: float, current_price: float) -> float:
        """
        Calculate position size based on risk
        """
        if entry_price <= 0 or stop_loss <= 0:
            return 0
        
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
        
        return round(adjusted_size, 4)
    
    def _generate_signal(self, direction: Optional[str], confidence: int, 
                        entry_data: Dict[str, float]) -> str:
        """
        Generate final signal based on confidence and risk
        """
        if not direction or direction == "NO_TRADE" or confidence < 60:
            return 'NO_TRADE'
        
        if confidence >= 85:
            return 'STRONG_' + direction.upper()
        elif confidence >= 70:
            return direction.upper()
        else:
            return 'WEAK_' + direction.upper()
    
    def _build_explanation(self, direction: Optional[str], confidence: int, 
                          htf: str, mtf_fvg: Optional[Dict], ltf_fvg: Optional[Dict],
                          htf_ob: Optional[Dict], mtf_breaker: Optional[Dict], 
                          htf_mss: bool, mtf_liquidity: bool) -> List[str]:
        """
        Build human-readable explanation of the signal
        """
        explanation = []
        
        if not direction or direction == "NO_TRADE":
            explanation.append("❌ No clear direction from multi-timeframe analysis")
            return explanation
        
        # HTF Analysis
        explanation.append(f"📊 HTF Trend: {htf.upper()}")
        if htf_ob:
            explanation.append(f"   └─ Order Block detected")
        if htf_mss:
            explanation.append("   └─ Market Structure Shift confirmed")
        
        # MTF Analysis
        if mtf_fvg:
            explanation.append(f"📈 FVG detected on MTF")
        if mtf_breaker:
            explanation.append(f"🔨 Breaker Block formed")
        if mtf_liquidity:
            explanation.append("💧 Liquidity sweep confirmed")
        
        # LTF Analysis
        if ltf_fvg:
            explanation.append(f"🎯 Entry FVG on LTF")
        
        # Confidence
        explanation.append(f"⚡ Confidence Score: {confidence}%")
        if confidence >= 80:
            explanation.append("✅ High probability setup")
        elif confidence >= 60:
            explanation.append("⚠️ Moderate probability - use proper risk management")
        
        # Risk/Reward
        explanation.append(f"💹 Multiple targets: 1:2, 1:3, 1:5 RR")
        
        return explanation