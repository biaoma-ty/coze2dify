import type { SyncDeletePolicy } from "../../types/sync";

export default function DeletePolicyNotice({
  title,
  policy,
}: {
  title: string;
  policy: SyncDeletePolicy;
}) {
  const tone = policy.supported ? "alert--info" : "alert--warning";

  return (
    <div className={`alert ${tone}`}>
      <strong>{title}</strong>
      <div style={{ marginTop: 6 }}>
        {policy.label} • {policy.summary}
      </div>
      <div style={{ marginTop: 6, fontSize: "0.78rem" }}>
        Rollback: {policy.rollback_requirement}
      </div>
      <div style={{ marginTop: 4, fontSize: "0.78rem" }}>
        Approval: {policy.approval_requirement}
      </div>
      {policy.intent_status ? (
        <div style={{ marginTop: 4, fontSize: "0.78rem", fontFamily: "var(--font-mono)" }}>
          Intent status: {policy.intent_status}
        </div>
      ) : null}
    </div>
  );
}
