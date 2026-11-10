"""
Authentication service: register, login, token generation.
"""
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from core.currencies import get_currency
from core.security import create_access_token, hash_password, verify_password
from models.models import User
from schemas.schemas import UserRegister, UserLogin, TokenResponse, UserRead


def register_user(db: Session, data: UserRegister) -> TokenResponse:
    """Register a new user and return an access token."""
    # Check if email already exists
    existing = db.query(User).filter(User.email == data.email.lower()).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe una cuenta con ese email",
        )

    # Validate currency
    currency = get_currency(data.currency_code)
    if not currency:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Moneda no soportada: {data.currency_code}",
        )

    user = User(
        email=data.email.lower().strip(),
        username=data.username.strip(),
        hashed_password=hash_password(data.password),
        currency_code=data.currency_code.upper(),
        locale=currency["locale"],
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token({"sub": str(user.id)})
    return TokenResponse(
        access_token=token,
        user=UserRead.model_validate(user),
    )


def login_user(db: Session, data: UserLogin) -> TokenResponse:
    """Authenticate a user and return an access token."""
    user = db.query(User).filter(User.email == data.email.lower()).first()
    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email o contraseña incorrectos",
        )

    token = create_access_token({"sub": str(user.id)})
    return TokenResponse(
        access_token=token,
        user=UserRead.model_validate(user),
    )
