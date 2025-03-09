from sqlalchemy import Column, Integer, String, Numeric, DateTime, Enum, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from enum import Enum as PyEnum
from database import Base

class TransactionType(PyEnum):
    INCOME = "INCOME"
    EXPENSE = "EXPENSE"

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    amount = Column(Numeric(15, 2), nullable=False)
    transaction_type = Column(Enum(TransactionType), nullable=False)
    description = Column(String, nullable=True)
    category = Column(String, nullable=False)
    transaction_date = Column(DateTime(timezone=True), nullable=False)
    notes = Column(String, nullable=True)

    inventory_item_id = Column(Integer, ForeignKey("inventory_items.id"), nullable=True)
    quantity = Column(Integer, nullable=True)

    inventory_item = relationship("InventoryItem", back_populates="transactions")
    invoice_items = relationship("InvoiceItem", back_populates="transactions")    

    