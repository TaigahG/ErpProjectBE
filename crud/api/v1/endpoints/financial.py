from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from database import get_db
from schemas.financial import Transaction, TransactionCreate, TransactionUpdate, AccountCategory as AccountCategorySchema, AccountCategoryCreate
from models.financial import TransactionType, AccountCategory
from crud import financial, inventory

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

@router.get("/account-categories/", response_model=List[AccountCategorySchema])
def list_account_categories(
    type: Optional[TransactionType] = None,
    parent_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    query = db.query(AccountCategory)
    if type:
        query = query.filter(AccountCategory.type == type)
    
    # if parent_id is not None:
    #     query = query.filter(AccountCategory.parent_id == parent_id)
    # else:
    #     query = query.filter(AccountCategory.parent_id.is_(None))

    return query.all()

@router.get("/account-categories/{category_id}", response_model=AccountCategorySchema)
def get_account_category(category_id: int, db: Session = Depends(get_db)):
    db_category = db.query(AccountCategory).filter(AccountCategory.id == category_id).first()
    if db_category is None:
        raise HTTPException(status_code=404, detail="Account category not found")
    return db_category


@router.post("/account-categories/", response_model=AccountCategorySchema)
def create_account_category(
    category: AccountCategoryCreate,
    db: Session = Depends(get_db)
):
    
    query_exists = db.query(AccountCategory).filter(AccountCategoryCreate.code == category.code).first()

    if query_exists:
        raise HTTPException(status_code=400, detail="Account category with this code already exists")
    
    db_category = AccountCategory(**category.dict())
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category

@router.put("/account-categories/{category_id}", response_model=AccountCategorySchema)
def update_account_category(category_id: int, category_update: AccountCategoryCreate, db: Session = Depends(get_db)):
    db_category = db.query(AccountCategory).filter(AccountCategory.id == category_id).first()
    if db_category is None:
        raise HTTPException(status_code=404, detail="Account category not found")
    
    if category_update.code != db_category.code:
        query_exists = db.query(AccountCategory).filter(AccountCategory.code == category_update.code).first()
        if query_exists:
                    raise HTTPException(status_code=400, detail="Account code already exists")
        
    if category_update.parent_id and category_update.parent_id == category_id:
        raise HTTPException(status_code=400, detail="Category cannot be its own parent")
    
    for key, value in category_update.dict().items():
        setattr(db_category, key, value)
    
    db.commit()
    db.refresh(db_category)
    return db_category

@router.delete("/account-categories/{category_id}")
def delete_account_category(category_id: int, db: Session = Depends(get_db)):
    db_category = db.query(AccountCategory).filter(AccountCategory.id == category_id).first()

    if not db_category:
        raise HTTPException(status_code=404, detail="Account category not found")
    
    child_count = db.query(AccountCategory).filter(AccountCategory.parent_id == category_id).count()
    if child_count > 0:
        raise HTTPException(status_code=400, detail="Cannot delete category with child categories")
    
    transaction_count = db.query(Transaction).filter(Transaction.account_category_id == category_id).count()
    if transaction_count > 0:
        raise HTTPException(status_code=400, detail="Cannot delete category with transactions")
    
    db.delete(db_category)
    db.commit()
    return {"status": "success"}

