import { useTranslation } from "react-i18next";
import { CheckCircle2, XCircle } from "lucide-react";
import type { NodeConversionResult } from "../../types/ir";

interface VerificationChecklistProps {
  result: NodeConversionResult;
}

export default function VerificationChecklist({ result }: VerificationChecklistProps) {
  const { t } = useTranslation();

  const checks = [
    {
      label: t("diff.nodeDrawer.typeMatched"),
      pass: result.target_node_type !== null,
    },
    {
      label: t("diff.nodeDrawer.nodeEmitted"),
      pass: result.target_node_id !== null,
    },
    {
      label: t("diff.nodeDrawer.noWarnings"),
      pass: result.warnings.length === 0,
    },
    {
      label: t("diff.nodeDrawer.noErrors"),
      pass: result.errors.length === 0,
    },
  ];

  return (
    <div className="verification-list">
      {checks.map((check, i) => (
        <div
          key={i}
          className={`verification-list__item ${check.pass ? "verification-list__item--pass" : "verification-list__item--fail"}`}
        >
          {check.pass ? <CheckCircle2 size={16} /> : <XCircle size={16} />}
          <span>{check.label}</span>
        </div>
      ))}
    </div>
  );
}
