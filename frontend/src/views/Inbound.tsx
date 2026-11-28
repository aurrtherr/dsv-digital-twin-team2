import { useApp } from '../ctx';
import { KpiGrid } from '../components/Kpi';
import { PageCardsView } from '../components/Card';
import { HBarsView, Rich } from '../components/common';
import { LookupForm, ProjPanelView } from '../components/OrderTable';
import { useState } from 'react';

function AsnBtn({ i, asn, hv }: { i: number; asn: string; hv: boolean }) {
  const { openAsn } = useApp();
  return <><button type="button" className="lnk num" onClick={() => openAsn(i)}>{asn}</button>{hv && <> <span className="tag late">High value</span></>}</>;
}

function Row({ r }: { r: any }) {
  const tag = r.st === 'dq' ? <span className="tag wait" title="Sent to the data owner (DQ-03)">Data issue</span> : r.st === 'over' ? <span className="tag late">Over usual</span> : <span className="tag ok">Within</span>;
  const fill = r.st === 'dq' ? 'repeating-linear-gradient(135deg,var(--due) 0 4px,transparent 4px 7px)' : r.st === 'over' ? 'var(--late)' : 'var(--ok)';
  return (
    <tr>
      <td><AsnBtn i={r.i} asn={r.asn} hv={r.hv} /><div className="muted small">{r.ref ? r.ref + ' · ' : ''}docked {r.docked}</div></td>
      <td>{r.type}<div className="muted small">{r.lines} lines</div></td>
      <td className="num" style={{ whiteSpace: 'nowrap', minWidth: 150 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <span style={{ position: 'relative', flex: 1, height: 10, background: 'var(--surface-2)', borderRadius: 5, display: 'block' }} role="img" aria-label={`Waited ${r.waited} h of a usual ${r.usual} h`}>
            <span style={{ position: 'absolute', left: 0, top: 0, bottom: 0, width: `${r.wf.toFixed(1)}%`, borderRadius: 5, background: fill }} />
            <span style={{ position: 'absolute', left: `${r.uf.toFixed(1)}%`, top: -3, bottom: -3, width: 2, background: 'var(--ink)' }} title="Usual time" />
          </span>
          <span><b>{r.waited}</b> / {r.usual} h</span>
        </div>
      </td>
      <td style={{ whiteSpace: 'nowrap' }}>{tag}</td>
    </tr>
  );
}

// I1: receiving-queue bars with a hover box showing the exact count
function QueueChart({ spec }: { spec: any }) {
  const [hov, setHov] = useState<number | null>(null);
  const W = 640, H = 240, L = 40, R = 10, T = 18, B = 42;
  const bw = (W - L - R) / Math.max(spec.rows.length, 1);
  const y = (v: number) => T + (H - T - B) * (1 - v / spec.max);
  const tip = hov === null ? null : spec.rows[hov];
  const tw = 190, th = 42;
  const tx = hov === null ? 0 : Math.min(Math.max(L + hov * bw + bw / 2 - tw / 2, L), W - R - tw);
  const ty = tip ? Math.max(0, y(tip.vals[0]) - th - 6) : 0;
  return (
    <svg viewBox={`0 0 ${W} ${H}`} width="100%" role="img" aria-label={spec.label} style={{ maxHeight: 300 }} onMouseLeave={() => setHov(null)}>
      {spec.grid.map(([g, lab]: [number, string]) => (
        <g key={g}><line x1={L} x2={W - R} y1={y(g)} y2={y(g)} stroke="var(--line)" /><text x={L - 6} y={y(g) + 4} fontSize="12.5" textAnchor="end" fill="var(--muted)">{lab}</text></g>
      ))}
      {spec.rows.map((r: any, k: number) => (
        <g key={k} onMouseEnter={() => setHov(k)}>
          <rect x={L + k * bw} y={T} width={bw} height={H - T - B} fill="transparent" />
          <rect x={L + k * bw + bw * 0.15} y={y(r.vals[0])} width={bw * 0.7} height={Math.max(0, y(0) - y(r.vals[0]))} rx="3"
            fill="var(--bar)" opacity={hov === null || hov === k ? 1 : 0.4} />
          {r.label && <text x={L + k * bw + bw / 2} y={H - B + 16} fontSize="13" textAnchor="middle" fill="var(--muted)">{r.label}</text>}
          {r.sub && <text x={L + k * bw + bw / 2} y={H - B + 31} fontSize="12" textAnchor="middle" fill="var(--muted)">{r.sub}</text>}
        </g>
      ))}
      {tip && (
        <g pointerEvents="none">
          <rect x={tx} y={ty} width={tw} height={th} rx="6" fill="var(--ink)" />
          <text x={tx + 10} y={ty + 17} fontSize="13" fontWeight="700" fill="var(--surface)">{tip.vals[0]} ASNs waiting</text>
          <text x={tx + 10} y={ty + 33} fontSize="12" fill="var(--surface)">{tip.time}</text>
        </g>
      )}
    </svg>
  );
}

export default function Inbound() {
  const { frame } = useApp();
  const d = frame.data;
  return (
    <>
      <div className="head"><div><h1>Inbound</h1><p className="sub"><Rich r={d.lead} /> Open an ASN to compare expected and received per line.</p></div><div className="chips"><LookupForm /></div></div>
      <ProjPanelView p={d.proj} />
      <KpiGrid ks={d.kpis} />
      <div className="grid2">
        <div style={{ display: 'flex', flexDirection: 'column', gap: 20, minWidth: 0 }}>
          <section className="panel"><h2>Waiting at the dock <span className="muted small">({d.rows.length})</span></h2>
            <p className="sec-sub">Most overdue first, against the usual time for that delivery type. Data issues go last.</p>
            {d.rows.length ? (
              <>
                <div className="tbl-wrap"><table><thead><tr><th>ASN</th><th>Type</th><th>Waited vs usual <span className="muted small">(line = usual)</span></th><th>Status</th></tr></thead>
                  <tbody>{d.rows.slice(0, 10).map((r: any) => <Row key={r.i} r={r} />)}</tbody></table></div>
                {d.rows.length > 10 && <details className="others" style={{ marginTop: 12 }}><summary>Show {d.rows.length - 10} more</summary>
                  <div className="tbl-wrap"><table><tbody>{d.rows.slice(10).map((r: any) => <Row key={r.i} r={r} />)}</tbody></table></div></details>}
              </>
            ) : <div className="empty">Nothing waiting at the dock.</div>}
          </section>
          <section className="panel"><h2>Receiving queue, last 24 h <span className="muted small">({d.queueRange})</span></h2>
            <p className="sec-sub">Deliveries docked but not yet received, counted every hour. Rising = work building up; falling = the queue is clearing.</p>
            <QueueChart spec={d.queue} />
          </section>
          <section className="panel"><h2>Received in the last 24 h <span className="muted small">({d.got} deliveries)</span></h2>
            <HBarsView h={d.byType} />
            <p className="muted small" style={{ margin: '8px 0 0' }}>Deliveries by type. Usual time = 90% of this week’s deliveries of that type were received within it. AIFTA’s is inflated by one bad record (DQ-03).</p>
            <details className="others" style={{ marginTop: 14 }}><summary>List the {d.got} deliveries, newest first</summary>
              <div className="tbl-wrap" style={{ marginTop: 8 }}><table><thead><tr><th>ASN</th><th>Shipment ref</th><th>Type</th><th>Docked</th><th>Received</th><th className="r">Lines</th></tr></thead>
                <tbody>{d.list.map((a: any) => <tr key={a.i}><td><AsnBtn i={a.i} asn={a.asn} hv={a.hv} /></td><td className="num">{a.ref}</td><td>{a.type}</td><td className="num">{a.docked}</td><td className="num">{a.received}</td><td className="r num">{a.lines}</td></tr>)}</tbody></table></div></details>
          </section>
        </div>
        <div className="stick" style={{ display: 'flex', flexDirection: 'column', gap: 20, minWidth: 0 }}><PageCardsView p={d.cards} /></div>
      </div>
      <p className="foot-note">{d.foot}</p>
    </>
  );
}
