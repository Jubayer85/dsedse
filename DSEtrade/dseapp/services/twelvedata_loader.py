import requests
from datetime import datetime
from django.conf import settings
from ..models import Candle

class TwelveDataLoader:
    """TwelveData API থেকে ফরেক্স ও মেটাল ডেটা লোড করার ক্লাস"""
    
    BASE_URL = "https://api.twelvedata.com"
    
    def __init__(self):
        self.api_key = "59b64fd742aa4662b5c94ff01376d850"  # আপনার API কী এখানে সেট করুন
        
    def fetch_data(self, symbol, timeframe, outputsize=200):
        """
        TwelveData থেকে ডেটা ফেচ করুন
        """
        # টাইমফ্রেম কনভার্ট করুন
        tf_map = {
            '1m': '1min',
            '5m': '5min',
            '15m': '15min',
            '30m': '30min',
            '1h': '1h',
            '4h': '4h',
            '1d': '1day'
        }
        
        interval = tf_map.get(timeframe, '15min')
        
        url = f"{self.BASE_URL}/time_series"
        params = {
            'symbol': symbol,
            'interval': interval,
            'apikey': self.api_key,
            'outputsize': outputsize,
            'format': 'JSON'
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            
            if 'values' not in data:
                print(f"API Error for {symbol}: {data.get('message', 'Unknown error')}")
                return None
                
            return self._parse_response(data, symbol, timeframe)
            
        except Exception as e:
            print(f"Error fetching {symbol}: {str(e)}")
            return None
    
    def _parse_response(self, data, symbol, timeframe):
        """
        API রেসপন্স পার্স করে Candle মডেলের জন্য ডাটা তৈরি করুন
        """
        candles = []
        
        for item in data['values']:
            # ডেটাটাইম পার্স করুন
            if 'datetime' in item:
                dt_str = item['datetime']
                # বিভিন্ন ফরম্যাট হ্যান্ডেল করুন
                try:
                    if ' ' in dt_str:
                        dt = datetime.strptime(dt_str, '%Y-%m-%d %H:%M:%S')
                    else:
                        dt = datetime.strptime(dt_str, '%Y-%m-%d')
                except:
                    dt = datetime.now()
            else:
                dt = datetime.now()
            
            candle = {
                'symbol': symbol,
                'timeframe': timeframe,
                'time': dt,
                'open': float(item['open']),
                'high': float(item['high']),
                'low': float(item['low']),
                'close': float(item['close']),
                'volume': float(item.get('volume', 0))
            }
            candles.append(candle)
        
        return candles
    
    def save_to_db(self, candles):
        """
        ডেটাবেসে ক্যান্ডেল সংরক্ষণ করুন
        """
        if not candles:
            return 0
            
        created_count = 0
        for candle_data in candles:
            obj, created = Candle.objects.update_or_create(
                symbol=candle_data['symbol'],
                timeframe=candle_data['timeframe'],
                time=candle_data['time'],
                defaults={
                    'open': candle_data['open'],
                    'high': candle_data['high'],
                    'low': candle_data['low'],
                    'close': candle_data['close'],
                    'volume': candle_data.get('volume', 0)
                }
            )
            if created:
                created_count += 1
        
        return created_count
    
    def fetch_and_store(self, symbol, timeframe):
        """
        ডেটা ফেচ করে ডেটাবেসে সংরক্ষণ করুন
        """
        candles = self.fetch_data(symbol, timeframe)
        if candles:
            return self.save_to_db(candles)
        return 0

# সুবিধার জন্য ফাংশন তৈরি করুন
def fetch_twelvedata_and_store(symbol, timeframe):
    loader = TwelveDataLoader()
    return loader.fetch_and_store(symbol, timeframe)