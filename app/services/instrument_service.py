import asyncio
import logging
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import Instrument, InstrumentType
from app.services.price_service import PriceService
from app.config import settings

logger = logging.getLogger(__name__)


class InstrumentService:
    """Service for managing and synchronizing trading instruments"""
    
    def __init__(self):
        self.price_service = PriceService()
    
    async def sync_instruments_from_apis(self, db: Session) -> Dict[str, int]:
        """
        Synchronize instruments from OANDA and Bitunix APIs to the database
        
        Returns:
            Dict with counts of synced instruments by type
        """
        logger.info("Starting instrument synchronization from APIs...")
        
        synced_counts = {"forex": 0, "crypto": 0, "total": 0}
        
        try:
            # Get available instruments from APIs
            available_instruments = await self.price_service.get_available_instruments()
            
            # Sync forex instruments from OANDA
            if available_instruments.get("forex"):
                forex_count = await self._sync_forex_instruments(db, available_instruments["forex"])
                synced_counts["forex"] = forex_count
            
            # Sync crypto instruments from Bitunix
            if available_instruments.get("crypto"):
                crypto_count = await self._sync_crypto_instruments(db, available_instruments["crypto"])
                synced_counts["crypto"] = crypto_count
            
            synced_counts["total"] = synced_counts["forex"] + synced_counts["crypto"]
            
            logger.info(f"Instrument synchronization completed: {synced_counts}")
            return synced_counts
            
        except Exception as e:
            logger.error(f"Error during instrument synchronization: {e}")
            raise
    
    async def _sync_forex_instruments(self, db: Session, forex_symbols: List[str]) -> int:
        """Sync forex instruments from OANDA"""
        logger.info(f"Syncing {len(forex_symbols)} forex instruments...")
        
        synced_count = 0
        
        for symbol in forex_symbols:
            try:
                # Check if instrument already exists
                existing = db.query(Instrument).filter(Instrument.symbol == symbol).first()
                if existing:
                    continue
                
                # Create new forex instrument
                instrument = Instrument(
                    symbol=symbol,
                    name=self._format_forex_name(symbol),
                    instrument_type=InstrumentType.FOREX,
                    base_currency=symbol.split('_')[0],
                    quote_currency=symbol.split('_')[1],
                    min_quantity=0.01,
                    max_quantity=1000000.0,
                    tick_size=0.00001,
                    is_active=True
                )
                
                db.add(instrument)
                synced_count += 1
                
            except Exception as e:
                logger.error(f"Error syncing forex instrument {symbol}: {e}")
                continue
        
        db.commit()
        logger.info(f"Synced {synced_count} new forex instruments")
        return synced_count
    
    async def _sync_crypto_instruments(self, db: Session, crypto_symbols: List[str]) -> int:
        """Sync crypto instruments from Bitunix"""
        logger.info(f"Syncing {len(crypto_symbols)} crypto instruments...")
        
        synced_count = 0
        
        for symbol in crypto_symbols:
            try:
                # Check if instrument already exists
                existing = db.query(Instrument).filter(Instrument.symbol == symbol).first()
                if existing:
                    continue
                
                # Parse symbol (e.g., BTC_USDT -> BTC, USDT)
                parts = symbol.split('_')
                if len(parts) != 2:
                    continue
                
                base_currency, quote_currency = parts
                
                # Create new crypto instrument
                instrument = Instrument(
                    symbol=symbol,
                    name=self._format_crypto_name(symbol),
                    instrument_type=InstrumentType.CRYPTO,
                    base_currency=base_currency,
                    quote_currency=quote_currency,
                    min_quantity=self._get_crypto_min_quantity(base_currency),
                    max_quantity=1000000.0,
                    tick_size=self._get_crypto_tick_size(base_currency),
                    is_active=True
                )
                
                db.add(instrument)
                synced_count += 1
                
            except Exception as e:
                logger.error(f"Error syncing crypto instrument {symbol}: {e}")
                continue
        
        db.commit()
        logger.info(f"Synced {synced_count} new crypto instruments")
        return synced_count
    
    def _format_forex_name(self, symbol: str) -> str:
        """Format forex symbol into display name"""
        parts = symbol.split('_')
        if len(parts) == 2:
            return f"{parts[0]} / {parts[1]}"
        return symbol
    
    def _format_crypto_name(self, symbol: str) -> str:
        """Format crypto symbol into display name"""
        parts = symbol.split('_')
        if len(parts) == 2:
            return f"{parts[0]} / {parts[1]} Futures"
        return symbol
    
    def _get_crypto_min_quantity(self, base_currency: str) -> float:
        """Get minimum quantity for crypto instrument"""
        # Common minimum quantities for popular cryptocurrencies
        min_quantities = {
            'BTC': 0.001,
            'ETH': 0.01,
            'SOL': 0.1,
            'ADA': 1.0,
            'DOT': 0.1,
            'LINK': 0.1,
            'MATIC': 1.0,
            'AVAX': 0.1,
            'BNB': 0.01,
            'XRP': 1.0,
            'LTC': 0.01,
            'BCH': 0.01,
            'EOS': 0.1,
            'TRX': 1.0,
            'XLM': 1.0,
        }
        return min_quantities.get(base_currency, 0.01)
    
    def _get_crypto_tick_size(self, base_currency: str) -> float:
        """Get tick size for crypto instrument"""
        # Common tick sizes for popular cryptocurrencies
        tick_sizes = {
            'BTC': 0.01,
            'ETH': 0.01,
            'SOL': 0.001,
            'ADA': 0.0001,
            'DOT': 0.001,
            'LINK': 0.001,
            'MATIC': 0.0001,
            'AVAX': 0.001,
            'BNB': 0.01,
            'XRP': 0.0001,
            'LTC': 0.01,
            'BCH': 0.01,
            'EOS': 0.001,
            'TRX': 0.0001,
            'XLM': 0.0001,
        }
        return tick_sizes.get(base_currency, 0.00001)
    
    async def get_instrument_counts(self, db: Session) -> Dict[str, int]:
        """Get counts of instruments by type"""
        total = db.query(Instrument).count()
        forex = db.query(Instrument).filter(Instrument.instrument_type == InstrumentType.FOREX).count()
        crypto = db.query(Instrument).filter(Instrument.instrument_type == InstrumentType.CRYPTO).count()
        equity = db.query(Instrument).filter(Instrument.instrument_type == InstrumentType.EQUITY).count()
        
        return {
            "total": total,
            "forex": forex,
            "crypto": crypto,
            "equity": equity
        }
    
    async def close(self):
        """Close the price service"""
        await self.price_service.close()


# Global instance
instrument_service = InstrumentService() 