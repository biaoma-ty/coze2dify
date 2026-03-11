import * as RadixToast from "@radix-ui/react-toast";
import { createContext, useCallback, useContext, useState } from "react";
import type { ReactNode } from "react";
import { X, CheckCircle2, AlertTriangle, XCircle, Info } from "lucide-react";

type ToastVariant = "success" | "error" | "warning" | "info";

interface ToastItem {
  id: number;
  message: string;
  variant: ToastVariant;
}

interface ToastContextValue {
  toast: (message: string, variant?: ToastVariant) => void;
}

const ToastContext = createContext<ToastContextValue>({
  toast: () => {},
});

export function useToast() {
  return useContext(ToastContext);
}

let nextId = 0;

const ICONS: Record<ToastVariant, typeof CheckCircle2> = {
  success: CheckCircle2,
  error: XCircle,
  warning: AlertTriangle,
  info: Info,
};

export function ToastProvider({ children }: { children: ReactNode }) {
  const [items, setItems] = useState<ToastItem[]>([]);

  const toast = useCallback((message: string, variant: ToastVariant = "info") => {
    const id = ++nextId;
    setItems((prev) => [...prev, { id, message, variant }]);
  }, []);

  const handleRemove = useCallback((id: number) => {
    setItems((prev) => prev.filter((item) => item.id !== id));
  }, []);

  return (
    <ToastContext.Provider value={{ toast }}>
      <RadixToast.Provider duration={4000}>
        {children}
        {items.map((item) => {
          const Icon = ICONS[item.variant];
          return (
            <RadixToast.Root
              key={item.id}
              className={`toast toast--${item.variant}`}
              onOpenChange={(open) => !open && handleRemove(item.id)}
            >
              <div className="toast__content">
                <Icon size={16} />
                <RadixToast.Description className="toast__message">
                  {item.message}
                </RadixToast.Description>
              </div>
              <RadixToast.Close asChild>
                <button className="toast__close" aria-label="Dismiss">
                  <X size={14} />
                </button>
              </RadixToast.Close>
            </RadixToast.Root>
          );
        })}
        <RadixToast.Viewport className="toast-viewport" />
      </RadixToast.Provider>
    </ToastContext.Provider>
  );
}
