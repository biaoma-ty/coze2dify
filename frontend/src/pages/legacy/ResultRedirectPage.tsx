import { Navigate, useParams } from "@umijs/max";

export default function ResultRedirectPage() {
  const { conversionId } = useParams<{ conversionId: string }>();

  return <Navigate replace to={`/migrate/result/${conversionId || ""}`} />;
}
