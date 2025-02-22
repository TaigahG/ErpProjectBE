from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from datetime import datetime, timedelta
from typing import List, Optional
from models.financial import Transaction, TransactionType
from models.invoice import Invoice, InvoiceStatus
from schemas.reports import ProfitLossReport, BalanceSheet, RevenuePrediction
import pandas as pd
from sklearn.linear_model import LinearRegression
import numpy as np

def generate_pnl(db: Session, start_date: datetime, end_date: datetime) -> ProfitLossReport:
    income = db.query(func.sum(Transaction.amount)).filter(
        Transaction.transaction_type == TransactionType.INCOME,
        Transaction.transaction_date >= start_date,
        Transaction.transaction_date <= end_date
    ).scalar() or 0

    expenses = db.query(func.sum(Transaction.amount)).filter(
        Transaction.transaction_type == TransactionType.EXPENSE,
        Transaction.transaction_date >= start_date,
        Transaction.transaction_date <= end_date
    ).scalar() or 0

    revenue_breakdown = db.query(
        func.date_trunc('month', Transaction.transaction_date).label('month'),
        func.sum(Transaction.amount).label('amount')
    ).filter(
        Transaction.transaction_type == TransactionType.INCOME,
        Transaction.transaction_date >= start_date,
        Transaction.transaction_date <= end_date
    ).group_by(
        func.date_trunc('month', Transaction.transaction_date)
    ).order_by(
        func.date_trunc('month', Transaction.transaction_date)
    ).all()

    expense_breakdown = db.query(
        func.date_trunc('month', Transaction.transaction_date).label('month'),
        func.sum(Transaction.amount).label('amount')
    ).filter(
        Transaction.transaction_type == TransactionType.EXPENSE,
        Transaction.transaction_date >= start_date,
        Transaction.transaction_date <= end_date
    ).group_by(
        func.date_trunc('month', Transaction.transaction_date)
    ).order_by(
        func.date_trunc('month', Transaction.transaction_date)
    ).all()

    total_revenue = sum(r.amount for r in revenue_breakdown)
    total_expenses = sum(e.amount for e in expense_breakdown)

    return ProfitLossReport(
        period_start=start_date,
        period_end=end_date,
        total_revenue=total_revenue,
        total_expenses=total_expenses,
        net_profit=total_revenue - total_expenses,
        revenue_breakdown=[{
            "category": r.month.strftime("%Y-%m-%d"),
            "amount": float(r.amount)
        } for r in revenue_breakdown],
        expenses_breakdown=[{
            "category": e.month.strftime("%Y-%m-%d"),
            "amount": float(e.amount)
        } for e in expense_breakdown]
    )

def generate_balance_sheet(db: Session, as_of_date: datetime) -> BalanceSheet:
    total_assets = db.query(func.sum(Transaction.amount)).filter(
        Transaction.transaction_type == TransactionType.INCOME,
        Transaction.transaction_date <= as_of_date
    ).scalar() or 0

    total_liabilities = db.query(func.sum(Transaction.amount)).filter(
        Transaction.transaction_type == TransactionType.EXPENSE,
        Transaction.transaction_date <= as_of_date
    ).scalar() or 0

    return BalanceSheet(
    as_of_date=as_of_date,
    total_assets=total_assets,
    total_liabilities=total_liabilities,
    total_equity=total_assets - total_liabilities,
    assets_breakdown=[], 
    liabilities_breakdown=[],
    equity_breakdown=[]
    )

def predict_revenue(db: Session, months_ahead: int = 3) -> List[RevenuePrediction]:
    monthly_revenue = db.query(
        func.date_trunc('month', Transaction.transaction_date).label('month'),
        func.sum(Transaction.amount).label('revenue')
    ).filter(
        Transaction.transaction_type == TransactionType.INCOME
    ).group_by(
        func.date_trunc('month', Transaction.transaction_date)
    ).order_by('month').all()

    if not monthly_revenue:
        return []

    df = pd.DataFrame(monthly_revenue, columns=['month', 'revenue'])
    df['revenue'] = df['revenue'].astype(float)
    
    last_month = df['month'].max()

    X = np.arange(len(df)).reshape(-1, 1)
    y = df['revenue'].values  

    model = LinearRegression()
    model.fit(X, y)

    y_pred = model.predict(X)
    
    mse = np.mean((y - y_pred) ** 2)
    
    r2 = model.score(X, y)
    print(f"Model R²: {r2:.2f}")
    
    n = len(X)
    std_error = np.sqrt(mse / (n - 2)) if n > 2 else 0
    
    predictions = []
    for i in range(1, months_ahead + 1):
        next_month = (last_month + pd.DateOffset(months=i)).replace(day=1)
        
        month_index = len(df) + i - 1
        X_new = np.array([[month_index]])
        predicted_value = float(model.predict(X_new)[0])
        
        time_factor = 1 / (i + 1) 
        data_quality = min(1.0, len(df) / 12)  
        model_accuracy = max(0, r2)  

        
        confidence_level = (time_factor * 0.3 + 
                          data_quality * 0.3 + 
                          model_accuracy * 0.4)
        
        prediction_dict = {
            "prediction_date": next_month,
            "predicted_amount": max(Decimal(str(predicted_value)), Decimal('0')),
            "confidence_level": round(confidence_level, 2),
            "factors": [
                f"Model accuracy (R²): {r2:.2f}",
                f"Data points: {len(df)} months",
                f"Prediction distance: {i} months",
                f"Standard error: {std_error:.2f}"
            ]
        }
        predictions.append(RevenuePrediction(**prediction_dict))

    return predictions

def get_dashboard_data(db: Session, period: str) -> dict:
    latest_transaction = db.query(func.max(Transaction.transaction_date)).scalar()
    if not latest_transaction:
        return {
            "total_income": 0,
            "total_expenses": 0,
            "net_profit": 0,
            "previous_income": 0,
            "previous_expenses": 0,
            "previous_profit": 0,
            "monthly_data": []
        }

    reference_date = latest_transaction

    if period == '30d':
        end_date = reference_date
        start_date = reference_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        previous_start = (start_date - timedelta(days=1)).replace(day=1)
    elif period == '90d':
        end_date = reference_date
        start_date = (reference_date - timedelta(days=90)).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        previous_start = (start_date - timedelta(days=90)).replace(day=1)
    else:  
        end_date = reference_date
        start_date = datetime(reference_date.year, 1, 1, 0, 0, 0)
        previous_start = datetime(reference_date.year - 1, 1, 1, 0, 0, 0)

    print(f"Period selected: {period}")
    print(f"Reference date: {reference_date}")
    print(f"Start date: {start_date}")
    print(f"End date: {end_date}")

    current_data = get_period_data(db, start_date, end_date)
    previous_data = get_period_data(db, previous_start, start_date)
    monthly_data = get_monthly_breakdown(db, start_date, end_date)

    return {
        "total_income": current_data["income"],
        "total_expenses": current_data["expenses"],
        "net_profit": current_data["income"] - current_data["expenses"],
        "previous_income": previous_data["income"],
        "previous_expenses": previous_data["expenses"],
        "previous_profit": previous_data["income"] - previous_data["expenses"],
        "monthly_data": monthly_data
    }

def get_period_data(db: Session, start_date: datetime, end_date: datetime) -> dict:
    print(f"Querying transactions from {start_date} to {end_date}")

    transactions = db.query(Transaction).filter(
        Transaction.transaction_date >= start_date,
        Transaction.transaction_date <= end_date
    ).all()

    income = sum(t.amount for t in transactions if t.transaction_type == TransactionType.INCOME)
    expenses = sum(t.amount for t in transactions if t.transaction_type == TransactionType.EXPENSE)

    print(f"Found {len(transactions)} transactions")
    print(f"Total income: {income}")
    print(f"Total expenses: {expenses}")

    return {
        "income": float(income),
        "expenses": float(expenses)
    }
def get_monthly_breakdown(db: Session, start_date: datetime, end_date: datetime) -> List[dict]:

    start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
    end_date = end_date.replace(hour=23, minute=59, second=59, microsecond=999999)

    income_by_month = db.query(
        func.date_trunc('month', Transaction.transaction_date).label('month'),
        func.sum(Transaction.amount).label('income')
    ).filter(
        Transaction.transaction_type == TransactionType.INCOME,
        Transaction.transaction_date >= start_date,
        Transaction.transaction_date <= end_date
    ).group_by('month').all()

    expenses_by_month = db.query(
        func.date_trunc('month', Transaction.transaction_date).label('month'),
        func.sum(Transaction.amount).label('expenses')
    ).filter(
        Transaction.transaction_type == TransactionType.EXPENSE,
        Transaction.transaction_date >= start_date,
        Transaction.transaction_date <= end_date
    ).group_by('month').all()

    monthly_data = {}
    for income in income_by_month:
        month_key = income.month.strftime("%b %Y")
        monthly_data[month_key] = {
            "month": month_key,
            "income": float(income.income),
            "expenses": 0
        }

    for expense in expenses_by_month:
        month_key = expense.month.strftime("%b %Y")
        if month_key in monthly_data:
            monthly_data[month_key]["expenses"] = float(expense.expenses)
        else:
            monthly_data[month_key] = {
                "month": month_key,
                "income": 0,
                "expenses": float(expense.expenses)
            }

    return list(monthly_data.values())

    
    




    