from django.utils import timezone
from datetime import timedelta

from dseapp.models import Candle, SignalLog
from dseapp.signals.smc_engine import ProfessionalSMCEngine


def is_candle_closed(symbol, timeframe):
    latest = Candle.objects.filter(
        symbol=symbol,
        timeframe=timeframe
    ).order_by("-time").first()

    if not latest:
        return False

    tf_minutes = {
        "1m": 1,
        "5m": 5,
        "15m": 15,
        "30m": 30,
        "1h": 60,
        "4h": 240,
        "1d": 1440
    }.get(timeframe, 15)

    return latest.time <= timezone.now() - timedelta(minutes=tf_minutes)