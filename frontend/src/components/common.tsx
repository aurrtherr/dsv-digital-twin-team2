import type { CSSProperties } from 'react';
import type { ReactNode } from 'react';
import type { HBars, Rich as RichT, Tag as TagT } from '../types';

export const Rich = ({ r }: { r: RichT }) => (
  <>{r.map(([s, b], k) => (b ? <b key={k}>{s}</b> : <span key={k}>{s}</span>))}</>
);

export const Tag = ({ t }: { t: TagT | null | undefined }) => (t ? <span className={`tag ${t[0]}`}>{t[1]}</span> : null);

export const Empty = ({ children }: { children: ReactNode }) => <div className="empty">{children}</div>;

export const LateChip = () => (
  <span className="chip"><b>Late</b> = handed over on a later calendar day than planned</span>
);

export function HBarsView({ h }: { h: HBars }) {
  return (
    <>
      {h.rows.map((r, k) => (
        <div className="hbar" key={k}>
          <span className="nm" title={r.nm}>{r.nm}</span>
          <span className="track"><span className={`fill ${h.cls}`} style={{ width: `${(100 * r.frac).toFixed(1)}%`, display: 'block' }} /></span>
          <span className="n num">{r.nText}</span>
        </div>
      ))}
    </>
  );
}

export function Panel({ title, sub, children, style, className }: { title?: ReactNode; sub?: ReactNode; children?: ReactNode; style?: CSSProperties; className?: string }) {
  return (
    <section className={`panel ${className || ''}`} style={style}>
      {title != null && <h2>{title}</h2>}
      {sub != null && <p className="sec-sub">{sub}</p>}
      {children}
    </section>
  );
}

export const Col = ({ children, stick }: { children: ReactNode; stick?: boolean }) => (
  <div className={stick ? 'stick' : undefined} style={{ display: 'flex', flexDirection: 'column', gap: 20, minWidth: 0 }}>{children}</div>
);

export function Segments({ segs, height = 22, label }: { segs: [number, string, string][]; height?: number; label?: string }) {
  return (
    <div style={{ display: 'flex', height, borderRadius: 6, overflow: 'hidden', gap: 2 }} role="img" aria-label={label}>
      {segs.map(([n, bg, l], k) => (n ? <span key={k} title={`${l}: ${n.toLocaleString('en-US')}`} style={{ flex: n, background: bg, minWidth: 3 }} /> : null))}
    </div>
  );
}
