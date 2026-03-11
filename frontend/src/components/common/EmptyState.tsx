import type { ReactNode } from "react";
import type { LucideIcon } from "lucide-react";
import { Inbox } from "lucide-react";

interface EmptyStateProps {
  icon?: LucideIcon;
  text: string;
  action?: ReactNode;
}

export default function EmptyState({
  icon: Icon = Inbox,
  text,
  action,
}: EmptyStateProps) {
  return (
    <div className="empty-state">
      <div className="empty-state__icon">
        <Icon size={40} strokeWidth={1.5} />
      </div>
      <p className="empty-state__text">{text}</p>
      {action && <div style={{ marginTop: 16 }}>{action}</div>}
    </div>
  );
}
