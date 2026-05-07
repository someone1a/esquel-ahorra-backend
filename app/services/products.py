from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from app.models.product import Product, Price, Barcode
from app.models.price_history import PriceHistory
from app.models.price_correction import PriceCorrection
from app.models.user import User
from app.schemas.product import ProductCreate, ProductUpdate, ProductSearchResponse
from datetime import datetime, timezone
import logging
import unicodedata

logger = logging.getLogger(__name__)

PRIVILEGED_ROLES = ["supervisor", "admin"]

def normalize_text(text: str) -> str:
    """Normaliza texto: lowercase y sin acentos."""
    return unicodedata.normalize('NFD', text.lower()).encode('ascii', 'ignore').decode('ascii')

def create_product(db: Session, product: ProductCreate):
    try:
        db_product = Product(nombre=product.nombre)
        db.add(db_product)
        db.flush()
        
        db_barcode = Barcode(codigo_barra=product.codigo_barra, product_id=db_product.id)
        db.add(db_barcode)
        db.flush()
        
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
        barcode = db.query(Barcode).filter(Barcode.codigo_barra == codigo_barra).first()
        if barcode:
            return barcode.product
        return None
    except SQLAlchemyError as e:
        logger.error(f"Error en base de datos al obtener producto por código: {str(e)}")
        raise ValueError("Error al obtener el producto")

def update_product_price(db: Session, product_id: int, update: ProductUpdate, user_id: int, user_role: str):
    try:
        price = db.query(Price).filter(Price.product_id == product_id, Price.local_id == update.local_id).first()
        
        if user_role in PRIVILEGED_ROLES:
            if price:
                old_price = price.precio
                price.precio = update.precio
                price.updated_by = user_id
            else:
                price = Price(
                    product_id=product_id,
                    local_id=update.local_id,
                    precio=update.precio,
                    created_by=user_id,
                    updated_by=user_id
                )
                db.add(price)
                db.flush()
                old_price = 0

            price.verificado = "si"
            price.verificado_por = user_id
            price.verificado_en = datetime.now(timezone.utc)
            
            correction = PriceCorrection(
                product_id=product_id,
                old_price=old_price,
                new_price=update.precio,
                local_id=update.local_id,
                user_id=user_id,
                status="approved"
            )
            db.add(correction)

            history = PriceHistory(
                price_id=price.id,
                old_price=old_price,
                new_price=update.precio,
                changed_by=user_id
            )
            db.add(history)

            db.commit()
            db.refresh(price)
            return price.product
        else:
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
        normalized_query = normalize_text(query)
        return db.query(Product).filter(
            Product.nombre.ilike(f"%{normalized_query}%")
        ).all()
    except SQLAlchemyError as e:
        logger.error(f"Error en base de datos al buscar productos por nombre: {str(e)}")
        raise ValueError("Error al buscar productos por nombre")

def approve_price_correction(db: Session, correction_id: int, approver_id: int):
    try:
        correction = db.query(PriceCorrection).filter(PriceCorrection.id == correction_id).first()
        if not correction:
            raise ValueError("Corrección no encontrada")

        if correction.status != "pending":
            raise ValueError("La corrección ya ha sido procesada")

        price = db.query(Price).filter(
            Price.product_id == correction.product_id,
            Price.local_id == correction.local_id
        ).first()
        old_price = price.precio if price else 0

        if price:
            price.precio = correction.new_price
            price.updated_by = approver_id
        else:
            price = Price(
                product_id=correction.product_id,
                local_id=correction.local_id,
                precio=correction.new_price,
                created_by=approver_id,
                updated_by=approver_id
            )
            db.add(price)
            db.flush()

        price.verificado = "si"
        price.verificado_por = approver_id
        price.verificado_en = datetime.now(timezone.utc)

        history = PriceHistory(
            price_id=price.id,
            old_price=old_price,
            new_price=correction.new_price,
            changed_by=approver_id
        )
        db.add(history)

        user = db.query(User).filter(User.id == correction.user_id).first()
        if user:
            user.points += 10

        correction.status = "approved"
        db.commit()
        return correction
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Error en base de datos al aprobar corrección: {str(e)}")
        raise ValueError("Error al aprobar la corrección")

def list_products(db: Session, skip: int, limit: int):
    try:
        return db.query(Product).offset(skip).limit(limit).all()
    except SQLAlchemyError as e:
        logger.error(f"Error en base de datos al listar productos: {str(e)}")
        raise ValueError("Error al listar productos")

def add_product_barcode(db: Session, product_id: int, codigo_barra: str):
    try:
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise ValueError("Producto no encontrado")

        exists = db.query(Barcode).filter(Barcode.codigo_barra == codigo_barra).first()
        if exists:
            raise ValueError("El código de barra ya existe")

        db_barcode = Barcode(codigo_barra=codigo_barra, product_id=product_id)
        db.add(db_barcode)
        db.commit()
        db.refresh(db_barcode)
        return db_barcode
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Error en base de datos al agregar barcode: {str(e)}")
        raise ValueError("Error al agregar el código de barras")

def get_product_prices_with_locals(db: Session, product_id: int):
    try:
        return db.query(Price).filter(Price.product_id == product_id).all()
    except SQLAlchemyError as e:
        logger.error(f"Error al obtener precios del producto {product_id}: {str(e)}")
        raise ValueError("Error al obtener precios")

def get_product_compare_response(db: Session, product_id: int):
    try:
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            return None

        prices = db.query(Price).filter(Price.product_id == product_id).order_by(Price.precio.asc()).all()
        return {"product": product, "prices": prices}
    except SQLAlchemyError as e:
        logger.error(f"Error al comparar precios del producto {product_id}: {str(e)}")
        raise ValueError("Error al comparar precios")

def get_product_price_history(db: Session, product_id: int, local_id: int):
    try:
        price = db.query(Price).filter(Price.product_id == product_id, Price.local_id == local_id).first()
        if not price:
            return []
        return db.query(PriceHistory).filter(PriceHistory.price_id == price.id).order_by(PriceHistory.changed_at.desc()).all()
    except SQLAlchemyError as e:
        logger.error(f"Error al obtener historial de precios: {str(e)}")
        raise ValueError("Error al obtener historial de precios")

def list_price_corrections(
    db: Session,
    status: str | None,
    local_id: int | None,
    product_id: int | None,
    skip: int,
    limit: int
):
    try:
        q = db.query(PriceCorrection)
        if status:
            q = q.filter(PriceCorrection.status == status)
        if local_id is not None:
            q = q.filter(PriceCorrection.local_id == local_id)
        if product_id is not None:
            q = q.filter(PriceCorrection.product_id == product_id)
        return q.order_by(PriceCorrection.timestamp.desc()).offset(skip).limit(limit).all()
    except SQLAlchemyError as e:
        logger.error(f"Error al listar correcciones: {str(e)}")
        raise ValueError("Error al listar correcciones")

def reject_price_correction(db: Session, correction_id: int):
    try:
        correction = db.query(PriceCorrection).filter(PriceCorrection.id == correction_id).first()
        if not correction:
            raise ValueError("Corrección no encontrada")
        if correction.status != "pending":
            raise ValueError("La corrección ya ha sido procesada")
        correction.status = "rejected"
        db.commit()
        return correction
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Error al rechazar corrección: {str(e)}")
        raise ValueError("Error al rechazar la corrección")

def get_pending_corrections(db: Session):
    try:
        return db.query(PriceCorrection).filter(PriceCorrection.status == "pending").all()
    except SQLAlchemyError as e:
        logger.error(f"Error en base de datos al obtener correcciones pendientes: {str(e)}")
        raise ValueError("Error al obtener correcciones pendientes")

def search_products(db: Session, barcode: str = None, name: str = None):
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

def get_product_prices(db: Session, product_id: int):
    try:
        return db.query(Price).filter(Price.product_id == product_id).all()
    except SQLAlchemyError as e:
        logger.error(f"Error al obtener precios del producto {product_id}: {str(e)}")
        raise ValueError("Error al obtener precios")

def get_product_compare(db: Session, product_id: int):
    try:
        prices = db.query(Price).filter(Price.product_id == product_id).order_by(Price.precio.asc()).all()
        return prices
    except SQLAlchemyError as e:
        logger.error(f"Error al comparar precios del producto {product_id}: {str(e)}")
        raise ValueError("Error al comparar precios")

def get_local_prices(db: Session, local_id: int):
    try:
        return db.query(Price).filter(Price.local_id == local_id).all()
    except SQLAlchemyError as e:
        logger.error(f"Error al obtener precios del local {local_id}: {str(e)}")
        raise ValueError("Error al obtener precios del local")

def get_user_corrections(db: Session, user_id: int):
    try:
        return db.query(PriceCorrection).filter(PriceCorrection.user_id == user_id).all()
    except SQLAlchemyError as e:
        logger.error(f"Error al obtener correcciones del usuario {user_id}: {str(e)}")
        raise ValueError("Error al obtener correcciones")
