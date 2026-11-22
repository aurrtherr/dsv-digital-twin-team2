"""View models: one module per screen, each returning JSON-ready data for the React frontend.

The frontend only lays things out. Business logic (rules, statuses, projections, wording of
recommendations and comparisons) stays in the backend.

Where things live:
    common.py    shared building blocks (cards, tasks, KPI tiles, charts, projections, tables)
    timeline.py  header timeline shown on every screen
    details.py   order / ASN detail dialogs and the lookup box
    <screen>.py  one file per screen; its v_<screen>() function feeds frontend/src/views/<Screen>.tsx

To add a screen: create <screen>.py with a v_<screen>(ctx, snap, params) function, register it in
VIEWS below, add it to VIEW_NAMES / NAV_GROUPS in service.py, and add the matching .tsx view.
"""
from __future__ import annotations

from typing import Callable

from ..engine import Ctx, Snap
from .atrisk import v_atrisk
from .checks import v_checks
from .details import asn_detail, lookup, order_detail
from .inbound import v_inbound
from .outbound import v_outbound
from .rules import RULES, v_rules
from .settings import v_settings
from .shift import v_shift
from .tasks import v_tasks
from .timeline import TL_NEXT, TL_PAST, timeline, tl_window
from .trace import v_trace
from .trends import v_trends
from .whatif import v_whatif, whatif

VIEWS: dict[str, Callable[[Ctx, Snap, dict], dict]] = {
    "shift": v_shift, "atrisk": v_atrisk, "outbound": v_outbound, "inbound": v_inbound, "trace": v_trace, "trends": v_trends,
    "whatif": v_whatif, "checks": v_checks, "rules": v_rules, "settings": v_settings, "tasks": v_tasks,
}

__all__ = ["VIEWS", "RULES", "TL_NEXT", "TL_PAST", "asn_detail", "lookup", "order_detail", "timeline", "tl_window", "whatif"]
