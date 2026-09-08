from datetime import datetime, timezone
from pathlib import Path
from typing import Literal
from uuid import uuid4
import json
import logging

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from services.telegram_service import telegram_service
from services.market_data import market_data

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/alerts", tags=["alerts"])
DATA_DIR = Path(__file__).resolve().parent.parent / "data"
ALERT_STORE_FILE = DATA_DIR / "alerts.json"

Condition = Literal[
    "spot_above",
    "spot_below",
    "pcr_above",
    "pcr_below",
    "signal_is",
    "breakout_resistance",
    "breakdown_support",
]


class AlertRuleCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    condition: Condition
    threshold: float | None = None
    signal: Literal["BULLISH", "BEARISH", "NEUTRAL"] | None = None
    notify_telegram: bool = True


class AlertEnabledUpdate(BaseModel):
    enabled: bool


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_rules() -> list:
    if not ALERT_STORE_FILE.exists():
        return []
    with ALERT_STORE_FILE.open(encoding="utf-8") as file:
        return json.load(file)


def save_rules(rules: list) -> None:
    temp = ALERT_STORE_FILE.with_suffix(".tmp")
    with temp.open("w", encoding="utf-8") as file:
        json.dump(rules, file, indent=2)
    temp.replace(ALERT_STORE_FILE)


def market_snapshot() -> dict:
    """Build a market snapshot using live NSE data when available."""
    # Prefer live data from market_data service
    payload, meta = market_data.payload("NIFTY")
    if not payload:
        # Fallback to bundled file
        option_chain_file = DATA_DIR / "option_chain.json"
        if not option_chain_file.exists():
            raise HTTPException(503, "No market data available")
        with option_chain_file.open(encoding="utf-8") as file:
            payload = json.load(file)

    records = payload.get("records", {}).get("data", [])
    spot = payload.get("records", {}).get("underlyingValue", 0)

    total_ce = sum(row.get("CE", {}).get("openInterest", 0) for row in records)
    total_pe = sum(row.get("PE", {}).get("openInterest", 0) for row in records)
    pcr = round(total_pe / total_ce, 2) if total_ce else 0

    nearby = [row for row in records if abs(row.get("strikePrice", 0) - spot) <= 1000]

    support_row = max(
        (row for row in nearby if row.get("strikePrice", 0) <= spot),
        key=lambda row: row.get("PE", {}).get("openInterest", 0),
        default=None,
    )
    resistance_row = max(
        (row for row in nearby if row.get("strikePrice", 0) >= spot),
        key=lambda row: row.get("CE", {}).get("openInterest", 0),
        default=None,
    )

    signal = "BULLISH" if pcr > 1.1 else "BEARISH" if pcr < 0.9 else "NEUTRAL"

    return {
        "spot": spot,
        "pcr": pcr,
        "signal": signal,
        "support": support_row["strikePrice"] if support_row else None,
        "resistance": resistance_row["strikePrice"] if resistance_row else None,
        "evaluatedAt": now_iso(),
        "dataSource": meta.get("source", "unknown"),
    }


def rule_matches(rule: dict, snapshot: dict) -> bool:
    condition = rule["condition"]
    threshold = rule.get("threshold")

    if condition == "spot_above":
        return threshold is not None and snapshot["spot"] > threshold
    if condition == "spot_below":
        return threshold is not None and snapshot["spot"] < threshold
    if condition == "pcr_above":
        return threshold is not None and snapshot["pcr"] > threshold
    if condition == "pcr_below":
        return threshold is not None and snapshot["pcr"] < threshold
    if condition == "signal_is":
        return snapshot["signal"] == rule.get("signal")
    if condition == "breakout_resistance":
        return (
            snapshot["resistance"] is not None
            and snapshot["spot"] > snapshot["resistance"]
        )
    if condition == "breakdown_support":
        return (
            snapshot["support"] is not None
            and snapshot["spot"] < snapshot["support"]
        )
    return False


@router.get("")
def list_alerts():
    return {"alerts": load_rules()}


@router.post("", status_code=status.HTTP_201_CREATED)
def create_alert(payload: AlertRuleCreate):
    if payload.condition in {"spot_above", "spot_below", "pcr_above", "pcr_below"} and payload.threshold is None:
        raise HTTPException(422, "This condition requires a threshold.")
    if payload.condition == "signal_is" and payload.signal is None:
        raise HTTPException(422, "Signal condition requires a signal value.")

    rule = {
        "id": str(uuid4()),
        "name": payload.name.strip(),
        "condition": payload.condition,
        "threshold": payload.threshold,
        "signal": payload.signal,
        "notify_telegram": payload.notify_telegram,
        "enabled": True,
        "createdAt": now_iso(),
        "lastTriggeredAt": None,
        "lastStatus": False,
    }
    rules = load_rules()
    rules.append(rule)
    save_rules(rules)
    return rule


@router.patch("/{alert_id}")
def update_alert_enabled(alert_id: str, payload: AlertEnabledUpdate):
    rules = load_rules()
    for rule in rules:
        if rule["id"] == alert_id:
            rule["enabled"] = payload.enabled
            rule["lastStatus"] = False
            save_rules(rules)
            return rule
    raise HTTPException(404, "Alert not found.")


@router.delete("/{alert_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_alert(alert_id: str):
    rules = load_rules()
    remaining = [rule for rule in rules if rule["id"] != alert_id]
    if len(remaining) == len(rules):
        raise HTTPException(404, "Alert not found.")
    save_rules(remaining)


@router.post("/evaluate")
def evaluate_alerts():
    """Evaluate all enabled alerts and send Telegram notifications for newly triggered ones."""
    try:
        snapshot = market_snapshot()
    except Exception as exc:
        logger.error("Failed to build market snapshot: %s", exc)
        raise HTTPException(503, f"Could not evaluate alerts: {exc}")

    rules = load_rules()
    triggered = []

    for rule in rules:
        active = rule.get("enabled", True) and rule_matches(rule, snapshot)

        # Only notify on rising edge (was False, now True)
        if active and not rule.get("lastStatus", False):
            rule["lastTriggeredAt"] = snapshot["evaluatedAt"]
            triggered.append({"alert": rule.copy(), "snapshot": snapshot})

            # Send Telegram if enabled for this rule
            if rule.get("notify_telegram", True):
                success = telegram_service.send_alert(rule, snapshot)
                if success:
                    logger.info("Telegram alert sent for: %s", rule.get("name"))
                else:
                    logger.warning("Failed to send Telegram for: %s", rule.get("name"))

        rule["lastStatus"] = active

    save_rules(rules)

    return {
        "snapshot": snapshot,
        "triggered": triggered,
        "triggered_count": len(triggered),
        "telegram_configured": telegram_service.enabled,
        "alerts": rules,
    }


@router.get("/telegram/status")
def telegram_status():
    """Check if Telegram is configured."""
    return {
        "configured": telegram_service.enabled,
        "message": (
            "Telegram is ready"
            if telegram_service.enabled
            else "Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in .env"
        ),
    }


@router.post("/telegram/test")
def test_telegram():
    """Send a test message to verify Telegram configuration."""
    if not telegram_service.enabled:
        raise HTTPException(
            400,
            "Telegram not configured. Add TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID to .env",
        )

    success = telegram_service.send_message(
        "✅ <b>AIdashBoard Test</b>\n\nSmart Alerts + Telegram is working correctly!"
    )

    if not success:
        raise HTTPException(500, "Failed to send test message. Check bot token and chat ID.")

    return {"success": True, "message": "Test message sent successfully"}
