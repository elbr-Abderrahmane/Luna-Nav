import { useEffect, useRef } from "react";

function rng(seed: number) {
  return () => {
    seed = (seed + 0x6d2b79f5) | 0;
    let t = Math.imul(seed ^ (seed >>> 15), 1 | seed);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

/** Static starry background, drawn once per window size. */
export function Starfield() {
  const ref = useRef<HTMLCanvasElement>(null);
  useEffect(() => {
    const c = ref.current;
    if (!c) return;
    const draw = () => {
      const dpr = Math.min(window.devicePixelRatio || 1, 2);
      const w = window.innerWidth;
      const h = window.innerHeight;
      c.width = w * dpr;
      c.height = h * dpr;
      c.style.width = `${w}px`;
      c.style.height = `${h}px`;
      const ctx = c.getContext("2d");
      if (!ctx) return;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      ctx.clearRect(0, 0, w, h);
      const r = rng(11);
      const n = Math.round((w * h) / 3200);
      for (let i = 0; i < n; i++) {
        const x = r() * w;
        const y = r() * h;
        const k = r();
        const size = k > 0.97 ? 1.7 : k > 0.85 ? 1.1 : 0.7;
        const tint = r();
        const rgb = tint < 0.15 ? "255,224,190" : tint < 0.35 ? "190,210,255" : "255,255,255";
        ctx.fillStyle = `rgba(${rgb},${(0.3 + 0.7 * r()).toFixed(2)})`;
        ctx.beginPath();
        ctx.arc(x, y, size, 0, Math.PI * 2);
        ctx.fill();
      }
    };
    draw();
    window.addEventListener("resize", draw);
    return () => window.removeEventListener("resize", draw);
  }, []);
  return <canvas ref={ref} className="starfield" aria-hidden="true" />;
}
