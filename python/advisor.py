from fastapi import APIRouter
from pydantic import BaseModel
import json

router = APIRouter()


# ==========================
# REQUEST MODEL
# ==========================

class OptionAnalysis(BaseModel):
    spot: float
    pcr: float
    maxPain: float
    support: list
    resistance: list
    view: str


# ==========================
# LOAD STRATEGIES
# ==========================

def load_strategies():
    with open("options_playbook.json", "r", encoding="utf-8") as f:
        return json.load(f)


# ==========================
# MARKET CLASSIFICATION
# ==========================

def classify_market(view, pcr):

    view = view.lower()

    if "range" in view:
        return "RANGE_BOUND"

    if "bullish" in view:
        return "BULLISH"

    if "bearish" in view:
        return "BEARISH"

    if pcr > 1.3:
        return "BULLISH"

    if pcr < 0.8:
        return "BEARISH"

    return "NEUTRAL"


# ==========================
# STRATEGY SCORING
# ==========================

def score_strategy(strategy, market_type):

    score = 0

    strategy_view = strategy.get("marketView", "").lower()

    if market_type == "RANGE_BOUND":

        if "neutral" in strategy_view:
            score += 90

        if "range" in strategy.get("whenToUse", "").lower():
            score += 10

    elif market_type == "BULLISH":

        if "bullish" in strategy_view:
            score += 100

    elif market_type == "BEARISH":

        if "bearish" in strategy_view:
            score += 100

    elif market_type == "NEUTRAL":

        if "neutral" in strategy_view:
            score += 100

    return score


# ==========================
# REASONS
# ==========================

def build_reasons(data):

    reasons = []

    reasons.append(f"PCR = {data.pcr}")
    reasons.append(f"Spot = {data.spot}")
    reasons.append(f"Max Pain = {data.maxPain}")
    reasons.append(f"View = {data.view}")

    return reasons


# ==========================
# ADJUSTMENT SUGGESTIONS
# ==========================

def get_adjustment_plan(strategy_name):

    adjustments = {

        "Iron Condor": {
            "bullishBreakout": [
                "Close Call Spread",
                "Convert To Bull Put Spread"
            ],
            "bearishBreakdown": [
                "Close Put Spread",
                "Convert To Bear Call Spread"
            ]
        },

        "Short Strangle": {
            "bullishBreakout": [
                "Roll Call Higher"
            ],
            "bearishBreakdown": [
                "Roll Put Lower"
            ]
        },

        "Bull Put Spread": {
            "bearishBreakdown": [
                "Close Position",
                "Roll Down"
            ]
        },

        "Bear Call Spread": {
            "bullishBreakout": [
                "Close Position",
                "Roll Higher"
            ]
        }
    }

    return adjustments.get(strategy_name, {})


# ==========================
# MAIN API
# ==========================

@router.post("/options/advisor")
def options_advisor(data: OptionAnalysis):

    strategies = load_strategies()

    market_type = classify_market(
        data.view,
        data.pcr
    )

    ranked = []

    for strategy in strategies:

        score = score_strategy(
            strategy,
            market_type
        )

        ranked.append({
            "score": score,
            "strategy": strategy
        })

    ranked.sort(
        key=lambda x: x["score"],
        reverse=True
    )

    best = ranked[0]

    return {

        "marketType": market_type,

        "recommendedStrategy": {
            "name": best["strategy"]["name"],
            "score": best["score"],
            "detail": best["strategy"],
            "reasons": build_reasons(data),
            "adjustments": get_adjustment_plan(
                best["strategy"]["name"]
            )
        },

        "alternatives": [
            {
                "name": r["strategy"]["name"],
                "score": r["score"]
            }
            for r in ranked[1:4]
        ]
    }