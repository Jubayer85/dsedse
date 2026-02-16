import requests
from datetime import datetime
from dseapp.models import Candle

BINANCE_URL = "https://api.binance.com/api/v3/klines"

# ===============================
# Supported Symbols
# ===============================

SUPPORTED_SYMBOLS = [
    "BTCUSDT",
    "ETHUSDT",
    "EURUSDT",
    "XAUUSDT",
    "XAGUSDT",
]

# ===============================
# Timeframe Mapping (Frontend → Binance)
# ===============================

SUPPORTED_TIMEFRAMES = {
    "1m": "1m",
    "5m": "5m",
    "15m": "15m",
    "1h": "1h",
    "4h": "4h",
    "1d": "1d",
}

# Backward compatibility if you still use M15 style
TF_MAP = {
    "M1": "1m",
    "M5": "5m",
    "M15": "15m",
    "H1": "1h",
    "H4": "4h",
    "D1": "1d"
}


def fetch_and_store(symbol, timeframe, limit=200):

    # Validate symbol
    if symbol not in SUPPORTED_SYMBOLS:
        return False

    # Accept both styles (15m / M15)
    interval = (
        SUPPORTED_TIMEFRAMES.get(timeframe)
        or TF_MAP.get(timeframe)
    )

    if not interval:
        return False

    params = {
        "symbol": symbol,
        "interval": interval,
        "limit": limit
    }

    try:
        response = requests.get(BINANCE_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        print("Binance fetch error:", e)
        return False

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

    return True
