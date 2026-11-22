"""Screen: Inbound (view id "inbound").
"""
from __future__ import annotations

import numpy as np

from ..engine import Ctx, DQ_WAIT, Snap
from ..fmt import day_label, day_n, day_of, fmt, hhmm, hrs, js_num, when
from .common import hbars, page_cards, page_kpis, proj_panel, R


def v_inbound(ctx: Ctx, snap: Snap, p: dict) -> dict:
    D, t = ctx.D, snap.t
    short = lambda m: f"{day_n(day_of(m)).split(' ')[0]} {hhmm(m)}"
    rows = []
    for i in snap.dock:
        a = D.asns[i]
        w = t - int(D.a_dock[i])
        u = ctx.usual_min(i)
        st = "dq" if w > DQ_WAIT else "over" if w > u else "ok"
        cap = max(u * 1.6, min(w, u * 3))
        docked = day_label(day_of(int(D.a_dock[i]))).split(" ", 1)[1] if w > 1440 * 6 else short(int(D.a_dock[i]))
        rows.append({"i": i, "asn": a[0], "hv": bool(D.hv[i]), "ref": a[5] or None, "docked": docked, "type": D.types[D.a_type[i]],
                     "lines": a[4], "st": st, "w": w, "u": u, "waited": hrs(w), "usual": js_num(u / 60),
                     "wf": min(100, 100 * w / cap), "uf": 100 * u / cap})
    rows.sort(key=lambda r: ((r["st"] == "dq"), -(r["w"] / r["u"])))
    over = [r for r in rows if r["st"] == "over"]
    dq = [r for r in rows if r["st"] == "dq"]
    if over:
        n = len(over)
        lead = R((f"{n} deliver{'ies are' if n > 1 else 'y is'} past the usual time.", True), " Start with the top row.")
    elif rows:
        lead = R(f"All {len(rows) - len(dq)} real waits are within their usual time." + (f" {len(dq)} record{'s look' if len(dq) > 1 else ' looks'} wrong and went to the data owner." if dq else ""))
    else:
        lead = R("Nothing is waiting at the dock.")
    m = D.a_has_gr & (D.a_gr > t - 1440) & (D.a_gr <= t)
    got = sorted([int(i) for i in np.flatnonzero(m)], key=lambda i: -int(D.a_gr[i]))
    rr = sorted([[ty, sum(1 for i in got if D.a_type[i] == k)] for k, ty in enumerate(D.types)], key=lambda r: -r[1])
    rr = [r for r in rr if r[1]]
    lst = [{"i": i, "asn": D.asns[i][0], "hv": bool(D.hv[i]), "ref": D.asns[i][5] or "–", "type": D.types[D.a_type[i]],
            "docked": when(int(D.a_dock[i])) if D.a_has_dock[i] else "—", "received": when(int(D.a_gr[i])), "lines": D.asns[i][4]} for i in got[:60]]
    return {
        "lead": lead, "proj": proj_panel(ctx, snap, "inbound"), "kpis": page_kpis(ctx, snap, ["dock", "dockOver", "linesIn", "stuck"], "inbound"),
        "rows": rows, "got": fmt(len(got)),
        "byType": hbars([[f"{r[0]} · usual {js_num(D.usual[r[0]])} h", r[1]] for r in rr], max([r[1] for r in rr] + [1]), "acc"),
        "list": lst, "cards": page_cards(ctx, snap, lambda c: c["rule"].startswith("IN") or c["rule"] == "DQ-03", "Inbound cards"),
        "foot": f"No shipment ref shown = DSV’s report has none for that delivery (usual for Normal deliveries). {fmt(D.dq['asns_no_dock'])} ASNs have no dock time and never show here (DQ-07).",
    }
