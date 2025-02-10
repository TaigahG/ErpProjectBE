from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from database import get_db
from schemas.financial import Transaction, TransactionCreate, TransactionUpdate
from models.financial import TransactionType
from crud import financial

router = APIRouter()

@router.post("/transactions/", response_model=Transaction)
def create_transaction(
    transaction: TransactionCreate,
    db: Session = Depends(get_db)
):
    return financial.create_transaction(db, transaction)

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

