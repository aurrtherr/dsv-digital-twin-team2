// Shapes of the JSON the Python backend returns (see backend/app/screens/).

export type Rich = [string, boolean][];
export type Tag = [string, string]; // [css class, text]
export type Mode = 'now' | 'past' | 'next';
export type Status = 'ok' | 'watch' | 'act' | 'info';

export interface Role { name: string; short: string }

export interface Meta {
  T0: number; T1: number;
  roles: Record<string, Role>;
  assign: Record<string, Role>;
  views: [string, string][];
  navGroups: [string, string, string[]][];
  projViews: string[];
  cfgMeta: [string, string, string, string, number, number, number][];
  cfgDef: Record<string, number>;
  tlPast: Record<string, string>;
  tlNext: Record<string, string>;
  days: [number, string][];
}

// ---------- charts
export interface DayChart {
  type: 'day'; t0: number; t1: number; t: number; val: number; st: Status;
  today: [number, number][]; base: [number, number][]; after: [number, number][];
  aria: string; t0Lab: string; nowLab: string; t1Lab: string;
}
export interface WeekBars {
  type: 'week'; bars: { label: string; valText: string; frac: number; good: boolean; current: boolean }[];
  refFrac: number | null; info: boolean; aria: string; refLab: string; badLab: string;
}
export interface ProjChart {
  type: 'proj'; hist: [number, number][]; proj: [number, number, number, number][];
  t0: number; t1: number; now: number; marks?: [number, string][];
}
export interface OnTimeChart { type: 'ontime'; done: number; mid: number | null; mn: number | null; mx: number | null; target: number; doneText: string; midText: string }
export interface DockChart { type: 'dock'; points: { asn: string; atHH: string; left: number; type: string }[]; nowLab: string; endLab: string }

export interface Kpi {
  lab: string; valText: string; st: Status; icon: string; word: string; cmp: string; def: string;
  go: string | null; goLab: string | null; chart: DayChart | WeekBars | null;
}
export interface ProjCard { lab: string; val: { main: string; sub: string | null }; foot: string; st: Status; chart: ProjChart | OnTimeChart | DockChart | null }
export interface ProjKpis { cards: ProjCard[]; legend: string }

export interface BarsRow { label: string; sub?: string; vals: number[]; faint?: boolean; hl?: boolean; colors: string[]; tips: string[]; valLabels?: string[] }
export interface BarsSpec { label: string; max: number; grid: [number, string][]; rows: BarsRow[]; ref: number | null; refLabel: string | null }

export interface HBars { kind: 'hbars'; rows: { nm: string; n: number; nText: string; frac: number }[]; cls: string }

// ---------- cards and tasks
export type Controls =
  | { kind: 'outcome'; k: string; text: string }
  | { kind: 'next' }
  | { kind: 'propose' }
  | { kind: 'waitPropose'; who: string }
  | { kind: 'owner'; early: boolean }
  | { kind: 'viewOnly'; who: string };

export interface Card {
  key: string; rule: string; sev: string; sevCls: string; sevLab: string; tier: string | null; tierTag: Tag | null;
  ownerName: string; notes: Tag[]; title: string; why: string; action: string; doer: string; done: string; mine: boolean;
  controls: Controls; assign: string[]; trig: number | null; nIds: number; early: boolean;
}
export interface OtherRow { rule: string; sevCls: string; sevLab: string; title: string; ownerShort: string; ownerName: string }
export interface PageCards { title: string; n: number; sub: string; mine: Card[]; rest: OtherRow[] }

export interface TaskPart { a: string; short: string; state: 'ok' | 'pending' | 'nn'; can?: boolean; suffix?: string; doneText?: string; btn?: string }
export interface TaskView {
  id: string; rule: string; head: string; statusTag: Tag; dueTag: Tag | null; extra: Tag[]; over: boolean; action: string; sub: string;
  progress: { kind: 'parts' | 'data'; n: number; tot: number; text: string } | null; parts: TaskPart[];
}
export interface PropView { rule: string; action: string; title: string; steps: Tag[]; reason: string | null }

export interface OrderTable {
  rows: { i: number; key: string; country: string; fwd: string; planned: string; state: string; packed: string | null; lines: number; cartons: number }[];
  hideC: boolean; hideF: boolean; total: number; cap: number; more: string | null;
}
export interface ProjPanel { at: string; kind: 'inbound' | 'orders'; rows?: { asn: string; type: string; docked: string; passes: string }[]; chips?: Rich[]; lanes?: [string, number][] }

export interface Timeline { w0: number; w1: number; now: number; hs: [number, number][]; fs: [number, number][]; lms: [number, string][] }

export interface Frame<T = any> {
  t: number; at: number | null; mode: Mode; role: string; view: string; myOpen: number; cfg: Record<string, number>;
  version: number; timeline: Timeline; noPlan: string; data: T;
}

export interface ActionResult { toast: string | null; undo: Record<string, unknown> | null }

export interface OrderDetail {
  i: number; key: string; state: string; dn: string; lane: string; created: string; planned: string; packed: string; handed: string;
  lines: { line: number; sku: string; qty: string; carton: string; milk: boolean }[]; foot: string;
}
export interface AsnDetail {
  i: number; asn: string; ref: string | null; type: string; hv: boolean; got: boolean; bad: number; docked: string; received: string;
  lines: { line: number; sku: string; pack: string; exp: string; rcv: string; match: boolean | null; zone: string }[];
}
