import asyncio
import aiohttp
import hmac
import hashlib
import time
import os
from typing import Dict, List, Optional
from datetime import datetime
import logging
from app.config import settings
from app.schemas import PriceData

logger = logging.getLogger(__name__)


class BitunixClient:
    """Bitunix API client for cryptocurrency futures trading"""
    
    def __init__(self, api_key: str, secret_key: str, base_url: str):
        self.api_key = api_key
        self.secret_key = secret_key
        self.base_url = base_url.rstrip('/')
        self.session = aiohttp.ClientSession()
    
    async def get_tickers(self, symbols: str = None) -> Optional[Dict]:
        """Get futures trading pair market data"""
        try:
            url = f"{self.base_url}/api/v1/futures/market/tickers"
            params = {}
            if symbols:
                params['symbols'] = symbols
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get('code') == 0:  # Success code
                        return data.get('data')
                return None
        except Exception as e:
            logger.error(f"Error fetching Bitunix tickers: {e}")
            return None
    
    async def get_depth(self, symbol: str, limit: int = 5) -> Optional[Dict]:
        """Get depth data for a symbol"""
        try:
            url = f"{self.base_url}/api/v1/futures/market/depth"
            params = {'symbol': symbol, 'limit': limit}
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get('code') == 0:  # Success code
                        return data.get('data')
                return None
        except Exception as e:
            logger.error(f"Error fetching Bitunix depth for {symbol}: {e}")
            return None
    
    async def close(self):
        """Close the aiohttp session"""
        await self.session.close()


class OandaClient:
    """OANDA API client for forex trading"""
    
    def __init__(self, api_key: str, account_id: str, base_url: str):
        self.api_key = api_key
        self.account_id = account_id
        self.base_url = base_url.rstrip('/')
        self.session = aiohttp.ClientSession()
    
    async def get_prices(self, instruments: List[str]) -> Optional[List[Dict]]:
        """Get current prices for instruments"""
        try:
            url = f"{self.base_url}/accounts/{self.account_id}/pricing"
            params = {'instruments': ','.join(instruments)}
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            async with self.session.get(url, params=params, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get('prices', [])
                return None
        except Exception as e:
            logger.error(f"Error fetching OANDA prices: {e}")
            return None
    
    async def get_instruments(self, instruments: List[str] = None) -> Optional[List[Dict]]:
        """Get instrument details"""
        try:
            url = f"{self.base_url}/accounts/{self.account_id}/instruments"
            params = {}
            if instruments:
                params['instruments'] = ','.join(instruments)
            
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            async with self.session.get(url, params=params, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get('instruments', [])
                return None
        except Exception as e:
            logger.error(f"Error fetching OANDA instruments: {e}")
            return None
    
    async def close(self):
        """Close the aiohttp session"""
        await self.session.close()


class PriceService:
    def __init__(self):
        self.oanda_client = None
        self.bitunix_client = None
        self._initialize_clients()
    
    def _initialize_clients(self):
        """Initialize API clients for price providers"""
        # Initialize OANDA client
        # Get OANDA credentials from environment variables
        oanda_api_key = os.getenv('OANDA_DEMO_KEY')
        oanda_account_id = os.getenv('OANDA_DEMO_ACCOUNT_ID')
        
        if oanda_api_key and oanda_account_id:
            try:
                # Use demo environment by default
                base_url = "https://api-fxpractice.oanda.com/v3"
                if settings.oanda_environment == "live":
                    base_url = "https://api-fxtrade.oanda.com/v3"
                
                self.oanda_client = OandaClient(
                    api_key=oanda_api_key,
                    account_id=oanda_account_id,
                    base_url=base_url
                )
                logger.info("OANDA client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize OANDA client: {e}")
        
        # Initialize Bitunix client
        bitunix_api_key = os.getenv('BITUNIX_API_KEY')
        bitunix_secret_key = os.getenv('BITUNIX_SECRET_KEY')
        
        if bitunix_api_key and bitunix_secret_key:
            try:
                # Bitunix API base URL - using the correct futures API endpoint
                base_url = "https://fapi.bitunix.com"
                # Note: BitunixClient will be initialized when first used to avoid event loop issues
                self._bitunix_config = {
                    'api_key': bitunix_api_key,
                    'secret_key': bitunix_secret_key,
                    'base_url': base_url
                }
                logger.info("Bitunix client configuration prepared")
            except Exception as e:
                logger.error(f"Failed to prepare Bitunix client configuration: {e}")
    
    async def close(self):
        """Close all client sessions"""
        if self.oanda_client:
            await self.oanda_client.close()
        if self.bitunix_client:
            await self.bitunix_client.close()
    
    async def get_forex_price(self, symbol: str) -> Optional[PriceData]:
        """Get current price for forex instrument from OANDA"""
        if not self.oanda_client:
            logger.warning("OANDA client not available")
            return None
        
        try:
            # Get pricing info from OANDA
            prices = await self.oanda_client.get_prices([symbol])
            
            if prices and len(prices) > 0:
                price_info = prices[0]
                if price_info.get('bids') and price_info.get('asks'):
                    return PriceData(
                        symbol=symbol,
                        bid=float(price_info['bids'][0]['price']),
                        ask=float(price_info['asks'][0]['price']),
                        timestamp=datetime.fromisoformat(price_info['time'].replace('Z', '+00:00')),
                        source="oanda"
                    )
        except Exception as e:
            logger.error(f"Error fetching forex price for {symbol}: {e}")
        
        return None
    
    async def get_crypto_price(self, symbol: str) -> Optional[PriceData]:
        """Get current price for cryptocurrency from Bitunix"""
        if not hasattr(self, '_bitunix_config'):
            logger.warning("Bitunix client not available")
            return None
        
        # Initialize Bitunix client on first use
        if not self.bitunix_client:
            try:
                self.bitunix_client = BitunixClient(
                    api_key=self._bitunix_config['api_key'],
                    secret_key=self._bitunix_config['secret_key'],
                    base_url=self._bitunix_config['base_url']
                )
                logger.info("Bitunix client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Bitunix client: {e}")
                return None
        
        try:
            # Convert symbol format (e.g., BTC_USDT -> BTCUSDT)
            # Bitunix uses symbols like BTCUSDT, ETHUSDT, etc.
            bitunix_symbol = symbol.replace("_", "")
            
            # Get tickers from Bitunix (single symbol)
            tickers_data = await self.bitunix_client.get_tickers(bitunix_symbol)
            
            if tickers_data and isinstance(tickers_data, list) and len(tickers_data) > 0:
                ticker_data = tickers_data[0]  # Get first (and only) ticker
                
                # Extract mark price and last price from ticker data
                mark_price = float(ticker_data.get('markPrice', 0))
                last_price = float(ticker_data.get('lastPrice', 0))
                
                # Use mark price as primary, fallback to last price
                price = mark_price if mark_price > 0 else last_price
                
                if price > 0:
                    # Create small spread for bid/ask
                    spread = price * 0.0001  # 0.01% spread
                    bid = price - spread
                    ask = price + spread
                    
                    return PriceData(
                        symbol=symbol,
                        bid=bid,
                        ask=ask,
                        timestamp=datetime.utcnow(),
                        source="bitunix"
                    )
            
            # Fallback: try to get depth for better bid/ask
            depth_data = await self.bitunix_client.get_depth(bitunix_symbol, limit=5)
            if depth_data and 'bids' in depth_data and 'asks' in depth_data:
                bids = depth_data['bids']
                asks = depth_data['asks']
                
                if bids and asks:
                    bid = float(bids[0][0])  # Best bid price
                    ask = float(asks[0][0])  # Best ask price
                    
                    return PriceData(
                        symbol=symbol,
                        bid=bid,
                        ask=ask,
                        timestamp=datetime.utcnow(),
                        source="bitunix"
                    )
                    
        except Exception as e:
            logger.error(f"Error fetching crypto price for {symbol}: {e}")
        
        return None
    
    async def get_price(self, symbol: str, instrument_type: str) -> Optional[PriceData]:
        """Get current price based on instrument type"""
        if instrument_type == "forex":
            return await self.get_forex_price(symbol)
        elif instrument_type == "crypto":
            return await self.get_crypto_price(symbol)
        else:
            logger.warning(f"Unsupported instrument type: {instrument_type}")
            return None
    
    async def get_prices_batch(self, symbols: List[Dict[str, str]]) -> List[PriceData]:
        """Get prices for multiple symbols in batch"""
        tasks = []
        for symbol_info in symbols:
            task = self.get_price(symbol_info['symbol'], symbol_info['instrument_type'])
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        prices = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Error fetching price for {symbols[i]}: {result}")
            elif result:
                prices.append(result)
        
        return prices


# Global price service instance
price_service = PriceService() 