import { useEffect, useRef, useState } from 'react';
import { useApp } from '../ctx';
import { api } from '../api';
import { Rich } from '../components/common';
import { SvgBars } from '../components/charts';

export default function WhatIf() {
  const { frame, ui, set } = useApp();
  const [d, setD] = useState<any>(frame.data);
  const [wi, setWi] = useState<number>(ui.wi);
  const tm = useRef<number | undefined>(undefined);
  useEffect(() => { setD(frame.data); }, [frame.data]);
  // Recalculate on the backend as the slider moves (short debounce), remember the value in the UI state.
  const change = (v: number) => {
    v = Math.max(-30, Math.min(60, Math.round(v || 0)));
    setWi(v);
    window.clearTimeout(tm.current);
    tm.current = window.setTimeout(() => { api.whatif(v).then(setD).catch(() => {}); set({ wi: v }); }, 120);
  };
  return (
    <>
      <div className="head"><div><h1>What-if: volume vs people</h1><p className="sub">If volume changes, how many people would the warehouse need, with each person handling the same work as today?</p></div>
        <span className="chip">Today: <b>20 people</b></span></div>
      <div className="wi">
        <section className="panel"><h2>Volume change</h2>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <input type="range" min={-30} max={60} step={5} value={wi} list="wiTicks" aria-label="Volume change in percent" style={{ flex: 1 }} onChange={e => change(+e.target.value)} />
            <input type="number" min={-30} max={60} step={5} value={wi} aria-label="Volume change, percent" style={{ width: 76 }} onChange={e => change(+e.target.value)} /> <span className="muted">%</span>
          </div>
          <datalist id="wiTicks"><option value="-30" /><option value="0" /><option value="30" /><option value="60" /></datalist>
          <div className="muted small" style={{ display: 'flex', justifyContent: 'space-between', margin: '4px 88px 0 0' }}><span>−30%</span><span>0</span><span>+30%</span><span>+60%</span></div>
          <div className="chips" style={{ marginTop: 10 }}>
            {[10, 20, 50].map(v => <button key={v} type="button" className="btn sm" onClick={() => change(v)}>+{v}%</button>)}
            <button type="button" className="btn sm" onClick={() => change(0)}>Reset</button>
          </div>
          <div>
            <p style={{ fontSize: 'var(--fs-md)', lineHeight: 1.45, margin: '4px 0 16px' }}><Rich r={d.sentence} /></p>
            <div style={{ display: 'flex', gap: 28, flexWrap: 'wrap' }}>
              <div><div className="muted small">Typical weekday</div><div className="big">{d.typical.n}</div><div className="muted small">{d.typical.range}</div></div>
              <div><div className="muted small">{d.busiest.lab}</div><div className="big">{d.busiest.n}</div><div className="muted small">{d.busiest.range}</div></div>
            </div>
            <dl className="kv" style={{ marginTop: 18 }}><dt>Average load</dt><dd className="num">{d.avgLoad}</dd><dt>Productivity</dt><dd className="num">{d.prod}</dd><dt>Range</dt><dd>if productivity is 10% better or worse</dd></dl>
          </div>
        </section>
        <section className="panel"><h2>People needed each day</h2><p className="sec-sub">Amber = more than today’s 20. Weekend bars are faint: far less work.</p>
          <SvgBars spec={d.chart} />
          <details className="others" style={{ marginTop: 10 }}><summary>View as table</summary>
            <div className="tbl-wrap" style={{ marginTop: 8 }}><table><thead><tr><th>Day</th><th className="r">Lines today</th><th className="r">{d.linesHead}</th><th className="r">People</th><th className="r">vs 20</th></tr></thead>
              <tbody>{d.table.map((r: any) => <tr key={r.day}><td>{r.day}</td><td className="r num">{r.lines}</td><td className="r num">{r.linesX}</td><td className="r num"><b>{r.people}</b></td><td className="r num" style={{ color: r.over ? 'var(--due)' : 'inherit' }}>{r.delta}</td></tr>)}</tbody></table></div></details>
        </section>
      </div>
      <section className="panel"><h2>How it is worked out</h2><p className="muted" style={{ margin: 0 }}>People needed = lines that day × (1 + change) ÷ lines per person, rounded up. Lines per person comes from this week: average lines a day ÷ 20 people. Two of our assumptions, to confirm with DSV: the 20 people cover inbound and outbound together, and each person handles the same number of lines however busy it gets. A prototype on one week of data.</p></section>
    </>
  );
}
