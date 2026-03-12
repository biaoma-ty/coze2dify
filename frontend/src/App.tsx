import { BrowserRouter, useLocation } from "react-router-dom";
import { AppRoutes } from "./routes";
import Header from "./components/layout/Header";
import { ToastProvider } from "./components/common/Toast";

export default function App() {
  return (
    <BrowserRouter>
      <ToastProvider>
        <AppFrame />
      </ToastProvider>
    </BrowserRouter>
  );
}

function AppFrame() {
  const location = useLocation();
  const isWorkbench = location.pathname.startsWith("/workbench");

  if (isWorkbench) {
    return <AppRoutes />;
  }

  return (
    <div style={{ minHeight: "100vh", display: "flex", flexDirection: "column" }}>
      <Header />
      <main
        style={{
          flex: 1,
          maxWidth: 1280,
          width: "100%",
          margin: "0 auto",
          padding: "32px 24px",
        }}
      >
        <AppRoutes />
      </main>
    </div>
  );
}
