// App-wide context: the current frame, metadata, UI settings and the actions screens can trigger.
import { createContext, useContext } from 'react';
import type { Card, Frame, Meta } from './types';

export interface UiState {
  t: number; at: number | null; role: string; view: string; theme: string | null;
  tlPast: string; tlNext: string; protoHidden: boolean; navOpen: Record<string, boolean>; othersOpen: boolean;
  obBy: string; obSel: string | null; obCap: number; arSel: string | null; traceQ: string; trWk: boolean; wi: number;
}

export interface App {
  meta: Meta;
  frame: Frame;
  ui: UiState;
  set: (patch: Partial<UiState>) => void;
  go: (view: string) => void;
  jump: (t: number) => void;
  openOrder: (i: number) => void;
  openAsn: (i: number) => void;
  lookup: (q: string) => void;
  trace: (q: string) => void;
  approve: (c: Card) => void;
  dismiss: (c: Card) => void;
  propose: (c: Card) => void;
  tick: (id: string, part: string, done: boolean) => void;
  newTask: () => void;
  seed: () => void;
  saveCfg: (values: Record<string, number>) => void;
  resetCfg: () => void;
  canAct: boolean;
}

export const AppCtx = createContext<App | null>(null);
export const useApp = (): App => {
  const a = useContext(AppCtx);
  if (!a) throw new Error('AppCtx missing');
  return a;
};
