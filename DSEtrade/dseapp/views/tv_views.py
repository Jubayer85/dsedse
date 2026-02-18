from rest_framework.views import APIView
from rest_framework.response import Response
from dseapp.services.twelvedata_loader import TwelveDataLoader
from datetime import datetime
import random

class TVSymbolInfoView(APIView):
    """TradingView এর জন্য Symbol তথ্য প্রদান"""
    
    def get(self, request):
        symbol = request.GET.get('symbol', 'BTCUSDT')
        
        symbol_info = {
            'symbol': symbol,
            'full_name': symbol,
            'description': self._get_description(symbol),
            'type': self._get_type(symbol),
            'pricescale': self._get_pricescale(symbol),
            'timezone': 'Asia/Dhaka',
            'session': '24x7',
            'has_intraday': True,
            'has_daily': True,
            'has_weekly_and_monthly': True,
            'supported_resolutions': ['1', '5', '15', '30', '60', '240', 'D'],
            'volume_precision': 2,
        }
        
        return Response(symbol_info)
    
    def _get_type(self, symbol):
        if symbol in ['BTCUSDT', 'ETHUSDT', 'BNBUSDT']:
            return 'crypto'
        elif symbol.startswith(('XAU', 'XAG')):
            return 'metal'
        elif symbol.startswith(('EUR', 'GBP', 'JPY', 'AUD')):
            return 'forex'
        return 'stock'
    
    def _get_description(self, symbol):
        descriptions = {
            'BTCUSDT': 'Bitcoin / Tether',
            'ETHUSDT': 'Ethereum / Tether',
            'EURUSD': 'Euro / US Dollar',
            'XAUUSD': 'Gold / US Dollar',
            'XAGUSD': 'Silver / US Dollar',
        }
        return descriptions.get(symbol, symbol)
    
    def _get_pricescale(self, symbol):
        if symbol == 'BTCUSDT':
            return 100  # 2 decimal places
        elif symbol == 'XAUUSD':
            return 100  # 2 decimal places
        elif symbol == 'XAGUSD':
            return 1000  # 3 decimal places
        elif symbol == 'EURUSD':
            return 100000  # 5 decimal places
        return 100


class TVHistoryView(APIView):
    """TradingView এর জন্য Historical Candle Data"""
    
    def get(self, request):
        symbol = request.GET.get('symbol')
        resolution = request.GET.get('resolution')  # '1', '5', '15', '60', 'D'
        
        if not symbol:
            return Response({'s': 'error', 'errmsg': 'Symbol is required'})
        
        # TwelveData থেকে ডেটা আনার চেষ্টা করুন
        loader = TwelveDataLoader()
        timeframe = self._resolution_to_timeframe(resolution)
        
        print(f"📊 Fetching {symbol} {timeframe} data...")
        
        try:
            candles = loader.fetch_data(symbol, timeframe, outputsize=200)
            
            if candles and len(candles) > 10:
                return self._format_response(candles)
            else:
                # ডেটা না পেলে ডামি ডেটা দিন
                return self._get_dummy_data(symbol, resolution)
                
        except Exception as e:
            print(f"Error: {e}")
            return self._get_dummy_data(symbol, resolution)
    
    def _resolution_to_timeframe(self, resolution):
        mapping = {
            '1': '1m',
            '5': '5m',
            '15': '15m',
            '30': '30m',
            '60': '1h',
            '240': '4h',
            'D': '1d',
            'W': '1w',
        }
        return mapping.get(resolution, '15m')
    
    def _format_response(self, candles):
        """ক্যান্ডেল ডেটা TradingView ফরম্যাটে পাঠান"""
        response_data = {
            's': 'ok',
            't': [int(c['time'].timestamp()) for c in candles],
            'o': [c['open'] for c in candles],
            'h': [c['high'] for c in candles],
            'l': [c['low'] for c in candles],
            'c': [c['close'] for c in candles],
            'v': [c.get('volume', 0) for c in candles]
        }
        return Response(response_data)
    
    def _get_dummy_data(self, symbol, resolution):
        """API কাজ না করলে ডামি ডেটা দিন"""
        from datetime import datetime, timedelta
        
        base_price = {
            'EURUSD': 1.0875,
            'XAUUSD': 1952.30,
            'XAGUSD': 23.45,
            'BTCUSDT': 51250.00,
        }.get(symbol, 100.00)
        
        now = datetime.now()
        candles = []
        
        # 100টি ডামি ক্যান্ডেল তৈরি করুন
        for i in range(100):
            t = now - timedelta(minutes=i*15)
            change = (random.random() - 0.5) * base_price * 0.02
            price = base_price + change
            
            candles.append({
                'time': t,
                'open': price * 0.999,
                'high': price * 1.002,
                'low': price * 0.998,
                'close': price,
                'volume': random.randint(1000, 10000)
            })
        
        candles.reverse()
        
        response_data = {
            's': 'ok',
            't': [int(c['time'].timestamp()) for c in candles],
            'o': [c['open'] for c in candles],
            'h': [c['high'] for c in candles],
            'l': [c['low'] for c in candles],
            'c': [c['close'] for c in candles],
            'v': [c['volume'] for c in candles]
        }
        
        return Response(response_data)