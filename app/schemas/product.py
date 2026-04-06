from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
from decimal import Decimal


class ProductCreate(BaseModel):
    name: str
    brand: Optional[str] = None
    presentation: Optional[str] = None
    category: Optional[str] = None
    barcode: Optional[str] = None
    image_url: Optional[str] = None


class ProductOut(BaseModel):
    id: int
    name: str
    brand: Optional[str]
    presentation: Optional[str]
    category: Optional[str]
    barcode: Optional[str]
    image_url: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class StoreSummary(BaseModel):
    id: int
    name: str
    branch: Optional[str]
    address: Optional[str]
    logo_url: Optional[str]

    class Config:
        from_attributes = True


class BestPrice(BaseModel):
    price_id: int
    price: Decimal
    status: str
    store: StoreSummary
    confirmation_count: int


class ProductDetail(ProductOut):
    best_prices: List[BestPrice] = []


class ProductSuggestion(BaseModel):
    name: str
    brand: Optional[str]
    presentation: Optional[str]
    category: Optional[str]
    image_url: Optional[str]
    barcode: str
    source: str = "openfoodfacts"


class BarcodeResult(BaseModel):
    found_in_db: bool
    product: Optional[ProductOut] = None
    suggestion: Optional[ProductSuggestion] = None
