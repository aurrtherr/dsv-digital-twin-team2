import type { OrderTable as T, ProjPanel } from '../types';
import { useApp } from '../ctx';
import { HBarsView, Rich } from './common';

const stateTag = (st: string) => (st === 'Past planned day' ? 'late' : st === 'Due today' ? 'wait' : '');

export function OrderTable({ tb }: { tb: T }) {
  const { openOrder } = useApp();
  return (
    <>
      <div className="tbl-wrap"><table>
        <thead><tr><th>Order</th>{!tb.hideC && <th>Country</th>}{!tb.hideF && <th>Forwarder</th>}<th>Planned</th><th>Status</th><th>Packed</th><th className="r">Lines</th><th className="r">Cartons</th></tr></thead>
        <tbody>
          {tb.rows.map(o => (
            <tr key={o.i}>
              <td><button type="button" className="lnk num" onClick={() => openOrder(o.i)}>{o.key}</button></td>
              {!tb.hideC && <td>{o.country}</td>}{!tb.hideF && <td>{o.fwd}</td>}
              <td>{o.planned}</td><td><span className={`tag ${stateTag(o.state)}`}>{o.state}</span></td>
              <td>{o.packed ? '✓ ' + o.packed : <span className="muted">not yet</span>}</td>
              <td className="r num">{o.lines}</td><td className="r num">{o.cartons}</td>
            </tr>
          ))}
        </tbody>
      </table></div>
      {tb.more && <p className="muted small" style={{ margin: '8px 0 0' }}>{tb.more}</p>}
    </>
  );
}

export function LookupForm() {
  const { lookup } = useApp();
  return (
    <form className="search" style={{ maxWidth: 420 }} onSubmit={e => { e.preventDefault(); const q = (new FormData(e.currentTarget).get('q') as string || '').trim(); if (q) lookup(q); }}>
      <input name="q" placeholder="Order key or ASN" aria-label="Open an order or ASN" /><button className="btn" type="submit">Open</button>
    </form>
  );
}

export function ProjPanelView({ p }: { p: ProjPanel | null }) {
  if (!p) return null;
  return (
    <section className="panel" style={{ marginBottom: 20, border: '1.5px dashed var(--due)' }}>
      <h2>Projection to {p.at} <span className="tag wait" style={{ marginLeft: 6 }}>Projection</span></h2>
      {p.kind === 'inbound' ? (
        p.rows && p.rows.length ? (
          <div className="tbl-wrap"><table><thead><tr><th>ASN</th><th>Type</th><th>Docked</th><th>Passes usual time</th></tr></thead>
            <tbody>{p.rows.map((r, i) => <tr key={i}><td className="num">{r.asn}</td><td>{r.type}</td><td className="num">{r.docked}</td><td className="num"><b>{r.passes}</b></td></tr>)}</tbody></table></div>
        ) : <div className="empty">No delivery now at the dock passes its usual time before {p.at}.</div>
      ) : (
        <>
          <div className="chips" style={{ marginBottom: 10 }}>{(p.chips || []).map((c, i) => <span className="chip" key={i}><Rich r={c} /></span>)}</div>
          {p.lanes && p.lanes.length > 0 && (
            <>
              <p className="sec-sub">Groups that join the overdue list at midnight if not picked up:</p>
              <HBarsView h={{ kind: 'hbars', cls: '', rows: p.lanes.map(([nm, n]) => ({ nm, n, nText: n.toLocaleString('en-US'), frac: n / Math.max(1, ...p.lanes!.map(l => l[1])) })) }} />
            </>
          )}
        </>
      )}
    </section>
  );
}
