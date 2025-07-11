#!/usr/bin/env python3
"""
Test Historical Data APIs
Tests Oanda and Bitunix historical data endpoints
"""

import asyncio
import aiohttp
import os
import sys
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Add the app directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'app')))

from app.services.price_service import OandaClient, BitunixClient

load_dotenv()


async def test_oanda_historical():
    """Test Oanda historical data API"""
    print("🔍 Testing Oanda Historical Data API")
    print("=" * 50)
    
    # Get credentials
    api_key = os.getenv('OANDA_API_KEY')
    account_id = os.getenv('OANDA_ACCOUNT_ID')
    
    if not api_key or not account_id:
        print("❌ Oanda credentials not found")
        return
    
    base_url = "https://api-fxpractice.oanda.com/v3"
    client = OandaClient(api_key=api_key, account_id=account_id, base_url=base_url)
    
    try:
        # Test different granularities
        granularities = ["M1", "M5", "M15", "M30", "H1", "H4", "D"]
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(days=7)
        
        for granularity in granularities:
            print(f"\n📊 Testing {granularity} candles for EUR_USD...")
            
            url = f"{base_url}/instruments/EUR_USD/candles"
            params = {
                'price': 'M',  # Midpoint
                'granularity': granularity,
                'from': start_time.isoformat() + 'Z',
                'to': end_time.isoformat() + 'Z'
                # Removed 'count' parameter as it conflicts with 'from' and 'to'
            }
            
            headers = {
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        candles = data.get('candles', [])
                        print(f"✅ Got {len(candles)} {granularity} candles")
                        
                        if candles:
                            # Show first and last candle
                            first = candles[0]
                            last = candles[-1]
                            print(f"   First: {first['time']} - O:{first['mid']['o']} H:{first['mid']['h']} L:{first['mid']['l']} C:{first['mid']['c']}")
                            print(f"   Last:  {last['time']} - O:{last['mid']['o']} H:{last['mid']['h']} L:{last['mid']['l']} C:{last['mid']['c']}")
                    else:
                        print(f"❌ Failed to get {granularity} candles: {response.status}")
                        error_text = await response.text()
                        print(f"   Error: {error_text}")
        
    except Exception as e:
        print(f"❌ Error testing Oanda historical data: {e}")
    finally:
        await client.close()


async def test_bitunix_historical():
    """Test Bitunix historical data API"""
    print("\n🔍 Testing Bitunix Historical Data API")
    print("=" * 50)
    
    # Get credentials
    api_key = os.getenv('BITUNIX_API_KEY')
    secret_key = os.getenv('BITUNIX_SECRET_KEY')
    
    if not api_key or not secret_key:
        print("❌ Bitunix credentials not found")
        return
    
    base_url = "https://fapi.bitunix.com"
    
    try:
        # Test different intervals - Bitunix uses string format like 1m, 5m, 15m, 30m, 1h, 4h, 1d
        intervals = ["1m", "5m", "15m", "30m", "1h", "4h", "1d"]
        end_time = int(datetime.utcnow().timestamp() * 1000)
        start_time = int((datetime.utcnow() - timedelta(days=7)).timestamp() * 1000)
        
        for interval in intervals:
            print(f"\n📊 Testing {interval} candles for BTCUSDT...")
            
            # Use the correct endpoint from Bitunix API documentation
            url = f"{base_url}/api/v1/futures/market/kline"
            params = {
                'symbol': 'BTCUSDT',
                'interval': interval,
                'startTime': start_time,
                'endTime': end_time,
                'limit': 100,
                'type': 'LAST_PRICE'  # Optional: LAST_PRICE or MARK_PRICE
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('code') == 0:
                            klines = data.get('data', [])
                            print(f"✅ Got {len(klines)} {interval} candles")
                            
                            if klines:
                                # Show first and last candle
                                first = klines[0]
                                last = klines[-1]
                                # Handle time field - could be string or number
                                first_time = first['time']
                                last_time = last['time']
                                if isinstance(first_time, str):
                                    first_time = int(first_time)
                                if isinstance(last_time, str):
                                    last_time = int(last_time)
                                
                                print(f"   First: {datetime.fromtimestamp(first_time/1000)} - O:{first['open']} H:{first['high']} L:{first['low']} C:{first['close']}")
                                print(f"   Last:  {datetime.fromtimestamp(last_time/1000)} - O:{last['open']} H:{last['high']} L:{last['low']} C:{last['close']}")
                        else:
                            print(f"❌ API error: {data.get('msg', 'Unknown error')}")
                    else:
                        print(f"❌ Failed to get {interval} candles: {response.status}")
                        error_text = await response.text()
                        print(f"   Error: {error_text}")
        
    except Exception as e:
        print(f"❌ Error testing Bitunix historical data: {e}")


async def main():
    """Main test function"""
    print("🚀 Testing Historical Data APIs")
    print("=" * 60)
    
    await test_oanda_historical()
    await test_bitunix_historical()
    
    print("\n" + "=" * 60)
    print("✅ Historical Data API Tests Complete")


if __name__ == "__main__":
    asyncio.run(main()) 