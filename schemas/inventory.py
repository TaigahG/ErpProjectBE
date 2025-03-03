from pydantic import BaseModel, Field, condecimal
from typing import Optional
from datetime import datetime

class InventoryItemBase(BaseModel):
    name: str
    description: Optional[str] = None
    price: condecimal(max_digits=15, decimal_places=2)
    quantity: int = Field(ge=0)

class InventoryItemCreate(InventoryItemBase):
    pass

class InventoryItemUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[condecimal(max_digits=15, decimal_places=2)] = None
    quantity: Optional[int] = Field(None, ge=0)

class InventoryItem(InventoryItemBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True