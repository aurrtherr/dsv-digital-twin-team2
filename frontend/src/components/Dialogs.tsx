import type { ReactNode } from 'react';
// Modal dialogs (native <dialog>): approve, dismiss, new task, look back, timeline range, order and ASN detail.
import { useEffect, useRef, useState } from 'react';
import type { AsnDetail, Card, Meta, OrderDetail } from '../types';
import { dayLabel, dayOf, hhmm, when } from '../format';

export function Dialog({ children, onClose, wide }: { children: ReactNode; onClose: () => void; wide?: boolean }) {
  const ref = useRef<HTMLDialogElement>(null);
  useEffect(() => {
    const d = ref.current!;
    const opener = document.activeElement as HTMLElement | null;
    if (!d.open) d.showModal();
    const first = d.querySelector<HTMLElement>('input:not([type=hidden]),select,textarea');
    first?.focus();
    return () => { if (opener && opener.isConnected) opener.focus(); };
  }, []);
  return (
    <dialog ref={ref} aria-labelledby="dlgTitle" onCancel={e => { e.preventDefault(); onClose(); }}>
      <div className="mod">{wide && <span className="drill" hidden />}{children}</div>
    </dialog>
  );
}

const Err = ({ msg }: { msg: string }) => (msg ? <p className="errmsg" role="alert">⚠ {msg}</p> : null);

function dueOptions(t: number): [number | '', string][] {
  const d = dayOf(t), h = t % 1440;
  const o: [number | '', string][] = [[t + 60, 'Within 1 hour'], [t + 120, 'Within 2 hours']];
  if (h < 18 * 60) o.push([d * 1440 + 18 * 60, 'Today 18:00']);
  o.push([(d + 1) * 1440 + 9 * 60, 'Tomorrow 09:00'], ['', 'No due time']);
  return o;
}

function DueSelect({ t, pick }: { t: number; pick?: number }) {
  const p = pick ?? ((t % 1440) < 16 * 60 ? 2 : 1);
  const opts = dueOptions(t);
  return (
    <label className="small muted">Due
      <select name="due" defaultValue={String(opts[Math.min(p, opts.length - 1)][0])}>
        {opts.map(([v, l]) => <option key={String(v) + l} value={String(v)}>{l}{v !== '' ? ` (${when(+v)})` : ''}</option>)}
      </select>
    </label>
  );
}

function WhoBoxes({ meta, pre }: { meta: Meta; pre: string[] }) {
  return (
    <fieldset className="whoset"><legend className="muted small">Who does it (each role ticks off its own part)</legend>
      {Object.entries(meta.assign).map(([k, r]) => <label className="ck" key={k}><input type="checkbox" name="a" value={k} defaultChecked={pre.includes(k)} /> {r.name}</label>)}
    </fieldset>
  );
}

type Submit = (fd: FormData) => Promise<string | void> | string | void; // return an error message to keep the dialog open

function FormDialog({ title, children, ok, onClose, onSubmit }: { title: ReactNode; children: ReactNode; ok: string; onClose: () => void; onSubmit: Submit }) {
  const [err, setErr] = useState('');
  return (
    <Dialog onClose={onClose}>
      <form onSubmit={async e => { e.preventDefault(); const m = await onSubmit(new FormData(e.currentTarget)); if (m) setErr(m); else onClose(); }} style={{ display: 'contents' }}>
        <h3 id="dlgTitle">{title}</h3>
        {children}
        <Err msg={err} />
        <div className="row"><button className="btn" type="button" onClick={onClose}>Cancel</button><button className="btn pri" type="submit">{ok}</button></div>
      </form>
    </Dialog>
  );
}

export function ApproveDialog({ c, t, meta, onClose, onSubmit }: { c: Card; t: number; meta: Meta; onClose: () => void; onSubmit: (b: { assign: string[]; due: number | null; note: string }) => Promise<string | void> }) {
  const early = c.tier === 'prevent' && c.trig != null;
  const trig = c.trig ?? t;
  const before = Math.max(t + 30, trig - 60);
  return (
    <FormDialog title={<>{early ? 'Act early' : 'Approve & assign'} · {c.rule}</>} ok={early ? 'Create early task' : 'Approve & assign'} onClose={onClose}
      onSubmit={fd => {
        const assign = fd.getAll('a') as string[];
        if (!assign.length) return 'Tick at least one role who will do this.';
        const due = fd.get('due') as string;
        return onSubmit({ assign, due: due ? +due : null, note: ((fd.get('note') as string) || '').trim() });
      }}>
      {early && <p className="small muted" style={{ margin: 0 }}>This rule would fire {trig >= (dayOf(t) + 1) * 1440 ? 'at midnight' : 'at ' + hhmm(trig)}. The task is created now, due before then.</p>}
      <p className="muted" style={{ margin: 0 }}>{c.title}</p>
      <div><b>Task:</b> {c.action}</div>
      <WhoBoxes meta={meta} pre={c.assign} />
      {early ? (
        <label className="small muted">Due<select name="due" defaultValue={String(before)}>
          <option value={String(before)}>Before it fires ({when(before)})</option>
          <option value={String(trig)}>When it would fire ({when(trig)})</option>
        </select></label>
      ) : <DueSelect t={t} pick={c.rule === 'IN-01' ? 0 : undefined} />}
      <label className="small muted">Note (optional)<textarea name="note" rows={2} /></label>
      <div className="muted small">The twin will check: {c.done} · {c.nIds.toLocaleString('en-US')} record{c.nIds > 1 ? 's' : ''}</div>
    </FormDialog>
  );
}

export function DismissDialog({ c, onClose, onSubmit }: { c: Card; onClose: () => void; onSubmit: (reason: string, details: string) => Promise<string | void> }) {
  return (
    <FormDialog title={<>Dismiss · {c.rule}</>} ok="Dismiss card" onClose={onClose}
      onSubmit={fd => {
        const r = fd.get('r') as string, d = ((fd.get('d') as string) || '').trim();
        if (r === 'Other' && !d) return 'Add a few words on why, so the team knows.';
        return onSubmit(r, d);
      }}>
      <p className="muted" style={{ margin: 0 }}>{c.title}</p>
      <label className="small muted">Reason<select name="r">
        <option>Already handled outside the twin</option><option>Data issue, not a real problem</option><option>Not a priority today</option><option>Other</option>
      </select></label>
      <label className="small muted">Details<textarea name="d" rows={2} /></label>
    </FormDialog>
  );
}

export function NewTaskDialog({ t, role, meta, onClose, onSubmit }: { t: number; role: string; meta: Meta; onClose: () => void; onSubmit: (b: { title: string; assign: string[]; due: number | null; note: string }) => Promise<string | void> }) {
  const pre = role === 'plan' ? ['plan'] : role === 'mgr' ? ['mgr'] : role === 'dq' ? ['dq'] : [role, 'floor'];
  return (
    <FormDialog title="New task" ok="Create task" onClose={onClose}
      onSubmit={fd => {
        const title = ((fd.get('title') as string) || '').trim(), assign = fd.getAll('a') as string[];
        if (!title) return 'Say what needs doing.';
        if (!assign.length) return 'Tick at least one role who will do this.';
        const due = fd.get('due') as string;
        return onSubmit({ title, assign, due: due ? +due : null, note: ((fd.get('note') as string) || '').trim() });
      }}>
      <p className="muted small" style={{ margin: 0 }}>For work that no rule card covers, such as a recount or a call. It is tracked by people ticking their part; the twin has no data to check it.</p>
      <label className="small muted">What needs doing<input className="field" name="title" maxLength={120} placeholder="e.g. Recount ASN 0000032060 at dock 3" /></label>
      <WhoBoxes meta={meta} pre={pre} />
      <DueSelect t={t} />
      <label className="small muted">Note (optional)<textarea name="note" rows={2} /></label>
    </FormDialog>
  );
}

export function EarlierDialog({ t, at, T0, onClose, onGo }: { t: number; at: number | null; T0: number; onClose: () => void; onGo: (t: number) => void }) {
  const d0 = dayOf(T0), d1 = dayOf(t), cur = at == null ? t : at;
  return (
    <FormDialog title="Look back to an earlier time" ok="Go to this time" onClose={onClose}
      onSubmit={fd => {
        const v = +(fd.get('d') as string) * 1440 + +(fd.get('h') as string) * 60;
        if (v > t) return 'Pick a time before now. To look ahead, drag right on the timeline.';
        onGo(v);
      }}>
      <p className="muted" style={{ margin: 0 }}>Pick any hour in the replay week before now.</p>
      <div style={{ display: 'flex', gap: 10 }}>
        <label className="small muted" style={{ flex: 1 }}>Day<select name="d" defaultValue={String(dayOf(cur))}>
          {Array.from({ length: d1 - d0 + 1 }, (_, k) => d0 + k).map(d => <option key={d} value={d}>{dayLabel(d)}</option>)}</select></label>
        <label className="small muted" style={{ flex: 1 }}>Hour<select name="h" defaultValue={String(Math.floor((cur % 1440) / 60))}>
          {Array.from({ length: 24 }, (_, h) => <option key={h} value={h}>{String(h).padStart(2, '0')}:00</option>)}</select></label>
      </div>
    </FormDialog>
  );
}

export function RangeDialog({ meta, tlPast, tlNext, onClose, onApply }: { meta: Meta; tlPast: string; tlNext: string; onClose: () => void; onApply: (p: string, n: string) => void }) {
  const grp = (name: string, legend: string, opts: Record<string, string>, cur: string) => (
    <fieldset className="whoset"><legend className="muted small">{legend}</legend>
      {Object.entries(opts).map(([k, l]) => <label className="ck" key={k}><input type="radio" name={name} value={k} defaultChecked={k === cur} /> {l}</label>)}
    </fieldset>
  );
  return (
    <FormDialog title="Timeline range" ok="Apply" onClose={onClose} onSubmit={fd => onApply(fd.get('p') as string, fd.get('n') as string)}>
      <p className="muted small" style={{ margin: 0 }}>Choose how far the timeline reaches. Longer projections are less certain; the range shown on each figure widens.</p>
      {grp('p', 'Look back', meta.tlPast, tlPast)}
      {grp('n', 'Project ahead', meta.tlNext, tlNext)}
    </FormDialog>
  );
}

export function OrderDialog({ o, onClose, onTrace }: { o: OrderDetail; onClose: () => void; onTrace: (c: string) => void }) {
  const tag = o.state === 'Past planned day' ? 'late' : o.state === 'Due today' ? 'wait' : o.state === 'Handed over' ? 'ok' : '';
  return (
    <Dialog onClose={onClose} wide>
      <h3 id="dlgTitle" className="drill">Order {o.key}</h3>
      <div className="chips"><span className={`tag ${tag}`}>{o.state}</span><span className="chip">{o.dn}</span><span className="chip">{o.lane}</span></div>
      <dl className="kv"><dt>Created</dt><dd className="num">{o.created}</dd><dt>Planned day</dt><dd>{o.planned}</dd><dt>Packed</dt><dd className="num">{o.packed}</dd><dt>Handed over</dt><dd className="num">{o.handed}</dd></dl>
      <div className="tbl-wrap" style={{ maxHeight: 300, overflow: 'auto' }}><table><thead><tr><th>Line</th><th>SKU</th><th className="r">Qty shipped</th><th>Carton</th></tr></thead>
        <tbody>{o.lines.map((r, i) => <tr key={i}><td className="num">{r.line}</td><td className="num">{r.sku}</td><td className="r num">{r.qty}</td>
          <td className="num">{r.carton}{r.milk && <> <button type="button" className="lnk" onClick={() => onTrace(r.carton)}>trace</button></>}</td></tr>)}</tbody></table></div>
      <p className="muted small" style={{ margin: 0 }}>{o.foot}</p>
      <div className="row"><button className="btn pri" type="button" onClick={onClose}>Close</button></div>
    </Dialog>
  );
}

export function AsnDialog({ a, onClose }: { a: AsnDetail; onClose: () => void }) {
  return (
    <Dialog onClose={onClose} wide>
      <h3 id="dlgTitle" className="drill">ASN {a.asn}{a.ref ? ' · shipment ' + a.ref : ''}</h3>
      <div className="chips"><span className="chip">{a.type}</span>{a.hv && <span className="tag late">High value</span>}
        {a.got ? <span className={`tag ${a.bad ? 'late' : 'ok'}`}>{a.bad ? `${a.bad} line${a.bad > 1 ? 's' : ''} differ` : 'All lines match'}</span> : <span className="tag wait">Not received yet</span>}</div>
      <dl className="kv"><dt>Docked</dt><dd className="num">{a.docked}</dd><dt>Received</dt><dd className="num">{a.received}</dd></dl>
      <div className="tbl-wrap" style={{ maxHeight: 300, overflow: 'auto' }}><table><thead><tr><th>Line</th><th>SKU</th><th>Packing</th><th className="r">Expected</th><th className="r">Received</th><th>Match</th><th>Zone</th></tr></thead>
        <tbody>{a.lines.map((r, i) => <tr key={i}><td className="num">{r.line}</td><td className="num">{r.sku}</td><td>{r.pack}</td><td className="r num">{r.exp}</td><td className="r num">{r.rcv}</td>
          <td>{r.match == null ? <span className="muted">—</span> : r.match ? '✓' : <b style={{ color: 'var(--late)' }}>≠</b>}</td><td>{r.zone}</td></tr>)}</tbody></table></div>
      <p className="muted small" style={{ margin: 0 }}>Line = ASN + Ref Line + Functional Packing (DSV A5); received quantities summed across split receipts.</p>
      <div className="row"><button className="btn pri" type="button" onClick={onClose}>Close</button></div>
    </Dialog>
  );
}
