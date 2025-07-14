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
    
    async def get_kline(self, symbol: str, interval: str, limit: int = 100, 
                       start_time: Optional[int] = None, end_time: Optional[int] = None, 
                       kline_type: str = "LAST_PRICE") -> Optional[List[Dict]]:
        """
        Get historical kline/candlestick data
        
        Args:
            symbol: Trading pair (e.g., BTCUSDT)
            interval: Kline interval (1m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 8h, 12h, 1d, 3d, 1w, 1M)
            limit: Number of candles to return (default 100, max 200)
            start_time: Start time in milliseconds (Unix timestamp)
            end_time: End time in milliseconds (Unix timestamp)
            kline_type: Kline type - LAST_PRICE or MARK_PRICE (default: LAST_PRICE)
            
        Returns:
            List of kline data dictionaries or None if error
        """
        try:
            url = f"{self.base_url}/api/v1/futures/market/kline"
            params = {
                'symbol': symbol,
                'interval': interval,
                'limit': limit,
                'type': kline_type
            }
            
            if start_time is not None:
                params['startTime'] = start_time
            if end_time is not None:
                params['endTime'] = end_time
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get('code') == 0:  # Success code
                        return data.get('data', [])
                    else:
                        logger.error(f"Bitunix API error: {data.get('msg', 'Unknown error')}")
                        return None
                else:
                    logger.error(f"HTTP error {response.status} fetching Bitunix klines for {symbol}")
                    return None
        except Exception as e:
            logger.error(f"Error fetching Bitunix klines for {symbol}: {e}")
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
        self._real_account_id = None
    
    async def _get_real_account_id(self) -> str:
        """Get the real account ID if the provided one is a placeholder"""
        if self._real_account_id:
            return self._real_account_id
        
        # If account_id looks like a placeholder, get the real one
        if self.account_id == "your_oanda_account_id_here" or "placeholder" in self.account_id.lower():
            try:
                url = f"{self.base_url}/accounts"
                headers = {
                    'Authorization': f'Bearer {self.api_key}',
                    'Content-Type': 'application/json'
                }
                
                timeout = aiohttp.ClientTimeout(total=30)
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    async with session.get(url, headers=headers) as response:
                        if response.status == 200:
                            data = await response.json()
                            accounts = data.get('accounts', [])
                            if accounts:
                                self._real_account_id = accounts[0]['id']
                                logger.info(f"Using real OANDA account ID: {self._real_account_id}")
                                return self._real_account_id
            except Exception as e:
                logger.error(f"Error getting real account ID: {e}")
        
        # Use the provided account ID if we can't get a real one
        return self.account_id
    
    async def get_prices(self, instruments: List[str]) -> Optional[List[Dict]]:
        """Get current prices for instruments"""
        try:
            account_id = await self._get_real_account_id()
            url = f"{self.base_url}/accounts/{account_id}/pricing"
            params = {'instruments': ','.join(instruments)}
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            timeout = aiohttp.ClientTimeout(total=30)  # 30 second timeout
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url, params=params, headers=headers) as response:
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
            account_id = await self._get_real_account_id()
            url = f"{self.base_url}/accounts/{account_id}/instruments"
            params = {}
            if instruments:
                params['instruments'] = ','.join(instruments)
            
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            timeout = aiohttp.ClientTimeout(total=30)  # 30 second timeout
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url, params=params, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get('instruments', [])
                    return None
        except Exception as e:
            logger.error(f"Error fetching OANDA instruments: {e}")
            return None
    
    async def get_candles(self, instrument: str, granularity: str, count: int = 100,
                         from_time: Optional[str] = None, to_time: Optional[str] = None,
                         price: str = "M") -> Optional[List[Dict]]:
        """
        Get historical candlestick data
        
        Args:
            instrument: Instrument name (e.g., EUR_USD)
            granularity: Candle granularity (M1, M5, M15, M30, H1, H4, D)
            count: Number of candles to return (default 100)
            from_time: Start time in ISO format (e.g., "2023-01-01T00:00:00Z")
            to_time: End time in ISO format (e.g., "2023-01-02T00:00:00Z")
            price: Price type - M (midpoint), B (bid), A (ask) (default: M)
            
        Returns:
            List of candle data dictionaries or None if error
        """
        try:
            url = f"{self.base_url}/instruments/{instrument}/candles"
            params = {
                'price': price,
                'granularity': granularity
            }
            
            if from_time and to_time:
                params['from'] = from_time
                params['to'] = to_time
            else:
                params['count'] = count
            
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            timeout = aiohttp.ClientTimeout(total=30)  # 30 second timeout
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url, params=params, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get('candles', [])
                    else:
                        logger.error(f"HTTP error {response.status} fetching OANDA candles for {instrument}")
                        return None
        except Exception as e:
            logger.error(f"Error fetching OANDA candles for {instrument}: {e}")
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
        oanda_api_key = settings.oanda_api_key
        oanda_account_id = settings.oanda_account_id
        
        # Use real demo credentials if placeholder is detected
        if oanda_api_key == "your_oanda_api_key_here":
            oanda_api_key = "808b8c2978ded93c563bc420348788ab-00fba0cf47cf2456d8b4bfeb4c65c312"
            logger.info("Using real OANDA demo API key")
        
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
        bitunix_api_key = settings.bitunix_api_key
        bitunix_secret_key = settings.bitunix_secret_key
        
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
    
    async def get_available_instruments(self) -> Dict[str, List[str]]:
        """Get all available instruments from both providers"""
        instruments = {"forex": [], "crypto": []}
        
        # Get OANDA instruments
        if self.oanda_client:
            try:
                oanda_instruments = await self.oanda_client.get_instruments()
                if oanda_instruments:
                    for instrument in oanda_instruments:
                        symbol = instrument.get('name', '')
                        if symbol:
                            instruments["forex"].append(symbol)
                    logger.info(f"Found {len(instruments['forex'])} OANDA instruments")
            except Exception as e:
                logger.error(f"Error fetching OANDA instruments: {e}")
        
        # Get Bitunix instruments
        if hasattr(self, '_bitunix_config'):
            if not self.bitunix_client:
                try:
                    self.bitunix_client = BitunixClient(
                        api_key=self._bitunix_config['api_key'],
                        secret_key=self._bitunix_config['secret_key'],
                        base_url=self._bitunix_config['base_url']
                    )
                except Exception as e:
                    logger.error(f"Failed to initialize Bitunix client: {e}")
                    return instruments
            
            try:
                # Get all tickers to extract available symbols
                tickers_data = await self.bitunix_client.get_tickers()
                if tickers_data and isinstance(tickers_data, list):
                    for ticker in tickers_data:
                        symbol = ticker.get('symbol', '')
                        if symbol:
                            # Convert Bitunix format (BTCUSDT) to our format (BTC_USDT)
                            formatted_symbol = self._format_bitunix_symbol(symbol)
                            if formatted_symbol:
                                instruments["crypto"].append(formatted_symbol)
                    logger.info(f"Found {len(instruments['crypto'])} Bitunix instruments")
            except Exception as e:
                logger.error(f"Error fetching Bitunix instruments: {e}")
        
        return instruments
    
    def _format_bitunix_symbol(self, symbol: str) -> Optional[str]:
        """Convert Bitunix symbol format to our format"""
        # Bitunix symbols are like BTCUSDT, ETHUSDT, etc.
        # We want to convert to BTC_USDT, ETH_USDT, etc.
        if len(symbol) < 6:  # Minimum length for a valid pair
            return None
        
        # Common quote currencies in crypto
        quote_currencies = ['USDT', 'USD', 'BTC', 'ETH', 'BNB', 'ADA', 'DOT', 'LINK', 'LTC', 'BCH', 'XRP']
        
        for quote in quote_currencies:
            if symbol.endswith(quote):
                base = symbol[:-len(quote)]
                if base and len(base) >= 2:  # Ensure base currency has reasonable length
                    return f"{base}_{quote}"
        
        return None
    
    async def get_instrument_type(self, symbol: str) -> Optional[str]:
        """Determine instrument type for a given symbol"""
        # First check if it's in our database
        # This would require a database session, so we'll implement a different approach
        
        # Check if it's a forex pair (common patterns)
        forex_patterns = [
            # Major pairs
            'EUR_USD', 'GBP_USD', 'USD_JPY', 'USD_CHF', 'AUD_USD', 'USD_CAD', 'NZD_USD',
            # Cross pairs
            'EUR_GBP', 'EUR_JPY', 'GBP_JPY', 'EUR_CHF', 'AUD_JPY', 'CAD_JPY',
            # Other common forex pairs
            'USD_CNH', 'USD_SGD', 'USD_HKD', 'USD_SEK', 'USD_NOK', 'USD_DKK',
            'EUR_AUD', 'EUR_CAD', 'GBP_AUD', 'GBP_CAD', 'AUD_CAD', 'NZD_JPY'
        ]
        
        if symbol in forex_patterns:
            return "forex"
        
        # Check if it's a crypto pair (common patterns)
        crypto_patterns = [
            'BTC_USDT', 'ETH_USDT', 'BNB_USDT', 'ADA_USDT', 'DOT_USDT', 'LINK_USDT',
            'LTC_USDT', 'BCH_USDT', 'XRP_USDT', 'EOS_USDT', 'TRX_USDT', 'XLM_USDT',
            'BTC_USD', 'ETH_USD', 'BTC_ETH', 'ETH_BTC'
        ]
        
        if symbol in crypto_patterns:
            return "crypto"
        
        # If not in common patterns, try to determine by structure
        if '_' in symbol:
            parts = symbol.split('_')
            if len(parts) == 2:
                # Check if it looks like forex (3-letter codes)
                if len(parts[0]) == 3 and len(parts[1]) == 3:
                    return "forex"
                # Check if it looks like crypto (variable length)
                else:
                    return "crypto"
        
        return None


# Global price service instance
price_service = PriceService() 