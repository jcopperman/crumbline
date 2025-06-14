from fastapi import Request, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
import os
from typing import Optional
from .models import User
from .database import get_session
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Security configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 60 * 24 * 7))  # Default: 1 week

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def authenticate_user(session: AsyncSession, username: str, password: str):
    result = await session.execute(select(User).filter(User.username == username))
    user = result.scalars().first()
    if not user:
        return False
    if not verify_password(password, user.password):
        return False
    return user

async def get_current_user_from_cookie(request: Request, session: AsyncSession = Depends(get_session)):
    """Get the current user from the session cookie"""
    token = request.cookies.get("session")
    if not token:
        return None
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            return None
    except JWTError:
        return None
    
    result = await session.execute(select(User).filter(User.username == username))
    user = result.scalars().first()
    if user is None:
        return None
    
    return user

def login_required(func):
    """Decorator to protect routes by requiring login"""
    async def wrapper(request: Request, *args, **kwargs):
        user = await get_current_user_from_cookie(request)
        if user is None:
            return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
        return await func(request=request, current_user=user, *args, **kwargs)
    return wrapper
