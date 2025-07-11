from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models import Account
from app.schemas import AccountCreate, AccountUpdate, Account as AccountSchema, StandardResponse, PaginatedResponse

router = APIRouter(prefix="/accounts", tags=["accounts"])


@router.post("/", response_model=AccountSchema)
def create_account(account: AccountCreate, db: Session = Depends(get_db)):
    """Create a new trading account"""
    # Check if account name already exists
    existing_account = db.query(Account).filter(Account.name == account.name).first()
    if existing_account:
        raise HTTPException(status_code=400, detail="Account name already exists")
    
    db_account = Account(**account.dict())
    db.add(db_account)
    db.commit()
    db.refresh(db_account)
    return db_account


@router.get("/", response_model=PaginatedResponse)
def get_accounts(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    account_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get all accounts with pagination and optional filtering"""
    query = db.query(Account)
    
    if account_type:
        query = query.filter(Account.account_type == account_type)
    
    total = query.count()
    accounts = query.offset(skip).limit(limit).all()
    
    # Convert accounts to dict format safely
    account_items = []
    for account in accounts:
        try:
            account_dict = {
                "id": account.id,
                "name": account.name,
                "account_type": account.account_type.value,
                "balance": account.balance,
                "currency": account.currency,
                "created_at": account.created_at,
                "updated_at": account.updated_at
            }
            account_items.append(account_dict)
        except Exception as e:
            print(f"Error converting account {account.id}: {e}")
            continue
    
    return PaginatedResponse(
        items=account_items,
        total=total,
        page=(skip // limit) + 1 if limit > 0 else 1,
        size=limit,
        pages=(total + limit - 1) // limit if limit > 0 else 1
    )


@router.get("/{account_id}", response_model=AccountSchema)
def get_account(account_id: int, db: Session = Depends(get_db)):
    """Get a specific account by ID"""
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    return account


@router.put("/{account_id}", response_model=AccountSchema)
def update_account(account_id: int, account_update: AccountUpdate, db: Session = Depends(get_db)):
    """Update an existing account"""
    db_account = db.query(Account).filter(Account.id == account_id).first()
    if not db_account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    # Check if new name conflicts with existing account
    if account_update.name and account_update.name != db_account.name:
        existing_account = db.query(Account).filter(Account.name == account_update.name).first()
        if existing_account:
            raise HTTPException(status_code=400, detail="Account name already exists")
    
    # Update fields
    update_data = account_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_account, field, value)
    
    db.commit()
    db.refresh(db_account)
    return db_account


@router.delete("/{account_id}", response_model=StandardResponse)
def delete_account(account_id: int, db: Session = Depends(get_db)):
    """Delete an account"""
    db_account = db.query(Account).filter(Account.id == account_id).first()
    if not db_account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    # Check if account has any positions or orders
    if db_account.positions or db_account.orders:
        raise HTTPException(status_code=400, detail="Cannot delete account with active positions or orders")
    
    db.delete(db_account)
    db.commit()
    
    return StandardResponse(success=True, message="Account deleted successfully") 