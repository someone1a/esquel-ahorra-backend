from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from decimal import Decimal


class StoreOut(BaseModel):
    id: int
    name: str
    branch: Optional[str]
    address: Optional[str]
    lat: Optional[Decimal]
    lng: Optional[Decimal]
    logo_url: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True
