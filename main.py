from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine
import models
from crud.api.v1.endpoints import financial
from models.financial import Base

app = FastAPI(title="ERP SaaS API", version="0.1.0")

origins = [
    "http://localhost:5173",
    "http://localhost:3000",
  
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

models.Base.metadata.create_all(bind=engine)

app.include_router(financial.router, prefix="/api/v1/financial", tags=["financial"])

if __name__ == '__main__':
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)