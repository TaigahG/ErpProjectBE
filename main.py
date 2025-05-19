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

@app.middleware("http")
async def exception_handling(request, call_next):
    try:
        return await call_next(request)
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        print(f"ERROR PROCESSING REQUEST: {str(e)}\n{error_detail}")
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=500,
            content={"detail": f"Internal server error occurred: {str(e)}"}
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


from datetime import datetime

@app.get("/health", tags=["system"])
def health_check():
    return {"status": "ok", "timestamp": datetime.now().isoformat()}

@app.get("/debug/env", tags=["system"], include_in_schema=False)
async def debug_env():
    import os
    env_vars = {}
    for key in os.environ:
        if key in ["DB_HOST", "DB_PORT", "DB_NAME", "DB_USER", "ANTHROPIC_API_KEY"]:
            env_vars[key] = "***" if "PASSWORD" in key or "KEY" in key else "present"
    return {"env_vars_available": env_vars}

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8000))

    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)