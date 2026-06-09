from beanie import PydanticObjectId
from fastapi import APIRouter, BackgroundTasks, status, HTTPException
from datetime import datetime, UTC, timedelta
from app.schemas.user import (
    UserCreate,
    UserResponse,
    UserPublicResponse,
    UserUpdate,
    ChangePassword,
    ApiKeyResponse,
    ApiKeyFullResponse,
    ApiKeyCreate,
    UserTag,
    VerifyUser,
)
from app.config import settings
from app.models import ApiKey, ResetToken, Tag, User, List, Workspace, Item
from app.auth import (
    hash_password,
    currentUser,
    verify_password,
    generate_secure_token,
    hash_api_key,
    decode_url_safe_token,
    create_url_safe_token,
)
from app.email_utils import (
    send_email_verification,
    send_email_verification_confirmation,
)

router = APIRouter()


@router.get("", response_model=list[UserPublicResponse])
async def fetch_users():
    return await User.find_all().sort("+created_at").to_list()


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(user_data: UserCreate):
    existing_user = await User.find_one(User.username == user_data.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="username already registered",
        )
    registered_email = await User.find_one(User.email == user_data.email)
    if registered_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="email already registered"
        )
    new_user = User(
        username=user_data.username,
        email=user_data.email,
        password_hash=hash_password(user_data.password),
    )
    await new_user.create()
    return new_user


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(current_user: currentUser):
    user = await User.get(current_user.id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="user not found"
        )
    await Item.find_all(Item.user_id == user.id).delete()
    await List.find_all(List.user_id == user.id).delete()
    await Workspace.find_all(Workspace.user_id == user.id).delete()
    await ApiKey.find_all(ApiKey.user_id == user.id).delete()
    await ResetToken.find_all(ResetToken.user_id == user.id).delete()
    await user.delete()


@router.patch("", response_model=UserResponse, status_code=status.HTTP_202_ACCEPTED)
async def update_user_partial(user_data: UserUpdate, current_user: currentUser):
    if user_data.username is not None:
        existing_user = await User.find_one(User.username == user_data.username)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="username already registered",
            )
    if user_data.email is not None:
        registered_email = await User.find_one(User.email == user_data.email)
        if registered_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="email already registered",
            )
    update_data = user_data.model_dump(exclude_none=True)
    update_data["updated_at"] = datetime.now(UTC)
    await current_user.update({"$set": update_data})  # type: ignore
    return await User.get(current_user.id)


@router.post("/send-verification", status_code=status.HTTP_200_OK)
async def send_verify_email(
    current_user: currentUser, background_task: BackgroundTasks
):
    if current_user.email is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="please set the email",
        )
    elif current_user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="user already verified"
        )
    verify_token = create_url_safe_token({"sub": current_user.email})
    background_task.add_task(
        send_email_verification,
        to_email=current_user.email,
        username=current_user.username,
        token=verify_token,
    )
    return {"message": "verification email sent"}


@router.post("/verify", status_code=status.HTTP_200_OK)
async def verify_user_email(user_data: VerifyUser, background_task: BackgroundTasks):
    token_data = decode_url_safe_token(user_data.verify_token)
    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="invalid or expired token"
        )
    if not token_data.get("sub"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="invalid or expired token"
        )
    user = await User.find_one(User.email == token_data.get("sub"))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="invalid or expire token"
        )
    if user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_200_OK, detail="email already verified"
        )
    await user.update({"$set": {"is_verified": True, "updated_at": datetime.now(UTC)}})
    background_task.add_task(
        send_email_verification_confirmation,
        to_email=user.email,
        username=user.username,
    )
    return {"message": "email verified sucessfully"}


@router.patch("/change-password", status_code=status.HTTP_200_OK)
async def change_password(passwordData: ChangePassword, current_user: currentUser):
    if not verify_password(passwordData.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="invalid password"
        )
    user = await User.get(current_user.id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="user not found"
        )
    await user.update(
        {
            "$set": {
                "password_hash": hash_password(passwordData.new_password),
                "updated_at": datetime.now(UTC),
            }
        }
    )
    return {"message": "password change sucessfull"}


@router.get(
    "/tags",
    response_model=list[UserTag],
    status_code=status.HTTP_200_OK,
    operation_id="list_tags",
)
async def fetch_user_tags(current_user: currentUser):
    return await Tag.find(Tag.user_id == current_user.id).to_list()


@router.get(
    "/api-keys", response_model=list[ApiKeyResponse], status_code=status.HTTP_200_OK
)
async def fetch_api_keys(current_user: currentUser):
    return await ApiKey.find_many(ApiKey.user_id == current_user.id).to_list()


@router.post(
    "/api-keys", response_model=ApiKeyFullResponse, status_code=status.HTTP_201_CREATED
)
async def create_api_key(input_data: ApiKeyCreate, current_user: currentUser):
    api_key_count = await ApiKey.find(ApiKey.user_id == current_user.id).count()
    if api_key_count > settings.max_api_key_count:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="api key limit reached"
        )
    existing_api_key = await ApiKey.find_one(
        ApiKey.name == input_data.name, ApiKey.user_id == current_user.id
    )
    if existing_api_key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="api key name already in use",
        )
    if input_data.expire_in is not None:
        expire = datetime.now(UTC) + timedelta(days=input_data.expire_in)
    else:
        expire = None

    api_key = generate_secure_token(type="api_key")
    new_api_key = ApiKey(
        user_id=current_user.id,
        name=input_data.name,
        key_hash=hash_api_key(api_key),
        prefix=api_key[:8],
        expires_at=expire,
    )
    await new_api_key.create()
    if not new_api_key.id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="failed to insert the api key",
        )

    return ApiKeyFullResponse(
        id=new_api_key.id,
        name=new_api_key.name,
        prefix=new_api_key.prefix,
        expires_at=new_api_key.expires_at,
        created_at=new_api_key.created_at,
        key=api_key,
    )


@router.delete("/api-keys/{api_key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_api_keys(api_key_id: PydanticObjectId, current_user: currentUser):
    api_key = await ApiKey.find_one(
        ApiKey.id == api_key_id, ApiKey.user_id == current_user.id
    )
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="api key not found"
        )
    await api_key.delete()
