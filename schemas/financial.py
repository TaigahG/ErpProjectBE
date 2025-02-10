from pydantic import BaseModel, condecimal
from datetime import datetime
from typing import Optional
from models.financial import TransactionType


class TransactionBase(BaseModel):
    amount: condecimal = condecimal(max_digits=10, decimal_places=2)
    transaction_type: TransactionType
    description: Optional[str] = None
    category: str
    notes: Optional[str] = None

class TransactionCreate(TransactionBase):
    pass

class Transaction(TransactionBase):
    id: int
    transaction_date: datetime

    class Config:
        from_attributes = True

class TransactionUpdate(BaseModel):
    amount: Optional[condecimal(max_digits=10, decimal_places=2)] = None
    description: Optional[str] = None
    category: Optional[str] = None
    notes: Optional[str] = None