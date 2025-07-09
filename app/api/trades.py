from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models import Trade, Account, Instrument, Order
from app.schemas import Trade as TradeSchema, StandardResponse, PaginatedResponse

router = APIRouter(prefix="/trades", tags=["trades"])


@router.get("/", response_model=PaginatedResponse)
def get_trades(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    account_id: Optional[int] = None,
    instrument_id: Optional[int] = None,
    order_id: Optional[int] = None,
    side: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get all trades with pagination and optional filtering"""
    query = db.query(Trade)
    
    if account_id:
        query = query.filter(Trade.account_id == account_id)
    if instrument_id:
        query = query.filter(Trade.instrument_id == instrument_id)
    if order_id:
        query = query.filter(Trade.order_id == order_id)
    if side:
        query = query.filter(Trade.side == side)
    
    total = query.count()
    trades = query.order_by(Trade.executed_at.desc()).offset(skip).limit(limit).all()
    
    return PaginatedResponse(
        items=[TradeSchema.from_orm(trade).dict() for trade in trades],
        total=total,
        page=skip // limit + 1,
        size=limit,
        pages=(total + limit - 1) // limit
    )


@router.get("/{trade_id}", response_model=TradeSchema)
def get_trade(trade_id: int, db: Session = Depends(get_db)):
    """Get a specific trade by ID"""
    trade = db.query(Trade).filter(Trade.id == trade_id).first()
    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found")
    return trade


@router.get("/account/{account_id}", response_model=List[TradeSchema])
def get_account_trades(account_id: int, db: Session = Depends(get_db)):
    """Get all trades for a specific account"""
    # Validate account exists
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    trades = db.query(Trade).filter(Trade.account_id == account_id).order_by(Trade.executed_at.desc()).all()
    return trades


@router.get("/order/{order_id}", response_model=List[TradeSchema])
def get_order_trades(order_id: int, db: Session = Depends(get_db)):
    """Get all trades for a specific order"""
    # Validate order exists
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    trades = db.query(Trade).filter(Trade.order_id == order_id).order_by(Trade.executed_at.desc()).all()
    return trades


@router.get("/instrument/{instrument_id}", response_model=List[TradeSchema])
def get_instrument_trades(instrument_id: int, db: Session = Depends(get_db)):
    """Get all trades for a specific instrument"""
    # Validate instrument exists
    instrument = db.query(Instrument).filter(Instrument.id == instrument_id).first()
    if not instrument:
        raise HTTPException(status_code=404, detail="Instrument not found")
    
    trades = db.query(Trade).filter(Trade.instrument_id == instrument_id).order_by(Trade.executed_at.desc()).all()
    return trades 