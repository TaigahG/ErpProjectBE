from sqlalchemy import Column, Integer, String, Numeric, DateTime, Enum, ForeignKey, UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from enum import Enum as PyEnum
import uuid
from database import Base

class InvoiceStatus(PyEnum):
    DRAFT = "DRAFT"
    SENT = "SENT"
    PAID = "PAID"
    OVERDUE = "OVERDUE"
    CANCELLED = "CANCELLED"

class PaymentTerms(PyEnum):
    NET_7 = "NET_7"
    NET_15 = "NET_15"
    NET_30 = "NET_30"
    NET_60 = "NET_60"

class Currency(PyEnum):
    USD = "USD"
    EUR = "EUR"
    GBP = "GBP"
    JPY = "JPY"
    IDR = "IDR"

class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, index=True)
    invoice_number = Column(UUID, default=uuid.uuid4, unique=True, nullable=False)
    client_name = Column(String, nullable=False)
    client_email = Column(String, nullable=False)
    client_address = Column(String, nullable=False)
    issue_date = Column(DateTime(timezone=True), server_default=func.now())
    due_date = Column(DateTime(timezone=True), nullable=False)
    status = Column(Enum(InvoiceStatus), default=InvoiceStatus.DRAFT)
    payment_terms = Column(Enum(PaymentTerms), nullable=False)
    currency = Column(Enum(Currency), nullable=False)
    subtotal = Column(Numeric(10, 2), nullable=False)
    tax_rate = Column(Numeric(4, 2), nullable=False) 
    tax_amount = Column(Numeric(10, 2), nullable=False)
    total = Column(Numeric(10, 2), nullable=False)
    notes = Column(String, nullable=True)
    pdf_url = Column(String, nullable=True)
    
    items = relationship("InvoiceItem", back_populates="invoice", cascade="all, delete-orphan")
    payment_history = relationship("PaymentHistory", back_populates="invoice", cascade="all, delete-orphan")

class InvoiceItem(Base):
    __tablename__ = "invoice_items"

    id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id"))
    description = Column(String, nullable=False)
    quantity = Column(Numeric(10, 2), nullable=False)
    unit_price = Column(Numeric(10, 2), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)

    inventory_item_id = Column(Integer, ForeignKey("inventory_items.id"), nullable=True)

    invoice = relationship("Invoice", back_populates="items")
    inventory_item = relationship("InventoryItem", back_populates="invoice_items")


class PaymentHistory(Base):
    __tablename__ = "payment_history"

    id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id"))
    amount_paid = Column(Numeric(10, 2), nullable=False)
    payment_date = Column(DateTime(timezone=True), server_default=func.now())
    payment_method = Column(String, nullable=False)
    transaction_reference = Column(String, nullable=True)

    invoice = relationship("Invoice", back_populates="payment_history")