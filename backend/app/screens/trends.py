"""Screen: Trends (view id "trends").
"""
from __future__ import annotations

import numpy as np

from ..engine import Ctx, Snap
from ..fmt import day_label, day_n, fmt, js_num, pct, to_fixed
from .common import accuracy, avg, bars_spec, hbars, page_cards, R, STAT


def v_trends(ctx: Ctx, snap: Snap, p: dict) -> dict:
    D, cfg = ctx.D, ctx.cfg
    wkend = bool(p.get("trWk"))
    all_d = list(D.late_by_day.keys())
    days = [d for d in all_d if wkend or D.late_by_day[d][0] >= 100]
    sm = [d for d in all_d if D.late_by_day[d][0] >= 100]
    tot = sum(D.late_by_day[d][0] for d in sm)
    late = sum(D.late_by_day[d][1] for d in sm)
    avg_l = 100 * late / tot
    tgt = 100 - cfg["ontime"]
    miss = [d for d in sm if 100 * D.late_by_day[d][1] / D.late_by_day[d][0] > tgt]
    worst = sorted(sm, key=lambda d: -D.late_by_day[d][1] / D.late_by_day[d][0])[0] if sm else None
    dn = lambda d: day_n(int(d[8:]) - 1)
    rows = []
    for d in days:
        n, l = D.late_by_day[d]
        v = 100 * l / n
        rows.append({"label": dn(d), "sub": fmt(n) + " orders", "vals": [v], "faint": n < 100, "colors": ["var(--late)" if v > tgt else "var(--ok)"],
                     "tips": [to_fixed(v, 1) + "% late, " + fmt(n) + " orders"], "valLabels": [to_fixed(v, 0) + "%"]})
    ld = [d for d in D.out_lines_day if "2026-08-17" <= d <= "2026-08-23" and (wkend or d not in ("2026-08-22", "2026-08-23"))]
    rows2 = [{"label": dn(d), "vals": [D.in_lines_day.get(d, 0), D.out_lines_day.get(d, 0)], "hl": int(d[8:]) - 1 == snap.day,
              "colors": ["var(--bar-2)", "var(--bar)"], "tips": [fmt(D.in_lines_day.get(d, 0)) + " inbound lines", fmt(D.out_lines_day.get(d, 0)) + " outbound lines"]}
             for d in ld]
    wl = [D.in_lines_day.get(d, 0) + D.out_lines_day.get(d, 0) for d in ld]
    wavg = avg(wl[:5])
    peak = ld[wl.index(max(wl))] if wl else None
    by: dict[int, list[int]] = {}
    m = D.o_has_plan & (D.o_planned >= 16) & (D.o_planned <= 22)
    for i in np.flatnonzero(m):
        r = by.setdefault(int(D.o_fwd[i]), [0, 0])
        r[0] += 1
        if D.o_hand[i] // 1440 > D.o_planned[i]:
            r[1] += 1
    rk = sorted([(f, r) for f, r in by.items() if r[0] >= cfg["fwdMin"]], key=lambda x: -x[1][1])[:8]
    flag = [(f, r) for f, r in by.items() if r[0] >= cfg["fwdMin"] and 100 * r[1] / r[0] >= cfg["fwdLate"]]
    flag_late = sum(r[1] for _, r in flag)
    on_wk = 100 - avg_l
    stat = lambda lab, val, foot, st: {"lab": lab, "val": val, "foot": foot, "st": st, "icon": STAT[st][0], "word": STAT[st][1]}
    max_wl = max(wl) if wl else 0
    sub = R((f"{len(miss)} of {len(sm)} weekdays missed the {js_num(cfg['ontime'])}% on-time target", True),
            (f", worst {day_label(int(worst[8:]) - 1)}" if worst else "") + f". {len(flag)} forwarders account for {to_fixed(pct(flag_late, late), 0)}% of late orders. Week-level views; they don’t follow the replay time.")
    return {
        "sub": sub, "wkend": wkend,
        "stats": [stat("On time this week", to_fixed(on_wk, 1) + "%", f"Weekdays, {fmt(tot)} orders. Target {js_num(cfg['ontime'])}%.",
                       "ok" if on_wk >= cfg["ontime"] else "watch" if on_wk >= cfg["ontime"] - 10 else "act"),
                  stat("Days below target", f"{len(miss)} of {len(sm)}", ", ".join(dn(d) for d in miss) or "None", "act" if miss else "ok"),
                  stat("Forwarders to review", str(len(flag)), f"{js_num(cfg['fwdLate'])}%+ of their orders late ({js_num(cfg['fwdMin'])}+ orders)", "watch" if flag else "ok"),
                  stat("Busiest day", dn(peak) if peak else "–", f"{fmt(max_wl)} lines, {to_fixed(max_wl / wavg, 2)}× the weekday average" if peak else "",
                       "watch" if max_wl > cfg["load"] * wavg else "ok")],
        "accuracy": accuracy(ctx),
        "lateChart": bars_spec(rows, "Late rate by planned day", 110, [0, 25, 50, 75, 100], lambda g: f"{g}%", tgt,
                               f"Target: at most {js_num(tgt)}% late · week average {to_fixed(avg_l, 1)}%"),
        "lateNote": "Red = missed the target, green = met it." + (" Grey = weekend days with under 100 orders; their rates swing." if wkend else " Weekends hidden: under 100 orders a day."),
        "fwdBars": hbars([[f"{D.fwds[f]} · {to_fixed(pct(r[1], r[0]), 0)}%", r[1]] for f, r in rk], max([r[1] for _, r in rk] + [1])),
        "workChart": bars_spec(rows2, "Inbound and outbound lines per day", max([v for r in rows2 for v in r["vals"]] + [1]) * 1.12,
                               [0, 2500, 5000, 7500, 10000], lambda g: f"{g // 1000}k" if g else "0"),
        "cards": page_cards(ctx, snap, lambda c: c["rule"].startswith("MGR"), "Manager reviews"),
    }
