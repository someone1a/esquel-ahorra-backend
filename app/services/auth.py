import uuid
import random
import logging
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from fastapi import HTTPException, status

from app.models.user import User
from app.models.token_blacklist import TokenBlacklist
from app.models.price_correction import PriceCorrection
from app.schemas.auth import RegisterRequest
from app.utils import (
    get_password_hash,
    create_access_token,
    create_refresh_token,
    verify_token,
    blacklist_token,
    cleanup_expired_tokens,
    is_token_blacklisted,
    validate_password,
    authenticate_user,
)
from app.utils.mail_sender import send_welcome_email, send_invitation_email

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Rate limiting en memoria
# ---------------------------------------------------------------------------
_login_attempts: dict = {}
_register_attempts: dict = {}

MAX_LOGIN_ATTEMPTS = 5
MAX_REGISTER_ATTEMPTS = 10
WINDOW_SECONDS = 60


def check_rate_limit(store: dict, key: str, max_attempts: int, window: int) -> None:
    """
    Verifica si se ha excedido el límite de intentos dentro de una ventana de tiempo.
    Lanza HTTPException si se excede el límite.
    """
    now = datetime.now(timezone.utc)
    record = store.get(key)
    if record:
        elapsed = (now - record["window_start"]).total_seconds()
        if elapsed < window:
            if record["count"] >= max_attempts:
                retry_after = int(window - elapsed)
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Demasiados intentos. Esperá {retry_after} segundos.",
                    headers={"Retry-After": str(retry_after)},
                )
            record["count"] += 1
        else:
            store[key] = {"count": 1, "window_start": now}
    else:
        store[key] = {"count": 1, "window_start": now}


def get_client_ip(x_forwarded_for: str | None, client_host: str | None) -> str:
    """
    Extrae la dirección IP del cliente, considerando proxies.
    """
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip()
    return client_host or "unknown"

# ---------------------------------------------------------------------------
# Registro
# ---------------------------------------------------------------------------

def _resolve_referrer(db: Session, referral_code: str | None) -> User | None:
    """Busca y valida el usuario referente. Lanza HTTPException si el código no existe."""
    if not referral_code:
        return None
    referrer = db.query(User).filter(User.referral_code == referral_code).first()
    if not referrer:
        raise HTTPException(status_code=400, detail="El código de referido no es válido")
    return referrer


def _validate_role(rol: str, has_referrer: bool) -> None:
    """Valida que el rol sea permitido según si el usuario tiene referente."""
    allowed = ["comprador", "vendedor"]
    if has_referrer:
        allowed.append("supervisor")
    if rol not in allowed:
        detail = (
            "El rol de 'supervisor' requiere un código de invitación válido."
            if rol == "supervisor"
            else "Rol inválido."
        )
        raise HTTPException(status_code=400, detail=detail)


def _build_tokens(email: str, rol: str) -> dict:
    return {
        "access_token": create_access_token(data={"sub": email, "rol": rol}),
        "refresh_token": create_refresh_token(data={"sub": email, "rol": rol}),
        "token_type": "bearer",
        "rol": rol,
    }


def register_user(db: Session, user_data: RegisterRequest) -> dict:
    # Verificar duplicado
    if db.query(User).filter(User.email == user_data.email).first():
        raise HTTPException(status_code=400, detail="El email ya está registrado")

    if user_data.password != user_data.confirm_password:
        raise HTTPException(status_code=400, detail="Las contraseñas no coinciden")

    validate_password(user_data.password)

    referrer = _resolve_referrer(db, user_data.referral_code)
    _validate_role(user_data.rol, has_referrer=referrer is not None)

    try:
        new_user = User(
            email=user_data.email,
            name=user_data.name,
            lastname=user_data.lastname,
            hashed_password=get_password_hash(user_data.password),
            rol=user_data.rol,
            referred_by_id=referrer.id if referrer else None,
        )
        db.add(new_user)

        if referrer:
            referrer.points += 50

        db.commit()
        db.refresh(new_user)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="El email ya está registrado")
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Error en BD al registrar usuario: {e}")
        raise HTTPException(status_code=500, detail="Error al crear el usuario")

    # Email de bienvenida (no bloquea si falla)
    try:
        send_welcome_email(
            to_email=new_user.email,
            username=new_user.name,
            referral_code=new_user.referral_code,
        )
    except Exception as e:
        logger.warning(f"No se pudo enviar email de bienvenida a {new_user.email}: {e}")

    return _build_tokens(new_user.email, new_user.rol)


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------

def login_user(db: Session, email: str, password: str) -> dict:
    user = authenticate_user(db, email, password)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Email o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return _build_tokens(user.email, user.rol)


# ---------------------------------------------------------------------------
# Logout
# ---------------------------------------------------------------------------

def logout_user(token: str, db: Session) -> None:
    """Invalida el access token. Limpieza oportunista de tokens vencidos."""
    from app.utils import SECRET_KEY  # importación local para evitar circular
    payload = verify_token(token, SECRET_KEY)
    if payload:
        jti = payload.get("jti")
        exp = payload.get("exp")
        if jti and exp:
            expires_at = datetime.fromtimestamp(exp, tz=timezone.utc)
            blacklist_token(jti, expires_at, db)

    if random.randint(1, 20) == 1:
        try:
            cleanup_expired_tokens(db)
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Refresh
# ---------------------------------------------------------------------------

def refresh_user_token(refresh_token: str, db: Session) -> dict:
    from app.utils import REFRESH_SECRET_KEY  # importación local para evitar circular

    payload = verify_token(refresh_token, REFRESH_SECRET_KEY)
    if not payload:
        raise HTTPException(status_code=401, detail="Token inválido")

    jti = payload.get("jti")
    if not jti or is_token_blacklisted(jti, db):
        raise HTTPException(status_code=401, detail="Token inválido o sesión cerrada")

    email = payload.get("sub")
    rol = payload.get("rol")

    if not db.query(User).filter(User.email == email).first():
        raise HTTPException(status_code=401, detail="Usuario no encontrado")

    # Rotar: invalidar el refresh token usado
    exp = payload.get("exp")
    if exp:
        blacklist_token(jti, datetime.fromtimestamp(exp, tz=timezone.utc), db)

    return _build_tokens(email, rol)


# ---------------------------------------------------------------------------
# Perfil
# ---------------------------------------------------------------------------

def get_user_profile(user: User, db: Session) -> dict:
    # Generar referral_code si no tiene (usuarios antiguos)
    if not user.referral_code:
        user.referral_code = str(uuid.uuid4())[:8]
        db.commit()
        db.refresh(user)

    try:
        corrections_count = (
            db.query(PriceCorrection)
            .filter(PriceCorrection.user_id == user.id)
            .count()
        )
    except Exception as e:
        logger.warning(f"No se pudo contar correcciones para user {user.id}: {e}")
        corrections_count = 0

    return {
        "id": user.id,
        "email": user.email,
        "name": user.name,
        "lastname": user.lastname,
        "rol": user.rol,
        "points": user.points,
        "corrections_count": corrections_count,
        "referral_code": user.referral_code,
    }


# ---------------------------------------------------------------------------
# Invite link
# ---------------------------------------------------------------------------

def get_invite_link(user: User, db: Session, base_url: str) -> dict:
    if not user.referral_code:
        user.referral_code = str(uuid.uuid4())[:8]
        db.commit()
        db.refresh(user)

    return {
        "invite_link": f"{base_url}/register?ref={user.referral_code}",
        "referral_code": user.referral_code,
    }


def send_supervisor_invitation(
    inviter: User,
    to_email: str,
    db: Session,
) -> None:
    if inviter.rol not in ["supervisor", "admin"]:
        raise HTTPException(status_code=403, detail="No tienes permisos para invitar supervisores")

    if not inviter.referral_code:
        inviter.referral_code = str(uuid.uuid4())[:8]
        db.commit()
        db.refresh(inviter)

    try:
        send_invitation_email(
            to_email=to_email,
            inviter_name=f"{inviter.name} {inviter.lastname}".strip() or "El equipo",
            referral_code=inviter.referral_code,
            invited_role="supervisor",
        )
    except Exception as e:
        logger.error(f"Error al enviar invitación a {to_email}: {e}")
        raise HTTPException(status_code=500, detail="No se pudo enviar la invitación")