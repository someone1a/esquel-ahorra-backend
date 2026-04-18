from pydantic import BaseModel
from typing import Optional

class LocalBase(BaseModel):
    nombre: str
    direccion: str
    telefono: Optional[str] = None

class LocalCreate(LocalBase):
    pass

class Local(LocalBase):
    id: int
    is_active: bool

    class Config:
        from_attributes = True
