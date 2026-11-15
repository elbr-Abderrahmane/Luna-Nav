/** API warnings must be visible on the card (README 3, rule 5). */
export function WarningList({ warnings }: { warnings: string[] | undefined }) {
  if (!warnings || warnings.length === 0) return null;
  return (
    <ul className="banner warn" role="status">
      {warnings.map((w, i) => (
        <li key={i}>{w}</li>
      ))}
    </ul>
  );
}
