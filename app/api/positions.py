from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models import Position, Account, Instrument
from app.schemas import PositionCreate, PositionUpdate, Position as PositionSchema, StandardResponse, PaginatedResponse
from app.services.trading_service import trading_service

router = APIRouter(prefix="/positions", tags=["positions"])


@router.post("/", response_model=PositionSchema)
def create_position(position: PositionCreate, db: Session = Depends(get_db)):
    """Create a new position"""
    # Validate account exists
    account = db.query(Account).filter(Account.id == position.account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    # Validate instrument exists
    instrument = db.query(Instrument).filter(Instrument.id == position.instrument_id).first()
    if not instrument:
        raise HTTPException(status_code=404, detail="Instrument not found")
    
    # Check if position already exists for this account and instrument
    existing_position = db.query(Position).filter(
        Position.account_id == position.account_id,
        Position.instrument_id == position.instrument_id
    ).first()
    
    if existing_position:
        raise HTTPException(status_code=400, detail="Position already exists for this account and instrument")
    
    db_position = Position(**position.dict())
    db.add(db_position)
    db.commit()
    db.refresh(db_position)
    return db_position


@router.get("/", response_model=PaginatedResponse)
def get_positions(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    account_id: Optional[int] = None,
    instrument_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Get all positions with pagination and optional filtering"""
    query = db.query(Position)
    
    if account_id:
        query = query.filter(Position.account_id == account_id)
    if instrument_id:
        query = query.filter(Position.instrument_id == instrument_id)
    
    total = query.count()
    positions = query.offset(skip).limit(limit).all()
    
    return PaginatedResponse(
        items=[PositionSchema.from_orm(position).dict() for position in positions],
        total=total,
        page=skip // limit + 1,
        size=limit,
        pages=(total + limit - 1) // limit
    )


@router.get("/{position_id}", response_model=PositionSchema)
def get_position(position_id: int, db: Session = Depends(get_db)):
    """Get a specific position by ID"""
    position = db.query(Position).filter(Position.id == position_id).first()
    if not position:
        raise HTTPException(status_code=404, detail="Position not found")
    return position


@router.get("/account/{account_id}", response_model=List[PositionSchema])
def get_account_positions(account_id: int, db: Session = Depends(get_db)):
    """Get all positions for a specific account"""
    # Validate account exists
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    positions = db.query(Position).filter(Position.account_id == account_id).all()
    return positions


@router.put("/{position_id}", response_model=PositionSchema)
def update_position(position_id: int, position_update: PositionUpdate, db: Session = Depends(get_db)):
    """Update an existing position"""
    db_position = db.query(Position).filter(Position.id == position_id).first()
    if not db_position:
        raise HTTPException(status_code=404, detail="Position not found")
    
    # Update fields
    update_data = position_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_position, field, value)
    
    db.commit()
    db.refresh(db_position)
    return db_position


@router.delete("/{position_id}", response_model=StandardResponse)
def delete_position(position_id: int, db: Session = Depends(get_db)):
    """Delete a position"""
    db_position = db.query(Position).filter(Position.id == position_id).first()
    if not db_position:
        raise HTTPException(status_code=404, detail="Position not found")
    
    # Only allow deletion of zero positions
    if db_position.quantity != 0:
        raise HTTPException(status_code=400, detail="Can only delete positions with zero quantity")
    
    db.delete(db_position)
    db.commit()
    
    return StandardResponse(success=True, message="Position deleted successfully")


@router.post("/{position_id}/update-pnl", response_model=StandardResponse)
async def update_position_pnl(position_id: int, db: Session = Depends(get_db)):
    """Update unrealized P&L for a position"""
    db_position = db.query(Position).filter(Position.id == position_id).first()
    if not db_position:
        raise HTTPException(status_code=404, detail="Position not found")
    
    await trading_service.update_position_pnl(db, db_position)
    
    return StandardResponse(success=True, message="Position P&L updated successfully")


@router.post("/account/{account_id}/update-all-pnl", response_model=StandardResponse)
async def update_all_account_positions_pnl(account_id: int, db: Session = Depends(get_db)):
    """Update unrealized P&L for all positions in an account"""
    # Validate account exists
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    positions = db.query(Position).filter(Position.account_id == account_id).all()
    
    for position in positions:
        await trading_service.update_position_pnl(db, position)
    
    return StandardResponse(success=True, message=f"Updated P&L for {len(positions)} positions") 