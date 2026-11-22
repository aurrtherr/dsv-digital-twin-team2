import { useState, useEffect } from 'react';
import { useApp } from '../ctx';
import { KpiCard } from '../components/Kpi';

const COLS = ['var(--bar-2)', 'var(--accent)', 'var(--due)', 'var(--ok)'];

export default function Trace() {
  const { frame, trace } = useApp();
  const d = frame.data, cv = d.coverage, r = d.result;
  const [q, setQ] = useState(d.q);
  useEffect(() => setQ(d.q), [d.q]);
  return (
    <>
      <div className="head"><div><h1>Milkrun trace</h1><p className="sub"><b>Follow one carton from the dock to the forwarder.</b> Milkrun is the one flow where inbound and outbound share an ID: the inbound LPN is the outbound carton ID. Search a carton ID, an ASN, an order key or an LP.</p></div></div>
      <div className="kpis big">
        <div className="kpi s-ok"><div className="khead"><span className="lab">Cartons traceable end to end</span><span className="stat ok">✓ Exact link</span></div>
          <div className="krow kwide"><span className="val">{cv.nM}</span><div className="kside"><div className="cmp">{cv.pctText}% of {cv.nC} Milkrun cartons · 15.9% of all outbound cartons</div>
            <div className="def">Only Milkrun shares an ID between the reports (DSV A2); the unmatched ones were received before the extract starts.</div></div></div>
          <div className="pchart">
            <div style={{ display: 'flex', height: 22, borderRadius: 6, overflow: 'hidden', gap: 2 }} role="img" aria-label={`Of ${cv.tot} outbound cartons: ${cv.nM} traceable, ${cv.miss} Milkrun without a match, ${cv.other} other flows`}>
              {cv.segs.map((s: any, i: number) => <span key={i} title={`${s[2]}: ${s[0].toLocaleString('en-US')}`} style={{ flex: s[0], background: s[1], minWidth: 3 }} />)}
            </div>
            <div className="legend" style={{ marginTop: 8 }}>
              <span><i style={{ background: 'var(--ok)' }} />Traceable <b className="num" style={{ color: 'var(--ink)' }}>{cv.nM}</b></span>
              <span><i style={{ background: 'var(--due)' }} />Milkrun, no match <b className="num" style={{ color: 'var(--ink)' }}>{cv.miss}</b></span>
              <span><i style={{ background: 'var(--bar-2)' }} />Other flows <b className="num" style={{ color: 'var(--ink)' }}>{cv.other}</b></span>
            </div>
            <p className="muted small" style={{ margin: '6px 0 0' }}>All {cv.tot} outbound cartons this week.</p>
          </div>
        </div>
        <KpiCard k={d.kpi} />
      </div>
      <section className="panel">
        <form className="search" onSubmit={e => { e.preventDefault(); trace(q.trim()); }}>
          <input value={q} onChange={e => setQ(e.target.value)} placeholder="e.g. 0000031762" aria-label="Carton, ASN, order or LP" />
          <button className="btn pri" type="submit">Trace</button>
        </form>
        <div className="chips" style={{ marginTop: 10 }}><span className="muted small">Try:</span>
          {d.examples.map(([l, v]: [string, string]) => <button key={v} type="button" className="btn sm" onClick={() => trace(v)}>{l} {v}</button>)}</div>
        {d.noHit && <div className="empty" style={{ marginTop: 12 }}>No Milkrun-from-ABC carton matches that value.</div>}
        {r && (
          <>
            <p className="muted small" style={{ margin: '12px 0 0' }}>{r.summary}</p>
            {r.time && (
              <div style={{ margin: '14px 0 6px' }}>
                <div className="muted small" style={{ marginBottom: 6 }}>Where the time went: {r.time.total} from dock to forwarder</div>
                <div style={{ display: 'flex', height: 16, borderRadius: 6, overflow: 'hidden', gap: 2 }} role="img" aria-label={r.time.parts.map((x: any) => `${x.lab} ${x.dur}`).join(', ')}>
                  {r.time.parts.map((x: any, k: number) => <span key={k} title={`${x.lab}: ${x.dur}`} style={{ flex: x.w, background: COLS[k], minWidth: 3 }} />)}
                </div>
                <div className="legend" style={{ marginTop: 8 }}>{r.time.parts.map((x: any, k: number) => <span key={k}><i style={{ background: COLS[k] }} />{x.lab} <b className="num" style={{ color: 'var(--ink)' }}>{x.dur}</b></span>)}</div>
              </div>
            )}
            <div className="steps">{r.steps.map((s: any, k: number) => (
              <div key={k} className={`step ${s.st}`}><div className="dot" /><div className="sl">{s.lab}</div><div className="sv">{s.val}</div><div className="sd">{s.sub}</div></div>
            ))}</div>
            <div className="tbl-wrap" style={{ marginTop: 18 }}><table>
              <thead><tr><th>Carton ID</th><th>ASN</th><th>Order</th><th>Received</th><th>Cyclone</th><th>Handed over</th></tr></thead>
              <tbody>{r.rows.map((c: any) => <tr key={c.carton}><td className="num">{c.carton}</td><td className="num">{c.asn}</td><td className="num">{c.order}</td><td className="num">{c.received}</td><td className="num">{c.cyclone}</td><td className="num">{c.handed ?? <span className="muted">not yet</span>}</td></tr>)}</tbody>
            </table></div>
            {r.more && <p className="muted small">{r.more}</p>}
          </>
        )}
      </section>
    </>
  );
}
