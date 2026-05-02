
import os
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import auth as schemas
from app.utils import get_current_user
from app.models.user import User
from app.services.auth import (
    register_user,
    login_user,
    logout_user,
    refresh_user_token,
    get_user_profile,
    get_invite_link,
    send_supervisor_invitation,
    check_rate_limit,
    get_client_ip,
    _login_attempts,
    _register_attempts,
    MAX_LOGIN_ATTEMPTS,
    MAX_REGISTER_ATTEMPTS,
    WINDOW_SECONDS,
)
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])

# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/register", response_model=schemas.Token)
async def register(request: Request, user_data: schemas.RegisterRequest, db: Session = Depends(get_db)):
    client_ip = get_client_ip(request.headers.get("X-Forwarded-For"), request.client.host)
    check_rate_limit(_register_attempts, client_ip, MAX_REGISTER_ATTEMPTS, WINDOW_SECONDS)
    return register_user(db, user_data)


@router.post("/login", response_model=schemas.Token)
async def login(request: Request, login_data: schemas.LoginRequest, db: Session = Depends(get_db)):
    client_ip = get_client_ip(request.headers.get("X-Forwarded-For"), request.client.host)
    check_rate_limit(_login_attempts, client_ip, MAX_LOGIN_ATTEMPTS, WINDOW_SECONDS)
    return login_user(db, login_data.email, login_data.password)


@router.post("/logout")
async def logout(
    refresh_token: str,
    db: Session = Depends(get_db),
):
    logout_user(refresh_token, db)
    return {"detail": "Sesión cerrada exitosamente"}


@router.post("/refresh", response_model=schemas.Token)
async def refresh(refresh_token: str, db: Session = Depends(get_db)):
    return refresh_user_token(refresh_token, db)


@router.get("/me", response_model=schemas.UserProfile)
async def get_me(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return get_user_profile(current_user, db)


@router.get("/invite-link")
@router.get("/invite")
async def invite_link(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    base_url = os.getenv("FRONTEND_URL", "https://esquel-ahorra.online")
    return get_invite_link(current_user, db, base_url)


@router.post("/invite")
async def invite_supervisor(
    invite_data: schemas.InviteSupervisorRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    send_supervisor_invitation(current_user, invite_data.email, db)
    return {"detail": "Invitación enviada"}