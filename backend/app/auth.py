from typing import Annotated, Literal
from fastapi import Depends, HTTPException, status
from pwdlib import PasswordHash
from datetime import timedelta, datetime, UTC
from itsdangerous import URLSafeTimedSerializer
import jwt
import secrets
import hashlib

from fastapi.security import OAuth2PasswordBearer
from app.config import settings
from app.models import User, ResetToken
from app.schemas.user import UserSecureResponse
from app.models import ApiKey
from app.utils import extract_profile, generate_username

password_hash = PasswordHash.recommended()
oauth2_scheme = OAuth2PasswordBearer("/api/auth/token")
serializer = URLSafeTimedSerializer(
    secret_key=settings.secret_key.get_secret_value(), salt="email-confirmation"
)


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(password: str, hash: str) -> bool:
    return password_hash.verify(password, hash)


def generate_secure_token(type: str = "reset") -> str:
    if type == "api_key":
        return "sk_" + secrets.token_urlsafe(32)
    return secrets.token_urlsafe(32)


def hash_reset_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def hash_api_key(key: str) -> str:
    return hashlib.sha256(key.encode()).hexdigest()


def create_url_safe_token(data: dict):
    return serializer.dumps(
        data,
    )


def decode_url_safe_token(token: str):
    try:
        token_data = serializer.loads(
            token,
            max_age=int(
                timedelta(hours=settings.verify_token_expire_hours).total_seconds()
            ),
        )
        return token_data
    except Exception:
        None


def create_token(data: dict, type: str, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    if type == "refresh":
        expire = datetime.now(UTC) + timedelta(days=settings.refresh_token_expire_days)
    elif expires_delta is not None:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(
            minutes=settings.access_token_expire_minutes
        )
    to_encode.update({"exp": expire, "type": type})
    encoded_jwt = jwt.encode(
        payload=to_encode,
        key=settings.secret_key.get_secret_value(),
        algorithm=settings.algorithm,
    )
    return encoded_jwt


def verify_token(token: str, type: str = "access") -> str | None:
    try:
        payload = jwt.decode(
            jwt=token,
            key=settings.secret_key.get_secret_value(),
            algorithms=[settings.algorithm],
            options={"require": ["exp", "sub", "type"]},
        )
    except jwt.InvalidTokenError:
        return None
    if type == "access" and payload.get("type") != "access":
        return None
    elif type == "refresh" and payload.get("type") != "refresh":
        return None
    else:
        return payload.get("sub")


async def get_oauth_user(token: dict, provider: Literal["github", "google"]) -> User:
    user_data = extract_profile(token, provider)
    if user_data is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="invalid login",
        )

    existing_user = await User.find_one(User.email == user_data.email)

    if existing_user:
        if (
            existing_user.oauth_provider_id is None
            and existing_user.oauth_provider is None
        ):
            await existing_user.update(
                {
                    "$set": {
                        "oauth_provider_id": user_data.provider_id,
                        "oauth_provider": provider,
                        "is_verified": True,
                        "updated_at": datetime.now(UTC),
                    }
                }
            )
            return existing_user
        if existing_user.oauth_provider != provider:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"email already registered with {existing_user.oauth_provider}, please login with {existing_user.oauth_provider}",
            )
        return existing_user

    new_user = User(
        username=generate_username(user_data.name),
        email=user_data.email,
        oauth_provider=provider,
        oauth_provider_id=user_data.provider_id,
        is_verified=True,
    )
    await new_user.create()
    return new_user


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
):
    if token.startswith("sk_"):
        api_key = await ApiKey.find_one(ApiKey.key_hash == hash_api_key(token))
        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="invalid or expired api key",
            )

        token_exp = api_key.expires_at
        if token_exp is not None and token_exp.tzinfo is None:
            token_exp = token_exp.replace(tzinfo=UTC)
        if token_exp is not None and token_exp < datetime.now(UTC):
            await api_key.delete()
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="invalid or expired api key",
            )

        user = await User.find_one(User.id == api_key.user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="invalid or expired api key",
            )
        await api_key.update({"$set": {"last_used_at": datetime.now(UTC)}})
        await ResetToken.find_all(ResetToken.user_id == user.id).delete()
        return user

    user_id = verify_token(token)
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid or expired token",
        )

    user = await User.get(user_id, fetch_links=True)
    if not user or user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="user not found"
        )
    await ResetToken.find_all(ResetToken.user_id == user.id).delete()
    return user


currentUser = Annotated[UserSecureResponse, Depends(get_current_user)]
