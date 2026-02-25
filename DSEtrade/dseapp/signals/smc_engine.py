"""
Professional Institutional SMC Engine
- True Multi-Timeframe Alignment
- Volume Confirmed Liquidity Sweeps
- Sweep Strength Scoring
- Order Block + FVG Integration
- ATR Based Risk Model
- Clean Confidence System
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime

from .structure import detect_structure, detect_mss
from .liquidity import volume_confirmed_sweep
from .breaker import detect_breaker_block
from .fvg import detect_fvg
from .order_block import detect_order_block
from .mitigation import detect_mitigation
from .imbalance import detect_imbalance
from .utils import calculate_atr


# =====================================================
# SIGNAL RESULT MODEL
# =====================================================

@dataclass
class SignalResult:
    signal: str = "NO_TRADE"
    direction: str = "NO_TRADE"
    confidence: int = 0
    entry_price: float = 0.0
    stop_loss: float = 0.0
    take_profit_1: float = 0.0
    take_profit_2: float = 0.0
    take_profit_3: float = 0.0
    risk_reward_ratio: float = 0.0
    position_size: float = 0.0
    structure: str = "unknown"
    liquidity_swept: bool = False
    timestamp: datetime = field(default_factory=datetime.now)


# =====================================================
# PROFESSIONAL ENGINE
# =====================================================

class ProfessionalSMCEngine:

    def __init__(
        self,
        candles_htf: List[Dict[str, Any]],
        candles_mtf: List[Dict[str, Any]],
        candles_ltf: List[Dict[str, Any]],
        account_balance: float = 10000,
        risk_percent: float = 1.0,
        commission: float = 0.001,
        slippage: float = 0.0005
    ):

        self.htf = candles_htf or []
        self.mtf = candles_mtf or []
        self.ltf = candles_ltf or []

        self.account_balance = account_balance
        self.risk_percent = risk_percent / 100
        self.commission = commission
        self.slippage = slippage

        self.atr = calculate_atr(self.ltf, 14) if self.ltf else 0


    # =====================================================
    # MAIN ANALYSIS
    # =====================================================

    def analyze(self) -> SignalResult:

        if not self.ltf or len(self.ltf) < 30:
            return SignalResult()

        current_price = self.ltf[-1]["close"]

        # ---------------- HTF ----------------
        htf_structure = detect_structure(self.htf)
        htf_mss = detect_mss(self.htf)
        htf_ob = detect_order_block(self.htf)
        htf_sweep = volume_confirmed_sweep(self.htf)

        # ---------------- MTF ----------------
        mtf_structure = detect_structure(self.mtf)
        mtf_sweep = volume_confirmed_sweep(self.mtf)
        mtf_fvg = detect_fvg(self.mtf)
        mtf_breaker = detect_breaker_block(self.mtf)
        mtf_ob = detect_order_block(self.mtf)
        mtf_imbalance = detect_imbalance(self.mtf)

        # ---------------- LTF ----------------
        ltf_structure = detect_structure(self.ltf)
        ltf_sweep = volume_confirmed_sweep(self.ltf)
        ltf_fvg = detect_fvg(self.ltf)
        ltf_mitigation = detect_mitigation(self.ltf)

        # =====================================================
        # DIRECTION
        # =====================================================

        direction = self._determine_direction(
            htf_structure, mtf_structure, ltf_structure
        )

        # =====================================================
        # CONFIDENCE
        # =====================================================

        confidence = self._calculate_confidence({
            "htf_structure": htf_structure in ["bullish", "bearish"],
            "htf_ob": htf_ob is not None,
            "htf_mss": htf_mss,
            "mtf_fvg": mtf_fvg is not None,
            "mtf_breaker": mtf_breaker is not None,
            "mtf_ob": mtf_ob is not None,
            "mtf_imbalance": mtf_imbalance,
            "ltf_fvg": ltf_fvg is not None,
            "ltf_mitigation": ltf_mitigation,
        })

        # Sweep Strength Bonus
        confidence += self._sweep_bonus(mtf_sweep)
        confidence += self._sweep_bonus(ltf_sweep)

        confidence = min(100, confidence)

        # =====================================================
        # ENTRY + SL + TP
        # =====================================================

        entry_data = self._calculate_trade_levels(
            direction,
            current_price,
            ltf_fvg,
            htf_ob
        )

        # =====================================================
        # POSITION SIZE
        # =====================================================

        position_size = self._calculate_position_size(
            entry_data["entry"],
            entry_data["sl"]
        )

        # =====================================================
        # SIGNAL
        # =====================================================

        signal = self._generate_signal(direction, confidence)

        return SignalResult(
            signal=signal,
            direction=direction.upper() if direction else "NO_TRADE",
            confidence=confidence,
            entry_price=entry_data["entry"],
            stop_loss=entry_data["sl"],
            take_profit_1=entry_data["tp1"],
            take_profit_2=entry_data["tp2"],
            take_profit_3=entry_data["tp3"],
            risk_reward_ratio=entry_data["rr"],
            position_size=position_size,
            structure=f"HTF:{htf_structure} | MTF:{mtf_structure} | LTF:{ltf_structure}",
            liquidity_swept=mtf_sweep["detected"] or ltf_sweep["detected"]
        )


    # =====================================================
    # DIRECTION LOGIC
    # =====================================================

    def _determine_direction(self, htf, mtf, ltf):

        if htf == "bullish" and mtf == "bullish" and ltf == "bullish":
            return "long"

        if htf == "bearish" and mtf == "bearish" and ltf == "bearish":
            return "short"

        if htf in ["bullish", "accumulation"] and mtf == "bullish":
            return "long"

        if htf in ["bearish", "distribution"] and mtf == "bearish":
            return "short"

        return None


    # =====================================================
    # CONFIDENCE ENGINE
    # =====================================================

    def _calculate_confidence(self, factors: Dict[str, bool]) -> int:

        weights = {
            "htf_structure": 20,
            "htf_ob": 15,
            "htf_mss": 15,
            "mtf_fvg": 10,
            "mtf_breaker": 10,
            "mtf_ob": 10,
            "mtf_imbalance": 8,
            "ltf_fvg": 6,
            "ltf_mitigation": 6,
        }

        score = 0
        for key, weight in weights.items():
            if factors.get(key):
                score += weight

        confirmations = sum(factors.values())
        if confirmations >= 5:
            score += 10
        if confirmations >= 7:
            score += 15

        return score


    def _sweep_bonus(self, sweep_data: Dict) -> int:
        if not sweep_data["detected"]:
            return 0
        if sweep_data["strength"] > 70:
            return 15
        if sweep_data["strength"] > 50:
            return 8
        return 0


    # =====================================================
    # TRADE LEVELS
    # =====================================================

    def _calculate_trade_levels(self, direction, price, ltf_fvg, htf_ob):

        if not direction:
            return {"entry": price, "sl": price, "tp1": price,
                    "tp2": price, "tp3": price, "rr": 0}

        entry = price
        if ltf_fvg and ltf_fvg.get("entry"):
            entry = ltf_fvg["entry"]
        elif htf_ob and htf_ob.get("entry"):
            entry = htf_ob["entry"]

        sl_distance = self.atr * 1.5 if self.atr else price * 0.005

        if direction == "long":
            sl = entry - sl_distance
            tp1 = entry + sl_distance * 2
            tp2 = entry + sl_distance * 3
            tp3 = entry + sl_distance * 5
        else:
            sl = entry + sl_distance
            tp1 = entry - sl_distance * 2
            tp2 = entry - sl_distance * 3
            tp3 = entry - sl_distance * 5

        rr = 2

        return {
            "entry": round(entry, 2),
            "sl": round(sl, 2),
            "tp1": round(tp1, 2),
            "tp2": round(tp2, 2),
            "tp3": round(tp3, 2),
            "rr": rr
        }


    # =====================================================
    # POSITION SIZE
    # =====================================================

    def _calculate_position_size(self, entry, sl):

        if entry <= 0 or sl <= 0:
            return 0

        risk_amount = self.account_balance * self.risk_percent
        sl_distance = abs(entry - sl)

        if sl_distance == 0:
            return 0

        size = risk_amount / sl_distance
        adjusted = size * (1 - self.commission - self.slippage)

        return round(adjusted, 4)


    # =====================================================
    # SIGNAL LOGIC
    # =====================================================

    def _generate_signal(self, direction, confidence):

        if not direction or confidence < 60:
            return "NO_TRADE"

        if confidence >= 85:
            return f"STRONG_{direction.upper()}"

        if confidence >= 70:
            return direction.upper()

        return f"WEAK_{direction.upper()}"