from fastapi import APIRouter, Body, Query, status, Response
from typing import List
from backend.models.category import Category
from backend.services.session_db import add_category, get_categories_by_session
import uuid

router = APIRouter()

@router.post("/", response_model=Category)
def create_category(
    name: str = Body(...),
    description: str = Body(None),
    session_id: str = Body(...)
):
    category = Category(
        id=uuid.uuid4(),  # Generate UUID for new category
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

@router.put("/{category_id}")
def update_category(category_id: str, name: str = Body(None), description: str = Body(None)):
    """Update a category's name and/or description"""
    from backend.database.db import SessionLocal
    from backend.database.models import Category as DBCategory
    from backend.database.models import Email as DBEmail
    
    db = SessionLocal()
    try:
        category = db.query(DBCategory).filter(DBCategory.id == category_id).first()
        if not category:
            return {"error": "Category not found"}
        
        # If trying to change the name, check if category has emails
        if name is not None and name != category.name:
            email_count = db.query(DBEmail).filter(DBEmail.category_id == category_id).count()
            if email_count > 0:
                return {
                    "error": f"Cannot rename category '{category.name}' because it contains {email_count} email(s). Please delete all emails in this category before renaming it."
                }
            category.name = name
            
        if description is not None:
            category.description = description
        
        db.commit()
        
        return {
            "message": "Category updated successfully",
            "category": {
                "id": str(category.id),
                "name": category.name,
                "description": category.description,
                "session_id": category.session_id
            }
        }
    except Exception as e:
        db.rollback()
        return {"error": f"Failed to update category: {str(e)}"}
    finally:
        db.close()
