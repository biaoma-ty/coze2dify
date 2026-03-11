import * as Dialog from "@radix-ui/react-dialog";
import { X } from "lucide-react";
import type { ReactNode } from "react";

interface ModalProps {
  open: boolean;
  onClose: () => void;
  title?: string;
  children: ReactNode;
  maxWidth?: number;
}

export default function Modal({
  open,
  onClose,
  title,
  children,
  maxWidth = 520,
}: ModalProps) {
  return (
    <Dialog.Root open={open} onOpenChange={(v) => !v && onClose()}>
      <Dialog.Portal>
        <Dialog.Overlay className="modal-overlay" />
        <Dialog.Content
          className="modal-panel"
          style={{ maxWidth }}
          aria-describedby={undefined}
        >
          {title && (
            <div className="modal-header">
              <Dialog.Title className="modal-title">{title}</Dialog.Title>
              <Dialog.Close asChild>
                <button className="drawer-close" aria-label="Close">
                  <X size={18} />
                </button>
              </Dialog.Close>
            </div>
          )}
          <div className="modal-body">{children}</div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
