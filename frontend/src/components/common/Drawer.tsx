import * as Dialog from "@radix-ui/react-dialog";
import { X } from "lucide-react";
import type { ReactNode } from "react";

interface DrawerProps {
  open: boolean;
  onClose: () => void;
  title?: string;
  children: ReactNode;
  width?: number;
}

export default function Drawer({
  open,
  onClose,
  title,
  children,
  width = 480,
}: DrawerProps) {
  return (
    <Dialog.Root open={open} onOpenChange={(v) => !v && onClose()}>
      <Dialog.Portal>
        <Dialog.Overlay className="drawer-overlay" />
        <Dialog.Content
          className="drawer-panel"
          style={{ width }}
          aria-describedby={undefined}
        >
          {title && (
            <div className="drawer-header">
              <Dialog.Title className="drawer-title">{title}</Dialog.Title>
              <Dialog.Close asChild>
                <button className="drawer-close" aria-label="Close">
                  <X size={18} />
                </button>
              </Dialog.Close>
            </div>
          )}
          <div className="drawer-body">{children}</div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
