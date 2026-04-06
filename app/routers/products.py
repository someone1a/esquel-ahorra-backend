from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.models.product import Product
from app.models.price import Price
from app.schemas.product import (
    ProductCreate,
    ProductOut,
    ProductDetail,
    BestPrice,
    StoreSummary,
    BarcodeResult,
    ProductSuggestion,
)
from app.dependencies import get_db, get_current_user
from app.models.user import User
from app.services.openfoodfacts_service import lookup_barcode

router = APIRouter(prefix="/api/products", tags=["products"])


@router.get("/", response_model=List[ProductOut])
def list_products(
    search: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    query = db.query(Product)
    if search:
        query = query.filter(
            text("MATCH(products.name, products.brand) AGAINST(:search IN BOOLEAN MODE)").bindparams(
                search=f"{search}*"
            )
        )
    if category:
        query = query.filter(Product.category == category)
    return query.all()


@router.get("/barcode/{barcode}", response_model=BarcodeResult)
async def get_by_barcode(barcode: str, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.barcode == barcode).first()
    if product:
        return BarcodeResult(found_in_db=True, product=ProductOut.model_validate(product))

    off_data = await lookup_barcode(barcode)
    if off_data:
        return BarcodeResult(
            found_in_db=False,
            suggestion=ProductSuggestion(
                name=off_data.name,
                brand=off_data.brand,
                presentation=off_data.presentation,
                category=off_data.category,
                image_url=off_data.image_url,
                barcode=off_data.barcode,
            ),
        )

    return BarcodeResult(found_in_db=False)


@router.get("/{product_id}", response_model=ProductDetail)
def get_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    prices = (
        db.query(Price)
        .filter(Price.product_id == product_id)
        .order_by(Price.price.asc())
        .all()
    )

    best_prices = []
    seen_stores = set()
    for p in prices:
        if p.store_id not in seen_stores:
            seen_stores.add(p.store_id)
            confirmation_count = len(p.confirmations_list)
            best_prices.append(
                BestPrice(
                    price_id=p.id,
                    price=p.price,
                    status=p.status,
                    store=StoreSummary.model_validate(p.store),
                    confirmation_count=confirmation_count,
                )
            )

    return ProductDetail(
        **{c.name: getattr(product, c.name) for c in product.__table__.columns},
        best_prices=best_prices,
    )


@router.post("/", response_model=ProductOut, status_code=status.HTTP_201_CREATED)
def create_product(
    payload: ProductCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if payload.barcode:
        existing = db.query(Product).filter(Product.barcode == payload.barcode).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Barcode already registered",
            )
    product = Product(**payload.model_dump())
    db.add(product)
    db.commit()
    db.refresh(product)
    return product
