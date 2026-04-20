from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from app.models.product import Product
from app.models.price_correction import PriceCorrection
from app.schemas.product import ProductCreate, ProductUpdate
import logging

logger = logging.getLogger(__name__)

def create_product(db: Session, product: ProductCreate):
    try:
        db_product = Product(**product.dict())
        db.add(db_product)
        db.commit()
        db.refresh(db_product)
        return db_product
    except IntegrityError as e:
        db.rollback()
        logger.error(f"Error de integridad al crear producto: {str(e)}")
        raise ValueError("El código de barra ya existe")
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Error en base de datos al crear producto: {str(e)}")
        raise ValueError("Error al crear el producto en la base de datos")

def get_product(db: Session, product_id: int):
    try:
        return db.query(Product).filter(Product.id == product_id).first()
    except SQLAlchemyError as e:
        logger.error(f"Error en base de datos al obtener producto: {str(e)}")
        raise ValueError("Error al obtener el producto")

def get_product_by_barcode(db: Session, codigo_barra: str):
    try:
        return db.query(Product).filter(Product.codigo_barra == codigo_barra).first()
    except SQLAlchemyError as e:
        logger.error(f"Error en base de datos al obtener producto por código: {str(e)}")
        raise ValueError("Error al obtener el producto")

def update_product_price(db: Session, product_id: int, update: ProductUpdate):
    try:
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
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Error en base de datos al actualizar precio: {str(e)}")
        raise ValueError("Error al actualizar el precio del producto")

def get_corrections_count(db: Session, local_id: int):
    try:
        return db.query(PriceCorrection).filter(PriceCorrection.local_id == local_id).count()
    except SQLAlchemyError as e:
        logger.error(f"Error en base de datos al contar correcciones: {str(e)}")
        return 0