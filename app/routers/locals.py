from fastapi import APIRouter, Depends, HTTPException, status
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

# Configurar logging
logger = logging.getLogger(__name__)

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
    # Solo vendedores o supervisores pueden crear locales
    if current_user.rol not in ["vendedor", "supervisor"]:
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
def read_locals(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    locals_list = db.query(LocalModel).offset(skip).limit(limit).all()
    return locals_list

@router.get("/{local_id}", response_model=Local)
def read_local(local_id: int, db: Session = Depends(get_db)):
    db_local = db.query(LocalModel).filter(LocalModel.id == local_id).first()
    if db_local is None:
        raise HTTPException(status_code=404, detail="Local no encontrado")
    return db_local

@router.get("/{local_id}/productos", response_model=LocalConProductos)
def read_local_with_products(local_id: int, db: Session = Depends(get_db)):
    """
    Obtiene los detalles de una tienda junto con todos sus productos y precios.
    """
    # Obtener la tienda
    db_local = db.query(LocalModel).filter(LocalModel.id == local_id).first()
    if db_local is None:
        raise HTTPException(status_code=404, detail="Local no encontrado")
    
    try:
        # Obtener todos los productos con precios para este local
        prices = db.query(
            ProductModel.id,
            ProductModel.nombre,
            PriceModel.precio
        ).join(
            PriceModel, ProductModel.id == PriceModel.product_id
        ).filter(
            PriceModel.local_id == local_id
        ).all()
        
        # Convertir los resultados a lista de diccionarios
        productos = [
            {
                "id": precio[0],
                "nombre": precio[1],
                "precio": precio[2]
            }
            for precio in prices
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
    except Exception as e:
        logger.error(f"Error inesperado: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error inesperado"
        )
