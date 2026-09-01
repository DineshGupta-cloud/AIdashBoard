# Options RAG Project

A local options-analysis dashboard for NIFTY and Bank Nifty. The application combines a React dashboard with a FastAPI service that reads stored option-chain snapshots and produces open-interest, PCR, support/resistance, signal, and strategy-analysis views.

> **Important:** This project works from bundled JSON snapshots. It does not fetch live NSE data, place trades, or provide investment advice.

## What is included

- NIFTY option-chain analysis: spot, put-call ratio (PCR), support, resistance, max pain, and market view.
- Open-interest chart and option-chain table.
- Rule-based CE/PE signal scoring using OI, PCR, RSI, and VWAP-derived values.
- Advanced strategy advisor with RSI, EMA, MACD, VWAP, OI levels, and strategy legs.
- Keyword strategy search over the options playbook (labelled “RAG” in the UI; it is currently JSON keyword search, not LLM/embedding RAG).
- Bank Nifty weighted analysis using constituent-stock option-chain snapshots and `weights.json`.

## Architecture

```text
React + Vite frontend (port 5173)
        |
        | HTTP / Axios
        v
FastAPI backend (port 8000)
        |
        v
python/data/*.json option-chain and strategy snapshots
```

The frontend calls the backend at `http://127.0.0.1:8000`, configured in `react/react-frontend/src/API/api.js`.

## Prerequisites

- Python 3.10 or newer
- Node.js 20.19+ or 22.12+ (required by Vite 8)
- npm

## Run locally

Open two PowerShell terminals from the repository root.

### 1. Start the API

```powershell
cd python
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install fastapi uvicorn pandas numpy ta
uvicorn app:app --reload
```

The API is available at <http://127.0.0.1:8000>. Interactive API documentation is available at <http://127.0.0.1:8000/docs>.

### 2. Start the frontend

```powershell
cd react\react-frontend
npm install
npm run dev
```

Open the URL Vite prints, normally <http://localhost:5173>.

If PowerShell blocks `npm.ps1`, use `npm.cmd run dev` instead.

## Build the frontend

```powershell
cd react\react-frontend
npm run build
npm run preview
```

The production files are written to `react/react-frontend/dist/`.

## Repository layout

```text
python/
  app.py                    Main FastAPI app and NIFTY endpoints
  routes/home.py            Advanced advisor endpoint
  routes/Bank_nifty.py      Bank Nifty weighted-analysis endpoint
  data/
    option_chain.json       NIFTY option-chain snapshot
    banknifty_option_chain.json
    options_playbook.json   Strategy catalogue
    weights.json            Bank Nifty constituent weights
    stocks/                 Constituent option-chain snapshots

react/react-frontend/
  src/App.jsx               Dashboard and selected-view rendering
  src/API/api.js            Backend client
  src/Component/            Dashboard, chart, table, signal, and search UI
```

## API reference

| Endpoint | Purpose |
| --- | --- |
| `GET /` | Service health message |
| `GET /rag/search?q=<query>` | Keyword search in the strategy playbook |
| `GET /options/analyze` | NIFTY summary, levels, and recommended strategy |
| `GET /options/chart` | Nearby-strike CE/PE open-interest series |
| `GET /options/table` | Formatted option-chain table with OI state labels |
| `GET /options/signals` | Rule-based NIFTY CE/PE signal |
| `GET /options/advanced-advisor` | Extended indicators and strategy legs |
| `GET /options/banknifty` | Weighted Bank Nifty and constituent analysis |
| `GET/POST /alerts` | List or create persisted in-app alert rules |
| `PATCH/DELETE /alerts/{id}` | Enable, disable, or delete an alert rule |
| `POST /alerts/evaluate` | Evaluate rules against the current NIFTY snapshot |

## Dashboard views

- **Dashboard:** NIFTY summary, OI chart, and Bank Nifty overview.
- **Chart:** support/resistance visualization.
- **Strategy:** recommended strategy detail from the playbook.
- **Open Interest / Open table:** OI visualisation and the nearby-strike option chain.
- **Signals:** CE/PE signal score and reasons.
- **Advanced Advisor:** extended technical-indicator and strategy-leg response.
- **Search:** strategy playbook search.

## Data and limitations

All calculations use files under `python/data/`. To update analysis, replace those snapshots with data in the same JSON shape. The indicator price and volume sequences used by the signal/advisor endpoints are generated examples, not market candles. Review and validate calculations before using this project for any real trading decision.

## Live market-data ingestion

The backend now has an NSE ingestion provider, periodic market-hours refresh, SQLite snapshot history, cache freshness metadata, and bundled-JSON fallback. Copy `.env.example` values into your environment before starting the backend. Use `POST /market/refresh` to force a refresh, `GET /market/status` to see provider/cache/staleness status, and `GET /market/{symbol}/history` for stored snapshot timestamps. NSE access can change or be rate limited; for production use, implement a licensed broker adapter behind the provider interface.

## Development notes

- Start Uvicorn from the `python` directory; the advanced-advisor route currently uses paths relative to that directory.
- CORS is open to all origins for local development.
- `python/advisor.py` and `python/Bank_nifty.py` are older duplicate implementations and are not wired into `app.py`; active routes live under `python/routes/`.
- `python/requirements.txt` does not yet list `ta`, even though the API imports it. The backend setup command above installs it explicitly.
