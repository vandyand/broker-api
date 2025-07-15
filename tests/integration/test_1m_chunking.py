import asyncio
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
from app.services.price_service import OandaClient, BitunixClient

# Load environment variables
load_dotenv()

async def test_oanda_1m():
    api_key = os.getenv('OANDA_API_KEY')
    account_id = os.getenv('OANDA_ACCOUNT_ID')
    
    print(f"Oanda API Key: {'SET' if api_key else 'NOT SET'}")
    print(f"Oanda Account ID: {'SET' if account_id else 'NOT SET'}")
    
    if not api_key or not account_id:
        print("❌ Oanda credentials missing")
        return
    
    base_url = 'https://api-fxpractice.oanda.com/v3'
    client = OandaClient(api_key=api_key, account_id=account_id, base_url=base_url)
    
    # Try a smaller window first - just 1 day
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(days=1)
    
    print(f"Requesting Oanda M1 candles from {start_time} to {end_time}")
    
    # Oanda max per request is 5000, but let's try with count first
    candles = await client.get_candles('EUR_USD', 'M1', count=1000)
    print(f'Oanda: Got {len(candles) if candles else 0} M1 candles (requested 1000)')
    
    if candles:
        print(f"First candle: {candles[0]}")
        print(f"Last candle: {candles[-1]}")
    
    await client.close()

async def test_bitunix_1m():
    api_key = os.getenv('BITUNIX_API_KEY')
    secret_key = os.getenv('BITUNIX_SECRET_KEY')
    
    print(f"Bitunix API Key: {'SET' if api_key else 'NOT SET'}")
    print(f"Bitunix Secret Key: {'SET' if secret_key else 'NOT SET'}")
    
    if not api_key or not secret_key:
        print("❌ Bitunix credentials missing")
        return
    
    base_url = 'https://fapi.bitunix.com'
    client = BitunixClient(api_key=api_key, secret_key=secret_key, base_url=base_url)
    
    # Try without time constraints first - just get the most recent 100 candles
    print("Requesting Bitunix 1m candles (most recent 100, no time constraints)")
    
    # Bitunix max per request is actually 500, not 200
    klines = await client.get_kline('BTCUSDT', '1m', limit=100)
    print(f'Bitunix: Got {len(klines) if klines else 0} 1m candles (requested 100)')
    
    if klines:
        print(f"First kline: {klines[0]}")
        print(f"Last kline: {klines[-1]}")
    
    # Also try with 500 limit to see if we can get more
    print("\nRequesting Bitunix 1m candles (most recent 500, no time constraints)")
    klines_500 = await client.get_kline('BTCUSDT', '1m', limit=500)
    print(f'Bitunix: Got {len(klines_500) if klines_500 else 0} 1m candles (requested 500)')
    
    await client.close()

async def main():
    print("🔍 Debugging 1m Candle Issues")
    print("=" * 50)
    
    await test_oanda_1m()
    print()
    await test_bitunix_1m()

if __name__ == '__main__':
    asyncio.run(main()) 