"""Drill-downs: order and ASN detail dialogs, and the order/ASN lookup.
"""
from __future__ import annotations

from ..engine import Ctx
from ..fmt import day_label, fmt, when
from .common import order_state


def order_detail(ctx: Ctx, i: int) -> dict:
    D, t = ctx.D, ctx.view_t()
    L, cs = D.extra["OL"][i], D.cartons_of(i)
    rows = [L[j:j + 4] for j in range(0, len(L), 4)]
    st = order_state(ctx, i, t)
    return {"i": i, "key": D.order_keys[i], "state": st, "dn": D.dns[D.o_dn[i]], "lane": D.lane(i), "created": when(int(D.o_created[i])),
            "planned": day_label(int(D.o_planned[i])) if D.o_has_plan[i] else "none (DQ-02)",
            "packed": when(int(D.o_ready[i])) if D.o_has_ready[i] and D.o_ready[i] <= t else "not yet",
            "handed": when(int(D.o_hand[i])) if D.o_hand[i] <= t else "not yet",
            "lines": [{"line": r[0], "sku": D.extra["skus"][r[1]], "qty": fmt(r[2]), "carton": cs[r[3]], "milk": cs[r[3]] in D.milk_ids} for r in rows],
            "foot": f"{len(rows)} line{'s' if len(rows) > 1 else ''} · {len(cs)} carton{'s' if len(cs) > 1 else ''}. Lines and cartons come from DSV’s outbound report."}


def asn_detail(ctx: Ctx, i: int) -> dict:
    D, t = ctx.D, ctx.view_t()
    a, L = D.asns[i], D.extra["AL"][i]
    rows = [L[j:j + 6] for j in range(0, len(L), 6)]
    got = bool(D.a_has_gr[i] and D.a_gr[i] <= t)
    bad = sum(1 for r in rows if r[3] != r[4]) if got else 0
    return {"i": i, "asn": a[0], "ref": a[5] or None, "type": D.types[D.a_type[i]], "hv": bool(D.hv[i]), "got": got, "bad": bad,
            "docked": when(int(D.a_dock[i])) if D.a_has_dock[i] else "—", "received": when(int(D.a_gr[i])) if got else "not yet",
            "lines": [{"line": r[0], "sku": D.extra["skus"][r[1]], "pack": r[2], "exp": fmt(r[3]), "rcv": fmt(r[4]) if got else "—",
                       "match": None if not got else r[3] == r[4], "zone": D.zones[r[5]]} for r in rows]}


def lookup(ctx: Ctx, q: str) -> dict:
    D = ctx.D
    q = q.strip()
    qq = q.rjust(10, "0")
    for k in (q, qq):
        if k in D.order_index:
            return {"kind": "order", "i": D.order_index[k]}
    for k in (q, qq):
        if k in D.asn_index:
            return {"kind": "asn", "i": D.asn_index[k]}
    return {"kind": None, "msg": f"No order or ASN “{q}” in this week’s data"}
