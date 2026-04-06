from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
from decimal import Decimal


class ShoppingListItemCreate(BaseModel):
    product_id: int
    store_id: Optional[int] = None
    price_snapshot: Optional[Decimal] = None


class ProductInfo(BaseModel):
    id: int
    name: str
    brand: Optional[str]
    presentation: Optional[str]
    image_url: Optional[str]

    class Config:
        from_attributes = True


class StoreInfo(BaseModel):
    id: int
    name: str
    branch: Optional[str]

    class Config:
        from_attributes = True


class ShoppingListItemOut(BaseModel):
    id: int
    list_id: int
    product_id: int
    store_id: Optional[int]
    price_snapshot: Optional[Decimal]
    checked: bool
    added_at: datetime
    product: Optional[ProductInfo]
    store: Optional[StoreInfo]

    class Config:
        from_attributes = True


class ShoppingListOut(BaseModel):
    id: int
    user_id: int
    created_at: datetime
    items: List[ShoppingListItemOut] = []

    class Config:
        from_attributes = True


class ShoppingListItemToggle(BaseModel):
    checked: bool
