from sqlalchemy import Column, Integer, String, DateTime, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    brand = Column(String(255))
    presentation = Column(String(100))
    category = Column(String(100))
    barcode = Column(String(100), unique=True)
    image_url = Column(String(500))
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    prices = relationship("Price", back_populates="product")
    shopping_list_items = relationship("ShoppingListItem", back_populates="product")

    __table_args__ = (
        Index("idx_fulltext_name_brand", "name", "brand", mysql_prefix="FULLTEXT"),
    )
