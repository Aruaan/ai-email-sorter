from fastapi import APIRouter, Body, Query, status, Response
from typing import List
from models.category import Category
from services.fake_db import add_category, get_categories_by_user

router = APIRouter()

_category_id_counter = 1

def get_next_id():
    global _category_id_counter
    _category_id_counter += 1
    return _category_id_counter - 1

@router.post("/", response_model=Category)
def create_category(
    name: str = Body(...),
    description: str = Body(None),
    user_email: str = Body(...)
):
    category = Category(
        id=get_next_id(),
        name=name,
        description=description,
        user_email=user_email
    )
    add_category(category)
    return category

@router.get("/", response_model=List[Category])
def list_categories(user_email: str = Query(...)):
    return get_categories_by_user(user_email) 