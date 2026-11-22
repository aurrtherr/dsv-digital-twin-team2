import type { KeyboardEvent as ReactKeyboardEvent, PointerEvent as ReactPointerEvent } from 'react';
// Header timeline: past (real data) to the left of "now", projection to the right.
// Drag, click a landmark, or use the keyboard. The backend sends the series and landmarks.
import { useRef, useState } from 'react';
import type { Mode, Timeline as T } from '../types';
import { when } from '../format';

export function Timeline({ tl, at, mode, onSet }: { tl: T; at: number | null; mode: Mode; onSet: (t: number | null) => void }) {
  const { w0, w1, now, hs, fs, lms } = tl;
  const W = 1000;
  const vt = at == null ? now : at;
  const x = (t: number) => ((Math.max(w0, Math.min(w1, t)) - w0) / (w1 - w0)) * W;
  const mx = Math.max(1, ...hs.map(h => h[1]), ...fs.map(f => f[1]));
  const Y = (v: number) => (30 - (26 * Math.min(v, mx)) / mx).toFixed(1);
  const area = 'M0 30 ' + hs.map(([t, v]) => `L${x(t).toFixed(1)} ${Y(v)}`).join(' ') + ` L${x(now).toFixed(1)} 30 Z`;
  const v0 = hs.length ? hs[hs.length - 1][1] : 0;
  const fpts = `L${x(now).toFixed(1)} ${Y(v0)} ` + fs.map(([t, v]) => `L${x(t).toFixed(1)} ${Y(v)}`).join(' ');
  const farea = fs.length ? `M${x(now).toFixed(1)} 30 ${fpts} L${x(w1).toFixed(1)} 30 Z` : '';
  const fline = fs.length ? 'M' + fpts.slice(1) : '';
  const past = mode === 'past', next = mode === 'next';

  const svg = useRef<SVGSVGElement>(null);
  const [drag, setDrag] = useState<number | null>(null); // knob fraction while dragging
  const frac = (e: ReactPointerEvent) => { const r = svg.current!.getBoundingClientRect(); return Math.max(0, Math.min(1, (e.clientX - r.left) / r.width)); };
  const snapTo = (t: number) => { const near = lms.find(([u]) => Math.abs(u - t) <= 45); return near ? near[0] : Math.round(t / 60) * 60; };
  const commit = (t: number) => onSet(t === now ? null : t);
  const knobT = drag != null ? w0 + drag * (w1 - w0) : vt;
  const knobLeft = drag != null ? drag * 100 : (x(vt) / W) * 100;

  const onKey = (e: ReactKeyboardEvent) => {
    const cur = at == null ? now : at, ls = lms.map(l => l[0]);
    let v: number | null = null;
    if (e.key === 'ArrowRight') v = cur + (e.shiftKey ? 360 : 60);
    else if (e.key === 'ArrowLeft') v = cur - (e.shiftKey ? 360 : 60);
    else if (e.key === 'PageDown') v = ls.find(u => u > cur) ?? w1;
    else if (e.key === 'PageUp') v = [...ls].reverse().find(u => u < cur) ?? w0;
    else if (e.key === 'Home') v = w0;
    else if (e.key === 'End') v = w1;
    else if (e.key.toLowerCase() === 'n' || e.key === 'Escape') v = now;
    if (v != null) { e.preventDefault(); commit(Math.max(Math.min(w0, cur), Math.min(w1, v))); }
  };

  return (
    <div className="tl" id="tl">
      <svg ref={svg} viewBox={`0 0 ${W} 40`} preserveAspectRatio="none" tabIndex={0} role="slider"
        aria-label="Time: drag left for the past, right for a projection" aria-valuemin={w0} aria-valuemax={w1} aria-valuenow={vt}
        aria-valuetext={`${when(vt)}, ${past ? 'past, read only' : next ? 'projection' : 'now'}`}
        onKeyDown={onKey}
        onPointerDown={e => { svg.current!.setPointerCapture(e.pointerId); setDrag(frac(e)); }}
        onPointerMove={e => { if (drag != null) setDrag(frac(e)); }}
        onPointerUp={e => { if (drag == null) return; const f = frac(e); setDrag(null); commit(snapTo(w0 + f * (w1 - w0))); }}
        onPointerCancel={() => setDrag(null)}>
        <path d={area} fill="rgba(255,255,255,.13)"><title>Open orders past their planned day, hour by hour</title></path>
        {farea && <>
          <defs><pattern id="tlHatch" width="6" height="6" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><rect width="2.5" height="6" fill="#FFD23F" fillOpacity=".55" /></pattern></defs>
          <path d={farea} fill="url(#tlHatch)"><title>Projected orders past their planned day, from this week’s pace</title></path>
          <path d={fline} fill="none" stroke="var(--gold)" strokeWidth="1.5" strokeDasharray="4 3" vectorEffect="non-scaling-stroke" />
        </>}
        <line x1="0" x2={W} y1="30" y2="30" stroke="rgba(255,255,255,.22)" strokeWidth="4" strokeLinecap="round" />
        <line x1="0" x2={x(now)} y1="30" y2="30" stroke="var(--on-navy-muted)" strokeWidth="4" strokeLinecap="round" />
        <line x1={x(now)} x2={W} y1="30" y2="30" stroke="var(--gold)" strokeWidth="2" strokeDasharray="6 6" />
        <line x1={x(now)} x2={x(now)} y1="2" y2="36" stroke="var(--gold)" strokeWidth="1.5" strokeDasharray="2 3" />
        {past && <line x1={x(vt)} x2={x(now)} y1="30" y2="30" stroke="var(--on-navy)" strokeWidth="4" />}
      </svg>
      <span className={`knob${knobT > now + 30 ? ' next' : ''}`} aria-hidden="true" style={{ left: `${knobLeft.toFixed(2)}%`, transition: drag != null ? 'none' : undefined }} />
      <div className="lms">
        {lms.map(([t, l]) => {
          const xx = x(t);
          return (
            <button key={`${t}${l}`} type="button" className={`lm${t === vt ? ' on' : ''}`} aria-current={t === vt ? 'true' : undefined} onClick={() => commit(t)}
              style={{ left: `${((xx / W) * 100).toFixed(2)}%`, transform: xx > W * 0.96 ? 'translateX(-90%)' : xx < W * 0.04 ? 'translateX(-10%)' : undefined }}>
              <span className="tk" aria-hidden="true" />{l}
            </button>
          );
        })}
      </div>
    </div>
  );
}
