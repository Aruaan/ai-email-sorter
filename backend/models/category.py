from pydantic import BaseModel
from typing import Optional

class Category(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    user_email: str 