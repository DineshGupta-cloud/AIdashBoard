from fastapi import APIRouter
import json
import os
from glob import glob
from services.market_data import market_data

router = APIRouter()

# =========================
# FIXED PATHS
# =========================
BASE_PATH = r"E:\OptionsRagProject\python\data"

STOCK_FOLDER = os.path.join(BASE_PATH, "stocks")
WEIGHTS_FILE = os.path.join(BASE_PATH, "weights.json")
BANKNIFTY_FILE = os.path.join(BASE_PATH, "banknifty_option_chain.json")

# =========================
# HELPERS
# =========================
def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def safe(v):
    return 0 if v is None else v

def nearest_row(rows, spot):
    valid_rows = [r for r in rows if r.get("strikePrice", 0) > 0]
    return min(valid_rows, key=lambda x: abs(x["strikePrice"] - spot))

# =========================
# STOCK ANALYSIS
# =========================
def analyze_stock(file_path):
    data = load_json(file_path)

    rows = data["records"]["data"]
    spot = data["records"]["underlyingValue"]

    row = nearest_row(rows, spot)

    ce = row.get("CE", {})
    pe = row.get("PE", {})

    ce_oi = safe(ce.get("openInterest"))
    pe_oi = safe(pe.get("openInterest"))

    ce_chg = safe(ce.get("changeinOpenInterest"))
    pe_chg = safe(pe.get("changeinOpenInterest"))

    score = 0
    reasons = []

    if pe_oi > ce_oi:
        score += 1
        reasons.append("PE OI strong")

    if pe_chg > ce_chg:
        score += 1
        reasons.append("PE writing strong")

    if ce_oi > pe_oi:
        score -= 1
        reasons.append("CE OI strong")

    if ce_chg > pe_chg:
        score -= 1
        reasons.append("CE writing strong")

    signal = "NEUTRAL"
    if score > 0:
        signal = "BULLISH"
    elif score < 0:
        signal = "BEARISH"

    return {
        "spot": spot,
        "nearestStrike": row["strikePrice"],
        "score": score,
        "signal": signal,
        "reasons": reasons
    }

# =========================
# BANKNIFTY ANALYSIS
# =========================
def analyze_banknifty():
    data = load_json(BANKNIFTY_FILE)
    data, _ = market_data.payload("BANKNIFTY", data)

    rows = data["records"]["data"]
    spot = data["records"]["underlyingValue"]

    max_ce = 0
    max_pe = 0
    ce_strike = 0
    pe_strike = 0
    total_ce = 0
    total_pe = 0

    for row in rows:
        strike = row["strikePrice"]

        ce_oi = safe(row.get("CE", {}).get("openInterest"))
        pe_oi = safe(row.get("PE", {}).get("openInterest"))

        total_ce += ce_oi
        total_pe += pe_oi

        if ce_oi > max_ce:
            max_ce = ce_oi
            ce_strike = strike

        if pe_oi > max_pe:
            max_pe = pe_oi
            pe_strike = strike

    pcr = round(total_pe / total_ce, 2) if total_ce else 0

    return {
        "spot": spot,
        "support": pe_strike,
        "resistance": ce_strike,
        "pcr": pcr
    }

# =========================
# API
# =========================
@router.get("/options/banknifty")
def openbanknifty():
    weights = load_json(WEIGHTS_FILE)

    files = {}
    for file_path in glob(os.path.join(STOCK_FOLDER, "*.json")) + glob(os.path.join(STOCK_FOLDER, "*.JSON")):
        symbol = os.path.basename(file_path).split(".")[0].upper()
        files[symbol] = file_path

    total_score = 0
    stock_report = []

    for item in weights:
        symbol = item["symbol"].upper()
        weight = item["weight"]

        if symbol in files:
            result = analyze_stock(files[symbol])
            weighted_score = result["score"] * weight
            total_score += weighted_score

            stock_report.append({
                "symbol": symbol,
                "weight": weight,
                "signal": result["signal"],
                "score": result["score"],
                "weightedScore": round(weighted_score, 2),
                "nearestStrike": result["nearestStrike"],
                "spot": result["spot"],
                "reasons": result["reasons"]
            })

    bn = analyze_banknifty()

    if total_score > 15:
        final_signal = "BULLISH"
    elif total_score < -15:
        final_signal = "BEARISH"
    else:
        final_signal = "SIDEWAYS"

    confidence = round(min(abs(total_score) * 1.8, 95), 2)

    return {
        "success": True,
        "banknifty": {
            "spot": bn["spot"],
            "signal": final_signal,
            "confidence": confidence,
            "pcr": bn["pcr"],
            "support": bn["support"],
            "resistance": bn["resistance"],
            "totalScore": round(total_score, 2)
        },
        "stocks": sorted(stock_report, key=lambda x: x["weight"], reverse=True)
    }
