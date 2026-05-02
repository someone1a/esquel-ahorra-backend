from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from typing import List
from app.database import get_db
from app.schemas.product import ProductCreate, Product, ProductUpdate, ProductSearchRequest, ProductSearchResponse, PriceCorrection
from app.services.products import create_product, get_product, get_product_by_barcode, update_product_price, get_corrections_count, search_products, search_products_by_name, approve_price_correction, get_pending_corrections, get_product_prices, get_product_compare, get_local_prices, get_user_corrections
from app.utils import get_current_user
from app.models.user import User
import logging

logger = logging.getLogger(__name__)

PRIVILEGED_ROLES = ["supervisor", "admin"]

router = APIRouter(
    tags=["products"]
)

@router.post("/products", response_model=Product)
def create_product_endpoint(product: ProductCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.rol not in PRIVILEGED_ROLES:
        raise HTTPException(status_code=403, detail="No tienes permisos para crear productos")
    
    try:
        return create_product(db, product)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error al crear producto: {str(e)}")
        raise HTTPException(status_code=500, detail="Error al crear el producto")

@router.get("/products/search", response_model=ProductSearchResponse)
def search_products_endpoint(barcode: str = None, name: str = None, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    try:
        if not barcode and not name:
            raise HTTPException(status_code=400, detail="Debe proporcionar al menos un parámetro: barcode o nombre del producto")
        return search_products(db, barcode, name)
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Error al buscar productos: {str(e)}")
        raise HTTPException(status_code=500, detail="Error al buscar productos")

@router.get("/products/barcode/{barcode}", response_model=Product)
def get_product_by_barcode_endpoint(barcode: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    try:
        product = get_product_by_barcode(db, barcode)
        if not product:
            raise HTTPException(status_code=404, detail="Producto no encontrado")
        return product
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Error al obtener producto por barcode: {str(e)}")
        raise HTTPException(status_code=500, detail="Error al obtener el producto")

@router.get("/products/{product_id}", response_model=Product)
def read_product(product_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    try:
        product = get_product(db, product_id)
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        return product
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Error al obtener producto: {str(e)}")
        raise HTTPException(status_code=500, detail="Error al obtener el producto")

@router.put("/products/{product_id}/price", response_model=Product)
def update_price(product_id: int, update: ProductUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    try:
        product = update_product_price(db, product_id, update, current_user.id, current_user.rol)
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        return product
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error al actualizar precio del producto: {str(e)}")
        raise HTTPException(status_code=500, detail="Error al actualizar el producto")

@router.get("/locals/{local_id}/corrections/count")
def get_corrections_count_endpoint(local_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    try:
        count = get_corrections_count(db, local_id)
        return {"count": count}
    except Exception as e:
        logger.error(f"Error al contar correcciones: {str(e)}")
        raise HTTPException(status_code=500, detail="Error al contar las correcciones")

@router.get("/corrections/pending", response_model=List[PriceCorrection])
def get_pending_corrections_endpoint(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.rol not in PRIVILEGED_ROLES:
        raise HTTPException(status_code=403, detail="No tienes permisos para ver correcciones pendientes")
    
    try:
        corrections = get_pending_corrections(db)
        return corrections
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Error al obtener correcciones pendientes: {str(e)}")
        raise HTTPException(status_code=500, detail="Error al obtener correcciones pendientes")

@router.put("/corrections/{correction_id}/approve")
def approve_correction(correction_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.rol not in PRIVILEGED_ROLES:
        raise HTTPException(status_code=403, detail="No tienes permisos para aprobar correcciones")
    
    try:
        correction = approve_price_correction(db, correction_id)
        return {"message": "Corrección aprobada exitosamente", "correction": correction}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error al aprobar corrección: {str(e)}")
        raise HTTPException(status_code=500, detail="Error al aprobar la corrección")

@router.get("/products/{product_id}/prices")
def get_product_prices_endpoint(product_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    try:
        prices = get_product_prices(db, product_id)
        return prices
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Error al obtener precios del producto {product_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Error al obtener precios")

@router.get("/products/{product_id}/compare")
def get_product_compare_endpoint(product_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    try:
        prices = get_product_compare(db, product_id)
        return prices
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Error al comparar precios del producto {product_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Error al comparar precios")

@router.get("/locals/{local_id}/prices")
def get_local_prices_endpoint(local_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    try:
        prices = get_local_prices(db, local_id)
        return prices
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Error al obtener precios del local {local_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Error al obtener precios del local")

@router.get("/users/{user_id}/corrections")
def get_user_corrections_endpoint(user_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.id != user_id and current_user.rol not in PRIVILEGED_ROLES:
        raise HTTPException(status_code=403, detail="No tienes permisos para ver las correcciones de este usuario")
    
    try:
        corrections = get_user_corrections(db, user_id)
        return corrections
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Error al obtener correcciones del usuario {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Error al obtener correcciones")