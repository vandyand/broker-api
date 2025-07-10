#!/usr/bin/env python3
"""
Test script for Bitunix API integration
"""

import asyncio
import aiohttp
import hmac
import hashlib
import time
from typing import Dict, Optional
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class BitunixTestClient:
    """Test client for Bitunix API"""
    
    def __init__(self, api_key: str, secret_key: str, base_url: str):
        self.api_key = api_key
        self.secret_key = secret_key
        self.base_url = base_url.rstrip('/')
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def _generate_signature(self, timestamp: str, method: str, path: str, body: str = '') -> str:
        """Generate HMAC signature for Bitunix API"""
        message = f"{timestamp}{method}{path}{body}"
        signature = hmac.new(
            self.secret_key.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return signature
    
    async def get_tickers(self, symbols: str = None) -> Optional[Dict]:
        """Get futures trading pair market data"""
        try:
            url = f"{self.base_url}/api/v1/futures/market/tickers"
            params = {}
            if symbols:
                params['symbols'] = symbols
            
            async with self.session.get(url, params=params) as response:
                print(f"Tickers response status: {response.status}")
                if response.status == 200:
                    data = await response.json()
                    print(f"Tickers response: {data}")
                    if data.get('code') == 0:  # Success code
                        return data.get('data')
                return None
        except Exception as e:
            print(f"Error fetching tickers: {e}")
            return None
    
    async def get_depth(self, symbol: str, limit: int = 5) -> Optional[Dict]:
        """Get depth data for a symbol"""
        try:
            url = f"{self.base_url}/api/v1/futures/market/depth"
            params = {'symbol': symbol, 'limit': limit}
            
            async with self.session.get(url, params=params) as response:
                print(f"Depth response status: {response.status}")
                if response.status == 200:
                    data = await response.json()
                    print(f"Depth response: {data}")
                    if data.get('code') == 0:  # Success code
                        return data.get('data')
                return None
        except Exception as e:
            print(f"Error fetching depth for {symbol}: {e}")
            return None
    
    async def get_server_time(self) -> Optional[Dict]:
        """Get server time"""
        try:
            url = f"{self.base_url}/api/v1/common/time"
            
            async with self.session.get(url) as response:
                print(f"Server time response status: {response.status}")
                if response.status == 200:
                    data = await response.json()
                    print(f"Server time response: {data}")
                    return data
                return None
        except Exception as e:
            print(f"Error fetching server time: {e}")
            return None


async def test_bitunix_connection():
    """Test Bitunix API connection"""
    print("🔗 Testing Bitunix API Connection...")
    print("=" * 50)
    
    # Get credentials from environment
    api_key = os.getenv('BITUNIX_API_KEY')
    secret_key = os.getenv('BITUNIX_SECRET_KEY')
    base_url = "https://fapi.bitunix.com"  # Bitunix futures API endpoint
    
    if not api_key or not secret_key:
        print("❌ Missing Bitunix credentials in .env file")
        print("Please set: BITUNIX_API_KEY, BITUNIX_SECRET_KEY")
        return
    
    print(f"🔑 API Key: {api_key[:10]}...")
    print(f"🌐 Base URL: {base_url}")
    print()
    
    async with BitunixTestClient(api_key, secret_key, base_url) as client:
        # Test server time
        print("⏰ Testing server time...")
        server_time = await client.get_server_time()
        if server_time:
            print("✅ Server time retrieved successfully")
        else:
            print("❌ Failed to get server time")
        
        print()
        
        # Test tickers for BTCUSDT
        print("📊 Testing BTCUSDT tickers...")
        tickers = await client.get_tickers("BTCUSDT")
        if tickers and len(tickers) > 0:
            ticker = tickers[0]
            print("✅ BTCUSDT tickers retrieved successfully")
            print(f"   Mark price: {ticker.get('markPrice', 'N/A')}")
            print(f"   Last price: {ticker.get('lastPrice', 'N/A')}")
            print(f"   High: {ticker.get('high', 'N/A')}")
            print(f"   Low: {ticker.get('low', 'N/A')}")
        else:
            print("❌ Failed to get BTCUSDT tickers")
        
        print()
        
        # Test depth for BTCUSDT
        print("📚 Testing BTCUSDT depth...")
        depth = await client.get_depth("BTCUSDT", limit=5)
        if depth:
            print("✅ BTCUSDT depth retrieved successfully")
            bids = depth.get('bids', [])
            asks = depth.get('asks', [])
            print(f"   Top 3 bids: {bids[:3]}")
            print(f"   Top 3 asks: {asks[:3]}")
        else:
            print("❌ Failed to get BTCUSDT depth")
        
        print()
        
        # Test multiple symbols at once
        print("📊 Testing multiple symbols...")
        tickers = await client.get_tickers("BTCUSDT,ETHUSDT,SOLUSDT")
        if tickers:
            print(f"✅ Retrieved {len(tickers)} tickers successfully")
            for ticker in tickers:
                symbol = ticker.get('symbol', 'Unknown')
                mark_price = ticker.get('markPrice', 'N/A')
                print(f"   {symbol}: {mark_price}")
        else:
            print("❌ Failed to get multiple tickers")
        
        print()


if __name__ == "__main__":
    asyncio.run(test_bitunix_connection()) 