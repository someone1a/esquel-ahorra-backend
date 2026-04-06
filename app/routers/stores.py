from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.models.store import Store
from app.schemas.store import StoreOut
from app.dependencies import get_db

router = APIRouter(prefix="/api/stores", tags=["stores"])


@router.get("/", response_model=List[StoreOut])
def list_stores(db: Session = Depends(get_db)):
    return db.query(Store).all()


@router.get("/{store_id}", response_model=StoreOut)
def get_store(store_id: int, db: Session = Depends(get_db)):
    store = db.query(Store).filter(Store.id == store_id).first()
    if not store:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Store not found")
    return store
