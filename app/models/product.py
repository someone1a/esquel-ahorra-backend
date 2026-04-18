from sqlalchemy import Column, Integer, String, Float
from app.database import Base

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(255), nullable=False)
    codigo_barra = Column(String(255), unique=True, nullable=False)
    precio = Column(Float, nullable=False)
    local_id = Column(Integer, nullable=False)