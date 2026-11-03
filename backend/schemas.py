from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


Condition = Literal["Excellent", "Good", "Average", "Poor"]


class ProductInput(BaseModel):
    title: str = Field(min_length=1, max_length=160)
    category: str = Field(min_length=1, max_length=80)
    price: float = Field(gt=0)
    age: float | None = Field(default=None, ge=0)
    condition: Condition | None = None
    original_price: float | None = Field(default=None, ge=0)
    source_id: str | None = Field(default=None, max_length=80)

    @field_validator("title", "category")
    @classmethod
    def strip_required_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("This field cannot be blank.")
        return value

    @field_validator("source_id")
    @classmethod
    def strip_source_id(cls, value: str | None) -> str | None:
        return value.strip() or None if value is not None else None


class ProductCreate(ProductInput):
    pass


class ProductUpdate(ProductInput):
    pass


class ProductOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    category: str
    price: float
    age: float | None
    condition: str | None
    original_price: float | None
    created_at: datetime
    source_id: str | None


class RecommendationOut(BaseModel):
    product: ProductOut
    affordability_score: float
    age_score: float
    condition_score: float
    final_score: float
    explanation: str
