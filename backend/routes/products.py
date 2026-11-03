import io
import json

import pandas as pd
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from pydantic import ValidationError
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from database import get_db
from models import Product
from schemas import ProductCreate, ProductOut, ProductUpdate
from services.analytics import anomaly_results, price_analysis

router = APIRouter(prefix="/products", tags=["products"])


def as_dict(product: Product, anomalies: dict) -> dict:
    return {
        **ProductOut.model_validate(product).model_dump(mode="json"),
        **price_analysis(product),
        "anomaly": anomalies.get(product.id),
    }


@router.get("", response_model=list[dict])
def list_products(
    q: str | None = None,
    category: str | None = None,
    max_budget: float | None = Query(default=None, gt=0),
    condition: str | None = None,
    sort: str | None = Query(default=None, pattern="^(price_asc|price_desc)$"),
    db: Session = Depends(get_db),
):
    query = db.query(Product)
    if q and q.strip():
        term = f"%{q.strip()}%"
        query = query.filter(or_(Product.title.ilike(term), Product.category.ilike(term)))
    if category:
        query = query.filter(func.lower(Product.category) == category.strip().lower())
    if max_budget is not None:
        query = query.filter(Product.price <= max_budget)
    if condition:
        query = query.filter(func.lower(Product.condition) == condition.strip().lower())
    if sort == "price_asc":
        query = query.order_by(Product.price.asc(), Product.id.asc())
    elif sort == "price_desc":
        query = query.order_by(Product.price.desc(), Product.id.asc())
    else:
        query = query.order_by(Product.created_at.desc(), Product.id.desc())
    products = query.all()
    anomalies = anomaly_results(db.query(Product).all())
    return [as_dict(product, anomalies) for product in products]


@router.get("/search", response_model=list[dict])
def search_products(q: str = Query(min_length=1), db: Session = Depends(get_db)):
    return list_products(q=q, category=None, max_budget=None, condition=None, sort=None, db=db)


@router.post("", response_model=ProductOut, status_code=status.HTTP_201_CREATED)
def create_product(payload: ProductCreate, db: Session = Depends(get_db)):
    if payload.source_id and db.query(Product).filter_by(source_id=payload.source_id).first():
        raise HTTPException(status_code=409, detail="A listing with this source_id already exists.")
    product = Product(**payload.model_dump())
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


@router.put("/{product_id}", response_model=ProductOut)
def update_product(product_id: int, payload: ProductUpdate, db: Session = Depends(get_db)):
    product = db.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Listing not found.")
    if payload.source_id and db.query(Product).filter(
        Product.source_id == payload.source_id, Product.id != product_id
    ).first():
        raise HTTPException(status_code=409, detail="A listing with this source_id already exists.")
    updates = payload.model_dump()
    if payload.source_id is None:
        updates.pop("source_id")
    for key, value in updates.items():
        setattr(product, key, value)
    db.commit()
    db.refresh(product)
    return product


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(product_id: int, db: Session = Depends(get_db)):
    product = db.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Listing not found.")
    db.delete(product)
    db.commit()


@router.post("/import")
async def import_products(file: UploadFile = File(...), db: Session = Depends(get_db)):
    filename = (file.filename or "").lower()
    content = await file.read()
    records = []
    try:
        if filename.endswith(".csv"):
            records = pd.read_csv(io.BytesIO(content), dtype=str, keep_default_na=False).to_dict(orient="records")
        elif filename.endswith(".json"):
            parsed = json.loads(content.decode("utf-8-sig"))
            if isinstance(parsed, list):
                records = parsed
            elif isinstance(parsed, dict):
                records = parsed.get("products", [parsed])
            else:
                raise ValueError("JSON must contain an object or a list of product records.")
            if not isinstance(records, list):
                raise ValueError("JSON must contain a list of product records.")
        else:
            raise HTTPException(status_code=400, detail="Upload a .csv or .json file.")
    except (UnicodeDecodeError, json.JSONDecodeError, pd.errors.ParserError, pd.errors.EmptyDataError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=f"Could not parse import file: {exc}") from exc

    imported, duplicates, invalid = [], [], []
    aliases = {"item": "title", "name": "title", "selling_price": "price", "product_id": "source_id", "id": "source_id"}
    for index, record in enumerate(records, start=1):
        if not isinstance(record, dict):
            invalid.append({"record": index, "errors": ["Record must be an object."]})
            continue
        normalized = {aliases.get(str(key).strip().lower(), str(key).strip().lower()): value for key, value in record.items()}
        normalized = {key: value for key, value in normalized.items() if value is not None and str(value).strip() != ""}
        try:
            item = ProductCreate.model_validate(normalized)
        except ValidationError as exc:
            invalid.append({"record": index, "errors": [error["msg"] for error in exc.errors()]})
            continue
        data = item.model_dump()
        duplicate = (
            db.query(Product).filter_by(source_id=item.source_id).first()
            if item.source_id
            else None
        )
        if not duplicate:
            duplicate = db.query(Product).filter(
                func.lower(Product.title) == item.title.lower(),
                func.lower(Product.category) == item.category.lower(),
                Product.price == item.price,
            ).first()
        if duplicate:
            duplicates.append({"record": index, "existing_id": duplicate.id})
            continue
        product = Product(**data)
        db.add(product)
        db.flush()
        imported.append({"record": index, "id": product.id})
    db.commit()
    return {"imported_count": len(imported), "duplicate_count": len(duplicates), "invalid_count": len(invalid),
            "imported": imported, "duplicates": duplicates, "invalid_records": invalid}
