from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, func, Index
from sqlalchemy.orm import relationship
from app.database import Base

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(255), nullable=False)
    marca = Column(String(255), nullable=True)
    presentacion = Column(String(255), nullable=True)
    categoria = Column(String(255), nullable=True)
    imagen_url = Column(String(500), nullable=True)
    
    # Relaciones
    barcodes = relationship("Barcode", back_populates="product", cascade="all, delete-orphan")
    prices = relationship("Price", back_populates="product")

class Barcode(Base):
    __tablename__ = "barcodes"

    id = Column(Integer, primary_key=True, index=True)
    codigo_barra = Column(String(255), unique=True, nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    
    # Relación inversa
    product = relationship("Product", back_populates="barcodes")

class Price(Base):
    __tablename__ = "prices"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    local_id = Column(Integer, ForeignKey("locals.id"), nullable=False)
    precio = Column(Float, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    updated_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    verificado = Column(String(10), default="no")  # 'si', 'no'
    verificado_por = Column(Integer, ForeignKey("users.id"), nullable=True)
    verificado_en = Column(DateTime, nullable=True)
    
    # Relaciones
    product = relationship("Product", back_populates="prices")
    local = relationship("Local", backref="prices")
    creator = relationship("User", foreign_keys=[created_by], back_populates="created_prices")
    updater = relationship("User", foreign_keys=[updated_by], back_populates="updated_prices")
    verificador = relationship("User", foreign_keys=[verificado_por], back_populates="verified_prices")

class PriceHistory(Base):
    __tablename__ = "price_history"

    id = Column(Integer, primary_key=True, index=True)
    price_id = Column(Integer, ForeignKey("prices.id"), nullable=False)
    old_price = Column(Float, nullable=False)
    new_price = Column(Float, nullable=False)
    changed_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    changed_at = Column(DateTime, default=func.now(), nullable=False)

# Índices importantes
Index('idx_price_product_local', Price.product_id, Price.local_id)
Index('idx_price_updated_by', Price.updated_by)
Index('idx_price_product_local_verified', Price.product_id, Price.local_id, Price.verificado)