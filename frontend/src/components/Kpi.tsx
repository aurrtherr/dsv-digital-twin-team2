import type { Kpi, ProjCard, ProjKpis } from '../types';
import { useApp } from '../ctx';
import { DayChartView, DockStrip, OnTimeBar, ProjChartView, WeekBarsView } from './charts';

export function KpiCard({ k, big = true }: { k: Kpi; big?: boolean }) {
  const { go } = useApp();
  const stat = k.st !== 'info'
    ? <span className={`stat ${k.st}`}><span aria-hidden="true">{k.icon}</span> {k.word}</span>
    : <span className="stat info">{k.word}</span>;
  const body = (
    <>
      <div className="khead"><span className="lab">{k.lab}</span>{stat}</div>
      {big ? (
        <div className="krow kwide"><span className="val">{k.valText}</span><div className="kside"><div className="cmp">{k.cmp}</div><div className="def">{k.def}</div></div></div>
      ) : (
        <><div className="krow"><span className="val">{k.valText}</span></div><div className="cmp">{k.cmp}</div><div className="def">{k.def}</div></>
      )}
      {big && k.chart && <div className="pchart">{k.chart.type === 'day' ? <DayChartView c={k.chart} /> : <WeekBarsView c={k.chart} />}</div>}
      {k.go && <div className="go">{k.goLab} →</div>}
    </>
  );
  return k.go
    ? <button type="button" className={`kpi s-${k.st}`} onClick={() => go(k.go!)}>{body}</button>
    : <div className={`kpi s-${k.st}`}>{body}</div>;
}

export const KpiGrid = ({ ks }: { ks: Kpi[] }) => <div className="kpis big">{ks.map((k, i) => <KpiCard key={i} k={k} />)}</div>;

export const KpiLegend = ({ ontime }: { ontime: number }) => (
  <p className="klegend"><b>How to read the status:</b> compared with this week’s usual level at this time of day.{' '}
    <span className="stat ok">✓ On track</span> at or better than average · <span className="stat watch">● Watch</span> up to 25% worse (or up to 10 pts under target) ·{' '}
    <span className="stat act">▲ Act now</span> more than 25% worse. On-time uses the {ontime}% target. <span className="stat info">For context</span> figures have no good or bad direction.
    The operations manager can change these limits.</p>
);

export function ProjCardView({ p }: { p: ProjCard }) {
  const c = p.chart;
  return (
    <div className={`kpi proj s-${p.st}`}>
      <div className="khead"><span className="lab">{p.lab}</span><span className={`stat ${p.st}`} style={{ border: '1px dashed currentColor', background: 'transparent' }}>Projection</span></div>
      <div className="krow kwide"><span className="val">{p.val.main}{p.val.sub && <> <span className="muted small">{p.val.sub}</span></>}</span><div className="kside"><div className="def">{p.foot}</div></div></div>
      {c && <div className="pchart">{c.type === 'proj' ? <ProjChartView c={c} /> : c.type === 'ontime' ? <OnTimeBar o={c} /> : <DockStrip d={c} />}</div>}
    </div>
  );
}

export function ProjKpisView({ p }: { p: ProjKpis }) {
  if (!p.cards.length) return <div className="empty-card"><p>No projection for data checks: they are about records that already exist.</p></div>;
  return (
    <>
      <div className="kpis projg">{p.cards.map((c, i) => <ProjCardView key={i} p={c} />)}</div>
      <p className="klegend">{p.legend}</p>
    </>
  );
}
