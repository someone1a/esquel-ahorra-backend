from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.models.price import Price, PriceConfirmation
from app.models.product import Product
from app.models.store import Store
from app.schemas.price import PriceCreate, PriceOut, PriceConfirmationOut
from app.dependencies import get_db, get_current_user
from app.models.user import User
from app.services.points_service import award_report_points, award_confirmation_points, update_price_status

router = APIRouter(prefix="/api/prices", tags=["prices"])


def _build_price_out(price: Price, db: Session) -> PriceOut:
    confirmation_count = len(price.confirmations_list)
    return PriceOut(
        id=price.id,
        product_id=price.product_id,
        store_id=price.store_id,
        price=price.price,
        status=price.status,
        confirmation_count=confirmation_count,
        reporter=price.reporter,
        store=price.store,
        created_at=price.created_at,
        updated_at=price.updated_at,
    )


@router.get("/", response_model=List[PriceOut])
def list_prices(product_id: int = Query(...), db: Session = Depends(get_db)):
    prices = (
        db.query(Price)
        .filter(Price.product_id == product_id)
        .order_by(Price.price.asc())
        .all()
    )
    return [_build_price_out(p, db) for p in prices]


@router.post("/", response_model=PriceOut, status_code=status.HTTP_201_CREATED)
def submit_price(
    payload: PriceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    product = db.query(Product).filter(Product.id == payload.product_id).first()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    store = db.query(Store).filter(Store.id == payload.store_id).first()
    if not store:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Store not found")

    price = Price(
        product_id=payload.product_id,
        store_id=payload.store_id,
        price=payload.price,
        reported_by=current_user.id,
    )
    db.add(price)
    award_report_points(db, current_user)
    db.commit()
    db.refresh(price)
    return _build_price_out(price, db)


@router.post("/{price_id}/confirm", response_model=PriceOut, status_code=status.HTTP_201_CREATED)
def confirm_price(
    price_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    price = db.query(Price).filter(Price.id == price_id).first()
    if not price:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Price not found")

    if price.reported_by == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot confirm your own reported price",
        )

    existing = (
        db.query(PriceConfirmation)
        .filter(
            PriceConfirmation.price_id == price_id,
            PriceConfirmation.user_id == current_user.id,
        )
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You have already confirmed this price",
        )

    confirmation = PriceConfirmation(price_id=price_id, user_id=current_user.id)
    db.add(confirmation)
    db.flush()

    db.refresh(price)
    update_price_status(db, price)
    award_confirmation_points(db, current_user)
    db.commit()
    db.refresh(price)
    return _build_price_out(price, db)
