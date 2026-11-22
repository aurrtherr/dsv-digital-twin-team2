import type { ReactElement } from 'react';
import { Fragment, useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { api, ApiError } from './api';
import { AppCtx, type App as AppT, type UiState } from './ctx';
import type { AsnDetail, Card, Frame, Meta, OrderDetail } from './types';
import { dayOf, hhmm, when } from './format';
import { Timeline } from './components/Timeline';
import { ApproveDialog, AsnDialog, DismissDialog, EarlierDialog, NewTaskDialog, OrderDialog, RangeDialog } from './components/Dialogs';
import Shift from './views/Shift';
import Outbound from './views/Outbound';
import Inbound from './views/Inbound';
import Trace from './views/Trace';
import Trends from './views/Trends';
import WhatIf from './views/WhatIf';
import Checks from './views/Checks';
import Rules from './views/Rules';
import AtRisk from './views/AtRisk';
import Settings from './views/Settings';
import Tasks from './views/Tasks';

const SCREENS: Record<string, () => ReactElement> = {
  shift: Shift, outbound: Outbound, inbound: Inbound, trace: Trace, trends: Trends, whatif: WhatIf,
  checks: Checks, rules: Rules, atrisk: AtRisk, settings: Settings, tasks: Tasks,
};

// UI preferences stay in this browser. Tasks, decisions and limits live on the backend.
const KEY = 'whtwin.ui.v1';
const DEFAULT_UI: UiState = {
  t: 20 * 1440 + 540, at: null, role: 'out', view: 'shift', theme: null, tlPast: 'yday', tlNext: 'mid', protoHidden: false,
  navOpen: {}, othersOpen: false, obBy: 'lane', obSel: null, obCap: 15, arSel: null, traceQ: '0000031762', trWk: false, wi: 20,
};
const loadUi = (): UiState => { try { return { ...DEFAULT_UI, ...JSON.parse(localStorage.getItem(KEY) || '{}') }; } catch { return DEFAULT_UI; } };

type Dlg =
  | { kind: 'approve'; c: Card } | { kind: 'dismiss'; c: Card } | { kind: 'task' } | { kind: 'earlier' } | { kind: 'range' }
  | { kind: 'order'; o: OrderDetail } | { kind: 'asn'; a: AsnDetail } | null;

export default function App() {
  const [meta, setMeta] = useState<Meta | null>(null);
  const [frame, setFrame] = useState<Frame | null>(null);
  const [err, setErr] = useState<string>('');
  const [ui, setUi] = useState<UiState>(loadUi);
  const [rev, setRev] = useState(0); // bump to refetch after an action
  const [dlg, setDlg] = useState<Dlg>(null);
  const [toast, setToast] = useState<{ msg: string; undo: Record<string, unknown> | null } | null>(null);
  const [playing, setPlaying] = useState(false);
  const toastTm = useRef<number | undefined>(undefined);

  const set = useCallback((p: Partial<UiState>) => setUi(u => ({ ...u, ...p })), []);
  useEffect(() => { try { localStorage.setItem(KEY, JSON.stringify(ui)); } catch { /* storage off */ } }, [ui]);
  useEffect(() => { if (ui.theme) document.documentElement.dataset.theme = ui.theme; }, [ui.theme]);
  useEffect(() => { api.meta().then(setMeta).catch(e => setErr(String(e.message || e))); }, []);

  // One request per render of a screen
  useEffect(() => {
    const ac = new AbortController();
    api.frame({ t: ui.t, at: ui.at, role: ui.role, view: ui.view, obBy: ui.obBy, obSel: ui.obSel, obCap: ui.obCap, arSel: ui.arSel,
      traceQ: ui.traceQ, trWk: ui.trWk, wi: ui.wi, tlPast: ui.tlPast, tlNext: ui.tlNext }, ac.signal)
      .then(f => { setFrame(f); setErr(''); })
      .catch(e => { if (e.name !== 'AbortError') setErr(String(e.message || e)); });
    return () => ac.abort();
  }, [ui.t, ui.at, ui.role, ui.view, ui.obBy, ui.obSel, ui.obCap, ui.arSel, ui.traceQ, ui.trWk, ui.tlPast, ui.tlNext, rev, ui.view === 'whatif' ? 0 : ui.wi]);

  const showToast = useCallback((msg: string | null, undo: Record<string, unknown> | null = null) => {
    if (!msg) return;
    setToast({ msg, undo });
    window.clearTimeout(toastTm.current);
    toastTm.current = window.setTimeout(() => setToast(null), 10000);
  }, []);

  // Play: one hour every 0.9 s
  useEffect(() => {
    if (!playing || !meta) return;
    const id = window.setInterval(() => setUi(u => {
      if (u.t >= meta.T1) { setPlaying(false); return u; }
      return { ...u, t: Math.min(meta.T1, u.t + 60), at: null };
    }), 900);
    return () => window.clearInterval(id);
  }, [playing, meta]);

  const act = useCallback(async (name: string, body: Record<string, unknown>): Promise<string | void> => {
    try {
      const r = await api.act(name, { t: ui.t, role: ui.role, ...body });
      setRev(x => x + 1);
      showToast(r.toast, r.undo);
    } catch (e) {
      if (e instanceof ApiError) return e.message;
      return 'Could not reach the backend.';
    }
  }, [ui.t, ui.role, showToast]);

  const app: AppT | null = useMemo(() => {
    if (!meta || !frame) return null;
    const canAct = frame.mode === 'now';
    return {
      meta, frame, ui, set, canAct,
      go: (view: string) => {
        const grp = meta.navGroups.find(g => g[2].includes(view));
        set({ view, navOpen: grp ? { ...ui.navOpen, [grp[0]]: true } : ui.navOpen });
        window.scrollTo({ top: 0 });
      },
      jump: (t: number) => { set({ t, at: null }); window.scrollTo({ top: 0 }); },
      openOrder: (i: number) => { api.order(i, ui.t, ui.at, ui.role).then(o => setDlg({ kind: 'order', o })).catch(e => showToast(String(e.message))); },
      openAsn: (i: number) => { api.asn(i, ui.t, ui.at, ui.role).then(a => setDlg({ kind: 'asn', a })).catch(e => showToast(String(e.message))); },
      lookup: (q: string) => {
        api.lookup(q).then(r => {
          if (r.kind === 'order') app!.openOrder(r.i!); else if (r.kind === 'asn') app!.openAsn(r.i!); else showToast(r.msg || 'Not found');
        });
      },
      trace: (q: string) => { setDlg(null); set({ traceQ: q, view: 'trace' }); window.scrollTo({ top: 0 }); },
      approve: (c: Card) => setDlg({ kind: 'approve', c }),
      dismiss: (c: Card) => setDlg({ kind: 'dismiss', c }),
      propose: (c: Card) => { act('propose', { key: c.key }).then(m => m && showToast(m)); },
      tick: (id: string, part: string, done: boolean) => { act('tick', { id, part, done }).then(m => m && showToast(m)); },
      newTask: () => setDlg({ kind: 'task' }),
      seed: () => { act('seed', {}).then(m => m && showToast(m)); },
      saveCfg: (values: Record<string, number>) => { act('cfg', { values }).then(m => m && showToast(m)); },
      resetCfg: () => { act('cfg-reset', {}).then(m => m && showToast(m)); },
    };
  }, [meta, frame, ui, set, act, showToast]);

  if (err && !frame) return <div style={{ padding: 40, fontFamily: 'system-ui' }}><h2>Cannot reach the twin backend</h2><p>{err}</p><p>Start it with <code>uvicorn app.main:app --port 8000</code> in the <code>backend</code> folder, then reload.</p></div>;
  if (!app || !meta || !frame) return <div style={{ padding: 40, fontFamily: 'system-ui' }}>Loading the twin…</div>;

  const mode = frame.mode, now = frame.t, vt = frame.at == null ? now : frame.at;
  const setAt = (t: number | null) => set({ at: t == null || t === ui.t ? null : t });
  const step = (dm: number) => set({ t: Math.min(meta.T1, Math.max(meta.T0, ui.t + dm)), at: null });
  const isDark = (ui.theme || (matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light')) === 'dark';
  const View = SCREENS[frame.view] || Shift;
  const navItem = ([k, n]: [string, string]) => (
    <button type="button" onClick={() => app.go(k)} aria-current={ui.view === k ? 'page' : undefined}>
      {n}{k === 'tasks' && frame.myOpen > 0 && <span className="badge" aria-label={`${frame.myOpen} open`}>{frame.myOpen}</span>}
    </button>
  );

  return (
    <AppCtx.Provider value={app}>
      <section className="proto" id="proto" aria-label="Prototype controls">
        <div className="proto-in" hidden={ui.protoHidden}>
          <div className="proto-row"><span className="proto-lab">Prototype controls <span className="muted">· not part of the product</span></span>
            <div className="roles" role="group" aria-label="View the twin as">
              {Object.entries(meta.roles).map(([k, r]) => <button key={k} type="button" aria-pressed={ui.role === k} onClick={() => { setToast(null); set({ role: k }); }}>{r.name}</button>)}
            </div>
            <button className="theme-btn" type="button" aria-pressed={isDark} onClick={() => set({ theme: isDark ? 'light' : 'dark' })}>{isDark ? 'Light mode' : 'Dark mode'}</button>
            <button className="theme-btn" type="button" aria-expanded="true" onClick={() => set({ protoHidden: true })}>Hide</button>
          </div>
          <div className="clock">
            <div className="now"><small>Simulated now</small>{when(now)}</div>
            <button type="button" aria-label="Simulated now one hour back" onClick={() => step(-60)}>−1 h</button>
            <input type="range" min={meta.T0} max={meta.T1} step={60} value={ui.t} aria-label="Simulated now (replay of DSV data)" onChange={e => set({ t: +e.target.value, at: null })} />
            <button type="button" aria-label="Simulated now one hour forward" onClick={() => step(60)}>+1 h</button>
            <button type="button" onClick={() => setPlaying(p => !p)}>{playing ? 'Pause' : 'Play'}</button>
            <div className="days">{meta.days.map(([d, l]) => <button key={d} type="button" className={dayOf(ui.t) === d ? 'on' : ''} onClick={() => set({ t: Math.min(meta.T1, Math.max(meta.T0, d * 1440 + 540)), at: null })}>{l}</button>)}</div>
          </div>
        </div>
        <button type="button" className="proto-tab" aria-expanded="false" hidden={!ui.protoHidden} onClick={() => set({ protoHidden: false })}>Prototype controls ▾</button>
      </section>

      <header className="top">
        <div className="top-row">
          <div className="brand"><b>Warehouse Twin</b><span>{meta.roles[frame.role].name} · Singapore</span></div>
          <div className="tl-head">
            <span className={`tl-mode ${mode}`}>{mode === 'past' ? 'Past · read only' : mode === 'next' ? 'Projection' : 'Now'}</span>
            <span className="tl-time num">{when(vt)}{vt < frame.timeline.w0 ? ' (earlier)' : ''}</span>
            {mode !== 'now' && <button type="button" className="tl-btn" onClick={() => setAt(null)}>Back to now</button>}
            <button type="button" className="tl-btn" onClick={() => setDlg({ kind: 'earlier' })}>Earlier…</button>
            <button type="button" className="tl-btn" aria-haspopup="dialog" onClick={() => setDlg({ kind: 'range' })}>Range…</button>
          </div>
        </div>
        <Timeline tl={frame.timeline} at={frame.at} mode={mode} onSet={setAt} />
        <p className="tl-say" aria-live="polite">
          <span>{mode === 'past' ? `Showing the warehouse as it was at ${when(vt)}. Actions are off; each card shows what happened next.`
            : mode === 'next' ? `Projection for ${when(vt)}, from plans known now and this week’s pace. Act on it in Now.`
              : 'Live. Drag left to look back, right to see a projection. Keys: ← → hour, Page Up / Down landmark, N now.'}</span>
          <span>Past · real data &nbsp;|&nbsp; <span style={{ color: 'var(--gold)' }}>Next · projection</span></span>
        </p>
      </header>

      <div className="shell">
        <nav className="side" aria-label="Screens">
          {meta.navGroups.map(([g, lab, keys]) => {
            const open = ui.navOpen[g] !== false;
            return (
              <Fragment key={g}>
                <button type="button" className="ngrp" aria-expanded={open} aria-controls={`ng-${g}`} onClick={() => set({ navOpen: { ...ui.navOpen, [g]: !open } })}>
                  <span>{lab}{keys.includes('tasks') && frame.myOpen > 0 && !open && <span className="gcount"> · {frame.myOpen} to do</span>}</span><span className="chev" aria-hidden="true">▾</span>
                </button>
                <ul className="nlist" id={`ng-${g}`} hidden={!open}>{keys.map(k => <li key={k}>{navItem(meta.views.find(v => v[0] === k)!)}</li>)}</ul>
              </Fragment>
            );
          })}
          <div className="side-note">Tasks and decisions are saved on the twin backend.<br />
            <button type="button" onClick={() => { if (confirm('Reset the demo? This deletes all tasks, decisions and limit changes on the backend.')) api.act('reset', {}).then(() => { set({ t: DEFAULT_UI.t, at: null, role: 'out', view: 'shift' }); setRev(x => x + 1); }); }}>Reset demo</button></div>
        </nav>
        <main id="main">
          <div className="mobile-nav" aria-label="Screens">{meta.views.map(v => <Fragment key={v[0]}>{navItem(v)}</Fragment>)}</div>
          <div id="view">
            {mode === 'past' && <div className="mode-banner past" role="status"><b>Past · {when(frame.at)}</b><span>Read only. This is what the twin showed then; cards show what happened next.</span><button type="button" className="btn sm" onClick={() => setAt(null)}>Back to now</button></div>}
            {mode === 'next' && <div className="mode-banner next" role="status"><b>Projection · {when(frame.at)}</b>
              <span>{meta.projViews.includes(frame.view) ? 'Projected figures are dashed. Everything else on this screen still shows now.' : 'No projection for this screen; it shows now.'} Projections use plans known at {dayOf(now) === dayOf(frame.at!) ? hhmm(now) : when(now)} and this week’s pace.</span>
              <button type="button" className="btn sm" onClick={() => setAt(null)}>Back to now</button></div>}
            <View />
          </div>
        </main>
      </div>

      {dlg?.kind === 'approve' && <ApproveDialog c={dlg.c} t={ui.t} meta={meta} onClose={() => setDlg(null)} onSubmit={b => act('approve', { key: dlg.c.key, ...b })} />}
      {dlg?.kind === 'dismiss' && <DismissDialog c={dlg.c} onClose={() => setDlg(null)} onSubmit={(reason, details) => act('dismiss', { key: dlg.c.key, reason, details })} />}
      {dlg?.kind === 'task' && <NewTaskDialog t={ui.t} role={ui.role} meta={meta} onClose={() => setDlg(null)} onSubmit={b => act('task', b)} />}
      {dlg?.kind === 'earlier' && <EarlierDialog t={ui.t} at={frame.at} T0={meta.T0} onClose={() => setDlg(null)} onGo={v => setAt(v)} />}
      {dlg?.kind === 'range' && <RangeDialog meta={meta} tlPast={ui.tlPast} tlNext={ui.tlNext} onClose={() => setDlg(null)}
        onApply={(p, n) => { set({ tlPast: p, tlNext: n, at: null }); showToast('Timeline range updated'); }} />}
      {dlg?.kind === 'order' && <OrderDialog o={dlg.o} onClose={() => setDlg(null)} onTrace={c => app.trace(c)} />}
      {dlg?.kind === 'asn' && <AsnDialog a={dlg.a} onClose={() => setDlg(null)} />}

      <div className="toast" role="status" aria-live="polite" hidden={!toast}>
        <span>{toast?.msg}</span>
        {toast?.undo && <button type="button" onClick={() => { const u = toast.undo; setToast(null); api.act('undo', { token: u }).then(() => setRev(x => x + 1)); }}>Undo</button>}
      </div>
    </AppCtx.Provider>
  );
}

