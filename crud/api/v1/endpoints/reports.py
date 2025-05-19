from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session
from typing import List, Optional
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

@router.get("/profit-loss-ifrs", response_model=dict)
def get_profit_loss_ifrs(
    start_date: date = Query(..., description="Start date of the report period"),
    end_date: date = Query(..., description="End date of the report period"),
    db: Session = Depends(get_db)
):
    """
    Generate a pnl report in IFRS format for the specified period
    """
    return reports.generate_pnl_ifrs(
        db,
        datetime.combine(start_date, datetime.min.time()),
        datetime.combine(end_date, datetime.max.time())
    )

@router.get("/balance-sheet-ifrs", response_model=dict)
def get_balance_sheet_ifrs(
    as_of_date: date = Query(..., description="Date for the balance sheet"),
    db: Session = Depends(get_db)
):
    """
    Generate a sheet in IFRS format with specified date
    """
    return reports.generate_balance_sheet_ifrs(
        db,
        datetime.combine(as_of_date, datetime.max.time())
    )

@router.get("/export/{report_type}")
def export_report(
    report_type: str,
    format: str = Query("pdf", regex="^(pdf|excel)$"),
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    as_of_date: Optional[date] = None,
    db: Session = Depends(get_db)
):
    try:
        if report_type == "profit-loss-ifrs":
            if not start_date or not end_date:
                raise HTTPException(status_code=400, detail="start_date and end_date are required for profit-loss reports")
            data = reports.generate_pnl_ifrs(
                db,
                datetime.combine(start_date, datetime.min.time()),
                datetime.combine(end_date, datetime.max.time())
            )
            filename = f"profit-loss-{start_date}-to-{end_date}"
        elif report_type == "balance-sheet-ifrs":
            if not as_of_date:
                raise HTTPException(status_code=400, detail="as_of_date is required for balance-sheet reports")
            data = reports.generate_balance_sheet_ifrs(
                db,
                datetime.combine(as_of_date, datetime.max.time())
            )
            filename = f"balance-sheet-{as_of_date}"
        else:
            raise HTTPException(status_code=400, detail="Invalid report type")

        if format == "pdf":
            pdf_data = reports.generate_pdf_report(report_type, data)
            filename = f"{filename}.pdf"
            media_type = "application/pdf"
            content = pdf_data
        else:  
            excel_data = reports.generate_excel_report(report_type, data)
            filename = f"{filename}.xlsx"
            media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            content = excel_data

        return Response(
            content=content,
            media_type=media_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        print(f"ERROR GENERATING REPORT: {str(e)}\n{error_detail}")
        raise HTTPException(status_code=500, detail=f"Error generating report: {str(e)}")

@router.get("/export-html/{report_type}")
def export_report_html(
    report_type: str,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    as_of_date: Optional[date] = None,
    db: Session = Depends(get_db)
):
    print("a")
    try:

        if report_type == "profit-loss-ifrs":
            print("b")
            if not start_date or not end_date:
                raise HTTPException(status_code=400, detail="start_date and end_date are required for profit-loss reports")
            data = reports.generate_pnl_ifrs(
                db,
                datetime.combine(start_date, datetime.min.time()),
                datetime.combine(end_date, datetime.max.time())
            )
            print(data)
            filename = f"profit-loss-{start_date}-to-{end_date}.html"
        elif report_type == "balance-sheet-ifrs":
            print("c", as_of_date)
            if not as_of_date:
                print("c1")
                raise HTTPException(status_code=400, detail="as_of_date is required for balance-sheet reports")
            data = reports.generate_balance_sheet_ifrs(
                db,
                datetime.combine(as_of_date, datetime.max.time())
            )
            print(data)
            filename = f"balance-sheet-{as_of_date}.html"
            print("c2")
        else:
            print("d")

            raise HTTPException(status_code=400, detail="Invalid report type")

        html_content = reports.generate_anthropic_report(report_type, data)
        print("e")

        return Response(
            content=html_content,
            media_type="text/html",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        print("f", e)

        raise HTTPException(status_code=500, detail=f"Error generating report: {str(e)}")