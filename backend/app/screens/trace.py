"""Screen: Milkrun trace (view id "trace").
"""
from __future__ import annotations

from ..engine import Ctx, kpi_fns, Snap, snapshot, WEEK
from ..fmt import fmt, hhmm, pct, to_fixed, when
from .common import avg, kpi_card


def v_trace(ctx: Ctx, snap: Snap, p: dict) -> dict:
    D, t = ctx.D, snap.t
    C = D.cartons
    q = (p.get("traceQ") or "").strip()
    hits = [i for i, c in enumerate(C) if q and (c[0] == q or c[1] == q or c[5] == q or c[8] == q)]
    n_m = sum(1 for c in C if c[1])
    inside = int((D.c_has_gr & (D.c_gr <= t) & (D.c_hand > t)).sum())
    tot, miss = 35092, len(C) - n_m
    other = tot - len(C)
    K = kpi_fns(ctx)
    others = [d for d in WEEK if d != snap.day]
    kb = {"key": "milkIn", "lab": f"Milkrun cartons in the warehouse at {hhmm(t)}", "val": inside,
          "def": "Received, not yet handed over to a forwarder.", "mode": "info",
          "base": avg(K["milkIn"](snapshot(d * 1440 + t % 1440)) for d in others) if others else None, "baseLab": f"week avg at {hhmm(t)}"}
    res = None
    if q and hits:
        f = C[hits[0]]
        asn_set = {C[i][1] for i in hits if C[i][1]}
        ord_set = {C[i][5] for i in hits}
        pts = [x for x in [["Dock → receipt", f[2], f[3]], ["Receipt → Cyclone", f[3], f[4]], ["Cyclone → order", f[4], f[6]], ["Order → handover", f[6], f[7]]]
               if x[1] is not None and x[2] is not None and x[2] >= x[1]]
        dur = lambda m: f"{m} min" if m < 60 else to_fixed(m / 60, 1) + " h"
        total = sum(max(1, x[2] - x[1]) for x in pts)

        def step(lab, v, sub):
            st = "none" if v is None else "future" if v > t else ""
            return {"lab": lab, "st": st, "val": "not in data" if v is None else when(v), "sub": "after the replay time" if v is not None and v > t else (sub or "")}

        res = {"summary": f"{fmt(len(hits))} carton{'s' if len(hits) > 1 else ''} · {len(asn_set)} ASN · {len(ord_set)} order · first carton shown, {D.countries[f[10]]} via {D.fwds[f[9]]}",
               "time": {"total": dur(total), "parts": [{"lab": x[0], "w": max(1, x[2] - x[1]), "dur": dur(x[2] - x[1])} for x in pts]} if pts else None,
               "steps": [step("Docked", f[2], "ASN " + f[1] if f[1] else ""), step("Received", f[3], "goods receipt" if f[1] else "carton has no inbound match"),
                         step("Cyclone scan", f[4], "carton " + f[0]), step("Order created", f[6], "order " + f[5]), step("Handed over", f[7], D.fwds[f[9]])],
               "rows": [{"carton": C[i][0], "asn": C[i][1] or "—", "order": C[i][5], "received": when(C[i][3]), "cyclone": when(C[i][4]),
                         "handed": when(C[i][7]) if C[i][7] <= t else None} for i in hits[:40]],
               "more": f"Showing 40 of {fmt(len(hits))}." if len(hits) > 40 else None}
    return {"q": q, "examples": [["Carton", C[0][0]], ["ASN", "0000031762"], ["Order", C[50][5]]], "noHit": bool(q) and not hits,
            "coverage": {"nM": fmt(n_m), "pctText": to_fixed(pct(n_m, len(C)), 1), "nC": fmt(len(C)), "tot": fmt(tot), "miss": fmt(miss), "other": fmt(other),
                         "segs": [[n_m, "var(--ok)", "Traceable"], [miss, "var(--due)", "Milkrun, no inbound match"], [other, "var(--bar-2)", "Other flows, no shared ID"]]},
            "kpi": kpi_card(ctx, kb, snap), "result": res}
