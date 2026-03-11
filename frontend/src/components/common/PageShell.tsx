import type { ReactNode } from "react";
import Breadcrumb from "./Breadcrumb";
import type { BreadcrumbItem } from "./Breadcrumb";

interface PageShellProps {
  breadcrumb?: BreadcrumbItem[];
  title: string;
  subtitle?: string;
  actions?: ReactNode;
  children: ReactNode;
}

export default function PageShell({
  breadcrumb,
  title,
  subtitle,
  actions,
  children,
}: PageShellProps) {
  return (
    <div className="fade-in">
      {breadcrumb && breadcrumb.length > 0 && (
        <div style={{ marginBottom: 16 }}>
          <Breadcrumb items={breadcrumb} />
        </div>
      )}
      <div className="page-header" style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
        <div>
          <h1 className="page-title">{title}</h1>
          {subtitle && <p className="page-description">{subtitle}</p>}
        </div>
        {actions && <div style={{ display: "flex", gap: 8, flexShrink: 0 }}>{actions}</div>}
      </div>
      {children}
    </div>
  );
}
