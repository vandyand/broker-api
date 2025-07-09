#!/usr/bin/env python3
"""
Simple test script to verify the Broker API functionality
"""

import requests
import json
import time
from typing import Dict, Any

BASE_URL = "http://localhost:8000"


def test_health():
    """Test health endpoint"""
    print("Testing health endpoint...")
    response = requests.get(f"{BASE_URL}/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    print("✓ Health check passed")


def test_accounts():
    """Test account operations"""
    print("\nTesting account operations...")
    
    # Create account
    account_data = {
        "name": "Test Account",
        "account_type": "practice",
        "balance": 5000.0,
        "currency": "USD"
    }
    
    response = requests.post(f"{BASE_URL}/accounts/", json=account_data)
    assert response.status_code == 200
    account = response.json()
    account_id = account["id"]
    print(f"✓ Created account with ID: {account_id}")
    
    # Get account
    response = requests.get(f"{BASE_URL}/accounts/{account_id}")
    assert response.status_code == 200
    retrieved_account = response.json()
    assert retrieved_account["name"] == account_data["name"]
    print("✓ Retrieved account successfully")
    
    return account_id


def test_instruments():
    """Test instrument operations"""
    print("\nTesting instrument operations...")
    
    # Get instruments
    response = requests.get(f"{BASE_URL}/instruments/")
    assert response.status_code == 200
    instruments = response.json()
    assert len(instruments["items"]) > 0
    print(f"✓ Found {len(instruments['items'])} instruments")
    
    # Get specific instrument
    instrument_id = instruments["items"][0]["id"]
    response = requests.get(f"{BASE_URL}/instruments/{instrument_id}")
    assert response.status_code == 200
    print("✓ Retrieved instrument successfully")
    
    return instrument_id


def test_orders(account_id: int, instrument_id: int):
    """Test order operations"""
    print("\nTesting order operations...")
    
    # Create market order
    order_data = {
        "account_id": account_id,
        "instrument_id": instrument_id,
        "order_type": "market",
        "side": "buy",
        "quantity": 100.0
    }
    
    response = requests.post(f"{BASE_URL}/orders/", json=order_data)
    assert response.status_code == 200
    order = response.json()
    order_id = order["id"]
    print(f"✓ Created order with ID: {order_id}")
    
    # Wait a moment for order execution
    time.sleep(2)
    
    # Get order
    response = requests.get(f"{BASE_URL}/orders/{order_id}")
    assert response.status_code == 200
    retrieved_order = response.json()
    print(f"✓ Order status: {retrieved_order['status']}")
    
    return order_id


def test_positions(account_id: int):
    """Test position operations"""
    print("\nTesting position operations...")
    
    # Get account positions
    response = requests.get(f"{BASE_URL}/positions/account/{account_id}")
    assert response.status_code == 200
    positions = response.json()
    print(f"✓ Found {len(positions)} positions for account")
    
    if positions:
        position_id = positions[0]["id"]
        print(f"✓ Position ID: {position_id}")
        
        # Update position P&L
        response = requests.post(f"{BASE_URL}/positions/{position_id}/update-pnl")
        assert response.status_code == 200
        print("✓ Updated position P&L")


def test_trades(account_id: int):
    """Test trade operations"""
    print("\nTesting trade operations...")
    
    # Get account trades
    response = requests.get(f"{BASE_URL}/trades/account/{account_id}")
    assert response.status_code == 200
    trades = response.json()
    print(f"✓ Found {len(trades)} trades for account")


def test_prices():
    """Test price operations"""
    print("\nTesting price operations...")
    
    # Get price for EUR_USD (should be available in sample data)
    try:
        response = requests.get(f"{BASE_URL}/prices/EUR_USD")
        if response.status_code == 200:
            price_data = response.json()
            print(f"✓ Got price for EUR_USD: {price_data['bid']} / {price_data['ask']}")
        else:
            print("⚠ Price not available (API credentials may be needed)")
    except Exception as e:
        print(f"⚠ Price service error: {e}")
    
    # Get price for BTC_USDT (crypto futures)
    try:
        response = requests.get(f"{BASE_URL}/prices/BTC_USDT")
        if response.status_code == 200:
            price_data = response.json()
            print(f"✓ Got price for BTC_USDT: {price_data['bid']} / {price_data['ask']}")
        else:
            print("⚠ Crypto price not available (Bitunix API credentials may be needed)")
    except Exception as e:
        print(f"⚠ Crypto price service error: {e}")


def main():
    """Run all tests"""
    print("Starting Broker API tests...")
    print("=" * 50)
    
    try:
        test_health()
        account_id = test_accounts()
        instrument_id = test_instruments()
        order_id = test_orders(account_id, instrument_id)
        test_positions(account_id)
        test_trades(account_id)
        test_prices()
        
        print("\n" + "=" * 50)
        print("✓ All tests passed successfully!")
        print(f"API is running at: {BASE_URL}")
        print(f"API documentation: {BASE_URL}/docs")
        
    except requests.exceptions.ConnectionError:
        print("✗ Could not connect to API. Make sure the service is running.")
        print("Start the service with: docker-compose up --build")
    except Exception as e:
        print(f"✗ Test failed: {e}")


if __name__ == "__main__":
    main() 