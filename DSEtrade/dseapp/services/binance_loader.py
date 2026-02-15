import requests
from datetime import datetime
from dseapp.models import Candle


BINANCE_URL = "https://api.binance.com/api/v3/klines"


INTERVAL_MAP = {
    "M1": "1m",
    "M5": "5m",
    "M15": "15m",
    "H1": "1h",
    "H4": "4h",
    "D1": "1d",
}


def fetch_and_store(symbol="BTCUSDT", timeframe="M15", limit=200):

    interval = INTERVAL_MAP.get(timeframe, "15m")

    params = {
        "symbol": symbol,
        "interval": interval,
        "limit": limit
    }

    response = requests.get(BINANCE_URL, params=params)
    data = response.json()

    for k in data:

        open_time = datetime.fromtimestamp(k[0] / 1000)

        Candle.objects.update_or_create(
            symbol=symbol,
            timeframe=timeframe,
            time=open_time,
            defaults={
                "open": float(k[1]),
                "high": float(k[2]),
                "low": float(k[3]),
                "close": float(k[4]),
            }
        )

    return len(data)
