from datetime import timedelta
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sqlalchemy import func
from sqlalchemy.orm import Session
from typing import List, Optional
from models.financial import Transaction, TransactionType
from models.inventory import InventoryItem
from models.invoice import Invoice, InvoiceItem, InvoiceStatus
from schemas.inventory import InventoryItemCreate, InventoryItemUpdate

def create_inventory_item(db: Session, item: InventoryItemCreate) -> InventoryItem:
    db_item = InventoryItem(**item.dict())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

def get_inventory_item(db: Session, item_id: int) -> Optional[InventoryItem]:
    return db.query(InventoryItem).filter(InventoryItem.id == item_id).first()

def get_inventory_items(db: Session, skip: int = 0, limit: int = 100, search: Optional[str]=None) -> List[InventoryItem]:
    query = db.query(InventoryItem)

    if search:
        query = query.filter(InventoryItem.name.ilike(f'%{search}%'))

    return query.offset(skip).limit(limit).all()

def update_inventory_item(db: Session, item_id: int, item_update: InventoryItemUpdate) -> Optional[InventoryItem]:
    db_item = get_inventory_item(db, item_id)

    if db_item:
        update_data = item_update.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_item, key, value)
        db.commit()
        db.refresh(db_item)
    return db_item

def delete_inventory_item(db: Session, item_id: int) -> bool:
    db_item = get_inventory_item(db, item_id)

    if db_item:
        db.delete(db_item)
        db.commit()
        return True
    return False

def update_inventory_quantity(db: Session, item_id: int, quantity_change: int) -> Optional[InventoryItem]:
    db_item = get_inventory_item(db, item_id)

    if db_item:
        db_item.quantity += quantity_change
        if db_item.quantity < 0:
            db_item.quantity = 0
        db.commit()
        db.refresh(db_item)
    return db_item

def analyze_inventory_sales(db: Session) -> dict:
    
    items = db.query(InventoryItem).all()
    items_analysis = []

    for item in items:
        transactions = db.query(Transaction).filter(
            Transaction.inventory_item_id == item.id,
            Transaction.transaction_type == TransactionType.INCOME
        ).all()

        invoice_items = db.query(InvoiceItem).filter(
            InvoiceItem.inventory_item_id == item.id
        ).join(Invoice).filter(
            Invoice.status.in_([InvoiceStatus.PAID, InvoiceStatus.SENT])
        ).all()

        total_quantity_sold = sum(t.quantity for t in transactions if t.quantity) + \
                            sum(float(i.quantity) for i in invoice_items)
        
        total_revenue = sum(t.amount for t in transactions) + \
                       sum(i.amount for i in invoice_items)
        
        # Regional analysis
        regional_data = db.query(
            Transaction.region, 
            func.sum(Transaction.quantity).label('quantity_sold'),
            func.sum(Transaction.amount).label('revenue')
        ).filter(
            Transaction.inventory_item_id == item.id,
            Transaction.transaction_type == TransactionType.INCOME
        ).group_by(Transaction.region).all()
        
        # Correctly format regional data
        regional_sales = [
            {
                "region": region.region,  # Use region.region to get the string value
                "quantity_sold": float(region.quantity_sold) if region.quantity_sold else 0,
                "revenue": float(region.revenue) if region.revenue else 0,
            }
            for region in regional_data
        ]

        regional_sales.sort(key=lambda x: x["revenue"], reverse=True)
        
        sales_by_month = db.query(
            func.date_trunc('month', Transaction.transaction_date).label('month'),
            func.sum(Transaction.quantity).label('quantity')
        ).filter(
            Transaction.inventory_item_id == item.id,
            Transaction.transaction_type == TransactionType.INCOME
        ).group_by('month').order_by('month').all()
        
        if len(sales_by_month) >= 3:  
            X = np.array([
                [i, m.month.month, m.month.isocalendar()[1]]  
                for i, m in enumerate(sales_by_month)
            ])
            y = np.array([m.quantity for m in sales_by_month])
            
            model = RandomForestRegressor(n_estimators=100, random_state=42)
            model.fit(X, y)
            
            next_month = sales_by_month[-1].month + timedelta(days=32)
            next_month = next_month.replace(day=1) 
            next_month_features = [
                len(sales_by_month), 
                next_month.month, 
                next_month.isocalendar()[1]
            ]
            
            predicted_quantity = float(model.predict([next_month_features])[0])
            
            # Add safety check for division by zero
            if sales_by_month[-1].quantity > 0:
                growth_rate = (predicted_quantity - sales_by_month[-1].quantity) / sales_by_month[-1].quantity
            else:
                growth_rate = 0
            
            feature_importance = {
                "time_trend": model.feature_importances_[0],
                "month_of_year": model.feature_importances_[1],
                "week_of_year": model.feature_importances_[2]
            }
            prediction_confidence = 0.7 + (len(sales_by_month) / 20)  
        else:
            predicted_quantity = 0
            growth_rate = 0
            prediction_confidence = 0
        
        if item.quantity > 0 and total_quantity_sold > 0:
            turnover_rate = total_quantity_sold / item.quantity
        else:
            turnover_rate = 0
        
        item_analysis = {
            "id": item.id,
            "name": item.name,
            "current_stock": item.quantity,
            "total_sold": total_quantity_sold,
            "total_revenue": float(total_revenue),
            "predicted_monthly_sales": max(0, predicted_quantity),
            "growth_rate": growth_rate,
            "turnover_rate": turnover_rate,
            "prediction_confidence": prediction_confidence,
            "revenue_impact": float(total_revenue) / (1 + item.quantity) if item.quantity > 0 else 0,
            "restock_recommendation": "High" if (item.quantity < predicted_quantity * 2) else 
                                     "Medium" if (item.quantity < predicted_quantity * 4) else "Low",
            "regional_sales": regional_sales[:5]
        }
        
        items_analysis.append(item_analysis)
    
    # Properly indented - outside the loop
    items_analysis.sort(key=lambda x: x["revenue_impact"], reverse=True)
    
    # Calculate overall top regions
    overall_top_regions = db.query(
        Transaction.region,
        func.sum(Transaction.quantity).label('quantity_sold'),
        func.sum(Transaction.amount).label('revenue'),
        func.count(Transaction.id.distinct()).label('transaction_count')
    ).filter(
        Transaction.transaction_type == TransactionType.INCOME,
        Transaction.inventory_item_id.isnot(None)
    ).group_by(Transaction.region).order_by(func.sum(Transaction.amount).desc()).limit(5).all()
    
    formatted_top_regions = [
        {
            "region": region.region,
            "quantity_sold": float(region.quantity_sold) if region.quantity_sold else 0,
            "revenue": float(region.revenue) if region.revenue else 0,
            "transaction_count": region.transaction_count
        }
        for region in overall_top_regions
    ]
    
    # Return statement outside the loop
    return {
        "top_selling_items": items_analysis[:5],
        "items_to_restock": [item for item in items_analysis if item["restock_recommendation"] == "High"],
        "growth_items": sorted(items_analysis, key=lambda x: x["growth_rate"], reverse=True)[:5],
        "top_regions": formatted_top_regions,  # Added top regions overall
        "all_items_analysis": items_analysis
    }
