import { useEffect, useState } from "react";
import { ArrowLeft, Check, Info } from "lucide-react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { api } from "../services/api";
import { ErrorState, Loading, Notice } from "../components/Feedback";

const blank = { title: "", category: "", price: "", original_price: "", age: "", condition: "" };

export default function ListingForm() {
  const [params] = useSearchParams();
  const id = params.get("id");
  const navigate = useNavigate();
  const [form, setForm] = useState(blank);
  const [categories, setCategories] = useState([]);
  const [errors, setErrors] = useState({});
  const [loading, setLoading] = useState(Boolean(id));
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState(null);
  useEffect(() => {
    api.summary().then((data) => setCategories(data.categories)).catch((err) => setNotice({ type: "error", message: err.message }));
    if (id) api.products().then((products) => {
      const product = products.find((item) => String(item.id) === id);
      if (!product) throw new Error("Listing not found.");
      setForm({ title: product.title, category: product.category, price: String(product.price), original_price: product.original_price == null ? "" : String(product.original_price), age: product.age == null ? "" : String(product.age), condition: product.condition || "" });
    }).catch((err) => setNotice({ type: "error", message: err.message })).finally(() => setLoading(false));
  }, [id]);
  const update = (key, value) => { setForm((current) => ({ ...current, [key]: value })); setErrors((current) => ({ ...current, [key]: "" })); };
  function validate() {
    const next = {};
    if (!form.title.trim()) next.title = "Please enter a product title.";
    if (!form.category.trim()) next.category = "Choose or enter a category.";
    if (!form.price || Number(form.price) <= 0) next.price = "Selling price must be greater than ₹0.";
    if (form.original_price !== "" && Number(form.original_price) < 0) next.original_price = "Original price cannot be negative.";
    if (form.age !== "" && Number(form.age) < 0) next.age = "Age cannot be negative.";
    return next;
  }
  async function submit(event) {
    event.preventDefault();
    const invalid = validate();
    setErrors(invalid);
    if (Object.keys(invalid).length) return;
    const payload = {
      title: form.title.trim(), category: form.category.trim(), price: Number(form.price),
      original_price: form.original_price === "" ? null : Number(form.original_price),
      age: form.age === "" ? null : Number(form.age), condition: form.condition || null,
    };
    setBusy(true);
    try { if (id) await api.updateProduct(id, payload); else await api.createProduct(payload); navigate("/marketplace", { state: { notice: id ? "Listing updated successfully." : "Your listing is live." } }); }
    catch (err) { setNotice({ type: "error", message: err.message }); }
    finally { setBusy(false); }
  }
  if (loading) return <Loading label="Loading listing..." />;
  return <><Notice notice={notice} onClose={() => setNotice(null)} />
    <div className="form-page"><div className="form-intro"><Link to="/marketplace" className="back-link"><ArrowLeft size={15} /> Back to marketplace</Link><h2>{id ? "Edit your listing" : "List something useful"}</h2><p>A clear, honest listing helps fellow students find a great deal.</p><div className="form-note"><Info size={16} /><span>Use accurate details. A good listing makes a better campus community.</span></div></div>
      <form className="listing-form panel" onSubmit={submit} noValidate>
        <div className="form-section-title"><span>01</span><div><strong>Item details</strong><p>What are you passing along?</p></div></div>
        <label className="form-field">Product title <span className="required">*</span><input value={form.title} maxLength="160" placeholder="e.g. Calculus textbook, Mountain bike" onChange={(e) => update("title", e.target.value)} aria-invalid={Boolean(errors.title)} />{errors.title && <small className="field-error">{errors.title}</small>}</label>
        <label className="form-field">Category <span className="required">*</span><input list="categories" value={form.category} maxLength="80" placeholder="e.g. Laptop, Books, Bicycle" onChange={(e) => update("category", e.target.value)} aria-invalid={Boolean(errors.category)} /><datalist id="categories">{categories.map((category) => <option key={category} value={category} />)}</datalist>{errors.category && <small className="field-error">{errors.category}</small>}</label>
        <div className="form-section-title with-space"><span>02</span><div><strong>Price & condition</strong><p>Help buyers compare with confidence.</p></div></div>
        <div className="form-two-col"><label className="form-field">Selling price (₹) <span className="required">*</span><input type="number" min="1" step="0.01" value={form.price} placeholder="e.g. 1200" onChange={(e) => update("price", e.target.value)} aria-invalid={Boolean(errors.price)} />{errors.price && <small className="field-error">{errors.price}</small>}</label><label className="form-field">Original price (₹)<input type="number" min="0" step="0.01" value={form.original_price} placeholder="Optional" onChange={(e) => update("original_price", e.target.value)} aria-invalid={Boolean(errors.original_price)} />{errors.original_price && <small className="field-error">{errors.original_price}</small>}</label></div>
        <div className="form-two-col"><label className="form-field">Age (years)<input type="number" min="0" step="0.1" value={form.age} placeholder="Optional" onChange={(e) => update("age", e.target.value)} aria-invalid={Boolean(errors.age)} />{errors.age && <small className="field-error">{errors.age}</small>}</label><label className="form-field">Condition<select value={form.condition} onChange={(e) => update("condition", e.target.value)}><option value="">Not provided</option>{["Excellent", "Good", "Average", "Poor"].map((item) => <option key={item}>{item}</option>)}</select></label></div>
        <div className="form-actions"><Link to="/marketplace" className="button button-outline">Cancel</Link><button className="button button-primary" type="submit" disabled={busy}>{busy ? "Saving..." : <><Check size={16} /> {id ? "Save changes" : "Publish listing"}</>}</button></div>
      </form>
    </div>
  </>;
}
