"""
Historical Data Service
Provides unified historical candlestick data with automatic chunking and caching
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass

from app.services.price_service import OandaClient, BitunixClient
from app.config import settings

logger = logging.getLogger(__name__)


@dataclass
class CandleData:
    """Unified candle data structure"""
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: Optional[float] = None
    source: str = "unknown"


@dataclass
class HistoricalRequest:
    """Historical data request parameters"""
    symbol: str
    interval: str
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    max_candles: Optional[int] = None
    source: str = "auto"  # "oanda", "bitunix", or "auto"


class HistoricalDataService:
    """Unified historical data service with chunking support"""
    
    # Broker-specific limits
    BROKER_LIMITS = {
        "oanda": 5000,
        "bitunix": 200
    }
    
    # Interval mappings
    INTERVAL_MAPPINGS = {
        "oanda": {
            "1m": "M1",
            "5m": "M5", 
            "15m": "M15",
            "30m": "M30",
            "1h": "H1",
            "4h": "H4",
            "1d": "D"
        },
        "bitunix": {
            "1m": "1m",
            "5m": "5m",
            "15m": "15m", 
            "30m": "30m",
            "1h": "1h",
            "4h": "4h",
            "1d": "1d"
        }
    }
    
    def __init__(self):
        self.oanda_client = None
        self.bitunix_client = None
        self._initialize_clients()
    
    def _initialize_clients(self):
        """Initialize API clients"""
        # Initialize OANDA client
        oanda_api_key = settings.oanda_api_key
        oanda_account_id = settings.oanda_account_id
        
        if oanda_api_key and oanda_account_id:
            try:
                base_url = "https://api-fxpractice.oanda.com/v3"
                if settings.oanda_environment == "live":
                    base_url = "https://api-fxtrade.oanda.com/v3"
                
                self.oanda_client = OandaClient(
                    api_key=oanda_api_key,
                    account_id=oanda_account_id,
                    base_url=base_url
                )
                logger.info("OANDA historical client initialized")
            except Exception as e:
                logger.error(f"Failed to initialize OANDA client: {e}")
        
        # Initialize Bitunix client
        bitunix_api_key = settings.bitunix_api_key
        bitunix_secret_key = settings.bitunix_secret_key
        
        if bitunix_api_key and bitunix_secret_key:
            try:
                base_url = "https://fapi.bitunix.com"
                self.bitunix_client = BitunixClient(
                    api_key=bitunix_api_key,
                    secret_key=bitunix_secret_key,
                    base_url=base_url
                )
                logger.info("Bitunix historical client initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Bitunix client: {e}")
    
    async def close(self):
        """Close all client sessions"""
        if self.oanda_client:
            await self.oanda_client.close()
        if self.bitunix_client:
            await self.bitunix_client.close()
    
    def _determine_source(self, symbol: str, source: str = "auto") -> str:
        """Determine which broker to use for a symbol"""
        if source != "auto":
            return source
        
        # Simple heuristic: if symbol contains underscore, it's forex (Oanda)
        # If no underscore, it's crypto (Bitunix)
        if "_" in symbol:
            return "oanda"
        else:
            return "bitunix"
    
    def _map_interval(self, interval: str, source: str) -> str:
        """Map unified interval to broker-specific format"""
        mappings = self.INTERVAL_MAPPINGS.get(source, {})
        return mappings.get(interval, interval)
    
    def _calculate_chunks(self, start_time: datetime, end_time: datetime, 
                         interval: str, source: str) -> List[Tuple[datetime, datetime]]:
        """Calculate time chunks based on broker limits and interval"""
        max_candles = self.BROKER_LIMITS[source]
        
        # Calculate minutes per candle
        interval_minutes = {
            "1m": 1, "5m": 5, "15m": 15, "30m": 30,
            "1h": 60, "4h": 240, "1d": 1440
        }
        
        minutes_per_candle = interval_minutes.get(interval, 1)
        max_minutes = max_candles * minutes_per_candle
        
        chunks = []
        current_start = start_time
        
        while current_start < end_time:
            current_end = min(current_start + timedelta(minutes=max_minutes), end_time)
            chunks.append((current_start, current_end))
            current_start = current_end
        
        return chunks
    
    async def get_historical_data(self, request: HistoricalRequest) -> List[CandleData]:
        """
        Get historical candlestick data with automatic chunking
        
        Args:
            request: HistoricalRequest object with parameters
            
        Returns:
            List of CandleData objects
        """
        source = self._determine_source(request.symbol, request.source)
        
        if source == "oanda" and not self.oanda_client:
            raise ValueError("Oanda client not available")
        elif source == "bitunix" and not self.bitunix_client:
            raise ValueError("Bitunix client not available")
        
        # Set default time range if not provided
        if not request.end_time:
            request.end_time = datetime.utcnow()
        if not request.start_time:
            # Default to 7 days ago
            request.start_time = request.end_time - timedelta(days=7)
        
        # Calculate chunks
        chunks = self._calculate_chunks(
            request.start_time, 
            request.end_time, 
            request.interval, 
            source
        )
        
        logger.info(f"Fetching {len(chunks)} chunks for {request.symbol} {request.interval}")
        
        all_candles = []
        
        for i, (chunk_start, chunk_end) in enumerate(chunks):
            logger.info(f"Fetching chunk {i+1}/{len(chunks)}: {chunk_start} to {chunk_end}")
            
            if source == "oanda":
                candles = await self._fetch_oanda_chunk(
                    request.symbol, request.interval, chunk_start, chunk_end
                )
            else:
                candles = await self._fetch_bitunix_chunk(
                    request.symbol, request.interval, chunk_start, chunk_end
                )
            
            if candles:
                all_candles.extend(candles)
            
            # Rate limiting - small delay between chunks
            if i < len(chunks) - 1:
                await asyncio.sleep(0.1)
        
        # Sort by timestamp and apply max_candles limit
        all_candles.sort(key=lambda x: x.timestamp)
        
        if request.max_candles:
            all_candles = all_candles[-request.max_candles:]
        
        logger.info(f"Retrieved {len(all_candles)} total candles")
        return all_candles
    
    async def _fetch_oanda_chunk(self, symbol: str, interval: str, 
                                start_time: datetime, end_time: datetime) -> List[CandleData]:
        """Fetch a chunk of Oanda historical data"""
        try:
            mapped_interval = self._map_interval(interval, "oanda")
            
            candles = await self.oanda_client.get_candles(
                instrument=symbol,
                granularity=mapped_interval,
                from_time=start_time.isoformat() + 'Z',
                to_time=end_time.isoformat() + 'Z'
            )
            
            if not candles:
                return []
            
            result = []
            for candle in candles:
                if candle.get('complete', True):  # Only include complete candles
                    result.append(CandleData(
                        timestamp=datetime.fromisoformat(candle['time'].replace('Z', '+00:00')),
                        open=float(candle['mid']['o']),
                        high=float(candle['mid']['h']),
                        low=float(candle['mid']['l']),
                        close=float(candle['mid']['c']),
                        volume=float(candle.get('volume', 0)),
                        source="oanda"
                    ))
            
            return result
            
        except Exception as e:
            logger.error(f"Error fetching Oanda chunk: {e}")
            return []
    
    async def _fetch_bitunix_chunk(self, symbol: str, interval: str,
                                  start_time: datetime, end_time: datetime) -> List[CandleData]:
        """Fetch a chunk of Bitunix historical data"""
        try:
            mapped_interval = self._map_interval(interval, "bitunix")
            
            # Convert to milliseconds
            start_ms = int(start_time.timestamp() * 1000)
            end_ms = int(end_time.timestamp() * 1000)
            
            klines = await self.bitunix_client.get_kline(
                symbol=symbol,
                interval=mapped_interval,
                limit=self.BROKER_LIMITS["bitunix"],
                start_time=start_ms,
                end_time=end_ms
            )
            
            if not klines:
                return []
            
            result = []
            for kline in klines:
                # Handle time field - could be string or number
                time_value = kline['time']
                if isinstance(time_value, str):
                    time_value = int(time_value)
                
                result.append(CandleData(
                    timestamp=datetime.fromtimestamp(time_value / 1000),
                    open=float(kline['open']),
                    high=float(kline['high']),
                    low=float(kline['low']),
                    close=float(kline['close']),
                    volume=float(kline.get('baseVol', 0)),
                    source="bitunix"
                ))
            
            return result
            
        except Exception as e:
            logger.error(f"Error fetching Bitunix chunk: {e}")
            return []
    
    async def get_available_intervals(self) -> Dict[str, List[str]]:
        """Get available intervals for each broker"""
        return {
            "oanda": ["1m", "5m", "15m", "30m", "1h", "4h", "1d"],
            "bitunix": ["1m", "5m", "15m", "30m", "1h", "4h", "1d"]
        }
    
    def get_broker_limits(self) -> Dict[str, int]:
        """Get broker-specific limits"""
        return self.BROKER_LIMITS.copy() 