from fastapi import APIRouter, Request, status, Depends, HTTPException, BackgroundTasks
from typing import Annotated, Literal
from fastapi.security import OAuth2PasswordRequestForm
from datetime import datetime, UTC, timedelta

from app.schemas.user import UserPrivateResponse
from app.schemas.auth import Token, RefreshToken, ForgotPassword, ResetPassword
from app.models import User, ResetToken
from app.auth import (
    hash_password,
    verify_token,
    verify_password,
    currentUser,
    create_token,
    generate_secure_token,
    hash_reset_token,
    get_oauth_user,
)
from app.config import settings
from app.email_utils import send_forgot_password_email, send_password_reset_confirmation
from app.services.oauth import get_oauth_client
from app.utils import REDIRECT_URLS

router = APIRouter()


@router.post("/token", response_model=Token, status_code=status.HTTP_202_ACCEPTED)
async def login_for_access_token(
    login_data: Annotated[OAuth2PasswordRequestForm, Depends()],
):
    user = await User.find_one(User.username == login_data.username)
    if not user or not verify_password(login_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid username or password",
        )
    await ResetToken.find(ResetToken.user_id == user.id).delete()
    expire_timedelta = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_token({"sub": str(user.id)}, "access", expire_timedelta)
    refresh_token = create_token({"sub": str(user.id)}, "refresh")
    return Token(
        access_token=access_token, refresh_token=refresh_token, token_type="Bearer"
    )


@router.post("/refresh", response_model=Token, status_code=status.HTTP_202_ACCEPTED)
async def refresh_access_token(token: RefreshToken):
    user_id = verify_token(token.refresh_token, "refresh")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid or expired token"
        )

    user = await User.get(user_id)
    if not user or user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="user not found"
        )
    await ResetToken.find(ResetToken.user_id == user.id).delete()
    expire_timedelta = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_token({"sub": str(user.id)}, "access", expire_timedelta)
    return Token(
        access_token=access_token,
        refresh_token=token.refresh_token,
        token_type="Bearer",
    )


@router.post("/forgot-password", status_code=status.HTTP_200_OK)
async def forgot_password(user_input: ForgotPassword, background_task: BackgroundTasks):
    user = await User.find_one(User.email == user_input.email)
    if user:
        await ResetToken.find(ResetToken.user_id == user.id).delete()
        expire = datetime.now(UTC) + timedelta(
            minutes=settings.reset_token_expire_minutes
        )
        reset_token = generate_secure_token()
        new_reset_token = ResetToken(
            token_hash=hash_reset_token(reset_token),
            user_id=user.id,  # type: ignore
            expires_at=expire,
        )
        await new_reset_token.create()

        background_task.add_task(
            send_forgot_password_email,
            to_email=user.email,
            username=user.username,
            reset_token=reset_token,
        )

    return {
        "message": "If an account with that email exists, a password reset link has been sent."
    }


@router.post("/reset-password", status_code=status.HTTP_200_OK)
async def reset_password(user_data: ResetPassword, background_task: BackgroundTasks):
    reset_token_hash = hash_reset_token(user_data.reset_token)
    existing_reset_token = await ResetToken.find_one(
        ResetToken.token_hash == reset_token_hash
    )
    if not existing_reset_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="invalid or expire reset token",
        )
    if not existing_reset_token.user_id:
        await existing_reset_token.delete()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="invalid or expire reset token",
        )
    token_exp = existing_reset_token.expires_at
    if token_exp.tzinfo is None:
        token_exp = token_exp.replace(tzinfo=UTC)
    if token_exp < datetime.now(UTC):
        await ResetToken.find(
            ResetToken.user_id == existing_reset_token.user_id
        ).delete()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="invalid or expire reset token",
        )
    user = await User.find_one(User.id == existing_reset_token.user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="invalid or expired reset token",
        )
    await user.update(
        {
            "$set": {
                "password_hash": hash_password(user_data.new_password),
                "updated_at": datetime.now(UTC),
            }
        }
    )
    await ResetToken.find_all(ResetToken.user_id == user.id).delete()
    background_task.add_task(
        send_password_reset_confirmation,
        to_email=user.email,
        username=user.username,
    )
    return {
        "message": "Your password has been successfully updated. Please log in with your new credentials."
    }


@router.get("/{provider}")
async def external_oauth(provider: Literal["google", "github"], request: Request):
    try:
        client = get_oauth_client(provider)
        return await client.authorize_redirect(request, REDIRECT_URLS[provider])
    except (ValueError, KeyError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"unsupported provider: {provider}",
        )


@router.get("/{provider}/callback")
async def oauth_callback(provider: Literal["google", "github"], request: Request):
    try:
        client = get_oauth_client(provider)
        token = await client.authorize_access_token(request)

        if provider == "github":
            resp = await client.get("user", token=token)
            profile = resp.json()
            if not profile.get("email"):
                email_resp = await client.get("user/emails", token=token)
                emails = email_resp.json()
                primary = next(
                    (e["email"] for e in emails if e["primary"] and e["verified"]), None
                )
                profile["email"] = primary
            token = profile
        user = await get_oauth_user(token, provider)
        expire_timedelta = timedelta(minutes=settings.access_token_expire_minutes)
        access_token = create_token({"sub": str(user.id)}, "access", expire_timedelta)
        refresh_token = create_token({"sub": str(user.id)}, "refresh")

        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="Bearer",
        )

    except HTTPException:
        raise
    except (ValueError, KeyError) as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"unsupported provider: {provider} - {exc}",
        )


@router.get(
    "/me",
    response_model=UserPrivateResponse,
    status_code=status.HTTP_200_OK,
    operation_id="get_current_user",
)
async def authenticated_user(current_user: currentUser):
    return current_user
