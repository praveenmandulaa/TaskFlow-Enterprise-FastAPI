
from sqlalchemy.orm import Session

from app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_refresh_token,
    refresh_expiration,
)
from app.models.refresh_session import RefreshSession
from app.models.user import User
from app.schemas.auth import TokenResponse


def issue_token_pair(
    db: Session,
    user: User,
) -> TokenResponse:

    refresh_token = create_refresh_token()

    session = RefreshSession(
        user_id=user.id,
        token_hash=hash_refresh_token(refresh_token),
        expires_at=refresh_expiration(),
    )

    db.add(session)
    db.commit()

    return TokenResponse(
        access_token=create_access_token(user.id),
        refresh_token=refresh_token,
    )
