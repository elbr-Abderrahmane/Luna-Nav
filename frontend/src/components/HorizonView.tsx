import { useEffect, useRef, useState } from "react";
import type { BodyOnSky, Trail } from "../state/useActive";

interface Props {
  /** 360 azimuth bins of the terrain skyline. null = not available (a flat 0 deg line is drawn). */
  profile: { azimuth_deg: number[]; elevation_deg: number[] } | null;
  sun: BodyOnSky | null;
  earth: BodyOnSky | null;
  sunTrail?: Trail | null;
  earthTrail?: Trail | null;
}

// Panorama: azimuth 0-360 left to right (north at both edges), elevation up. Drawing only, no science.
const L = 40;
const R = 12;
const T = 14;
const B = 30;
const YMIN = -8;
const COMPASS = ["N", "NE", "E", "SE", "S", "SW", "W", "NW", "N"];

const niceStep = (range: number, maxTicks: number) => [1, 2, 5, 10, 15, 30].find((s) => range / s <= maxTicks) ?? 30;

export function HorizonView({ profile, sun, earth, sunTrail, earthTrail }: Props) {
  const wrap = useRef<HTMLDivElement>(null);
  const [size, setSize] = useState({ w: 720, h: 300 });
  useEffect(() => {
    const el = wrap.current;
    if (!el) return;
    const ro = new ResizeObserver(([entry]) => {
      const { width, height } = entry.contentRect;
      if (width > 80 && height > 80) setSize({ w: Math.round(width), h: Math.round(height) });
    });
    ro.observe(el);
    return () => ro.disconnect();
  }, []);
  const W = size.w;
  const H = size.h;

  const profileMax = profile && profile.elevation_deg.length ? Math.max(...profile.elevation_deg) : 0;
  const trailMax = Math.max(0, ...(sunTrail?.el ?? []), ...(earthTrail?.el ?? []));
  const top = Math.max(profileMax, sun?.el ?? 0, earth?.el ?? 0, trailMax);
  const ymax = Math.min(90, Math.max(12, Math.ceil(top + 3)));

  const x = (az: number) => L + (az / 360) * (W - L - R);
  const y = (el: number) => {
    const c = Math.min(ymax, Math.max(YMIN, el));
    return H - B - ((c - YMIN) / (ymax - YMIN)) * (H - B - T);
  };

  let line = "";
  if (profile && profile.azimuth_deg.length) {
    profile.azimuth_deg.forEach((a, i) => {
      line += `${i ? "L" : "M"}${x(a).toFixed(1)} ${y(profile.elevation_deg[i]).toFixed(1)}`;
    });
    line += `L${x(360).toFixed(1)} ${y(profile.elevation_deg[0]).toFixed(1)}`;
  } else {
    line = `M${x(0)} ${y(0)}L${x(360)} ${y(0)}`;
  }
  const area = `${line}L${x(360)} ${H - B}L${x(0)} ${H - B}Z`;

  const trailPath = (t?: Trail | null) =>
    t ? t.az.map((a, i) => (t.el[i] >= YMIN ? `M${x(a).toFixed(1)} ${y(t.el[i]).toFixed(1)}h0` : "")).join("") : "";

  const step = niceStep(ymax, Math.max(3, Math.floor((H - B - T) / 38)));
  const yTicks: number[] = [];
  for (let v = 0; v <= ymax; v += step) yTicks.push(v);

  const label = (b: BodyOnSky, name: string, cls: string, r: number, color: string) => {
    const cx = x(b.az);
    const cy = y(b.el);
    const lx = Math.min(W - R - 40, Math.max(L + 40, cx));
    const above = cy > T + 26;
    return (
      <g opacity={b.up ? 1 : 0.4}>
        <circle cx={cx} cy={cy} r={r * 2} style={{ fill: color }} opacity={0.22} />
        <circle cx={cx} cy={cy} r={r} style={{ fill: color }} />
        <text x={lx} y={above ? cy - r * 2 - 4 : cy + r * 2 + 12} textAnchor="middle" className={cls}>
          {b.up ? name : `${name} (below horizon)`}
        </text>
      </g>
    );
  };

  const summary = `Horizon view. ${sun ? `Sun at azimuth ${sun.az.toFixed(0)} degrees, elevation ${sun.el.toFixed(1)} degrees. ` : ""}${earth ? `Earth at azimuth ${earth.az.toFixed(0)} degrees, elevation ${earth.el.toFixed(1)} degrees.` : ""}`;

  return (
    <div className="sky-wrap" ref={wrap}>
      <svg className="sky" width={W} height={H} viewBox={`0 0 ${W} ${H}`} role="img" aria-label={summary}>
        <defs>
          <linearGradient id="sky-grad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0" stopColor="#070b1a" />
            <stop offset="1" stopColor="#16203f" />
          </linearGradient>
          <linearGradient id="terrain-grad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0" stopColor="#3a3f4d" />
            <stop offset="1" stopColor="#14171f" />
          </linearGradient>
        </defs>
        <rect x={L} y={T} width={W - L - R} height={H - B - T} fill="url(#sky-grad)" />
        {yTicks.map((v) => (
          <g key={v}>
            <line x1={L} x2={W - R} y1={y(v)} y2={y(v)} stroke="rgba(190,210,255,0.12)" strokeDasharray={v === 0 ? "5 4" : undefined} />
            <text x={L - 6} y={y(v) + 4} textAnchor="end">{`${v}`}</text>
          </g>
        ))}
        {COMPASS.map((c, i) => (
          <g key={i}>
            <line x1={x(i * 45)} x2={x(i * 45)} y1={H - B} y2={H - B + 4} stroke="rgba(190,210,255,0.4)" />
            <text x={x(i * 45)} y={H - B + 16} textAnchor="middle">{c}</text>
          </g>
        ))}
        <path d={trailPath(sunTrail)} style={{ stroke: "var(--sun)" }} strokeWidth={2} strokeLinecap="round" opacity={0.3} fill="none" />
        <path d={trailPath(earthTrail)} style={{ stroke: "var(--earth)" }} strokeWidth={2} strokeLinecap="round" opacity={0.3} fill="none" />
        <path d={area} fill="url(#terrain-grad)" />
        <path d={line} fill="none" stroke="rgba(214,224,245,0.8)" strokeWidth={1.2} />
        {earth && label(earth, "Earth", "lbl-earth", 6.5, "#5aa8ff")}
        {sun && label(sun, "Sun", "lbl-sun", 8, "#ffcf6b")}
        {H >= 260 && <text x={W - R} y={T + 12} textAnchor="end">elevation (deg), azimuth from north</text>}
      </svg>
    </div>
  );
}
