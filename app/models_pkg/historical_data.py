"""
Database models for historical candlestick data
"""

from sqlalchemy import Column, Integer, Float, String, DateTime, Index, Text
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


class CandleData(Base):
    """Database model for storing candlestick data"""
    __tablename__ = "candle_data"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Symbol and interval
    symbol = Column(String(20), nullable=False, index=True)
    interval = Column(String(10), nullable=False, index=True)
    source = Column(String(20), nullable=False, index=True)  # "oanda" or "bitunix"
    
    # Timestamp
    timestamp = Column(DateTime, nullable=False, index=True)
    
    # OHLC data
    open_price = Column(Float, nullable=False)
    high_price = Column(Float, nullable=False)
    low_price = Column(Float, nullable=False)
    close_price = Column(Float, nullable=False)
    
    # Volume (optional)
    volume = Column(Float, nullable=True)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Composite indexes for efficient queries
    __table_args__ = (
        Index('idx_symbol_interval_timestamp', 'symbol', 'interval', 'timestamp'),
        Index('idx_source_symbol_interval', 'source', 'symbol', 'interval'),
        Index('idx_timestamp_desc', 'timestamp', postgresql_ops={'timestamp': 'DESC'}),
    )
    
    def __repr__(self):
        return f"<CandleData(symbol='{self.symbol}', interval='{self.interval}', timestamp='{self.timestamp}')>"


class DataGap(Base):
    """Model to track data gaps for efficient refetching"""
    __tablename__ = "data_gaps"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Symbol and interval
    symbol = Column(String(20), nullable=False, index=True)
    interval = Column(String(10), nullable=False, index=True)
    source = Column(String(20), nullable=False, index=True)
    
    # Gap time range
    gap_start = Column(DateTime, nullable=False, index=True)
    gap_end = Column(DateTime, nullable=False, index=True)
    
    # Gap size in minutes
    gap_size_minutes = Column(Integer, nullable=False)
    
    # Status
    status = Column(String(20), default="pending")  # "pending", "fetching", "completed", "failed"
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Composite indexes
    __table_args__ = (
        Index('idx_gap_symbol_interval_status', 'symbol', 'interval', 'status'),
        Index('idx_gap_time_range', 'gap_start', 'gap_end'),
    )
    
    def __repr__(self):
        return f"<DataGap(symbol='{self.symbol}', interval='{self.interval}', gap_start='{self.gap_start}', gap_end='{self.gap_end}')>"


class CacheMetadata(Base):
    """Model to track cache metadata and statistics"""
    __tablename__ = "cache_metadata"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Symbol and interval
    symbol = Column(String(20), nullable=False, index=True)
    interval = Column(String(10), nullable=False, index=True)
    source = Column(String(20), nullable=False, index=True)
    
    # Cache statistics
    first_candle_time = Column(DateTime, nullable=True)
    last_candle_time = Column(DateTime, nullable=True)
    total_candles = Column(Integer, default=0)
    
    # Last fetch information
    last_fetch_time = Column(DateTime, nullable=True)
    last_fetch_count = Column(Integer, default=0)
    
    # Cache health
    is_complete = Column(String(5), default="false")  # "true" or "false"
    last_health_check = Column(DateTime, nullable=True)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Composite indexes
    __table_args__ = (
        Index('idx_metadata_symbol_interval', 'symbol', 'interval'),
        Index('idx_metadata_last_fetch', 'last_fetch_time'),
    )
    
    def __repr__(self):
        return f"<CacheMetadata(symbol='{self.symbol}', interval='{self.interval}', total_candles={self.total_candles})>" 