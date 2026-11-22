"""Screen: Packing priorities / at risk (view id "atrisk").
"""
from __future__ import annotations

from ..engine import all_cards, Ctx, group_by, Snap
from ..fmt import fmt, js_num
from .common import card_view, order_table, page_kpis, proj_panel, R


def v_atrisk(ctx: Ctx, snap: Snap, p: dict) -> dict:
    D, cfg, t, day = ctx.D, ctx.cfg, snap.t, snap.day
    due, np_ = list(snap.due), list(snap.notPacked)
    late = {i for i in due if D.o_created[i] >= day * 1440 + cfg["created"] * 60}
    cards = all_cards(ctx, snap)
    c6 = next((c for c in cards if c["rule"] == "OUT-06"), None)
    c2 = next((c for c in cards if c["rule"] == "OUT-02"), None)
    kf = lambda i: f"{D.o_country[i]}|{D.o_fwd[i]}"
    gs = []
    for k, ids in group_by(np_, kf):
        allg = [i for i in due if kf(i) == k]
        gs.append({"k": k, "ids": ids, "all": len(allg), "lab": D.lane(ids[0]), "late": sum(1 for i in ids if i in late)})
    sel = next((g for g in gs if g["k"] == p.get("arSel")), gs[0] if gs else None)
    if np_:
        lead = R((f"{fmt(len(np_))} of {fmt(len(due))} orders due today are not fully packed.", True), " Pack the top lanes first; the rest only need a pickup.")
    else:
        lead = R(("Everything due today is packed.", True), f" {fmt(len(due))} orders only need a pickup.")
    if late:
        lead += R(f" {len(late)} were created after {js_num(cfg['created'])}:00 and usually leave late (OUT-02).")
    return {"lead": lead, "proj": proj_panel(ctx, snap, "atrisk"), "kpis": page_kpis(ctx, snap, ["due", "notPacked", "packedDue", "past"], "atrisk"),
            "hasLate": bool(late),
            "lanes": [{"k": g["k"], "lab": g["lab"], "n": fmt(len(g["ids"])), "pk": g["all"] - len(g["ids"]), "all": g["all"],
                       "frac": (g["all"] - len(g["ids"])) / max(1, g["all"]), "late": g["late"] or None, "sel": g is sel} for g in gs[:12]],
            "sel": {"lab": sel["lab"], "n": len(sel["ids"]), "table": order_table(ctx, sel["ids"], t, 40, "cf")} if sel else None,
            "cards": [card_view(ctx, c, snap) for c in (c6, c2) if c]}
