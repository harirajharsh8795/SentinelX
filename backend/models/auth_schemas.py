from typing import List, Optional
from pydantic import BaseModel, ConfigDict

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None
    role: Optional[str] = None

class User(BaseModel):
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    role: str  # Admin, Auditor, Officer
    is_active: Optional[bool] = None

    model_config = ConfigDict(from_attributes=True)

class UserInDB(User):
    hashed_password: str
