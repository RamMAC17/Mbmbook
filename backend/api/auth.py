"""Authentication endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from backend.schemas import UserCreate, UserResponse, Token
from backend.core.security import (
    get_password_hash, verify_password, create_access_token, decode_access_token
)

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

# In-memory store for dev. Replaced by DB in production.
_users_store: dict[str, dict] = {}


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user: UserCreate):
    if user.username in _users_store:
        raise HTTPException(status_code=400, detail="Username already exists")

    import uuid
    from datetime import datetime, timezone

    user_id = uuid.uuid4()
    record = {
        "id": user_id,
        "username": user.username,
        "email": user.email,
        "full_name": user.full_name,
        "hashed_password": get_password_hash(user.password),
        "role": "user",
        "is_active": True,
        "created_at": datetime.now(timezone.utc),
    }
    _users_store[user.username] = record
    return UserResponse(**record)


@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = _users_store.get(form_data.username)
    if not user or not verify_password(form_data.password, user["hashed_password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token(data={"sub": user["username"], "uid": str(user["id"])})
    return Token(access_token=token)


async def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(status_code=401, detail="Invalid token")
    username = payload.get("sub")
    user = _users_store.get(username)
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return user
