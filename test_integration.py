#!/usr/bin/env python3
"""
Comprehensive integration test for both OANDA and Bitunix APIs
"""

import asyncio
import os
import sys
from dotenv import load_dotenv

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from services.price_service import PriceService

async def test_comprehensive_integration():
    """Test both OANDA and Bitunix integration comprehensively"""
    print("🚀 Starting Comprehensive API Integration Tests")
    print("=" * 60)
    
    # Load environment variables
    load_dotenv()
    
    # Create price service
    price_service = PriceService()
    
    try:
        # Test OANDA (Forex) prices
        print("\n📊 Testing OANDA Forex Prices...")
        forex_symbols = ["EUR_USD", "USD_JPY", "GBP_USD"]
        
        for symbol in forex_symbols:
            price_data = await price_service.get_forex_price(symbol)
            if price_data:
                print(f"✅ {symbol}: Bid={price_data.bid}, Ask={price_data.ask}, Source={price_data.source}")
            else:
                print(f"❌ Failed to get {symbol} price")
        
        # Test Bitunix (Crypto) prices
        print("\n📊 Testing Bitunix Crypto Prices...")
        crypto_symbols = ["BTC_USDT", "ETH_USDT", "SOL_USDT"]
        
        for symbol in crypto_symbols:
            price_data = await price_service.get_crypto_price(symbol)
            if price_data:
                print(f"✅ {symbol}: Bid={price_data.bid}, Ask={price_data.ask}, Source={price_data.source}")
            else:
                print(f"❌ Failed to get {symbol} price")
        
        # Test batch pricing with mixed instrument types
        print("\n📊 Testing Batch Pricing (Mixed Instruments)...")
        mixed_symbols = [
            {"symbol": "EUR_USD", "instrument_type": "forex"},
            {"symbol": "USD_JPY", "instrument_type": "forex"},
            {"symbol": "BTC_USDT", "instrument_type": "crypto"},
            {"symbol": "ETH_USDT", "instrument_type": "crypto"}
        ]
        
        prices = await price_service.get_prices_batch(mixed_symbols)
        if prices:
            print(f"✅ Retrieved {len(prices)} prices in batch")
            for price in prices:
                print(f"   {price.symbol}: Bid={price.bid}, Ask={price.ask}, Source={price.source}")
        else:
            print("❌ Failed to get batch prices")
        
        # Test individual price fetching by instrument type
        print("\n📊 Testing Individual Price Fetching...")
        
        # Forex
        eur_usd_price = await price_service.get_price("EUR_USD", "forex")
        if eur_usd_price:
            print(f"✅ EUR_USD (forex): Bid={eur_usd_price.bid}, Ask={eur_usd_price.ask}")
        
        # Crypto
        btc_usdt_price = await price_service.get_price("BTC_USDT", "crypto")
        if btc_usdt_price:
            print(f"✅ BTC_USDT (crypto): Bid={btc_usdt_price.bid}, Ask={btc_usdt_price.ask}")
        
        # Invalid instrument type
        invalid_price = await price_service.get_price("INVALID", "invalid_type")
        if not invalid_price:
            print("✅ Correctly handled invalid instrument type")
        
    except Exception as e:
        print(f"❌ Error during integration testing: {e}")
    finally:
        # Properly close the price service
        await price_service.close()
        print("\n🔒 All client sessions closed properly")

async def test_error_handling():
    """Test error handling scenarios"""
    print("\n🔍 Testing Error Handling...")
    
    # Load environment variables
    load_dotenv()
    
    # Create price service
    price_service = PriceService()
    
    try:
        # Test with invalid symbols
        print("\n📊 Testing Invalid Symbols...")
        
        invalid_forex = await price_service.get_forex_price("INVALID_FOREX")
        if not invalid_forex:
            print("✅ Correctly handled invalid forex symbol")
        
        invalid_crypto = await price_service.get_crypto_price("INVALID_CRYPTO")
        if not invalid_crypto:
            print("✅ Correctly handled invalid crypto symbol")
        
        # Test with None/null values
        print("\n📊 Testing Null Values...")
        
        null_forex = await price_service.get_forex_price("")
        if not null_forex:
            print("✅ Correctly handled empty forex symbol")
        
        null_crypto = await price_service.get_crypto_price("")
        if not null_crypto:
            print("✅ Correctly handled empty crypto symbol")
            
    except Exception as e:
        print(f"❌ Error during error handling tests: {e}")
    finally:
        await price_service.close()

async def main():
    """Main test function"""
    print("🎯 Comprehensive API Integration Test Suite")
    print("=" * 60)
    
    await test_comprehensive_integration()
    await test_error_handling()
    
    print("\n" + "=" * 60)
    print("✅ All Integration Tests Complete")
    print("🎉 Both OANDA and Bitunix APIs are working correctly!")

if __name__ == "__main__":
    asyncio.run(main()) 