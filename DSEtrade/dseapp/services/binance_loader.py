import requests
from datetime import datetime
from django.utils import timezone
from dseapp.models import Candle

BINANCE_URL = "https://api.binance.com/api/v3/klines"

TF_MAP = {
    "M1": "1m",
    "M5": "5m",
    "M15": "15m",
    "M30": "30m",
    "H1": "1h",
    "H4": "4h",
    "D1": "1d"
}

SUPPORTED_SYMBOLS = [
    "BTCUSDT",
    "ETHUSDT",
    "BNBUSDT",
]

SUPPORTED_TIMEFRAMES = list(TF_MAP.keys())


def fetch_and_store(symbol, timeframe, limit=200):

    # Validate input
    if symbol not in SUPPORTED_SYMBOLS:
        print("Unsupported symbol")
        return

    interval = TF_MAP.get(timeframe)
    if not interval:
        print("Unsupported timeframe")
        return

    params = {
        "symbol": symbol,
        "interval": interval,
        "limit": limit
    }

    try:
        response = requests.get(BINANCE_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        if not isinstance(data, list):
            print("Invalid response from Binance:", data)
            return

        for k in data:
            open_time = datetime.fromtimestamp(int(k[0]) / 1000, tz=timezone.utc)

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

        print(f"{symbol} {timeframe} updated successfully.")

    except requests.RequestException as e:
        print("Binance request failed:", e)

    except Exception as e:
        print("Unexpected error:", e)
