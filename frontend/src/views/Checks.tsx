import { useApp } from '../ctx';
import { KpiGrid } from '../components/Kpi';
import { PageCardsView } from '../components/Card';
import { Rich } from '../components/common';

export default function Checks() {
  const { frame } = useApp();
  const d = frame.data;
  return (
    <>
      <div className="head"><div><h1>Data checks</h1><p className="sub"><Rich r={d.lead} /></p></div><span className="chip">Owner: <b>Data owner</b></span></div>
      <KpiGrid ks={d.kpis} />
      <div className="grid2">
        <section className="panel"><h2>This week’s checks</h2><p className="sec-sub">Counts across the whole extract. “Live” checks raise cards as the replay runs.</p>
          <div className="tbl-wrap"><table><thead><tr><th>Rule</th><th>Check</th><th className="r">Count</th><th>Unit</th><th>Note</th></tr></thead>
            <tbody>{d.rows.map((r: any, i: number) => (
              <tr key={i}><td><span className="rid">{r.rule}</span></td><td>{r.check}</td>
                <td className="r num" style={{ whiteSpace: 'nowrap' }}>{r.count == null ? 'live' : <>
                  <span style={{ display: 'inline-block', verticalAlign: 'middle', width: 60, height: 8, background: 'var(--surface-2)', borderRadius: 4, marginRight: 8, overflow: 'hidden' }} aria-hidden="true">
                    <span style={{ display: 'block', height: 8, background: r.rule === '—' ? 'var(--bar-2)' : 'var(--due)', width: `${(100 * r.frac).toFixed(0)}%` }} /></span>{r.countText}</>}</td>
                <td className="muted">{r.unit}</td><td className="muted">{r.note}</td></tr>
            ))}</tbody></table></div>
          <p className="muted small" style={{ margin: '10px 0 0' }}>Already resolved: inbound times run 8 h behind outbound, a time-zone setting. The twin corrects this automatically.</p>
        </section>
        <div className="stick" style={{ display: 'flex', flexDirection: 'column', gap: 20, minWidth: 0 }}><PageCardsView p={d.cards} /></div>
      </div>
    </>
  );
}
