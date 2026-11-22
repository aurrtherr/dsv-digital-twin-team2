"""Loads the twin dataset once and keeps it in memory as numpy arrays.

Source order of preference:
1. app/data/twin_data.json (built by `python -m app.build_data`, or shipped with the repo)
2. the two Excel files in DATA_DIR (default: ../data), built on first start and cached to (1)
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

import numpy as np

HERE = Path(__file__).parent
JSON_PATH = Path(os.environ.get("TWIN_DATA_JSON", HERE / "data" / "twin_data.json"))
DATA_DIR = Path(os.environ.get("DATA_DIR", HERE.parent.parent / "data"))

T0 = 16 * 1440                 # Mon 17 Aug 00:00
T1 = 23 * 1440 + 23 * 60       # Mon 24 Aug 23:00
NULL = -(10 ** 9)              # stands in for "no value" in integer arrays


@dataclass
class Dataset:
    raw: dict
    extra: dict
    countries: list[str] = field(init=False)
    fwds: list[str] = field(init=False)
    dns: list[str] = field(init=False)
    types: list[str] = field(init=False)

    def __post_init__(self) -> None:
        D = self.raw
        self.countries, self.fwds, self.dns, self.types = D["countries"], D["fwds"], D["dns"], D["types"]
        O = D["orders"]
        col = lambda j: np.array([NULL if o[j] is None else o[j] for o in O], dtype=np.int64)
        self.o_created, self.o_planned, self.o_hand = col(0), col(1), col(2)
        self.o_country, self.o_fwd, self.o_dn, self.o_ready = col(3), col(4), col(5), col(6)
        self.o_lines, self.o_cartons = col(7), col(8)
        self.o_has_plan = self.o_planned != NULL
        self.o_has_ready = self.o_ready != NULL
        self.order_keys: list[str] = D["orderKeys"]
        self.n_orders = len(O)
        A = D["asns"]
        acol = lambda j: np.array([NULL if a[j] is None else a[j] for a in A], dtype=np.int64)
        self.asns = A
        self.a_type, self.a_dock, self.a_gr, self.a_lines = acol(1), acol(2), acol(3), acol(4)
        self.a_has_dock = self.a_dock != NULL
        self.a_has_gr = self.a_gr != NULL
        self.usual = D["usual"]
        self.a_usual_min = np.array([self.usual[self.types[t]] * 60 for t in self.a_type], dtype=float)
        C = D["cartons"]
        self.cartons = C
        ccol = lambda j: np.array([NULL if c[j] is None else c[j] for c in C], dtype=np.int64)
        self.c_dock, self.c_gr, self.c_cyc, self.c_created, self.c_hand = ccol(2), ccol(3), ccol(4), ccol(6), ccol(7)
        self.c_has_gr = self.c_gr != NULL
        self.dq = D["dq"]
        self.late_by_day: dict[str, list[int]] = D["lateByDay"]
        self.in_lines_day: dict[str, int] = D["inLinesDay"]
        self.out_lines_day: dict[str, int] = D["outLinesDay"]
        X = self.extra
        self.hv = np.array(X["HV"], dtype=bool)
        self.zones: list[str] = X["zones"]
        # received lines per ASN going to SEQ / HBS (MGR-03)
        z = {self.zones.index(n) for n in ("SEQ", "HBS") if n in self.zones}
        self.a_line_n = np.array([len(L) // 6 for L in X["AL"]], dtype=np.int64)
        self.a_line_seq = np.array([sum(1 for j in range(5, len(L), 6) if L[j] in z) for L in X["AL"]], dtype=np.int64)
        self.order_index = {k: i for i, k in enumerate(self.order_keys)}
        self.asn_index = {a[0]: i for i, a in enumerate(A)}
        self.milk_ids = {c[0] for c in C}

    # convenient labels
    def lane(self, i: int) -> str:
        return f"{self.countries[self.o_country[i]]} · {self.fwds[self.o_fwd[i]]}"

    def cartons_of(self, i: int) -> list[str]:
        c = self.extra["OC"][i]
        if len(c) == 2 and isinstance(c[0], str) and isinstance(c[1], list):
            return [c[0] + f"{n:03d}" for n in c[1]]
        return c


def _load_json() -> dict | None:
    if JSON_PATH.exists():
        with open(JSON_PATH) as f:
            return json.load(f)
    return None


@lru_cache(maxsize=1)
def get_dataset() -> Dataset:
    blob = _load_json()
    if blob is None:
        from .build_data import _load, build
        ib, ob = DATA_DIR / "Daily_Inbound_Report.xlsx", DATA_DIR / "Daily_Outbound_Report.xlsx"
        if not (ib.exists() and ob.exists()):
            raise FileNotFoundError(
                f"No twin data found. Put the DSV Excel files in {DATA_DIR} "
                f"or build {JSON_PATH} with `python -m app.build_data`.")
        data, extra = build(_load(ib), _load(ob))
        JSON_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(JSON_PATH, "w") as f:
            json.dump({"data": data, "extra": extra}, f, separators=(",", ":"))
        blob = {"data": data, "extra": extra}
    return Dataset(blob["data"], blob["extra"])
