from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from models.invoice import Invoice, InvoiceItem, PaymentHistory, InvoiceStatus
from schemas.invoice import InvoiceCreate, InvoiceUpdate, PaymentHistoryCreate

def create_invoice(db: Session, invoice: InvoiceCreate) -> Invoice:
    subtotal = sum(item.quantity * item.unit_price for item in invoice.items)
    tax_amount = subtotal * (invoice.tax_rate / 100)
    total = subtotal + tax_amount

    db_invoice = Invoice(
        **invoice.dict(exclude={'items'}),
        subtotal=subtotal,
        tax_amount=tax_amount,
        total=total
    )
    db.add(db_invoice)
    db.flush()  
    
    for item in invoice.items:
        db_item = InvoiceItem(
            invoice_id=db_invoice.id,
            **item.dict()
        )
        db.add(db_item)

    db.commit()
    db.refresh(db_invoice)
    return db_invoice

def get_invoice(db: Session, invoice_id: int) -> Optional[Invoice]:
    return db.query(Invoice).filter(Invoice.id == invoice_id).first()

def get_invoice_by_number(db: Session, invoice_number: str) -> Optional[Invoice]:
    return db.query(Invoice).filter(Invoice.invoice_number == invoice_number).first()

def get_invoices(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    status: Optional[InvoiceStatus] = None,
    client_name: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
) -> List[Invoice]:
    query = db.query(Invoice)
    
    if status:
        query = query.filter(Invoice.status == status)
    if client_name:
        query = query.filter(Invoice.client_name.ilike(f"%{client_name}%"))
    if start_date:
        query = query.filter(Invoice.issue_date >= start_date)
    if end_date:
        query = query.filter(Invoice.issue_date <= end_date)
    
    return query.offset(skip).limit(limit).all()

def update_invoice(
    db: Session,
    invoice_id: int,
    invoice_update: InvoiceUpdate
) -> Optional[Invoice]:
    db_invoice = get_invoice(db, invoice_id)
    if db_invoice:
        update_data = invoice_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_invoice, field, value)
        db.commit()
        db.refresh(db_invoice)
    return db_invoice

#add payment
def add_payment(db: Session, invoice_id: int, payment: PaymentHistoryCreate) -> Optional[Invoice]:
    db_invoice = get_invoice(db, invoice_id)
    if not db_invoice:
        return None
    db_paymet = PaymentHistory(
        invoice_id=invoice_id,
        **payment.dict()
    )
    db.add(db_paymet)

    total_paid = sum(i.amount_paid for i in db_invoice.payment_history) + payment.amount_paid
    if total_paid >= db_invoice.total:
        db_invoice.status = InvoiceStatus.PAID
    db.commit()
    db.refresh(db_invoice)
    return db_invoice
#generate pdf url