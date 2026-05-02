from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base
import uuid

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    lastname = Column(String(255), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    rol = Column(String(50), nullable=False)
    points = Column(Integer, default=0)
    referral_code = Column(String(50), unique=True, default=lambda: str(uuid.uuid4())[:8])
    referred_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    referred_by = relationship("User", remote_side=[id], backref="referrals")
    created_prices = relationship("Price", foreign_keys="Price.created_by", back_populates="creator")
    updated_prices = relationship("Price", foreign_keys="Price.updated_by", back_populates="updater")
    verified_prices = relationship("Price", foreign_keys="Price.verificado_por", back_populates="verificador")