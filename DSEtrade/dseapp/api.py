from rest_framework.views import APIView
from rest_framework.response import Response
from dseapp.signals.smc_engine import SMCSignalEngine
from dseapp.models import Candle
from dseapp.services.binance_loader import (
    fetch_and_store,
    SUPPORTED_SYMBOLS,
    SUPPORTED_TIMEFRAMES
)

class CurrentSignalView(APIView):

    def get(self, request):

        symbol = request.GET.get("symbol", "BTCUSDT")
        timeframe = request.GET.get("tf", "15m")

        # Validate input
        if symbol not in SUPPORTED_SYMBOLS:
            return Response({
                "error": "Unsupported symbol"
            })

        if timeframe not in SUPPORTED_TIMEFRAMES:
            return Response({
                "error": "Unsupported timeframe"
            })

        qs = Candle.objects.filter(
            symbol=symbol,
            timeframe=timeframe
        ).order_by("-time")[:200]

        # Auto fetch if empty
        if not qs.exists():
            fetch_and_store(symbol, timeframe)

            qs = Candle.objects.filter(
                symbol=symbol,
                timeframe=timeframe
            ).order_by("-time")[:200]

            if not qs.exists():
                return Response({
                    "signal": "NO_DATA",
                    "confidence": 0,
                    "price": None
                })

        candles = list(reversed(list(qs.values(
            "time", "open", "high", "low", "close"
        ))))

        engine = SMCSignalEngine(candles)
        result = engine.analyze()

        result["price"] = candles[-1]["close"]
        result["symbol"] = symbol
        result["timeframe"] = timeframe

        return Response(result)
