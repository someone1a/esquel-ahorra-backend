from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from typing import List
import logging
from app.database import get_db
from app.models.local import Local as LocalModel
from app.models.product import Product as ProductModel, Price as PriceModel
from app.schemas.local import Local, LocalCreate, LocalConProductos
from app.utils import get_current_user
from app.models.user import User

logger = logging.getLogger(__name__)

PRIVILEGED_ROLES = ["supervisor", "admin"]

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
    if current_user.rol not in ["vendedor", "supervisor", "admin"]:
        raise HTTPException(status_code=403, detail="No tienes permisos para crear locales")
    
    try:
        db_local = LocalModel(**local.dict())
        db.add(db_local)
        db.commit()
        db.refresh(db_local)
        return db_local
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Error en base de datos al crear local: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al crear el local en la base de datos"
        )
    except Exception as e:
        logger.error(f"Error inesperado al crear local: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error inesperado al crear el local"
        )

@router.get("/", response_model=List[Local])
def read_locals(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    return db.query(LocalModel).offset(skip).limit(limit).all()

@router.get("/{local_id}", response_model=Local)
def read_local(local_id: int, db: Session = Depends(get_db)):
    db_local = db.query(LocalModel).filter(LocalModel.id == local_id).first()
    if db_local is None:
        raise HTTPException(status_code=404, detail="Local no encontrado")
    return db_local

@router.get("/{local_id}/productos", response_model=LocalConProductos)
def read_local_with_products(local_id: int, db: Session = Depends(get_db)):
    db_local = db.query(LocalModel).filter(LocalModel.id == local_id).first()
    if db_local is None:
        raise HTTPException(status_code=404, detail="Local no encontrado")
    
    try:
        prices = db.query(
            ProductModel.id,
            ProductModel.nombre,
            PriceModel.precio
        ).join(
            PriceModel, ProductModel.id == PriceModel.product_id
        ).filter(
            PriceModel.local_id == local_id
        ).all()
        
        productos = [
            {"id": p[0], "nombre": p[1], "precio": p[2]}
            for p in prices
        ]
        
        return {
            "id": db_local.id,
            "nombre": db_local.nombre,
            "direccion": db_local.direccion,
            "telefono": db_local.telefono,
            "is_active": db_local.is_active,
            "productos": productos
        }
    except SQLAlchemyError as e:
        logger.error(f"Error en base de datos al obtener productos del local: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al obtener los productos del local"
        )
        logger.error(f"Error inesperado: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error inesperado"
        )

@router.patch("/{local_id}", response_model=Local)
def update_local(
    local_id: int,
    local_update: LocalCreate,  # Reutilizar schema
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.rol not in ["vendedor", "supervisor", "admin"]:
        raise HTTPException(status_code=403, detail="No tienes permisos para actualizar locales")
    
    db_local = db.query(LocalModel).filter(LocalModel.id == local_id).first()
    if db_local is None:
        raise HTTPException(status_code=404, detail="Local no encontrado")
    
    try:
        for key, value in local_update.dict(exclude_unset=True).items():
            setattr(db_local, key, value)
        db.commit()
        db.refresh(db_local)
        return db_local
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Error en base de datos al actualizar local: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al actualizar el local en la base de datos"
        )
    except Exception as e:
        logger.error(f"Error inesperado al actualizar local: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error inesperado al actualizar el local"
        )

@router.delete("/{local_id}")
def delete_local(
    local_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.rol not in ["supervisor", "admin"]:
        raise HTTPException(status_code=403, detail="No tienes permisos para eliminar locales")
    
    db_local = db.query(LocalModel).filter(LocalModel.id == local_id).first()
    if db_local is None:
        raise HTTPException(status_code=404, detail="Local no encontrado")
    
    try:
        # Soft delete
        db_local.is_active = False
        db.commit()
        return {"message": "Local eliminado exitosamente (soft delete)"}
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Error en base de datos al eliminar local: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al eliminar el local en la base de datos"
        )
    except Exception as e:
        logger.error(f"Error inesperado al eliminar local: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error inesperado al eliminar el local"
        )