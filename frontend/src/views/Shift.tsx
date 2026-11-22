import type { ReactNode } from 'react';
import { Fragment } from 'react';
import { useApp } from '../ctx';
import { KpiGrid, KpiLegend, ProjKpisView } from '../components/Kpi';
import { OtherList, PropItem, RuleCard, TaskItem } from '../components/Card';
import { HBarsView, LateChip } from '../components/common';
import type { Card } from '../types';

function Recs({ r }: { r: any }) {
  const { jump } = useApp();
  if (r.kind === 'next') return (
    <>
      <p className="sec-sub">Coming up before {r.atWhen} if nothing changes. Act on them in Now.</p>
      <div className="cards">{r.cards.length ? r.cards.map((c: Card) => <RuleCard key={c.key} c={c} />) : <div className="empty">Nothing predictable fires for you before {r.atHH}.</div>}</div>
    </>
  );
  if (r.kind === 'empty') return (
    <div className="cards"><div className="empty-card">
      <p><b>Nothing needs your decision at {r.hh}.</b> Your KPIs above are what to watch.</p>
      {r.next && <><p>Next card for you: <span className="rid">{r.next.rule}</span> {r.next.title} at <b>{r.next.when}</b>.</p>
        <button type="button" className="btn" onClick={() => jump(r.next.t)}>Jump to {r.next.when}</button></>}
    </div></div>
  );
  return (
    <>
      {r.tiers.map((tr: any) => {
        const body = (
          <>
            <div className="cards">{tr.shown.map((c: Card) => <RuleCard key={c.key} c={c} />)}</div>
            {tr.rest.length > 0 && <details className="others" style={{ marginTop: 10 }}><summary>Show {tr.rest.length} more</summary>
              <div className="cards" style={{ marginTop: 10 }}>{tr.rest.map((c: Card) => <RuleCard key={c.key} c={c} />)}</div></details>}
          </>
        );
        return tr.open ? (
          <Fragment key={tr.k}><h3 className="tier-h">{tr.name} <span className="muted small">({tr.n})</span> <span className="tsub">· {tr.sub}</span></h3>{body}</Fragment>
        ) : (
          <details key={tr.k} className="others" style={{ marginTop: 14 }}><summary>{tr.name} <span className="muted small">({tr.n}) · {tr.sub}</span></summary><div style={{ marginTop: 10 }}>{body}</div></details>
        );
      })}
    </>
  );
}

export function LookFirst({ lf }: { lf: any }) {
  const b = lf.body;
  let body: ReactNode;
  if (b.kind === 'empty') body = <div className="empty">{b.text}</div>;
  else if (b.kind === 'hbars') body = <HBarsView h={b} />;
  else if (b.kind === 'dock') body = (
    <>
      {b.rows.map((r: any, i: number) => (
        <div className="hbar" key={i}><span className="nm" title={r.nm}>{r.nm}</span>
          <span className="track"><span className={`fill ${r.over ? '' : 'acc'}`} style={{ width: `${(100 * r.frac).toFixed(1)}%`, display: 'block' }} /></span>
          <span className="n num">{r.hText} h</span></div>
      ))}
      <p className="muted small" style={{ margin: '8px 0 0' }}>Red = over the usual time for that type; bar is scaled to 1.5× the usual time.</p>
    </>
  );
  else body = b.rows.map((r: any, i: number) => (
    <div className="hbar" key={i}><span className="nm" title={r.nm}>{r.nm} <span className="muted small">{r.sub}</span></span>
      <span className="track"><span className={`fill ${r.red ? '' : 'acc'}`} style={{ width: `${(100 * r.frac).toFixed(1)}%`, display: 'block' }} /></span>
      <span className="n num">{r.vText}</span></div>
  ));
  return <section className="panel"><h2>{lf.h}</h2><p className="muted small" style={{ margin: '-6px 0 10px' }}>{lf.sub}</p>{body}</section>;
}

export default function Shift() {
  const { frame, go, ui, set, newTask, canAct } = useApp();
  const d = frame.data;
  const f = d.follow;
  return (
    <>
      <div className="head"><div><h1>{d.title}</h1><p className="sub">{d.intro}</p></div>
        <div className="chips">{d.lateChip && <LateChip />}<button type="button" className="btn" onClick={() => go(d.start.view)}>{d.start.label} →</button></div></div>
      {d.proj ? <ProjKpisView p={d.proj} /> : <><KpiGrid ks={d.kpis} /><KpiLegend ontime={frame.cfg.ontime} /></>}
      {d.hindsight && (
        <section className="panel" style={{ margin: '16px 0 20px' }}><h2>What happened next</h2><p className="sec-sub">{d.hindsight.sub}</p>
          <div className="chips">
            <span className="chip"><b>{d.hindsight.approved}</b> acted on</span><span className="chip"><b>{d.hindsight.dismissed}</b> dismissed</span>
            <span className="chip"><b>{d.hindsight.self}</b> cleared on their own</span><span className="chip"><b>{d.hindsight.open}</b> not acted on, still open</span>
            <span className="chip">{d.hindsight.pastThen} orders were past their planned day then; <b>{d.hindsight.gone}</b> have left since</span>
          </div></section>
      )}
      <div className="grid2">
        <section className="panel"><h2>Recommendations for you <span className="muted small">({d.nMine})</span></h2>
          <Recs r={d.recs} />
          {d.others.length > 0 && (
            <details className="others" open={ui.othersOpen} onToggle={e => set({ othersOpen: (e.currentTarget as HTMLDetailsElement).open })}>
              <summary>Other roles’ cards <span className="muted small">(view only, {d.others.length})</span></summary>
              <OtherList rows={d.others} full />
            </details>
          )}
        </section>
        <div className="stick" style={{ display: 'flex', flexDirection: 'column', gap: 20, minWidth: 0 }}>
          <LookFirst lf={d.lookFirst} />
          <section className="panel">
            <div className="head" style={{ alignItems: 'center', marginBottom: 12 }}><h2 style={{ margin: 0 }}>My follow-ups</h2>
              {canAct && <button type="button" className="btn sm" onClick={newTask}>+ New task</button>}</div>
            <p className="sec-sub">Tasks you must do, tasks you approved, and what you proposed.</p>
            <div className="fu">
              <button type="button" onClick={() => go('tasks')}><div className="fn">{f.toDo}</div><div className="fl">My parts to do</div></button>
              <button type="button" onClick={() => go('tasks')}><div className="fn">{f.byMe}</div><div className="fl">Approved by me, open</div></button>
              <button type="button" onClick={() => go('tasks')}><div className="fn">{f.waitProps}</div><div className="fl">My proposals waiting</div></button>
            </div>
            <div className="cards">
              {f.list.kind === 'tasks' ? f.list.items.map((x: any) => <TaskItem key={x.id} x={x} />)
                : f.list.kind === 'props' ? f.list.items.map((p: any, i: number) => <PropItem key={i} p={p} />)
                  : <div className="empty">Nothing to follow up yet. Approve or propose a card; you will see who has done their part and what the twin checked.</div>}
            </div>
          </section>
        </div>
      </div>
      <p className="foot-note">{d.foot}</p>
    </>
  );
}
