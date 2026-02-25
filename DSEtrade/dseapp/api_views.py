from rest_framework.views import APIView
from rest_framework.response import Response
from django.utils import timezone
from datetime import timedelta

from dseapp.signals.smc_engine import ProfessionalSMCEngine
from dseapp.models import Candle, SignalLog
from dseapp.services.binance_loader import fetch_and_store as fetch_binance
from dseapp.services.twelvedata_loader import fetch_twelvedata_and_store


class CurrentSignalView(APIView):

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

        # 1️⃣ Ensure latest data exists
        self._ensure_fresh_data(symbol, timeframe)

        # 2️⃣ Check if new candle closed
        self._run_engine_if_new_candle(symbol, timeframe)

        # 3️⃣ Return latest cached signal
        return self._get_latest_signal(symbol, timeframe)

    # --------------------------------------------------
    # DATA UPDATE
    # --------------------------------------------------

    def _ensure_fresh_data(self, symbol, timeframe):
        latest = Candle.objects.filter(
            symbol=symbol,
            timeframe=timeframe
        ).order_by("-time").first()

        tf_minutes = self.TF_MINUTES.get(timeframe, 15)

        if not latest or latest.time < timezone.now() - timedelta(minutes=tf_minutes):
            if symbol.endswith("USDT"):
                fetch_binance(symbol, timeframe)
            else:
                fetch_twelvedata_and_store(symbol, timeframe)

    # --------------------------------------------------
    # ENGINE RUN ONLY IF NEW CANDLE
    # --------------------------------------------------

    def _run_engine_if_new_candle(self, symbol, timeframe):

        latest_candle = Candle.objects.filter(
            symbol=symbol,
            timeframe=timeframe
        ).order_by("-time").first()

        if not latest_candle:
            return

        # Last generated signal
        last_signal = SignalLog.objects.filter(
            symbol=symbol,
            timeframe=timeframe
        ).order_by("-created_at").first()

        # If already analyzed this candle → do nothing
        if last_signal and last_signal.created_at >= latest_candle.time:
            return

        # Load candles
        candles = list(Candle.objects.filter(
            symbol=symbol,
            timeframe=timeframe
        ).order_by("time").values(
            "time", "open", "high", "low", "close", "volume"
        ))

        if len(candles) < 50:
            return

        # Run engine
        engine = ProfessionalSMCEngine(
            candles_htf=candles,
            candles_mtf=candles,
            candles_ltf=candles,
            account_balance=10000,
            risk_percent=1.0
        )

        result = engine.analyze()

        # Save signal
        SignalLog.objects.create(
            symbol=symbol,
            timeframe=timeframe,
            signal=result.signal,
            direction=result.direction,
            confidence=result.confidence,
            entry_price=result.entry_price,
            stop_loss=result.stop_loss,
            take_profit_1=result.take_profit_1,
            take_profit_2=result.take_profit_2,
            take_profit_3=result.take_profit_3
        )

    # --------------------------------------------------
    # RETURN CACHED SIGNAL
    # --------------------------------------------------

    def _get_latest_signal(self, symbol, timeframe):

        signal = SignalLog.objects.filter(
            symbol=symbol,
            timeframe=timeframe
        ).order_by("-created_at").first()

        if not signal:
            return Response({
                "signal": "WAITING_FOR_CLOSE",
                "confidence": 0,
                "symbol": symbol,
                "timeframe": timeframe
            })

        return Response({
            "signal": signal.signal,
            "direction": signal.direction,
            "confidence": signal.confidence,
            "entry_price": signal.entry_price,
            "stop_loss": signal.stop_loss,
            "take_profit_1": signal.take_profit_1,
            "take_profit_2": signal.take_profit_2,
            "take_profit_3": signal.take_profit_3,
            "symbol": symbol,
            "timeframe": timeframe
        })