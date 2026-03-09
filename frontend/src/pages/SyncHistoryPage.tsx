import { useEffect, useState } from "react";
import { listConversionHistory } from "../api/conversion";
import ConversionHistoryTable from "../components/history/ConversionHistoryTable";
import type { ConversionHistoryItem } from "../types/ir";

const PAGE_SIZE = 10;

export default function SyncHistoryPage() {
  const [items, setItems] = useState<ConversionHistoryItem[]>([]);
  const [total, setTotal] = useState(0);
  const [offset, setOffset] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [reloadKey, setReloadKey] = useState(0);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);

    listConversionHistory({ limit: PAGE_SIZE, offset })
      .then((response) => {
        if (cancelled) {
          return;
        }
        setItems(response.items);
        setTotal(response.total);
      })
      .catch((e: any) => {
        if (cancelled) {
          return;
        }
        setError(e?.response?.data?.detail || e?.message || "Failed to load conversion history");
      })
      .finally(() => {
        if (!cancelled) {
          setLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [offset, reloadKey]);

  const start = total === 0 ? 0 : offset + 1;
  const end = Math.min(offset + items.length, total);
  const writtenCount = items.filter((item) => item.write_result?.app_id).length;
  const reviewCount = items.filter((item) => !item.write_result?.app_id).length;

  return (
    <div className="fade-in">
      <div className="page-header">
        <h1 className="page-title">Conversion History</h1>
        <p className="page-description">
          Review persisted conversions, reopen diff and result views, and check whether each workflow was written into Dify
        </p>
      </div>

      {loading && items.length === 0 ? (
        <div className="empty-state card" style={{ borderStyle: "dashed" }}>
          <div className="empty-state__icon">⏳</div>
          <p className="empty-state__text">Loading conversion history...</p>
        </div>
      ) : null}

      {!loading && error && items.length === 0 ? (
        <div className="card" style={{ padding: 24, display: "grid", gap: 14 }}>
          <div className="alert alert--error">{error}</div>
          <div>
            <button className="btn btn-secondary" onClick={() => setReloadKey((value) => value + 1)}>
              Retry
            </button>
          </div>
        </div>
      ) : null}

      {!loading && !error && items.length === 0 ? (
        <div className="empty-state card" style={{ borderStyle: "dashed" }}>
          <div className="empty-state__icon">📋</div>
          <p className="empty-state__text">No persisted conversions yet</p>
          <p style={{ fontSize: "0.8rem", color: "var(--c-text-tertiary)", marginTop: 4 }}>
            Run a conversion from upload, Coze API, or Coze DB to populate this history.
          </p>
        </div>
      ) : null}

      {items.length > 0 ? (
        <>
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
              gap: 16,
              marginBottom: 20,
            }}
          >
            <div className="stat-card stat-card--accent">
              <div className="stat-card__value">{total}</div>
              <div className="stat-card__label">Persisted conversions</div>
            </div>
            <div className="stat-card stat-card--green">
              <div className="stat-card__value">{writtenCount}</div>
              <div className="stat-card__label">Written on this page</div>
            </div>
            <div className="stat-card stat-card--blue">
              <div className="stat-card__value">{reviewCount}</div>
              <div className="stat-card__label">Awaiting Dify write</div>
            </div>
          </div>

          {error ? (
            <div className="alert alert--error" style={{ marginBottom: 20 }}>
              {error}
            </div>
          ) : null}

          <ConversionHistoryTable items={items} />

          <div
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              gap: 12,
              marginTop: 16,
            }}
          >
            <div style={{ fontSize: "0.82rem", color: "var(--c-text-tertiary)" }}>
              Showing {start}-{end} of {total}
            </div>

            <div style={{ display: "flex", gap: 10 }}>
              <button className="btn btn-ghost" onClick={() => setOffset(Math.max(0, offset - PAGE_SIZE))} disabled={offset === 0 || loading}>
                ← Previous
              </button>
              <button
                className="btn btn-secondary"
                onClick={() => setOffset(offset + PAGE_SIZE)}
                disabled={loading || offset + PAGE_SIZE >= total}
              >
                Next →
              </button>
            </div>
          </div>
        </>
      ) : null}
    </div>
  );
}
