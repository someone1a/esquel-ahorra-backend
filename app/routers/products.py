from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from typing import List
from app.database import get_db
from app.schemas.product import Barcode, BarcodeCreate, PriceCorrection, PriceHistoryEntry, Product, ProductCompareResponse, ProductCreate, ProductPriceEntry, ProductUpdate, ProductSearchResponse
from app.services.products import add_product_barcode, approve_price_correction, create_product, get_corrections_count, get_local_prices, get_pending_corrections, get_product, get_product_by_barcode, get_product_compare_response, get_product_price_history, get_product_prices_with_locals, get_user_corrections, list_products, search_products, update_product_price
from app.utils import get_current_user
from app.models.user import User
import logging

logger = logging.getLogger(__name__)

PRIVILEGED_ROLES = ["supervisor", "admin"]

router = APIRouter(
    tags=["products"]
)

@router.get("/products", response_model=List[Product])
def list_products_endpoint(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db)
):
    try:
        return list_products(db, skip, limit)
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Error al listar productos: {str(e)}")
        raise HTTPException(status_code=500, detail="Error al listar productos")

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
def search_products_endpoint(barcode: str = None, name: str = None, db: Session = Depends(get_db)):
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
def get_product_by_barcode_endpoint(barcode: str, db: Session = Depends(get_db)):
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
def read_product(product_id: int, db: Session = Depends(get_db)):
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
def get_pending_corrections_endpoint(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.rol not in PRIVILEGED_ROLES:
        raise HTTPException(status_code=403, detail="No tienes permisos para ver correcciones pendientes")
    
    try:
        corrections = get_pending_corrections(db)
        return corrections[skip:skip + limit]
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
        correction = approve_price_correction(db, correction_id, current_user.id)
        return {"message": "Corrección aprobada exitosamente", "correction": correction}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error al aprobar corrección: {str(e)}")
        raise HTTPException(status_code=500, detail="Error al aprobar la corrección")

@router.get("/products/{product_id}/prices", response_model=List[ProductPriceEntry])
def get_product_prices_endpoint(product_id: int, db: Session = Depends(get_db)):
    try:
        prices = get_product_prices_with_locals(db, product_id)
        return [
            {
                "local": p.local,
                "precio": p.precio,
                "updated_at": p.updated_at,
                "updated_by": p.updated_by,
                "verificado": p.verificado,
                "verificado_por": p.verificado_por,
                "verificado_en": p.verificado_en
            }
            for p in prices
        ]
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Error al obtener precios del producto {product_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Error al obtener precios")

@router.get("/products/{product_id}/compare", response_model=ProductCompareResponse)
def get_product_compare_endpoint(product_id: int, db: Session = Depends(get_db)):
    try:
        result = get_product_compare_response(db, product_id)
        if not result:
            raise HTTPException(status_code=404, detail="Producto no encontrado")

        product = result["product"]
        prices = result["prices"]
        return {
            "id": product.id,
            "nombre": product.nombre,
            "marca": product.marca,
            "presentacion": product.presentacion,
            "categoria": product.categoria,
            "imagen_url": product.imagen_url,
            "prices": [
                {
                    "local": p.local,
                    "precio": p.precio,
                    "updated_at": p.updated_at,
                    "updated_by": p.updated_by,
                    "verificado": p.verificado,
                    "verificado_por": p.verificado_por,
                    "verificado_en": p.verificado_en
                }
                for p in prices
            ]
        }
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Error al comparar precios del producto {product_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Error al comparar precios")

@router.get("/products/{product_id}/history", response_model=List[PriceHistoryEntry])
def get_product_history_endpoint(
    product_id: int,
    local_id: int = Query(..., ge=1),
    db: Session = Depends(get_db)
):
    try:
        return get_product_price_history(db, product_id, local_id)
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Error al obtener historial del producto {product_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Error al obtener historial")

@router.post("/products/{product_id}/barcodes", response_model=Barcode)
def add_barcode_endpoint(
    product_id: int,
    barcode: BarcodeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.rol not in PRIVILEGED_ROLES:
        raise HTTPException(status_code=403, detail="No tienes permisos para agregar códigos de barra")

    try:
        return add_product_barcode(db, product_id, barcode.codigo_barra)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error al agregar barcode al producto {product_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Error al agregar el código de barras")

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
