from pydantic import BaseModel, EmailStr, UUID4, Field, condecimal, validator
from typing import List, Optional
from datetime import datetime
from decimal import Decimal
from models.invoice import InvoiceStatus, PaymentTerms, Currency

class InvoiceItemBase(BaseModel):
    description: str
    quantity: Decimal = Field(gt=0)
    unit_price: Decimal = Field(gt=0)
    amount: Decimal = Field(gt=0)

class InvoiceItemCreate(InvoiceItemBase):
    description: str
    quantity: condecimal(max_digits=10, decimal_places=2) = Field(gt=0)
    unit_price: condecimal(max_digits=10, decimal_places=2) = Field(gt=0)
    amount: condecimal(max_digits=10, decimal_places=2) = Field(gt=0)
    inventory_item_id: Optional[int] = None
    transaction_id: Optional[int] = None

class InvoiceItem(InvoiceItemBase):
    id: int
    invoice_id: int
    transaction_id: Optional[int] = None

    class Config:
        from_attributes = True

class PaymentHistoryBase(BaseModel):
    amount_paid: Decimal = Field(gt=0)
    payment_method: str
    transaction_reference: Optional[str] = None

class PaymentHistoryCreate(PaymentHistoryBase):
    pass

class PaymentHistory(PaymentHistoryBase):
    id: int
    invoice_id: int
    payment_date: datetime

    class Config:
        from_attributes = True

class InvoiceBase(BaseModel):
    client_name: Optional[str]
    client_email: Optional[EmailStr]
    client_address: Optional[str]
    payment_terms: PaymentTerms
    currency: Currency
    tax_rate: Decimal = Field(ge=0, le=100)
    notes: Optional[str] = None

class InvoiceCreate(InvoiceBase):
    due_date: datetime
    items: List[InvoiceItemCreate]
    transaction_ids: Optional[List[int]] = None

    @validator('items')
    def validate_items(cls, v, values):
        if values.get('transaction_ids') and len(values.get('transaction_ids', [])) > 0:
            return v
        if not v:
            raise ValueError('At least one item is required')
        return v

class Invoice(InvoiceBase):
    id: int
    invoice_number: UUID4
    issue_date: datetime
    due_date: datetime
    status: InvoiceStatus
    subtotal: Decimal
    tax_amount: Decimal
    total: Decimal
    pdf_url: Optional[str]
    items: List[InvoiceItem]
    payment_history: List[PaymentHistory]

    class Config:
        from_attributes = True

class InvoiceUpdate(BaseModel):
    client_name: Optional[str] = None
    client_email: Optional[EmailStr] = None
    client_address: Optional[str] = None
    payment_terms: Optional[PaymentTerms] = None
    currency: Optional[Currency] = None
    tax_rate: Optional[Decimal] = Field(None, ge=0, le=100)
    notes: Optional[str] = None
    status: Optional[InvoiceStatus] = None