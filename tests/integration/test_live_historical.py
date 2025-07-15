#!/usr/bin/env python3
"""
Test Live Historical Data Endpoints
Tests the historical data API endpoints on the running server
"""

import requests
import json
from datetime import datetime, timedelta

BASE_URL = "http://localhost:23456"

def test_basic_endpoints():
    """Test basic API endpoints"""
    print("🔍 Testing Basic API Endpoints")
    print("=" * 50)
    
    # Test health endpoint
    response = requests.get(f"{BASE_URL}/health")
    print(f"Health: {response.status_code} - {response.json()}")
    
    # Test root endpoint
    response = requests.get(f"{BASE_URL}/")
    print(f"Root: {response.status_code} - {response.json()}")
    
    # Test API info
    response = requests.get(f"{BASE_URL}/api/v1")
    print(f"API Info: {response.status_code} - {response.json()}")

def test_historical_endpoints():
    """Test historical data endpoints"""
    print("\n📊 Testing Historical Data Endpoints")
    print("=" * 50)
    
    # Test intervals
    response = requests.get(f"{BASE_URL}/historical/intervals")
    print(f"Intervals: {response.status_code} - {response.json()}")
    
    # Test limits
    response = requests.get(f"{BASE_URL}/historical/limits")
    print(f"Limits: {response.status_code} - {response.json()}")
    
    # Test cache stats
    response = requests.get(f"{BASE_URL}/historical/stats")
    print(f"Cache Stats: {response.status_code} - {response.json()}")
    
    # Test gaps (should be empty initially)
    response = requests.get(f"{BASE_URL}/historical/gaps")
    print(f"Gaps: {response.status_code} - {response.json()}")

def test_instruments():
    """Test instruments endpoint"""
    print("\n🎯 Testing Instruments")
    print("=" * 50)
    
    response = requests.get(f"{BASE_URL}/instruments/")
    if response.status_code == 200:
        data = response.json()
        print(f"Instruments: {response.status_code} - Found {len(data['items'])} instruments")
        for instrument in data['items']:
            print(f"  - {instrument['symbol']} ({instrument['instrument_type']})")
    else:
        print(f"Instruments: {response.status_code} - {response.text}")

def test_historical_candles_without_credentials():
    """Test historical candles without API credentials (should fail gracefully)"""
    print("\n📈 Testing Historical Candles (without credentials)")
    print("=" * 50)
    
    # Test OANDA endpoint
    params = {
        "symbol": "EUR_USD",
        "interval": "5m",
        "max_candles": 5
    }
    response = requests.get(f"{BASE_URL}/historical/candles", params=params)
    print(f"OANDA EUR_USD 5m: {response.status_code} - {response.json()}")
    
    # Test Bitunix endpoint
    params = {
        "symbol": "BTCUSDT",
        "interval": "5m",
        "max_candles": 5
    }
    response = requests.get(f"{BASE_URL}/historical/candles", params=params)
    print(f"Bitunix BTCUSDT 5m: {response.status_code} - {response.json()}")

def main():
    """Main test function"""
    print("🚀 Testing Live Broker API Server")
    print("=" * 60)
    
    try:
        test_basic_endpoints()
        test_historical_endpoints()
        test_instruments()
        test_historical_candles_without_credentials()
        
        print("\n" + "=" * 60)
        print("✅ Live API Tests Complete")
        print(f"📖 API Documentation: {BASE_URL}/docs")
        print(f"🔍 Alternative Docs: {BASE_URL}/redoc")
        
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to server. Make sure it's running on port 23456")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main() 