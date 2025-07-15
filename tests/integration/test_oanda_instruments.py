#!/usr/bin/env python3
"""
Test OANDA Instruments Availability
"""

import asyncio
import os
from dotenv import load_dotenv
from app.services.price_service import PriceService

# Load environment variables
load_dotenv()


async def test_oanda_instruments():
    """Test OANDA instruments availability"""
    print("🔍 Testing OANDA Instruments Availability")
    print("=" * 50)
    
    service = PriceService()
    
    try:
        # Get available instruments
        instruments = await service.get_available_instruments()
        
        print(f"Forex instruments: {len(instruments.get('forex', []))}")
        print(f"Crypto instruments: {len(instruments.get('crypto', []))}")
        
        if instruments.get('forex'):
            print("\n📈 Sample Forex Instruments:")
            for symbol in instruments['forex'][:10]:  # Show first 10
                print(f"   {symbol}")
        
        if instruments.get('crypto'):
            print("\n🪙 Sample Crypto Instruments:")
            for symbol in instruments['crypto'][:10]:  # Show first 10
                print(f"   {symbol}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await service.close()


if __name__ == "__main__":
    asyncio.run(test_oanda_instruments()) 