from sqlalchemy import Column, Integer, String, Numeric, DateTime, Enum, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship, backref
from enum import Enum as PyEnum
from database import Base

class TransactionType(PyEnum):
    ASSET = "ASSET"
    LIABILITY = "LIABILITY"
    EQUITY = "EQUITY"
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
    region = Column(String, nullable=False)

    inventory_item_id = Column(Integer, ForeignKey("inventory_items.id"), nullable=True)
    quantity = Column(Integer, nullable=True)

    inventory_item = relationship("InventoryItem", back_populates="transactions")
    invoice_items = relationship("InvoiceItem", back_populates="transactions")   

    account_category_id = Column(Integer, ForeignKey("account_categories.id"), nullable=False)
    account_category = relationship("AccountCategory", back_populates="transactions")

class AccountCategory(Base):
    __tablename__ = "account_categories"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    code = Column(String, nullable=False, unique=True)
    type = Column(Enum(TransactionType), nullable=False)
    parent_id = Column(Integer, ForeignKey("account_categories.id"), nullable=True)
    
    children = relationship("AccountCategory", backref=backref("parent", remote_side=[id]))
    transactions = relationship("Transaction", back_populates="account_category") 

    