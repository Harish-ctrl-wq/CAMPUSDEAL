import { NavLink, Outlet, useLocation } from "react-router-dom";
import { BarChart3, BookOpen, Boxes, ChevronRight, LayoutDashboard, Plus, Sparkles } from "lucide-react";

const links = [
  { to: "/", label: "Dashboard", icon: LayoutDashboard, end: true },
  { to: "/marketplace", label: "Marketplace", icon: Boxes },
  { to: "/recommendations", label: "Recommendations", icon: Sparkles },
];
const titles = {
  "/": ["Overview", "Your student marketplace at a glance"],
  "/marketplace": ["Marketplace", "Find your next campus essential"],
  "/recommendations": ["Smart picks", "Thoughtful recommendations, made for your budget"],
  "/add-listing": ["Add a listing", "Give useful things a second life"],
};

export default function Layout() {
  const { pathname } = useLocation();
  const [title, subtitle] = titles[pathname] || titles["/"];
  return (
    <div className="min-h-screen bg-[#f7f9fb] lg:flex">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-icon"><BookOpen size={19} /></div>
          <div><strong>campus<span>deal</span></strong><small>STUDENT MARKETPLACE</small></div>
        </div>
        <div className="side-label">WORKSPACE</div>
        <nav className="side-nav">
          {links.map(({ to, label, icon: Icon, end }) => (
            <NavLink key={to} to={to} end={end} className={({ isActive }) => `side-link ${isActive ? "active" : ""}`}>
              <Icon size={18} /><span>{label}</span>{label === "Recommendations" && <span className="nav-new">AI</span>}
            </NavLink>
          ))}
        </nav>
        <NavLink to="/add-listing" className="sidebar-add"><Plus size={17} /> Add a listing</NavLink>
        <div className="sidebar-bottom">
          <div className="campus-card"><div className="campus-orb"><BarChart3 size={16} /></div><strong>Good finds. Better budgets.</strong><p>Buy smarter. Spend wiser.</p><ChevronRight size={15} /></div>
          <div className="student-profile"><div className="avatar">S</div><div><strong>Student</strong><small>Campus community</small></div></div>
        </div>
      </aside>
      <div className="main-column">
        <header className="topbar">
          <div className="mobile-brand"><div className="brand-icon"><BookOpen size={17} /></div><strong>campus<span>deal</span></strong></div>
          <div className="breadcrumb">CampusDeal <ChevronRight size={13} /> <span>{title}</span></div>
          <div className="topbar-right"><span className="live-dot" /> Student marketplace <div className="avatar small">S</div></div>
        </header>
        <nav className="mobile-nav" aria-label="Main navigation">
          {[...links, { to: "/add-listing", label: "Add listing", icon: Plus }].map(({ to, label, icon: Icon, end }) => (
            <NavLink key={to} to={to} end={end} className={({ isActive }) => `mobile-nav-link ${isActive ? "active" : ""}`}>
              <Icon size={15} /><span>{label}</span>
            </NavLink>
          ))}
        </nav>
        <main className="page-wrap">
          <div className="page-heading"><div><p className="eyebrow">CAMPUSDEAL · BUY SMARTER. SPEND WISER.</p><h1>{title}</h1><p className="page-subtitle">{subtitle}</p></div></div>
          <Outlet />
        </main>
      </div>
    </div>
  );
}
