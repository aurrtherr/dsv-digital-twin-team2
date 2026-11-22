import type { CSSProperties, ReactNode } from 'react';
import type { Card, OtherRow, PageCards, PropView, TaskView } from '../types';
import { useApp } from '../ctx';
import { Tag } from './common';

export function RuleCard({ c }: { c: Card }) {
  const { approve, dismiss, propose } = useApp();
  const ctl = c.controls;
  let btns: ReactNode;
  switch (ctl.kind) {
    case 'outcome': btns = <div className="outcome">{ctl.text}</div>; break;
    case 'next': btns = <span className="tag">Act on this in Now</span>; break;
    case 'propose': btns = <button className="btn pri" type="button" onClick={() => propose(c)}>Propose to supervisor</button>; break;
    case 'waitPropose': btns = <span className="tag">Waiting for the {ctl.who} to propose · view only</span>; break;
    case 'owner': btns = (
      <>
        <button className="btn pri" type="button" onClick={() => approve(c)}>{ctl.early ? 'Act early' : 'Approve & assign'}</button>
        <button className="btn" type="button" onClick={() => dismiss(c)}>Dismiss</button>
      </>
    ); break;
    case 'viewOnly': btns = <span className="tag">View only · decided by the {ctl.who}</span>; break;
  }
  return (
    <article className={`card sev-${c.sev} ${c.early ? 'tier-prevent' : ''} ${c.mine ? '' : 'other'}`}>
      <div className="card-top">
        <span className="rid">{c.rule}</span>
        {c.tierTag ? <Tag t={c.tierTag} /> : <span className={`sev ${c.sevCls}`}>{c.sevLab}</span>}
        <span>{c.ownerName}</span>
        {c.notes.map((n, i) => <Tag key={i} t={n} />)}
      </div>
      <h3>{c.title}</h3>
      <p>{c.why}</p>
      <div className="act"><b>Recommended:</b> {c.action}</div>
      <div className="meta"><span><b>Who does it:</b> {c.doer}</span><span><b>Twin checks:</b> {c.done}</span></div>
      <div className="btns">{btns}</div>
    </article>
  );
}

export function OtherList({ rows, full, style }: { rows: OtherRow[]; full?: boolean; style?: CSSProperties }) {
  return (
    <div className="olist" style={style}>
      {rows.map((c, i) => (
        <div className="orow" key={i}>
          <span className="rid">{c.rule}</span><span className={`sev ${c.sevCls}`}>{c.sevLab}</span>
          <span className={full ? 'tt' : undefined}>{c.title}</span>
          <span className="muted small">{full ? c.ownerName : c.ownerShort} decides</span>
        </div>
      ))}
    </div>
  );
}

export function PageCardsView({ p }: { p: PageCards }) {
  return (
    <section className="panel">
      <h2>{p.title} <span className="muted small">({p.n})</span></h2>
      <p className="sec-sub">{p.sub}</p>
      <div className="cards">{p.mine.map(c => <RuleCard key={c.key} c={c} />)}</div>
      {p.rest.length > 0 && <OtherList rows={p.rest} style={{ marginTop: p.mine.length ? 12 : 0 }} />}
    </section>
  );
}

export function TaskItem({ x }: { x: TaskView }) {
  const { tick } = useApp();
  const p = x.progress;
  return (
    <div className={`task ${x.over ? 'is-over' : ''}`}>
      <div className="t1"><span className="rid">{x.rule}</span><span>{x.head}</span><Tag t={x.statusTag} /><Tag t={x.dueTag} />{x.extra.map((e, i) => <Tag key={i} t={e} />)}</div>
      <div className="t2">{x.action}</div>
      <div className="muted small">{x.sub}</div>
      {p && (
        <>
          <div className="prog" role="progressbar" aria-valuemin={0} aria-valuemax={p.tot} aria-valuenow={p.n} aria-label={p.text}><i style={{ width: `${(p.tot ? (100 * p.n) / p.tot : 0).toFixed(1)}%` }} /></div>
          <div className="muted small num">{p.text}</div>
        </>
      )}
      <div className="parts" aria-label="Who does it">
        {x.parts.map(pt => pt.state === 'nn' ? (
          <div className="part nn" key={pt.a}><span className="pi" aria-hidden="true">–</span><span><span className="pn">{pt.short}</span> · no longer needed: the data shows it resolved</span></div>
        ) : (
          <div className={`part ${pt.state === 'ok' ? 'ok' : ''}`} key={pt.a}>
            <span className="pi" aria-hidden="true">{pt.state === 'ok' ? '✓' : ''}</span>
            <span><span className="pn">{pt.short}{pt.suffix}</span> · {pt.doneText}</span>
            {pt.can && (pt.state === 'ok'
              ? <button type="button" className="lnk" onClick={() => tick(x.id, pt.a, false)}>Undo</button>
              : <button type="button" className="btn sm" onClick={() => tick(x.id, pt.a, true)}>{pt.btn}</button>)}
          </div>
        ))}
      </div>
    </div>
  );
}

export function PropItem({ p }: { p: PropView }) {
  return (
    <div className="task">
      <div className="t1"><span className="rid">{p.rule}</span><span>proposed by you</span></div>
      <div className="t2">{p.action}</div>
      <div className="muted small">{p.title}</div>
      <div className="prop-steps">
        {p.steps.map((s, i) => <span key={i} style={{ display: 'contents' }}>{i > 0 && '→'}<span className={s[0]}>{s[1]}</span></span>)}
      </div>
      {p.reason && <div className="muted small">Reason: {p.reason}</div>}
    </div>
  );
}
