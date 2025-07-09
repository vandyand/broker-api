from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models import Order, Account, Instrument, OrderStatus
from app.schemas import OrderCreate, OrderUpdate, Order as OrderSchema, StandardResponse, PaginatedResponse
from app.services.trading_service import trading_service

router = APIRouter(prefix="/orders", tags=["orders"])


@router.post("/", response_model=OrderSchema)
async def create_order(order: OrderCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Create a new order"""
    # Validate account exists
    account = db.query(Account).filter(Account.id == order.account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    # Validate instrument exists and is active
    instrument = db.query(Instrument).filter(Instrument.id == order.instrument_id).first()
    if not instrument:
        raise HTTPException(status_code=404, detail="Instrument not found")
    if not instrument.is_active:
        raise HTTPException(status_code=400, detail="Instrument is not active")
    
    # Validate order quantity
    if order.quantity < instrument.min_quantity:
        raise HTTPException(status_code=400, detail=f"Quantity must be at least {instrument.min_quantity}")
    if instrument.max_quantity and order.quantity > instrument.max_quantity:
        raise HTTPException(status_code=400, detail=f"Quantity cannot exceed {instrument.max_quantity}")
    
    # Create order
    db_order = Order(**order.dict())
    db.add(db_order)
    db.commit()
    db.refresh(db_order)
    
    # Execute order in background if it's a market order
    if order.order_type.value == "market":
        background_tasks.add_task(execute_order_task, db_order.id)
    
    return db_order


@router.get("/", response_model=PaginatedResponse)
def get_orders(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    account_id: Optional[int] = None,
    instrument_id: Optional[int] = None,
    status: Optional[str] = None,
    order_type: Optional[str] = None,
    side: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get all orders with pagination and optional filtering"""
    query = db.query(Order)
    
    if account_id:
        query = query.filter(Order.account_id == account_id)
    if instrument_id:
        query = query.filter(Order.instrument_id == instrument_id)
    if status:
        query = query.filter(Order.status == status)
    if order_type:
        query = query.filter(Order.order_type == order_type)
    if side:
        query = query.filter(Order.side == side)
    
    total = query.count()
    orders = query.offset(skip).limit(limit).all()
    
    return PaginatedResponse(
        items=[OrderSchema.from_orm(order).dict() for order in orders],
        total=total,
        page=skip // limit + 1,
        size=limit,
        pages=(total + limit - 1) // limit
    )


@router.get("/{order_id}", response_model=OrderSchema)
def get_order(order_id: int, db: Session = Depends(get_db)):
    """Get a specific order by ID"""
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


@router.put("/{order_id}", response_model=OrderSchema)
def update_order(order_id: int, order_update: OrderUpdate, db: Session = Depends(get_db)):
    """Update an existing order"""
    db_order = db.query(Order).filter(Order.id == order_id).first()
    if not db_order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # Only allow updates to pending orders
    if db_order.status != OrderStatus.PENDING:
        raise HTTPException(status_code=400, detail="Can only update pending orders")
    
    # Update fields
    update_data = order_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_order, field, value)
    
    db.commit()
    db.refresh(db_order)
    return db_order


@router.delete("/{order_id}", response_model=StandardResponse)
def cancel_order(order_id: int, db: Session = Depends(get_db)):
    """Cancel an order"""
    db_order = db.query(Order).filter(Order.id == order_id).first()
    if not db_order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # Only allow cancellation of pending orders
    if db_order.status != OrderStatus.PENDING:
        raise HTTPException(status_code=400, detail="Can only cancel pending orders")
    
    db_order.status = OrderStatus.CANCELLED
    db.commit()
    
    return StandardResponse(success=True, message="Order cancelled successfully")


@router.post("/{order_id}/execute", response_model=StandardResponse)
async def execute_order_manual(order_id: int, db: Session = Depends(get_db)):
    """Manually execute a pending order"""
    db_order = db.query(Order).filter(Order.id == order_id).first()
    if not db_order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    if db_order.status != OrderStatus.PENDING:
        raise HTTPException(status_code=400, detail="Can only execute pending orders")
    
    success = await trading_service.execute_order(db, db_order)
    
    if success:
        return StandardResponse(success=True, message="Order executed successfully")
    else:
        return StandardResponse(success=False, message="Order execution failed")


async def execute_order_task(order_id: int):
    """Background task to execute an order"""
    from app.database import SessionLocal
    db = SessionLocal()
    try:
        order = db.query(Order).filter(Order.id == order_id).first()
        if order and order.status == OrderStatus.PENDING:
            await trading_service.execute_order(db, order)
    except Exception as e:
        print(f"Error executing order {order_id}: {e}")
    finally:
        db.close() 