from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from database import get_db
from schemas.inventory import InventoryItem, InventoryItemCreate, InventoryItemUpdate
from crud import inventory

router = APIRouter()

@router.post("/", response_model=InventoryItem)
def create_inventory_item(item: InventoryItemCreate, db: Session = Depends(get_db)):
    return inventory.create_inventory_item(db, item)

@router.get("/", response_model=List[InventoryItem])
def list_inventory_items(skip: int = 0, limit: int = 100, search: Optional[str] = None, db: Session = Depends(get_db)):
    return inventory.get_inventory_items(db, skip, limit, search)

@router.get("/{item_id}", response_model=InventoryItem)
def get_inventory_item(item_id: int, db: Session = Depends(get_db)):
    db_item = inventory.get_inventory_item(db, item_id)
    if db_item is None:
        raise HTTPException(status_code=404, detail="Inventory item is not found")
    return db_item

@router.put("/{item_id}", response_model=InventoryItem)
def update_inventory_item(item_id: int, item_update: InventoryItemUpdate, db: Session = Depends(get_db)):
    db_item = inventory.update_inventory_item(db, item_id, item_update)
    if db_item is None:
        raise HTTPException(status_code=404, detail="Inventory item is not found")
    return db_item

@router.delete("/{item_id}", response_model=InventoryItem)
def delete_inventory_item(item_id: int, db: Session = Depends(get_db)):
    success = inventory.delete_inventory_item(db, item_id)
    if not success:
        raise HTTPException(status_code=404, detail="Inventory item is not found")
    return {"status": "success"}

@router.get("/analysis", response_model=dict)
def get_inventory_analysis(db: Session = Depends(get_db)):
    return inventory.analyze_inventory_sales(db)