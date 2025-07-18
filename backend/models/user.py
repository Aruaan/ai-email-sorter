from typing import Optional
from pydantic import BaseModel

class UserToken(BaseModel):
    email: str
    access_token: str
    refresh_token: Optional[str] = None