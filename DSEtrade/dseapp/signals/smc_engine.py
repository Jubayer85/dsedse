"""
Professional SMC Trading Engine
- Multi-timeframe Analysis
- Signal Generation with Liquidity/Breaker
- Entry/Exit Levels with Stop Loss & Take Profit
- Risk Management Integration
"""

from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime
import numpy as np

from .structure import detect_structure, detect_mss
from .liquidity import detect_liquidity, detect_liquidity_levels, detect_liquidity_sweep
from .breaker import detect_breaker_block, detect_breaker
from .fvg import detect_fvg, validate_fvg
from .order_block import detect_order_block, validate_ob
from .risk_manager import RiskManager
from .utils import calculate_atr, find_swing_points


@dataclass
class TradeSignal:
    """Complete Trade Signal Structure"""
    # Basic Info
    symbol: str = "XAUUSD"
    timeframe: str = "15m"
    timestamp: datetime = field(default_factory=datetime.now)
    
    # Signal
    signal: str = "NO_TRADE"  # STRONG_BUY, BUY, WEAK_BUY, NO_TRADE, WEAK_SELL, SELL, STRONG_SELL
    direction: str = "NEUTRAL"  # LONG, SHORT, NEUTRAL
    confidence: int = 0  # 0-100
    
    # Structure
    htf_structure: str = "neutral"
    mtf_structure: str = "neutral"
    ltf_structure: str = "neutral"
    
    # Factors
    liquidity_swept: bool = False
    breaker_detected: bool = False
    fvg_detected: bool = False
    order_block_detected: bool = False
    mss_detected: bool = False
    
    # Entry Levels
    entry_price: float = 0.0
    entry_min: float = 0.0
    entry_max: float = 0.0
    
    # Exit Levels
    stop_loss: float = 0.0
    take_profit_1: float = 0.0
    take_profit_2: float = 0.0
    take_profit_3: float = 0.0
    
    # Risk Management
    risk_percent: float = 1.0
    position_size: float = 0.0
    position_value: float = 0.0
    risk_amount: float = 0.0
    reward_potential: Dict[str, float] = field(default_factory=dict)
    
    # Market Data
    current_price: float = 0.0
    atr: float = 0.0
    
    # Explanation
    explanation: List[str] = field(default_factory=list)


class ProfessionalSMCEngine:
    """
    Advanced SMC Signal Engine with Complete Trade Management
    """
    
    def __init__(self, 
                 candles_htf: List[Dict[str, Any]],
                 candles_mtf: List[Dict[str, Any]],
                 candles_ltf: List[Dict[str, Any]],
                 account_balance: float = 10000,
                 risk_percent: float = 1.0,
                 commission: float = 0.001,
                 symbol: str = "XAUUSD",
                 timeframe: str = "15m"):
        
        self.htf_candles = candles_htf
        self.mtf_candles = candles_mtf
        self.ltf_candles = candles_ltf
        
        self.symbol = symbol
        self.timeframe = timeframe
        
        # Calculate ATR for all timeframes
        self.atr_htf = calculate_atr(candles_htf, period=14) if candles_htf else 0
        self.atr_mtf = calculate_atr(candles_mtf, period=14) if candles_mtf else 0
        self.atr_ltf = calculate_atr(candles_ltf, period=14) if candles_ltf else 0
        
        # Risk Manager
        self.risk_manager = RiskManager(
            account_balance=account_balance,
            risk_percent=risk_percent,
            commission=commission
        )
        
        self.current_price = candles_ltf[-1]['close'] if candles_ltf else 0
        
    def analyze(self) -> TradeSignal:
        """
        Complete Multi-timeframe SMC Analysis
        """
        # Step 1: HTF Analysis (Trend Direction)
        htf_structure = detect_structure(self.htf_candles) if self.htf_candles else "neutral"
        htf_liquidity = detect_liquidity_levels(self.htf_candles) if self.htf_candles else {}
        htf_mss = detect_mss(self.htf_candles) if self.htf_candles else False
        
        # Step 2: MTF Analysis (Setup)
        mtf_structure = detect_structure(self.mtf_candles) if self.mtf_candles else "neutral"
        mtf_liquidity_sweep = detect_liquidity_sweep(self.mtf_candles) if self.mtf_candles else False
        mtf_breaker = detect_breaker_block(self.mtf_candles) if self.mtf_candles else None
        mtf_fvg = detect_fvg(self.mtf_candles) if self.mtf_candles else None
        mtf_ob = detect_order_block(self.mtf_candles) if self.mtf_candles else None
        
        # Step 3: LTF Analysis (Entry)
        ltf_structure = detect_structure(self.ltf_candles) if self.ltf_candles else "neutral"
        ltf_liquidity = detect_liquidity(self.ltf_candles) if self.ltf_candles else False
        ltf_fvg = detect_fvg(self.ltf_candles) if self.ltf_candles else None
        
        # Step 4: Calculate Confidence Score
        confidence, factors = self._calculate_confidence({
            'htf_structure': htf_structure in ['bullish', 'bearish'],
            'htf_mss': htf_mss,
            'mtf_liquidity_sweep': mtf_liquidity_sweep,
            'mtf_breaker': mtf_breaker is not None,
            'mtf_fvg': mtf_fvg is not None,
            'mtf_ob': mtf_ob is not None,
            'ltf_fvg': ltf_fvg is not None,
            'ltf_liquidity': ltf_liquidity
        })
        
        # Step 5: Determine Trade Direction
        direction = self._determine_direction(
            htf_structure, mtf_structure, ltf_structure
        )
        
        # Step 6: Generate Signal based on confidence and factors
        signal = self._generate_signal(direction, confidence, factors)
        
        # Step 7: Calculate Entry Levels
        entry_data = self._calculate_entry_levels(
            direction, mtf_fvg, mtf_ob, mtf_breaker
        )
        
        # Step 8: Calculate Exit Levels (SL/TP)
        exit_data = self._calculate_exit_levels(
            direction, entry_data['entry'], self.atr_ltf
        )
        
        # Step 9: Calculate Position Size
        position_data = self.risk_manager.calculate_position_size(
            entry_price=entry_data['entry'],
            stop_loss=exit_data['stop_loss'],
            current_price=self.current_price
        ) if hasattr(self.risk_manager, 'calculate_position_size') else {
            'size': 0,
            'value': 0,
            'risk_amount': 0,
            'reward_potential': {}
        }
        
        # Step 10: Build Explanation
        explanation = self._build_explanation(
            direction, confidence, factors,
            entry_data, exit_data, position_data
        )
        
        # Step 11: Create TradeSignal Object
        signal_result = TradeSignal(
            symbol=self.symbol,
            timeframe=self.timeframe,
            signal=signal,
            direction=direction.upper() if direction else "NEUTRAL",
            confidence=confidence,
            htf_structure=htf_structure,
            mtf_structure=mtf_structure,
            ltf_structure=ltf_structure,
            liquidity_swept=mtf_liquidity_sweep,
            breaker_detected=mtf_breaker is not None,
            fvg_detected=mtf_fvg is not None or ltf_fvg is not None,
            order_block_detected=mtf_ob is not None,
            mss_detected=htf_mss,
            entry_price=entry_data['entry'],
            entry_min=entry_data['min'],
            entry_max=entry_data['max'],
            stop_loss=exit_data['stop_loss'],
            take_profit_1=exit_data['tp1'],
            take_profit_2=exit_data['tp2'],
            take_profit_3=exit_data['tp3'],
            risk_percent=self.risk_manager.risk_percent * 100 if hasattr(self.risk_manager, 'risk_percent') else 1.0,
            position_size=position_data.get('size', 0),
            position_value=position_data.get('value', 0),
            risk_amount=position_data.get('risk_amount', 0),
            reward_potential=position_data.get('reward_potential', {}),
            current_price=self.current_price,
            atr=self.atr_ltf,
            explanation=explanation
        )
        
        return signal_result
    
    def _calculate_confidence(self, factors: Dict[str, bool]) -> Tuple[int, Dict]:
        """
        Calculate confidence score with detailed factor breakdown
        """
        weights = {
            'htf_structure': 25,
            'htf_mss': 15,
            'mtf_liquidity_sweep': 15,
            'mtf_breaker': 15,
            'mtf_fvg': 10,
            'mtf_ob': 10,
            'ltf_fvg': 5,
            'ltf_liquidity': 5
        }
        
        score = 0
        active_factors = {}
        
        for key, weight in weights.items():
            if factors.get(key, False):
                score += weight
                factor_name = key.replace('_', ' ').title()
                active_factors[factor_name] = weight
        
        # Bonus for multiple confirmations
        factor_count = len(active_factors)
        if factor_count >= 4:
            score = min(100, score + 10)
        if factor_count >= 6:
            score = min(100, score + 15)
        
        return min(100, score), active_factors
    
    def _determine_direction(self, htf: str, mtf: str, ltf: str) -> Optional[str]:
        """
        Determine trade direction based on multi-timeframe alignment
        """
        # Strong Bullish (all aligned)
        if htf == 'bullish' and mtf == 'bullish' and ltf == 'bullish':
            return 'strong_long'
        
        # Bullish
        if htf in ['bullish', 'accumulation'] and mtf in ['bullish', 'pullback']:
            if ltf in ['bullish', 'breakout']:
                return 'long'
        
        # Strong Bearish (all aligned)
        if htf == 'bearish' and mtf == 'bearish' and ltf == 'bearish':
            return 'strong_short'
        
        # Bearish
        if htf in ['bearish', 'distribution'] and mtf in ['bearish', 'pullback']:
            if ltf in ['bearish', 'breakout']:
                return 'short'
        
        return None
    
    def _generate_signal(self, direction: Optional[str], confidence: int, 
                        factors: Dict) -> str:
        """
        Generate final signal with strength indication
        """
        if not direction or confidence < 50:
            return "NO_TRADE"
        
        # Check for liquidity sweep and breaker (high probability setups)
        has_liquidity = any('liquidity' in k.lower() for k in factors.keys())
        has_breaker = any('breaker' in k.lower() for k in factors.keys())
        
        if 'long' in direction.lower():
            if confidence >= 80 and (has_liquidity or has_breaker):
                return "STRONG_BUY"
            elif confidence >= 60:
                return "BUY"
            else:
                return "WEAK_BUY"
        
        elif 'short' in direction.lower():
            if confidence >= 80 and (has_liquidity or has_breaker):
                return "STRONG_SELL"
            elif confidence >= 60:
                return "SELL"
            else:
                return "WEAK_SELL"
        
        return "NO_TRADE"
    
    def _calculate_entry_levels(self, direction: Optional[str],
                               fvg: Optional[Dict], ob: Optional[Dict],
                               breaker: Optional[Dict]) -> Dict:
        """
        Calculate entry zone based on SMC concepts
        """
        if not direction or not self.current_price:
            return {'entry': self.current_price, 'min': self.current_price, 
                   'max': self.current_price}
        
        entry_zone = []
        
        # FVG entry
        if fvg and fvg.get('entry'):
            entry_zone.append(fvg['entry'])
        
        # Order Block entry
        if ob and ob.get('entry'):
            entry_zone.append(ob['entry'])
        
        # Breaker entry
        if breaker and breaker.get('entry'):
            entry_zone.append(breaker['entry'])
        
        # Current price as fallback
        if not entry_zone:
            entry_zone.append(self.current_price)
        
        # Calculate entry zone
        entry = float(np.mean(entry_zone))
        entry_min = float(min(entry_zone))
        entry_max = float(max(entry_zone))
        
        return {
            'entry': round(entry, 2),
            'min': round(entry_min, 2),
            'max': round(entry_max, 2)
        }
    
    def _calculate_exit_levels(self, direction: Optional[str], 
                              entry: float, atr: float) -> Dict:
        """
        Calculate Stop Loss and Take Profit levels
        """
        if not direction or entry == 0 or atr == 0:
            return {
                'stop_loss': entry,
                'tp1': entry,
                'tp2': entry,
                'tp3': entry
            }
        
        # ATR-based stop loss (1.5x ATR)
        sl_distance = atr * 1.5
        
        if 'long' in direction.lower():
            stop_loss = entry - sl_distance
            tp1 = entry + (sl_distance * 2)    # 1:2 RR
            tp2 = entry + (sl_distance * 3)    # 1:3 RR
            tp3 = entry + (sl_distance * 5)    # 1:5 RR
        else:
            stop_loss = entry + sl_distance
            tp1 = entry - (sl_distance * 2)
            tp2 = entry - (sl_distance * 3)
            tp3 = entry - (sl_distance * 5)
        
        return {
            'stop_loss': round(stop_loss, 2),
            'tp1': round(tp1, 2),
            'tp2': round(tp2, 2),
            'tp3': round(tp3, 2)
        }
    
    def _build_explanation(self, direction: Optional[str], confidence: int,
                          factors: Dict, entry_data: Dict, exit_data: Dict,
                          position_data: Dict) -> List[str]:
        """
        Build human-readable explanation
        """
        explanation = []
        
        if not direction:
            explanation.append("❌ No clear trade direction detected")
            return explanation
        
        # Direction
        direction_emoji = "📈" if 'long' in direction.lower() else "📉"
        explanation.append(f"{direction_emoji} Direction: {direction.upper()}")
        
        # Confidence
        explanation.append(f"⚡ Confidence: {confidence}%")
        
        # Key Factors
        if factors:
            explanation.append("🎯 Key Factors:")
            for factor, weight in factors.items():
                explanation.append(f"   • {factor}: +{weight}")
        
        # Entry Zone
        explanation.append(f"💰 Entry Zone: {entry_data['min']} - {entry_data['max']}")
        explanation.append(f"   Optimal Entry: {entry_data['entry']}")
        
        # Exit Levels
        explanation.append(f"🛑 Stop Loss: {exit_data['stop_loss']}")
        explanation.append(f"🎯 Take Profit 1 (1:2): {exit_data['tp1']}")
        explanation.append(f"🎯 Take Profit 2 (1:3): {exit_data['tp2']}")
        explanation.append(f"🎯 Take Profit 3 (1:5): {exit_data['tp3']}")
        
        # Risk Management
        explanation.append(f"📊 Risk: 1.0% of account")
        if position_data.get('size', 0) > 0:
            explanation.append(f"💵 Position Size: {position_data['size']} units")
            explanation.append(f"💰 Risk Amount: ${position_data.get('risk_amount', 0):.2f}")
        
        return explanation


# Backward compatibility class
class SMCSignalEngine:
    """
    Legacy SMC Signal Engine for backward compatibility
    """
    
    def __init__(self, candles: List[Dict]):
        self.candles = candles

    def analyze(self) -> Dict:
        """
        Simple SMC analysis
        """
        try:
            from .structure import detect_structure
            from .liquidity import detect_liquidity
            from .breaker import detect_breaker
            
            structure = detect_structure(self.candles)
            liquidity = detect_liquidity(self.candles)
            breaker = detect_breaker(self.candles)
            
            confidence = 0
            
            if structure in ["bullish", "bearish"]:
                confidence += 40
            if liquidity:
                confidence += 30
            if breaker:
                confidence += 30
            
            if confidence >= 70:
                if structure == "bullish":
                    signal = "BUY"
                elif structure == "bearish":
                    signal = "SELL"
                else:
                    signal = "NO_TRADE"
            else:
                signal = "NO_TRADE"
            
            return {
                "signal": signal,
                "structure": structure,
                "confidence": confidence
            }
            
        except Exception as e:
            print(f"Legacy SMC Engine Error: {e}")
            return {
                "signal": "ANALYSIS_ERROR",
                "structure": "unknown",
                "confidence": 0
            }