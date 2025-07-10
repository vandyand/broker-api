#!/usr/bin/env python3
"""
Test script for OANDA API integration
"""

import asyncio
import os
import sys
from dotenv import load_dotenv

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from app.services.price_service import OandaClient, PriceService

async def test_oanda_client():
    """Test the OandaClient directly"""
    print("🔍 Testing OANDA Client...")
    
    # Load environment variables
    load_dotenv()
    
    # Get credentials from environment
    api_key = os.getenv('OANDA_DEMO_KEY')
    account_id = os.getenv('OANDA_DEMO_ACCOUNT_ID')
    base_url = "https://api-fxpractice.oanda.com/v3"
    
    if not api_key or not account_id:
        print("❌ OANDA credentials not found in environment")
        return
    
    print(f"✅ Using OANDA Demo Account: {account_id}")
    
    # Create client
    client = OandaClient(api_key=api_key, account_id=account_id, base_url=base_url)
    
    try:
        # Test pricing for EUR_USD
        print("\n📊 Testing EUR_USD pricing...")
        prices = await client.get_prices(["EUR_USD"])
        if prices and len(prices) > 0:
            price_info = prices[0]
            print("✅ EUR_USD pricing retrieved successfully")
            print(f"   Instrument: {price_info.get('instrument')}")
            print(f"   Bid: {price_info.get('bids', [{}])[0].get('price', 'N/A')}")
            print(f"   Ask: {price_info.get('asks', [{}])[0].get('price', 'N/A')}")
            print(f"   Time: {price_info.get('time', 'N/A')}")
        else:
            print("❌ Failed to get EUR_USD pricing")
        
        # Test multiple instruments
        print("\n📊 Testing multiple instruments...")
        instruments = ["EUR_USD", "USD_JPY", "GBP_USD"]
        prices = await client.get_prices(instruments)
        if prices:
            print(f"✅ Retrieved pricing for {len(prices)} instruments")
            for price in prices:
                instrument = price.get('instrument', 'Unknown')
                bid = price.get('bids', [{}])[0].get('price', 'N/A')
                ask = price.get('asks', [{}])[0].get('price', 'N/A')
                print(f"   {instrument}: Bid={bid}, Ask={ask}")
        else:
            print("❌ Failed to get multiple instrument pricing")
        
        # Test instruments endpoint
        print("\n📋 Testing instruments endpoint...")
        instruments_info = await client.get_instruments(["EUR_USD", "USD_JPY"])
        if instruments_info:
            print(f"✅ Retrieved info for {len(instruments_info)} instruments")
            for instrument in instruments_info:
                name = instrument.get('name', 'Unknown')
                display_name = instrument.get('displayName', 'Unknown')
                margin_rate = instrument.get('marginRate', 'N/A')
                print(f"   {name} ({display_name}): Margin Rate={margin_rate}")
        else:
            print("❌ Failed to get instruments info")
            
    except Exception as e:
        print(f"❌ Error testing OANDA client: {e}")
    finally:
        await client.close()

async def test_price_service():
    """Test the PriceService integration"""
    print("\n🔍 Testing PriceService Integration...")
    
    # Load environment variables
    load_dotenv()
    
    # Create price service
    price_service = PriceService()
    
    try:
        # Test forex price
        print("\n📊 Testing forex price via PriceService...")
        price_data = await price_service.get_forex_price("EUR_USD")
        if price_data:
            print("✅ EUR_USD price retrieved via PriceService")
            print(f"   Symbol: {price_data.symbol}")
            print(f"   Bid: {price_data.bid}")
            print(f"   Ask: {price_data.ask}")
            print(f"   Source: {price_data.source}")
            print(f"   Timestamp: {price_data.timestamp}")
        else:
            print("❌ Failed to get EUR_USD price via PriceService")
        
        # Test batch pricing
        print("\n📊 Testing batch pricing...")
        symbols = [
            {"symbol": "EUR_USD", "instrument_type": "forex"},
            {"symbol": "USD_JPY", "instrument_type": "forex"},
            {"symbol": "GBP_USD", "instrument_type": "forex"}
        ]
        prices = await price_service.get_prices_batch(symbols)
        if prices:
            print(f"✅ Retrieved {len(prices)} prices in batch")
            for price in prices:
                print(f"   {price.symbol}: Bid={price.bid}, Ask={price.ask}, Source={price.source}")
        else:
            print("❌ Failed to get batch prices")
            
    except Exception as e:
        print(f"❌ Error testing PriceService: {e}")
    finally:
        # Properly close the price service
        await price_service.close()

async def main():
    """Main test function"""
    print("🚀 Starting OANDA API Integration Tests")
    print("=" * 50)
    
    await test_oanda_client()
    await test_price_service()
    
    print("\n" + "=" * 50)
    print("✅ OANDA API Integration Tests Complete")

if __name__ == "__main__":
    asyncio.run(main()) 