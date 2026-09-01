from datetime import datetime, timezone
from pathlib import Path
from typing import Literal
from uuid import uuid4
import json

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

router = APIRouter(prefix="/alerts", tags=["alerts"])
DATA_DIR = Path(__file__).resolve().parent.parent / "data"
OPTION_CHAIN_FILE = DATA_DIR / "option_chain.json"
ALERT_STORE_FILE = DATA_DIR / "alerts.json"
Condition = Literal["spot_above", "spot_below", "pcr_above", "pcr_below", "signal_is", "breakout_resistance", "breakdown_support"]

class AlertRuleCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    condition: Condition
    threshold: float | None = None
    signal: Literal["BULLISH", "BEARISH", "NEUTRAL"] | None = None

class AlertEnabledUpdate(BaseModel):
    enabled: bool

def now_iso(): return datetime.now(timezone.utc).isoformat()

def load_rules():
    if not ALERT_STORE_FILE.exists(): return []
    with ALERT_STORE_FILE.open(encoding="utf-8") as file: return json.load(file)

def save_rules(rules):
    temp = ALERT_STORE_FILE.with_suffix(".tmp")
    with temp.open("w", encoding="utf-8") as file: json.dump(rules, file, indent=2)
    temp.replace(ALERT_STORE_FILE)

def market_snapshot():
    with OPTION_CHAIN_FILE.open(encoding="utf-8") as file: raw = json.load(file)
    records, spot = raw["records"]["data"], raw["records"]["underlyingValue"]
    total_ce = sum(row.get("CE", {}).get("openInterest", 0) for row in records)
    total_pe = sum(row.get("PE", {}).get("openInterest", 0) for row in records)
    pcr = round(total_pe / total_ce, 2) if total_ce else 0
    nearby = [row for row in records if abs(row["strikePrice"] - spot) <= 1000]
    support = max((row for row in nearby if row["strikePrice"] <= spot), key=lambda row: row.get("PE", {}).get("openInterest", 0), default=None)
    resistance = max((row for row in nearby if row["strikePrice"] >= spot), key=lambda row: row.get("CE", {}).get("openInterest", 0), default=None)
    signal = "BULLISH" if pcr > 1.1 else "BEARISH" if pcr < 0.9 else "NEUTRAL"
    return {"spot": spot, "pcr": pcr, "signal": signal, "support": support["strikePrice"] if support else None, "resistance": resistance["strikePrice"] if resistance else None, "evaluatedAt": now_iso()}

def rule_matches(rule, snapshot):
    condition, threshold = rule["condition"], rule.get("threshold")
    if condition == "spot_above": return threshold is not None and snapshot["spot"] > threshold
    if condition == "spot_below": return threshold is not None and snapshot["spot"] < threshold
    if condition == "pcr_above": return threshold is not None and snapshot["pcr"] > threshold
    if condition == "pcr_below": return threshold is not None and snapshot["pcr"] < threshold
    if condition == "signal_is": return snapshot["signal"] == rule.get("signal")
    if condition == "breakout_resistance": return snapshot["resistance"] is not None and snapshot["spot"] > snapshot["resistance"]
    if condition == "breakdown_support": return snapshot["support"] is not None and snapshot["spot"] < snapshot["support"]
    return False

@router.get("")
def list_alerts(): return {"alerts": load_rules()}

@router.post("", status_code=status.HTTP_201_CREATED)
def create_alert(payload: AlertRuleCreate):
    if payload.condition in {"spot_above", "spot_below", "pcr_above", "pcr_below"} and payload.threshold is None: raise HTTPException(422, "This condition requires a threshold.")
    if payload.condition == "signal_is" and payload.signal is None: raise HTTPException(422, "Signal condition requires a signal value.")
    rule = {"id": str(uuid4()), "name": payload.name.strip(), "condition": payload.condition, "threshold": payload.threshold, "signal": payload.signal, "enabled": True, "createdAt": now_iso(), "lastTriggeredAt": None, "lastStatus": False}
    rules = load_rules(); rules.append(rule); save_rules(rules)
    return rule

@router.patch("/{alert_id}")
def update_alert_enabled(alert_id: str, payload: AlertEnabledUpdate):
    rules = load_rules()
    for rule in rules:
        if rule["id"] == alert_id:
            rule["enabled"], rule["lastStatus"] = payload.enabled, False; save_rules(rules); return rule
    raise HTTPException(404, "Alert not found.")

@router.delete("/{alert_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_alert(alert_id: str):
    rules = load_rules(); remaining = [rule for rule in rules if rule["id"] != alert_id]
    if len(remaining) == len(rules): raise HTTPException(404, "Alert not found.")
    save_rules(remaining)

@router.post("/evaluate")
def evaluate_alerts():
    snapshot, rules, triggered = market_snapshot(), load_rules(), []
    for rule in rules:
        active = rule["enabled"] and rule_matches(rule, snapshot)
        if active and not rule.get("lastStatus", False):
            rule["lastTriggeredAt"] = snapshot["evaluatedAt"]; triggered.append({"alert": rule.copy(), "snapshot": snapshot})
        rule["lastStatus"] = active
    save_rules(rules)
    return {"snapshot": snapshot, "triggered": triggered, "alerts": rules}
