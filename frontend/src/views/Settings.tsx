import { useApp } from '../ctx';

export default function Settings() {
  const { frame, saveCfg, resetCfg } = useApp();
  const d = frame.data;
  return (
    <>
      <div className="head"><div><h1>Settings</h1><p className="sub">Every alert limit in one place. {d.can ? 'You can change them; each change is logged and the cards update at once.' : 'Only the operations manager can change these. You can see what each one does.'}</p></div></div>
      <section className="panel">
        <form key={frame.version} onSubmit={e => {
          e.preventDefault();
          const fd = new FormData(e.currentTarget), v: Record<string, number> = {};
          for (const r of d.rows) v[r.k] = Number(fd.get(r.k));
          saveCfg(v);
        }}>
          <div className="tbl-wrap"><table><thead><tr><th>Limit</th><th>Used by</th><th className="r">Value</th><th>Default</th></tr></thead>
            <tbody>{d.rows.map((r: any) => (
              <tr key={r.k}><td><label htmlFor={`cfg_${r.k}`}>{r.lab}</label></td><td><span className="rid">{r.rule}</span></td>
                <td className="r"><input id={`cfg_${r.k}`} name={r.k} type="number" min={r.min} max={r.max} step={r.step} defaultValue={r.value} disabled={!d.can} style={{ width: 90 }} /> <span className="muted small">{r.unit}</span></td>
                <td className="muted num">{r.def}{r.changed && <> · <b style={{ color: 'var(--due)' }}>changed</b></>}</td></tr>
            ))}</tbody></table></div>
          {d.can && <div className="row" style={{ marginTop: 14, display: 'flex', gap: 10 }}><button className="btn pri" type="submit">Save limits</button><button className="btn" type="button" onClick={resetCfg}>Back to defaults</button></div>}
        </form>
        <p className="muted small" style={{ margin: '12px 0 0' }}>Defaults are our proposals from one week of data (appendix A4–A5). Targets are for DSV to confirm.</p>
      </section>
    </>
  );
}
