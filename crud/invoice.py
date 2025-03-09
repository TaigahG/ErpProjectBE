from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from crud import inventory
from models.financial import Transaction
from models.invoice import Invoice, InvoiceItem, PaymentHistory, InvoiceStatus
from schemas.invoice import InvoiceCreate, InvoiceUpdate, PaymentHistoryCreate

def create_invoice(db: Session, invoice: InvoiceCreate) -> Invoice:
    if invoice.transaction_ids and len(invoice.transaction_ids) > 0:
        return create_invoice_from_transaction(db, invoice)
    
    subtotal = sum(item.quantity * item.unit_price for item in invoice.items)
    tax_amount = subtotal * (invoice.tax_rate / 100)
    total = subtotal + tax_amount

    invoice_data = invoice.dict(exclude={'items', 'transaction_ids'})
    db_invoice = Invoice(
        **invoice_data,
        subtotal=subtotal,
        tax_amount=tax_amount,
        total=total
    )
    db.add(db_invoice)
    db.flush()  

    for item in invoice.items:
        item_data = item.dict(exclude={'inventory_item_id', 'transaction_id'})
        
        db_item = InvoiceItem(
            invoice_id=db_invoice.id,
            **item_data
        )
        
        if item.inventory_item_id:
            inventory_item = inventory.get_inventory_item(db, item.inventory_item_id)
            if inventory_item:
                db_item.inventory_item_id = item.inventory_item_id
        
        if item.transaction_id:
            transaction = db.query(Transaction).get(item.transaction_id)
            if transaction:
                db_item.transaction_id = item.transaction_id
        
        db.add(db_item)

    db.commit()
    db.refresh(db_invoice)
    return db_invoice

def create_invoice_from_transaction(db: Session, invoice: InvoiceCreate) -> Invoice:
    transactions = db.query(Transaction).filter(Transaction.id.in_(invoice.transaction_ids)).all()

    if not transactions:
        raise ValueError("No transactions found")
    
    subtotal = sum(transaction.amount for transaction in transactions)
    tax_amount = subtotal * (invoice.tax_rate / 100)
    total = subtotal + tax_amount

    invoice_dict = invoice.dict(exclude={'items', 'transaction_ids'})

    db_invoice = Invoice(
        **invoice_dict,
        subtotal=subtotal,
        tax_amount=tax_amount,
        total=total
    )
    db.add(db_invoice)
    db.flush()  
    
    for transaction in transactions:
        quantity = transaction.quantity if transaction.quantity else 1
        unit_price = transaction.amount / quantity
        
        db_item = InvoiceItem(
            invoice_id=db_invoice.id,
            description=transaction.description or f"Transaction #{transaction.id}",
            quantity=quantity,
            unit_price=unit_price,
            amount=transaction.amount,
            transaction_id=transaction.id
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

