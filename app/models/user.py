from sqlalchemy import Column, Integer, String
from app.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    lastname = Column(String(255), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    rol = Column(String(50), nullable=False)
    points = Column(Integer, default=0)