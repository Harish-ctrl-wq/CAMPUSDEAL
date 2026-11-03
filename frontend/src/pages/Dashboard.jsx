import { useEffect, useState } from "react";
import { ArrowRight, BadgeAlert, Boxes, CircleDollarSign, PackageCheck, Plus, Sparkles } from "lucide-react";
import { Link } from "react-router-dom";
import { api, money } from "../services/api";
import { ErrorState, Loading } from "../components/Feedback";

const Stat = ({ icon: Icon, label, value, note, tone }) => <div className="stat-card"><div className={`stat-icon ${tone}`}><Icon size={19} /></div><span className="stat-label">{label}</span><strong className="stat-value">{value}</strong><small>{note}</small></div>;

export default function Dashboard() {
  const [summary, setSummary] = useState(null);
  const [error, setError] = useState("");
  const load = () => api.summary().then(setSummary).catch((err) => setError(err.message));
  useEffect(() => { load(); }, []);
  if (error) return <ErrorState message={error} onRetry={() => { setError(""); load(); }} />;
  if (!summary) return <Loading />;
  return (
    <>
      <section className="welcome-banner"><div className="welcome-copy"><span className="welcome-tag"><Sparkles size={13} /> YOUR SMARTER CAMPUS CIRCLE</span><h2>Great finds are closer<br />than you think.</h2><p>Discover pre-loved essentials from your community. Better for your budget, and better for the planet.</p><div className="welcome-actions"><Link to="/marketplace" className="button button-white">Explore marketplace <ArrowRight size={15} /></Link><Link to="/add-listing" className="button button-ghost"><Plus size={15} /> List an item</Link></div></div><div className="welcome-art" aria-hidden="true"><div className="art-sun" /><div className="art-circle circle-one" /><div className="art-circle circle-two" /><div className="art-card"><PackageCheck size={25} /><span>Good things,<br />second rounds.</span></div><div className="art-leaf">✳</div></div></section>
      <div className="section-title-row"><div><h2>Marketplace pulse</h2><p>What's happening around campus</p></div><Link to="/marketplace" className="text-link">View marketplace <ArrowRight size={15} /></Link></div>
      <section className="stats-grid">
        <Stat icon={Boxes} label="Total listings" value={summary.total_listings} note="Across the community" tone="blue" />
        <Stat icon={PackageCheck} label="Categories" value={summary.available_categories} note={summary.categories.join(", ") || "No categories yet"} tone="green" />
        <Stat icon={CircleDollarSign} label="Average asking price" value={money(summary.average_price)} note="Based on active listings" tone="gold" />
        <Stat icon={BadgeAlert} label="Unusual prices" value={summary.unusual_price_listings} note="Worth a closer look · not proof of fraud" tone="rose" />
      </section>
      <section className="panel recent-panel"><div className="panel-heading"><div><h2>Fresh on campus</h2><p>The latest finds, just listed</p></div><Link to="/marketplace" className="icon-link" aria-label="See all listings"><ArrowRight size={17} /></Link></div>
        {!summary.recent_products.length ? <div className="empty-inline">No listings yet — be the first to share something useful.</div> : <div className="recent-list">{summary.recent_products.map((item) => <Link className="recent-item" to="/marketplace" key={item.id}><div className="recent-thumb">{item.category.toLowerCase().includes("book") ? "▤" : item.category.toLowerCase().includes("bike") ? "◉" : "⌘"}</div><div className="recent-description"><strong>{item.title}</strong><span>{item.category} <span className="muted-separator">·</span> {new Date(item.created_at).toLocaleDateString("en-IN", { day: "numeric", month: "short" })}</span></div><strong className="recent-price">{money(item.price)}</strong><ArrowRight size={14} className="recent-arrow" /></Link>)}</div>}
      </section>
    </>
  );
}
