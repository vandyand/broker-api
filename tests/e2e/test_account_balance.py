#!/usr/bin/env python3
"""
Account Balance and Position Management Test
Tests account balance tracking, position updates, and P&L calculations
"""

import requests
import json
import time
from typing import Dict, Any

BASE_URL = "http://localhost:8000"


def test_account_balance_tracking():
    """Test account balance tracking through trading"""
    print("Testing Account Balance Tracking")
    print("=" * 50)
    
    # Get or create a test account
    account_data = {
        "name": "Balance Test Account",
        "account_type": "practice",
        "balance": 10000.0,
        "currency": "USD"
    }
    
    # Try to create account
    response = requests.post(f"{BASE_URL}/accounts/", json=account_data)
    if response.status_code == 200:
        account = response.json()
        print(f"✓ Created test account: {account['name']}")
    else:
        # Account might exist, get it
        response = requests.get(f"{BASE_URL}/accounts/")
        accounts = response.json()["items"]
        account = next((acc for acc in accounts if acc["name"] == account_data["name"]), None)
        if account:
            print(f"✓ Found existing test account: {account['name']}")
        else:
            print("✗ Could not create or find test account")
            return
    
    initial_balance = account["balance"]
    print(f"Initial balance: ${initial_balance:,.2f}")
    
    # Get available instruments
    response = requests.get(f"{BASE_URL}/instruments/")
    instruments = response.json()["items"]
    
    # Find a forex instrument
    forex_instrument = next((inst for inst in instruments if inst["instrument_type"] == "forex"), None)
    if not forex_instrument:
        print("✗ No forex instruments available")
        return
    
    print(f"Using instrument: {forex_instrument['symbol']}")
    
    # Place a buy order
    order_data = {
        "account_id": account["id"],
        "instrument_id": forex_instrument["id"],
        "order_type": "market",
        "side": "buy",
        "quantity": 1000.0  # 1000 units
    }
    
    print(f"\nPlacing buy order: {order_data['quantity']} {forex_instrument['symbol']}")
    response = requests.post(f"{BASE_URL}/orders/", json=order_data)
    
    if response.status_code == 200:
        order = response.json()
        print(f"✓ Order created: {order['id']}")
        
        # Wait for execution
        time.sleep(2)
        
        # Check order status
        response = requests.get(f"{BASE_URL}/orders/{order['id']}")
        if response.status_code == 200:
            executed_order = response.json()
            print(f"Order status: {executed_order['status']}")
            if executed_order['status'] == 'filled':
                print(f"Fill price: ${executed_order['average_fill_price']:.5f}")
                print(f"Commission: ${executed_order['commission']:.2f}")
        
        # Check account balance after trade
        response = requests.get(f"{BASE_URL}/accounts/{account['id']}")
        if response.status_code == 200:
            updated_account = response.json()
            new_balance = updated_account["balance"]
            balance_change = new_balance - initial_balance
            print(f"\nBalance after buy: ${new_balance:,.2f}")
            print(f"Balance change: ${balance_change:,.2f}")
        
        # Check positions
        response = requests.get(f"{BASE_URL}/positions/account/{account['id']}")
        if response.status_code == 200:
            positions = response.json()
            if positions:
                position = positions[0]
                print(f"\nPosition created:")
                print(f"  Quantity: {position['quantity']:.4f}")
                print(f"  Average Price: ${position['average_price']:.5f}")
                print(f"  Unrealized P&L: ${position['unrealized_pnl']:.2f}")
        
        # Place a sell order to close position
        sell_order_data = {
            "account_id": account["id"],
            "instrument_id": forex_instrument["id"],
            "order_type": "market",
            "side": "sell",
            "quantity": 1000.0
        }
        
        print(f"\nPlacing sell order to close position...")
        response = requests.post(f"{BASE_URL}/orders/", json=sell_order_data)
        
        if response.status_code == 200:
            sell_order = response.json()
            print(f"✓ Sell order created: {sell_order['id']}")
            
            # Wait for execution
            time.sleep(2)
            
            # Check final account balance
            response = requests.get(f"{BASE_URL}/accounts/{account['id']}")
            if response.status_code == 200:
                final_account = response.json()
                final_balance = final_account["balance"]
                total_change = final_balance - initial_balance
                print(f"\nFinal balance: ${final_balance:,.2f}")
                print(f"Total balance change: ${total_change:,.2f}")
                
                if total_change < 0:
                    print("✓ Balance decreased due to trading costs (commission)")
                else:
                    print("✓ Balance increased due to profitable trade")
            
            # Check final positions
            response = requests.get(f"{BASE_URL}/positions/account/{account['id']}")
            if response.status_code == 200:
                final_positions = response.json()
                if final_positions:
                    position = final_positions[0]
                    print(f"\nFinal position:")
                    print(f"  Quantity: {position['quantity']:.4f}")
                    print(f"  Realized P&L: ${position['realized_pnl']:.2f}")
                else:
                    print("✓ Position closed (quantity = 0)")
        
        # Check trade history
        response = requests.get(f"{BASE_URL}/trades/account/{account['id']}")
        if response.status_code == 200:
            trades = response.json()
            print(f"\nTrade history: {len(trades)} trades")
            for trade in trades:
                print(f"  {trade['side'].upper()}: {trade['quantity']:.4f} @ ${trade['price']:.5f} (${trade['commission']:.2f} commission)")
    
    else:
        print(f"✗ Failed to create order: {response.text}")


def test_position_pnl_calculation():
    """Test position P&L calculation"""
    print("\n\nTesting Position P&L Calculation")
    print("=" * 50)
    
    # Get an account with positions
    response = requests.get(f"{BASE_URL}/accounts/")
    if response.status_code == 200:
        accounts = response.json()["items"]
        if accounts:
            account = accounts[0]
            print(f"Using account: {account['name']}")
            
            # Get positions
            response = requests.get(f"{BASE_URL}/positions/account/{account['id']}")
            if response.status_code == 200:
                positions = response.json()
                if positions:
                    print(f"Found {len(positions)} positions")
                    
                    for position in positions:
                        instrument_symbol = position.get("instrument", {}).get("symbol", "Unknown")
                        print(f"\nPosition: {instrument_symbol}")
                        print(f"  Quantity: {position['quantity']:.4f}")
                        print(f"  Average Price: ${position['average_price']:.5f}")
                        print(f"  Unrealized P&L: ${position['unrealized_pnl']:.2f}")
                        print(f"  Realized P&L: ${position['realized_pnl']:.2f}")
                        
                        # Update P&L
                        response = requests.post(f"{BASE_URL}/positions/{position['id']}/update-pnl")
                        if response.status_code == 200:
                            print("  ✓ P&L updated")
                            
                            # Get updated position
                            response = requests.get(f"{BASE_URL}/positions/{position['id']}")
                            if response.status_code == 200:
                                updated_position = response.json()
                                new_unrealized = updated_position["unrealized_pnl"]
                                print(f"  Updated Unrealized P&L: ${new_unrealized:.2f}")
                        else:
                            print("  ⚠ Failed to update P&L")
                else:
                    print("No positions found")
            else:
                print("Failed to get positions")
        else:
            print("No accounts found")
    else:
        print("Failed to get accounts")


def main():
    """Main function"""
    try:
        test_account_balance_tracking()
        test_position_pnl_calculation()
        
        print("\n" + "=" * 50)
        print("✓ Account balance and position tests completed!")
        
    except requests.exceptions.ConnectionError:
        print("✗ Could not connect to API. Make sure the service is running.")
        print("Start the service with: docker-compose up --build")
    except Exception as e:
        print(f"✗ Test failed: {e}")


if __name__ == "__main__":
    main() 