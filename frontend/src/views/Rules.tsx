import { Fragment } from 'react';
import { useApp } from '../ctx';
import { Rich } from '../components/common';

export default function Rules() {
  const { frame, go } = useApp();
  const d = frame.data;
  return (
    <>
      <div className="head"><div><h1>Rules</h1><p className="sub"><Rich r={d.lead} /></p></div>
        <div className="chips"><button type="button" className="btn" onClick={() => go('settings')}>Open Settings →</button></div></div>
      <section className="panel"><h2>All rules</h2>
        <div className="tbl-wrap"><table><thead><tr><th>Rule</th><th>When this happens</th><th>Limit</th><th>In this prototype</th><th className="r">Cards now</th></tr></thead>
          <tbody>{d.groups.map((g: any) => (
            <Fragment key={g.lab}>
              <tr><td colSpan={5} style={{ background: 'var(--surface-2)', fontWeight: 600, fontSize: 'var(--fs-sm)', letterSpacing: '.02em' }}>{g.lab}</td></tr>
              {g.rules.map((r: any) => (
                <tr key={r.id}><td><span className="rid">{r.id}</span></td><td>{r.name}</td><td className="num muted">{r.lim}</td>
                  <td>{r.live ? <span className="tag ok">Live</span> : <span className="muted small">{r.note}</span>}</td>
                  <td className="r num">{r.now ? <b>{r.now}</b> : <span className="muted">–</span>}</td></tr>
              ))}
            </Fragment>
          ))}</tbody></table></div>
      </section>
      <section className="panel" style={{ marginTop: 20 }}><h2>KPI definitions</h2><p className="sec-sub">One definition per KPI, used the same way on every screen.</p>
        <div className="tbl-wrap"><table><thead><tr><th>KPI</th><th>Definition</th><th>Watched by</th><th>Target or baseline</th></tr></thead>
          <tbody>{d.kpiReg.map((k: string[]) => <tr key={k[0]}><td><b>{k[0]}</b></td><td>{k[1]}</td><td className="muted">{k[2]}</td><td>{k[3]}</td></tr>)}</tbody></table></div>
      </section>
    </>
  );
}
