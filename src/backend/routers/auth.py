from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, SQLModel, select

from backend.auth.security import create_access_token, hash_password, verify_password
from db.models import User, UserCreate, UserRead
from db.session import get_session


router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(SQLModel):
    email: str
    password: str


class TokenResponse(SQLModel):
    access_token: str
    token_type: str = "bearer"


@router.post("/signup", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def signup(*, session: Session = Depends(get_session), payload: UserCreate):
    user = User(
        name=payload.name,
        email=payload.email,
        password=hash_password(payload.password),
    )
    session.add(user)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email already exists.",
        )

    session.refresh(user)
    return user


@router.post("/login", response_model=TokenResponse)
def login(*, session: Session = Depends(get_session), payload: LoginRequest):
    statement = select(User).where(User.email == payload.email)
    user = session.exec(statement).first()
    if not user or not verify_password(payload.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_access_token(subject=str(user.id))
    return TokenResponse(access_token=token)
