from sqlalchemy.orm import Session
from sqlalchemy import extract, func
from datetime import datetime
from typing import List, Optional
from crud import inventory
from models.financial import Transaction, TransactionType
from schemas.financial import TransactionCreate, TransactionUpdate


def create_transaction(db: Session, transaction: TransactionCreate) -> Transaction:
    transaction_data = transaction.model_dump()
    print(transaction_data)
    inventory_item_id = transaction_data.pop('inventory_item_id', None)
    print(inventory_item_id)
    quantity = transaction_data.pop('quantity', None)
    print(quantity)
    
    db_transaction = Transaction(**transaction_data)
    
    if inventory_item_id and quantity:
        inventory_item = inventory.get_inventory_item(db, inventory_item_id)
        if not inventory_item:
            raise ValueError(f"Inventory item with ID {inventory_item_id} not found")
        
        db_transaction.inventory_item_id = inventory_item_id
        db_transaction.quantity = quantity
        
        quantity_change = -quantity if transaction.transaction_type == TransactionType.INCOME else quantity
        inventory.update_inventory_quantity(db, inventory_item_id, quantity_change)
    
    db.add(db_transaction)
    db.commit()
    db.refresh(db_transaction)
    return db_transaction

def get_transaction(db: Session, transaction_id: int) -> Optional[Transaction]:
    return db.query(Transaction).filter(Transaction.id == transaction_id).first()

def get_transactions(db: Session, 
    skip: int = 0, 
    limit: int = 100,
    transaction_type: Optional[TransactionType] = None,
    category: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None) -> List[Transaction]:
    query = db.query(Transaction)

    if transaction_type:
        query = query.filter(Transaction.transaction_type == transaction_type)
    if category:
        query = query.filter(Transaction.category == category)
    if start_date:
        query = query.filter(Transaction.transaction_date >= start_date)
    if end_date:
        query = query.filter(Transaction.transaction_date <= end_date)

    return query.offset(skip).limit(limit).all()

def update_transaction(db: Session, transaction_id: int, transaction_update: TransactionUpdate) -> Optional[Transaction]:
    db_transaction = get_transaction(db, transaction_id)
    if db_transaction:
        update_data = transaction_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_transaction, field, value)
        db.commit()
        db.refresh(db_transaction)
    return db_transaction

def delete_transaction(db: Session, transaction_id: int) -> bool:
    db_transaction = get_transaction(db, transaction_id)
    if db_transaction:
        db.delete(db_transaction)
        db.commit()
        return True
    return False

def get_monthly_summary(db: Session, year: int, month: int) -> dict:
    income = db.query(Transaction).filter(
    Transaction.transaction_type == TransactionType.INCOME,
    extract('year', Transaction.transaction_date) == year,
    extract('month', Transaction.transaction_date) == month).with_entities(func.sum(Transaction.amount)).scalar() or 0

    expense = db.query(Transaction).filter(
    Transaction.transaction_type == TransactionType.EXPENSE,
    extract('year', Transaction.transaction_date) == year,
    extract('month', Transaction.transaction_date) == month).with_entities(func.sum(Transaction.amount)).scalar() or 0

    return {
        "year": year,
        "month": month,
        "total_income": income,
        "total_expense": expense,
        "net": income - expense
    }

def get_financial_report(db: Session ):
    pass