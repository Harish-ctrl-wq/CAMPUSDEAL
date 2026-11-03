from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from models import Product
from services.analytics import anomaly_results

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/summary")
def summary(db: Session = Depends(get_db)):
    products = db.query(Product).all()
    anomalies = anomaly_results(products)
    prices = [product.price for product in products]
    categories_by_key = {product.category.casefold(): product.category for product in products}
    categories = sorted(categories_by_key.values(), key=str.casefold)
    return {
        "total_listings": len(products),
        "available_categories": len(categories),
        "categories": categories,
        "average_price": round(sum(prices) / len(prices), 2) if prices else 0,
        "unusual_price_listings": sum(1 for item in anomalies.values() if item["is_anomaly"]),
        "recent_products": [
            {
                "id": product.id,
                "title": product.title,
                "category": product.category,
                "price": product.price,
                "created_at": product.created_at,
            }
            for product in sorted(products, key=lambda item: (item.created_at, item.id), reverse=True)[:5]
        ],
    }


@router.get("/anomalies")
def anomalies(db: Session = Depends(get_db)):
    products = db.query(Product).all()
    results = anomaly_results(products)
    return [
        {"product_id": product.id, "title": product.title, "category": product.category, "price": product.price, **results[product.id]}
        for product in products
    ]
