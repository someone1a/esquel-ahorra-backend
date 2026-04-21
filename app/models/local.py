from sqlalchemy import Column, Integer, String, Boolean
from app.database import Base

class Local(Base):
    __tablename__ = "locals"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(255), nullable=False)
    direccion = Column(String(255), nullable=False)
    telefono = Column(String(50), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
