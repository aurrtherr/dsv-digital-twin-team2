# DSV Warehouse Digital Twin (SUTD 40.318, Team 2)

A student design and prototype for DSV: a historical "digital twin" of one week of warehouse inbound and outbound operations. It covers event replay, ASN / order / line / carton visibility, planned-date and quantity reconciliation, Milkrun carton traceability, one staffing what-if and explainable rule-based recommendations.

> This is a course prototype on one week of anonymised data. It is not a live system and not a forecast.

## Working on this as a team

- **`WORK_SPLIT.md`**: the list of features and improvements. Put your name next to the ones you take.
- **`CLAUDE.md` / `AGENTS.md`**: rules your AI assistant reads automatically (which files to touch, data rules, tests to run). The two files are identical, so keep them the same.
- Work on your own branch (`<name>/<topic>`) and merge through a pull request. The automatic check (`.github/workflows/check.yml`) runs the backend tests and the frontend build on every pull request; merge only when it is green.

## What's in this repo

| Folder | What it holds |
|---|---|
| `backend/` | **The app's Python backend** (FastAPI): loads DSV's reports, replays the week, runs the rules, projections and staffing what-if, and keeps shared tasks. See `backend/README.md`. |
| `frontend/` | **The app's React + TypeScript frontend** (Vite): the 11 screens, calling the backend. See `frontend/README.md`. |
| `prototype/twin.html` | The original single-file prototype (12 Nov 2026), kept as the reference the app was ported from. Open it in a browser, no install needed. |
| `notebooks/Feasure_Final.ipynb` | The data team's analysis notebook, as handed over (16 Nov). |
| `notebooks/Feasure_Final_review_16Nov.ipynb` | Review copy of the same notebook. Marks what is already in the prototype, what is not yet, and the code fixes (search the code for `REVIEW 16 Nov`). |
| `notebooks/DSV_Digital_Twin_Core.ipynb` | Earlier core analysis notebook (5 Nov), with self-checks and tidy-table exports. |
| `docs/team-doc/` | The team Google Doc, exported tab by tab on 23 Nov 2026: checklist, meeting notes, data handover pointers, DSV Q&A log, assumption log, strategy alignment, midterm feedback. **The Google Doc is the master copy.** |
| `docs/design/` | Detailed design (concept, architecture, journeys, interactions), the rule catalogue, and the slide design system. |
| `docs/analysis/` | Block-by-block explanation of the early analysis, and the DSV strategy check with sources. |
| `docs/course/` | Course materials copied into the team doc: DSV brief, course addendum (7 Nov), midterm guideline. |
| `docs/archive/` | Midterm Q&A prep. |
| `data/` | Empty. Put the DSV Excel files here (they are not committed, see below). |

Some design and analysis docs were written before DSV's 11 Nov answers; each one has a note at the top saying what has changed since.

## Running the app (backend + frontend)

You need Python 3.10+ and Node.js 18+. Use two terminals.

```bash
# Terminal 1: backend on http://localhost:8000
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Terminal 2: frontend on http://localhost:5173
cd frontend
npm install
npm run dev
```

Open http://localhost:5173. The API docs are at http://localhost:8000/docs.

How the work is split:
- **Backend (Python):** every calculation. That covers the data build from the Excel files, the replay snapshot at any hour, all 22 rules (IN, OUT, DQ, MGR), the Prevent cards, projections, task checks, KPIs, the what-if, and the shared state (tasks, decisions, limits). Each screen has its own file in `backend/app/screens/` (for example `inbound.py`), matching `frontend/src/views/Inbound.tsx`.
- **Frontend (TSX):** layout and interaction only. That covers the screens, charts, header timeline, dialogs, role switch, dark mode and the replay controls.

The port was checked against `prototype/twin.html`:
- the backend's data build reproduces the prototype's embedded data exactly from DSV's raw Excel files;
- the rule cards match the original JavaScript at 119 sampled moments in the week;
- KPI values and projections also match;
- in a browser, the screens render the same as the original (same page height and visible text) for all 25 role and screen combinations checked.

## Running the notebooks

1. Put the DSV files in `data/`:
   - `Daily_Inbound_Report.xlsx`
   - `Daily_Outbound_Report.xlsx`
   - `Data_Glossary.xlsx` (used by the core notebook)
2. Install the packages: `pip install pandas numpy matplotlib openpyxl ipywidgets jupyter`
3. Open a notebook in Jupyter and choose **Run All**. The review and core notebooks look for `data/` next to the notebook first, then in the repo root.

`Feasure_Final.ipynb` (the original) still has a hard-coded `C:/Users/...` path in its first code cell. Use the review copy, or change that path.

## Key data rules (so everyone gets the same numbers)

- Add **+8 hours** to inbound Dock and GR times before comparing them with outbound times.
- An inbound line is **WMS ASN# + Ref Line# + Functional Packing** (DSV A5). With this key all 36,533 lines match their expected quantity.
- Count **Qty Shipped once per Order Key + Order Line Number**. It repeats on every carton row of a line, so adding up rows is about 49% too high. This is our working assumption until DSV answers Q25.
- The only exact inbound-to-outbound link is Milkrun: inbound LPN = outbound Carton ID (5,564 of 7,869 cartons).
- "Released after the planned date" is a signal to review, not proof of lateness (DSV, 11 Nov).
- Rule names follow the prototype: IN-xx (inbound), OUT-xx (outbound), DQ-xx (data checks), MGR-xx (manager).

## Data and privacy

The DSV reports are pre-anonymised and need no NDA, but they are client data shared for this course. Keep this repository **private** and add only team members, the professor and the TA. `.gitignore` keeps `*.xlsx` files out of commits.

`prototype/twin.html`, `backend/app/data/twin_data.json` and the notebook outputs contain values from the data, which is one more reason to keep the repo private.

## Team

| Week | Work | Who |
|---|---|---|
| W9 | Data analytics | Tigger, Regnars |
| W10 | Figma prototype | Esther, Hern |
| W11 | Working demo | Mk, Alicia |
| W12 | Presentation slides and buffer | All |
| W13 | Final presentation | All |

Only Claude, Gemini or Microsoft Copilot may be used with the DSV data (course addendum).
