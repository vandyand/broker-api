"""
Cache Service for Historical Data
Manages storage, retrieval, and gap detection for historical candlestick data
"""

import logging
from datetime import datetime, timedelta
from typing import List, Optional, Tuple, Dict
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func

from app.models_pkg.historical_data import CandleData, DataGap, CacheMetadata
from app.services.historical_data_service import CandleData as ServiceCandleData
from app.database import get_db

logger = logging.getLogger(__name__)


class CacheService:
    """Service for managing historical data caching"""
    
    def __init__(self):
        self.db = next(get_db())
    
    def __del__(self):
        if hasattr(self, 'db'):
            self.db.close()
    
    def store_candles(self, candles: List[ServiceCandleData], symbol: str, 
                     interval: str, source: str) -> int:
        """
        Store candles in the database
        
        Args:
            candles: List of CandleData objects from the service
            symbol: Trading symbol
            interval: Time interval
            source: Data source (oanda/bitunix)
            
        Returns:
            Number of candles stored
        """
        try:
            stored_count = 0
            
            for candle in candles:
                # Check if candle already exists
                existing = self.db.query(CandleData).filter(
                    and_(
                        CandleData.symbol == symbol,
                        CandleData.interval == interval,
                        CandleData.source == source,
                        CandleData.timestamp == candle.timestamp
                    )
                ).first()
                
                if not existing:
                    # Create new candle record
                    db_candle = CandleData(
                        symbol=symbol,
                        interval=interval,
                        source=source,
                        timestamp=candle.timestamp,
                        open_price=candle.open,
                        high_price=candle.high,
                        low_price=candle.low,
                        close_price=candle.close,
                        volume=candle.volume
                    )
                    self.db.add(db_candle)
                    stored_count += 1
            
            self.db.commit()
            logger.info(f"Stored {stored_count} new candles for {symbol} {interval} from {source}")
            
            # Update cache metadata
            self._update_cache_metadata(symbol, interval, source)
            
            return stored_count
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error storing candles: {e}")
            raise
    
    def get_candles(self, symbol: str, interval: str, source: str,
                   start_time: Optional[datetime] = None,
                   end_time: Optional[datetime] = None,
                   limit: Optional[int] = None) -> List[ServiceCandleData]:
        """
        Retrieve candles from cache
        
        Args:
            symbol: Trading symbol
            interval: Time interval
            source: Data source
            start_time: Start time filter
            end_time: End time filter
            limit: Maximum number of candles to return
            
        Returns:
            List of CandleData objects
        """
        try:
            query = self.db.query(CandleData).filter(
                and_(
                    CandleData.symbol == symbol,
                    CandleData.interval == interval,
                    CandleData.source == source
                )
            )
            
            if start_time:
                query = query.filter(CandleData.timestamp >= start_time)
            if end_time:
                query = query.filter(CandleData.timestamp <= end_time)
            
            # Order by timestamp descending (most recent first)
            query = query.order_by(desc(CandleData.timestamp))
            
            if limit:
                query = query.limit(limit)
            
            db_candles = query.all()
            
            # Convert to service format
            candles = []
            for db_candle in db_candles:
                candle = ServiceCandleData(
                    timestamp=db_candle.timestamp,
                    open=db_candle.open_price,
                    high=db_candle.high_price,
                    low=db_candle.low_price,
                    close=db_candle.close_price,
                    volume=db_candle.volume,
                    source=db_candle.source
                )
                candles.append(candle)
            
            # Reverse to get chronological order
            candles.reverse()
            
            logger.info(f"Retrieved {len(candles)} candles from cache for {symbol} {interval}")
            return candles
            
        except Exception as e:
            logger.error(f"Error retrieving candles from cache: {e}")
            raise
    
    def get_cache_coverage(self, symbol: str, interval: str, source: str,
                          start_time: datetime, end_time: datetime) -> Dict:
        """
        Get cache coverage information for a time range
        
        Args:
            symbol: Trading symbol
            interval: Time interval
            source: Data source
            start_time: Start time
            end_time: End time
            
        Returns:
            Dictionary with coverage information
        """
        try:
            # Get total expected candles
            interval_minutes = self._get_interval_minutes(interval)
            total_minutes = int((end_time - start_time).total_seconds() / 60)
            expected_candles = total_minutes // interval_minutes
            
            # Get actual candles in range
            actual_candles = self.db.query(CandleData).filter(
                and_(
                    CandleData.symbol == symbol,
                    CandleData.interval == interval,
                    CandleData.source == source,
                    CandleData.timestamp >= start_time,
                    CandleData.timestamp <= end_time
                )
            ).count()
            
            # Get first and last candle in range
            first_candle = self.db.query(CandleData).filter(
                and_(
                    CandleData.symbol == symbol,
                    CandleData.interval == interval,
                    CandleData.source == source,
                    CandleData.timestamp >= start_time,
                    CandleData.timestamp <= end_time
                )
            ).order_by(CandleData.timestamp).first()
            
            last_candle = self.db.query(CandleData).filter(
                and_(
                    CandleData.symbol == symbol,
                    CandleData.interval == interval,
                    CandleData.source == source,
                    CandleData.timestamp >= start_time,
                    CandleData.timestamp <= end_time
                )
            ).order_by(desc(CandleData.timestamp)).first()
            
            coverage = {
                "symbol": symbol,
                "interval": interval,
                "source": source,
                "start_time": start_time,
                "end_time": end_time,
                "expected_candles": expected_candles,
                "actual_candles": actual_candles,
                "coverage_percentage": (actual_candles / expected_candles * 100) if expected_candles > 0 else 0,
                "first_candle_time": first_candle.timestamp if first_candle else None,
                "last_candle_time": last_candle.timestamp if last_candle else None,
                "has_gaps": actual_candles < expected_candles
            }
            
            return coverage
            
        except Exception as e:
            logger.error(f"Error getting cache coverage: {e}")
            raise
    
    def detect_gaps(self, symbol: str, interval: str, source: str,
                   start_time: datetime, end_time: datetime) -> List[Tuple[datetime, datetime]]:
        """
        Detect gaps in cached data
        
        Args:
            symbol: Trading symbol
            interval: Time interval
            source: Data source
            start_time: Start time
            end_time: End time
            
        Returns:
            List of (gap_start, gap_end) tuples
        """
        try:
            # Get all candles in range, ordered by timestamp
            candles = self.db.query(CandleData).filter(
                and_(
                    CandleData.symbol == symbol,
                    CandleData.interval == interval,
                    CandleData.source == source,
                    CandleData.timestamp >= start_time,
                    CandleData.timestamp <= end_time
                )
            ).order_by(CandleData.timestamp).all()
            
            if not candles:
                # No data at all - entire range is a gap
                return [(start_time, end_time)]
            
            gaps = []
            interval_minutes = self._get_interval_minutes(interval)
            
            # Check gap before first candle
            first_candle_time = candles[0].timestamp
            if first_candle_time > start_time + timedelta(minutes=interval_minutes):
                gaps.append((start_time, first_candle_time))
            
            # Check gaps between candles
            for i in range(len(candles) - 1):
                current_time = candles[i].timestamp
                next_time = candles[i + 1].timestamp
                expected_next = current_time + timedelta(minutes=interval_minutes)
                
                if next_time > expected_next + timedelta(minutes=interval_minutes):
                    gaps.append((expected_next, next_time))
            
            # Check gap after last candle
            last_candle_time = candles[-1].timestamp
            if last_candle_time < end_time - timedelta(minutes=interval_minutes):
                gaps.append((last_candle_time + timedelta(minutes=interval_minutes), end_time))
            
            return gaps
            
        except Exception as e:
            logger.error(f"Error detecting gaps: {e}")
            raise
    
    def store_gaps(self, symbol: str, interval: str, source: str,
                  gaps: List[Tuple[datetime, datetime]]) -> int:
        """
        Store detected gaps in the database
        
        Args:
            symbol: Trading symbol
            interval: Time interval
            source: Data source
            gaps: List of (gap_start, gap_end) tuples
            
        Returns:
            Number of gaps stored
        """
        try:
            stored_count = 0
            
            for gap_start, gap_end in gaps:
                # Check if gap already exists
                existing = self.db.query(DataGap).filter(
                    and_(
                        DataGap.symbol == symbol,
                        DataGap.interval == interval,
                        DataGap.source == source,
                        DataGap.gap_start == gap_start,
                        DataGap.gap_end == gap_end
                    )
                ).first()
                
                if not existing:
                    gap_size = int((gap_end - gap_start).total_seconds() / 60)
                    gap = DataGap(
                        symbol=symbol,
                        interval=interval,
                        source=source,
                        gap_start=gap_start,
                        gap_end=gap_end,
                        gap_size_minutes=gap_size,
                        status="pending"
                    )
                    self.db.add(gap)
                    stored_count += 1
            
            self.db.commit()
            logger.info(f"Stored {stored_count} new gaps for {symbol} {interval}")
            return stored_count
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error storing gaps: {e}")
            raise
    
    def get_pending_gaps(self, symbol: str = None, interval: str = None, 
                        source: str = None) -> List[DataGap]:
        """
        Get pending gaps that need to be filled
        
        Args:
            symbol: Optional symbol filter
            interval: Optional interval filter
            source: Optional source filter
            
        Returns:
            List of DataGap objects
        """
        try:
            query = self.db.query(DataGap).filter(DataGap.status == "pending")
            
            if symbol:
                query = query.filter(DataGap.symbol == symbol)
            if interval:
                query = query.filter(DataGap.interval == interval)
            if source:
                query = query.filter(DataGap.source == source)
            
            return query.order_by(DataGap.gap_start).all()
            
        except Exception as e:
            logger.error(f"Error getting pending gaps: {e}")
            raise
    
    def mark_gap_completed(self, gap_id: int):
        """Mark a gap as completed"""
        try:
            gap = self.db.query(DataGap).filter(DataGap.id == gap_id).first()
            if gap:
                gap.status = "completed"
                gap.updated_at = datetime.utcnow()
                self.db.commit()
                logger.info(f"Marked gap {gap_id} as completed")
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error marking gap as completed: {e}")
            raise
    
    def _update_cache_metadata(self, symbol: str, interval: str, source: str):
        """Update cache metadata for a symbol/interval combination"""
        try:
            # Get or create metadata record
            metadata = self.db.query(CacheMetadata).filter(
                and_(
                    CacheMetadata.symbol == symbol,
                    CacheMetadata.interval == interval,
                    CacheMetadata.source == source
                )
            ).first()
            
            if not metadata:
                metadata = CacheMetadata(
                    symbol=symbol,
                    interval=interval,
                    source=source
                )
                self.db.add(metadata)
            
            # Update statistics
            stats = self.db.query(
                func.min(CandleData.timestamp).label('first_time'),
                func.max(CandleData.timestamp).label('last_time'),
                func.count(CandleData.id).label('total_count')
            ).filter(
                and_(
                    CandleData.symbol == symbol,
                    CandleData.interval == interval,
                    CandleData.source == source
                )
            ).first()
            
            if stats:
                metadata.first_candle_time = stats.first_time
                metadata.last_candle_time = stats.last_time
                metadata.total_candles = stats.total_count
                metadata.last_fetch_time = datetime.utcnow()
                metadata.updated_at = datetime.utcnow()
            
            self.db.commit()
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating cache metadata: {e}")
    
    def _get_interval_minutes(self, interval: str) -> int:
        """Get minutes for an interval"""
        interval_map = {
            "1m": 1,
            "5m": 5,
            "15m": 15,
            "30m": 30,
            "1h": 60,
            "4h": 240,
            "1d": 1440
        }
        return interval_map.get(interval, 1)
    
    def get_cache_stats(self) -> Dict:
        """Get overall cache statistics"""
        try:
            stats = {
                "total_candles": self.db.query(CandleData).count(),
                "total_gaps": self.db.query(DataGap).count(),
                "pending_gaps": self.db.query(DataGap).filter(DataGap.status == "pending").count(),
                "symbols": self.db.query(CandleData.symbol).distinct().count(),
                "sources": self.db.query(CandleData.source).distinct().count(),
                "intervals": self.db.query(CandleData.interval).distinct().count()
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            raise 