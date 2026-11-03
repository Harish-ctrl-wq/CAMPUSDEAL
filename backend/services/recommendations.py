from models import Product

CONDITION_SCORE = {"Excellent": 1.0, "Good": 0.75, "Average": 0.5, "Poor": 0.25}


def recommend(products: list[Product], budget: float, category: str, priority: str) -> list[dict]:
    candidates = [p for p in products if p.category.casefold() == category.casefold()]
    known_ages = [p.age for p in candidates if p.age is not None]
    max_age = max(known_ages) if known_ages else None
    weights = (0.65, 0.15, 0.20) if priority == "affordability" else (0.15, 0.15, 0.70)

    scored = []
    for product in candidates:
        if product.price > budget or product.condition not in CONDITION_SCORE:
            continue
        affordability = min(1.0, max(0.0, 1 - product.price / budget))
        # Missing age uses a documented neutral score; it is never inferred from other products.
        age_score = (
            0.5
            if product.age is None or max_age is None or max_age == 0
            else min(1.0, max(0.0, 1 - product.age / max_age))
        )
        condition_score = CONDITION_SCORE[product.condition]
        final_score = 100 * (
            weights[0] * affordability + weights[1] * age_score + weights[2] * condition_score
        )
        scored.append(
            {
                "product": product,
                "affordability_score": round(affordability, 4),
                "age_score": round(age_score, 4),
                "condition_score": round(condition_score, 4),
                "final_score": round(final_score, 2),
                "_unrounded_score": final_score,
                "explanation": (
                    f"Within your ₹{budget:,.0f} budget; {product.condition.lower()} condition; "
                    + (
                        f"{product.age:g} years old."
                        if product.age is not None
                        else "age not provided, so a neutral age score (0.50) was used."
                    )
                ),
            }
        )
    ranked = sorted(
        scored,
        key=lambda row: (-row["_unrounded_score"], row["product"].price, row["product"].id),
    )[:3]
    for row in ranked:
        del row["_unrounded_score"]
    return ranked
