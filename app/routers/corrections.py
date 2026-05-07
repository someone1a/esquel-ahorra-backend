from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import logging

from app.database import get_db
from app.schemas.product import PriceCorrection
from app.services.products import list_price_corrections, reject_price_correction
from app.utils import get_current_user
from app.models.user import User


logger = logging.getLogger(__name__)

PRIVILEGED_ROLES = ["supervisor", "admin"]

router = APIRouter(
    tags=["corrections"]
)


@router.get("/corrections", response_model=List[PriceCorrection])
def list_corrections_endpoint(
    status: Optional[str] = None,
    local_id: Optional[int] = None,
    product_id: Optional[int] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.rol not in PRIVILEGED_ROLES:
        raise HTTPException(status_code=403, detail="No tienes permisos para ver correcciones")

    try:
        return list_price_corrections(db, status, local_id, product_id, skip, limit)
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Error al listar correcciones: {str(e)}")
        raise HTTPException(status_code=500, detail="Error al listar correcciones")


@router.put("/corrections/{correction_id}/reject", response_model=PriceCorrection)
def reject_correction_endpoint(
    correction_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.rol not in PRIVILEGED_ROLES:
        raise HTTPException(status_code=403, detail="No tienes permisos para rechazar correcciones")

    try:
        return reject_price_correction(db, correction_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error al rechazar corrección {correction_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Error al rechazar la corrección")

