/** Full-width tab switch with a highlight that slides to the chosen option. */
export function Seg<T extends string>({ label, value, options, onChange }: {
  label: string;
  value: T;
  options: { value: T; label: string }[];
  onChange: (v: T) => void;
}) {
  const i = Math.max(0, options.findIndex((o) => o.value === value));
  return (
    <div className="seg fill" role="group" aria-label={label} style={{ "--n": options.length, "--i": i } as React.CSSProperties}>
      <span className="seg-thumb" aria-hidden="true" />
      {options.map((o) => (
        <button key={o.value} aria-pressed={o.value === value} onClick={() => onChange(o.value)}>
          {o.label}
        </button>
      ))}
    </div>
  );
}
