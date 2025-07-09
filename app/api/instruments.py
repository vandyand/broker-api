from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models import Instrument
from app.schemas import InstrumentCreate, InstrumentUpdate, Instrument as InstrumentSchema, StandardResponse, PaginatedResponse

router = APIRouter(prefix="/instruments", tags=["instruments"])


@router.post("/", response_model=InstrumentSchema)
def create_instrument(instrument: InstrumentCreate, db: Session = Depends(get_db)):
    """Create a new trading instrument"""
    # Check if instrument symbol already exists
    existing_instrument = db.query(Instrument).filter(Instrument.symbol == instrument.symbol).first()
    if existing_instrument:
        raise HTTPException(status_code=400, detail="Instrument symbol already exists")
    
    db_instrument = Instrument(**instrument.dict())
    db.add(db_instrument)
    db.commit()
    db.refresh(db_instrument)
    return db_instrument


@router.get("/", response_model=PaginatedResponse)
def get_instruments(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    instrument_type: Optional[str] = None,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """Get all instruments with pagination and optional filtering"""
    query = db.query(Instrument)
    
    if instrument_type:
        query = query.filter(Instrument.instrument_type == instrument_type)
    
    if is_active is not None:
        query = query.filter(Instrument.is_active == is_active)
    
    total = query.count()
    instruments = query.offset(skip).limit(limit).all()
    
    return PaginatedResponse(
        items=[InstrumentSchema.from_orm(instrument).dict() for instrument in instruments],
        total=total,
        page=skip // limit + 1,
        size=limit,
        pages=(total + limit - 1) // limit
    )


@router.get("/{instrument_id}", response_model=InstrumentSchema)
def get_instrument(instrument_id: int, db: Session = Depends(get_db)):
    """Get a specific instrument by ID"""
    instrument = db.query(Instrument).filter(Instrument.id == instrument_id).first()
    if not instrument:
        raise HTTPException(status_code=404, detail="Instrument not found")
    return instrument


@router.get("/symbol/{symbol}", response_model=InstrumentSchema)
def get_instrument_by_symbol(symbol: str, db: Session = Depends(get_db)):
    """Get a specific instrument by symbol"""
    instrument = db.query(Instrument).filter(Instrument.symbol == symbol).first()
    if not instrument:
        raise HTTPException(status_code=404, detail="Instrument not found")
    return instrument


@router.put("/{instrument_id}", response_model=InstrumentSchema)
def update_instrument(instrument_id: int, instrument_update: InstrumentUpdate, db: Session = Depends(get_db)):
    """Update an existing instrument"""
    db_instrument = db.query(Instrument).filter(Instrument.id == instrument_id).first()
    if not db_instrument:
        raise HTTPException(status_code=404, detail="Instrument not found")
    
    # Update fields
    update_data = instrument_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_instrument, field, value)
    
    db.commit()
    db.refresh(db_instrument)
    return db_instrument


@router.delete("/{instrument_id}", response_model=StandardResponse)
def delete_instrument(instrument_id: int, db: Session = Depends(get_db)):
    """Delete an instrument"""
    db_instrument = db.query(Instrument).filter(Instrument.id == instrument_id).first()
    if not db_instrument:
        raise HTTPException(status_code=404, detail="Instrument not found")
    
    # Check if instrument has any positions or orders
    if db_instrument.positions or db_instrument.orders:
        raise HTTPException(status_code=400, detail="Cannot delete instrument with active positions or orders")
    
    db.delete(db_instrument)
    db.commit()
    
    return StandardResponse(success=True, message="Instrument deleted successfully") 