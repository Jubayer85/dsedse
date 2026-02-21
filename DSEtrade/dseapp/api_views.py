from rest_framework.views import APIView
from rest_framework.response import Response
from django.utils import timezone
import random
from datetime import datetime, timedelta

# পুরানো SMCSignalEngine এর পরিবর্তে ProfessionalSMCEngine ইম্পোর্ট করুন
from dseapp.signals.smc_engine import ProfessionalSMCEngine
from dseapp.models import Candle
from dseapp.services.binance_loader import fetch_and_store as fetch_binance
from dseapp.services.twelvedata_loader import fetch_twelvedata_and_store

class CurrentSignalView(APIView):
    """Current trading signal API using Professional SMC Engine"""

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

    def _get_candles(self, symbol, timeframe, count=200):
        """ডাটাবেস থেকে ক্যান্ডেল ডেটা নিন"""
        qs = Candle.objects.filter(
            symbol=symbol,
            timeframe=timeframe
        ).order_by("-time")[:count]
        
        if not qs.exists():
            return None
            
        candles = list(reversed(list(qs.values(
            "time", "open", "high", "low", "close", "volume"
        ))))
        
        return candles

    def _handle_crypto(self, symbol, timeframe):
        """Binance থেকে ক্রিপ্টো ডেটা নিন"""
        candles = self._get_candles(symbol, timeframe)
        
        if not candles:
            try:
                fetch_binance(symbol, timeframe)
                candles = self._get_candles(symbol, timeframe)
            except Exception as e:
                print(f"Binance fetch error: {e}")
        
        return self._analyze_with_engine(candles, symbol, timeframe)

    def _handle_forex_metal(self, symbol, timeframe):
        """TwelveData থেকে ফরেক্স/মেটাল ডেটা নিন"""
        candles = self._get_candles(symbol, timeframe)
        
        if not candles:
            try:
                fetch_twelvedata_and_store(symbol, timeframe)
                candles = self._get_candles(symbol, timeframe)
            except Exception as e:
                print(f"TwelveData fetch error: {e}")
        
        return self._analyze_with_engine(candles, symbol, timeframe)

    def _handle_fallback(self, symbol, timeframe):
        """কোনো ডেটা না পেলে ফallback ডেটা দিন"""
        # ডামি ক্যান্ডেল তৈরি করুন
        candles = self._create_dummy_candles(symbol)
        
        if candles:
            return self._analyze_with_engine(candles, symbol, timeframe)
        
        return Response({
            "signal": "NO_DATA",
            "confidence": 0,
            "price": 0,
            "structure": "No data available",
            "symbol": symbol,
            "timeframe": timeframe
        })

    def _create_dummy_candles(self, symbol):
        """ডামি ক্যান্ডেল ডেটা তৈরি করুন"""
        candles = []
        now = timezone.now()
        base_price = {
            'EURUSD': 1.0875,
            'XAUUSD': 1952.30,
            'XAGUSD': 23.45,
            'BTCUSDT': 51250.00,
        }.get(symbol, 100.00)
        
        for i in range(100):
            time = now - timedelta(minutes=i*15)
            change = (random.random() - 0.5) * base_price * 0.02
            price = base_price + change
            
            candles.append({
                'time': time,
                'open': price * 0.999,
                'high': price * 1.002,
                'low': price * 0.998,
                'close': price,
                'volume': random.randint(1000, 10000)
            })
        
        candles.reverse()
        return candles

    def _analyze_with_engine(self, candles, symbol, timeframe):
        """Professional SMC Engine দিয়ে অ্যানালাইসিস করুন"""
        if not candles or len(candles) < 20:
            return Response({
                "signal": "INSUFFICIENT_DATA",
                "confidence": 0,
                "price": candles[-1]['close'] if candles else 0,
                "structure": "Insufficient data",
                "symbol": symbol,
                "timeframe": timeframe
            })
        
        try:
            # Professional SMC Engine ব্যবহার করুন
            # Note: Professional engine requires 3 timeframes
            # For now, we'll use the same candles for all timeframes
            engine = ProfessionalSMCEngine(
                candles_htf=candles,  # HTF as same candles
                candles_mtf=candles,  # MTF as same candles
                candles_ltf=candles,  # LTF as same candles
                account_balance=10000,
                risk_percent=1.0
            )
            
            result = engine.analyze()
            
            response_data = {
                "signal": result.signal,
                "structure": result.structure,
                "confidence": result.confidence,
                "price": result.entry_price,
                "symbol": symbol,
                "timeframe": timeframe,
                "stop_loss": result.stop_loss,
                "take_profit_1": result.take_profit_1,
                "take_profit_2": result.take_profit_2,
                "take_profit_3": result.take_profit_3,
                "risk_reward": result.risk_reward_ratio
            }
            
        except Exception as e:
            print(f"SMC Engine Error: {e}")
            # Fallback to simple analysis
            response_data = {
                "signal": "ANALYSIS_ERROR",
                "structure": "Analysis in progress",
                "confidence": 50,
                "price": candles[-1]['close'],
                "symbol": symbol,
                "timeframe": timeframe
            }
        
        return Response(response_data)