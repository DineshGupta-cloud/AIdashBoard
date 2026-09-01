# Backend: FastAPI options analysis

This directory contains the FastAPI API and its local JSON data source.

## Start

Run these commands from this directory:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install fastapi uvicorn pandas numpy ta
uvicorn app:app --reload
```

Visit <http://127.0.0.1:8000/docs> to inspect and call the API.

## Active application structure

- `app.py` creates the FastAPI app, enables CORS, and exposes NIFTY/search endpoints.
- `routes/home.py` provides `GET /options/advanced-advisor`.
- `routes/Bank_nifty.py` provides `GET /options/banknifty`.
- `data/` is the local source of truth for option-chain snapshots and the strategy playbook.

## Data files

| File or directory | Use |
| --- | --- |
| `option_chain.json` | NIFTY option-chain input |
| `options_playbook.json` | Strategy metadata and search source |
| `banknifty_option_chain.json` | Bank Nifty aggregate-chain input |
| `weights.json` | Constituent weights for Bank Nifty scoring |
| `stocks/*.json` | Individual constituent option-chain inputs |

Keep the existing JSON structure when refreshing a snapshot. The application assumes `records.underlyingValue` and `records.data`, with a `strikePrice` and optional `CE`/`PE` fields per row.

## Endpoints

See the root [README](../README.md) for the complete endpoint table and project runbook.

## Notes

- Launch from `python/`, not the repository root: `routes/home.py` currently uses relative `data/...` paths.
- `ta` is required by `app.py` for RSI calculation but is not presently listed in `requirements.txt`.
- `advisor.py` and the top-level `Bank_nifty.py` are not registered by the active app. The routed counterparts are used instead.

