from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
from database import engine
from crud.api.v1.endpoints import financial, invoice, reports, inventory
from models import financial as financial_models
from models import invoice as invoice_models
from models import reports as reports_models
from models import inventory as inventory_models

app = FastAPI(title="ERP SaaS API", version="0.1.0")

origins = [
    "http://localhost:5173",
    "http://localhost:3000",
    "http://localhost:5174",
    "http://localhost:5175",
    "https://erp-project-fe.vercel.app"
  
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# financial_models.Base.metadata.drop_all(bind=engine)
# invoice_models.Base.metadata.drop_all(bind=engine)
# reports_models.Base.metadata.drop_all(bind=engine)
# inventory_models.Base.metadata.drop_all(bind=engine)
 
financial_models.Base.metadata.create_all(bind=engine)
invoice_models.Base.metadata.create_all(bind=engine)
reports_models.Base.metadata.create_all(bind=engine)
inventory_models.Base.metadata.create_all(bind=engine)


app.include_router(financial.router, prefix="/api/v1/financial", tags=["financial"])
app.include_router(invoice.router, prefix="/api/v1/invoice", tags=["invoice"])
app.include_router(reports.router, prefix="/api/v1/reports", tags=["reports"])
app.include_router(inventory.router, prefix="/api/v1/inventory", tags=["inventory"])
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8000))

    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)