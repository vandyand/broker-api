#!/usr/bin/env python3
"""
Instrument Synchronization Script

This script synchronizes instruments from OANDA and Bitunix APIs to the database.
It will fetch all available instruments and add them to the database if they don't already exist.
"""

import asyncio
import os
import sys
from dotenv import load_dotenv

# Add the app directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from app.database import SessionLocal
from app.services.instrument_service import instrument_service
from app.models import Instrument, InstrumentType

# Load environment variables
load_dotenv()


async def main():
    """Main function to sync instruments"""
    print("🔄 Starting Instrument Synchronization")
    print("=" * 50)
    
    # Check if API credentials are available
    oanda_api_key = os.getenv('OANDA_API_KEY')
    oanda_account_id = os.getenv('OANDA_ACCOUNT_ID')
    bitunix_api_key = os.getenv('BITUNIX_API_KEY')
    bitunix_secret_key = os.getenv('BITUNIX_SECRET_KEY')
    
    print(f"OANDA API Key: {'✅ SET' if oanda_api_key else '❌ NOT SET'}")
    print(f"OANDA Account ID: {'✅ SET' if oanda_account_id else '❌ NOT SET'}")
    print(f"Bitunix API Key: {'✅ SET' if bitunix_api_key else '❌ NOT SET'}")
    print(f"Bitunix Secret Key: {'✅ SET' if bitunix_secret_key else '❌ NOT SET'}")
    print()
    
    if not oanda_api_key or not oanda_account_id:
        print("⚠️  OANDA credentials not set - forex instruments will not be synced")
    
    if not bitunix_api_key or not bitunix_secret_key:
        print("⚠️  Bitunix credentials not set - crypto instruments will not be synced")
    
    if not any([oanda_api_key, oanda_account_id, bitunix_api_key, bitunix_secret_key]):
        print("❌ No API credentials available. Please set up your .env file.")
        return
    
    # Get current instrument counts
    db = SessionLocal()
    try:
        current_counts = await instrument_service.get_instrument_counts(db)
        print("📊 Current Database State:")
        print(f"   Total instruments: {current_counts['total']}")
        print(f"   Forex instruments: {current_counts['forex']}")
        print(f"   Crypto instruments: {current_counts['crypto']}")
        print(f"   Equity instruments: {current_counts['equity']}")
        print()
        
        # Sync instruments from APIs
        print("🔄 Syncing instruments from APIs...")
        synced_counts = await instrument_service.sync_instruments_from_apis(db)
        
        print("✅ Synchronization completed!")
        print(f"   New forex instruments: {synced_counts['forex']}")
        print(f"   New crypto instruments: {synced_counts['crypto']}")
        print(f"   Total new instruments: {synced_counts['total']}")
        print()
        
        # Get updated counts
        updated_counts = await instrument_service.get_instrument_counts(db)
        print("📊 Updated Database State:")
        print(f"   Total instruments: {updated_counts['total']}")
        print(f"   Forex instruments: {updated_counts['forex']}")
        print(f"   Crypto instruments: {updated_counts['crypto']}")
        print(f"   Equity instruments: {updated_counts['equity']}")
        
        # Show some examples of synced instruments
        if synced_counts['forex'] > 0:
            print(f"\n📈 Sample Forex Instruments:")
            forex_instruments = db.query(Instrument).filter(Instrument.instrument_type == InstrumentType.FOREX).limit(5).all()
            for instrument in forex_instruments:
                print(f"   {instrument.symbol}: {instrument.name}")
        
        if synced_counts['crypto'] > 0:
            print(f"\n🪙 Sample Crypto Instruments:")
            crypto_instruments = db.query(Instrument).filter(Instrument.instrument_type == InstrumentType.CRYPTO).limit(5).all()
            for instrument in crypto_instruments:
                print(f"   {instrument.symbol}: {instrument.name}")
        
    except Exception as e:
        print(f"❌ Error during synchronization: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        db.close()
        await instrument_service.close()


if __name__ == "__main__":
    asyncio.run(main()) 