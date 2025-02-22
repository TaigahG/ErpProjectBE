from sqlalchemy import Column, Integer, String, Numeric, DateTime, Enum, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base


class FinancialReports(Base):
    __tablename__ = "financial_reports"

    id = Column(Integer, primary_key=True, index=True)
    report_type = Column(String, nullable=False)
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)
    total_revenue = Column(Numeric(10, 2), nullable=False)
    total_expenses = Column(Numeric(10, 2), nullable=False)
    net_profit = Column(Numeric(10, 2), nullable=False)
    generated_at = Column(DateTime(timezone=True), server_default=func.now())

    total_assets = Column(Numeric(10, 2), nullable=False)
    total_liabilities = Column(Numeric(10, 2), nullable=False)
    total_equity = Column(Numeric(10, 2), nullable=False)
    
