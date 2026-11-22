"""Screen: Outbound (view id "outbound").
"""
from __future__ import annotations

from ..engine import Ctx, group_by, Snap, task_status
from ..fmt import fmt, hhmm
from .common import hbars, order_table, page_cards, page_kpis, proj_panel, R


def v_outbound(ctx: Ctx, snap: Snap, p: dict) -> dict:
    D, t = ctx.D, snap.t
    by = p.get("obBy") or "lane"
    seg = [["Past planned day", len(snap.past), "var(--late)"], ["Due today", len(snap.due), "var(--due)"],
           ["Planned later", len(snap.later), "var(--bar)"], ["No planned date", len(snap.noPlan), "var(--bar-2)"]]
    key_of = (lambda i: f"{D.o_country[i]}|{D.o_fwd[i]}") if by == "lane" else (lambda i: f"f|{D.o_fwd[i]}") if by == "fwd" else (lambda i: f"c|{D.o_country[i]}")
    lab_of = D.lane if by == "lane" else (lambda i: D.fwds[D.o_fwd[i]]) if by == "fwd" else (lambda i: D.countries[D.o_country[i]])
    live = [x for x in ctx.store.tasks if x["created"] <= t and x.get("kind") == "orders" and task_status(ctx, x, t)["st"] != "done"]
    rows = []
    for k, ids in group_by(snap.open, key_of):
        pp = [i for i in ids if D.o_has_plan[i] and D.o_planned[i] < snap.day]
        dd = [i for i in ids if D.o_has_plan[i] and D.o_planned[i] == snap.day]
        npk = sum(1 for i in dd if not D.o_has_ready[i] or D.o_ready[i] > t)
        pk = sum(1 for i in pp if D.o_has_ready[i] and D.o_ready[i] <= t)
        tk = next((x for x in live if any(key_of(i) == k for i in x["ids"])), None)
        rows.append({"k": k, "lab": lab_of(ids[0]), "ids": ids, "open": len(ids), "past": len(pp), "due": len(dd), "np": npk, "pk": pk,
                     "tk": tk["rule"] if tk else None})
    rows.sort(key=lambda r: (-r["past"], -r["open"]))
    top = rows[:12]
    mx = max([r["past"] for r in top] + [1])
    sel = next((r for r in rows if r["k"] == p.get("obSel")), top[0] if top else None)
    if top and top[0]["past"]:
        r0 = top[0]
        lead = R((r0["lab"], True), f" holds the most overdue orders ({fmt(r0['past'])}{', all packed: the hold-up is the pickup' if r0['pk'] == r0['past'] else ''}).")
    else:
        lead = R("No orders are past their planned day.")
    buckets = [["1 day late", 1, 1], ["2 days late", 2, 2], ["3–6 days late", 3, 6], ["7+ days late", 7, 99]]
    b = [[l, sum(1 for i in snap.past if a <= snap.day - D.o_planned[i] <= z)] for l, a, z in buckets]
    old = b[2][1] + b[3][1]
    cap = int(p.get("obCap") or 15)
    return {
        "lead": lead, "proj": proj_panel(ctx, snap, "outbound"), "kpis": page_kpis(ctx, snap, ["past", "notPacked", "topGroup", "onTime"], "outbound"),
        "total": fmt(len(snap.open)), "hh": hhmm(t), "seg": [[s[0], s[1], s[2], fmt(s[1])] for s in seg],
        "age": {"sub": R(f"Days past their planned day, at {hhmm(t)}. ", *((fmt(old), True), " have waited 3 days or more: chase these first.") if old else ("None has waited more than 2 days.",)),
                "bars": hbars(b, max([x[1] for x in b] + [1]))},
        "by": by, "groupHead": "Country · forwarder" if by == "lane" else "Forwarder" if by == "fwd" else "Country",
        "rows": [{"k": r["k"], "lab": r["lab"], "past": r["past"], "pastText": fmt(r["past"]), "frac": r["past"] / mx,
                  "due": fmt(r["due"]) if r["due"] else None, "np": fmt(r["np"]) if r["np"] else None, "tk": r["tk"], "sel": r is sel} for r in top],
        "groupsNote": f"Top {len(top)} of {fmt(len(rows))} groups. “Not packed” = due today with cartons still to pack.",
        "sel": {"lab": sel["lab"], "open": fmt(sel["open"]), "table": order_table(ctx, sel["ids"], t, cap, "cf" if by == "lane" else "f" if by == "fwd" else "c"),
                "moreBtn": ("more" if min(60, len(sel["ids"])) - cap > 0 else "fewer") if len(sel["ids"]) > cap else None} if sel else None,
        "cards": page_cards(ctx, snap, lambda c: c["rule"].startswith("OUT"), "Outbound cards"),
        "foot": f"{fmt(len(snap.noPlan))} open orders with no planned date are left out of past-due and due-today counts (DQ-02).",
    }
