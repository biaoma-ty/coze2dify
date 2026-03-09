import { Link, useLocation } from "react-router-dom";
import { usePlatformStore } from "../../store/platformStore";

const navItems = [
  { to: "/", label: "Migration", icon: "⚡" },
  { to: "/browse", label: "Browse", icon: "🔍" },
  { to: "/sync", label: "Sync", icon: "🔄" },
  { to: "/history", label: "Conversions", icon: "📋" },
];

export default function Header() {
  const location = useLocation();
  const devModeEnabled = usePlatformStore((s) => s.devModeEnabled);

  const isActive = (path: string) => {
    if (path === "/") return location.pathname === "/" || location.pathname.startsWith("/diff") || location.pathname.startsWith("/mapping") || location.pathname.startsWith("/result");
    if (path === "/sync") return location.pathname === "/sync";
    return location.pathname.startsWith(path);
  };

  return (
    <header
      style={{
        background: "rgba(15, 20, 32, 0.85)",
        borderBottom: "1px solid var(--c-border-subtle)",
        padding: "0 24px",
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        height: 56,
        position: "sticky",
        top: 0,
        zIndex: 50,
        backdropFilter: "blur(16px)",
        WebkitBackdropFilter: "blur(16px)",
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: 32 }}>
        <Link to="/" style={{ textDecoration: "none", display: "flex", alignItems: "center", gap: 10 }}>
          <div
            style={{
              width: 30,
              height: 30,
              borderRadius: 8,
              background: "linear-gradient(135deg, #00d4aa, #0891b2)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontSize: 14,
              fontWeight: 800,
              color: "#0a0e17",
              fontFamily: "var(--font-display)",
            }}
          >
            C2D
          </div>
          <span
            style={{
              fontFamily: "var(--font-display)",
              fontWeight: 700,
              fontSize: "1.05rem",
              color: "var(--c-text-primary)",
              letterSpacing: "-0.03em",
            }}
          >
            coze<span style={{ color: "var(--c-accent)" }}>2</span>dify
          </span>
        </Link>

        <nav style={{ display: "flex", gap: 2 }}>
          {navItems.map(({ to, label, icon }) => {
            const active = isActive(to);
            return (
              <Link
                key={to}
                to={to}
                style={{
                  textDecoration: "none",
                  padding: "7px 16px",
                  borderRadius: 6,
                  display: "flex",
                  alignItems: "center",
                  gap: 7,
                  fontSize: "0.82rem",
                  fontWeight: active ? 600 : 500,
                  color: active ? "var(--c-accent)" : "var(--c-text-tertiary)",
                  background: active ? "var(--c-accent-dim)" : "transparent",
                  transition: "all 0.2s ease",
                }}
              >
                <span style={{ fontSize: "0.78rem" }}>{icon}</span>
                {label}
              </Link>
            );
          })}
        </nav>
      </div>

      <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
        {devModeEnabled && (
          <span
            style={{
              fontSize: "0.62rem",
              fontWeight: 800,
              fontFamily: "var(--font-mono)",
              color: "#000",
              background: "var(--c-amber)",
              padding: "2px 8px",
              borderRadius: 100,
              letterSpacing: "0.08em",
            }}
          >
            DEV MODE
          </span>
        )}
        <div
          style={{
            fontSize: "0.68rem",
            fontFamily: "var(--font-mono)",
            color: "var(--c-text-tertiary)",
            background: "var(--c-surface-2)",
            padding: "3px 10px",
            borderRadius: 100,
            border: "1px solid var(--c-border-subtle)",
          }}
        >
          v0.1.0
        </div>
      </div>
    </header>
  );
}
