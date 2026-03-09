export default function DirectWriteButton({ conversionId }: { conversionId: string }) {
  const handleWrite = async () => {
    // TODO: call /convert/{id}/write-to-dify
    alert("Direct write to Dify DB not yet implemented");
  };

  return (
    <button className="btn btn-secondary" onClick={handleWrite}>
      🗄 Write to Dify DB
    </button>
  );
}
