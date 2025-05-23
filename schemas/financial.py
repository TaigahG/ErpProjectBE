from pydantic import BaseModel, Field, condecimal
from datetime import datetime
from typing import Optional
from decimal import Decimal
from models.financial import TransactionType


class TransactionCreate(BaseModel):
    amount: condecimal(max_digits=15, decimal_places=2)
    transaction_type: TransactionType
    description: Optional[str] = None
    category: str
    transaction_date: datetime
    notes: Optional[str] = None
    inventory_item_id: Optional[int] = None
    quantity: Optional[int] = None
    region: str
    account_category_id: int


class Transaction(TransactionCreate):
    id: int
    transaction_date: datetime

    class Config:
        from_attributes = True

class TransactionUpdate(BaseModel):
    amount: Optional[condecimal(max_digits=10, decimal_places=2)] = None
    description: Optional[str] = None
    category: Optional[str] = None
    transaction_date: Optional[datetime] = None
    notes: Optional[str] = None
    region: Optional[str] = None


class AccountCategoryBase(BaseModel):
    name: str
    code: str
    type: TransactionType
    parent_id: Optional[int] = None

class AccountCategoryCreate(AccountCategoryBase):
    pass

class AccountCategory(AccountCategoryBase):
    id: int

    class Config:
        from_attributes = True
