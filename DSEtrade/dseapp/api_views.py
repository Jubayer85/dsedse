# dseapp/api_views.py

from rest_framework.views import APIView
from rest_framework.response import Response
from django.utils import timezone
import random
from datetime import datetime, timedelta

# মডেল ও সার্ভিস ইম্পোর্ট
from dseapp.models import Candle
from dseapp.signals.smc_engine import SMCSignalEngine
from dseapp.services.binance_loader import fetch_and_store as fetch_binance
from dseapp.services.twelvedata_loader import fetch_twelvedata_and_store

class CurrentSignalView(APIView):
    """Current trading signal API"""

    def get(self, request):
        symbol = request.GET.get("symbol", "BTCUSDT")
        timeframe = request.GET.get("tf", "15m")

        # টাইমফ্রেম ভ্যালিডেশন
        valid_timeframes = ['1m', '5m', '15m', '30m', '1h', '4h', '1d']
        if timeframe not in valid_timeframes:
            timeframe = '15m'

        # সিম্বল টাইপ ডিটেক্ট করুন
        symbol_type = self._get_symbol_type(symbol)
        
        if symbol_type == 'crypto':
            return self._handle_crypto(symbol, timeframe)
        elif symbol_type in ['forex', 'metals']:
            return self._handle_forex_metal(symbol, timeframe)
        else:
            return self._handle_fallback(symbol, timeframe)

    def _get_symbol_type(self, symbol):
        """সিম্বল টাইপ ডিটেক্ট করুন"""
        crypto_symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT']
        forex_symbols = ['EURUSD', 'GBPUSD', 'USDJPY', 'AUDUSD']
        metals_symbols = ['XAUUSD', 'XAGUSD']
        
        if symbol in crypto_symbols:
            return 'crypto'
        elif symbol in forex_symbols:
            return 'forex'
        elif symbol in metals_symbols:
            return 'metals'
        return 'unknown'

    def _handle_crypto(self, symbol, timeframe):
        """Binance থেকে ক্রিপ্টো ডেটা নিন"""
        qs = Candle.objects.filter(
            symbol=symbol,
            timeframe=timeframe
        ).order_by("-time")[:200]

        if not qs.exists():
            try:
                fetch_binance(symbol, timeframe)
                qs = Candle.objects.filter(
                    symbol=symbol,
                    timeframe=timeframe
                ).order_by("-time")[:200]
            except Exception as e:
                print(f"Binance fetch error: {e}")

        return self._analyze_candles(qs, symbol, timeframe)

    def _handle_forex_metal(self, symbol, timeframe):
        """TwelveData থেকে ফরেক্স/মেটাল ডেটা নিন"""
        
        qs = Candle.objects.filter(
            symbol=symbol,
            timeframe=timeframe
        ).order_by("-time")[:200]

        # যদি ডেটা না থাকে বা পুরানো হয় (১ ঘণ্টার বেশি)
        needs_fetch = False
        if not qs.exists():
            needs_fetch = True
        else:
            latest = qs.first()
            time_diff = timezone.now() - latest.time
            if time_diff.total_seconds() > 3600:  # ১ ঘণ্টা পুরানো
                needs_fetch = True

        if needs_fetch:
            try:
                count = fetch_twelvedata_and_store(symbol, timeframe)
                print(f"Fetched {count} new candles for {symbol}")
                
                qs = Candle.objects.filter(
                    symbol=symbol,
                    timeframe=timeframe
                ).order_by("-time")[:200]
            except Exception as e:
                print(f"Error fetching from TwelveData: {str(e)}")

        return self._analyze_candles(qs, symbol, timeframe)

    def _handle_fallback(self, symbol, timeframe):
        """কোনো ডেটা না পেলে ফallback ডেটা দিন"""
        # ডামি ক্যান্ডেল তৈরি করুন
        candles = []
        now = timezone.now()
        
        for i in range(100):
            time = now - timedelta(minutes=i*15)
            base_price = 100.0 if symbol == 'UNKNOWN' else 50000.0
            change = (random.random() - 0.5) * base_price * 0.02
            
            candles.append({
                'time': time,
                'open': base_price + change * 0.9,
                'high': base_price + change * 1.1,
                'low': base_price + change * 0.8,
                'close': base_price + change,
            })
        
        candles.reverse()
        
        try:
            engine = SMCSignalEngine(candles)
            result = engine.analyze()
            result["price"] = float(candles[-1]["close"])
        except:
            result = {
                "signal": "NEUTRAL",
                "structure": "Fallback Mode",
                "confidence": "50%",
                "price": float(candles[-1]["close"])
            }
        
        result["symbol"] = symbol
        result["timeframe"] = timeframe
        return Response(result)

    def _analyze_candles(self, qs, symbol, timeframe):
        """ক্যান্ডেল ডেটা অ্যানালাইসিস করুন"""
        if not qs.exists():
            return Response({
                "signal": "NO_DATA",
                "confidence": "0%",
                "price": "0.00",
                "structure": "No data available",
                "symbol": symbol,
                "timeframe": timeframe
            })

        candles = list(reversed(list(qs.values(
            "time", "open", "high", "low", "close"
        ))))

        try:
            engine = SMCSignalEngine(candles)
            result = engine.analyze()
            
            # নিশ্চিত করুন সব ফিল্ড আছে
            result["price"] = float(candles[-1]["close"])
            result["symbol"] = symbol
            result["timeframe"] = timeframe
            result["structure"] = result.get("structure", "Analyzing...")
            result["confidence"] = result.get("confidence", "75%")
            
        except Exception as e:
            print(f"SMC Engine Error: {e}")
            # ইঞ্জিন এরর হলে ফallback ডেটা দিন
            result = {
                "signal": "ANALYSIS_ERROR",
                "structure": "Pattern detection in progress",
                "confidence": "50%",
                "price": float(candles[-1]["close"]),
                "symbol": symbol,
                "timeframe": timeframe
            }
        
        return Response(result)