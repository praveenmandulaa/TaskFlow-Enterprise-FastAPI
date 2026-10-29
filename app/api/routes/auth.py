
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    hash_refresh_token,
    refresh_expiration,
    verify_password,
)
from app.db.session import get_db
from app.models.refresh_session import RefreshSession
from app.models.user import User
from app.schemas.auth import (
    LoginRequest,
    LogoutRequest,
    RefreshRequest,
    TokenResponse,
)
from app.schemas.user import UserRegister, UserResponse
from app.services.auth_service import issue_token_pair


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def register(
    payload: UserRegister,
    db: Session = Depends(get_db),
):
    email = str(payload.email).strip().lower()

    existing_user = db.scalar(
        select(User).where(User.email == email)
    )

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    user = User(
        name=payload.name.strip(),
        email=email,
        hashed_password=hash_password(payload.password),
        role="employee",
        is_active=True,
    )

    db.add(user)

    try:
        db.commit()
        db.refresh(user)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    return user


@router.post(
    "/login",
    response_model=TokenResponse,
)
def login(
    payload: LoginRequest,
    db: Session = Depends(get_db),
):
    email = str(payload.email).strip().lower()

    user = db.scalar(
        select(User).where(User.email == email)
    )

    if not user or not verify_password(
        payload.password,
        user.hashed_password,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )

    return issue_token_pair(db, user)


@router.post(
    "/token",
    response_model=TokenResponse,
)
def login_for_swagger(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    email = form_data.username.strip().lower()

    user = db.scalar(
        select(User).where(User.email == email)
    )

    if not user or not verify_password(
        form_data.password,
        user.hashed_password,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )

    return issue_token_pair(db, user)


@router.post(
    "/refresh",
    response_model=TokenResponse,
)
def refresh_tokens(
    payload: RefreshRequest,
    db: Session = Depends(get_db),
):
    now = datetime.now(timezone.utc)
    token_hash = hash_refresh_token(
        payload.refresh_token
    )

    session = db.scalar(
        select(RefreshSession)
        .where(
            RefreshSession.token_hash == token_hash
        )
        .with_for_update()
    )

    if (
        session is None
        or session.revoked_at is not None
        or session.expires_at <= now
    ):
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    user = db.get(User, session.user_id)

    if user is None or not user.is_active:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh session",
        )

    # Revoke the old refresh token.
    session.revoked_at = now

    # Generate a replacement refresh token.
    new_refresh_token = create_refresh_token()

    new_session = RefreshSession(
        user_id=user.id,
        token_hash=hash_refresh_token(
            new_refresh_token
        ),
        expires_at=refresh_expiration(),
    )

    db.add(new_session)
    db.commit()

    return TokenResponse(
        access_token=create_access_token(user.id),
        refresh_token=new_refresh_token,
    )


@router.post("/logout")
def logout(
    payload: LogoutRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    token_hash = hash_refresh_token(
        payload.refresh_token
    )

    session = db.scalar(
        select(RefreshSession)
        .where(
            RefreshSession.token_hash == token_hash,
            RefreshSession.user_id == current_user.id,
        )
        .with_for_update()
    )

    if (
        session is not None
        and session.revoked_at is None
    ):
        session.revoked_at = datetime.now(timezone.utc)
        db.commit()
    else:
        db.rollback()

    return {
        "message": "Logged out successfully"
    }
