from rest_framework.views import APIView
from rest_framework.response import Response
from django.utils import timezone
from datetime import timedelta

from dseapp.signals.smc_engine import ProfessionalSMCEngine
from dseapp.models import Candle
from dseapp.services.binance_loader import fetch_and_store as fetch_binance
from dseapp.services.twelvedata_loader import fetch_twelvedata_and_store


class CurrentSignalView(APIView):
    """
    Production-Ready Signal API
    - Auto market data update
    - True multi-timeframe loading
    - Safe candle handling
    """

    VALID_TIMEFRAMES = ['1m', '5m', '15m', '30m', '1h', '4h', '1d']

    TF_MINUTES = {
        "1m": 1,
        "5m": 5,
        "15m": 15,
        "30m": 30,
        "1h": 60,
        "4h": 240,
        "1d": 1440
    }

    def get(self, request):
        symbol = request.GET.get("symbol", "XAUUSD")
        timeframe = request.GET.get("tf", "15m")

        if timeframe not in self.VALID_TIMEFRAMES:
            timeframe = "15m"

        # 1️⃣ Ensure latest candle exists
        self._ensure_fresh_data(symbol, timeframe)

        # 2️⃣ Load multi-timeframe candles
        candles_ltf = self._get_candles(symbol, timeframe)
        candles_mtf = self._get_candles(symbol, self._get_mtf(timeframe))
        candles_htf = self._get_candles(symbol, self._get_htf(timeframe))

        if not candles_ltf:
            return Response({
                "signal": "NO_DATA",
                "confidence": 0,
                "price": 0,
                "structure": "No market data",
                "symbol": symbol,
                "timeframe": timeframe
            })

        return self._analyze_with_engine(
            candles_htf,
            candles_mtf,
            candles_ltf,
            symbol,
            timeframe
        )

    # --------------------------------------------------
    # DATA FRESHNESS CHECK
    # --------------------------------------------------

    def _ensure_fresh_data(self, symbol, timeframe):
        latest = Candle.objects.filter(
            symbol=symbol,
            timeframe=timeframe
        ).order_by("-time").first()

        tf_minutes = self.TF_MINUTES.get(timeframe, 15)

        if not latest or latest.time < timezone.now() - timedelta(minutes=tf_minutes):
            symbol_type = self._get_symbol_type(symbol)

            if symbol_type == "crypto":
                fetch_binance(symbol, timeframe)
            else:
                fetch_twelvedata_and_store(symbol, timeframe)

    # --------------------------------------------------
    # MULTI TIMEFRAME MAPPING
    # --------------------------------------------------

    def _get_mtf(self, tf):
        mapping = {
            "1m": "5m",
            "5m": "15m",
            "15m": "1h",
            "30m": "1h",
            "1h": "4h",
            "4h": "1d"
        }
        return mapping.get(tf, tf)

    def _get_htf(self, tf):
        mapping = {
            "1m": "15m",
            "5m": "1h",
            "15m": "4h",
            "30m": "4h",
            "1h": "1d",
            "4h": "1d"
        }
        return mapping.get(tf, tf)

    # --------------------------------------------------
    # CLEAN CANDLE LOADER (NO FLOAT BUG)
    # --------------------------------------------------

    def _get_candles(self, symbol, timeframe, count=200):
        qs = Candle.objects.filter(
            symbol=symbol,
            timeframe=timeframe
        ).order_by("-time")[:count]

        if not qs.exists():
            return []

        candles = []
        for obj in reversed(qs):
            candles.append({
                "time": obj.time,
                "open": float(obj.open),
                "high": float(obj.high),
                "low": float(obj.low),
                "close": float(obj.close),
                "volume": float(obj.volume or 0)
            })

        return candles

    # --------------------------------------------------
    # SYMBOL TYPE
    # --------------------------------------------------

    def _get_symbol_type(self, symbol):
        crypto = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT']
        forex = ['EURUSD', 'GBPUSD', 'USDJPY', 'AUDUSD']
        metals = ['XAUUSD', 'XAGUSD']

        if symbol in crypto:
            return "crypto"
        if symbol in forex:
            return "forex"
        if symbol in metals:
            return "metals"

        return "unknown"

    # --------------------------------------------------
    # ENGINE ANALYSIS
    # --------------------------------------------------

    def _analyze_with_engine(self, candles_htf, candles_mtf,
                             candles_ltf, symbol, timeframe):

        if len(candles_ltf) < 30:
            return Response({
                "signal": "INSUFFICIENT_DATA",
                "confidence": 0,
                "price": candles_ltf[-1]['close'],
                "symbol": symbol,
                "timeframe": timeframe
            })

        try:
            engine = ProfessionalSMCEngine(
                candles_htf=candles_htf,
                candles_mtf=candles_mtf,
                candles_ltf=candles_ltf,
                account_balance=10000,
                risk_percent=1.0
            )

            result = engine.analyze()

            return Response({
                "signal": result.signal,
                "direction": result.direction,
                "confidence": result.confidence,
                "entry_price": result.entry_price,
                "stop_loss": result.stop_loss,
                "take_profit_1": result.take_profit_1,
                "take_profit_2": result.take_profit_2,
                "take_profit_3": result.take_profit_3,
                "risk_reward": result.risk_reward_ratio,
                "position_size": result.position_size,
                "structure": result.structure,
                "symbol": symbol,
                "timeframe": timeframe
            })

        except Exception as e:
            print("SMC Engine Error:", e)

            return Response({
                "signal": "ENGINE_ERROR",
                "confidence": 0,
                "price": candles_ltf[-1]['close'],
                "symbol": symbol,
                "timeframe": timeframe
            })