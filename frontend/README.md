# Frontend (React + TypeScript)

The twin's screens, written in TSX with Vite. Every number comes from the Python backend; this folder only lays it out. The styling is the prototype's CSS, unchanged.

## Run it

Start the backend first (see `../backend/README.md`), then:

```bash
cd frontend
npm install
npm run dev          # http://localhost:5173  (calls to /api go to the backend on port 8000)
```

Other commands:

- `npm run typecheck`: TypeScript check only
- `npm run build`: production build into `dist/`. Serve it with `python -m app.dev_server --static ../frontend/dist` from `backend/`, or any static host that forwards `/api` to the backend.

To point at a backend elsewhere, set `VITE_API_BASE`, for example `VITE_API_BASE=http://192.168.1.20:8000 npm run dev`.

## Files

| Path | What it holds |
|---|---|
| `src/App.tsx` | Shell: prototype controls, header and timeline, sidebar, dialogs, toast; fetches one "frame" per screen render |
| `src/api.ts` | Calls to the backend |
| `src/types.ts` | Shapes of the backend's JSON |
| `src/ctx.ts` | App context: current frame, UI settings, actions |
| `src/views/` | One file per screen: Shift (Operations overview), AtRisk (Packing priorities), Outbound, Inbound, Trace, Trends, WhatIf, Checks, Rules, Settings, Tasks |
| `src/components/` | Rule cards and tasks, KPI cards, charts, header timeline, dialogs, order tables |
| `src/styles.css` | The prototype's design (colours, type, layout, dark mode) |

UI preferences (screen, role, simulated time, theme) are kept in the browser's localStorage. Tasks, decisions and limits are kept on the backend.
