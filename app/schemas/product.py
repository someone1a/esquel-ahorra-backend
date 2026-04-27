from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional

class ProductBase(BaseModel):
    nombre: str

class BarcodeBase(BaseModel):
    codigo_barra: str

class Barcode(BarcodeBase):
    id: int
    product_id: int

    class Config:
        from_attributes = True

class ProductCreate(ProductBase):
    precio: float
    local_id: int
    codigo_barra: str  # Se usa al crear para crear el barcode

class Product(ProductBase):
    id: int
    barcodes: Optional[List[Barcode]] = None
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
    timestamp: datetime  # era str, ahora datetime

    class Config:
        from_attributes = True