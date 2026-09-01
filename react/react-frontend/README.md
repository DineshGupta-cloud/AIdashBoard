# TradeDesk frontend

React 18 and Vite frontend for the Options RAG Project dashboard.

## Run

```powershell
npm install
npm run dev
```

The development server normally runs on <http://localhost:5173>. Start the FastAPI backend first, following the root [README](../../README.md).

If PowerShell prevents `npm` from running because of its script execution policy, use:

```powershell
npm.cmd run dev
```

## Scripts

| Command | Purpose |
| --- | --- |
| `npm run dev` | Start the Vite development server |
| `npm run build` | Create an optimised production build in `dist/` |
| `npm run preview` | Serve the production build locally |
| `npm run lint` | Run ESLint |

## Structure

```text
src/
  App.jsx               Root dashboard and view selector
  API/api.js            Axios calls to the FastAPI backend
  Component/            Reusable dashboard panels and charts
  assets/               Image and SVG assets
```

## Backend connection

The API base URL is set to `http://127.0.0.1:8000` in `src/API/api.js`. The backend must be available at that address for dashboard data to load. For a deployed environment, replace this hard-coded value with an environment-specific configuration.

## UI views

The sidebar exposes Dashboard, Chart, Strategy, Open Interest, Open table, Search, Signals, and Advanced Advisor. The Dashboard also includes the Bank Nifty weighted-analysis panel.

