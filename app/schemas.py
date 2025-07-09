from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from app.models import AccountType, InstrumentType, OrderType, OrderSide, OrderStatus


# Account Schemas
class AccountBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    account_type: AccountType = AccountType.PRACTICE
    balance: float = Field(0.0, ge=0)
    currency: str = Field("USD", min_length=3, max_length=3)


class AccountCreate(AccountBase):
    pass


class AccountUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    balance: Optional[float] = Field(None, ge=0)
    currency: Optional[str] = Field(None, min_length=3, max_length=3)


class Account(AccountBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# Instrument Schemas
class InstrumentBase(BaseModel):
    symbol: str = Field(..., min_length=1, max_length=20)
    name: str = Field(..., min_length=1, max_length=100)
    instrument_type: InstrumentType
    base_currency: str = Field(..., min_length=1, max_length=10)
    quote_currency: str = Field(..., min_length=1, max_length=10)
    min_quantity: float = Field(0.01, gt=0)
    max_quantity: Optional[float] = Field(None, gt=0)
    tick_size: float = Field(0.00001, gt=0)
    is_active: bool = True


class InstrumentCreate(InstrumentBase):
    pass


class InstrumentUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    min_quantity: Optional[float] = Field(None, gt=0)
    max_quantity: Optional[float] = Field(None, gt=0)
    tick_size: Optional[float] = Field(None, gt=0)
    is_active: Optional[bool] = None


class Instrument(InstrumentBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


# Position Schemas
class PositionBase(BaseModel):
    account_id: int
    instrument_id: int
    quantity: float = 0.0
    average_price: float = 0.0
    unrealized_pnl: float = 0.0
    realized_pnl: float = 0.0


class PositionCreate(PositionBase):
    pass


class PositionUpdate(BaseModel):
    quantity: Optional[float] = None
    average_price: Optional[float] = None
    unrealized_pnl: Optional[float] = None
    realized_pnl: Optional[float] = None


class Position(PositionBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# Order Schemas
class OrderBase(BaseModel):
    account_id: int
    instrument_id: int
    order_type: OrderType
    side: OrderSide
    quantity: float = Field(..., gt=0)
    price: Optional[float] = Field(None, gt=0)
    stop_price: Optional[float] = Field(None, gt=0)
    notes: Optional[str] = None


class OrderCreate(OrderBase):
    pass


class OrderUpdate(BaseModel):
    price: Optional[float] = Field(None, gt=0)
    stop_price: Optional[float] = Field(None, gt=0)
    notes: Optional[str] = None


class Order(OrderBase):
    id: int
    status: OrderStatus
    filled_quantity: float
    average_fill_price: float
    commission: float
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# Trade Schemas
class TradeBase(BaseModel):
    order_id: int
    account_id: int
    instrument_id: int
    side: OrderSide
    quantity: float = Field(..., gt=0)
    price: float = Field(..., gt=0)
    commission: float = 0.0
    realized_pnl: float = 0.0


class TradeCreate(TradeBase):
    pass


class Trade(TradeBase):
    id: int
    executed_at: datetime
    
    class Config:
        from_attributes = True


# Price Schemas
class PriceData(BaseModel):
    symbol: str
    bid: float
    ask: float
    timestamp: datetime
    source: str


# Response Schemas
class StandardResponse(BaseModel):
    success: bool
    message: str
    data: Optional[dict] = None


class PaginatedResponse(BaseModel):
    items: List[dict]
    total: int
    page: int
    size: int
    pages: int 