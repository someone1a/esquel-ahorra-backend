from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.models.shopping_list import ShoppingList, ShoppingListItem
from app.models.product import Product
from app.models.store import Store
from app.schemas.shopping_list import (
    ShoppingListOut,
    ShoppingListItemCreate,
    ShoppingListItemOut,
    ShoppingListItemToggle,
)
from app.dependencies import get_db, get_current_user
from app.models.user import User

router = APIRouter(prefix="/api/shopping-list", tags=["shopping-list"])


def _get_or_create_list(db: Session, user_id: int) -> ShoppingList:
    shopping_list = db.query(ShoppingList).filter(ShoppingList.user_id == user_id).first()
    if not shopping_list:
        shopping_list = ShoppingList(user_id=user_id)
        db.add(shopping_list)
        db.commit()
        db.refresh(shopping_list)
    return shopping_list


@router.get("/", response_model=ShoppingListOut)
def get_shopping_list(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    shopping_list = _get_or_create_list(db, current_user.id)
    return shopping_list


@router.post("/items", response_model=ShoppingListItemOut, status_code=status.HTTP_201_CREATED)
def add_item(
    payload: ShoppingListItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    product = db.query(Product).filter(Product.id == payload.product_id).first()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    if payload.store_id:
        store = db.query(Store).filter(Store.id == payload.store_id).first()
        if not store:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Store not found")

    shopping_list = _get_or_create_list(db, current_user.id)

    item = ShoppingListItem(
        list_id=shopping_list.id,
        product_id=payload.product_id,
        store_id=payload.store_id,
        price_snapshot=payload.price_snapshot,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.patch("/items/{item_id}", response_model=ShoppingListItemOut)
def toggle_item(
    item_id: int,
    payload: ShoppingListItemToggle,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    item = db.query(ShoppingListItem).filter(ShoppingListItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")

    shopping_list = db.query(ShoppingList).filter(
        ShoppingList.id == item.list_id,
        ShoppingList.user_id == current_user.id,
    ).first()
    if not shopping_list:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    item.checked = payload.checked
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    item = db.query(ShoppingListItem).filter(ShoppingListItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")

    shopping_list = db.query(ShoppingList).filter(
        ShoppingList.id == item.list_id,
        ShoppingList.user_id == current_user.id,
    ).first()
    if not shopping_list:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    db.delete(item)
    db.commit()
