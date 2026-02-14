from rest_framework.decorators import api_view
from rest_framework.response import Response
from dseapp.signals.smc_engine import SMCSignalEngine
from dseapp.models import Candle


@api_view(["GET"])
def current_signal(request):

    symbol = request.GET.get("symbol", "EURUSD")
    timeframe = request.GET.get("tf", "M15")

    qs = (
        Candle.objects
        .filter(symbol=symbol, timeframe=timeframe)
        .order_by("-time")[:200]
    )

    candles = list(qs.values("open", "high", "low", "close"))

    if not candles:
        return Response({
            "signal": "NO_DATA",
            "structure": "--",
            "confidence": 0,
            "price": None
        })

    engine = SMCSignalEngine(candles)
    result = engine.analyze()

    result["symbol"] = symbol
    result["timeframe"] = timeframe

    return Response(result)
