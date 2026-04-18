from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.product import ProductCreate, Product, ProductUpdate
from app.services.products import create_product, get_product, get_product_by_barcode, update_product_price, get_corrections_count
from app.utils import get_current_user
from app.models.user import User

router = APIRouter(
    tags=["products"]
)

@router.post("/products", response_model=Product)
def create_product_endpoint(product: ProductCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return create_product(db, product)

@router.get("/products/{product_id}", response_model=Product)
def read_product(product_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    product = get_product(db, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@router.get("/products/barcode/{codigo_barra}", response_model=Product)
def read_product_by_barcode(codigo_barra: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    product = get_product_by_barcode(db, codigo_barra)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@router.put("/products/{product_id}/price", response_model=Product)
def update_price(product_id: int, update: ProductUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    try:
        product = update_product_price(db, product_id, update)
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        return product
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/locals/{local_id}/corrections/count")
def get_corrections_count_endpoint(local_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    count = get_corrections_count(db, local_id)
    return {"count": count}