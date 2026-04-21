from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from app.models.product import Product, Price
from app.models.price_correction import PriceCorrection
from app.schemas.product import ProductCreate, ProductUpdate, ProductSearchResponse
import logging

logger = logging.getLogger(__name__)

def create_product(db: Session, product: ProductCreate):
    try:
        # Crear el producto
        db_product = Product(nombre=product.nombre, codigo_barra=product.codigo_barra)
        db.add(db_product)
        db.flush()  # Para obtener el id
        
        # Crear el precio
        db_price = Price(product_id=db_product.id, local_id=product.local_id, precio=product.precio)
        db.add(db_price)
        
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

def update_product_price(db: Session, product_id: int, update: ProductUpdate, user_id: int, user_role: str):
    try:
        # Buscar el precio existente para este producto y local
        price = db.query(Price).filter(Price.product_id == product_id, Price.local_id == update.local_id).first()
        
        if user_role == "supervisor":
            # Supervisores pueden actualizar directamente sin restricciones
            if price:
                old_price = price.precio
                price.precio = update.precio
            else:
                # Si no existe, crear uno nuevo
                price = Price(product_id=product_id, local_id=update.local_id, precio=update.precio)
                db.add(price)
                old_price = 0
            
            correction = PriceCorrection(
                product_id=product_id,
                old_price=old_price,
                new_price=update.precio,
                local_id=update.local_id,
                user_id=user_id,
                status="approved"  # Aprobado automáticamente para supervisores
            )
            db.add(correction)
            db.commit()
            db.refresh(price)
            return price.product
        else:
            # Usuarios normales requieren aprobación para ser más estrictos
            old_price = price.precio if price else 0
            correction = PriceCorrection(
                product_id=product_id,
                old_price=old_price,
                new_price=update.precio,
                local_id=update.local_id,
                user_id=user_id,
                status="pending"
            )
            db.add(correction)
            db.commit()
            # No actualizar el precio aún, esperar aprobación
            return db.query(Product).filter(Product.id == product_id).first()
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

def search_products_by_name(db: Session, query: str):
    try:
        return db.query(Product).filter(Product.nombre.ilike(f"%{query}%")).all()
    except SQLAlchemyError as e:
        logger.error(f"Error en base de datos al buscar productos por nombre: {str(e)}")
        raise ValueError("Error al buscar productos por nombre")

def approve_price_correction(db: Session, correction_id: int):
    try:
        correction = db.query(PriceCorrection).filter(PriceCorrection.id == correction_id).first()
        if not correction:
            raise ValueError("Corrección no encontrada")
        
        if correction.status != "pending":
            raise ValueError("La corrección ya ha sido procesada")
        
        # Actualizar el precio
        price = db.query(Price).filter(Price.product_id == correction.product_id, Price.local_id == correction.local_id).first()
        if price:
            price.precio = correction.new_price
        else:
            # Crear precio si no existe
            price = Price(product_id=correction.product_id, local_id=correction.local_id, precio=correction.new_price)
            db.add(price)
        
        correction.status = "approved"
        db.commit()
        return correction
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Error en base de datos al aprobar corrección: {str(e)}")
        raise ValueError("Error al aprobar la corrección")

def get_pending_corrections(db: Session):
    try:
        return db.query(PriceCorrection).filter(PriceCorrection.status == "pending").all()
    except SQLAlchemyError as e:
        logger.error(f"Error en base de datos al obtener correcciones pendientes: {str(e)}")
        raise ValueError("Error al obtener correcciones pendientes")
    try:
        if barcode:
            product = get_product_by_barcode(db, barcode)
            if product:
                return ProductSearchResponse(
                    status="exact_match",
                    product=product,
                    message="Producto encontrado por código de barras"
                )
        
        if name:
            products = search_products_by_name(db, name)
            if products:
                return ProductSearchResponse(
                    status="partial_matches",
                    products=products,
                    message=f"Encontrados {len(products)} productos que coinciden con '{name}'"
                )
        
        return ProductSearchResponse(
            status="not_found",
            message="No se encontraron productos que coincidan con los criterios de búsqueda"
        )
    except SQLAlchemyError as e:
        logger.error(f"Error en base de datos al buscar productos: {str(e)}")
        raise ValueError("Error al buscar productos")