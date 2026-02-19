import requests
from django.utils import timezone
from datetime import datetime
import pytz  # pytz ইম্পোর্ট করুন
from django.conf import settings
from ..models import Candle


class TwelveDataLoader:
    """TwelveData API থেকে ফরেক্স ও মেটাল ডেটা লোড করার ক্লাস"""
    
    BASE_URL = "https://api.twelvedata.com"
    
    def __init__(self):
        self.api_key = "59b64fd742aa4662b5c94ff01376d850"  # আপনার API কী
        
    def _format_symbol(self, symbol):
        """
        TwelveData API এর জন্য সিম্বল ফরম্যাট করুন
        """
        # ফরেক্স সিম্বল: EURUSD -> EUR/USD
        forex_pairs = ['EURUSD', 'GBPUSD', 'USDJPY', 'AUDUSD', 'USDCAD', 'USDCHF', 'NZDUSD']
        if symbol in forex_pairs:
            return symbol[:3] + '/' + symbol[3:]
        
        # মেটাল সিম্বল: XAUUSD -> XAU/USD, XAGUSD -> XAG/USD
        metal_pairs = ['XAUUSD', 'XAGUSD', 'XPTUSD', 'XPDUSD']
        if symbol in metal_pairs:
            return symbol[:3] + '/' + symbol[3:]
        
        # ক্রিপ্টো: BTCUSDT -> BTC/USDT, ETHUSDT -> ETH/USDT
        if symbol.endswith('USDT'):
            base = symbol.replace('USDT', '')
            return base + '/USDT'
        if symbol.endswith('USD'):
            base = symbol.replace('USD', '')
            return base + '/USD'
        
        return symbol
    
    def _make_aware(self, dt):
        """
        naive datetime কে timezone-aware করুন
        """
        if dt.tzinfo is None or dt.tzinfo.utcoffset(dt) is None:
            # UTC timezone তৈরি করার সঠিক উপায়
            return timezone.make_aware(dt, timezone=pytz.UTC)  # pytz.UTC ব্যবহার করুন
        return dt
    
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
        formatted_symbol = self._format_symbol(symbol)
        
        url = f"{self.BASE_URL}/time_series"
        params = {
            'symbol': formatted_symbol,
            'interval': interval,
            'apikey': self.api_key,
            'outputsize': outputsize,
            'format': 'JSON'
        }
        
        print(f"🔍 Fetching {formatted_symbol} ({symbol}) with interval {interval}")
        
        try:
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            
            # API error চেক করুন
            if 'status' in data and data['status'] == 'error':
                print(f"❌ API Error for {symbol}: {data.get('message', 'Unknown error')}")
                return None
            
            if 'values' not in data:
                print(f"⚠️ No values in response for {symbol}")
                return None
            
            print(f"✅ Successfully fetched {len(data['values'])} candles for {symbol}")
            return self._parse_response(data, symbol, timeframe)
            
        except requests.exceptions.Timeout:
            print(f"⏱️ Timeout fetching {symbol}")
            return None
        except requests.exceptions.RequestException as e:
            print(f"🌐 Network error fetching {symbol}: {str(e)}")
            return None
        except Exception as e:
            print(f"❌ Unexpected error fetching {symbol}: {str(e)}")
            return None
    
    def _parse_response(self, data, symbol, timeframe):
        """
        API রেসপন্স পার্স করে Candle মডেলের জন্য ডাটা তৈরি করুন
        """
        candles = []
        
        for item in data['values']:
            try:
                # ডেটাটাইম পার্স করুন
                if 'datetime' in item:
                    dt_str = item['datetime']
                    
                    try:
                        if ' ' in dt_str:
                            naive_dt = datetime.strptime(dt_str, '%Y-%m-%d %H:%M:%S')
                        else:
                            naive_dt = datetime.strptime(dt_str, '%Y-%m-%d')
                        
                        # timezone-aware করুন (সবসময় UTC)
                        aware_dt = self._make_aware(naive_dt)
                        
                    except ValueError as e:
                        print(f"⚠️ Date parsing error for {dt_str}: {e}")
                        aware_dt = timezone.now()
                else:
                    aware_dt = timezone.now()
                
                # ভলিউম হ্যান্ডেল করুন
                try:
                    volume = float(item.get('volume', 0)) if item.get('volume') else 0
                except (ValueError, TypeError):
                    volume = 0
                
                candle = {
                    'symbol': symbol,
                    'timeframe': timeframe,
                    'time': aware_dt,
                    'open': float(item['open']),
                    'high': float(item['high']),
                    'low': float(item['low']),
                    'close': float(item['close']),
                    'volume': volume
                }
                candles.append(candle)
                
            except KeyError as e:
                print(f"⚠️ Missing key in candle data: {e}")
                continue
            except ValueError as e:
                print(f"⚠️ Value error parsing candle: {e}")
                continue
            except Exception as e:
                print(f"⚠️ Unexpected error parsing candle: {e}")
                continue
        
        return candles
    
    def save_to_db(self, candles):
        """
        ডেটাবেসে ক্যান্ডেল সংরক্ষণ করুন
        """
        if not candles:
            return 0
            
        created_count = 0
        updated_count = 0
        
        for candle_data in candles:
            try:
                # নিশ্চিত করুন time timezone-aware আছে
                if candle_data['time'].tzinfo is None:
                    candle_data['time'] = self._make_aware(candle_data['time'])
                
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
                else:
                    updated_count += 1
                    
            except Exception as e:
                print(f"❌ Error saving candle: {e}")
                continue
        
        if created_count > 0 or updated_count > 0:
            print(f"💾 Database: {created_count} created, {updated_count} updated")
        
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
    """
    TwelveData থেকে ডেটা ফেচ করে ডেটাবেসে সংরক্ষণ করুন
    """
    loader = TwelveDataLoader()
    return loader.fetch_and_store(symbol, timeframe)


# টেস্ট ফাংশন
def test_twelvedata():
    """
    TwelveDataLoader টেস্ট করার জন্য ফাংশন
    """
    loader = TwelveDataLoader()
    
    test_symbols = ['EURUSD', 'XAUUSD', 'BTCUSDT']
    
    for symbol in test_symbols:
        print(f"\n{'='*50}")
        print(f"Testing {symbol}")
        print('='*50)
        
        candles = loader.fetch_data(symbol, '15m', outputsize=5)
        
        if candles:
            print(f"✅ Success! Got {len(candles)} candles")
            for i, candle in enumerate(candles):
                print(f"\nCandle {i+1}:")
                print(f"  Time: {candle['time']} (Timezone: {candle['time'].tzinfo})")
                print(f"  Open: {candle['open']}")
                print(f"  High: {candle['high']}")
                print(f"  Low: {candle['low']}")
                print(f"  Close: {candle['close']}")
                print(f"  Volume: {candle['volume']}")
        else:
            print(f"❌ Failed to fetch {symbol}")


if __name__ == "__main__":
    # টেস্ট করার জন্য
    test_twelvedata()