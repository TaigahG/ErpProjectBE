from pydantic import BaseModel
from datetime import datetime
from decimal import Decimal
from typing import Optional, List

class ProfitLossReport(BaseModel):
    period_start: datetime
    period_end: datetime
    total_revenue: Decimal
    total_expenses: Decimal
    net_profit: Decimal
    revenue_breakdown: List[dict]
    expenses_breakdown: List[dict]

    class Config:
        from_attributes = True

class BalanceSheet(BaseModel):
    total_assets: Decimal
    total_liabilities: Decimal
    total_equity: Decimal
    as_of_date: datetime
    assets_breakdown: List[dict]
    liabilities_breakdown: List[dict]
    equity_breakdown: List[dict]

    class Config:
        from_attributes = True

class RevenuePrediction(BaseModel):
    prediction_date: datetime
    predicted_amount: Decimal
    confidence_level: float
    factors: List[str]

    class Config:
        from_attributes = True

