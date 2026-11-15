import { useEffect, useRef } from "react";

interface Star { x: number; y: number; r: number; a: number; ph: number; tw: number; v: number; rgb: string }
interface Comet { x: number; y: number; vx: number; vy: number; len: number }

function rng(seed: number) {
  return () => {
    seed = (seed + 0x6d2b79f5) | 0;
    let t = Math.imul(seed ^ (seed >>> 15), 1 | seed);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

/** Drifting, twinkling stars plus an occasional comet. Static when the system asks for reduced motion. */
export function Starfield() {
  const ref = useRef<HTMLCanvasElement>(null);
  useEffect(() => {
    const c = ref.current;
    const ctx = c?.getContext("2d");
    if (!c || !ctx) return;
    const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const rand = rng(11);
    let w = 0, h = 0, stars: Star[] = [];
    const comets: Comet[] = [];
    let raf = 0, last = 0, untilComet = 1800;

    const build = () => {
      const dpr = Math.min(window.devicePixelRatio || 1, 2);
      w = window.innerWidth; h = window.innerHeight;
      c.width = w * dpr; c.height = h * dpr; c.style.width = `${w}px`; c.style.height = `${h}px`;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      const n = Math.round((w * h) / 3000);
      stars = Array.from({ length: n }, () => {
        const k = rand(), t = rand();
        const layer = k > 0.97 ? 2 : k > 0.85 ? 1 : 0;
        return {
          x: rand() * w, y: rand() * h, r: [0.7, 1.1, 1.7][layer], a: 0.3 + 0.7 * rand(),
          ph: rand() * 6.28, tw: 0.6 + rand() * 1.8, v: [2, 5, 9][layer],
          rgb: t < 0.15 ? "255,224,190" : t < 0.35 ? "190,210,255" : "255,255,255",
        };
      });
    };

    const spawnComet = () => {
      const deg = 28 + Math.random() * 24, rad = (deg * Math.PI) / 180, speed = 650 + Math.random() * 350;
      comets.push({ x: w * (0.35 + 0.7 * Math.random()), y: -30, vx: -Math.cos(rad) * speed, vy: Math.sin(rad) * speed, len: 110 + Math.random() * 90 });
    };

    const draw = (time: number, dt: number) => {
      ctx.clearRect(0, 0, w, h);
      for (const s of stars) {
        s.x -= s.v * dt;
        if (s.x < -3) s.x = w + 3;
        const a = s.a * (0.72 + 0.28 * Math.sin(time * s.tw + s.ph));
        ctx.fillStyle = `rgba(${s.rgb},${a.toFixed(2)})`;
        ctx.beginPath(); ctx.arc(s.x, s.y, s.r, 0, 6.2832); ctx.fill();
      }
      for (let i = comets.length - 1; i >= 0; i--) {
        const k = comets[i];
        k.x += k.vx * dt; k.y += k.vy * dt;
        if (k.x < -k.len * 2 || k.y > h + k.len * 2) { comets.splice(i, 1); continue; }
        const sp = Math.hypot(k.vx, k.vy), tx = k.x - (k.vx / sp) * k.len, ty = k.y - (k.vy / sp) * k.len;
        const g = ctx.createLinearGradient(k.x, k.y, tx, ty);
        g.addColorStop(0, "rgba(255,255,255,0.9)"); g.addColorStop(1, "rgba(110,170,255,0)");
        ctx.strokeStyle = g; ctx.lineWidth = 2; ctx.lineCap = "round";
        ctx.beginPath(); ctx.moveTo(k.x, k.y); ctx.lineTo(tx, ty); ctx.stroke();
        ctx.fillStyle = "rgba(255,255,255,0.95)";
        ctx.beginPath(); ctx.arc(k.x, k.y, 2.2, 0, 6.2832); ctx.fill();
      }
    };

    const frame = (ts: number) => {
      const dt = Math.min(0.05, (ts - last) / 1000); last = ts;
      untilComet -= dt * 1000;
      if (untilComet <= 0) { spawnComet(); untilComet = 5000 + Math.random() * 7000; }
      draw(ts / 1000, dt);
      raf = requestAnimationFrame(frame);
    };
    const start = () => { if (reduce || raf) return; last = performance.now(); raf = requestAnimationFrame(frame); };
    const stop = () => { cancelAnimationFrame(raf); raf = 0; };
    const onResize = () => { build(); if (reduce) draw(0, 0); };
    const onVisibility = () => (document.hidden ? stop() : start());

    build();
    if (reduce) draw(0, 0); else start();
    window.addEventListener("resize", onResize);
    document.addEventListener("visibilitychange", onVisibility);
    return () => { stop(); window.removeEventListener("resize", onResize); document.removeEventListener("visibilitychange", onVisibility); };
  }, []);
  return <canvas ref={ref} className="starfield" aria-hidden="true" />;
}
