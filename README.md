# DSV Warehouse Digital Twin (SUTD 40.318, Team 2)

A student design and prototype for DSV: a historical "digital twin" of one week of warehouse inbound and outbound operations. It covers event replay, ASN / order / line / carton visibility, planned-date and quantity reconciliation, Milkrun carton traceability, one staffing what-if and explainable rule-based recommendations.

> This is a course prototype on one week of anonymised data. It is not a live system and not a forecast.

## Working on this as a team

- **`WORK_SPLIT.md`**: the list of features and improvements. Put your name next to the ones you take.
- **`AGENTS.md`**: rules your AI assistant reads automatically (which files to touch, data rules, tests to run).
- Work on your own branch (`<name>/<topic>`) and merge through a pull request. Before merging, run the backend tests and the frontend build yourself (see *Running the app*). An automatic check on pull requests is still to do (F16).

## New to the repo? Start here

Use `git clone`, not `git init` (`git init` makes a new empty repo). You need Git, Python 3.10+ and Node.js 18+.

**1. One-time setup**

```bash
# Copy the repo to your computer
git clone https://github.com/aurrtherr/dsv-digital-twin-team2.git
cd dsv-digital-twin-team2

# Tell git who you are (once per computer)
git config --global user.name "Your Name"
git config --global user.email "you@example.com"

# Install the backend
cd backend
pip install -r requirements.txt
cd ..

# Install the frontend
cd frontend
npm install
cd ..
```

Before your first push, ask the repo owner to add you as a collaborator (Settings → Collaborators). Anyone can clone the repo, but only collaborators can push.

You do not need the Excel files: `backend/app/data/twin_data.json` is already in the repo.

**2. Run the app on your computer** (two terminals)

```bash
# Terminal 1: backend
cd backend
uvicorn app.main:app --reload --port 8000

# Terminal 2: frontend
cd frontend
npm run dev
```

Then open http://localhost:5173.

**3. Every time you work on something**

```bash
git checkout main
git pull                                   # get the latest main
git checkout -b yourname/topic             # e.g. alicia/inbound-chart

# ... make your changes ...

cd backend && python -m pytest -q && cd ..   # tests must pass
cd frontend && npm run build && cd ..        # build must pass

git add <the files you changed>
git commit -m "F5: add hourly receiving-queue chart"
git push -u origin yourname/topic
```

Open the link that `git push` prints and create a pull request on GitHub. When it is merged into `main`, the online demo updates by itself.

Pick your feature in `WORK_SPLIT.md` first, and only change the files listed for it. If you use an AI assistant, it follows `AGENTS.md`.

## What's in this repo

| Folder | What it holds |
|---|---|
| `backend/` | **The app's Python backend** (FastAPI): loads DSV's reports, replays the week, runs the rules, projections and staffing what-if, and keeps shared tasks. See `backend/README.md`. |
| `frontend/` | **The app's React + TypeScript frontend** (Vite): the 11 screens, calling the backend. See `frontend/README.md`. |
| `prototype_archive/twin.html` | The original single-file prototype (12 Nov 2026), kept as the reference the app was ported from. Open it in a browser, no install needed. |
| `notebooks/Feasure_Final.ipynb` | The data team's analysis notebook, as handed over (16 Nov). |
| `notebooks/Feasure_Final_review_16Nov.ipynb` | Review copy of the same notebook. Marks what is already in the prototype, what is not yet, and the code fixes (search the code for `REVIEW 16 Nov`). |
| `notebooks/DSV_Digital_Twin_Core.ipynb` | Earlier core analysis notebook (5 Nov), with self-checks and tidy-table exports. |
| `docs/team-doc/` | The team Google Doc, exported tab by tab on 23 Nov 2026: checklist, meeting notes, data handover pointers, DSV Q&A log, assumption log, strategy alignment, midterm feedback. **The Google Doc is the master copy.** |
| `docs/design/` | Detailed design (concept, architecture, journeys, interactions), the rule catalogue, and the slide design system. |
| `docs/analysis/` | Block-by-block explanation of the early analysis, and the DSV strategy check with sources. |
| `docs/course/` | Course materials copied into the team doc: DSV brief, course addendum (7 Nov), midterm guideline. |
| `docs/archive/` | Midterm Q&A prep. |
| `.github/workflows/pages.yml`, `render.yaml` | Online demo: frontend build for GitHub Pages and backend setup for Render (see *Online demo*). |
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

To check your changes before a pull request:

```bash
cd backend && python -m pytest -q   # plain `pytest` cannot find the app package
cd frontend && npm run build
```

How the work is split:
- **Backend (Python):** every calculation. That covers the data build from the Excel files, the replay snapshot at any hour, all 22 rules (IN, OUT, DQ, MGR), the Prevent cards, projections, task checks, KPIs, the what-if, and the shared state (tasks, decisions, limits). Each screen has its own file in `backend/app/screens/` (for example `inbound.py`), matching `frontend/src/views/Inbound.tsx`.
- **Frontend (TSX):** layout and interaction only. That covers the screens, charts, header timeline, dialogs, role switch, dark mode and the replay controls.

The port was checked against `prototype_archive/twin.html`:
- the backend's data build reproduces the prototype's embedded data exactly from DSV's raw Excel files;
- the rule cards match the original JavaScript at 119 sampled moments in the week;
- KPI values and projections also match;
- in a browser, the screens render the same as the original (same page height and visible text) for all 25 role and screen combinations checked.

## Online demo

For the team to check progress: **https://aurrtherr.github.io/dsv-digital-twin-team2/**

### Logging in

The app opens on a log-in screen. Each demo account opens the app as one role:

| Name | Password | Opens as |
|---|---|---|
| Aisha | `inboundsupervisor` | Inbound supervisor |
| John | `outboundsupervisor` | Outbound supervisor |
| Mei | `planner` | Planner |
| Raj | `operationsmanager` | Operations manager |
| Sam | `dataowner` | Data owner |

- Names ignore capital letters. The log-in is remembered in your browser until you press **Log out** in the header.
- The same accounts work when you run the app on your own computer.
- This is a prototype log-in, not real security: the accounts are in the public code (`backend/app/demo_users.py`). Do not use real passwords. To add or rename an account, edit that file.

### How it is hosted

- **Frontend** is on GitHub Pages. `.github/workflows/pages.yml` builds `frontend/` and publishes it every time something is merged into `main`, so the link always shows the latest `main`.
- **Backend** is on Render's free plan, set up from `render.yaml`. GitHub Pages can only host static files, so the Python backend has to run somewhere else. The frontend finds it through the repo variable `VITE_API_BASE` (Settings → Secrets and variables → Actions → Variables).
- The free backend goes to sleep after about 15 minutes with no use. The first load after that takes about a minute, so open the link early before a demo.
- Tasks, approvals and limits changed on the online demo are shared by everyone using it, and reset when the backend is redeployed.

One-time setup (only the repo owner needs to do this):
1. On render.com: New → Blueprint → this repo. Copy the service URL.
2. On GitHub: add the repo variable `VITE_API_BASE` = that URL, with no slash at the end.
3. On GitHub: Settings → Pages → Source → **GitHub Actions**.
4. Merge anything into `main`, or run the workflow by hand from the Actions tab.

### Updating the online demo

The online demo always shows what is on `main`. To update it, get your change merged into `main`; there is nothing else to deploy.

1. Push your branch and open a pull request (see *New to the repo? Start here*).
2. Merge the pull request into `main`.
3. Both halves update by themselves:
   - **Frontend:** GitHub Actions rebuilds it. Watch the **Actions** tab: when "Deploy frontend to GitHub Pages" turns green (about 2 minutes), the site is updated.
   - **Backend:** Render sees the new commit on `main` and redeploys it (about 2–5 minutes). Progress is on the Render dashboard → `dsv-twin-api` → **Events**.
4. Open the demo link and hard-refresh (**Cmd + Shift + R** on Mac, **Ctrl + Shift + R** on Windows) so your browser does not show the old version.

If it did not update:
- **Actions run is red:** open it to see the error. It is usually a TypeScript error, so run `cd frontend && npm run build` locally, fix it, and merge the fix.
- **Frontend to redeploy without a new commit:** Actions tab → **Deploy frontend to GitHub Pages** → **Run workflow** → branch `main`.
- **Backend to redeploy by hand** (only the repo owner can do this): Render dashboard → `dsv-twin-api` → **Manual Deploy** → **Deploy latest commit**.
- **Backend URL changed:** update the repo variable `VITE_API_BASE`, then run the frontend workflow again.

Redeploying the backend clears tasks, approvals and limit changes made on the online demo.

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

`prototype_archive/twin.html`, `backend/app/data/twin_data.json` and the notebook outputs contain values from the data, which is one more reason to keep the repo private.

## Team

| Week | Work | Who |
|---|---|---|
| W9 | Data analytics | Tigger, Regnars |
| W10 | Figma prototype | Esther, Hern |
| W11 | Working demo | Mk, Alicia |
| W12 | Presentation slides and buffer | All |
| W13 | Final presentation | All |

Only Claude, Gemini or Microsoft Copilot may be used with the DSV data (course addendum).
