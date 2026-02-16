from rest_framework.views import APIView
from rest_framework.response import Response
from dseapp.signals.smc_engine import SMCSignalEngine
from dseapp.models import Candle


class CurrentSignalView(APIView):

    def get(self, request):

        symbol = request.GET.get("symbol", "BTCUSDT")
        timeframe = request.GET.get("tf", "M15")

        qs = (
            Candle.objects
            .filter(symbol=symbol, timeframe=timeframe)
            .order_by("-time")[:200]
        )

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

        return Response(result)
