"""Screen: Settings and limits (view id "settings").
"""
from __future__ import annotations

from ..engine import Ctx, Snap


def v_settings(ctx: Ctx, snap: Snap, p: dict) -> dict:
    from ..state import CFG_DEF, CFG_META
    can = ctx.role == "mgr" and ctx.can_act()
    return {"can": can, "rows": [{"k": k, "lab": lab, "unit": unit, "rule": rule, "min": mn, "max": mx, "step": st, "value": ctx.cfg[k],
                                  "def": CFG_DEF[k], "changed": ctx.cfg[k] != CFG_DEF[k]} for k, lab, unit, rule, mn, mx, st in CFG_META]}
