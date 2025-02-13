from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from database import get_db
from schemas.invoice import (
    Invoice, InvoiceCreate, InvoiceUpdate,
    PaymentHistoryCreate
)
from models.invoice import InvoiceStatus
from crud import invoice

router = APIRouter()

@router.post("/invoices/", response_model=Invoice)
def create_invoice(invoice_data: InvoiceCreate,db: Session = Depends(get_db)):
    return invoice.create_invoice(db, invoice_data)

@router.get("/invoices/", response_model=List[Invoice])
def list_invoices(
    skip: int = 0,
    limit: int = 100,
    status: Optional[InvoiceStatus] = None,
    client_name: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db)
):
    return invoice.get_invoices(db, skip, limit, status, client_name, start_date, end_date)

@router.get("/invoices/{invoice_id}", response_model=Invoice)
def get_invoice(invoice_id: int, db: Session = Depends(get_db)):
    db_invoice = invoice.get_invoice(db, invoice_id)
    if not db_invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return db_invoice

@router.put("/invoices/{invoice_id}", response_model=Invoice)
def update_invoice(invoice_id: int, invoice_update: InvoiceUpdate, db: Session = Depends(get_db)):
    db_invoice = invoice.update_invoices(db, invoice_id, invoice_update)
    if not db_invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return db_invoice

@router.post("/invoices/{invoice_id}/payments/", response_model=Invoice)
def add_payment(invoice_id: int, payment: PaymentHistoryCreate, db: Session = Depends(get_db)):
    db_invoice = invoice.add_payment(db, invoice_id, payment)
    if not db_invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return db_invoice
