
from sqlalchemy import Column, Integer, String, DateTime
from app.database import Base
from datetime import datetime, timezone

class TokenBlacklist(Base):
    __tablename__ = "token_blacklist"

    id = Column(Integer, primary_key=True, index=True)
    jti = Column(String(64), unique=True, nullable=False, index=True)  # JWT ID único
    expires_at = Column(DateTime, nullable=False)  # Para poder limpiar tokens vencidos
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))