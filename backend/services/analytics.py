from collections import defaultdict
from statistics import median

from models import Product


def price_analysis(product: Product) -> dict:
    original = product.original_price
    ratio = round(product.price / original * 100, 1) if original and original > 0 else None
    return {
        "original_price": original,
        "current_price": product.price,
        "price_ratio": ratio,
        "discount_percentage": round(100 - ratio, 1) if ratio is not None else None,
    }


def anomaly_results(products: list[Product]) -> dict[int, dict]:
    categories: dict[str, list[float]] = defaultdict(list)
    for product in products:
        categories[product.category.casefold()].append(product.price)

    results = {}
    for product in products:
        prices = categories[product.category.casefold()]
        if len(prices) < 3:
            results[product.id] = {
                "is_anomaly": False,
                "status": "insufficient_data",
                "median_price": None,
                "deviation_percentage": None,
                "explanation": "Insufficient comparison data: at least 3 listings in this category are required.",
            }
            continue
        category_median = median(prices)
        deviation = abs(product.price - category_median) / category_median if category_median else 0
        flagged = deviation > 0.20
        results[product.id] = {
            "is_anomaly": flagged,
            "status": "unusual" if flagged else "typical",
            "median_price": round(category_median, 2),
            "deviation_percentage": round(deviation * 100, 1),
            "explanation": (
                f"Price is {deviation * 100:.1f}% from this category's median of ₹{category_median:,.0f}. "
                "An unusual price is not proof of fraud."
                if flagged
                else f"Price is within 20% of this category's median of ₹{category_median:,.0f}."
            ),
        }
    return results
