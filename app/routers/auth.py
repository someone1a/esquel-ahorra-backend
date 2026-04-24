import os
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from app.database import get_db
from app.schemas import auth as schemas
from app.utils import (
    authenticate_user,
    create_access_token,
    create_refresh_token,
    validate_password,
    verify_token,
    REFRESH_SECRET_KEY,
    get_current_user
)
from app.models import user as models
from app.utils import get_password_hash
from app.utils.mail_sender import send_invitation_email, send_welcome_email
from app.models.price_correction import PriceCorrection
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/auth",
    tags=["auth"]
)

@router.post("/register", response_model=schemas.Token)
async def register(user_data: schemas.RegisterRequest, db: Session = Depends(get_db)):
    try:
        # Verificar si el usuario ya existe
        db_user = db.query(models.User).filter(models.User.email == user_data.email).first()
        if db_user:
            raise HTTPException(
                status_code=400,
                detail="El email ya está registrado"
            )
        
        # Validar que las contraseñas coincidan
        if user_data.password != user_data.confirm_password:
            raise HTTPException(
                status_code=400,
                detail="Las contraseñas no coinciden"
            )
        
        # Validar la seguridad de la contraseña
        validate_password(user_data.password)
        
        # Buscar el referente si existe el código
        referred_by_id = None
        referrer = None
        if user_data.referral_code:
            referrer = db.query(models.User).filter(models.User.referral_code == user_data.referral_code).first()
            if referrer:
                referred_by_id = referrer.id
            else:
                raise HTTPException(
                    status_code=400,
                    detail="El código de referido no es válido"
                )
        
        # Validar el rol
        allowed_roles = ["comprador", "vendedor"]
        # Solo permitir rol 'supervisor' si tiene un código de referido (invitación) válido
        if referred_by_id:
            allowed_roles.append("supervisor")
            
        if user_data.rol not in allowed_roles:
            detail = "Rol inválido."
            if user_data.rol == "supervisor":
                detail = "El rol de 'supervisor' requiere un código de invitación válido."
            raise HTTPException(
                status_code=400,
                detail=detail
            )
        
        # Crear el usuario
        hashed_password = get_password_hash(user_data.password)
        
        db_user = models.User(
            email=user_data.email,
            name=user_data.name,
            lastname=user_data.lastname,
            hashed_password=hashed_password,
            rol=user_data.rol,
            referred_by_id=referred_by_id
        )
        
        db.add(db_user)
        # Si hay un referente válido, premiarlo
        if referrer:
            referrer.points += 50
            
        db.commit()
        db.refresh(db_user)
        
        # Enviar email de bienvenida (no detengas el proceso si falla)
        try:
            send_welcome_email(
                to_email=db_user.email,
                username=user_data.name,
                referral_code=db_user.referral_code
            )
        except Exception as e:
            logger.warning(f"No se pudo enviar email de bienvenida a {db_user.email}: {str(e)}")
        
        # Generar tokens
        access_token = create_access_token(
            data={"sub": db_user.email, "rol": db_user.rol}
        )
        refresh_token = create_refresh_token(
            data={"sub": db_user.email, "rol": db_user.rol}
        )
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "rol": db_user.rol
        }
    
    except HTTPException:
        raise
    except IntegrityError as e:
        db.rollback()
        logger.error(f"Error de integridad al registrar usuario: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail="El email ya está registrado"
        )
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Error en base de datos al registrar usuario: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Error al crear el usuario"
        )
    except Exception as e:
        db.rollback()
        logger.error(f"Error inesperado al registrar usuario: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Error al crear el usuario"
        )

@router.post("/login", response_model=schemas.Token)
async def login(
    login_data: schemas.LoginRequest,
    db: Session = Depends(get_db)
):
    try:
        user = authenticate_user(db, login_data.email, login_data.password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Email o contraseña incorrectos",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        access_token = create_access_token(data={"sub": user.email, "rol": user.rol})
        refresh_token = create_refresh_token(data={"sub": user.email, "rol": user.rol})
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "rol": user.rol
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al hacer login: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Error al iniciar sesión"
        )

@router.post("/refresh", response_model=schemas.Token)
async def refresh_token(refresh_token: str, db: Session = Depends(get_db)):
    try:
        # Verificar el refresh token
        payload = verify_token(refresh_token, REFRESH_SECRET_KEY)
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido"
            )
        
        email = payload.get("sub")
        rol = payload.get("rol")
        
        # Verificar que el usuario existe
        user = db.query(models.User).filter(models.User.email == email).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Usuario no encontrado"
            )
        
        # Generar nuevos tokens
        new_access_token = create_access_token(
            data={"sub": email, "rol": rol}
        )
        new_refresh_token = create_refresh_token(
            data={"sub": email, "rol": rol}
        )
        
        return {
            "access_token": new_access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al refrescar token: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No se pudo refrescar el token"
        )

@router.get("/me", response_model=schemas.UserProfile)
async def get_me(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        # Si el usuario no tiene código de referido (usuarios antiguos), generar uno
        if not current_user.referral_code:
            import uuid
            current_user.referral_code = str(uuid.uuid4())[:8]
            db.commit()
            db.refresh(current_user)

        # Contar las correcciones del usuario
        try:
            corrections_count = db.query(PriceCorrection).filter(
                PriceCorrection.user_id == current_user.id
            ).count()
        except Exception as e:
            logger.warning(f"No se pudo contar correcciones: {str(e)}")
            corrections_count = 0
        
        return {
            "id": current_user.id,
            "email": current_user.email,
            "name": current_user.name,
            "lastname": current_user.lastname,
            "rol": current_user.rol,
            "points": current_user.points,
            "corrections_count": corrections_count,
            "referral_code": current_user.referral_code
        }
    except Exception as e:
        logger.error(f"Error al obtener datos del usuario: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Error al obtener los datos del usuario"
        )

@router.get("/invite-link")
async def get_invite_link(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Asegurar que tenga código antes de generar el link
    if not current_user.referral_code:
        import uuid
        current_user.referral_code = str(uuid.uuid4())[:8]
        db.commit()
        db.refresh(current_user)

    # La URL base debería venir de una variable de entorno en producción
    base_url = os.getenv("FRONTEND_URL", "https://esquel-ahorra.online")
    invite_link = f"{base_url}/register?ref={current_user.referral_code}"
    return {"invite_link": invite_link, "referral_code": current_user.referral_code}

@router.get("/invite")
async def get_invite_link_alias(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return await get_invite_link(current_user=current_user, db=db)

@router.post("/invite")
async def invite_supervisor(
    invite_data: schemas.InviteSupervisorRequest,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.rol != "supervisor":
        raise HTTPException(status_code=403, detail="No tienes permisos para invitar supervisores")

    if not current_user.referral_code:
        import uuid
        current_user.referral_code = str(uuid.uuid4())[:8]
        db.commit()
        db.refresh(current_user)

    smtp_user = os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")
    if not smtp_user or not smtp_password:
        raise HTTPException(status_code=500, detail="SMTP no configurado (SMTP_USER/SMTP_PASSWORD)")

    try:
        inviter_name = f"{current_user.name} {current_user.lastname}".strip()
        send_invitation_email(
            to_email=invite_data.email,
            inviter_name=inviter_name or "El equipo",
            referral_code=current_user.referral_code,
            invited_role="supervisor"
        )
        return {"detail": "Invitación enviada"}
    except Exception as e:
        logger.error(f"Error al enviar invitación a {invite_data.email}: {str(e)}")
        raise HTTPException(status_code=500, detail="No se pudo enviar la invitación")
