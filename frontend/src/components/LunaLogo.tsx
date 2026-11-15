export function LunaLogo({ size = 34, className = "" }: { size?: number; className?: string }) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 64 64"
      width={size}
      height={size}
      fill="none"
      className={className}
      aria-hidden="true"
      style={{ flexShrink: 0, filter: "drop-shadow(0 0 10px rgba(51, 240, 213, 0.28))" }}
    >
      <defs>
        <radialGradient id="lunaBgGlow" cx="50%" cy="50%" r="55%">
          <stop offset="0%" stopColor="#0f2342" />
          <stop offset="100%" stopColor="#040711" />
        </radialGradient>
        <linearGradient id="lunaMoonSurface" x1="16" y1="12" x2="48" y2="52" gradientUnits="userSpaceOnUse">
          <stop offset="0%" stopColor="#f4f8ff" />
          <stop offset="55%" stopColor="#b8cce8" />
          <stop offset="100%" stopColor="#526b94" />
        </linearGradient>
        <linearGradient id="lunaOrbitCyan" x1="6" y1="44" x2="58" y2="20" gradientUnits="userSpaceOnUse">
          <stop offset="0%" stopColor="#33f0d5" stopOpacity="0.15" />
          <stop offset="50%" stopColor="#33f0d5" stopOpacity="0.95" />
          <stop offset="100%" stopColor="#5aa8ff" stopOpacity="0.9" />
        </linearGradient>
      </defs>

      <rect x="2" y="2" width="60" height="60" rx="16" fill="url(#lunaBgGlow)" stroke="#33f0d5" strokeWidth="2" strokeOpacity="0.55" />
      <path d="M 10 38 A 25 10 0 0 1 54 26" stroke="url(#lunaOrbitCyan)" strokeWidth="2" strokeDasharray="3 3" transform="rotate(-22 32 32)" />
      <circle cx="46" cy="17" r="4.5" fill="#ffd166" />
      <circle cx="46" cy="17" r="8" fill="#ffd166" fillOpacity="0.22" />
      <circle cx="31" cy="33" r="16" fill="url(#lunaMoonSurface)" />
      <path d="M 31 17 A 16 16 0 0 0 31 49 A 10.5 16 0 0 1 31 17 Z" fill="#081124" fillOpacity="0.72" />
      <circle cx="36" cy="27" r="2.6" fill="#7d95ba" fillOpacity="0.55" />
      <circle cx="40" cy="35" r="1.8" fill="#7d95ba" fillOpacity="0.5" />
      <circle cx="33" cy="39" r="3.1" fill="#6b83a8" fillOpacity="0.5" />
      <path d="M 54 26 A 25 10 0 0 1 10 38" stroke="url(#lunaOrbitCyan)" strokeWidth="2.5" strokeLinecap="round" transform="rotate(-22 32 32)" />
      <circle cx="31" cy="49" r="6.5" fill="#33f0d5" fillOpacity="0.28" />
      <circle cx="31" cy="49" r="3.4" fill="#33f0d5" stroke="#040711" strokeWidth="1.4" />
    </svg>
  );
}
