from pydantic import BaseModel, field_validator
from typing import Optional, List

class LocalBase(BaseModel):
    nombre: str
    direccion: str
    telefono: Optional[str] = None

class LocalCreate(LocalBase):
    pass

class Local(LocalBase):
    id: int
    is_active: Optional[bool] = True

    @field_validator('is_active', mode='before')
    @classmethod
    def validate_is_active(cls, v):
        # Si es None, devuelve True (por defecto)
        return v if v is not None else True

    class Config:
        from_attributes = True

class ProductoConPrecio(BaseModel):
    id: int
    nombre: str
    precio: float

    class Config:
        from_attributes = True

class LocalConProductos(LocalBase):
    id: int
    is_active: Optional[bool] = True
    productos: List[ProductoConPrecio] = []

    class Config:
        from_attributes = True
