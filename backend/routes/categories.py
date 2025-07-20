from fastapi import APIRouter, Body, Query, status, Response
from typing import List
from models.category import Category
from services.fake_db import add_category, get_categories_by_session

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
    session_id: str = Body(...)
):
    category = Category(
        id=get_next_id(),
        name=name,
        description=description,
        session_id=session_id
    )
    db_cat = add_category(category)
    # Return as Pydantic model
    return Category(
        id=db_cat.id,
        name=db_cat.name,
        description=db_cat.description,
        session_id=db_cat.session_id
    )

@router.get("/", response_model=List[Category])
def list_categories(session_id: str = Query(...)):
    db_cats = get_categories_by_session(session_id)
    return [Category(
        id=cat.id,
        name=cat.name,
        description=cat.description,
        session_id=cat.session_id
    ) for cat in db_cats]
