// Small time helpers used for labels the frontend draws itself (timeline, dialogs).
// Time is whole minutes since Sat 1 Aug 2026 00:00, as in the backend.

const WD = ['Sat', 'Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri'];

export const dayOf = (t: number) => Math.floor(t / 1440);
export const dayLabel = (d: number) => `${WD[((d % 7) + 7) % 7]} ${d + 1} Aug`;
export const dayN = (d: number) => dayLabel(d).replace(' Aug', '');
export const hhmm = (t: number) => {
  const m = ((t % 1440) + 1440) % 1440;
  return String(Math.floor(m / 60)).padStart(2, '0') + ':' + String(Math.floor(m % 60)).padStart(2, '0');
};
export const when = (t: number | null | undefined) => (t == null ? '—' : `${dayLabel(dayOf(t))} ${hhmm(t)}`);
export const fmt = (n: number) => Number(n).toLocaleString('en-US');
