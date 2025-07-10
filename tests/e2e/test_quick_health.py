#!/usr/bin/env python3
"""
Quick API Test Script
Tests basic API functionality to ensure everything is working
"""

import requests
import json

BASE_URL = "http://localhost:8000"


def test_basic_endpoints():
    """Test basic API endpoints"""
    print("Testing Basic API Endpoints")
    print("=" * 40)
    
    # Test health
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            print("✓ Health check passed")
        else:
            print(f"✗ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Health check error: {e}")
        return False
    
    # Test accounts
    try:
        response = requests.get(f"{BASE_URL}/accounts/")
        if response.status_code == 200:
            accounts = response.json()
            print(f"✓ Accounts endpoint: {len(accounts['items'])} accounts found")
        else:
            print(f"✗ Accounts endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"✗ Accounts endpoint error: {e}")
    
    # Test instruments
    try:
        response = requests.get(f"{BASE_URL}/instruments/")
        if response.status_code == 200:
            instruments = response.json()
            print(f"✓ Instruments endpoint: {len(instruments['items'])} instruments found")
            
            # Show some instruments
            for instrument in instruments['items'][:3]:
                print(f"  - {instrument['symbol']} ({instrument['instrument_type']})")
        else:
            print(f"✗ Instruments endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"✗ Instruments endpoint error: {e}")
    
    # Test orders
    try:
        response = requests.get(f"{BASE_URL}/orders/")
        if response.status_code == 200:
            orders = response.json()
            print(f"✓ Orders endpoint: {len(orders['items'])} orders found")
        else:
            print(f"✗ Orders endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"✗ Orders endpoint error: {e}")
    
    # Test positions
    try:
        response = requests.get(f"{BASE_URL}/positions/")
        if response.status_code == 200:
            positions = response.json()
            print(f"✓ Positions endpoint: {len(positions['items'])} positions found")
        else:
            print(f"✗ Positions endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"✗ Positions endpoint error: {e}")
    
    # Test trades
    try:
        response = requests.get(f"{BASE_URL}/trades/")
        if response.status_code == 200:
            trades = response.json()
            print(f"✓ Trades endpoint: {len(trades['items'])} trades found")
        else:
            print(f"✗ Trades endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"✗ Trades endpoint error: {e}")
    
    return True


def test_price_endpoints():
    """Test price endpoints"""
    print("\nTesting Price Endpoints")
    print("=" * 40)
    
    # Test forex price
    try:
        response = requests.get(f"{BASE_URL}/prices/EUR_USD")
        if response.status_code == 200:
            price_data = response.json()
            print(f"✓ EUR/USD price: {price_data['bid']:.5f} / {price_data['ask']:.5f}")
        else:
            print(f"⚠ EUR/USD price not available: {response.status_code}")
    except Exception as e:
        print(f"⚠ EUR/USD price error: {e}")
    
    # Test crypto price
    try:
        response = requests.get(f"{BASE_URL}/prices/BTC_USDT")
        if response.status_code == 200:
            price_data = response.json()
            print(f"✓ BTC/USDT price: {price_data['bid']:.2f} / {price_data['ask']:.2f}")
        else:
            print(f"⚠ BTC/USDT price not available: {response.status_code}")
    except Exception as e:
        print(f"⚠ BTC/USDT price error: {e}")


def main():
    """Main function"""
    print("Quick API Test")
    print("=" * 50)
    
    try:
        if test_basic_endpoints():
            test_price_endpoints()
            
            print("\n" + "=" * 50)
            print("✓ Quick test completed!")
            print(f"API Documentation: {BASE_URL}/docs")
        else:
            print("\n✗ Basic endpoints failed - API may not be running")
            print("Start the service with: docker-compose up --build")
            
    except requests.exceptions.ConnectionError:
        print("✗ Could not connect to API. Make sure the service is running.")
        print("Start the service with: docker-compose up --build")
    except Exception as e:
        print(f"✗ Test failed: {e}")


if __name__ == "__main__":
    main() 