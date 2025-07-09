from sqlalchemy.orm import Session
from app.database import SessionLocal, engine
from app.models import Base, Account, Instrument, AccountType, InstrumentType
from app.config import settings
import logging

logger = logging.getLogger(__name__)


def init_db():
    """Initialize database with sample data"""
    db = SessionLocal()
    try:
        # Create tables
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created")
        
        # Check if data already exists
        if db.query(Account).first() or db.query(Instrument).first():
            logger.info("Database already contains data, skipping initialization")
            return
        
        # Create sample accounts
        sample_accounts = [
            Account(
                name="Demo Account 1",
                account_type=AccountType.PRACTICE,
                balance=10000.0,
                currency="USD"
            ),
            Account(
                name="Demo Account 2", 
                account_type=AccountType.PRACTICE,
                balance=5000.0,
                currency="USD"
            )
        ]
        
        for account in sample_accounts:
            db.add(account)
        
        # Create sample forex instruments
        forex_instruments = [
            Instrument(
                symbol="EUR_USD",
                name="Euro / US Dollar",
                instrument_type=InstrumentType.FOREX,
                base_currency="EUR",
                quote_currency="USD",
                min_quantity=0.01,
                max_quantity=1000000.0,
                tick_size=0.00001,
                is_active=True
            ),
            Instrument(
                symbol="GBP_USD",
                name="British Pound / US Dollar",
                instrument_type=InstrumentType.FOREX,
                base_currency="GBP",
                quote_currency="USD",
                min_quantity=0.01,
                max_quantity=1000000.0,
                tick_size=0.00001,
                is_active=True
            ),
            Instrument(
                symbol="USD_JPY",
                name="US Dollar / Japanese Yen",
                instrument_type=InstrumentType.FOREX,
                base_currency="USD",
                quote_currency="JPY",
                min_quantity=0.01,
                max_quantity=1000000.0,
                tick_size=0.01,
                is_active=True
            ),
            Instrument(
                symbol="USD_CHF",
                name="US Dollar / Swiss Franc",
                instrument_type=InstrumentType.FOREX,
                base_currency="USD",
                quote_currency="CHF",
                min_quantity=0.01,
                max_quantity=1000000.0,
                tick_size=0.00001,
                is_active=True
            ),
            Instrument(
                symbol="AUD_USD",
                name="Australian Dollar / US Dollar",
                instrument_type=InstrumentType.FOREX,
                base_currency="AUD",
                quote_currency="USD",
                min_quantity=0.01,
                max_quantity=1000000.0,
                tick_size=0.00001,
                is_active=True
            )
        ]
        
        # Create sample crypto instruments (Bitunix futures compatible)
        crypto_instruments = [
            Instrument(
                symbol="BTC_USDT",
                name="Bitcoin / USDT Futures",
                instrument_type=InstrumentType.CRYPTO,
                base_currency="BTC",
                quote_currency="USDT",
                min_quantity=0.001,
                max_quantity=1000.0,
                tick_size=0.01,
                is_active=True
            ),
            Instrument(
                symbol="ETH_USDT",
                name="Ethereum / USDT Futures",
                instrument_type=InstrumentType.CRYPTO,
                base_currency="ETH",
                quote_currency="USDT",
                min_quantity=0.01,
                max_quantity=10000.0,
                tick_size=0.01,
                is_active=True
            ),
            Instrument(
                symbol="SOL_USDT",
                name="Solana / USDT Futures",
                instrument_type=InstrumentType.CRYPTO,
                base_currency="SOL",
                quote_currency="USDT",
                min_quantity=0.1,
                max_quantity=100000.0,
                tick_size=0.001,
                is_active=True
            ),
            Instrument(
                symbol="ADA_USDT",
                name="Cardano / USDT Futures",
                instrument_type=InstrumentType.CRYPTO,
                base_currency="ADA",
                quote_currency="USDT",
                min_quantity=1.0,
                max_quantity=1000000.0,
                tick_size=0.0001,
                is_active=True
            ),
            Instrument(
                symbol="DOT_USDT",
                name="Polkadot / USDT Futures",
                instrument_type=InstrumentType.CRYPTO,
                base_currency="DOT",
                quote_currency="USDT",
                min_quantity=0.1,
                max_quantity=100000.0,
                tick_size=0.001,
                is_active=True
            ),
            Instrument(
                symbol="LINK_USDT",
                name="Chainlink / USDT Futures",
                instrument_type=InstrumentType.CRYPTO,
                base_currency="LINK",
                quote_currency="USDT",
                min_quantity=0.1,
                max_quantity=100000.0,
                tick_size=0.001,
                is_active=True
            ),
            Instrument(
                symbol="MATIC_USDT",
                name="Polygon / USDT Futures",
                instrument_type=InstrumentType.CRYPTO,
                base_currency="MATIC",
                quote_currency="USDT",
                min_quantity=1.0,
                max_quantity=1000000.0,
                tick_size=0.0001,
                is_active=True
            ),
            Instrument(
                symbol="AVAX_USDT",
                name="Avalanche / USDT Futures",
                instrument_type=InstrumentType.CRYPTO,
                base_currency="AVAX",
                quote_currency="USDT",
                min_quantity=0.1,
                max_quantity=100000.0,
                tick_size=0.001,
                is_active=True
            )
        ]
        
        # Add all instruments
        for instrument in forex_instruments + crypto_instruments:
            db.add(instrument)
        
        # Commit all changes
        db.commit()
        logger.info("Sample data initialized successfully")
        logger.info(f"Created {len(sample_accounts)} accounts")
        logger.info(f"Created {len(forex_instruments)} forex instruments")
        logger.info(f"Created {len(crypto_instruments)} crypto instruments")
        
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    init_db() 