import { Outlet, NavLink, useNavigate } from "react-router-dom";
import { useState } from "react";
import { Search, PlusCircle, Tag, Zap, BookOpen } from "lucide-react";

export default function Layout() {
  const navigate = useNavigate();
  const [query, setQuery] = useState("");

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim()) {
      navigate(`/search?q=${encodeURIComponent(query.trim())}`);
    }
  };

  return (
    <div className="min-h-screen flex flex-col">
      {/* Top nav */}
      <header className="sticky top-0 z-30 bg-slate-950/90 backdrop-blur border-b border-slate-800">
        <div className="max-w-7xl mx-auto px-4 h-14 flex items-center gap-4">
          {/* Logo */}
          <NavLink to="/" className="flex items-center gap-2 shrink-0">
            <span className="w-8 h-8 rounded-lg bg-brand-500 flex items-center justify-center text-white font-bold text-sm select-none">
              Z
            </span>
            <span className="font-semibold text-slate-100 hidden sm:block">
              Zomato Notes
            </span>
          </NavLink>

          {/* Global search bar */}
          <form onSubmit={handleSearch} className="flex-1 max-w-xl">
            <div className="relative">
              <Search
                size={15}
                className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500 pointer-events-none"
              />
              <input
                type="search"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Search notes… (press Enter)"
                className="input pl-9 pr-3 py-1.5 text-sm h-9"
                aria-label="Global search"
              />
            </div>
          </form>

          {/* Nav links */}
          <nav className="flex items-center gap-1 ml-auto">
            <NavLink
              to="/"
              end
              className={({ isActive }) =>
                `btn-ghost text-xs px-3 py-1.5 ${isActive ? "text-brand-400" : ""}`
              }
            >
              <BookOpen size={15} />
              <span className="hidden sm:inline">Notes</span>
            </NavLink>
            <NavLink
              to="/search"
              className={({ isActive }) =>
                `btn-ghost text-xs px-3 py-1.5 ${isActive ? "text-brand-400" : ""}`
              }
            >
              <Zap size={15} />
              <span className="hidden sm:inline">Smart Search</span>
            </NavLink>
            <NavLink
              to="/notes/new"
              className="btn-primary text-xs px-3 py-1.5 ml-1"
            >
              <PlusCircle size={15} />
              <span className="hidden sm:inline">New Note</span>
            </NavLink>
          </nav>
        </div>
      </header>

      {/* Page content */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 py-6">
        <Outlet />
      </main>

      <footer className="border-t border-slate-800 py-3 text-center text-xs text-slate-600">
        Zomato On-Call Notes — internal tool
      </footer>
    </div>
  );
}
