"""
Historical Data API Endpoints
Provides REST API for historical candlestick data with caching
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel

import logging
from app.services.historical_data_service import HistoricalDataService, HistoricalRequest, CandleData
from app.services.cache_service import CacheService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/historical", tags=["Historical Data"])


class CandleDataResponse(BaseModel):
    """Response model for candle data"""
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: Optional[float] = None
    source: str
    
    class Config:
        from_attributes = True


class HistoricalDataRequest(BaseModel):
    """Request model for historical data"""
    symbol: str
    interval: str
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    max_candles: Optional[int] = None
    source: str = "auto"  # "oanda", "bitunix", or "auto"
    use_cache: bool = True
    fill_gaps: bool = True


class CacheCoverageResponse(BaseModel):
    """Response model for cache coverage"""
    symbol: str
    interval: str
    source: str
    start_time: datetime
    end_time: datetime
    expected_candles: int
    actual_candles: int
    coverage_percentage: float
    first_candle_time: Optional[datetime] = None
    last_candle_time: Optional[datetime] = None
    has_gaps: bool


class CacheStatsResponse(BaseModel):
    """Response model for cache statistics"""
    total_candles: int
    total_gaps: int
    pending_gaps: int
    symbols: int
    sources: int
    intervals: int


# Dependency injection
def get_historical_service():
    return HistoricalDataService()


def get_cache_service():
    return CacheService()


@router.get("/candles", response_model=List[CandleDataResponse])
async def get_historical_candles(
    symbol: str = Query(..., description="Trading symbol (e.g., EUR_USD, BTCUSDT)"),
    interval: str = Query(..., description="Time interval (1m, 5m, 15m, 30m, 1h, 4h, 1d)"),
    start_time: Optional[datetime] = Query(None, description="Start time (ISO format)"),
    end_time: Optional[datetime] = Query(None, description="End time (ISO format)"),
    max_candles: Optional[int] = Query(None, description="Maximum number of candles to return"),
    source: str = Query("auto", description="Data source: oanda, bitunix, or auto"),
    use_cache: bool = Query(True, description="Use cached data if available"),
    fill_gaps: bool = Query(True, description="Fill data gaps by fetching from broker"),
    historical_service: HistoricalDataService = Depends(get_historical_service),
    cache_service: CacheService = Depends(get_cache_service)
):
    """
    Get historical candlestick data
    
    This endpoint provides historical OHLC data with intelligent caching:
    - If use_cache=True, checks local cache first
    - If fill_gaps=True, detects and fills missing data
    - Automatically chunks large requests
    - Supports both Oanda (forex) and Bitunix (crypto)
    """
    try:
        # Set default time range if not provided
        if not end_time:
            end_time = datetime.utcnow()
        if not start_time:
            # Default to 7 days ago
            start_time = end_time - timedelta(days=7)
        
        # Determine source if auto
        if source == "auto":
            if "_" in symbol:
                source = "oanda"
            else:
                source = "bitunix"
        
        # Check cache first if enabled
        if use_cache:
            cached_candles = cache_service.get_candles(
                symbol=symbol,
                interval=interval,
                source=source,
                start_time=start_time,
                end_time=end_time,
                limit=max_candles
            )
            
            if cached_candles:
                # Check if we have complete coverage
                coverage = cache_service.get_cache_coverage(
                    symbol=symbol,
                    interval=interval,
                    source=source,
                    start_time=start_time,
                    end_time=end_time
                )
                
                if coverage["coverage_percentage"] >= 95:  # 95% coverage threshold
                    logger.info(f"Returning {len(cached_candles)} candles from cache")
                    return [CandleDataResponse.from_orm(candle) for candle in cached_candles]
                
                # If fill_gaps is enabled, detect and fill gaps
                if fill_gaps and coverage["has_gaps"]:
                    gaps = cache_service.detect_gaps(
                        symbol=symbol,
                        interval=interval,
                        source=source,
                        start_time=start_time,
                        end_time=end_time
                    )
                    
                    if gaps:
                        logger.info(f"Detected {len(gaps)} gaps, fetching missing data")
                        
                        # Store gaps for tracking
                        cache_service.store_gaps(symbol, interval, source, gaps)
                        
                        # Fetch missing data for each gap
                        for gap_start, gap_end in gaps:
                            try:
                                request = HistoricalRequest(
                                    symbol=symbol,
                                    interval=interval,
                                    start_time=gap_start,
                                    end_time=gap_end,
                                    source=source
                                )
                                
                                new_candles = await historical_service.get_historical_data(request)
                                
                                if new_candles:
                                    # Store new candles in cache
                                    cache_service.store_candles(new_candles, symbol, interval, source)
                                    
                                    # Add to cached candles
                                    cached_candles.extend(new_candles)
                                    
                            except Exception as e:
                                logger.error(f"Error filling gap {gap_start} to {gap_end}: {e}")
                        
                        # Sort and limit
                        cached_candles.sort(key=lambda x: x.timestamp)
                        if max_candles:
                            cached_candles = cached_candles[-max_candles:]
                        
                        return [CandleDataResponse.from_orm(candle) for candle in cached_candles]
        
        # Fetch from broker if cache is disabled or incomplete
        logger.info(f"Fetching {symbol} {interval} data from {source}")
        
        request = HistoricalRequest(
            symbol=symbol,
            interval=interval,
            start_time=start_time,
            end_time=end_time,
            max_candles=max_candles,
            source=source
        )
        
        candles = await historical_service.get_historical_data(request)
        
        # Store in cache if enabled
        if use_cache and candles:
            cache_service.store_candles(candles, symbol, interval, source)
        
        return [CandleDataResponse.from_orm(candle) for candle in candles]
        
    except Exception as e:
        logger.error(f"Error getting historical candles: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/coverage", response_model=CacheCoverageResponse)
async def get_cache_coverage(
    symbol: str = Query(..., description="Trading symbol"),
    interval: str = Query(..., description="Time interval"),
    source: str = Query("auto", description="Data source"),
    start_time: Optional[datetime] = Query(None, description="Start time"),
    end_time: Optional[datetime] = Query(None, description="End time"),
    cache_service: CacheService = Depends(get_cache_service)
):
    """
    Get cache coverage information for a symbol/interval combination
    """
    try:
        # Set default time range
        if not end_time:
            end_time = datetime.utcnow()
        if not start_time:
            start_time = end_time - timedelta(days=7)
        
        # Determine source if auto
        if source == "auto":
            if "_" in symbol:
                source = "oanda"
            else:
                source = "bitunix"
        
        coverage = cache_service.get_cache_coverage(
            symbol=symbol,
            interval=interval,
            source=source,
            start_time=start_time,
            end_time=end_time
        )
        
        return CacheCoverageResponse(**coverage)
        
    except Exception as e:
        logger.error(f"Error getting cache coverage: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/gaps", response_model=List[dict])
async def get_pending_gaps(
    symbol: Optional[str] = Query(None, description="Filter by symbol"),
    interval: Optional[str] = Query(None, description="Filter by interval"),
    source: Optional[str] = Query(None, description="Filter by source"),
    cache_service: CacheService = Depends(get_cache_service)
):
    """
    Get pending data gaps that need to be filled
    """
    try:
        gaps = cache_service.get_pending_gaps(symbol=symbol, interval=interval, source=source)
        
        return [
            {
                "id": gap.id,
                "symbol": gap.symbol,
                "interval": gap.interval,
                "source": gap.source,
                "gap_start": gap.gap_start,
                "gap_end": gap.gap_end,
                "gap_size_minutes": gap.gap_size_minutes,
                "status": gap.status,
                "created_at": gap.created_at
            }
            for gap in gaps
        ]
        
    except Exception as e:
        logger.error(f"Error getting pending gaps: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/gaps/{gap_id}/fill")
async def fill_data_gap(
    gap_id: int,
    historical_service: HistoricalDataService = Depends(get_historical_service),
    cache_service: CacheService = Depends(get_cache_service)
):
    """
    Fill a specific data gap by fetching missing data
    """
    try:
        # Get the gap
        gaps = cache_service.get_pending_gaps()
        gap = next((g for g in gaps if g.id == gap_id), None)
        
        if not gap:
            raise HTTPException(status_code=404, detail="Gap not found")
        
        # Fetch data for the gap
        request = HistoricalRequest(
            symbol=gap.symbol,
            interval=gap.interval,
            start_time=gap.gap_start,
            end_time=gap.gap_end,
            source=gap.source
        )
        
        candles = await historical_service.get_historical_data(request)
        
        if candles:
            # Store in cache
            cache_service.store_candles(candles, gap.symbol, gap.interval, gap.source)
            
            # Mark gap as completed
            cache_service.mark_gap_completed(gap_id)
            
            return {"message": f"Filled gap {gap_id} with {len(candles)} candles"}
        else:
            return {"message": f"No data found for gap {gap_id}"}
        
    except Exception as e:
        logger.error(f"Error filling gap {gap_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats", response_model=CacheStatsResponse)
async def get_cache_stats(
    cache_service: CacheService = Depends(get_cache_service)
):
    """
    Get overall cache statistics
    """
    try:
        stats = cache_service.get_cache_stats()
        return CacheStatsResponse(**stats)
        
    except Exception as e:
        logger.error(f"Error getting cache stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/intervals")
async def get_available_intervals(
    historical_service: HistoricalDataService = Depends(get_historical_service)
):
    """
    Get available intervals for each broker
    """
    try:
        intervals = await historical_service.get_available_intervals()
        return intervals
        
    except Exception as e:
        logger.error(f"Error getting available intervals: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/limits")
async def get_broker_limits(
    historical_service: HistoricalDataService = Depends(get_historical_service)
):
    """
    Get broker-specific limits
    """
    try:
        limits = historical_service.get_broker_limits()
        return limits
        
    except Exception as e:
        logger.error(f"Error getting broker limits: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 