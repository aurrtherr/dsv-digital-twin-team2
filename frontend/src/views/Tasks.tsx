import type { ReactNode } from 'react';
import { useApp } from '../ctx';
import { PropItem, TaskItem } from '../components/Card';

function Sec({ h, sub, n, children, empty }: { h: string; sub: string; n: number; children: ReactNode; empty: string }) {
  return <section className="panel"><h2>{h} <span className="muted small">({n})</span></h2><p className="sec-sub">{sub}</p><div className="cards">{n ? children : <div className="empty">{empty}</div>}</div></section>;
}

const HOW: [string, string, string][] = [
  ['1', 'Approve a card', 'A supervisor approves a rule’s card and ticks who does the work.'],
  ['2', 'Each role ticks its part', 'The work happens by phone or in DSV’s systems. Each role marks its own part done; the floor team through its supervisor.'],
  ['3', 'The data closes it', 'The twin checks the next data. When the issue is gone the task closes itself and records whether the action helped.'],
];

export default function Tasks() {
  const { frame, newTask, seed } = useApp();
  const d = frame.data;
  const seg = (n: number, bg: string, l: string) => (n ? <span title={`${l}: ${n}`} style={{ flex: n, background: bg, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff', fontSize: 'var(--fs-xs)', fontWeight: 600, minWidth: 22 }}>{n}</span> : null);
  return (
    <>
      <div className="head"><div><h1>{d.title}</h1><p className="sub">Keep track of everything you are part of. Each role ticks off its own part; the twin checks the next data to confirm the work really happened.</p></div>
        <div className="chips">{d.canAct && <><button className="btn pri" type="button" onClick={newTask}>+ New task</button><button className="btn" type="button" onClick={seed}>Add example tasks</button></>}</div></div>
      {!d.nAll && (
        <section className="panel" style={{ marginBottom: 20 }}><h2>How tasks work</h2>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit,minmax(200px,1fr))', gap: 14, marginTop: 10 }}>
            {HOW.map(([n, h, t]) => <div key={n} style={{ display: 'flex', gap: 12 }}><span className="big" style={{ fontSize: 28, lineHeight: 1, color: 'var(--accent)' }}>{n}</span><div><b>{h}</b><p className="muted small" style={{ margin: '4px 0 0' }}>{t}</p></div></div>)}
          </div>
          <p className="muted small" style={{ margin: '14px 0 0' }}>No tasks yet at {d.hh}. Approve a card on the Operations overview, or use “Add example tasks” to see a filled list.</p>
        </section>
      )}
      {d.glance && (
        <section className="panel" style={{ marginBottom: 20 }}><h2>Your tasks at a glance <span className="muted small">({d.glance.n})</span></h2>
          <div style={{ display: 'flex', height: 26, borderRadius: 6, overflow: 'hidden', gap: 2, marginTop: 6 }} role="img" aria-label={`${d.glance.over} overdue, ${d.glance.open} open, ${d.glance.done} done`}>
            {seg(d.glance.over, 'var(--late)', 'Overdue')}{seg(d.glance.open, 'var(--due)', 'Open')}{seg(d.glance.done, 'var(--ok)', 'Done')}</div>
          <div className="legend" style={{ marginTop: 8 }}><span><i style={{ background: 'var(--late)' }} />Overdue {d.glance.over}</span><span><i style={{ background: 'var(--due)' }} />Open {d.glance.open}</span><span><i style={{ background: 'var(--ok)' }} />Done {d.glance.done}</span></div>
        </section>
      )}
      {d.closed && (
        <section className="panel" style={{ marginBottom: 20 }}><h2>Closed by the data <span className="muted small">({d.closed.n})</span></h2>
          <p className="sec-sub">Tasks close themselves when the data shows the issue is gone. Parts nobody ticked become “no longer needed”.</p>
          <div className="chips"><span className="chip"><b>{d.closed.act}</b> resolved after action</span><span className="chip"><b>{d.closed.self}</b> cleared before anyone acted</span><span className="chip"><b>{d.closed.late}</b> resolved after the due time</span></div>
          {d.closed.self > d.closed.act && <p className="muted small" style={{ margin: '10px 0 0' }}>Most issues cleared on their own: the rule may be firing too early. Review its threshold.</p>}
        </section>
      )}
      <div className="grid2">
        <div style={{ display: 'flex', flexDirection: 'column', gap: 20, minWidth: 0 }}>
          <Sec h="Needs your action" sub="Your part is not ticked yet. Do the work by phone or in the WMS, then mark it done." n={d.toDo.length} empty="Nothing waiting on you.">{d.toDo.map((x: any) => <TaskItem key={x.id} x={x} />)}</Sec>
          <Sec h="Approved by you" sub="Follow up on what you signed off (and is not waiting on you): who has done their part, and what the data shows." n={d.byMe.length} empty="You have not approved any cards yet.">{d.byMe.map((x: any) => <TaskItem key={x.id} x={x} />)}</Sec>
          {d.showProps && <Sec h="Proposed by you" sub="What happened to each proposal: waiting, approved (and its progress), or dismissed with a reason." n={d.props.length} empty="No proposals yet.">{d.props.map((p: any, i: number) => <PropItem key={i} p={p} />)}</Sec>}
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 20, minWidth: 0 }}>
          <Sec h="Also involving you" sub="Tasks you are on, where your part is already done." n={d.assigned.length} empty="None.">{d.assigned.map((x: any) => <TaskItem key={x.id} x={x} />)}</Sec>
          <section className="panel">
            <details className="others" style={{ marginTop: 0, borderTop: 0, paddingTop: 0 }}><summary>All tasks <span className="muted small">({d.nAll})</span></summary>
              <div className="cards" style={{ marginTop: 12 }}>{d.all.length ? d.all.map((x: any) => <TaskItem key={x.id} x={x} />) : <div className="empty">None yet.</div>}</div></details>
            <details className="others" style={{ marginTop: 16 }}><summary>Activity log <span className="muted small">({d.nActivity})</span></summary>
              <p className="sec-sub" style={{ marginTop: 8 }}>Who did what, and when. Nothing is deleted.</p>
              {d.activity.length ? <div className="tbl-wrap"><table><thead><tr><th>When</th><th>Who</th><th>What</th></tr></thead>
                <tbody>{d.activity.map((e: any, i: number) => <tr key={i}><td className="num">{e.when}</td><td>{e.who}</td><td>{e.what}</td></tr>)}</tbody></table></div> : <div className="empty">Nothing yet.</div>}
            </details>
            {d.dismissed.length > 0 && <><h2 style={{ marginTop: 20 }}>Dismissed</h2><div className="cards">{d.dismissed.map((x: any, i: number) => (
              <div className="task" key={i}><div className="t1"><span className="rid">{x.rule}</span><span>{x.head}</span></div><div className="t2">{x.title}</div><div className="muted small">Reason: {x.reason}</div></div>
            ))}</div></>}
          </section>
        </div>
      </div>
    </>
  );
}
