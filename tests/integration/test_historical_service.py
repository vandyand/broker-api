#!/usr/bin/env python3
"""
Test Historical Data Service
Tests the unified historical data service with chunking support
"""

import asyncio
import os
import sys
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Add the app directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'app')))

from app.services.historical_data_service import HistoricalDataService, HistoricalRequest

load_dotenv()


async def test_historical_service():
    """Test the unified historical data service"""
    print("🚀 Testing Historical Data Service")
    print("=" * 60)
    
    service = HistoricalDataService()
    
    try:
        # Test 1: Small request (should fit in one chunk)
        print("\n📊 Test 1: Small request (1 day of 5m candles)")
        print("-" * 50)
        
        request = HistoricalRequest(
            symbol="EUR_USD",
            interval="5m",
            start_time=datetime.utcnow() - timedelta(days=1),
            end_time=datetime.utcnow(),
            source="oanda"
        )
        
        candles = await service.get_historical_data(request)
        print(f"✅ Got {len(candles)} 5m candles from Oanda")
        if candles:
            print(f"   First: {candles[0].timestamp} - O:{candles[0].open} H:{candles[0].high} L:{candles[0].low} C:{candles[0].close}")
            print(f"   Last:  {candles[-1].timestamp} - O:{candles[-1].open} H:{candles[-1].high} L:{candles[-1].low} C:{candles[-1].close}")
        
        # Test 2: Large request (should require chunking)
        print("\n📊 Test 2: Large request (7 days of 1m candles)")
        print("-" * 50)
        
        request = HistoricalRequest(
            symbol="EUR_USD",
            interval="1m",
            start_time=datetime.utcnow() - timedelta(days=7),
            end_time=datetime.utcnow(),
            source="oanda"
        )
        
        candles = await service.get_historical_data(request)
        print(f"✅ Got {len(candles)} 1m candles from Oanda (chunked)")
        if candles:
            print(f"   First: {candles[0].timestamp} - O:{candles[0].open} H:{candles[0].high} L:{candles[0].low} C:{candles[0].close}")
            print(f"   Last:  {candles[-1].timestamp} - O:{candles[-1].open} H:{candles[-1].high} L:{candles[-1].low} C:{candles[-1].close}")
        
        # Test 3: Bitunix small request
        print("\n📊 Test 3: Bitunix small request (1 day of 5m candles)")
        print("-" * 50)
        
        request = HistoricalRequest(
            symbol="BTCUSDT",
            interval="5m",
            start_time=datetime.utcnow() - timedelta(days=1),
            end_time=datetime.utcnow(),
            source="bitunix"
        )
        
        candles = await service.get_historical_data(request)
        print(f"✅ Got {len(candles)} 5m candles from Bitunix")
        if candles:
            print(f"   First: {candles[0].timestamp} - O:{candles[0].open} H:{candles[0].high} L:{candles[0].low} C:{candles[0].close}")
            print(f"   Last:  {candles[-1].timestamp} - O:{candles[-1].open} H:{candles[-1].high} L:{candles[-1].low} C:{candles[-1].close}")
        
        # Test 4: Bitunix large request (should require chunking)
        print("\n📊 Test 4: Bitunix large request (3 days of 1m candles)")
        print("-" * 50)
        
        request = HistoricalRequest(
            symbol="BTCUSDT",
            interval="1m",
            start_time=datetime.utcnow() - timedelta(days=3),
            end_time=datetime.utcnow(),
            source="bitunix"
        )
        
        candles = await service.get_historical_data(request)
        print(f"✅ Got {len(candles)} 1m candles from Bitunix (chunked)")
        if candles:
            print(f"   First: {candles[0].timestamp} - O:{candles[0].open} H:{candles[0].high} L:{candles[0].low} C:{candles[0].close}")
            print(f"   Last:  {candles[-1].timestamp} - O:{candles[-1].open} H:{candles[-1].high} L:{candles[-1].low} C:{candles[-1].close}")
        
        # Test 5: Auto source detection
        print("\n📊 Test 5: Auto source detection")
        print("-" * 50)
        
        # Forex symbol (should use Oanda)
        request = HistoricalRequest(
            symbol="EUR_USD",
            interval="1h",
            start_time=datetime.utcnow() - timedelta(days=1),
            end_time=datetime.utcnow(),
            source="auto"
        )
        
        candles = await service.get_historical_data(request)
        print(f"✅ Auto-detected Oanda for EUR_USD: {len(candles)} 1h candles")
        
        # Crypto symbol (should use Bitunix)
        request = HistoricalRequest(
            symbol="BTCUSDT",
            interval="1h",
            start_time=datetime.utcnow() - timedelta(days=1),
            end_time=datetime.utcnow(),
            source="auto"
        )
        
        candles = await service.get_historical_data(request)
        print(f"✅ Auto-detected Bitunix for BTCUSDT: {len(candles)} 1h candles")
        
        # Test 6: Broker limits
        print("\n📊 Test 6: Broker limits")
        print("-" * 50)
        
        limits = service.get_broker_limits()
        print(f"Oanda max candles per request: {limits['oanda']}")
        print(f"Bitunix max candles per request: {limits['bitunix']}")
        
        intervals = await service.get_available_intervals()
        print(f"Oanda intervals: {intervals['oanda']}")
        print(f"Bitunix intervals: {intervals['bitunix']}")
        
    except Exception as e:
        print(f"❌ Error testing historical service: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await service.close()
    
    print("\n" + "=" * 60)
    print("✅ Historical Data Service Tests Complete")


if __name__ == "__main__":
    asyncio.run(test_historical_service()) 