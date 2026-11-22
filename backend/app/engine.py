"""The twin's calculations, ported from the single-file prototype (twin.html).

Everything here is plain Python + numpy and has no web code, so it can be tested
directly. A `Ctx` bundles one request: the dataset, the shared state (tasks, limits),
the simulated "now" (t), the moment being viewed (at) and the viewer's role.

Time is whole minutes since Sat 1 Aug 2026 00:00 (outbound clock). Day 16 = Mon 17 Aug.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from functools import lru_cache
from typing import Any, Callable

import numpy as np

from .dataset import NULL, T0, T1, Dataset, get_dataset
from .fmt import (day_label, day_n, day_of, dkey, fmt, hhmm, hrs, in_min, js_num, js_round, pct,
                  to_fixed, when)

WEEK = [16, 17, 18, 19, 20]   # Mon 17 – Fri 21
DQ_WAIT = 120 * 60            # a dock wait this long is treated as a data issue (DQ-03)

ROLES = {
    "in": {"name": "Inbound supervisor", "short": "Inbound sup."},
    "out": {"name": "Outbound supervisor", "short": "Outbound sup."},
    "plan": {"name": "Planner", "short": "Planner"},
    "mgr": {"name": "Operations manager", "short": "Ops manager"},
    "dq": {"name": "Data owner", "short": "Data owner"},
}
ASSIGN = {**ROLES, "floor": {"name": "Floor team (through its supervisor)", "short": "Floor team"}}
DATA_CHECK = {"shipped", "packed", "received", "linked"}


# ---------------------------------------------------------------- snapshot
@dataclass(frozen=True)
class Snap:
    t: int
    day: int
    open: tuple
    past: tuple
    due: tuple
    later: tuple
    noPlan: tuple
    notPacked: tuple
    pastPacked: int
    dock: tuple


@lru_cache(maxsize=4096)
def snapshot(t: int) -> Snap:
    D = get_dataset()
    day = day_of(t)
    open_m = (D.o_created <= t) & (D.o_hand > t)
    hp = D.o_has_plan
    past = open_m & hp & (D.o_planned < day)
    due = open_m & hp & (D.o_planned == day)
    later = open_m & hp & (D.o_planned > day)
    noplan = open_m & ~hp
    packed = D.o_has_ready & (D.o_ready <= t)
    dock = D.a_has_dock & (D.a_dock <= t) & (t < D.a_gr)
    ids = lambda m: tuple(int(i) for i in np.flatnonzero(m))
    return Snap(t, day, ids(open_m), ids(past), ids(due), ids(later), ids(noplan), ids(due & ~packed),
                int((past & packed).sum()), ids(dock))


def group_by(ids, key: Callable[[int], Any]) -> list[tuple[Any, list[int]]]:
    """Group ids by key; biggest group first, ties keep first-seen order (as in the JS)."""
    m: dict[Any, list[int]] = {}
    for i in ids:
        m.setdefault(key(i), []).append(i)
    return sorted(m.items(), key=lambda kv: -len(kv[1]))


# ---------------------------------------------------------------- request context
@dataclass
class Ctx:
    store: Any                         # state.Store
    t: int                             # simulated "now"
    at: int | None = None              # viewed moment (None = now)
    role: str = "out"
    D: Dataset = field(default_factory=get_dataset)
    _cache: dict = field(default_factory=dict)

    @property
    def cfg(self) -> dict:
        return self.store.cfg

    @property
    def mode(self) -> str:
        if self.at is None or self.at == self.t:
            return "now"
        return "past" if self.at < self.t else "next"

    def can_act(self) -> bool:
        return self.mode == "now"

    def view_t(self) -> int:
        return self.at if self.mode == "past" else self.t

    # ---- helpers used by many rules
    def usual_min(self, i: int) -> float:
        return float(self.D.a_usual_min[i])

    def covered(self, rule: str, t: int) -> set:
        s: set = set()
        for x in self.store.tasks:
            if x["rule"] == rule and x["created"] <= t:
                s.update(x["ids"])
        for x in self.store.dismissed:
            if x["rule"] == rule and x["created"] <= t:
                s.update(x["ids"])
        return s


# ---------------------------------------------------------------- rules
def _key(c: dict, prefix: str = "") -> str:
    return prefix + c["rule"] + "|" + ",".join(str(i) for i in c["ids"][:3]) + "|" + str(len(c["ids"]))


def rules(ctx: Ctx, snap: Snap) -> list[dict]:
    ck = ("rules", snap.t)
    if ck in ctx._cache:
        return ctx._cache[ck]
    D, cfg, t, day = ctx.D, ctx.cfg, snap.t, snap.day
    h = (t % 1440) // 60
    cards: list[dict] = []
    cc = lambda i: D.countries[D.o_country[i]]
    fw = lambda i: D.fwds[D.o_fwd[i]]

    def free(rule, ids):
        c = ctx.covered(rule, t)
        return [i for i in ids if i not in c]

    def packed_share(ids):
        n = sum(1 for i in ids if D.o_has_ready[i] and D.o_ready[i] <= t)
        return "All" if n == len(ids) else to_fixed(pct(n, len(ids)), 1) + "%"

    # OUT-01 · largest past-due group (country × forwarder)
    gs = group_by(free("OUT-01", snap.past), lambda i: f"{D.o_country[i]}|{D.o_fwd[i]}")
    if gs:
        k, ids = gs[0]
        c, f = cc(ids[0]), fw(ids[0])
        cards.append(dict(rule="OUT-01", grp="OUT-01|" + k, sev="late", owner="out", kind="orders", check="shipped",
                          assign=["out"], title=f"{fmt(len(ids))} orders to {c} with {f} are past their planned day",
                          why=f"The largest past-due group right now. {packed_share(ids)} are already packed, so the hold-up is the pickup, not packing.",
                          action=f"Book one extra pickup slot with {f} for {c}.", doer="Transport desk books the pickup",
                          ids=ids, done="Order handed over"))
    # OUT-02 · created after the late-created hour on its planned day
    ids = free("OUT-02", [i for i in snap.due if D.o_created[i] >= day * 1440 + cfg["created"] * 60])
    if ids:
        cards.append(dict(rule="OUT-02", sev="due", owner="out", kind="orders", check="shipped", assign=["plan"],
                          title=f"{fmt(len(ids))} orders were created after {js_num(cfg['created'])}:00 on their planned day",
                          why="Orders created this late on their planned day were mostly released late in this week’s data.",
                          action="Find the earliest pickup for these orders and tell the customer team.", doer="Planner",
                          ids=ids, done="Order handed over"))
    # OUT-03 · from the cut-off, planned today and not handed over
    if h >= cfg["cut"]:
        ids = free("OUT-03", snap.due)
        if ids:
            cards.append(dict(rule="OUT-03", sev="late", owner="out", kind="orders", check="shipped", assign=["out"],
                              title=f"{fmt(len(ids))} orders planned for today are not handed over yet",
                              why=f"It is past {js_num(cfg['cut'])}:00. Without action these become late at midnight.",
                              action="Escalate: ship tonight or set a new date.", doer="Outbound supervisor escalates",
                              ids=ids, done="Handed over or new date set"))
    # OUT-04 · forwarders with many past-due orders
    gs = [g for g in group_by(free("OUT-04", snap.past), fw) if len(g[1]) >= cfg["fwd"]]
    if gs:
        ids = [i for g in gs for i in g[1]]
        n = len(gs)
        cards.append(dict(rule="OUT-04", sev="late", owner="out", kind="orders", check="shipped", assign=["out"],
                          title=f"{n} forwarder{'s have' if n > 1 else ' has'} {js_num(cfg['fwd'])} or more overdue orders",
                          why="Top: " + ", ".join(f"{g[0]} ({fmt(len(g[1]))})" for g in gs[:3]) + ".",
                          action="Call these forwarders about their overdue orders.", doer="Transport desk calls the forwarder",
                          ids=ids, done="Overdue count drops"))
    # OUT-05 · countries with many past-due orders
    gs = [g for g in group_by(free("OUT-05", snap.past), cc) if len(g[1]) >= cfg["ctry"]]
    if gs:
        ids = [i for g in gs for i in g[1]]
        n = len(gs)
        cards.append(dict(rule="OUT-05", sev="late", owner="out", kind="orders", check="shipped", assign=["plan", "floor"],
                          title=f"{n} countr{'ies have' if n > 1 else 'y has'} {js_num(cfg['ctry'])} or more overdue orders",
                          why="Top: " + ", ".join(f"{g[0]} ({fmt(len(g[1]))})" for g in gs[:3]) + ".",
                          action="Put these countries first in today’s plan.", doer="Planner", ids=ids, done="Overdue count drops"))
    # OUT-06 · due today, not fully packed (planner proposes, supervisor approves)
    ids = free("OUT-06", snap.notPacked)
    if ids:
        cards.append(dict(rule="OUT-06", sev="due", owner="out", proposer="plan", kind="orders", check="packed",
                          assign=["plan", "floor"], title=f"{fmt(len(ids))} orders due today are not fully packed",
                          why=f"Out of {fmt(len(snap.due))} orders due today. The rest are packed and waiting for pickup.",
                          action="Pack these first, then confirm today’s pickups.", doer="Packing team lead reorders work in the WMS",
                          ids=ids, done="Packed before pickup"))
    # IN-01 / DQ-03 · docked, not received
    c1, c3 = ctx.covered("IN-01", t), ctx.covered("DQ-03", t)
    for i in snap.dock:
        a = D.asns[i]
        w = t - int(D.a_dock[i])
        u = ctx.usual_min(i)
        ty = D.types[D.a_type[i]]
        if w > DQ_WAIT:
            if i not in c3:
                cards.append(dict(rule="DQ-03", sev="dq", owner="dq", kind="asns", check="label", assign=["dq", "in"],
                                  title=f"ASN {a[0]} shows {fmt(js_round(w / 60))} h at the dock",
                                  why=f"Docked {when(int(D.a_dock[i]))}, no receipt yet. A wait this long is far beyond any real wait (usual for {ty}: {js_num(u / 60)} h), so it is treated as a data issue and no floor alert is raised.",
                                  action="Confirm or close this record.", doer="Data owner, with the inbound supervisor",
                                  ids=[i], done="Record labelled"))
        elif w > u and i not in c1:
            cards.append(dict(rule="IN-01", sev="due", owner="in", kind="asns", check="received", assign=["in", "floor"],
                              title=f"ASN {a[0]} ({ty}) docked {hrs(w)} h ago, not received",
                              why=f"Usual time for {ty} is {js_num(u / 60)} h (90% of this week’s {ty} deliveries were received within it). {a[4]} lines.",
                              action="Check its receipt status within 1 h.", doer="Receiving team lead", ids=[i], done="Receipt posted"))
    # IN-04 · Milkrun carton received a while ago, no outbound order yet
    c = ctx.covered("IN-04", t)
    m = D.c_has_gr & (D.c_gr <= t - cfg["milk"]) & (D.c_created > t)
    ids = [int(i) for i in np.flatnonzero(m) if int(i) not in c]
    if ids:
        n_asn = len({D.cartons[i][1] for i in ids})
        cards.append(dict(rule="IN-04", sev="due", owner="in", kind="cartons", check="linked", assign=["in", "dq"],
                          title=f"{fmt(len(ids))} Milkrun cartons received {js_num(cfg['milk'] / 60)} h+ ago have no order yet",
                          why=f"From {n_asn} ASN(s). They cannot ship until an order exists.",
                          action="Create the outbound orders for these cartons.", doer="DSV admin creates the order",
                          ids=ids, done="Order linked to the carton"))
    # DQ-01 · planned before created / DQ-02 · no planned date
    ids = free("DQ-01", [i for i in snap.open if D.o_has_plan[i] and D.o_planned[i] < day_of(int(D.o_created[i]))])
    if ids:
        cards.append(dict(rule="DQ-01", sev="dq", owner="dq", kind="orders", check="label", assign=["dq", "plan"],
                          title=f"{fmt(len(ids))} open orders have a planned date before their order date",
                          why="They count as past due the moment they are created. Late figures on this screen keep them, labelled.",
                          action="Label these records; ask DSV which date is right.", doer="Data owner", ids=ids, done="Record labelled"))
    ids2 = free("DQ-02", snap.noPlan)
    if ids2:
        cards.append(dict(rule="DQ-02", sev="dq", owner="dq", kind="orders", check="label", assign=["dq"],
                          title=f"{fmt(len(ids2))} open orders have no planned date",
                          why="Mostly Milkrun to ABC. They cannot be past due or due today, so they are left out of those counts.",
                          action="Label these records; confirm with DSV how they are planned.", doer="Data owner", ids=ids2, done="Record labelled"))
    # MGR-01 · yesterday's on-time below target (only known once that day has ended)
    y = day - 1
    if 16 <= y <= 22:
        n, late = D.late_by_day[dkey(y)]
        on = pct(n - late, n)
        if n >= 100 and on < cfg["ontime"] and y not in ctx.covered("MGR-01", t):
            cards.append(dict(rule="MGR-01", sev="late", owner="mgr", kind="days", check="review", assign=["mgr"],
                              title=f"On-time for orders planned {day_label(y)} was {to_fixed(on, 1)}%",
                              why=f"{fmt(late)} of {fmt(n)} orders left on a later day than planned. Target: {js_num(cfg['ontime'])}% or better.",
                              action="Review pickup windows with the slowest forwarders.", doer="Operations manager", ids=[y],
                              done="Next week’s on-time figure"))
    # IN-02 · high-value delivery waiting longer than the limit
    c = ctx.covered("IN-02", t)
    ids = [i for i in snap.dock if D.hv[i] and t - D.a_dock[i] > cfg["hvWait"] * 60 and t - D.a_dock[i] <= DQ_WAIT and i not in c]
    if ids:
        cards.append(dict(rule="IN-02", sev="late", owner="in", kind="asns", check="received", assign=["floor"],
                          title=f"High-value delivery {D.asns[ids[0]][0]} has waited {hrs(t - int(D.a_dock[ids[0]]))} h at the dock",
                          why=f"Flagged high value in DSV’s inbound report. The limit for high-value deliveries is {js_num(cfg['hvWait'])} h.",
                          action="Receive it before other deliveries.", doer="Receiving team, through the inbound supervisor",
                          ids=ids, done="Receipt posted"))
    # IN-05 · returns (RMA) received in the last 24 h
    if "RMA" in D.types:
        rma = D.types.index("RMA")
        c = ctx.covered("IN-05", t)
        m = (D.a_type == rma) & D.a_has_gr & (D.a_gr <= t) & (D.a_gr > t - 1440)
        ids = [int(i) for i in np.flatnonzero(m) if int(i) not in c]
        if ids:
            cards.append(dict(rule="IN-05", sev="due", owner="in", kind="asns", check="manual", assign=["floor"],
                              title=f"{len(ids)} return{'s' if len(ids) > 1 else ''} (RMA) received in the last 24 h",
                              why="Returned goods can be damaged or wrong. They should be checked before they go to a shelf.",
                              action="Inspect these returns before putaway.", doer="Floor team, through the inbound supervisor",
                              ids=ids, done="Floor team ticks the inspection"))
    # MGR-02 · forwarders with a high late share (week so far)
    c = ctx.covered("MGR-02", t)
    by = fwd_late(day, t)
    gs = sorted([(f, r) for f, r in by if r[0] >= cfg["fwdMin"] and 100 * r[1] / r[0] >= cfg["fwdLate"] and f not in c],
                key=lambda x: -x[1][1])
    if gs:
        n = len(gs)
        cards.append(dict(rule="MGR-02", sev="late", owner="mgr", kind="fwds", check="review", assign=["mgr"],
                          title=f"{n} forwarder{'s' if n > 1 else ''} left {js_num(cfg['fwdLate'])}%+ of their orders late this week",
                          why="Top: " + ", ".join(f"{D.fwds[f]} ({fmt(r[1])} of {fmt(r[0])})" for f, r in gs[:3]) + ". A ranking, not a cause: check pickup windows first.",
                          action="Raise their pickup windows in the weekly review.", doer="Operations manager",
                          ids=[f for f, _ in gs], done="Next week’s late rate for these forwarders"))
    # MGR-03 · share of yesterday's receipts going to SEQ / HBS zones
    y = day - 1
    if 16 <= y <= 23 and y not in ctx.covered("MGR-03", t):
        m = D.a_has_gr & (D.a_gr // 1440 == y)
        n, k = int(D.a_line_n[m].sum()), int(D.a_line_seq[m].sum())
        if n >= 100 and 100 * k / n > cfg["zone"]:
            cards.append(dict(rule="MGR-03", sev="due", owner="mgr", kind="days", check="review", assign=["mgr", "in"],
                              title=f"{to_fixed(pct(k, n), 1)}% of {day_label(y)}’s received lines went to SEQ / HBS zones",
                              why=f"Above the {js_num(cfg['zone'])}% limit ({fmt(k)} of {fmt(n)} lines). These zones hold less, so space can run out.",
                              action="Check those zones have space for the next days.", doer="Operations manager with the inbound supervisor",
                              ids=[y], done="Reviewed with the inbound supervisor"))
    # MGR-04 · yesterday's workload above the limit
    y = day - 1
    if 16 <= y <= 22 and y not in ctx.covered("MGR-04", t):
        wk = [work(d) for d in WEEK]
        av = sum(wk) / len(wk)
        v = work(y)
        if v > cfg["load"] * av:
            cards.append(dict(rule="MGR-04", sev="due", owner="mgr", kind="days", check="review", assign=["mgr", "plan"],
                              title=f"{day_label(y)} carried {to_fixed(v / av, 2)}× the weekday average workload",
                              why=f"{fmt(v)} inbound + outbound lines against an average of {fmt(js_round(av))}. The limit is {js_num(cfg['load'])}×.",
                              action="Plan extra people for days like this; check the What-if.", doer="Operations manager with the planner",
                              ids=[y], done="Reviewed in the staffing plan"))
    for c in cards:
        c["key"] = _key(c)
    ctx._cache[ck] = cards
    return cards


def work(d: int) -> int:
    D = get_dataset()
    return D.in_lines_day.get(dkey(d), 0) + D.out_lines_day.get(dkey(d), 0)


@lru_cache(maxsize=1024)
def fwd_late(day: int, t: int) -> tuple:
    """Per forwarder [orders, late] for orders planned 17 Aug .. yesterday and handed over by t (first-seen order)."""
    D = get_dataset()
    m = D.o_has_plan & (D.o_planned >= 16) & (D.o_planned < day) & (D.o_hand <= t)
    idx = np.flatnonzero(m)
    out: dict[int, list[int]] = {}
    for i in idx:
        r = out.setdefault(int(D.o_fwd[i]), [0, 0])
        r[0] += 1
        if D.o_hand[i] // 1440 > D.o_planned[i]:
            r[1] += 1
    return tuple((f, tuple(r)) for f, r in out.items())


# ---------------------------------------------------------------- task checks
def done_time(ctx: Ctx, check: str, i: int):
    D = ctx.D
    if check == "shipped":
        return int(D.o_hand[i])
    if check == "packed":
        return int(D.o_hand[i]) if not D.o_has_ready[i] else int(min(D.o_ready[i], D.o_hand[i]))
    if check == "received":
        return None if not D.a_has_gr[i] else int(D.a_gr[i])
    if check == "linked":
        return int(D.c_created[i])
    return None


def part_done(x: dict, a: str, t: int) -> bool:
    p = x.get("parts") or {}
    return p.get(a) is not None and p[a] <= t


def task_status(ctx: Ctx, x: dict, t: int) -> dict:
    if t < x["created"]:
        return {"st": "future", "label": f"Created {when(x['created'])}", "n": 0, "tot": len(x["ids"])}
    if x["check"] == "manual":
        n = sum(1 for a in x["assign"] if part_done(x, a, t))
        if n == len(x["assign"]):
            return {"st": "done", "label": "Done: every part ticked", "n": n, "tot": len(x["assign"])}
        return {"st": "wait", "label": "In progress", "n": n, "tot": len(x["assign"])}
    if x["check"] == "label":
        return {"st": "done", "label": "Done in the twin: records labelled", "n": len(x["ids"]), "tot": len(x["ids"])}
    if x["check"] == "review":
        return {"st": "wait", "label": "Checked against next week’s data (not in this replay)", "n": 0, "tot": 1}
    n, last = 0, 0
    for i in x["ids"]:
        d = done_time(ctx, x["check"], i)
        if d is not None and d <= t:
            n += 1
            last = max(last, d)
    tot = len(x["ids"])
    left = tot - n
    if n == tot:
        at = -(-last // 60) * 60
        parts = x.get("parts") or {}
        acted = any(parts.get(a) is not None and parts[a] <= last for a in x["assign"])
        late = x.get("due") is not None and last > x["due"]
        lab = f"{'Resolved after action' if acted else 'Cleared before anyone acted'} · seen in data {when(at)}"
        return {"st": "done", "out": "action" if acted else "self", "late": late, "at": at, "n": n, "tot": tot, "label": lab}
    lab = f"Partly resolved · {fmt(left)} of {fmt(tot)} still open" if n else "Open · waiting for the data to show it resolved"
    return {"st": "wait", "n": n, "tot": tot, "left": left, "label": lab}


def floor_sup(x: dict) -> str:
    return "in" if x["rule"].startswith("IN") or x["rule"].startswith("DQ") else "out"


def can_tick(x: dict, a: str, role: str) -> bool:
    return a == role or (a == "floor" and floor_sup(x) == role)


def my_parts(x: dict, role: str) -> list[str]:
    return [a for a in x["assign"] if can_tick(x, a, role)]


def auto_closed(ctx: Ctx, x: dict, t: int) -> bool:
    return x["check"] in DATA_CHECK and t >= x["created"] and task_status(ctx, x, t)["st"] == "done"


def todo(ctx: Ctx, x: dict, role: str, t: int) -> bool:
    return t >= x["created"] and not auto_closed(ctx, x, t) and any(not part_done(x, a, t) for a in my_parts(x, role))


def same_before(ctx: Ctx, c: dict, t: int) -> list[dict]:
    return [x for x in ctx.store.tasks if c.get("grp") and x.get("grp") == c["grp"] and x["created"] <= t]


def prop_status(ctx: Ctx, p: dict, t: int) -> dict:
    tk = next((x for x in ctx.store.tasks if x.get("key") == p["key"] and p["created"] <= x["created"] <= t), None)
    if tk:
        return {"st": "approved", "task": tk}
    d = next((x for x in ctx.store.dismissed if x.get("key") == p["key"] and p["created"] <= x["created"] <= t), None)
    if d:
        return {"st": "dismissed", "d": d}
    return {"st": "waiting"}


def can_tick_any(x: dict, role: str) -> bool:
    return any(can_tick(x, a, role) for a in x["assign"])


def mine(x: dict, role: str) -> bool:
    return role in x["assign"] or ("floor" in x["assign"] and ((role == "in" and x["rule"].startswith("IN")) or
                                                               (role == "out" and x["rule"].startswith("OUT"))))


def outcome(ctx: Ctx, c: dict, t: int) -> dict:
    """In Past mode: what happened after this card was shown at t (looking back from now)."""
    now = ctx.t
    hit = lambda x: x["rule"] == c["rule"] and t < x["created"] <= now and (x.get("key") == c["key"] or any(i in c["ids"] for i in x["ids"]))
    tk = next((x for x in ctx.store.tasks if hit(x)), None)
    if tk:
        st = task_status(ctx, tk, now)
        return {"k": "approved", "text": f"✓ {'Acted on early' if tk.get('early') else 'Approved'} {when(tk['created'])} by the {ROLES[tk['by']]['short'].lower()} → {st['label']}"}
    d = next((x for x in ctx.store.dismissed if hit(x)), None)
    if d:
        return {"k": "dismissed", "text": f"⨯ Dismissed {when(d['created'])}: “{d['reason']}”"}
    if c["check"] in DATA_CHECK:
        last, ok = 0, True
        for i in c["ids"]:
            dt = done_time(ctx, c["check"], i)
            if dt is None or dt > now:
                ok = False
                break
            last = max(last, dt)
        if ok:
            return {"k": "self", "text": f"○ No one acted · cleared on its own at {when(-(-last // 60) * 60)}"}
        return {"k": "open", "text": "● No one acted · still open now"}
    return {"k": "open", "text": "● No one acted on this card"}


# ---------------------------------------------------------------- tiers and projections
TIERS = {"now": ["Act now", "The problem exists now"], "prevent": ["Prevent today", "Will happen if nothing changes"],
         "review": ["Review this week", "Patterns over days · 1 week of data"]}
TIER_ORDER = {"out": ["now", "prevent", "review"], "in": ["now", "prevent", "review"], "plan": ["prevent", "now", "review"],
              "mgr": ["review", "now", "prevent"], "dq": ["now", "prevent", "review"]}


def tier_of(c: dict, snap: Snap) -> dict:
    if c["rule"].startswith("MGR"):
        return {**c, "tier": "review"}
    if c["rule"] == "OUT-06" and snap.t % 1440 < 720:
        return {**c, "tier": "prevent", "trig": snap.day * 1440 + 720,
                "title": c["title"].replace("are not fully packed", "must be packed by 12:00")}
    return {**c, "tier": "now"}


def _num(x):
    return int(x) if isinstance(x, float) and x.is_integer() else x


def _avg(xs):
    xs = list(xs)
    return sum(xs) / (len(xs) or 1)


@lru_cache(maxsize=8192)
def ship_rate_due(t: int, horizon: int):
    """Share of orders planned for their day, open at this hour on earlier days, that left within the horizon."""
    D = get_dataset()
    day, off, rs = day_of(t), t % 1440, []
    for d in range(16, day):
        td = d * 1440 + off
        m = (D.o_created <= td) & (D.o_hand > td) & D.o_has_plan & (D.o_planned == d)
        n = int(m.sum())
        if n >= 20:
            rs.append(int((m & (D.o_hand <= td + horizon)).sum()) / n)
    return {"mean": _avg(rs), "min": min(rs), "max": max(rs), "n": len(rs)} if rs else None


def _count_past_shift(sn: Snap, d: int, sh: int) -> int:
    D = get_dataset()
    ids = np.fromiter(sn.open, dtype=np.int64) if sn.open else np.zeros(0, dtype=np.int64)
    return int((D.o_has_plan[ids] & (D.o_planned[ids] < d + sh)).sum())


def _count_due(sn: Snap, d: int) -> int:
    D = get_dataset()
    ids = np.fromiter(sn.open, dtype=np.int64) if sn.open else np.zeros(0, dtype=np.int64)
    return int((D.o_has_plan[ids] & (D.o_planned[ids] == d)).sum())


@lru_cache(maxsize=16384)
def ratio_est(t: int, T: int, kind: str, sh: int = 0):
    """On earlier days: count at the target hour ÷ count at this hour (only days already in the past)."""
    day, off, h, rs = day_of(t), t % 1440, T - t, []
    for d in range(16, day):
        td = d * 1440 + off
        if td + h > t:
            continue
        pick = (lambda sn: _count_past_shift(sn, d, sh)) if kind == "past" else (lambda sn: _count_due(sn, d))
        a, b = pick(snapshot(td)), pick(snapshot(td + h))
        if a >= 20:
            rs.append(b / a)
    return {"mean": _avg(rs), "min": min(rs), "max": max(rs), "n": len(rs)} if rs else None


def est_r(n: int, r) -> dict:
    if not r:
        return {"mid": None, "lo": 0, "hi": n, "worst": n, "days": 0}
    sp = max((r["max"] - r["min"]) / 2, 0.12 * r["mean"])
    return {"mid": js_round(n * r["mean"]), "lo": js_round(n * max(0, r["mean"] - sp)), "hi": js_round(n * (r["mean"] + sp)),
            "worst": n, "days": r["n"]}


def project(ctx: Ctx, snap: Snap, T: int) -> dict:
    ck = ("proj", snap.t, T)
    if ck in ctx._cache:
        return ctx._cache[ck]
    D, t, day = ctx.D, snap.t, snap.day
    dT = day_of(T)
    sh = dT - day
    pool = [i for i in snap.open if D.o_has_plan[i] and D.o_planned[i] < dT]
    past = est_r(len(pool), ratio_est(t, T, "past", sh))
    due = est_r(len(snap.due), ratio_est(t, T, "due")) if dT == day else None
    shipped = int((D.o_has_plan & (D.o_planned == day) & (D.o_hand <= t)).sum())
    Dn = len(snap.due)
    N = shipped + Dn
    r_end = ship_rate_due(t, (day + 1) * 1440 - t)
    ontime = None
    if N >= 100:
        ontime = {"lo": 100 * shipped / N, "hi": 100,
                  "mid": 100 * (shipped + Dn * r_end["mean"]) / N if r_end else None,
                  "mn": 100 * (shipped + Dn * r_end["min"]) / N if r_end else None,
                  "mx": 100 * (shipped + Dn * r_end["max"]) / N if r_end else None,
                  "shipped": shipped, "D": Dn, "N": N}
    dock_pass = sorted([{"i": i, "at": _num(int(D.a_dock[i]) + ctx.usual_min(i))} for i in snap.dock
                        if t < int(D.a_dock[i]) + ctx.usual_min(i) <= T and t - int(D.a_dock[i]) <= DQ_WAIT],
                       key=lambda x: x["at"])
    lanes = [[D.lane(ids[0]), len(ids)] for _, ids in
             group_by([i for i in pool if D.o_planned[i] >= day], lambda i: f"{D.o_country[i]}|{D.o_fwd[i]}")[:6]]
    res = {"T": T, "past": past, "due": due, "notPacked": len(snap.notPacked), "ontime": ontime, "dockPass": dock_pass, "lanes": lanes}
    ctx._cache[ck] = res
    return res


def upcoming(ctx: Ctx, snap: Snap) -> list[dict]:
    """"Prevent" cards: rules whose trigger can be predicted from what is known now."""
    D, cfg, t, day = ctx.D, ctx.cfg, snap.t, snap.day
    cards = []
    cut_t, mid_t = day * 1440 + cfg["cut"] * 60, (day + 1) * 1440
    if t < cut_t:
        c = ctx.covered("OUT-03", t)
        ids = [i for i in snap.due if i not in c]
        if ids:
            e = project(ctx, snap, cut_t)["due"]
            why = (f"At this week’s pace about {fmt(e['mid'])} ({fmt(e['lo'])}–{fmt(e['hi'])}) will still be here at {js_num(cfg['cut'])}:00 and need escalation."
                   if e and e["mid"] is not None else f"Up to {fmt(len(ids))} would need escalation at {js_num(cfg['cut'])}:00.")
            cards.append(dict(tier="prevent", trig=cut_t, rule="OUT-03", sev="due", owner="out", kind="orders", check="shipped", assign=["out"],
                              title=f"{fmt(len(ids))} orders due today must leave before {js_num(cfg['cut'])}:00", why=why,
                              action="Confirm today’s pickups now so these leave before the cut-off.", doer="Transport desk confirms pickups",
                              ids=ids, done="Order handed over"))
    c = ctx.covered("IN-01", t)
    soon = sorted([{"i": i, "at": _num(int(D.a_dock[i]) + ctx.usual_min(i))} for i in snap.dock
                   if t < int(D.a_dock[i]) + ctx.usual_min(i) <= t + 180 and t - int(D.a_dock[i]) <= DQ_WAIT and i not in c],
                  key=lambda x: x["at"])
    for x in soon[:3]:
        i = x["i"]
        a, ty = D.asns[i], D.types[D.a_type[i]]
        cards.append(dict(tier="prevent", trig=x["at"], rule="IN-01", sev="due", owner="in", kind="asns", check="received", assign=["in", "floor"],
                          title=f"ASN {a[0]} ({ty}) passes its usual time at {hhmm(int(x['at']))}",
                          why=f"Docked {when(int(D.a_dock[i]))}. 90% of {ty} deliveries are received within {js_num(ctx.usual_min(i) / 60)} h.",
                          action="Start receiving it before it goes over.", doer="Receiving team lead", ids=[i], done="Receipt posted"))
    c = ctx.covered("IN-04", t)
    milk = cfg["milk"]
    m = D.c_has_gr & (D.c_gr <= t) & (D.c_gr > t - milk) & (D.c_gr + milk <= t + 60) & (D.c_created > t)
    ids = [int(i) for i in np.flatnonzero(m) if int(i) not in c]
    if ids:
        first = int(min(D.c_gr[i] for i in ids) + milk)
        cards.append(dict(tier="prevent", trig=first, rule="IN-04", sev="due", owner="in", kind="cartons", check="linked", assign=["in", "dq"],
                          title=f"{fmt(len(ids))} Milkrun cartons pass {js_num(milk / 60)} h without an order from {hhmm(first)}",
                          why="They cannot ship until an order exists.", action="Get the outbound orders created now.",
                          doer="DSV admin creates the order", ids=ids, done="Order linked to the carton"))
    if 16 <= day <= 20 and day not in ctx.covered("MGR-01", t):
        p = project(ctx, snap, mid_t)["ontime"]
        if p and p["mid"] is not None and p["mn"] < cfg["ontime"]:
            cards.append(dict(tier="prevent", trig=mid_t, rule="MGR-01", sev="late", owner="mgr", kind="days", check="review", assign=["mgr", "out"],
                              title=f"Today’s on-time could end near {to_fixed(p['mid'], 0)}% ({to_fixed(p['mn'], 0)}–{to_fixed(p['mx'], 0)}%)",
                              why=f"Target {js_num(cfg['ontime'])}%. {fmt(p['shipped'])} of {fmt(p['N'])} orders planned today have left; {fmt(p['D'])} are still open.",
                              action="Ask the outbound supervisor to put today’s pickups first.", doer="Operations manager with the outbound supervisor",
                              ids=[day], done="Today’s on-time figure"))
    for c in cards:
        c["key"] = _key(c, "P|")
    return cards


def all_cards(ctx: Ctx, snap: Snap) -> list[dict]:
    ck = ("all", snap.t)
    if ck not in ctx._cache:
        ctx._cache[ck] = [tier_of(c, snap) for c in rules(ctx, snap)] + upcoming(ctx, snap)
    return ctx._cache[ck]


def next_card_for(ctx: Ctx, role: str, t: int):
    u, n = t + 60, 0
    while u <= T1 and n < 72:
        cs = [c for c in rules(ctx, snapshot(u)) if c["owner"] == role or c.get("proposer") == role]
        if cs:
            return {"t": u, "c": cs[0]}
        u += 60
        n += 1
    return None


# ---------------------------------------------------------------- KPIs
def kpi_fns(ctx: Ctx) -> dict[str, Callable[[Snap], float]]:
    D, cfg = ctx.D, ctx.cfg
    return {
        "past": lambda s: len(s.past),
        "notPacked": lambda s: len(s.notPacked),
        "due": lambda s: len(s.due),
        "packedDue": lambda s: 100 * (len(s.due) - len(s.notPacked)) / len(s.due) if s.due else 100,
        "topGroup": lambda s: (len(g[0][1]) if (g := group_by(s.past, lambda i: f"{D.o_country[i]}|{D.o_fwd[i]}")) else 0),
        "fwd20": lambda s: len([g for g in group_by(s.past, lambda i: int(D.o_fwd[i])) if len(g[1]) >= cfg["fwd"]]),
        "dock": lambda s: len(s.dock),
        "dockOver": lambda s: sum(1 for i in s.dock if s.t - D.a_dock[i] > ctx.usual_min(i)),
        "stuck": lambda s: sum(1 for i in s.dock if s.t - D.a_dock[i] > DQ_WAIT),
        "noPlan": lambda s: len(s.noPlan),
        "early": lambda s: sum(1 for i in s.open if D.o_has_plan[i] and D.o_planned[i] < day_of(int(D.o_created[i]))),
        "milkIn": lambda s: int((D.c_has_gr & (D.c_gr <= s.t) & (D.c_hand > s.t)).sum()),
    }


def last_weekday(day: int):
    D = get_dataset()
    for y in range(day - 1, 15, -1):
        r = D.late_by_day.get(dkey(y))
        if r and r[0] >= 100:
            return y
    return None


def on_time(y: int):
    r = get_dataset().late_by_day.get(dkey(y))
    return 100 * (r[0] - r[1]) / r[0] if r else None
