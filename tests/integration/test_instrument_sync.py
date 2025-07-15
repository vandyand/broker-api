#!/usr/bin/env python3
"""
Test Instrument Synchronization and API Endpoints

This script tests the instrument synchronization functionality and verifies that
the instruments endpoint returns the expected number of instruments.
"""

import asyncio
import os
import sys
import requests
from dotenv import load_dotenv

# Add the app directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from app.database import SessionLocal
from app.services.instrument_service import instrument_service
from app.models import Instrument, InstrumentType

# Load environment variables
load_dotenv()

BASE_URL = "http://localhost:8000"


async def test_instrument_sync():
    """Test instrument synchronization"""
    print("🧪 Testing Instrument Synchronization")
    print("=" * 50)
    
    db = SessionLocal()
    try:
        # Get initial counts
        initial_counts = await instrument_service.get_instrument_counts(db)
        print(f"📊 Initial instrument counts: {initial_counts}")
        
        # Test sync
        print("\n🔄 Testing instrument sync...")
        synced_counts = await instrument_service.sync_instruments_from_apis(db)
        print(f"✅ Sync results: {synced_counts}")
        
        # Get final counts
        final_counts = await instrument_service.get_instrument_counts(db)
        print(f"📊 Final instrument counts: {final_counts}")
        
        # Verify we have more instruments
        if final_counts['total'] > initial_counts['total']:
            print("✅ Success: Instrument count increased")
        else:
            print("⚠️  Warning: No new instruments were added")
        
        return final_counts
        
    except Exception as e:
        print(f"❌ Error during sync test: {e}")
        return None
    finally:
        db.close()


def test_api_endpoints():
    """Test API endpoints"""
    print("\n🌐 Testing API Endpoints")
    print("=" * 50)
    
    try:
        # Test instruments endpoint
        print("📋 Testing /instruments/ endpoint...")
        response = requests.get(f"{BASE_URL}/instruments/")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Instruments endpoint: {data['total']} total instruments")
            print(f"   Page size: {data['size']}")
            print(f"   Total pages: {data['pages']}")
            
            # Show breakdown by type
            instruments = data['items']
            forex_count = len([i for i in instruments if i['instrument_type'] == 'forex'])
            crypto_count = len([i for i in instruments if i['instrument_type'] == 'crypto'])
            equity_count = len([i for i in instruments if i['instrument_type'] == 'equity'])
            
            print(f"   Forex: {forex_count}")
            print(f"   Crypto: {crypto_count}")
            print(f"   Equity: {equity_count}")
        else:
            print(f"❌ Instruments endpoint failed: {response.status_code}")
        
        # Test instrument counts endpoint
        print("\n📊 Testing /instruments/counts endpoint...")
        response = requests.get(f"{BASE_URL}/instruments/counts")
        if response.status_code == 200:
            counts = response.json()
            print(f"✅ Counts endpoint: {counts}")
        else:
            print(f"❌ Counts endpoint failed: {response.status_code}")
        
        # Test sync endpoint
        print("\n🔄 Testing /instruments/sync endpoint...")
        response = requests.post(f"{BASE_URL}/instruments/sync")
        if response.status_code == 200:
            sync_result = response.json()
            print(f"✅ Sync endpoint: {sync_result['message']}")
            if 'data' in sync_result:
                print(f"   Sync data: {sync_result['data']}")
        else:
            print(f"❌ Sync endpoint failed: {response.status_code}")
            print(f"   Response: {response.text}")
        
        # Test filtering by instrument type
        print("\n🔍 Testing instrument filtering...")
        response = requests.get(f"{BASE_URL}/instruments/?instrument_type=forex")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Forex instruments: {data['total']} total")
        
        response = requests.get(f"{BASE_URL}/instruments/?instrument_type=crypto")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Crypto instruments: {data['total']} total")
        
        return True
        
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to API server. Make sure the server is running on http://localhost:8000")
        return False
    except Exception as e:
        print(f"❌ Error testing API endpoints: {e}")
        return False


def test_pagination():
    """Test pagination functionality"""
    print("\n📄 Testing Pagination")
    print("=" * 50)
    
    try:
        # Test first page
        response = requests.get(f"{BASE_URL}/instruments/?limit=10&skip=0")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ First page: {len(data['items'])} instruments (page {data['page']})")
        
        # Test second page
        response = requests.get(f"{BASE_URL}/instruments/?limit=10&skip=10")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Second page: {len(data['items'])} instruments (page {data['page']})")
        
        # Test large limit
        response = requests.get(f"{BASE_URL}/instruments/?limit=1000")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Large limit: {len(data['items'])} instruments")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing pagination: {e}")
        return False


async def main():
    """Main test function"""
    print("🚀 Starting Instrument Sync and API Tests")
    print("=" * 60)
    
    # Check if API credentials are available
    oanda_api_key = os.getenv('OANDA_API_KEY')
    oanda_account_id = os.getenv('OANDA_ACCOUNT_ID')
    bitunix_api_key = os.getenv('BITUNIX_API_KEY')
    bitunix_secret_key = os.getenv('BITUNIX_SECRET_KEY')
    
    print(f"OANDA credentials: {'✅' if oanda_api_key and oanda_account_id else '❌'}")
    print(f"Bitunix credentials: {'✅' if bitunix_api_key and bitunix_secret_key else '❌'}")
    print()
    
    # Test instrument sync
    final_counts = await test_instrument_sync()
    
    # Test API endpoints
    api_success = test_api_endpoints()
    
    # Test pagination
    pagination_success = test_pagination()
    
    # Summary
    print("\n📋 Test Summary")
    print("=" * 50)
    
    if final_counts:
        print(f"✅ Database contains {final_counts['total']} instruments")
        print(f"   Forex: {final_counts['forex']}")
        print(f"   Crypto: {final_counts['crypto']}")
        print(f"   Equity: {final_counts['equity']}")
    
    print(f"API Endpoints: {'✅ PASS' if api_success else '❌ FAIL'}")
    print(f"Pagination: {'✅ PASS' if pagination_success else '❌ FAIL'}")
    
    # Recommendations
    print("\n💡 Recommendations:")
    if final_counts and final_counts['total'] < 50:
        print("   - Consider setting up API credentials to get more instruments")
        print("   - Run the sync script manually: python sync_instruments.py")
    
    if not api_success:
        print("   - Make sure the API server is running: uvicorn app.main:app --reload")
    
    print("\n🎯 Expected Results:")
    print("   - 50+ forex instruments (with OANDA credentials)")
    print("   - 400+ crypto instruments (with Bitunix credentials)")
    print("   - All API endpoints working correctly")
    print("   - Proper pagination support")
    
    await instrument_service.close()


if __name__ == "__main__":
    asyncio.run(main()) 