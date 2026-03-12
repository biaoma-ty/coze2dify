import type { Dispatch, SetStateAction } from "react";
import { C } from "../theme";
import type { ReviewItem, WorkflowSummary } from "../types";
import Panel from "../components/Panel";
import StatusBadge from "../components/StatusBadge";
import WorkbenchButton from "../components/WorkbenchButton";

interface ReviewViewProps {
  workflow: WorkflowSummary;
  reviewQueue: ReviewItem[];
  setReviewQueue: Dispatch<SetStateAction<ReviewItem[]>>;
}

export default function ReviewView({
  workflow,
  reviewQueue,
  setReviewQueue,
}: ReviewViewProps) {
  const setVerdict = (id: string, verdict: ReviewItem["verdict"]) => {
    setReviewQueue((current) =>
      current.map((item) => (item.id === id ? { ...item, verdict } : item)),
    );
  };

  return (
    <div>
      <h1 style={{ fontSize: 20, fontWeight: 700, margin: "0 0 4px" }}>人工审核</h1>
      <p style={{ margin: "0 0 18px", color: C.tx2, fontSize: 12 }}>
        {workflow.name} · 低相似度判定
      </p>

      {reviewQueue.map((review) => (
        <Panel
          key={review.id}
          style={{
            padding: "14px 16px",
            marginBottom: 10,
            border: !review.verdict ? `1px solid ${C.warn}30` : `1px solid ${C.bd}`,
          }}
        >
          <div
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              marginBottom: 10,
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <span style={{ fontSize: 13, fontWeight: 600 }}>{review.q}</span>
              <StatusBadge tone="warning">{(review.sim * 100).toFixed(0)}%</StatusBadge>
              {review.verdict && (
                <StatusBadge
                  tone={
                    review.verdict === "equivalent"
                      ? "success"
                      : review.verdict === "not_eq"
                        ? "danger"
                        : "warning"
                  }
                >
                  {review.verdict === "equivalent"
                    ? "等价"
                    : review.verdict === "not_eq"
                      ? "不等价"
                      : "可接受"}
                </StatusBadge>
              )}
            </div>
          </div>

          <div
            style={{
              display: "grid",
              gridTemplateColumns: "1fr 1fr",
              gap: 8,
              marginBottom: 10,
            }}
          >
            {[
              { label: "Coze", value: review.cS, color: C.coze },
              { label: "Dify", value: review.dS, color: C.dify },
            ].map((side) => (
              <div
                key={side.label}
                style={{
                  padding: 10,
                  borderRadius: 5,
                  background: C.bg,
                  border: `1px solid ${C.bd}`,
                }}
              >
                <div
                  style={{
                    fontSize: 9,
                    fontWeight: 700,
                    color: side.color,
                    marginBottom: 4,
                    textTransform: "uppercase",
                  }}
                >
                  {side.label}
                </div>
                <div style={{ fontSize: 12 }}>{side.value}</div>
              </div>
            ))}
          </div>

          {!review.verdict && (
            <div style={{ display: "flex", gap: 5, justifyContent: "flex-end" }}>
              <WorkbenchButton
                compact
                type="button"
                variant="success"
                onClick={() => setVerdict(review.id, "equivalent")}
              >
                等价
              </WorkbenchButton>
              <WorkbenchButton
                compact
                type="button"
                onClick={() => setVerdict(review.id, "acceptable")}
              >
                可接受
              </WorkbenchButton>
              <WorkbenchButton
                compact
                type="button"
                variant="danger"
                onClick={() => setVerdict(review.id, "not_eq")}
              >
                不等价
              </WorkbenchButton>
            </div>
          )}
        </Panel>
      ))}
    </div>
  );
}
