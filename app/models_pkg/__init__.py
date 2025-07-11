# Models package
import enum

class AccountType(str, enum.Enum):
    PRACTICE = "practice"
    LIVE = "live"

class InstrumentType(str, enum.Enum):
    FOREX = "forex"
    CRYPTO = "crypto"
    EQUITY = "equity"
    FUTURE = "future"

class OrderType(str, enum.Enum):
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"

class OrderSide(str, enum.Enum):
    BUY = "buy"
    SELL = "sell"

class OrderStatus(str, enum.Enum):
    PENDING = "pending"
    FILLED = "filled"
    PARTIALLY_FILLED = "partially_filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"

__all__ = [
    'AccountType', 'InstrumentType', 'OrderType', 'OrderSide', 'OrderStatus'
] 