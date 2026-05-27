from fastapi import APIRouter, Depends, HTTPException, status, Request
from typing import Optional
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from models.schemas import LoginRequest, LoginResponse
from utils.logger import get_logger
from utils.config import settings
from models.auth_schemas import Token, TokenData, User, UserInDB
from services.auth_service import verify_password, get_user, create_access_token
from database.database import get_db

logger = get_logger(__name__)
router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        username: str = payload.get("sub")
        role: str = payload.get("role")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username, role=role)
    except JWTError:
        raise credentials_exception
        
    user_db = get_user(db, username=token_data.username)
    if user_db is None:
        raise credentials_exception
    return User.model_validate(user_db)


async def get_current_active_user(current_user: User = Depends(get_current_user)):
    if current_user.is_active is False:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user_db = get_user(db, form_data.username)
    if not user_db or not verify_password(form_data.password, user_db.hashed_password):
        logger.warning(f"Failed login attempt for user: {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(
        data={"sub": user_db.username, "role": user_db.role}
    )
    
    logger.info(f"Successful login for user: {user_db.username} (Role: {user_db.role})")
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/users/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    return current_user


# User Registration Endpoint
from pydantic import BaseModel

class RegisterRequest(BaseModel):
    username: str
    password: str
    role: Optional[str] = "Officer"

@router.post("/register")
async def register_user(payload: RegisterRequest, request: Request, db: Session = Depends(get_db)):
    from services.auth_service import get_password_hash
    from database import models
    
    # Restrict Admin registration
    requested_role = payload.role or "Officer"
    if requested_role == "Admin":
        user_count = db.query(models.User).count()
        if user_count > 0:
            auth_header = request.headers.get("Authorization")
            if not auth_header or not auth_header.startswith("Bearer "):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Authentication required to register Admin clearance."
                )
            token = auth_header.split(" ")[1]
            try:
                current_user = await get_current_user(token, db)
                if current_user.role != "Admin":
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Only existing Admin profiles can provision new Admin clearance."
                    )
            except Exception:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Invalid token. Provisioning rejected."
                )

    # Check if username/email already exists
    existing = db.query(models.User).filter(models.User.username == payload.username).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email is already registered"
        )
        
    # Create new user
    new_user = models.User(
        username=payload.username,
        role=requested_role,
        hashed_password=get_password_hash(payload.password),
        is_active=True
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    logger.info(f"New user registered: {new_user.username} (Role: {new_user.role})")
    return {"status": "success", "message": f"User {new_user.username} registered successfully"}


