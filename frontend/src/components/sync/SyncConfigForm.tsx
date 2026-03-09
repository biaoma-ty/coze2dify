import DbConnectionConfig from "../upload/DbConnectionConfig";

export default function SyncConfigForm() {
  return (
    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
      <DbConnectionConfig label="Coze" onTest={(url) => console.log("Test Coze DB:", url)} />
      <DbConnectionConfig label="Dify" onTest={(url) => console.log("Test Dify DB:", url)} />
    </div>
  );
}
