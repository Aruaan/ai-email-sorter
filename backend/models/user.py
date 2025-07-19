from typing import Optional, List
from pydantic import BaseModel

class UserToken(BaseModel):
    email: str
    access_token: str
    refresh_token: Optional[str] = None

class UserSession(BaseModel):
    session_id: str
    accounts: List[UserToken]
    primary_account: str  # email of primary account