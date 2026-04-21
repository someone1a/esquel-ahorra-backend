from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(255), nullable=False)
    codigo_barra = Column(String(255), unique=True, nullable=False)
    
    # Relación con precios
    prices = relationship("Price", back_populates="product")

class Price(Base):
    __tablename__ = "prices"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    local_id = Column(Integer, nullable=False)
    precio = Column(Float, nullable=False)
    
    # Relación inversa
    product = relationship("Product", back_populates="prices")