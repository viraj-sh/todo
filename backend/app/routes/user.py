from fastapi import APIRouter, status, HTTPException
from app.schemas.user import (
    UserCreate,
    UserResponse,
    UserPublicResponse,
    UserUpdate,
    ChangePassword,
)
from app.models import User, List
from app.auth import hash_password, currentUser, verify_password
from datetime import datetime, UTC

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
    await user.delete()


@router.patch("", response_model=UserResponse, status_code=status.HTTP_202_ACCEPTED)
async def update_user_partial(user_data: UserUpdate, current_user: currentUser):
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
    user = await User.get(current_user.id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="user not found"
        )
    if user_data.username != None:
        await user.update({"$set": {"username": user_data.username}})
    if user_data.email != None:
        await user.update({"$set": {"email": user_data.email}})
    await user.update({"$set": {"updated_at": datetime.now(UTC)}})
    return await user.get(user.id)


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
        {"$set": {"password_hash": hash_password(passwordData.new_password)}}
    )
    await user.update({"$set": {"updated_at": datetime.now(UTC)}})
    return {"message": "password change sucessfull"}


@router.get("/tags", status_code=status.HTTP_200_OK)
async def fetch_user_tags(current_user: currentUser):
    return await List.get_all_user_tags(current_user.id)
