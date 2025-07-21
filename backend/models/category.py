from pydantic import BaseModel
from typing import Optional
import uuid

class Category(BaseModel):
    id: uuid.UUID
    name: str
    description: Optional[str] = None
    session_id: str 