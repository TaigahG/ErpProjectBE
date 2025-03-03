from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from database import get_db
from schemas.financial import Transaction, TransactionCreate, TransactionUpdate
from models.financial import TransactionType
from crud import financial, inventory

router = APIRouter()

def create_transaction(db: Session, transaction: TransactionCreate) -> Transaction:
    transaction_data = transaction.model_dump()
    
    # Handle inventory item if provided
    inventory_item_id = transaction_data.pop('inventory_item_id', None)
    quantity = transaction_data.pop('quantity', None)
    
    # Create transaction
    db_transaction = Transaction(**transaction_data)
    
    # Link with inventory item if provided
    if inventory_item_id and quantity:
        # Check if inventory item exists
        inventory_item = inventory.get_inventory_item(db, inventory_item_id)
        if not inventory_item:
            raise ValueError(f"Inventory item with ID {inventory_item_id} not found")
        
        # Link transaction to inventory item
        db_transaction.inventory_item_id = inventory_item_id
        db_transaction.quantity = quantity
        
        # Update inventory quantity based on transaction type
        quantity_change = -quantity if transaction.transaction_type == TransactionType.INCOME else quantity
        inventory.update_inventory_quantity(db, inventory_item_id, quantity_change)
    
    db.add(db_transaction)
    db.commit()
    db.refresh(db_transaction)
    return db_transaction

@router.get("/transactions/", response_model=List[Transaction])
def list_transactions(skip: int = 0,
    limit: int = 100,
    transaction_type: Optional[TransactionType] = None,
    category: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db)):
    transactions = financial.get_transactions(
        db, 
        skip=skip, 
        limit=limit,
        transaction_type=transaction_type,
        category=category,
        start_date=start_date,
        end_date=end_date
    )
    return transactions

@router.get("/transactions/{transaction_id}", response_model=Transaction)
def get_transaction(transaction_id: int, db: Session = Depends(get_db)):
    db_transaction = financial.get_transaction(db, transaction_id)
    if db_transaction is None:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return db_transaction

@router.put("/transactions/{transaction_id}", response_model=Transaction)
def update_transaction(transaction_id: int, transaction_update: TransactionUpdate, db: Session = Depends(get_db)):
    db_transaction = financial.update_transaction(db, transaction_id, transaction_update)
    if db_transaction is None:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return db_transaction

@router.delete("/transactions/{transaction_id}")
def delete_transaction(transaction_id: int, db: Session = Depends(get_db)):
    success = financial.delete_transaction(db, transaction_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return {"status": "success"}

@router.get("/transactions/summary/{year}/{month}")
def get_monthly_summary(year: int, month: int, db: Session = Depends(get_db)):
    return financial.get_monthly_summary(db, year, month)

