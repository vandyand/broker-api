#!/usr/bin/env python3
"""
Test with Real OANDA Credentials
"""

import asyncio
import os
import aiohttp
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


async def test_real_oanda():
    """Test OANDA API with real demo credentials"""
    print("🔍 Testing OANDA API with Real Demo Credentials")
    print("=" * 60)
    
    # Use the real demo credentials from the .env file
    api_key = "808b8c2978ded93c563bc420348788ab-00fba0cf47cf2456d8b4bfeb4c65c312"
    account_id = "101-001-12345678-001"  # This is a placeholder - we need to get the real account ID
    base_url = "https://api-fxpractice.oanda.com/v3"
    
    print(f"API Key: {api_key[:10]}...")
    print(f"Account ID: {account_id}")
    print(f"Base URL: {base_url}")
    print()
    
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    timeout = aiohttp.ClientTimeout(total=30)
    
    async with aiohttp.ClientSession(timeout=timeout) as session:
        try:
            # Test 1: Get accounts list first
            print("📊 Test 1: Getting accounts list...")
            url = f"{base_url}/accounts"
            async with session.get(url, headers=headers) as response:
                print(f"Status: {response.status}")
                if response.status == 200:
                    data = await response.json()
                    accounts = data.get('accounts', [])
                    print(f"✅ Found {len(accounts)} accounts")
                    
                    if accounts:
                        # Use the first account ID
                        real_account_id = accounts[0]['id']
                        print(f"Using account ID: {real_account_id}")
                        
                        # Test 2: Get instruments for this account
                        print("\n📋 Test 2: Getting instruments...")
                        url = f"{base_url}/accounts/{real_account_id}/instruments"
                        async with session.get(url, headers=headers) as response:
                            print(f"Status: {response.status}")
                            if response.status == 200:
                                data = await response.json()
                                instruments = data.get('instruments', [])
                                print(f"✅ Found {len(instruments)} instruments")
                                
                                if instruments:
                                    print("Sample instruments:")
                                    for instrument in instruments[:10]:
                                        name = instrument.get('name', 'Unknown')
                                        display_name = instrument.get('displayName', 'Unknown')
                                        print(f"   {name}: {display_name}")
                                    
                                    # Return the instruments for testing
                                    return instruments
                            else:
                                print(f"❌ Error: {await response.text()}")
                    else:
                        print("❌ No accounts found")
                else:
                    print(f"❌ Error: {await response.text()}")
            
        except Exception as e:
            print(f"❌ Exception: {e}")
            import traceback
            traceback.print_exc()
    
    return []


if __name__ == "__main__":
    instruments = asyncio.run(test_real_oanda())
    if instruments:
        print(f"\n🎯 Success! Found {len(instruments)} OANDA instruments")
        print("This means the OANDA API is working and we can sync forex instruments.")
    else:
        print("\n❌ Failed to get OANDA instruments") 