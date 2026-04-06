from sqlalchemy import Column, Integer, String, Text, DECIMAL, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class Store(Base):
    __tablename__ = "stores"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    branch = Column(String(255))
    address = Column(Text)
    lat = Column(DECIMAL(10, 8))
    lng = Column(DECIMAL(11, 8))
    logo_url = Column(String(500))
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    prices = relationship("Price", back_populates="store")
    shopping_list_items = relationship("ShoppingListItem", back_populates="store")
