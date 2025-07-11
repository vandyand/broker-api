from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models import Instrument, Position, Account
from app.schemas import PriceData, StandardResponse
from app.services.price_service import price_service

router = APIRouter(prefix="/prices", tags=["prices"])


@router.get("/{symbol}", response_model=PriceData)
async def get_price(symbol: str, db: Session = Depends(get_db)):
    """Get current price for a specific symbol"""
    # First try to get instrument from database
    instrument = db.query(Instrument).filter(Instrument.symbol == symbol).first()
    
    if instrument:
        # Use database instrument type
        instrument_type = instrument.instrument_type.value
    else:
        # Try to determine instrument type automatically
        instrument_type = await price_service.get_instrument_type(symbol)
        if not instrument_type:
            raise HTTPException(status_code=404, detail="Instrument not found")
    
    price_data = await price_service.get_price(symbol, instrument_type)
    if not price_data:
        raise HTTPException(status_code=404, detail="Price not available")
    
    return price_data


@router.get("/instrument/{instrument_id}", response_model=PriceData)
async def get_price_by_instrument_id(instrument_id: int, db: Session = Depends(get_db)):
    """Get current price for a specific instrument by ID"""
    instrument = db.query(Instrument).filter(Instrument.id == instrument_id).first()
    if not instrument:
        raise HTTPException(status_code=404, detail="Instrument not found")
    
    price_data = await price_service.get_price(instrument.symbol, instrument.instrument_type.value)
    if not price_data:
        raise HTTPException(status_code=404, detail="Price not available")
    
    return price_data


@router.post("/batch", response_model=List[PriceData])
async def get_prices_batch(symbols: List[dict], db: Session = Depends(get_db)):
    """Get current prices for multiple symbols"""
    # Validate symbols and get instrument types
    validated_symbols = []
    for symbol_info in symbols:
        if 'symbol' not in symbol_info:
            raise HTTPException(status_code=400, detail="Symbol is required for each item")
        
        symbol = symbol_info['symbol']
        
        # First try to get instrument from database
        instrument = db.query(Instrument).filter(Instrument.symbol == symbol).first()
        
        if instrument:
            # Use database instrument type
            instrument_type = instrument.instrument_type.value
        else:
            # Try to determine instrument type automatically
            instrument_type = await price_service.get_instrument_type(symbol)
            if not instrument_type:
                raise HTTPException(status_code=404, detail=f"Instrument not found for symbol: {symbol}")
        
        validated_symbols.append({
            'symbol': symbol,
            'instrument_type': instrument_type
        })
    
    prices = await price_service.get_prices_batch(validated_symbols)
    return prices


@router.get("/account/{account_id}/positions", response_model=List[PriceData])
async def get_account_position_prices(account_id: int, db: Session = Depends(get_db)):
    """Get current prices for all instruments in an account's positions"""
    
    # Validate account exists
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    # Get all positions for the account
    positions = db.query(Position).filter(Position.account_id == account_id).all()
    
    if not positions:
        return []
    
    # Get unique instruments from positions
    instrument_ids = list(set([pos.instrument_id for pos in positions]))
    instruments = db.query(Instrument).filter(Instrument.id.in_(instrument_ids)).all()
    
    # Prepare symbols for batch price fetch
    symbols = [{'symbol': inst.symbol, 'instrument_type': inst.instrument_type.value} for inst in instruments]
    
    prices = await price_service.get_prices_batch(symbols)
    return prices


@router.get("/instruments/available", response_model=dict)
async def get_available_instruments():
    """Get all available instruments from OANDA and Bitunix"""
    instruments = await price_service.get_available_instruments()
    return {
        "forex": instruments["forex"],
        "crypto": instruments["crypto"],
        "total_forex": len(instruments["forex"]),
        "total_crypto": len(instruments["crypto"]),
        "total": len(instruments["forex"]) + len(instruments["crypto"])
    } 