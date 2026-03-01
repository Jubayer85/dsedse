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

    # =============================================
    # MAIN GET
    # =============================================

    def get(self, request):

        symbol = request.GET.get("symbol", "XAUUSD")
        timeframe = request.GET.get("tf", "15m")

        if timeframe not in self.VALID_TIMEFRAMES:
            timeframe = "15m"

        self._ensure_fresh_data(symbol, timeframe)
        self._run_engine_if_new_candle(symbol, timeframe)

        return self._get_latest_signal(symbol, timeframe)

    # =============================================
    # DATA ENSURE
    # =============================================

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

    # =============================================
    # RUN ENGINE (3 LAYER)
    # =============================================

    def _run_engine_if_new_candle(self, symbol, timeframe):

        latest_candle = Candle.objects.filter(
            symbol=symbol,
            timeframe=timeframe
        ).order_by("-time").first()

        if not latest_candle:
            return

        last_signal = SignalLog.objects.filter(
            symbol=symbol,
            timeframe=timeframe
        ).order_by("-created_at").first()

        # Already processed
        if last_signal and last_signal.created_at >= latest_candle.time:
            return

        candles = list(
            Candle.objects.filter(
                symbol=symbol,
                timeframe=timeframe
            ).order_by("time").values(
                "time", "open", "high", "low", "close", "volume"
            )
        )

        if len(candles) < 50:
            return

        # -------------------------------
        # ENGINE RUN
        # -------------------------------

        engine = ProfessionalSMCEngine(
            candles_htf=candles,
            candles_mtf=candles,
            candles_ltf=candles
        )

        results = engine.analyze_all()

        # -------------------------------
        # SAVE SINGLE ROW (JSON STORAGE)
        # -------------------------------

        SignalLog.objects.create(
            symbol=symbol,
            timeframe=timeframe,
            signal="MULTI_LAYER",
            direction="MULTI",
            confidence=0,
            entry_price=0,
            stop_loss=0,
            take_profit_1=0,
            take_profit_2=0,
            take_profit_3=0,
            extra_data={
                "scalp": results["scalp"].__dict__,
                "institutional": results["institutional"].__dict__,
                "hybrid": results["hybrid"].__dict__
            }
        )

    # =============================================
    # RETURN LATEST MULTI LAYER
    # =============================================

    def _get_latest_signal(self, symbol, timeframe):

        signal = SignalLog.objects.filter(
            symbol=symbol,
            timeframe=timeframe
        ).order_by("-created_at").first()

        if not signal:
            return Response({
                "symbol": symbol,
                "timeframe": timeframe,
                "status": "WAITING_FOR_CLOSE"
            })

        return Response({
            "symbol": symbol,
            "timeframe": timeframe,
            "scalp": signal.extra_data.get("scalp"),
            "institutional": signal.extra_data.get("institutional"),
            "hybrid": signal.extra_data.get("hybrid"),
        })