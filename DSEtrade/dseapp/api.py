from rest_framework.decorators import api_view
from rest_framework.response import Response
from dseapp.signals.smc_engine import SMCSignalEngine


@api_view(["POST"])
def current_signal(request):

    candles = request.data.get("candles", [])

    engine = SMCSignalEngine(candles)
    result = engine.analyze()

    return Response(result)
