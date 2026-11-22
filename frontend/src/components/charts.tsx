import type { CSSProperties, ReactNode } from 'react';
// Charts. The backend sends the numbers; this file only turns them into SVG.
import type { BarsSpec, DayChart, DockChart, OnTimeChart, ProjChart, WeekBars } from '../types';
import { fmt, hhmm, when } from '../format';

const colOf = (st: string) => (st === 'act' ? 'var(--late)' : st === 'watch' ? 'var(--due)' : st === 'ok' ? 'var(--ok)' : 'var(--accent)');

const Lab = ({ x, W, children, al }: { x: number; W: number; children: ReactNode; al?: string }) => (
  <span style={{ position: 'absolute', left: `${((100 * x) / W).toFixed(1)}%`, transform: `translateX(${al || '-50%'})`, whiteSpace: 'nowrap' }}>{children}</span>
);

export function DayChartView({ c }: { c: DayChart }) {
  const W = 600, H = 120, x = (u: number) => ((u - c.t0) / (c.t1 - c.t0)) * W;
  const mx = Math.max(1, ...c.today.map(p => p[1]), ...c.base.map(p => p[1]), ...c.after.map(p => p[1])) * 1.12;
  const y = (v: number) => H - 6 - ((H - 14) * v) / mx;
  const path = (pts: [number, number][]) => pts.map(([u, v], i) => `${i ? 'L' : 'M'}${x(u).toFixed(1)} ${y(v).toFixed(1)}`).join(' ');
  const col = colOf(c.st);
  const xt = x(c.t);
  return (
    <>
      <svg viewBox={`0 0 ${W} ${H}`} preserveAspectRatio="none" width="100%" height={H} role="img" aria-label={c.aria}>
        <line x1="0" x2={W} y1={H - 6} y2={H - 6} stroke="var(--line)" />
        {c.base.length > 0 && <path d={path(c.base)} fill="none" stroke="var(--muted)" strokeWidth="1.5" strokeDasharray="4 4" vectorEffect="non-scaling-stroke" />}
        <path d={`${path(c.today)} L${xt.toFixed(1)} ${H - 6} L${x(c.today[0][0]).toFixed(1)} ${H - 6} Z`} fill={col} fillOpacity=".12" />
        <path d={path(c.today)} fill="none" stroke={col} strokeWidth="2.2" vectorEffect="non-scaling-stroke" />
        {c.after.length > 0 && (
          <path d={`M${xt.toFixed(1)} ${y(c.val).toFixed(1)} ${path(c.after).replace(/^M/, 'L')}`} fill="none" stroke="var(--muted)" strokeWidth="2" strokeDasharray="1 3" vectorEffect="non-scaling-stroke" />
        )}
        <line x1={xt} x2={xt} y1="0" y2={H - 6} stroke="var(--ink)" strokeDasharray="2 3" vectorEffect="non-scaling-stroke" />
      </svg>
      <div className="plabs">
        <Lab x={x(c.t0)} W={W} al="0">{c.t0Lab}</Lab>
        <Lab x={xt} W={W} al={xt > W * 0.85 ? '-100%' : '-50%'}><b>{c.nowLab}</b></Lab>
        {xt < W * 0.85 && <Lab x={x(c.t1)} W={W} al="-100%">{c.t1Lab}</Lab>}
      </div>
      <div className="legend" style={{ marginTop: 4 }}>
        <span><i style={{ background: col }} />Today</span>
        {c.base.length > 0 && <span><i style={{ background: 'var(--muted)' }} />Usual this week, same hour (dashed)</span>}
        {c.after.length > 0 && <span><i style={{ background: 'var(--muted)' }} />What happened next (dotted)</span>}
      </div>
    </>
  );
}

export function WeekBarsView({ c }: { c: WeekBars }) {
  const H = 110;
  return (
    <>
      <div style={{ position: 'relative', height: H, display: 'flex', alignItems: 'flex-end', gap: 10, borderBottom: '1px solid var(--line)' }} role="img" aria-label={c.aria}>
        {c.refFrac != null && <span style={{ position: 'absolute', left: 0, right: 0, bottom: `${(100 * c.refFrac).toFixed(1)}%`, borderTop: '2px dashed var(--ink)', opacity: 0.55 }} />}
        {c.bars.map((b, k) => (
          <div key={k} style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'flex-end', height: '100%' }}>
            <span className="num small" style={{ fontWeight: b.current ? 700 : 400 }}>{b.valText}</span>
            <span style={{ width: '70%', height: `${(100 * b.frac).toFixed(1)}%`, borderRadius: '4px 4px 0 0', background: c.info ? 'var(--accent)' : b.good ? 'var(--ok)' : 'var(--late)', opacity: b.current ? 1 : 0.45 }} />
          </div>
        ))}
      </div>
      <div style={{ display: 'flex', gap: 10, marginTop: 4 }}>
        {c.bars.map((b, k) => <span key={k} className="small muted" style={{ flex: 1, textAlign: 'center', fontWeight: b.current ? 700 : 400 }}>{b.label}</span>)}
      </div>
      <div className="legend" style={{ marginTop: 4 }}>
        <span><i style={{ background: 'var(--ink)', opacity: 0.55 }} />{c.refLab} (dashed)</span>
        {!c.info && <span><i style={{ background: 'var(--late)' }} />{c.badLab}</span>}
      </div>
    </>
  );
}

export function ProjChartView({ c }: { c: ProjChart }) {
  const W = 600, H = 130, { hist, proj, t0, t1, now } = c, marks = c.marks || [];
  const x = (t: number) => ((t - t0) / (t1 - t0)) * W;
  const mx = Math.max(1, ...hist.map(h => h[1]), ...proj.map(p => p[3])) * 1.1;
  const y = (v: number) => H - 6 - ((H - 14) * v) / mx;
  const hp = hist.map(([t, v], i) => `${i ? 'L' : 'M'}${x(t).toFixed(1)} ${y(v).toFixed(1)}`).join(' ');
  const ha = hp + ` L${x(now).toFixed(1)} ${H - 6} L${x(hist[0][0]).toFixed(1)} ${H - 6} Z`;
  const last = hist[hist.length - 1];
  const band = proj.length ? `M${x(now).toFixed(1)} ${y(last[1]).toFixed(1)} ` + proj.map(p => `L${x(p[0]).toFixed(1)} ${y(p[3]).toFixed(1)}`).join(' ') + ' ' + proj.slice().reverse().map(p => `L${x(p[0]).toFixed(1)} ${y(p[2]).toFixed(1)}`).join(' ') + ' Z' : '';
  const mid = proj.length ? `M${x(now).toFixed(1)} ${y(last[1]).toFixed(1)} ` + proj.map(p => `L${x(p[0]).toFixed(1)} ${y(p[1]).toFixed(1)}`).join(' ') : '';
  const endP = proj[proj.length - 1];
  const al = (t: number, a: 'left' | 'right' | 'center') => (a === 'left' ? '0' : a === 'right' ? '-100%' : '-50%');
  const mk = marks.filter(([t]) => t > t0 && t < t1);
  const pid = `pjh${Math.round(t0)}${Math.round(t1)}`;
  return (
    <>
      {mk.length > 0 && <div className="plabs">{mk.map(([t, l], k) => <Lab key={k} x={x(t)} W={W} al={al(t, x(t) > W * 0.85 ? 'right' : 'center')}><span style={{ color: 'var(--late)' }}>{l}</span></Lab>)}</div>}
      <svg viewBox={`0 0 ${W} ${H}`} preserveAspectRatio="none" width="100%" height={H} role="img"
        aria-label={`History until now, then the projection${endP ? `: about ${fmt(endP[1])} (${fmt(endP[2])}–${fmt(endP[3])}) at ${when(endP[0])}` : ''}`}>
        <defs><pattern id={pid} width="6" height="6" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><rect width="2.5" height="6" fill="var(--due)" fillOpacity=".35" /></pattern></defs>
        <line x1="0" x2={W} y1={H - 6} y2={H - 6} stroke="var(--line)" />
        <path d={ha} fill="var(--accent-soft)" />
        <path d={hp} fill="none" stroke="var(--accent)" strokeWidth="2" vectorEffect="non-scaling-stroke" />
        {band && <><path d={band} fill={`url(#${pid})`} /><path d={mid} fill="none" stroke="var(--due)" strokeWidth="2" strokeDasharray="5 4" vectorEffect="non-scaling-stroke" /></>}
        <line x1={x(now)} x2={x(now)} y1="0" y2={H - 6} stroke="var(--ink)" strokeDasharray="2 3" vectorEffect="non-scaling-stroke" />
        {marks.map(([t], k) => (t > t0 && t < t1 ? <line key={k} x1={x(t)} x2={x(t)} y1="0" y2={H - 6} stroke="var(--late)" strokeDasharray="4 3" vectorEffect="non-scaling-stroke" /> : null))}
      </svg>
      <div className="plabs">
        <Lab x={x(t0)} W={W} al="0">{hhmm(t0)}</Lab>
        <Lab x={x(now)} W={W} al={x(now) > W * 0.85 ? '-100%' : '-50%'}><b>Now</b> {fmt(last[1])}</Lab>
        {endP && <Lab x={x(t1)} W={W} al="-100%"><b style={{ color: 'var(--due)' }}>{fmt(endP[1])}</b></Lab>}
      </div>
      <div className="legend" style={{ marginTop: 4 }}>
        <span><i style={{ background: 'var(--accent)' }} />So far</span>
        {proj.length > 0 && <span><i style={{ background: 'var(--due)' }} />Projection, hatched = range</span>}
      </div>
    </>
  );
}

export function OnTimeBar({ o }: { o: OnTimeChart }) {
  const tg = o.target;
  const hatch = 'repeating-linear-gradient(135deg,var(--due) 0 3px,transparent 3px 7px)';
  const seg = (a: number, b: number, bg: string, extra: CSSProperties = {}) => (
    <span style={{ position: 'absolute', top: 0, bottom: 0, left: `${a.toFixed(1)}%`, width: `${Math.max(0, b - a).toFixed(1)}%`, background: bg, ...extra }} />
  );
  return (
    <>
      <div style={{ position: 'relative', height: 26, borderRadius: 6, background: 'var(--surface-2)', overflow: 'hidden', marginTop: 6 }} role="img"
        aria-label={`${o.doneText}% already left on time; projected ${o.midText}%; target ${tg}%`}>
        {seg(0, o.done, 'var(--ok)')}
        {o.mid != null && o.mn != null && o.mx != null ? <>{seg(o.done, o.mn, 'var(--ok-soft)')}{seg(o.mn, o.mx, hatch, { opacity: 0.6 })}</> : seg(o.done, 100, hatch, { opacity: 0.4 })}
        {o.mid != null && <span style={{ position: 'absolute', top: 0, bottom: 0, left: `${o.mid.toFixed(1)}%`, width: 3, background: 'var(--due)' }} />}
        <span style={{ position: 'absolute', top: -2, bottom: -2, left: `${tg}%`, width: 2, background: 'var(--ink)' }} />
      </div>
      <div className="plabs" style={{ marginTop: 4 }}>
        <span style={{ position: 'absolute', left: 0 }}>0%</span>
        <span style={{ position: 'absolute', left: `${tg}%`, transform: 'translateX(-50%)' }}>Target {tg}%</span>
        <span style={{ position: 'absolute', right: 0 }}>100%</span>
      </div>
      <div className="legend" style={{ marginTop: 4 }}>
        <span><i style={{ background: 'var(--ok)' }} />Left on time so far ({o.doneText}%)</span>
        <span><i style={{ background: 'var(--due)' }} />Projected range</span>
      </div>
    </>
  );
}

export function DockStrip({ d }: { d: DockChart }) {
  return (
    <>
      <div style={{ position: 'relative', height: 44, marginTop: 8 }}>
        <span style={{ position: 'absolute', left: 0, right: 0, top: 20, height: 4, borderRadius: 2, background: 'repeating-linear-gradient(90deg,var(--due) 0 6px,transparent 6px 10px)' }} />
        {d.points.map((p, k) => (
          <span key={k} title={`${p.asn} at ${p.atHH}`} style={{ position: 'absolute', left: `${p.left.toFixed(1)}%`, top: 14, width: 16, height: 16, marginLeft: -8, borderRadius: '50%', background: 'var(--late)', border: '2px solid var(--surface)' }} />
        ))}
      </div>
      <div className="plabs"><span style={{ position: 'absolute', left: 0 }}><b>Now</b> {d.nowLab}</span><span style={{ position: 'absolute', right: 0 }}>{d.endLab}</span></div>
      {d.points.length > 0 && (
        <div className="olist" style={{ marginTop: 10 }}>
          {d.points.slice(0, 4).map((p, k) => <div className="orow" key={k}><span className="num">{p.asn}</span><span className="muted small">{p.type}</span><span style={{ marginLeft: 'auto' }}><b>{p.atHH}</b></span></div>)}
        </div>
      )}
    </>
  );
}

// Grouped bar chart (Trends, What-if)
export function SvgBars({ spec }: { spec: BarsSpec }) {
  const W = 640, H = 240, L = 40, R = 10, T = 18, B = 42, n = spec.rows.length, bw = (W - L - R) / Math.max(n, 1);
  const max = spec.max;
  const y = (v: number) => T + (H - T - B) * (1 - v / max);
  return (
    <>
      {spec.ref != null && (
        <div className="legend" style={{ marginBottom: 4 }}>
          <span><svg width="22" height="8" aria-hidden="true" style={{ verticalAlign: 1, marginRight: 6 }}><line x1="0" x2="22" y1="4" y2="4" stroke="var(--ink)" strokeDasharray="4 3" /></svg>{spec.refLabel}</span>
        </div>
      )}
      <svg viewBox={`0 0 ${W} ${H}`} width="100%" role="img" aria-label={spec.label} style={{ maxHeight: 300 }}>
        {spec.grid.map(([g, lab]) => (
          <g key={g}><line x1={L} x2={W - R} y1={y(g)} y2={y(g)} stroke="var(--line)" /><text x={L - 6} y={y(g) + 4} fontSize="12.5" textAnchor="end" fill="var(--muted)">{lab}</text></g>
        ))}
        {spec.rows.map((r, k) => {
          const k0 = r.vals.length, gw = (bw * 0.7) / k0;
          return (
            <g key={k}>
              {r.vals.map((v, j) => {
                const x = L + k * bw + bw * 0.15 + j * gw;
                const inside = y(0) - y(v) > 24;
                return (
                  <g key={j}>
                    <rect x={x + 1} y={y(v)} width={gw - 2} height={Math.max(0, y(0) - y(v))} rx="3" fill={r.faint ? 'var(--bar-2)' : r.colors[j]}><title>{`${r.label}: ${r.tips[j]}`}</title></rect>
                    {r.valLabels && <text x={x + gw / 2} y={inside ? y(v) + 17 : y(v) - 5} fontSize="12.5" fontWeight="600" textAnchor="middle" fill={inside && !r.faint ? '#fff' : 'var(--ink)'}>{r.valLabels[j]}</text>}
                  </g>
                );
              })}
              {r.hl && <rect x={L + k * bw + bw * 0.08} y={T - 4} width={bw * 0.84} height={H - B - T + 8} rx="6" fill="none" stroke="var(--ink)" strokeDasharray="3 3" />}
              <text x={L + k * bw + bw / 2} y={H - B + 16} fontSize="13" textAnchor="middle" fill="var(--muted)">{r.label}</text>
              {r.sub && <text x={L + k * bw + bw / 2} y={H - B + 31} fontSize="12" textAnchor="middle" fill="var(--muted)">{r.sub}</text>}
            </g>
          );
        })}
        {spec.ref != null && <line x1={L} x2={W - R} y1={y(spec.ref)} y2={y(spec.ref)} stroke="var(--ink)" strokeDasharray="4 4" />}
      </svg>
    </>
  );
}
