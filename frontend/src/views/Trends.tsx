import { useApp } from '../ctx';
import { PageCardsView } from '../components/Card';
import { HBarsView, LateChip, Rich } from '../components/common';
import { SvgBars } from '../components/charts';

export default function Trends() {
  const { frame, set, ui } = useApp();
  const d = frame.data, a = d.accuracy;
  return (
    <>
      <div className="head"><div><h1>Trends</h1><p className="sub"><Rich r={d.sub} /></p></div>
        <div className="chips"><LateChip /><button type="button" className="btn sm" aria-pressed={ui.trWk} onClick={() => set({ trWk: !ui.trWk })}>{ui.trWk ? 'Hide' : 'Show'} weekend</button></div></div>
      <div className="kpis">{d.stats.map((s: any, i: number) => (
        <div key={i} className={`kpi s-${s.st}`}><div className="khead"><span className="lab">{s.lab}</span>{s.st !== 'info' && <span className={`stat ${s.st}`}>{s.icon} {s.word}</span>}</div>
          <div className="krow"><span className="val">{s.val}</span></div><div className="def">{s.foot}</div></div>
      ))}</div>
      <section className="panel" style={{ marginBottom: 20 }}><h2>How good were the projections?</h2>
        <p className="sec-sub">Each weekday at 09:00 the twin projects how many orders will be past their planned day at midnight, using only what it knew at 09:00. Here is what then happened.
          {a.scored > 0 && <> <b>{a.hits} of {a.scored}</b> landed inside the projected range.</>}</p>
        {a.rows.length ? (
          <div className="tbl-wrap"><table><thead><tr><th>Day</th><th className="r">Projected at 09:00</th><th className="r">Range</th><th className="r">Actual at midnight</th><th>Result</th></tr></thead>
            <tbody>{a.rows.map((r: any, i: number) => (
              <tr key={i}><td>{r.day}</td><td className="r num">{r.midText}</td><td className="r num">{r.rangeText}</td><td className="r num"><b>{r.actText}</b></td>
                <td>{r.mid == null ? <span className="muted small">First day: no earlier pace, worst case only</span> : r.ok ? <span className="tag ok">Inside range</span> : <span className="tag wait">Outside · off by {r.errText}</span>}</td></tr>
            ))}</tbody></table></div>
        ) : <div className="empty">Projections can be checked once the first midnight has passed.</div>}
        {a.lesson && <p style={{ margin: '10px 0 0', fontSize: 'var(--fs-sm)' }}><b>What this tells us:</b> one week of pace is not enough. Days differ a lot because pickups are lumpy: whole forwarder groups leave at once (313 HK orders with FORWARDER 013 in one go). DSV’s pickup schedule would explain most of the gap; it is on our data request.</p>}
        <p className="muted small" style={{ margin: '10px 0 0' }}>Early actions taken in Prevent: <b>{a.early}</b>{a.early > 0 && <> · {a.avoided} cleared before the rule would have fired</>}. A simple pace-based projection (Stage 1.5); a forecasting model needs 4–8 weeks of data (Stage 2).</p>
      </section>
      <div className="grid2">
        <section className="panel"><h2>Late rate by planned day</h2><SvgBars spec={d.lateChart} /><p className="muted small" style={{ margin: '6px 0 0' }}>{d.lateNote}</p></section>
        <section className="panel"><h2>Forwarders with the most late orders</h2><p className="sec-sub">Orders planned 17–23 Aug. A ranking, not a cause (MGR-02).</p>
          <HBarsView h={d.fwdBars} /><p className="muted small" style={{ margin: '8px 0 0' }}>Bar = late orders; % = share of that forwarder’s orders that left late.</p></section>
      </div>
      <div className="grid2" style={{ marginTop: 20 }}>
        <section className="panel"><h2>Workload per day</h2><p className="sec-sub">Outbound peaks early in the week at about twice inbound. The replay day is outlined.</p>
          <div className="legend" style={{ marginBottom: 6 }}><span><i style={{ background: 'var(--bar-2)' }} />Inbound lines received</span><span><i style={{ background: 'var(--bar)' }} />Outbound order lines handed over</span></div>
          <SvgBars spec={d.workChart} /><p className="muted small" style={{ margin: '6px 0 0' }}>Inbound lines are counted on the day they were received; outbound lines on the day they were handed over.</p></section>
        <div className="stick" style={{ display: 'flex', flexDirection: 'column', gap: 20, minWidth: 0 }}><PageCardsView p={d.cards} /></div>
      </div>
    </>
  );
}
