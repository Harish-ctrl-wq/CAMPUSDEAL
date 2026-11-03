# CAMPUSDEAL QA Audit Report

**Audit date:** 2026-11-03
**Scope:** Frontend/backend connectivity, product CRUD, search and filters, CSV/JSON imports, recommendations, anomaly detection, missing and invalid values, duplicate handling, tie-breaking, budget boundaries, and responsive layouts.

## Test results

| Test case ID | Test description | Expected result | Actual result | Status |
|---|---|---|---|---|
| CD-QA-01 | Frontend-to-backend connectivity: load dashboard and query API health/analytics | UI receives live API data; API endpoints respond successfully | Dashboard displayed 5 live listings; `/` and `/analytics/summary` returned HTTP 200 | PASS |
| CD-QA-02 | Product create, update, and delete through REST API | Create returns 201, update 200, delete 204; missing delete returns 404; import source metadata remains intact on edit | All status checks matched; an updated imported listing retained its source ID and a repeat import was skipped as duplicate | PASS |
| CD-QA-03 | Product create, edit, and delete through browser form | Listing is saved, edits persist, delete confirmation removes the listing | Browser create and edit success notices displayed; DELETE returned 204 and the card was removed | PASS |
| CD-QA-04 | Search and category, budget, condition, and sort filters | Each control returns only matching items and price sorting is ordered | Search “Laptop C” returned 1; ₹15,000 cap returned Laptop E; Excellent filter returned Laptop C; ascending price put Laptop E first | PASS |
| CD-QA-05 | CSV import with valid and invalid rows, then repeat import | Valid row imported; invalid row reported; repeat recognized as duplicate | First import reported 1 imported / 1 invalid; repeat reported duplicate | PASS |
| CD-QA-06 | JSON import of generated 25-item dataset across five categories | All valid records stored and individually queryable | 25 records across QA Laptop, Books, Bicycles, Gadgets, and Furniture imported successfully | PASS |
| CD-QA-07 | Duplicate detection on repeated generated JSON import | Existing records skipped and duplicate count reported | Re-import reported 25 duplicates and imported 0 | PASS |
| CD-QA-08 | Recommendation budget eligibility using supplied laptop data | At ₹23,000: 4 eligible; at ₹15,000: 1; at ₹10,000: 0 | Filtered listing counts were 4, 1, and 0 respectively; recommendation output remained capped at the top 3 | PASS |
| CD-QA-09 | Affordability-priority score and ranking at ₹23,000 | Scores use the specified weights, only in-budget laptops qualify, and descending ranking is returned | Top three were Laptop E (32.61), Laptop D (30.98), Laptop B (27.88); all were in budget | PASS |
| CD-QA-10 | Condition-priority score and dynamic priority switch | Condition weights are recalculated and the order updates when switched | API and browser switched the top result from Laptop E (affordability) to Laptop D (condition, 61.96) | PASS |
| CD-QA-11 | Category median and outlier detection on generated dataset | Each category uses its own median; one price at ₹200 is flagged against median ₹100 | All five generated categories reported median ₹100 and flagged only their ₹200 listing | PASS |
| CD-QA-12 | Sparse category anomaly handling | Fewer than three comparable listings report insufficient data without a median or fraud claim | Both listings in a two-item category returned `insufficient_data`, null median, and the explanatory message | PASS |
| CD-QA-13 | Missing age, condition, and original-price handling | Missing age gets neutral 0.50; missing condition is not assumed; absent/zero original price has no ratio | Recommendation used age 0.50; unknown-condition listing was excluded; missing and zero original prices returned null ratio and discount | PASS |
| CD-QA-14 | Invalid negative values | Negative selling price, age, and original price are rejected; browser age validation is visible | API returned HTTP 422 for each negative-value case; browser showed the age validation error and did not submit | PASS |
| CD-QA-15 | Exact and rounded-score tie behavior | Exact score ties use lower price then ID; displayed-score rounding must not reorder unequal raw scores | Identical score entries were ordered by ID; near-equal scores displaying the same rounded value were ordered by their unrounded scores | PASS |
| CD-QA-16 | Responsive layout and mobile navigation | Main pages fit narrow/mobile and desktop widths without horizontal page overflow; navigation is reachable | Dashboard, marketplace, recommendations, and listing form checked at 320, 390, 768, and 1280 px; document width did not exceed viewport and navigation was visible | PASS |
| CD-QA-17 | Final backend tests, compilation, frontend production build, dependency audit | Tests/build/compile succeed and no dependency advisories remain | 10/10 backend tests passed; Python compilation passed; Vite production build passed; `npm audit` found 0 vulnerabilities | PASS |

### Executed test commands

- `python -m unittest discover -s tests -v` — **10 tests passed**
- `python -m compileall -q .` — **passed**
- `npm run build` — **passed**
- `npm audit` — **0 vulnerabilities**

The backend tests use an isolated temporary SQLite database. The 25 generated products are constructed during the test and imported through the real JSON API; the supplied five-laptop seed dataset is also verified independently.

## Bugs discovered and fixed

1. **Recommendation sorting used rounded display scores.** Two unequal underlying scores that rounded to the same two-decimal value could be incorrectly treated as a tie, allowing the price tie-breaker to invert the true ranking. Sorting now uses unrounded scores and only rounds the returned display score. A near-tie regression case passes.
2. **Mobile navigation was hidden with the desktop sidebar.** Added a compact mobile navigation row for Dashboard, Marketplace, Recommendations, and Add Listing. Browser checks at 320–390 px confirmed visible navigation and no page-level horizontal overflow.
3. **Zero original price was rejected.** The requirement calls for safe zero/missing original-price handling. The API schema and form now accept zero while returning unavailable ratio/discount values. API and browser create checks pass.
4. **Editing a listing cleared its import source ID.** The browser CRUD audit showed that a full-form update with no source ID could erase the import de-duplication key. Updates now preserve existing source IDs when the field is omitted; a repeat import after an update is skipped in the regression test.

## Audit observations and cleanup

- One early browser save attempt received HTTP 422 because the already-running Uvicorn process had loaded the pre-fix schema. Restarting the process loaded the updated code; the same zero-original-price create then returned HTTP 201. This was a stale-process issue, not a remaining application failure.
- During browser CRUD testing, a broad edit selector initially targeted the seeded Laptop A record. The original seed row was restored with its original ID and exact supplied field values; temporary QA listings were removed. The five seeded records P01–P05 were verified with their original values and IDs.
- A separate `second hand laptop` listing was present in the shared persistent database during the final runtime check. It was not part of the isolated generated test fixture and was left untouched. The seeded P01–P05 rows remained intact; the generated QA dataset and CRUD tests used temporary databases or clearly identified QA listings.
- CSV import validation is covered by backend tests; the browser import control was exercised with the supplied JSON file and correctly reported 5 duplicates, 0 imported, and 0 invalid.

## Remaining limitations

- Browser interactions were exercised in the integrated browser; there is no separate committed automated browser-test suite.
- Recommendations intentionally show at most three products even when more listings are eligible; the separate marketplace filter was used to verify the eligible counts.
- No authentication, messaging, or payment flow is part of this application.
