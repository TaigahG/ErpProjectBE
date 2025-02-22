from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, date
from database import get_db
from crud import reports
from schemas.reports import ProfitLossReport, BalanceSheet, RevenuePrediction

router = APIRouter()

@router.get("/profit-loss", response_model=ProfitLossReport)
def get_profit_loss_report(
    start_date: date = Query(..., description="Start date of the report period"),
    end_date: date = Query(..., description="End date of the report period"),
    db: Session = Depends(get_db)
):
    """
    Generate a Profit & Loss report for the specified period
    """
    return reports.generate_pnl(
        db,
        datetime.combine(start_date, datetime.min.time()),
        datetime.combine(end_date, datetime.max.time())
    )

@router.get("/balance-sheet", response_model=BalanceSheet)
def get_balance_sheet(
    as_of_date: date = Query(..., description="Date for the balance sheet"),
    db: Session = Depends(get_db)
):
    """
    Generate a Balance Sheet as of the specified date
    """
    return reports.generate_balance_sheet(
        db,
        datetime.combine(as_of_date, datetime.max.time())
    )

@router.get("/revenue-prediction", response_model=List[RevenuePrediction])
def get_revenue_prediction(
    months_ahead: int = Query(3, ge=1, le=12, description="Number of months to predict"),
    db: Session = Depends(get_db)
):
    """
    Predict revenue for the specified number of months ahead
    """
    predictions = reports.predict_revenue(db, months_ahead)
    if not predictions:
        raise HTTPException(
            status_code=404,
            detail="Not enough historical data for prediction"
        )
    return predictions

@router.get("/dashboard")
def get_dashboard_overview(
    period: str = Query(..., regex="^(30d|90d|year)$", description="Period for dashboard data"),
    db: Session = Depends(get_db)
):
    """
    Get dashboard overview data including:
    - Total income and expenses
    - Comparison with previous period
    - Monthly breakdown
    """
    return reports.get_dashboard_data(db, period)
