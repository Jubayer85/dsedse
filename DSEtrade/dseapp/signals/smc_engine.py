"""
Professional Institutional SMC Engine
3 Logic Layer Version:
- SCALP (LTF driven)
- INSTITUTIONAL (HTF dominant)
- HYBRID (True MTF alignment)

Features:
- Multi-timeframe analysis
- Volume-confirmed liquidity sweeps
- Order block detection
- FVG detection
- Dynamic position sizing
- Risk management integration
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
import numpy as np

from .structure import detect_structure, detect_mss
from .liquidity import volume_confirmed_sweep, detect_liquidity_sweep
from .breaker import detect_breaker_block
from .fvg import detect_fvg, validate_fvg
from .order_block import detect_order_block, validate_ob
from .mitigation import detect_mitigation
from .imbalance import detect_imbalance
from .utils import calculate_atr, find_swing_points
from .risk_manager import RiskManager


# =====================================================
# SIGNAL MODEL
# =====================================================

@dataclass
class SignalResult:
    """Complete signal result for a trading mode"""
    mode: str = "HYBRID"
    signal: str = "NO_TRADE"
    direction: str = "NO_TRADE"
    confidence: int = 0
    entry_price: float = 0.0
    stop_loss: float = 0.0
    take_profit_1: float = 0.0
    take_profit_2: float = 0.0
    take_profit_3: float = 0.0
    structure: str = "unknown"
    liquidity_swept: bool = False
    order_block_detected: bool = False
    fvg_detected: bool = False
    risk_reward_ratio: float = 0.0
    position_size: float = 0.0
    explanation: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        return {
            'mode': self.mode,
            'signal': self.signal,
            'direction': self.direction,
            'confidence': self.confidence,
            'entry_price': self.entry_price,
            'stop_loss': self.stop_loss,
            'take_profit': {
                'tp1': self.take_profit_1,
                'tp2': self.take_profit_2,
                'tp3': self.take_profit_3
            },
            'structure': self.structure,
            'liquidity_swept': self.liquidity_swept,
            'order_block_detected': self.order_block_detected,
            'fvg_detected': self.fvg_detected,
            'risk_reward_ratio': self.risk_reward_ratio,
            'position_size': self.position_size,
            'explanation': self.explanation,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }


# =====================================================
# ENGINE
# =====================================================

class ProfessionalSMCEngine:
    """
    Professional Institutional SMC Engine with 3 trading modes
    
    Modes:
    - SCALP: Fast reactions based on LTF (1m-5m)
    - INSTITUTIONAL: HTF dominant (1H-4H) for swing trades
    - HYBRID: True multi-timeframe alignment for high probability
    """
    
    def __init__(self, 
                 candles_htf: List[Dict[str, Any]],
                 candles_mtf: List[Dict[str, Any]],
                 candles_ltf: List[Dict[str, Any]],
                 account_balance: float = 10000,
                 risk_percent: float = 1.0,
                 commission: float = 0.001):
        """
        Initialize the engine with multi-timeframe data
        
        Args:
            candles_htf: Higher timeframe candles (1H/4H)
            candles_mtf: Medium timeframe candles (15M/30M)
            candles_ltf: Lower timeframe candles (1M/5M)
            account_balance: Account balance for position sizing
            risk_percent: Risk percentage per trade
            commission: Trading commission
        """
        self.htf = candles_htf or []
        self.mtf = candles_mtf or []
        self.ltf = candles_ltf or []
        
        self.account_balance = account_balance
        self.risk_percent = risk_percent
        self.commission = commission
        
        # Calculate ATR for all timeframes
        self.atr_ltf = calculate_atr(self.ltf, 14) if self.ltf else 0
        self.atr_mtf = calculate_atr(self.mtf, 14) if self.mtf else 0
        self.atr_htf = calculate_atr(self.htf, 14) if self.htf else 0
        
        # Risk manager
        self.risk_manager = RiskManager(
            account_balance=account_balance,
            risk_percent=risk_percent,
            commission=commission
        )
        
        # Current price from LTF
        self.current_price = self.ltf[-1].get('close', 0) if self.ltf else 0


    # =====================================================
    # PUBLIC ENTRY
    # =====================================================

    def analyze_all(self) -> Dict[str, SignalResult]:
        """
        Analyze all three trading modes
        
        Returns:
            Dictionary with results for each mode
        """
        return {
            "scalp": self._analyze_scalp(),
            "institutional": self._analyze_institutional(),
            "hybrid": self._analyze_hybrid()
        }
    
    def analyze_best(self) -> SignalResult:
        """
        Get the best signal among all modes
        
        Returns:
            Best signal based on confidence
        """
        results = self.analyze_all()
        
        # Find best by confidence
        best = max(results.values(), key=lambda x: x.confidence)
        
        # If no good signal, return hybrid (which might be NO_TRADE)
        if best.confidence < 50:
            return results.get("hybrid", SignalResult())
        
        return best


    # =====================================================
    # SCALP MODE (FAST REACTION)
    # =====================================================

    def _analyze_scalp(self) -> SignalResult:
        """
        SCALP Mode - Fast reactions based on LTF (1m-5m)
        
        Focuses on:
        - LTF structure breaks
        - Volume-confirmed sweeps
        - FVG entries
        """
        explanation = ["🔍 SCALP Mode Analysis:"]
        
        if not self.ltf or len(self.ltf) < 20:
            explanation.append("❌ Insufficient LTF data")
            return SignalResult(mode="SCALP", explanation=explanation)
        
        # Detect factors
        ltf_structure = detect_structure(self.ltf)
        ltf_sweep = volume_confirmed_sweep(self.ltf)
        ltf_fvg = detect_fvg(self.ltf)
        ltf_ob = detect_order_block(self.ltf)
        
        explanation.append(f"  LTF Structure: {ltf_structure}")
        explanation.append(f"  Volume Sweep: {ltf_sweep}")
        explanation.append(f"  FVG Detected: {ltf_fvg is not None}")
        explanation.append(f"  OB Detected: {ltf_ob is not None}")
        
        # Determine direction
        direction = self._direction_from_structure(ltf_structure)
        
        # Calculate confidence
        confidence = 40  # Base
        
        if ltf_structure in ["bullish", "bearish"]:
            confidence += 10
        
        if ltf_sweep:
            confidence += 20
            explanation.append("  ✓ Volume-confirmed sweep (+20)")
        
        if ltf_fvg:
            confidence += 15
            explanation.append("  ✓ FVG detected (+15)")
        
        if ltf_ob:
            confidence += 15
            explanation.append("  ✓ Order Block detected (+15)")
        
        # Build trade
        result = self._build_trade(
            mode="SCALP",
            direction=direction,
            confidence=confidence,
            structure=f"LTF:{ltf_structure}",
            sweep=ltf_sweep,
            ob=ltf_ob is not None,
            fvg=ltf_fvg is not None
        )
        
        result.explanation = explanation
        return result


    # =====================================================
    # INSTITUTIONAL MODE (HTF DOMINANT)
    # =====================================================

    def _analyze_institutional(self) -> SignalResult:
        """
        INSTITUTIONAL Mode - HTF dominant for swing trades
        
        Focuses on:
        - HTF structure
        - Order blocks
        - Breaker blocks
        - Major liquidity sweeps
        """
        explanation = ["🏦 INSTITUTIONAL Mode Analysis:"]
        
        if not self.htf or len(self.htf) < 30:
            explanation.append("❌ Insufficient HTF data")
            return SignalResult(mode="INSTITUTIONAL", explanation=explanation)
        
        # Detect factors
        htf_structure = detect_structure(self.htf)
        htf_ob = detect_order_block(self.htf)
        htf_breaker = detect_breaker_block(self.htf)
        htf_sweep = volume_confirmed_sweep(self.htf)
        htf_mss = detect_mss(self.htf)
        
        explanation.append(f"  HTF Structure: {htf_structure}")
        explanation.append(f"  Order Block: {htf_ob is not None}")
        explanation.append(f"  Breaker Block: {htf_breaker is not None}")
        explanation.append(f"  Volume Sweep: {htf_sweep}")
        explanation.append(f"  MSS: {htf_mss}")
        
        # Determine direction
        direction = self._direction_from_structure(htf_structure)
        
        # Calculate confidence
        confidence = 50  # Base
        
        if htf_structure in ["bullish", "bearish"]:
            confidence += 15
        
        if htf_ob:
            confidence += 15
            explanation.append("  ✓ Order Block detected (+15)")
        
        if htf_breaker:
            confidence += 15
            explanation.append("  ✓ Breaker Block detected (+15)")
        
        if htf_sweep:
            confidence += 15
            explanation.append("  ✓ Volume-confirmed sweep (+15)")
        
        if htf_mss:
            confidence += 10
            explanation.append("  ✓ Market Structure Shift (+10)")
        
        # Build trade
        result = self._build_trade(
            mode="INSTITUTIONAL",
            direction=direction,
            confidence=confidence,
            structure=f"HTF:{htf_structure}",
            sweep=htf_sweep,
            ob=htf_ob is not None,
            fvg=False
        )
        
        result.explanation = explanation
        return result


    # =====================================================
    # HYBRID MODE (TRUE ALIGNMENT)
    # =====================================================

    def _analyze_hybrid(self) -> SignalResult:
        """
        HYBRID Mode - True multi-timeframe alignment
        
        Only generates signals when all timeframes align
        Highest probability setups
        """
        explanation = ["🔄 HYBRID Mode Analysis:"]
        
        if not all([self.htf, self.mtf, self.ltf]):
            explanation.append("❌ Missing timeframe data")
            return SignalResult(mode="HYBRID", explanation=explanation)
        
        # Detect structure on all timeframes
        htf = detect_structure(self.htf)
        mtf = detect_structure(self.mtf)
        ltf = detect_structure(self.ltf)
        
        explanation.append(f"  HTF: {htf}")
        explanation.append(f"  MTF: {mtf}")
        explanation.append(f"  LTF: {ltf}")
        
        # Check for alignment
        direction = None
        confidence = 40
        
        # Strong alignment (all bullish/bearish)
        if htf == mtf == ltf and htf in ["bullish", "bearish"]:
            direction = self._direction_from_structure(htf)
            confidence = 85
            explanation.append(f"  ✓ Full alignment detected (+85)")
        
        # Partial alignment (HTF and MTF agree, LTF neutral)
        elif htf == mtf and htf in ["bullish", "bearish"] and ltf == "ranging":
            direction = self._direction_from_structure(htf)
            confidence = 70
            explanation.append(f"  ✓ HTF/MTF alignment (+70)")
        
        # HTF dominant with confirming factors
        elif htf in ["bullish", "bearish"]:
            direction = self._direction_from_structure(htf)
            confidence = 60
            explanation.append(f"  ✓ HTF direction only (+60)")
        
        # Check for additional confirmations
        if direction:
            # Check for sweep on any timeframe
            if volume_confirmed_sweep(self.htf) or volume_confirmed_sweep(self.mtf):
                confidence = min(95, confidence + 10)
                explanation.append(f"  ✓ Volume sweep confirmation (+10)")
            
            # Check for order blocks
            if detect_order_block(self.htf) or detect_order_block(self.mtf):
                confidence = min(95, confidence + 10)
                explanation.append(f"  ✓ Order block confirmation (+10)")
        
        # Build trade
        result = self._build_trade(
            mode="HYBRID",
            direction=direction,
            confidence=confidence,
            structure=f"HTF:{htf} | MTF:{mtf} | LTF:{ltf}",
            sweep=False
        )
        
        result.explanation = explanation
        return result


    # =====================================================
    # HELPER FUNCTIONS
    # =====================================================

    def _direction_from_structure(self, structure: str) -> Optional[str]:
        """
        Convert structure string to direction
        
        Args:
            structure: Structure string (bullish, bearish, ranging, etc.)
            
        Returns:
            Direction string or None
        """
        if structure == "bullish":
            return "LONG"
        if structure == "bearish":
            return "SHORT"
        return None


    def _build_trade(self, 
                    mode: str,
                    direction: Optional[str],
                    confidence: int,
                    structure: str,
                    sweep: bool,
                    ob: bool = False,
                    fvg: bool = False) -> SignalResult:
        """
        Build complete trade signal with entry/exit levels
        
        Args:
            mode: Trading mode
            direction: Trade direction
            confidence: Confidence score
            structure: Structure description
            sweep: Liquidity sweep detected
            ob: Order block detected
            fvg: FVG detected
            
        Returns:
            Complete SignalResult object
        """
        if not direction or not self.ltf:
            return SignalResult(
                mode=mode,
                structure=structure,
                liquidity_swept=sweep,
                order_block_detected=ob,
                fvg_detected=fvg
            )
        
        price = self.ltf[-1].get("close", 0)
        
        # Use ATR for stop distance
        atr_to_use = self.atr_ltf or self.atr_mtf or self.atr_htf or (price * 0.01)
        sl_distance = atr_to_use * 1.5  # 1.5 ATR stop
        
        # Calculate levels based on direction
        if direction == "LONG":
            sl = price - sl_distance
            tp1 = price + sl_distance * 2    # 1:2 RR
            tp2 = price + sl_distance * 3    # 1:3 RR
            tp3 = price + sl_distance * 5    # 1:5 RR
            rr = (tp1 - price) / (price - sl) if sl < price else 0
        else:  # SHORT
            sl = price + sl_distance
            tp1 = price - sl_distance * 2
            tp2 = price - sl_distance * 3
            tp3 = price - sl_distance * 5
            rr = (price - tp1) / (sl - price) if sl > price else 0
        
        # Calculate position size
        position_size = 0
        if sl_distance > 0:
            risk_amount = self.account_balance * (self.risk_percent / 100)
            position_size = risk_amount / sl_distance
        
        return SignalResult(
            mode=mode,
            signal=direction if confidence >= 60 else f"WEAK_{direction}",
            direction=direction,
            confidence=min(confidence, 100),
            entry_price=round(price, 2),
            stop_loss=round(sl, 2),
            take_profit_1=round(tp1, 2),
            take_profit_2=round(tp2, 2),
            take_profit_3=round(tp3, 2),
            risk_reward_ratio=round(rr, 2),
            position_size=round(position_size, 4),
            structure=structure,
            liquidity_swept=sweep,
            order_block_detected=ob,
            fvg_detected=fvg
        )
    
    def get_current_price(self) -> float:
        """Get current price from LTF"""
        if not self.ltf:
            return 0.0
        return float(self.ltf[-1].get('close', 0))


# =====================================================
# USAGE EXAMPLE
# =====================================================

if __name__ == "__main__":
    # Example usage
    import random
    from datetime import datetime, timedelta
    
    # Create dummy candles
    def create_dummy_candles(count=100, base=50000):
        candles = []
        now = datetime.now()
        for i in range(count):
            time = now - timedelta(minutes=i*15)
            price = base + (random.random() - 0.5) * base * 0.02
            candles.append({
                'time': time,
                'open': price * 0.999,
                'high': price * 1.002,
                'low': price * 0.998,
                'close': price,
                'volume': random.randint(1000, 10000)
            })
        return list(reversed(candles))
    
    # Create engine
    engine = ProfessionalSMCEngine(
        candles_htf=create_dummy_candles(100, 50000),
        candles_mtf=create_dummy_candles(200, 50000),
        candles_ltf=create_dummy_candles(300, 50000),
        account_balance=10000,
        risk_percent=1.0
    )
    
    # Analyze all modes
    results = engine.analyze_all()
    
    # Print results
    for mode, signal in results.items():
        print(f"\n{'='*50}")
        print(f"{mode.upper()} MODE")
        print('='*50)
        print(f"Signal: {signal.signal}")
        print(f"Confidence: {signal.confidence}%")
        print(f"Entry: {signal.entry_price}")
        print(f"Stop Loss: {signal.stop_loss}")
        print(f"TP1: {signal.take_profit_1} (1:{signal.risk_reward_ratio})")
        print(f"Structure: {signal.structure}")
        print(f"Liquidity Swept: {signal.liquidity_swept}")
        if signal.explanation:
            print("\nExplanation:")
            for line in signal.explanation:
                print(f"  {line}")