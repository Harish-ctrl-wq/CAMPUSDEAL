import { Link } from "react-router-dom";
import { ArrowDownRight, ArrowUpRight, Pencil, Trash2 } from "lucide-react";
import { money } from "../services/api";

export default function ProductCard({ product, onDelete }) {
  const anomaly = product.anomaly;
  return (
    <article className="product-card">
      <div className="product-card-top"><span className="category-pill">{product.category}</span><span className={`condition-pill ${(product.condition || "").toLowerCase()}`}>{product.condition || "Condition not listed"}</span></div>
      <div className="product-illustration"><div className="product-glyph">{product.category.toLowerCase().includes("book") ? "▤" : product.category.toLowerCase().includes("bike") ? "◉" : product.category.toLowerCase().includes("phone") || product.category.toLowerCase().includes("gadget") ? "▯" : "⌘"}</div><span className="listing-number">CD-{String(product.id).padStart(4, "0")}</span></div>
      <div className="product-info"><h3>{product.title}</h3><p className="product-meta">{product.age == null ? "Age not provided" : `${product.age} ${product.age === 1 ? "year" : "years"} old`} <span>·</span> Listed on {new Date(product.created_at).toLocaleDateString("en-IN", { day: "numeric", month: "short" })}</p></div>
      <div className="price-row"><div><span className="price-label">ASKING PRICE</span><strong>{money(product.price)}</strong></div>{product.original_price ? <div className="original-price"><span>Original</span><del>{money(product.original_price)}</del></div> : null}</div>
      <div className="ratio-row"><span>Price / original</span><strong>{product.price_ratio == null ? "Not available" : `${product.price_ratio}%`}</strong>{product.discount_percentage != null && <span className="discount">{product.discount_percentage}% lower</span>}</div>
      {anomaly && <div className={`anomaly-note ${anomaly.is_anomaly ? "flagged" : ""}`}><span>{anomaly.is_anomaly ? <ArrowUpRight size={14} /> : anomaly.status === "insufficient_data" ? "i" : <ArrowDownRight size={14} />}</span>{anomaly.explanation}</div>}
      <div className="product-actions"><Link className="button button-soft" to={`/add-listing?id=${product.id}`}><Pencil size={14} /> Edit listing</Link><button className="icon-button delete-button" onClick={() => onDelete(product)} title="Delete listing" aria-label={`Delete ${product.title}`}><Trash2 size={16} /></button></div>
    </article>
  );
}
