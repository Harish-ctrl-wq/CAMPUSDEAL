import os
import json
import tempfile
import unittest
from pathlib import Path

TEST_DATABASE = Path(tempfile.gettempdir()) / "campusdeal-api-tests.sqlite"
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DATABASE.as_posix()}"

from fastapi.testclient import TestClient

from database import engine
from main import app


class CampusDealApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        TEST_DATABASE.unlink(missing_ok=True)
        cls.client = TestClient(app)
        cls.client.__enter__()

    @classmethod
    def tearDownClass(cls):
        cls.client.__exit__(None, None, None)
        engine.dispose()
        TEST_DATABASE.unlink(missing_ok=True)

    def test_seed_and_analytics(self):
        products = self.client.get("/products").json()
        self.assertGreaterEqual(len(products), 5)
        laptops = {item["title"]: item for item in products if item["category"] == "Laptop"}
        self.assertEqual(len(laptops), 5)
        summary = self.client.get("/analytics/summary").json()
        self.assertEqual(summary["total_listings"], len(products))
        self.assertGreaterEqual(summary["available_categories"], 1)
        self.assertTrue(laptops["Laptop C"]["anomaly"]["is_anomaly"])
        self.assertTrue(laptops["Laptop E"]["anomaly"]["is_anomaly"])
        self.assertTrue(all(item["price_ratio"] is not None for item in laptops.values()))

    def test_search_filters_and_sorting(self):
        response = self.client.get("/products/search", params={"q": "Laptop A"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual([item["title"] for item in response.json()], ["Laptop A"])
        filtered = self.client.get(
            "/products",
            params={"category": "Laptop", "max_budget": 20000, "sort": "price_asc"},
        ).json()
        self.assertEqual([item["price"] for item in filtered], [15000, 18000, 20000])

    def test_recommendations_are_dynamic_category_bounded_and_ranked(self):
        response = self.client.get(
            "/recommendations",
            params={"budget": 23000, "category": "Laptop", "priority": "affordability"},
        )
        self.assertEqual(response.status_code, 200)
        results = response.json()
        self.assertEqual(len(results), 3)
        self.assertEqual([item["product"]["title"] for item in results], ["Laptop E", "Laptop D", "Laptop B"])
        self.assertAlmostEqual(results[0]["final_score"], 32.61, places=2)
        self.assertTrue(all(item["product"]["price"] <= 23000 for item in results))
        self.assertEqual(
            self.client.get(
                "/recommendations",
                params={"budget": 23000, "category": "No such category", "priority": "affordability"},
            ).json(),
            [],
        )
        condition_results = self.client.get(
            "/recommendations",
            params={"budget": 23000, "category": "Laptop", "priority": "condition"},
        ).json()
        self.assertEqual(len(condition_results), 3)
        self.assertEqual(condition_results[0]["product"]["title"], "Laptop D")
        self.assertAlmostEqual(condition_results[0]["final_score"], 61.96, places=2)

    def test_crud_and_validation(self):
        invalid = self.client.post(
            "/products", json={"title": "Bad listing", "category": "Books", "price": 0}
        )
        self.assertEqual(invalid.status_code, 422)
        created = self.client.post(
            "/products",
            json={
                "title": "Test listing",
                "category": "Books",
                "price": 500,
                "age": 1,
                "condition": "Good",
                "original_price": 1000,
                "source_id": "PUT-SOURCE",
            },
        )
        self.assertEqual(created.status_code, 201)
        product_id = created.json()["id"]
        updated = self.client.put(
            f"/products/{product_id}",
            json={"title": "Updated listing", "category": "Books", "price": 450},
        )
        self.assertEqual(updated.status_code, 200)
        self.assertEqual(updated.json()["title"], "Updated listing")
        self.assertEqual(updated.json()["source_id"], "PUT-SOURCE")
        duplicate_source = self.client.post(
            "/products/import",
            files={
                "file": (
                    "duplicate-source.json",
                    b'[{"source_id":"PUT-SOURCE","title":"Updated listing","category":"Books","price":450}]',
                    "application/json",
                )
            },
        )
        self.assertEqual(duplicate_source.json()["duplicate_count"], 1)
        self.assertEqual(self.client.delete(f"/products/{product_id}").status_code, 204)
        self.assertEqual(self.client.delete(f"/products/{product_id}").status_code, 404)

    def test_missing_recommendation_data_and_category_anomaly_threshold(self):
        create = lambda title, price, condition: self.client.post(
            "/products",
            json={"title": title, "category": "TestOnly", "price": price, "condition": condition},
        )
        first = create("Unknown condition", 100, None)
        self.assertEqual(first.status_code, 201)
        self.assertEqual(
            self.client.get(
                "/recommendations",
                params={"budget": 200, "category": "TestOnly", "priority": "affordability"},
            ).json(),
            [],
        )
        second = create("Known condition A", 100, "Good")
        third = create("Known condition B", 120, "Good")
        fourth = self.client.post(
            "/products",
            json={"title": "Case variant", "category": "testonly", "price": 100, "condition": "Good"},
        )
        self.assertEqual(fourth.status_code, 201)
        results = self.client.get(
            "/recommendations",
            params={"budget": 200, "category": "TestOnly", "priority": "affordability"},
        ).json()
        self.assertEqual(len(results), 3)
        self.assertTrue(all(result["age_score"] == 0.5 for result in results))
        anomaly_rows = self.client.get("/analytics/anomalies").json()
        by_title = {row["title"]: row for row in anomaly_rows}
        self.assertEqual(by_title["Unknown condition"]["status"], "typical")
        self.assertFalse(by_title["Known condition B"]["is_anomaly"])
        self.assertEqual(by_title["Case variant"]["status"], "typical")
        self.assertNotEqual(second.json()["id"], third.json()["id"])

    def test_csv_import_reports_invalid_and_duplicate_rows(self):
        csv_content = (
            b"id,title,category,price,age,condition,original_price\n"
            b"IMP-1,Imported Book,Books,300,1,Average,600\n"
            b",Invalid Book,Books,0,,Good,\n"
        )
        first = self.client.post(
            "/products/import",
            files={"file": ("listings.csv", csv_content, "text/csv")},
        )
        self.assertEqual(first.status_code, 200)
        self.assertEqual(first.json()["imported_count"], 1)
        self.assertEqual(first.json()["invalid_count"], 1)
        second = self.client.post(
            "/products/import",
            files={"file": ("listings.csv", csv_content, "text/csv")},
        )
        self.assertEqual(second.json()["duplicate_count"], 1)

    def test_json_import(self):
        response = self.client.post(
            "/products/import",
            files={
                "file": (
                    "listings.json",
                    b'{"products":[{"title":"JSON book","category":"Books","price":99}]}',
                    "application/json",
                )
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["imported_count"], 1)

    def test_budget_boundaries_and_negative_input_rejections(self):
        counts = {}
        for budget in (23000, 15000, 10000):
            response = self.client.get(
                "/recommendations",
                params={"budget": budget, "category": "Laptop", "priority": "affordability"},
            )
            self.assertEqual(response.status_code, 200)
            # The endpoint intentionally returns only the top three; verify eligibility
            # count separately through the complete filtered listing collection.
            eligible = self.client.get(
                "/products", params={"category": "Laptop", "max_budget": budget}
            ).json()
            counts[budget] = len(eligible)
            self.assertLessEqual(len(response.json()), 3)
            self.assertTrue(all(row["product"]["price"] <= budget for row in response.json()))
        self.assertEqual(counts, {23000: 4, 15000: 1, 10000: 0})

        for payload in (
            {"title": "Negative price", "category": "Validation QA", "price": -1},
            {"title": "Negative age", "category": "Validation QA", "price": 100, "age": -0.1},
            {"title": "Negative original", "category": "Validation QA", "price": 100, "original_price": -1},
        ):
            self.assertEqual(self.client.post("/products", json=payload).status_code, 422)

        zero_original = self.client.post(
            "/products",
            json={"title": "Zero original", "category": "Validation QA", "price": 100, "original_price": 0},
        )
        self.assertEqual(zero_original.status_code, 201)
        zero_analysis = self.client.get(
            "/products", params={"q": "Zero original"}
        ).json()[0]
        self.assertIsNone(zero_analysis["price_ratio"])
        self.assertIsNone(zero_analysis["discount_percentage"])

    def test_generated_25_product_multi_category_json_import_and_medians(self):
        categories = ("QA Laptop", "QA Books", "QA Bicycles", "QA Gadgets", "QA Furniture")
        generated = []
        for category_index, category in enumerate(categories):
            for item_index, price in enumerate((100, 100, 100, 100, 200)):
                record = {
                    "source_id": f"QA-{category_index}-{item_index}",
                    "title": f"{category} item {item_index}",
                    "category": category,
                    "price": price,
                    "condition": "Good",
                    "age": None if category_index == 0 and item_index == 0 else item_index,
                    "original_price": None if category_index == 1 and item_index == 0 else 400,
                }
                generated.append(record)

        response = self.client.post(
            "/products/import",
            files={
                "file": (
                    "generated-25.json",
                    json.dumps({"products": generated}).encode(),
                    "application/json",
                )
            },
        )
        self.assertEqual(response.status_code, 200, response.text)
        report = response.json()
        self.assertEqual((report["imported_count"], report["duplicate_count"], report["invalid_count"]), (25, 0, 0))

        second_import = self.client.post(
            "/products/import",
            files={
                "file": (
                    "generated-25.json",
                    json.dumps({"products": generated}).encode(),
                    "application/json",
                )
            },
        )
        self.assertEqual(second_import.json()["duplicate_count"], 25)

        anomaly_rows = self.client.get("/analytics/anomalies").json()
        generated_anomalies = {row["title"]: row for row in anomaly_rows if row["category"] in categories}
        self.assertEqual(len(generated_anomalies), 25)
        for category in categories:
            category_rows = [row for row in generated_anomalies.values() if row["category"] == category]
            self.assertEqual({row["median_price"] for row in category_rows}, {100})
            self.assertEqual(sum(row["is_anomaly"] for row in category_rows), 1)
            self.assertTrue(next(row for row in category_rows if row["price"] == 200)["explanation"].find("median of ₹100") >= 0)

        without_original = self.client.get(
            "/products", params={"q": "QA Books item 0"}
        ).json()[0]
        self.assertIsNone(without_original["price_ratio"])
        self.assertIsNone(without_original["discount_percentage"])
        missing_age = self.client.get(
            "/recommendations",
            params={"budget": 250, "category": "QA Laptop", "priority": "affordability"},
        ).json()
        missing_age_pick = next(row for row in missing_age if row["product"]["title"] == "QA Laptop item 0")
        self.assertEqual(missing_age_pick["age_score"], 0.5)
        self.assertIn("age not provided", missing_age_pick["explanation"])

        sparse_a = self.client.post(
            "/products",
            json={"title": "Sparse A", "category": "QA Sparse", "price": 100},
        ).json()
        sparse_b = self.client.post(
            "/products",
            json={"title": "Sparse B", "category": "QA Sparse", "price": 500},
        ).json()
        sparse_rows = {
            row["product_id"]: row
            for row in self.client.get("/analytics/anomalies").json()
            if row["product_id"] in {sparse_a["id"], sparse_b["id"]}
        }
        self.assertEqual(len(sparse_rows), 2)
        self.assertTrue(all(row["status"] == "insufficient_data" for row in sparse_rows.values()))
        self.assertTrue(all(row["median_price"] is None for row in sparse_rows.values()))

    def test_recommendation_exact_and_rounded_score_tie_breaks(self):
        identical = []
        for title in ("Identical A", "Identical B", "Identical C"):
            identical.append(
                self.client.post(
                    "/products",
                    json={
                        "title": title,
                        "category": "QA Exact Tie",
                        "price": 1000,
                        "age": 1,
                        "condition": "Good",
                    },
                ).json()
            )
        exact_ties = self.client.get(
            "/recommendations",
            params={"budget": 2000, "category": "QA Exact Tie", "priority": "affordability"},
        ).json()
        self.assertEqual(
            [row["product"]["id"] for row in exact_ties],
            sorted(item["id"] for item in identical),
        )

        near_tie = []
        for title, price, age in (
            ("Slightly lower raw score", 1000, 100),
            ("Slightly higher raw score", 1000.01, 99.9783),
            ("Age range anchor", 2000, 0),
        ):
            near_tie.append(
                self.client.post(
                    "/products",
                    json={
                        "title": title,
                        "category": "QA Rounded Tie",
                        "price": price,
                        "age": age,
                        "condition": "Good",
                    },
                ).json()
            )
        ranked = self.client.get(
            "/recommendations",
            params={"budget": 2000, "category": "QA Rounded Tie", "priority": "affordability"},
        ).json()
        self.assertEqual(ranked[0]["product"]["title"], "Slightly higher raw score")
        self.assertEqual(ranked[0]["final_score"], ranked[1]["final_score"])


if __name__ == "__main__":
    unittest.main()
