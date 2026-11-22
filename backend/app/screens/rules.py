"""Screen: Rules catalogue (view id "rules").
"""
from __future__ import annotations

from ..engine import all_cards, Ctx, Snap
from ..fmt import hhmm, js_num
from .common import R


RULES = [
    ["IN-01", "Docked, not received in usual time", "in", "live"], ["IN-02", "High-value delivery waiting too long", "in", "live"],
    ["IN-03", "Received quantity differs", "in", "Checked: 0 of 36,533 lines flagged this week"], ["IN-04", "Milkrun carton, no order", "in", "live"],
    ["IN-05", "Returns (RMA) received", "in", "live"],
    ["OUT-01", "Past planned day (top group)", "out", "live"], ["OUT-02", "Created late on its planned day", "out", "live"],
    ["OUT-03", "Not handed over by the cut-off", "out", "live"], ["OUT-04", "Forwarder with many overdue", "out", "live"],
    ["OUT-05", "Country with many overdue", "out", "live"], ["OUT-06", "Due today, not fully packed (planner proposes)", "out", "live"],
    ["DQ-01", "Planned before created", "dq", "live"], ["DQ-02", "No planned date", "dq", "live"], ["DQ-03", "Dock with no receipt (120 h+)", "dq", "live"],
    ["DQ-04", "Contents mismatch", "dq", "Not built yet"], ["DQ-05", "Clock drift (+8 h)", "dq", "Resolved on load"],
    ["DQ-06", "Identical rows: label, never delete", "dq", "Count on Data checks"], ["DQ-07", "Missing fields", "dq", "Counts on Data checks"],
    ["MGR-01", "On-time below target", "mgr", "live"], ["MGR-02", "Forwarder with a high late share", "mgr", "live"],
    ["MGR-03", "Receipts to SEQ / HBS above limit", "mgr", "live"], ["MGR-04", "Workload above limit", "mgr", "live"],
]


def v_rules(ctx: Ctx, snap: Snap, p: dict) -> dict:
    cfg = ctx.cfg
    live: dict[str, int] = {}
    for c in all_cards(ctx, snap):
        live[c["rule"]] = live.get(c["rule"], 0) + 1
    j = js_num
    lim = {"IN-02": f"{j(cfg['hvWait'])} h", "IN-04": f"{j(cfg['milk'])} min", "OUT-02": f"after {j(cfg['created'])}:00", "OUT-03": f"{j(cfg['cut'])}:00",
           "OUT-04": f"{j(cfg['fwd'])}+ orders", "OUT-05": f"{j(cfg['ctry'])}+ orders", "MGR-01": f"< {j(cfg['ontime'])}%", "MGR-02": f"{j(cfg['fwdLate'])}%+ late",
           "MGR-03": f"> {j(cfg['zone'])}%", "MGR-04": f"> {j(cfg['load'])}×", "IN-01": "usual time", "DQ-03": "120 h"}
    grp = [["in", "Inbound · inbound supervisor approves"], ["out", "Outbound · outbound supervisor approves, planner proposes"],
           ["dq", "Data checks · labels only, no floor alert"], ["mgr", "Manager reviews · operations manager decides"]]
    n_live = sum(1 for r in RULES if r[3] == "live")
    firing = len(live)
    kpi_reg = [
        ["On time", "Share of orders planned for a day that were handed over on that calendar day", "Outbound sup., Ops manager", f"Target {j(cfg['ontime'])}% (proposed)"],
        ["Late", "Handed over on a later calendar day than the Planned Post Date (working definition WA-05)", "All", "Waits on DSV (PC-01)"],
        ["Past planned day", "Open orders whose planned day has passed", "Outbound sup., Planner, Ops manager", "Baseline: week average at that hour"],
        ["Due today, not packed", "Planned for today with cartons still to pack", "Outbound sup., Planner", "Baseline: week average at that hour"],
        ["Waiting longer than usual", "Docked, not received, past the time 90% of that delivery type finish within", "Inbound sup.", "Baseline: week average at that hour"],
        ["Workload", "Inbound + outbound lines in a day", "Ops manager, Planner", f"Limit {j(cfg['load'])}× the weekday average (proposed)"],
        ["Suspect records open", "Orders and deliveries caught by the data checks, not yet labelled", "Data owner", "Target: falling"],
    ]
    return {"lead": R((f"{n_live} of {len(RULES)} rules run on the data; {firing} {'is' if firing == 1 else 'are'} raising a card at {hhmm(snap.t)}.", True),
                      " A rule only raises a card; a person always approves or dismisses it. The operations manager sets the limits on Settings."),
            "groups": [{"lab": lab, "rules": [{"id": r[0], "name": r[1], "lim": lim.get(r[0], "–"), "live": r[3] == "live", "note": r[3], "now": live.get(r[0], 0)}
                                              for r in RULES if r[2] == o]} for o, lab in grp],
            "kpiReg": kpi_reg}
