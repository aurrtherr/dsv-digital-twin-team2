import { useApp } from '../ctx';
import { KpiGrid } from '../components/Kpi';
import { RuleCard } from '../components/Card';
import { LateChip, Rich } from '../components/common';
import { OrderTable, ProjPanelView } from '../components/OrderTable';

export default function AtRisk() {
  const { frame, set } = useApp();
  const d = frame.data;
  return (
    <>
      <div className="head"><div><h1>Packing priorities</h1><p className="sub"><Rich r={d.lead} /></p></div><div className="chips"><LateChip /></div></div>
      <ProjPanelView p={d.proj} />
      <KpiGrid ks={d.kpis} />
      <div className="grid2">
        <div style={{ display: 'flex', flexDirection: 'column', gap: 20, minWidth: 0 }}>
          <section className="panel"><h2>Unpacked, by country · forwarder</h2><p className="sec-sub">Pack the top lanes first. Pick a lane to see its orders.</p>
            {d.lanes.length ? (
              <div className="tbl-wrap"><table><thead><tr><th>Lane</th><th className="r">Not packed</th><th style={{ minWidth: 150 }}>Packed so far</th>{d.hasLate && <th className="r">Created late</th>}</tr></thead>
                <tbody>{d.lanes.map((g: any) => (
                  <tr key={g.k} style={g.sel ? { background: 'var(--accent-soft)' } : undefined}>
                    <td><button type="button" className="lnk" aria-pressed={g.sel} onClick={() => set({ arSel: g.k })}>{g.lab}</button></td>
                    <td className="r num"><b>{g.n}</b></td>
                    <td><div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      <span style={{ flex: 1, height: 10, background: 'var(--due-soft)', borderRadius: 5, display: 'block', overflow: 'hidden' }} role="img" aria-label={`${g.pk} of ${g.all} packed`}>
                        <span style={{ display: 'block', height: 10, width: `${(100 * g.frac).toFixed(1)}%`, background: 'var(--ok)' }} /></span>
                      <span className="num small">{g.pk}/{g.all}</span></div></td>
                    {d.hasLate && <td className="r num">{g.late ?? ''}</td>}
                  </tr>))}</tbody></table></div>
            ) : <div className="empty">Everything due today is packed. Only pickups are left.</div>}
          </section>
          {d.sel && <section className="panel"><h2>{d.sel.lab} <span className="muted small">({d.sel.n} not packed)</span></h2><OrderTable tb={d.sel.table} /></section>}
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 20, minWidth: 0 }}>
          <section className="panel"><h2>Your suggestion</h2><p className="sec-sub">You propose; the outbound supervisor approves and assigns.</p>
            <div className="cards">{d.cards.length ? d.cards.map((c: any) => <RuleCard key={c.key} c={c} />) : <div className="empty">No packing card right now.</div>}</div></section>
        </div>
      </div>
    </>
  );
}
