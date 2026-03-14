import { Navigate, useParams } from "@umijs/max";

export default function DiffRedirectPage() {
  const { conversionId } = useParams<{ conversionId: string }>();

  return <Navigate replace to={`/migrate/diff/${conversionId || ""}`} />;
}
