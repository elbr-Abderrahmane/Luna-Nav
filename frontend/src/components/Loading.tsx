export function Loading({ label = "Calculating..." }: { label?: string }) {
  return (
    <div className="loading" role="status">
      {label}
    </div>
  );
}
