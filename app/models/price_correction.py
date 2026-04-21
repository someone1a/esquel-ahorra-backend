from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey, String
from app.database import Base
from datetime import datetime

class PriceCorrection(Base):
    __tablename__ = "price_corrections"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    old_price = Column(Float, nullable=False)
    new_price = Column(Float, nullable=False)
    local_id = Column(Integer, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(String(20), default="pending")  # pending, approved, rejected
    timestamp = Column(DateTime, default=datetime.utcnow)