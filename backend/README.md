# Backend (Python)

The twin's data and logic: it loads DSV's reports, replays the week, runs the rules, makes the projections and the staffing what-if, and keeps the shared tasks. The React frontend only displays what this API returns.

## Run it

```bash
cd backend
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

- API docs (try every endpoint in the browser): http://localhost:8000/docs
- Health check: http://localhost:8000/api/health

**No FastAPI available?** `python -m app.dev_server --port 8000` runs the same API with the standard library only. Add `--static ../frontend/dist` to serve the built frontend too, so the whole app runs from one command.

## Data

The backend reads `app/data/twin_data.json`, which is built from DSV's two Excel reports. It is committed so the app runs straight after cloning; it holds DSV data, so keep the repo private.

To rebuild it (for example after DSV sends a new extract):

```bash
python -m app.build_data --inbound ../data/Daily_Inbound_Report.xlsx --outbound ../data/Daily_Outbound_Report.xlsx
```

If the JSON file is missing, the backend builds it from `../data/*.xlsx` on first start.

Data rules applied (same as the notebooks): inbound Dock and GR times +8 h; inbound line = ASN + Ref Line# + Functional Packing; the only exact inbound-to-outbound link is Milkrun (LPN = Carton ID); times are whole minutes from 1 Aug 2026, rounded up.

## Files

| File | What it does |
|---|---|
| `app/build_data.py` | Excel reports → `twin_data.json` (orders, ASNs, Milkrun cartons, day totals, data-quality counts, line details) |
| `app/dataset.py` | Loads the data once into numpy arrays |
| `app/engine.py` | The calculations: snapshot at time t, the 22 rules (IN, OUT, DQ, MGR), "Prevent" cards, projections, task checks, KPIs |
| `app/views.py` | One function per screen: turns engine results into the JSON each React screen needs |
| `app/service.py` | Request handling and actions (approve, dismiss, propose, tick, new task, limits, undo), independent of the web framework |
| `app/main.py` | FastAPI routes |
| `app/dev_server.py` | Same routes with the standard library only |
| `app/state.py` | Shared state (tasks, dismissals, proposals, limits, change log) in `state.json` |
| `app/fmt.py` | Number and date formatting that matches the original prototype exactly |
| `tests/` | `pytest -q` checks headline numbers and the approve / limits flows |

## API

| Method | Path | Returns |
|---|---|---|
| GET | `/api/meta` | Roles, screens, nav groups, limit definitions, replay window |
| GET | `/api/frame?t=&role=&view=&at=` (+ screen options) | Everything one screen needs at simulated time `t` (minutes from 1 Aug), viewed at `at` (past or projection) |
| GET | `/api/order/{i}`, `/api/asn/{i}` | Order lines and cartons; ASN lines with expected vs received |
| GET | `/api/lookup?q=` | Finds an order key or ASN |
| GET | `/api/whatif?wi=20` | Staffing what-if for a volume change in % |
| POST | `/api/actions/{approve, dismiss, propose, tick, task, seed, cfg, cfg-reset, undo, reset}` | Changes shared state; returns a message and an undo token |

Shared state lives in `state.json` next to this README (set `TWIN_STATE_FILE` to move it). Everyone using the same backend sees the same tasks, which suits a team demo. Delete the file, or use "Reset demo", to start clean.
