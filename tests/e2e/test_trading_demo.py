#!/usr/bin/env python3
"""
Comprehensive Trading Demo Script
Tests the complete trading flow for both forex and crypto instruments
"""

import requests
import json
import time
from typing import Dict, Any, List
from datetime import datetime

BASE_URL = "http://localhost:8000"


class TradingDemo:
    def __init__(self):
        self.session = requests.Session()
        self.demo_accounts = {}
        self.instruments = {}
        self.orders = []
        self.positions = {}
    
    def log(self, message: str, level: str = "INFO"):
        """Log messages with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
    
    def test_health(self):
        """Test API health"""
        self.log("Testing API health...")
        response = self.session.get(f"{BASE_URL}/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        self.log("✓ API is healthy", "SUCCESS")
    
    def setup_demo_accounts(self):
        """Create demo accounts for testing"""
        self.log("Setting up demo accounts...")
        
        # Create demo accounts with different balances
        demo_accounts_data = [
            {
                "name": "Forex Demo Account",
                "account_type": "practice",
                "balance": 25000.0,
                "currency": "USD"
            },
            {
                "name": "Crypto Demo Account", 
                "account_type": "practice",
                "balance": 50000.0,
                "currency": "USD"
            }
        ]
        
        for account_data in demo_accounts_data:
            response = self.session.post(f"{BASE_URL}/accounts/", json=account_data)
            if response.status_code == 200:
                account = response.json()
                self.demo_accounts[account["name"]] = account
                self.log(f"✓ Created {account['name']} with ${account['balance']:,.2f}", "SUCCESS")
            else:
                # Account might already exist, try to get it
                response = self.session.get(f"{BASE_URL}/accounts/")
                if response.status_code == 200:
                    accounts = response.json()["items"]
                    for account in accounts:
                        if account["name"] == account_data["name"]:
                            self.demo_accounts[account["name"]] = account
                            self.log(f"✓ Found existing {account['name']} with ${account['balance']:,.2f}", "SUCCESS")
                            break
    
    def get_instruments(self):
        """Get available instruments"""
        self.log("Fetching available instruments...")
        response = self.session.get(f"{BASE_URL}/instruments/")
        assert response.status_code == 200
        instruments_data = response.json()
        
        # Organize instruments by type
        for instrument in instruments_data["items"]:
            instrument_type = instrument["instrument_type"]
            if instrument_type not in self.instruments:
                self.instruments[instrument_type] = []
            self.instruments[instrument_type].append(instrument)
        
        self.log(f"✓ Found {len(instruments_data['items'])} instruments", "SUCCESS")
        self.log(f"  - Forex: {len(self.instruments.get('forex', []))}", "INFO")
        self.log(f"  - Crypto: {len(self.instruments.get('crypto', []))}", "INFO")
    
    def test_price_fetching(self):
        """Test price fetching for different instruments"""
        self.log("Testing price fetching...")
        
        # Test forex prices
        forex_instruments = self.instruments.get("forex", [])
        if forex_instruments:
            symbol = forex_instruments[0]["symbol"]
            try:
                response = self.session.get(f"{BASE_URL}/prices/{symbol}")
                if response.status_code == 200:
                    price_data = response.json()
                    self.log(f"✓ {symbol}: {price_data['bid']:.5f} / {price_data['ask']:.5f}", "SUCCESS")
                else:
                    self.log(f"⚠ {symbol}: Price not available (check Oanda API credentials)", "WARNING")
            except Exception as e:
                self.log(f"⚠ {symbol}: Error fetching price - {e}", "WARNING")
        
        # Test crypto prices
        crypto_instruments = self.instruments.get("crypto", [])
        if crypto_instruments:
            symbol = crypto_instruments[0]["symbol"]
            try:
                response = self.session.get(f"{BASE_URL}/prices/{symbol}")
                if response.status_code == 200:
                    price_data = response.json()
                    self.log(f"✓ {symbol}: {price_data['bid']:.2f} / {price_data['ask']:.2f}", "SUCCESS")
                else:
                    self.log(f"⚠ {symbol}: Price not available (check Bitunix API credentials)", "WARNING")
            except Exception as e:
                self.log(f"⚠ {symbol}: Error fetching price - {e}", "WARNING")
    
    def place_forex_orders(self):
        """Place forex orders"""
        self.log("Placing forex orders...")
        
        forex_account = self.demo_accounts.get("Forex Demo Account")
        forex_instruments = self.instruments.get("forex", [])
        
        if not forex_account or not forex_instruments:
            self.log("⚠ No forex account or instruments available", "WARNING")
            return
        
        # Place a buy order for EUR/USD
        eur_usd = next((inst for inst in forex_instruments if inst["symbol"] == "EUR_USD"), None)
        if eur_usd:
            order_data = {
                "account_id": forex_account["id"],
                "instrument_id": eur_usd["id"],
                "order_type": "market",
                "side": "buy",
                "quantity": 10000.0  # 10k EUR
            }
            
            response = self.session.post(f"{BASE_URL}/orders/", json=order_data)
            if response.status_code == 200:
                order = response.json()
                self.orders.append(order)
                self.log(f"✓ Placed EUR/USD buy order: {order['quantity']} EUR", "SUCCESS")
            else:
                self.log(f"✗ Failed to place EUR/USD order: {response.text}", "ERROR")
        
        # Place a sell order for GBP/USD
        gbp_usd = next((inst for inst in forex_instruments if inst["symbol"] == "GBP_USD"), None)
        if gbp_usd:
            order_data = {
                "account_id": forex_account["id"],
                "instrument_id": gbp_usd["id"],
                "order_type": "market",
                "side": "sell",
                "quantity": 5000.0  # 5k GBP
            }
            
            response = self.session.post(f"{BASE_URL}/orders/", json=order_data)
            if response.status_code == 200:
                order = response.json()
                self.orders.append(order)
                self.log(f"✓ Placed GBP/USD sell order: {order['quantity']} GBP", "SUCCESS")
            else:
                self.log(f"✗ Failed to place GBP/USD order: {response.text}", "ERROR")
    
    def place_crypto_orders(self):
        """Place crypto orders"""
        self.log("Placing crypto orders...")
        
        crypto_account = self.demo_accounts.get("Crypto Demo Account")
        crypto_instruments = self.instruments.get("crypto", [])
        
        if not crypto_account or not crypto_instruments:
            self.log("⚠ No crypto account or instruments available", "WARNING")
            return
        
        # Place a buy order for BTC/USDT
        btc_usdt = next((inst for inst in crypto_instruments if inst["symbol"] == "BTC_USDT"), None)
        if btc_usdt:
            order_data = {
                "account_id": crypto_account["id"],
                "instrument_id": btc_usdt["id"],
                "order_type": "market",
                "side": "buy",
                "quantity": 0.5  # 0.5 BTC
            }
            
            response = self.session.post(f"{BASE_URL}/orders/", json=order_data)
            if response.status_code == 200:
                order = response.json()
                self.orders.append(order)
                self.log(f"✓ Placed BTC/USDT buy order: {order['quantity']} BTC", "SUCCESS")
            else:
                self.log(f"✗ Failed to place BTC/USDT order: {response.text}", "ERROR")
        
        # Place a sell order for ETH/USDT
        eth_usdt = next((inst for inst in crypto_instruments if inst["symbol"] == "ETH_USDT"), None)
        if eth_usdt:
            order_data = {
                "account_id": crypto_account["id"],
                "instrument_id": eth_usdt["id"],
                "order_type": "market",
                "side": "sell",
                "quantity": 2.0  # 2 ETH
            }
            
            response = self.session.post(f"{BASE_URL}/orders/", json=order_data)
            if response.status_code == 200:
                order = response.json()
                self.orders.append(order)
                self.log(f"✓ Placed ETH/USDT sell order: {order['quantity']} ETH", "SUCCESS")
            else:
                self.log(f"✗ Failed to place ETH/USDT order: {response.text}", "ERROR")
    
    def wait_for_order_execution(self):
        """Wait for orders to be executed"""
        self.log("Waiting for order execution...")
        time.sleep(3)  # Give time for background execution
        
        # Check order statuses
        for order in self.orders:
            response = self.session.get(f"{BASE_URL}/orders/{order['id']}")
            if response.status_code == 200:
                updated_order = response.json()
                status = updated_order["status"]
                if status == "filled":
                    self.log(f"✓ Order {order['id']}: {status} at ${updated_order['average_fill_price']:.5f}", "SUCCESS")
                else:
                    self.log(f"⚠ Order {order['id']}: {status}", "WARNING")
    
    def check_positions(self):
        """Check positions for all accounts"""
        self.log("Checking positions...")
        
        for account_name, account in self.demo_accounts.items():
            response = self.session.get(f"{BASE_URL}/positions/account/{account['id']}")
            if response.status_code == 200:
                positions = response.json()
                if positions:
                    self.log(f"✓ {account_name}: {len(positions)} positions", "SUCCESS")
                    for position in positions:
                        instrument_symbol = position.get("instrument", {}).get("symbol", "Unknown")
                        quantity = position["quantity"]
                        avg_price = position["average_price"]
                        unrealized_pnl = position["unrealized_pnl"]
                        realized_pnl = position["realized_pnl"]
                        
                        self.log(f"  - {instrument_symbol}: {quantity:.4f} @ ${avg_price:.5f}", "INFO")
                        self.log(f"    Unrealized P&L: ${unrealized_pnl:.2f}, Realized P&L: ${realized_pnl:.2f}", "INFO")
                else:
                    self.log(f"⚠ {account_name}: No positions", "WARNING")
    
    def update_position_pnl(self):
        """Update P&L for all positions"""
        self.log("Updating position P&L...")
        
        for account_name, account in self.demo_accounts.items():
            response = self.session.post(f"{BASE_URL}/positions/account/{account['id']}/update-all-pnl")
            if response.status_code == 200:
                self.log(f"✓ Updated P&L for {account_name}", "SUCCESS")
            else:
                self.log(f"⚠ Failed to update P&L for {account_name}", "WARNING")
    
    def check_account_balances(self):
        """Check account balances after trading"""
        self.log("Checking account balances...")
        
        for account_name, account in self.demo_accounts.items():
            response = self.session.get(f"{BASE_URL}/accounts/{account['id']}")
            if response.status_code == 200:
                updated_account = response.json()
                balance = updated_account["balance"]
                self.log(f"✓ {account_name}: ${balance:,.2f}", "SUCCESS")
    
    def check_trades(self):
        """Check trade history"""
        self.log("Checking trade history...")
        
        for account_name, account in self.demo_accounts.items():
            response = self.session.get(f"{BASE_URL}/trades/account/{account['id']}")
            if response.status_code == 200:
                trades = response.json()
                if trades:
                    self.log(f"✓ {account_name}: {len(trades)} trades", "SUCCESS")
                    for trade in trades[:3]:  # Show first 3 trades
                        instrument_symbol = trade.get("instrument", {}).get("symbol", "Unknown")
                        side = trade["side"]
                        quantity = trade["quantity"]
                        price = trade["price"]
                        commission = trade["commission"]
                        
                        self.log(f"  - {side.upper()} {quantity:.4f} {instrument_symbol} @ ${price:.5f} (${commission:.2f} commission)", "INFO")
                else:
                    self.log(f"⚠ {account_name}: No trades", "WARNING")
    
    def run_demo(self):
        """Run the complete trading demo"""
        self.log("Starting Comprehensive Trading Demo", "HEADER")
        self.log("=" * 60, "HEADER")
        
        try:
            # Test API health
            self.test_health()
            
            # Setup demo accounts
            self.setup_demo_accounts()
            
            # Get available instruments
            self.get_instruments()
            
            # Test price fetching
            self.test_price_fetching()
            
            # Place orders
            self.place_forex_orders()
            self.place_crypto_orders()
            
            # Wait for execution
            self.wait_for_order_execution()
            
            # Check results
            self.check_positions()
            self.update_position_pnl()
            self.check_account_balances()
            self.check_trades()
            
            self.log("=" * 60, "HEADER")
            self.log("✓ Trading Demo Completed Successfully!", "SUCCESS")
            self.log(f"API Documentation: {BASE_URL}/docs", "INFO")
            
        except requests.exceptions.ConnectionError:
            self.log("✗ Could not connect to API. Make sure the service is running.", "ERROR")
            self.log("Start the service with: docker-compose up --build", "INFO")
        except Exception as e:
            self.log(f"✗ Demo failed: {e}", "ERROR")


def main():
    """Main function"""
    demo = TradingDemo()
    demo.run_demo()


if __name__ == "__main__":
    main() 