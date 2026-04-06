from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from decimal import Decimal


class PriceCreate(BaseModel):
    product_id: int
    store_id: int
    price: Decimal


class ReporterOut(BaseModel):
    id: int
    email: str

    class Config:
        from_attributes = True


class StoreOut(BaseModel):
    id: int
    name: str
    branch: Optional[str]
    address: Optional[str]
    logo_url: Optional[str]

    class Config:
        from_attributes = True


class PriceOut(BaseModel):
    id: int
    product_id: int
    store_id: int
    price: Decimal
    status: str
    confirmation_count: int
    reporter: ReporterOut
    store: StoreOut
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PriceConfirmationOut(BaseModel):
    id: int
    price_id: int
    user_id: int
    confirmed_at: datetime

    class Config:
        from_attributes = True
