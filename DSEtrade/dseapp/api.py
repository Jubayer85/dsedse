from rest_framework.decorators import api_view
from rest_framework.response import Response
from dseapp.signals.smc_engine import SMCSignalEngine


@api_view(["GET"])
def current_signal(request):

    # এখানে ideally আপনার DB বা loader থাকবে
    candles = []  # temporarily dummy

    engine = SMCSignalEngine(candles)
    result = engine.analyze()

    return Response(result)
