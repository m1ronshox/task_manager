from fastapi import APIRouter, Depends, HTTPException
from auth import get_current_user
from models import User
from schema import UserCreate, UserResponse

router = APIRouter(
    prefix="/api/users",
    tags=["Users"]
)


@router.post("/", response_model=UserResponse)
def create_user(
    data: UserCreate,
    user: User = Depends(get_current_user)
):
    if data.telegram_id != user.telegram_id:
        raise HTTPException(403, "User identity does not match")

    return user


@router.get("/", response_model=list[UserResponse])
def get_users(user: User = Depends(get_current_user)):
    return [user]
