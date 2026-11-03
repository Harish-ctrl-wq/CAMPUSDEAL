import { useEffect, useState } from "react";
import { FileUp, Search, SlidersHorizontal, X } from "lucide-react";
import { useLocation, useNavigate } from "react-router-dom";
import ProductCard from "../components/ProductCard";
import { EmptyState, ErrorState, Loading, Notice } from "../components/Feedback";
import { api } from "../services/api";

export default function Marketplace() {
  const location = useLocation();
  const navigate = useNavigate();
  const [products, setProducts] = useState(null);
  const [filters, setFilters] = useState({ q: "", category: "", max_budget: "", condition: "", sort: "" });
  const [categories, setCategories] = useState([]);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState(null);
  const [importReport, setImportReport] = useState(null);
  const [busy, setBusy] = useState(false);
  useEffect(() => {
    if (location.state?.notice) {
      setNotice({ type: "success", message: location.state.notice });
      navigate(location.pathname, { replace: true, state: null });
    }
  }, [location, navigate]);
  const load = () => api.products(filters).then((data) => { setProducts(data); setError(""); }).catch((err) => setError(err.message));
  useEffect(() => { api.summary().then((data) => setCategories(data.categories)).catch((err) => setError(err.message)); }, []);
  useEffect(() => { setProducts(null); const timer = setTimeout(load, 180); return () => clearTimeout(timer); }, [filters]);
  const set = (key, value) => setFilters((current) => ({ ...current, [key]: value }));
  async function remove(product) {
    if (!window.confirm(`Delete "${product.title}"? This cannot be undone.`)) return;
    try { await api.deleteProduct(product.id); setNotice({ type: "success", message: "Listing deleted." }); load(); }
    catch (err) { setNotice({ type: "error", message: err.message }); }
  }
  async function importFile(event) {
    const file = event.target.files?.[0];
    event.target.value = "";
    if (!file) return;
    setBusy(true); setImportReport(null);
    try {
      const report = await api.importFile(file);
      setImportReport(report);
      setNotice({ type: "success", message: `Imported ${report.imported_count} listing${report.imported_count === 1 ? "" : "s"}.` });
      load();
    } catch (err) { setNotice({ type: "error", message: err.message }); }
    finally { setBusy(false); }
  }
  return (
    <>
      <Notice notice={notice} onClose={() => setNotice(null)} />
      <div className="marketplace-toolbar"><div className="search-field"><Search size={17} /><input aria-label="Search listings" placeholder="Search laptops, books, bikes..." value={filters.q} onChange={(e) => set("q", e.target.value)} />{filters.q && <button onClick={() => set("q", "")} aria-label="Clear search"><X size={15} /></button>}</div>
        <label className={`button button-outline import-button ${busy ? "disabled" : ""}`}><FileUp size={16} /> {busy ? "Importing..." : "Import CSV / JSON"}<input type="file" accept=".csv,.json" onChange={importFile} disabled={busy} /></label>
      </div>
      {importReport && <div className="import-report"><strong>Import results</strong><span>{importReport.imported_count} imported</span><span>{importReport.duplicate_count} duplicates skipped</span><span>{importReport.invalid_count} invalid</span>{importReport.invalid_records.length > 0 && <details><summary>Review invalid records</summary><ul>{importReport.invalid_records.map((r) => <li key={r.record}>Record {r.record}: {r.errors.join(", ")}</li>)}</ul></details>}</div>}
      <section className="filter-bar"><div className="filter-heading"><SlidersHorizontal size={15} /> Refine results</div>
        <select aria-label="Filter by category" value={filters.category} onChange={(e) => set("category", e.target.value)}><option value="">All categories</option>{categories.map((category) => <option key={category}>{category}</option>)}</select>
        <div className="budget-input"><span>₹</span><input aria-label="Maximum budget" type="number" min="1" placeholder="Max budget" value={filters.max_budget} onChange={(e) => set("max_budget", e.target.value)} /></div>
        <select aria-label="Filter by condition" value={filters.condition} onChange={(e) => set("condition", e.target.value)}><option value="">Any condition</option>{["Excellent", "Good", "Average", "Poor"].map((item) => <option key={item}>{item}</option>)}</select>
        <select aria-label="Sort by price" value={filters.sort} onChange={(e) => set("sort", e.target.value)}><option value="">Recently added</option><option value="price_asc">Price: low to high</option><option value="price_desc">Price: high to low</option></select>
        {(filters.category || filters.max_budget || filters.condition || filters.sort) && <button className="clear-filters" onClick={() => setFilters((current) => ({ ...current, category: "", max_budget: "", condition: "", sort: "" }))}>Clear filters <X size={13} /></button>}
      </section>
      {error && <ErrorState message={error} onRetry={load} />}
      {!products && !error ? <Loading /> : products && <div className="results-caption"><span><strong>{products.length}</strong> {products.length === 1 ? "listing" : "listings"} to explore</span><span>Prices shown in INR</span></div>}
      {products && (products.length ? <section className="product-grid">{products.map((product) => <ProductCard key={product.id} product={product} onDelete={remove} />)}</section> : <EmptyState title="No listings match just yet" description="Try adjusting your search or filters, or add a new listing." />)}
    </>
  );
}
