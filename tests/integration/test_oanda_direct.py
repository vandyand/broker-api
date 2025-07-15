#!/usr/bin/env python3
"""
Direct OANDA API Test
"""

import asyncio
import os
import aiohttp
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


async def test_oanda_direct():
    """Test OANDA API directly"""
    print("🔍 Direct OANDA API Test")
    print("=" * 50)
    
    api_key = os.getenv('OANDA_API_KEY')
    account_id = os.getenv('OANDA_ACCOUNT_ID')
    environment = os.getenv('OANDA_ENVIRONMENT', 'practice')
    
    print(f"API Key: {api_key[:10]}..." if api_key else "Not set")
    print(f"Account ID: {account_id}")
    print(f"Environment: {environment}")
    print()
    
    if not api_key or not account_id:
        print("❌ OANDA credentials not set")
        return
    
    # Set base URL
    base_url = "https://api-fxpractice.oanda.com/v3"
    if environment == "live":
        base_url = "https://api-fxtrade.oanda.com/v3"
    
    print(f"Base URL: {base_url}")
    print()
    
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    timeout = aiohttp.ClientTimeout(total=30)
    
    async with aiohttp.ClientSession(timeout=timeout) as session:
        try:
            # Test 1: Get account info
            print("📊 Test 1: Getting account info...")
            url = f"{base_url}/accounts/{account_id}"
            async with session.get(url, headers=headers) as response:
                print(f"Status: {response.status}")
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Account: {data.get('account', {}).get('name', 'Unknown')}")
                else:
                    print(f"❌ Error: {await response.text()}")
            print()
            
            # Test 2: Get instruments
            print("📋 Test 2: Getting instruments...")
            url = f"{base_url}/accounts/{account_id}/instruments"
            async with session.get(url, headers=headers) as response:
                print(f"Status: {response.status}")
                if response.status == 200:
                    data = await response.json()
                    instruments = data.get('instruments', [])
                    print(f"✅ Found {len(instruments)} instruments")
                    
                    if instruments:
                        print("Sample instruments:")
                        for instrument in instruments[:5]:
                            name = instrument.get('name', 'Unknown')
                            display_name = instrument.get('displayName', 'Unknown')
                            print(f"   {name}: {display_name}")
                else:
                    print(f"❌ Error: {await response.text()}")
            print()
            
            # Test 3: Get pricing for EUR_USD
            print("💰 Test 3: Getting EUR_USD pricing...")
            url = f"{base_url}/accounts/{account_id}/pricing"
            params = {'instruments': 'EUR_USD'}
            async with session.get(url, params=params, headers=headers) as response:
                print(f"Status: {response.status}")
                if response.status == 200:
                    data = await response.json()
                    prices = data.get('prices', [])
                    print(f"✅ Found {len(prices)} price(s)")
                    
                    if prices:
                        price = prices[0]
                        instrument = price.get('instrument', 'Unknown')
                        bids = price.get('bids', [])
                        asks = price.get('asks', [])
                        print(f"   Instrument: {instrument}")
                        if bids:
                            print(f"   Bid: {bids[0].get('price', 'N/A')}")
                        if asks:
                            print(f"   Ask: {asks[0].get('price', 'N/A')}")
                else:
                    print(f"❌ Error: {await response.text()}")
            
        except Exception as e:
            print(f"❌ Exception: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_oanda_direct()) 