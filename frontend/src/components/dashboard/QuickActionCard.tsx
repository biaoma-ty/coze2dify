import { Link } from "@umijs/max";
import type { LucideIcon } from "lucide-react";

interface QuickActionCardProps {
  icon: LucideIcon;
  title: string;
  description: string;
  to: string;
}

export default function QuickActionCard({
  icon: Icon,
  title,
  description,
  to,
}: QuickActionCardProps) {
  return (
    <Link to={to} className="quick-action-card" style={{ textDecoration: "none" }}>
      <div className="quick-action-card__icon">
        <Icon size={24} strokeWidth={1.5} />
      </div>
      <div className="quick-action-card__title">{title}</div>
      <div className="quick-action-card__desc">{description}</div>
    </Link>
  );
}
