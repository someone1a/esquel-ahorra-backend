from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models.local import Local as LocalModel
from app.schemas.local import Local, LocalCreate
from app.utils import get_current_user
from app.models.user import User

router = APIRouter(
    prefix="/locals",
    tags=["locals"]
)

@router.post("/", response_model=Local)
def create_local(
    local: LocalCreate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Solo vendedores o admin pueden crear locales
    if current_user.rol != "vendedor":
        raise HTTPException(status_code=403, detail="No tienes permisos para crear locales")
        
    db_local = LocalModel(**local.dict())
    db.add(db_local)
    db.commit()
    db.refresh(db_local)
    return db_local

@router.get("/", response_model=List[Local])
def read_locals(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    locals_list = db.query(LocalModel).offset(skip).limit(limit).all()
    return locals_list

@router.get("/{local_id}", response_model=Local)
def read_local(local_id: int, db: Session = Depends(get_db)):
    db_local = db.query(LocalModel).filter(LocalModel.id == local_id).first()
    if db_local is None:
        raise HTTPException(status_code=404, detail="Local no encontrado")
    return db_local
