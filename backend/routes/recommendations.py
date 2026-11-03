from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from database import get_db
from models import Product
from services.recommendations import recommend

router = APIRouter(tags=["recommendations"])


@router.get("/recommendations")
def get_recommendations(
    budget: float = Query(gt=0),
    category: str = Query(min_length=1),
    priority: str = Query(pattern="^(affordability|condition)$"),
    db: Session = Depends(get_db),
):
    if not category.strip():
        raise HTTPException(status_code=422, detail="Category cannot be blank.")
    return recommend(db.query(Product).all(), budget, category.strip(), priority)
