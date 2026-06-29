import logging
from datetime import timedelta
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.api import deps
from app.core.config import settings
from app.core import jwt as jwt_core
from app.schemas.auth_token import Token
from app.schemas.user import UserCreate, UserResponse
from app.services import user as user_service

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/register", response_model=UserResponse)
def register(
    *,
    db: Session = Depends(deps.get_db),
    user_in: UserCreate,
) -> Any:
    user = user_service.get_user_by_email(db, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=400,
            detail="Este e-mail já está cadastrado.",
        )
    try:
        user = user_service.create_user(db, user_in=user_in)
    except SQLAlchemyError:
        db.rollback()
        logger.exception("Falha de banco ao criar usuário.")
        raise HTTPException(
            status_code=500,
            detail="Falha ao salvar usuário. Verifique os logs do backend.",
        )
    except Exception:
        db.rollback()
        logger.exception("Erro inesperado ao criar usuário.")
        raise HTTPException(
            status_code=500,
            detail="Erro interno ao criar usuário. Verifique os logs do backend.",
        )
    return user

@router.post("/login", response_model=Token)
def login_access_token(
    db: Session = Depends(deps.get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    user = user_service.authenticate_user(
        db, email=form_data.username, password=form_data.password
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-mail ou senha incorretos.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    elif not user.is_active:
        raise HTTPException(status_code=400, detail="Usuário inativo.")
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return {
        "access_token": jwt_core.create_access_token(
            user.id, expires_delta=access_token_expires
        ),
        "token_type": "bearer",
    }
