from pydantic import BaseModel
from typing import List, Optional

class ProductBase(BaseModel):
    nombre: str
    codigo_barra: str

class ProductCreate(ProductBase):
    precio: float
    local_id: int

class Product(ProductBase):
    id: int
    prices: Optional[List["Price"]] = None

    class Config:
        from_attributes = True

class PriceBase(BaseModel):
    product_id: int
    local_id: int
    precio: float

class Price(PriceBase):
    id: int

    class Config:
        from_attributes = True

class ProductUpdate(BaseModel):
    precio: float
    local_id: int

class ProductSearchRequest(BaseModel):
    barcode: Optional[str] = None
    name: Optional[str] = None

class ProductSearchResponse(BaseModel):
    status: str  # "exact_match", "partial_matches", "not_found"
    product: Optional[Product] = None
    products: Optional[List[Product]] = None
    message: str

class PriceCorrectionBase(BaseModel):
    product_id: int
    old_price: float
    new_price: float
    local_id: int
    user_id: int
    status: str

class PriceCorrection(PriceCorrectionBase):
    id: int
    timestamp: str

    class Config:
        from_attributes = True