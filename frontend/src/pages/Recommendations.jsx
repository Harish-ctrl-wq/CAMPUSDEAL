import { useEffect, useState } from "react";
import { Award, CheckCircle2, Heart, Medal, Sparkles, Target } from "lucide-react";
import { api, money } from "../services/api";
import { EmptyState, ErrorState, Loading } from "../components/Feedback";

const rankIcons = [Award, Medal, Heart];
function ScoreBar({ label, score, detail, color }) {
  return <div className="score-line"><div className="score-line-label"><span>{label}</span><strong>{Math.round(score * 100)}<small>%</small></strong></div><div className="score-track"><div className={`score-fill ${color}`} style={{ width: `${score * 100}%` }} /></div><small>{detail}</small></div>;
}

export default function Recommendations() {
  const [categories, setCategories] = useState([]);
  const [budget, setBudget] = useState("23000");
  const [category, setCategory] = useState("");
  const [priority, setPriority] = useState("affordability");
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  useEffect(() => { api.summary().then((data) => { setCategories(data.categories); setCategory(data.categories[0] || ""); }).catch((err) => setError(err.message)); }, []);
  useEffect(() => {
    if (!category || !budget || Number(budget) <= 0) { setResults(null); return; }
    let active = true;
    setLoading(true); setError("");
    api.recommendations({ budget, category, priority }).then((data) => { if (active) setResults(data); }).catch((err) => { if (active) setError(err.message); }).finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [budget, category, priority]);
  if (error && !categories.length) return <ErrorState message={error} onRetry={() => window.location.reload()} />;
  return <div className="recommend-layout">
    <section className="recommend-controls">
      <div className="recommend-intro"><div className="recommend-spark"><Sparkles size={18} /></div><span className="eyebrow">PERSONALIZED PICKS</span><h2>Find the right<br />fit for your budget.</h2><p>We score real listings against what matters to you, and show exactly how each one earned its place.</p></div>
      <div className="priority-switch"><label>Your buying priority</label><button className={priority === "affordability" ? "selected" : ""} onClick={() => setPriority("affordability")}><Target size={16} /><span><strong>Affordability</strong><small>Make every rupee count</small></span></button><button className={priority === "condition" ? "selected" : ""} onClick={() => setPriority("condition")}><CheckCircle2 size={16} /><span><strong>Best condition</strong><small>Quality comes first</small></span></button></div>
      <div className="recommend-fields"><label className="form-field">Your budget (₹)<input type="number" min="1" value={budget} onChange={(e) => setBudget(e.target.value)} placeholder="Enter your budget" /></label><label className="form-field">Looking for<select value={category} onChange={(e) => setCategory(e.target.value)}>{categories.length ? categories.map((item) => <option key={item}>{item}</option>) : <option value="">No categories yet</option>}</select></label></div>
      <div className="formula-hint"><Sparkles size={15} /><span>Scores weigh {priority === "affordability" ? "affordability 65%, age 15%, condition 20%" : "condition 70%, affordability 15%, age 15%"}.</span></div>
    </section>
    <section className="recommend-results"><div className="recommend-result-heading"><div><span className="eyebrow">MADE FOR YOU</span><h2>Top recommendations</h2><p>Ranked from eligible {category || "category"} listings</p></div><span className="top-three-badge">TOP 3</span></div>
      {error && <ErrorState message={error} />}
      {loading && <Loading label="Scoring matching listings..." />}
      {!loading && results && !results.length && <EmptyState title="No eligible listings yet" description="We only recommend in-budget listings with a known condition. Try a higher budget or another category." />}
      {!loading && results?.length > 0 && <div className="recommend-cards">{results.map((result, index) => {
        const Icon = rankIcons[index];
        const product = result.product;
        const conditionDetail = `${product.condition} · ${Math.round(result.condition_score * 100)}%`;
        return <article className={`recommend-card ${index === 0 ? "winner" : ""}`} key={product.id}>
          <div className="recommend-card-head"><div className={`rank-icon rank-${index}`}><Icon size={17} /></div><span className="rank-label">{index === 0 ? "BEST MATCH" : `PICK #${index + 1}`}</span><span className="final-score">{result.final_score.toFixed(2)}<small> / 100</small></span></div>
          <div className="recommend-product"><div className="recommend-product-glyph">{product.category.toLowerCase().includes("book") ? "▤" : product.category.toLowerCase().includes("bike") ? "◉" : "⌘"}</div><div><h3>{product.title}</h3><span>{product.category} <span>·</span> {product.age == null ? "Age not listed" : `${product.age} ${product.age === 1 ? "year" : "years"} old`}</span></div><strong>{money(product.price)}</strong></div>
          <p className="recommend-explanation">{result.explanation}</p>
          <div className="score-breakdown"><ScoreBar label="Affordability" score={result.affordability_score} detail={`${money(product.price)} of ${money(Number(budget))} budget`} color="green-fill" /><ScoreBar label="Age score" score={result.age_score} detail={product.age == null ? "Neutral score · age not provided" : `${product.age} years`} color="blue-fill" /><ScoreBar label="Condition" score={result.condition_score} detail={conditionDetail} color="gold-fill" /></div>
        </article>;
      })}</div>}
      <p className="recommend-footnote">Only listings in the selected category and within budget are compared. Listings without a condition are excluded; missing age receives a neutral 0.50 score. An unusual price does not automatically exclude a listing.</p>
    </section>
  </div>;
}
