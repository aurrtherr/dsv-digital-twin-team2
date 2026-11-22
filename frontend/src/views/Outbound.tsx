import { useApp } from '../ctx';
import { KpiGrid } from '../components/Kpi';
import { PageCardsView } from '../components/Card';
import { HBarsView, LateChip, Rich } from '../components/common';
import { LookupForm, OrderTable, ProjPanelView } from '../components/OrderTable';

export default function Outbound() {
  const { frame, set, ui } = useApp();
  const d = frame.data;
  const tabs: [string, string][] = [['lane', 'Country · forwarder'], ['fwd', 'Forwarder'], ['ctry', 'Country']];
  return (
    <>
      <div className="head"><div><h1>Outbound</h1><p className="sub"><Rich r={d.lead} /> Open any order to see its lines and cartons.</p></div>
        <div className="chips"><LateChip /><LookupForm /></div></div>
      <ProjPanelView p={d.proj} />
      <KpiGrid ks={d.kpis} />
      <div className="grid2">
        <div style={{ display: 'flex', flexDirection: 'column', gap: 20, minWidth: 0 }}>
          <section className="panel"><h2>{d.total} open orders at {d.hh}</h2>
            <div style={{ display: 'flex', height: 22, borderRadius: 6, overflow: 'hidden', gap: 2 }}>
              {d.seg.map((x: any, i: number) => (x[1] ? <span key={i} title={`${x[0]}: ${x[3]}`} style={{ flex: x[1], background: x[2] }} /> : null))}
            </div>
            <div className="legend" style={{ marginTop: 10 }}>{d.seg.map((x: any, i: number) => <span key={i}><i style={{ background: x[2] }} />{x[0]} <b className="num" style={{ color: 'var(--ink)' }}>{x[3]}</b></span>)}</div>
          </section>
          <section className="panel"><h2>How long the overdue orders have waited</h2><p className="sec-sub"><Rich r={d.age.sub} /></p><HBarsView h={d.age.bars} /></section>
          <section className="panel">
            <div className="head" style={{ alignItems: 'center', marginBottom: 6 }}><h2 style={{ margin: 0 }}>Where the overdue orders sit</h2>
              <div className="chips" role="group" aria-label="Group by">
                {tabs.map(([k, l]) => <button key={k} type="button" className={`btn sm${d.by === k ? ' pri' : ''}`} aria-pressed={d.by === k} onClick={() => set({ obBy: k, obSel: null })}>{l}</button>)}
              </div></div>
            <p className="sec-sub">Sorted by orders past their planned day. Pick a row to see its orders.</p>
            <div className="tbl-wrap"><table>
              <thead><tr><th>{d.groupHead}</th><th style={{ width: '34%' }}>Past planned day</th><th className="r">Due today</th><th className="r">Not packed</th></tr></thead>
              <tbody>{d.rows.map((r: any) => (
                <tr key={r.k} style={r.sel ? { background: 'var(--accent-soft)' } : undefined}>
                  <td><button type="button" className="lnk" aria-pressed={r.sel} onClick={() => set({ obSel: r.k, obCap: 15 })}>{r.lab}</button>{r.tk && <> <span className="tag info">{r.tk} task open</span></>}</td>
                  <td><div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <span className="track" style={{ flex: 1, height: 8, background: 'var(--surface-2)', borderRadius: 4, display: 'block' }}><span style={{ display: 'block', height: 8, borderRadius: 4, width: `${(100 * r.frac).toFixed(1)}%`, background: 'var(--late)' }} /></span>
                    <b className="num" style={{ minWidth: 42, textAlign: 'right' }}>{r.pastText}</b></div></td>
                  <td className="r num">{r.due ?? <span className="muted">–</span>}</td>
                  <td className="r num">{r.np ? <b style={{ color: 'var(--due)' }}>{r.np}</b> : <span className="muted">–</span>}</td>
                </tr>))}</tbody>
            </table></div>
            <p className="muted small" style={{ margin: '10px 0 0' }}>{d.groupsNote}</p>
          </section>
          {d.sel && (
            <section className="panel"><h2>{d.sel.lab} <span className="muted small">({d.sel.open} open)</span></h2><p className="sec-sub">Order → lines → cartons: open an order key.</p>
              <OrderTable tb={d.sel.table} />
              {d.sel.moreBtn && <button type="button" className="btn sm" style={{ marginTop: 10 }} onClick={() => set({ obCap: ui.obCap > 15 ? 15 : 60 })}>Show {d.sel.moreBtn}</button>}
            </section>
          )}
        </div>
        <div className="stick" style={{ display: 'flex', flexDirection: 'column', gap: 20, minWidth: 0 }}><PageCardsView p={d.cards} /></div>
      </div>
      <p className="foot-note">{d.foot}</p>
    </>
  );
}
