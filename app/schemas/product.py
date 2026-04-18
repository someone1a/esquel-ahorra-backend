from pydantic import BaseModel

class ProductBase(BaseModel):
    nombre: str
    codigo_barra: str
    precio: float
    local_id: int

class ProductCreate(ProductBase):
    pass

class Product(ProductBase):
    id: int

    class Config:
        from_attributes = True

class ProductUpdate(BaseModel):
    precio: float