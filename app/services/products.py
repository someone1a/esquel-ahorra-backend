from sqlalchemy.orm import Session
from app.models.product import Product
from app.models.price_correction import PriceCorrection
from app.schemas.product import ProductCreate, ProductUpdate

def create_product(db: Session, product: ProductCreate):
    db_product = Product(**product.dict())
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product

def get_product(db: Session, product_id: int):
    return db.query(Product).filter(Product.id == product_id).first()

def get_product_by_barcode(db: Session, codigo_barra: str):
    return db.query(Product).filter(Product.codigo_barra == codigo_barra).first()

def update_product_price(db: Session, product_id: int, update: ProductUpdate):
    product = get_product(db, product_id)
    if not product:
        return None
    old_price = product.precio
    product.precio = update.precio
    correction = PriceCorrection(
        product_id=product_id,
        old_price=old_price,
        new_price=update.precio,
        local_id=product.local_id
    )
    db.add(correction)
    db.commit()
    db.refresh(product)
    return product

def get_corrections_count(db: Session, local_id: int):
    return db.query(PriceCorrection).filter(PriceCorrection.local_id == local_id).count()