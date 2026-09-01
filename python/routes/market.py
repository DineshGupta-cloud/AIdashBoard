from fastapi import APIRouter
from services.market_data import market_data
router=APIRouter(prefix="/market", tags=["market-data"])
@router.get("/status")
def status(): return market_data.status()
@router.post("/refresh")
def refresh(): return market_data.refresh_all(force=True)
@router.get("/{symbol}/history")
def history(symbol: str, limit: int=50): return {"symbol":symbol.upper(),"snapshots":market_data.store.history(symbol,min(max(limit,1),500))}
