"""Build the twin dataset from DSV's two Excel reports.

Output: one JSON file (twin_data.json) holding everything the engine needs.
Times are whole minutes since 2026-08-01 00:00 on the outbound clock. Inbound
Dock and GR times get +8 h (DSV / course rule). Days are counted from 1 Aug (day 0).

Run:  python -m app.build_data --inbound data/Daily_Inbound_Report.xlsx --outbound data/Daily_Outbound_Report.xlsx
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

BASE = pd.Timestamp("2026-08-01")
IB_SHIFT = 8 * 60  # minutes


def _load(path: Path) -> pd.DataFrame:
    df = pd.read_excel(path, dtype=str)
    for c in df.columns:
        df[c] = df[c].fillna("").astype(str).str.strip()
    return df


def _mins(s: pd.Series, shift: int = 0) -> pd.Series:
    t = pd.to_datetime(s.replace("", None), errors="coerce")
    m = np.ceil((t - BASE).dt.total_seconds() / 60)   # whole minutes, rounded up
    return (m + shift).astype("Int64")


def _day(s: pd.Series) -> pd.Series:
    t = pd.to_datetime(s.replace("", None), errors="coerce")
    return ((t - BASE).dt.days).astype("Int64")


def _v(x):
    """JSON-safe scalar (pandas NA -> None, numpy ints -> int)."""
    if x is None or (isinstance(x, float) and np.isnan(x)) or x is pd.NA:
        return None
    if isinstance(x, (np.integer,)):
        return int(x)
    if isinstance(x, (np.floating,)):
        return float(x)
    return x


def build(ib: pd.DataFrame, ob: pd.DataFrame) -> tuple[dict, dict]:
    # ---------------- outbound ----------------
    ob = ob.copy()
    ob["_created"] = _mins(ob["Orderdate Date & Time"])
    ob["_planned"] = _day(ob["Planned Post Date"])
    ob["_cday"] = _day(ob["Orderdate Date & Time"])
    ob["_hand"] = _mins(ob["Cargo Release Handover to Forwarder Date & Time"])
    ob["_cyc"] = _mins(ob["Receiving of Shipping Carton into Cyclone Date & Time"])
    ob["_pack"] = _mins(ob["Packing Confirmation Timestamp"])
    ob["_ready"] = ob["_pack"].fillna(ob["_cyc"])
    countries = ["?"] + sorted(x for x in ob["Country Code"].unique() if x)
    fwds = ["?"] + sorted(x for x in ob["Final Forwarder"].unique() if x)
    dns = sorted(ob["DN Type"].unique())
    ci = {c: i for i, c in enumerate(countries)}
    fi = {f: i for i, f in enumerate(fwds)}
    di = {d: i for i, d in enumerate(dns)}

    g = ob.groupby("Order Key", sort=True)
    od = g.agg(created=("_created", "min"), created_day=("_cday", "min"), planned=("_planned", "min"), hand=("_hand", "max"),
               country=("Country Code", "first"), fwd=("Final Forwarder", "first"), dn=("DN Type", "first"),
               ready=("_ready", "max"), ready_n=("_ready", "count"), rows=("_created", "size"),
               lines=("Order Line Number", "nunique"), cartons=("Carton ID", "nunique"))
    # an order is "packed" only when every row is ready
    od.loc[od["ready_n"] < od["rows"], "ready"] = pd.NA
    order_keys = list(od.index)
    orders = [[_v(r.created), _v(r.planned), _v(r.hand), ci.get(r.country, 0), fi.get(r.fwd, 0), di[r.dn],
               _v(r.ready), int(r.lines), int(r.cartons)] for r in od.itertuples()]

    # ---------------- inbound ----------------
    ib = ib.copy()
    ib["_dock"] = _mins(ib["Dock in Date & Time"], IB_SHIFT)
    ib["_gr"] = _mins(ib["GR Date & Time"], IB_SHIFT)
    types = sorted(ib["Shipment Type"].unique())
    ti = {t: i for i, t in enumerate(types)}
    key3 = ["WMS ASN#", "Ref Line#", "Functional Packing"]
    ga = ib.groupby("WMS ASN#", sort=True)
    ad = ga.agg(type=("Shipment Type", "first"), dock=("_dock", "min"), gr=("_gr", "max"),
                ref=("Shipment Ref", "first"))
    ad["lines"] = ib.drop_duplicates(key3).groupby("WMS ASN#").size().reindex(ad.index).fillna(0).astype(int)
    asns = [[k, ti[r.type], _v(r.dock), _v(r.gr), int(r.lines), r.ref] for k, r in zip(ad.index, ad.itertuples())]

    # usual dock-to-receipt time per type: P90 of completed ASNs, hours, 1 decimal
    w = (ad["gr"] - ad["dock"]).astype("float") / 60
    usual = {t: round(float(np.nanpercentile(w[ad["type"] == t].dropna(), 90)), 1) for t in types}

    # ---------------- Milkrun cartons (inbound LPN = outbound Carton ID) ----------------
    mo = ob[ob["DN Type"] == "Milkrun from ABC"]
    mi = ib[(ib["Shipment Type"] == "Milkrun to ABC") & (ib["LPN"] != "")]
    inl = mi.groupby("LPN").agg(asn=("WMS ASN#", "first"), dock=("_dock", "min"), gr=("_gr", "min"))
    cg = mo.groupby("Carton ID", sort=True).agg(cyc=("_cyc", "min"), order=("Order Key", "first"),
                                                created=("_created", "min"), hand=("_hand", "max"),
                                                lp=("LP", "first"), fwd=("Final Forwarder", "first"),
                                                country=("Country Code", "first"))
    cartons = []
    for cid, r in cg.iterrows():
        m = inl.loc[cid] if cid in inl.index else None
        cartons.append([cid, None if m is None else m["asn"], None if m is None else _v(m["dock"]),
                        None if m is None else _v(m["gr"]), _v(r["cyc"]), r["order"], _v(r["created"]),
                        _v(r["hand"]), r["lp"], fi.get(r["fwd"], 0), ci.get(r["country"], 0)])

    # ---------------- day-level series ----------------
    def dkey(d):
        return (BASE + pd.Timedelta(days=int(d))).strftime("%Y-%m-%d")

    lines3 = ib.groupby(key3).agg(gr=("_gr", "max")).dropna()
    in_day = (lines3["gr"] // 1440).value_counts().sort_index()
    inLinesDay = {dkey(d): int(n) for d, n in in_day.items() if 16 <= d <= 23}
    ol = ob.groupby(["Order Key", "Order Line Number"]).agg(h=("_hand", "max")).dropna()
    out_day = (ol["h"] // 1440).value_counts().sort_index()
    outLinesDay = {dkey(d): int(n) for d, n in out_day.items() if 16 <= d <= 23}
    late = od.dropna(subset=["planned"])
    lateByDay = {}
    for d in range(16, 23):
        x = late[late["planned"] == d]
        lateByDay[dkey(d)] = [int(len(x)), int(((x["hand"] // 1440) > x["planned"]).sum())]

    # ---------------- data-quality counts ----------------
    nop = od[od["planned"].isna()]
    dq = {
        "planned_before_created": int((od["planned"] < od["created_day"]).sum()),
        "no_planned_date": int(len(nop)),
        "no_planned_date_by_type": {k: int(v) for k, v in nop["dn"].value_counts().items()},
        "identical_rows": int(ob.duplicated().sum()),
        "shared_carton_ids": int((ob.groupby("Carton ID")["Order Key"].nunique() > 1).sum()),
        "rows_no_dock": int((ib["Dock in Date & Time"] == "").sum()),
        "asns_no_dock": int(ad["dock"].isna().sum()),
        "rows_no_zone": int((ib["Putaway Zone"] == "").sum()),
        "placeholder_sizes": int((ob["Carton Dimension"].str.upper().str.replace(" ", "") == "XX").sum()),
        "urgent_y_rows": int((ob["Urgent Flag"] == "Y").sum()),
        "outbound_rows": int(len(ob)),
    }

    data = {"base": "2026-08-01T00:00:00", "countries": countries, "fwds": fwds, "dns": dns, "types": types,
            "orders": orders, "orderKeys": order_keys, "asns": asns, "usual": usual, "cartons": cartons,
            "dq": dq, "lateByDay": lateByDay, "inLinesDay": inLinesDay, "outLinesDay": outLinesDay}

    # ---------------- detail tables (order lines, ASN lines) ----------------
    skus: dict[str, int] = {}
    si = lambda v: skus.setdefault(v, len(skus))
    oi = {k: i for i, k in enumerate(order_keys)}
    OL: list[list] = [[] for _ in order_keys]
    for r in ob.itertuples(index=False):   # every source row, as in DSV's report
        i = oi[r[1]]
        q = int(float(r[15])) if r[15] else 0
        OL[i].append([int(r[2]), si(r[9]), q, r[18]])
    zones: dict[str, int] = {}
    zi = lambda v: zones.setdefault(v or "?", len(zones))
    ai = {a[0]: i for i, a in enumerate(asns)}
    AL: list[list] = [[] for _ in asns]
    HV = [0] * len(asns)
    rcv = pd.to_numeric(ib["Qty Rcvd"], errors="coerce").fillna(0)
    agg = ib.assign(_r=rcv).groupby(key3, sort=True).agg(sku=("SKU", "first"), exp=("Qty Exp", "first"),
                                                            rcv=("_r", "sum"), zone=("Putaway Zone", "first"),
                                                            hv=("High Value Flag", "first")).reset_index()
    for r in agg.itertuples(index=False):
        i = ai[r[0]]
        AL[i].append([int(r[1]), si(r.sku), r[2], int(float(r.exp)) if r.exp else 0, int(r.rcv), zi(r.zone)])
        if r.hv == "Y":
            HV[i] = 1
    OC = []
    for i, ls in enumerate(OL):
        cs: list[str] = []
        for l in ls:
            if l[3] not in cs:
                cs.append(l[3])
            l[3] = cs.index(l[3])
        # compact form: [shared prefix, [3-digit suffixes]] when every carton ID is prefix + 3 digits
        if cs and all(len(c) == len(cs[0]) and c[:-3] == cs[0][:-3] and c[-3:].isdigit() for c in cs):
            OC.append([cs[0][:-3], [int(c[-3:]) for c in cs]])
        else:
            OC.append(cs)
        OL[i] = [x for l in ls for x in l]
    AL = [[x for l in ls for x in l] for ls in AL]
    extra = {"OC": OC, "skus": list(skus), "zones": list(zones), "OL": OL, "AL": AL, "HV": HV}
    return data, extra


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--inbound", default="data/Daily_Inbound_Report.xlsx")
    ap.add_argument("--outbound", default="data/Daily_Outbound_Report.xlsx")
    ap.add_argument("--out", default=str(Path(__file__).parent / "data" / "twin_data.json"))
    a = ap.parse_args()
    data, extra = build(_load(Path(a.inbound)), _load(Path(a.outbound)))
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    with open(a.out, "w") as f:
        json.dump({"data": data, "extra": extra}, f, separators=(",", ":"))
    print(f"wrote {a.out}: {len(data['orders'])} orders, {len(data['asns'])} ASNs, {len(data['cartons'])} Milkrun cartons")


if __name__ == "__main__":
    main()
