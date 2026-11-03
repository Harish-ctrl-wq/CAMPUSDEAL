# CAMPUSDEAL — Smart Student Marketplace

**Buy Smarter. Spend Wiser.**

CampusDeal is a lightweight marketplace for students to list and compare second-hand campus essentials. The app combines a React dashboard with a FastAPI REST API and SQLite storage. It includes a rule-based recommendation engine that explains how eligible products score against a buyer's budget and priority.

Recommendation scores are based on the documented scoring assumptions below. They are **not predictions of market value**, product quality beyond the supplied condition, or fraud.

## Problem statement

Students often need affordable books, laptops, bicycles, and gadgets but have limited ways to compare second-hand listings. They need transparent listing details and recommendations that respect a budget without presenting an opaque score as an objective market valuation.

## Objectives

- Provide a simple student marketplace for creating and maintaining listings.
- Make listings searchable and filterable by category, budget, condition, and price.
- Compare eligible products within one category using an explainable, configurable scoring formula.
- Highlight statistically unusual category prices while clearly communicating uncertainty.
- Support organizer-provided CSV and JSON data with validation and duplicate reporting.

## Features

- Dashboard summary: listing count, category count, average asking price, unusual-price count, and recent listings.
- Marketplace with search, category/maximum-budget/condition filters, and price sorting.
- Listing create, edit, and delete with input validation and user-visible feedback.
- CSV/JSON import with per-record validation, duplicate detection, and an import report.
- Dynamic recommendations for affordability or condition priority, limited to the top three in-budget products in the selected category.
- Price-to-original-price ratio and provided-price discount percentage; unavailable when original price is absent or zero.
- Category-wise median anomaly analysis; unusual price is not proof of fraud.
- Responsive layouts with mobile navigation.

## Technology and architecture

| Layer | Technologies |
|---|---|
| Frontend | React 18, Vite, Tailwind CSS, React Router, Lucide React, Fetch API |
| Backend | Python 3.10+, FastAPI, Pydantic, SQLAlchemy 2, Pandas |
| Database | SQLite |
| API | JSON REST endpoints; multipart file upload for imports |

```text
backend/
  main.py                 FastAPI app, schema initialization, initial seed
  database.py             SQLAlchemy engine and session dependency
  models.py               Product ORM model
  schemas.py              Request validation and response models
  routes/                 Product, analytics, and recommendation APIs
  services/               Recommendation and anomaly calculations
  data/                   Supplied seed dataset as JSON
  tests/                  API integration tests
  requirements.txt        Python dependencies
frontend/
  src/components/         Shared layout, feedback, and product-card UI
  src/pages/              Dashboard, marketplace, listing form, recommendations
  src/services/api.js     Fetch API client
  src/App.jsx             React Router routes
```

## Database and sample data

The `products` table contains:

| Field | Type | Notes |
|---|---|---|
| `id` | Integer | Primary key |
| `title` | String | Required |
| `category` | String | Required |
| `price` | Float | Selling price; must be greater than zero |
| `age` | Float, nullable | Item age in years; if supplied, must be non-negative |
| `condition` | String, nullable | Excellent, Good, Average, or Poor |
| `original_price` | Float, nullable | Zero/absent means price ratio is unavailable |
| `created_at` | DateTime | Listing timestamp |
| `source_id` | String, nullable | Optional unique import ID used for duplicate detection |

On startup, the backend creates `backend/campusdeal.db` if it does not exist and seeds it with the five supplied Laptop records only when the products table is empty. The source data is [`backend/data/sample_products.json`](backend/data/sample_products.json). A curated SQLite snapshot containing only P01–P05 is also provided as [`backend/campusdeal-demo.sqlite3`](backend/campusdeal-demo.sqlite3); it is for inspection/demo use, while the app uses `campusdeal.db` by default.

The sample data is:

| ID | Item | Category | Price | Age | Condition | Original price |
|---|---|---|---:|---:|---|---:|
| P01 | Laptop A | Laptop | ₹22,000 | 2 | Good | ₹45,000 |
| P02 | Laptop B | Laptop | ₹18,000 | 3 | Average | ₹42,000 |
| P03 | Laptop C | Laptop | ₹25,000 | 1 | Excellent | ₹48,000 |
| P04 | Laptop D | Laptop | ₹20,000 | 2 | Good | ₹40,000 |
| P05 | Laptop E | Laptop | ₹15,000 | 4 | Average | ₹38,000 |

Local active databases, SQLite backups, and SQLite journal/sidecar files are excluded from Git. The curated demo snapshot is the only SQLite file allowed by `.gitignore`; no backup database is intended for publication.

## Recommendation engine

`GET /recommendations?budget=23000&category=Laptop&priority=affordability` returns at most three products. Candidates must be within the requested category and budget and have one of the recognized condition values. Missing condition is never assumed to be Good.

Normalized factor scores are clamped to `[0, 1]`:

- **Affordability:** `1 − (product price / buyer budget)`
- **Age:** `1 − (product age / maximum known age in that category)`
- **Condition:** Excellent `1.00`, Good `0.75`, Average `0.50`, Poor `0.25`

Priority weights:

- **Affordability:** `100 × (0.65 × affordability + 0.15 × age + 0.20 × condition)`
- **Condition:** `100 × (0.15 × affordability + 0.15 × age + 0.70 × condition)`

When age is missing or there is no usable category age range, the age score is a neutral `0.50`; no age is inferred. Products are compared only within the selected category. Scores are computed from current database records at request time. Ranking uses unrounded scores; exact ties are broken by lower price and then lower product ID. Anomaly flags do not automatically exclude recommendations.

These are relative scores under the chosen formula. They do not use external marketplace data and do not estimate actual market value.

## Price analysis and anomaly detection

Price ratio is `(selling price / original price) × 100`; discount percentage is `100 − price ratio`. If the original price is missing or zero, both results are unavailable. These calculations compare only values supplied in the listing; they do not represent actual market value.

Anomaly detection runs independently per category. It calculates that category's median price and flags a listing when:

```text
abs(listing price − category median) / category median > 0.20
```

At least three comparable listings in the category are required; otherwise the result is reported as **Insufficient comparison data**, without an anomaly claim. An unusual price is not proof of fraud.

## Importing listings

The marketplace import control and `POST /products/import` accept `.csv` and `.json` files. Required fields are `title`, `category`, and `price`. Optional fields are `source_id`, `age`, `condition`, and `original_price`; blank optional values are treated as missing. CSV/JSON imports validate records individually, skip duplicate source IDs or matching title/category/price records, and return imported, duplicate, and invalid record details.

## API overview

Interactive OpenAPI documentation is available at `/docs` when the backend is running.

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/products` | List products; supports `q`, `category`, `max_budget`, `condition`, and `sort` |
| `GET` | `/products/search?q=...` | Search product titles and categories |
| `POST` | `/products` | Create a product (`201`) |
| `PUT` | `/products/{id}` | Update a product |
| `DELETE` | `/products/{id}` | Delete a product (`204`) |
| `POST` | `/products/import` | Import CSV/JSON multipart upload |
| `GET` | `/recommendations` | Score products using `budget`, `category`, and `priority` |
| `GET` | `/analytics/summary` | Listing/category/average-price/anomaly summary |
| `GET` | `/analytics/anomalies` | Per-product category median comparison |

Invalid request values return `422`, missing products return `404`, conflicting source IDs return `409`, and malformed or unsupported import files return `400`.

## Installation and development

Run the backend and frontend in separate terminals from the project root.

### Backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m uvicorn main:app --reload
```

Backend API: `http://localhost:8000`
API documentation: `http://localhost:8000/docs`

### Frontend

```powershell
cd frontend
npm ci
npm run dev
```

Frontend: `http://localhost:5173`. Set `VITE_API_URL` if the API runs on a different origin. The local Vite origins are allowed by the backend CORS configuration.

### Tests and production build

```powershell
cd backend
python -m unittest discover -s tests -v
python -m compileall -q .
```

```powershell
cd frontend
npm run build
npm audit
```

## Known limitations

- The application has no authentication, moderation, messaging, or payment processing.
- Listings do not include images or verified specifications.
- Recommendations and anomaly detection are based solely on stored user/imported data and the formulas above; there is no external market-price feed.
- The starter dataset contains five laptop listings. Other categories are available when listings are added or imported.
