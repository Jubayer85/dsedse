import requests
from datetime import datetime
from dseapp.models import Candle

# Direct Binance Symbols
SUPPORTED_SYMBOLS = [
    "BTCUSDT",
    "ETHUSDT",
    "EURUSDT",
    "XAUUSDT",
    "XAGUSDT",
]

# API → DB timeframe mapping
SUPPORTED_TIMEFRAMES = {
    "1m": "1m",
    "5m": "5m",
    "15m": "15m",
    "1h": "1h",
    "4h": "4h",
    "1d": "1d",
}


def fetch_and_store(symbol, timeframe, limit=200):

    if symbol not in SUPPORTED_SYMBOLS:
        return

    if timeframe not in SUPPORTED_TIMEFRAMES:
        return

    url = "https://api.binance.com/api/v3/klines"

    params = {
        "symbol": symbol,
        "interval": SUPPORTED_TIMEFRAMES[timeframe],
        "limit": limit
    }

    response = requests.get(url, params=params, timeout=10)

    if response.status_code != 200:
        return

    data = response.json()

    for k in data:
        Candle.objects.update_or_create(
            symbol=symbol,
            timeframe=timeframe,
            time=datetime.fromtimestamp(k[0] / 1000),
            defaults={
                "open": float(k[1]),
                "high": float(k[2]),
                "low": float(k[3]),
                "close": float(k[4]),
            }
        )
