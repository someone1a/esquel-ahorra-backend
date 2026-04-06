from sqlalchemy import Column, Integer, String, Enum, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(Enum("user", "collaborator", "supervisor"), default="user", nullable=False)
    points = Column(Integer, default=0, nullable=False)
    prices_loaded = Column(Integer, default=0, nullable=False)
    confirmations = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    prices = relationship("Price", back_populates="reporter", foreign_keys="Price.reported_by")
    confirmations_given = relationship("PriceConfirmation", back_populates="user")
    shopping_lists = relationship("ShoppingList", back_populates="user")
