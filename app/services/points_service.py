from sqlalchemy.orm import Session
from app.models.user import User
from app.models.price import Price

POINTS_REPORT_PRICE = 10
POINTS_CONFIRM_PRICE = 5


def award_report_points(db: Session, user: User) -> None:
    user.points += POINTS_REPORT_PRICE
    user.prices_loaded += 1
    db.add(user)


def award_confirmation_points(db: Session, user: User) -> None:
    user.points += POINTS_CONFIRM_PRICE
    user.confirmations += 1
    db.add(user)


def update_price_status(db: Session, price: Price) -> None:
    count = len(price.confirmations_list)
    if count >= 3:
        price.status = "confirmed"
    elif count >= 1:
        price.status = "recent"
    else:
        price.status = "unconfirmed"
    db.add(price)
