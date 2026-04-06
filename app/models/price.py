from sqlalchemy import Column, Integer, ForeignKey, DECIMAL, Enum, DateTime, UniqueConstraint, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class Price(Base):
    __tablename__ = "prices"

    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    store_id = Column(Integer, ForeignKey("stores.id"), nullable=False)
    price = Column(DECIMAL(10, 2), nullable=False)
    reported_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(
        Enum("unconfirmed", "recent", "confirmed"),
        default="unconfirmed",
        nullable=False,
    )
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    product = relationship("Product", back_populates="prices")
    store = relationship("Store", back_populates="prices")
    reporter = relationship("User", back_populates="prices", foreign_keys=[reported_by])
    confirmations_list = relationship("PriceConfirmation", back_populates="price", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_product_store", "product_id", "store_id"),
    )


class PriceConfirmation(Base):
    __tablename__ = "price_confirmations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    price_id = Column(Integer, ForeignKey("prices.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    confirmed_at = Column(DateTime, server_default=func.now(), nullable=False)

    price = relationship("Price", back_populates="confirmations_list")
    user = relationship("User", back_populates="confirmations_given")

    __table_args__ = (
        UniqueConstraint("price_id", "user_id", name="uq_price_user_confirmation"),
    )
