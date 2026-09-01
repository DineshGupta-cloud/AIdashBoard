from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
import json
import os
import json
import pandas as pd
import ta
from routes.Bank_nifty import router as openbanknifty
from routes.home import router as advisor_router
from routes.alerts import router as alerts_router
from routes.market import router as market_router
from services.market_data import market_data
import math
@asynccontextmanager
async def lifespan(application: FastAPI):
    await market_data.start()
    yield
    await market_data.stop()

app = FastAPI(lifespan=lifespan)

# Register Router
app.include_router(advisor_router)
app.include_router(openbanknifty)
app.include_router(alerts_router)
app.include_router(market_router)

# CORS for React later
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")



# ----------------------------
# Load JSON Helper
# ----------------------------
def load_json(file_name):
    path = os.path.join(DATA_DIR, file_name)
    with open(path, "r", encoding="utf-8") as f:
        bundled = json.load(f)
    symbol = {"option_chain.json": "NIFTY", "banknifty_option_chain.json": "BANKNIFTY"}.get(file_name)
    if symbol:
        payload, _ = market_data.payload(symbol, bundled)
        return payload
    return bundled


# ----------------------------
# Home API
# ----------------------------
@app.get("/")
def home():
    return {"message": "Python Options + RAG Service Running"}


# ----------------------------
# Home API
# ----------------------------
@app.get("/test")
def home():
    return {"message": "testing Routing with changes "}
# ----------------------------
# RAG Search API
# ----------------------------
@app.get("/rag/search")
def search_strategy(q: str):
    data = load_json("options_playbook.json")
    query = q.lower()

    result = []

    for item in data:
        text = (
            item["name"] + " " +
            item["category"] + " " +
            item["marketView"] + " " +
            " ".join(item["keywords"])
        ).lower()

        if query in text:
            result.append(item)

    return {
        "query": q,
        "count": len(result),
        "results": result
    }


# ----------------------------
# Option Chain Analysis API
# ----------------------------
@app.get("/options/analyze")
def analyze_options():
    raw = load_json("option_chain.json")
    strategies = load_json("options_playbook.json")

    records = raw["records"]["data"]
    spot = raw["records"]["underlyingValue"]

    rows = []
    total_ce_oi = 0
    total_pe_oi = 0

    for row in records:
        strike = row["strikePrice"]
        ce_oi = row["CE"]["openInterest"] if "CE" in row else 0
        pe_oi = row["PE"]["openInterest"] if "PE" in row else 0

        total_ce_oi += ce_oi
        total_pe_oi += pe_oi

        rows.append({
            "strike": strike,
            "ceOi": ce_oi,
            "peOi": pe_oi
        })

    # Only nearby strikes ±500
    nearby = [r for r in rows if abs(r["strike"] - spot) <= 1000]

    support = sorted(
        [r for r in nearby if r["strike"] <= spot],
        key=lambda x: x["peOi"],
        reverse=True
    )[:3]

    resistance = sorted(
        [r for r in nearby if r["strike"] >= spot],
        key=lambda x: x["ceOi"],
        reverse=True
    )[:3]

    best_support = support[0]["strike"] if support else None
    best_resistance = resistance[0]["strike"] if resistance else None

    pcr = round(total_pe_oi / total_ce_oi, 2) if total_ce_oi else 0
    max_pain = max(nearby, key=lambda x: x["ceOi"] + x["peOi"])["strike"]

    # Strategy Logic
    if best_support < spot < best_resistance:
        strategy_name = "Iron Condor" if pcr >= 1 else "Short Strangle"
        view = "Range Bound to Bullish" if pcr >= 1 else "Range Bound"
    elif spot >= best_resistance:
        strategy_name = "Bull Call Spread"
        view = "Bullish Breakout"
    else:
        strategy_name = "Bear Put Spread"
        view = "Bearish Breakdown"

    # Full strategy details
    strategy_detail = next(
        (s for s in strategies if s["name"].lower() == strategy_name.lower()),
        None
    )

    return {
        "spot": spot,
        "pcr": pcr,
        "maxPain": max_pain,
        "support": support,
        "resistance": resistance,
        "view": view,
        "bestStrategy": strategy_name,
        "strategyDetail": strategy_detail
    }


@app.get("/options/chart")
def openInterestChart():
    raw = load_json("option_chain.json")
    records = raw["records"]["data"]
    spot = raw["records"]["underlyingValue"]

    # Filter only nearby strikes (+/- 500)
    nearby = [
        r for r in records
        if abs(r["strikePrice"] - spot) <= 1000
    ]

    chart_data = []

    for row in nearby:
        strike = row["strikePrice"]
        ce_oi = row["CE"]["openInterest"] if "CE" in row else 0
        pe_oi = row["PE"]["openInterest"] if "PE" in row else 0

        chart_data.append({
            "strike": strike,
            "ceOi": ce_oi,
            "peOi": pe_oi
        })

    return {
        "spot": spot,
        "chartData": chart_data
    } 

@app.get("/options/table")
def openInterestTable():
    raw = load_json("option_chain.json")
    records = raw["records"]["data"]
    spot = raw["records"]["underlyingValue"]

    table = []
    total_ce_oi = 0
    total_pe_oi = 0

    strikes = []

    # -------------------------
    # Build raw option chain
    # -------------------------
    for row in records:
        strike = row.get("strikePrice")
        ce = row.get("CE", {})
        pe = row.get("PE", {})

        ce_oi = ce.get("openInterest", 0)
        pe_oi = pe.get("openInterest", 0)

        ce_chg = ce.get("changeinOpenInterest", 0)
        pe_chg = pe.get("changeinOpenInterest", 0)

        total_ce_oi += ce_oi
        total_pe_oi += pe_oi

        strikes.append(strike)

        # -------------------------
        # OI Build-up Logic
        # -------------------------
        def oi_state(change, oi):
            if change > 0 and oi > 0:
                return "LONG_BUILDUP"
            elif change < 0 and oi > 0:
                return "SHORT_BUILDUP"
            elif change < 0 and oi == 0:
                return "LONG_UNWIND"
            elif change > 0 and oi == 0:
                return "SHORT_COVERING"
            return "NEUTRAL"

        table.append({
            "strike": strike,
            "ce": {
                "oi": ce_oi,
                "changeOi": ce_chg,
                "ltp": ce.get("lastPrice", 0),
                "volume": ce.get("totalTradedVolume", 0),
                "oiState": oi_state(ce_chg, ce_oi)
            },
            "pe": {
                "oi": pe_oi,
                "changeOi": pe_chg,
                "ltp": pe.get("lastPrice", 0),
                "volume": pe.get("totalTradedVolume", 0),
                "oiState": oi_state(pe_chg, pe_oi)
            }
        })

    # -------------------------
    # Spot-based calculations
    # -------------------------
    atm_strike = min(strikes, key=lambda x: abs(x - spot))

    pcr = round(total_pe_oi / total_ce_oi, 2) if total_ce_oi else 0

    max_pain = max(
        table,
        key=lambda x: x["ce"]["oi"] + x["pe"]["oi"]
    )["strike"]

    # -------------------------
    # NSE-style filtering (±500 range)
    # -------------------------
    nearby = [
        r for r in table
        if abs(r["strike"] - spot) <= 1000
    ]

    # Sort strikes
    nearby = sorted(nearby, key=lambda x: x["strike"])

    # -------------------------
    # Add UI flags
    # -------------------------
    for r in nearby:
        r["isATM"] = (r["strike"] == atm_strike)
        r["distanceFromSpot"] = r["strike"] - spot

    # -------------------------
    # Market bias (simple NSE logic)
    # -------------------------
    if pcr > 1:
        trend = "BULLISH_BIAS"
    elif pcr < 0.8:
        trend = "BEARISH_BIAS"
    else:
        trend = "NEUTRAL"

    # -------------------------
    # Return NSE-style payload
    # -------------------------
    return {
        "spot": spot,
        "atmStrike": atm_strike,
        "maxPain": max_pain,
        "pcr": pcr,
        "trend": trend,
        "optionChainTable": nearby
    }


def calculate_rsi(close_prices):
    df = pd.DataFrame(close_prices, columns=["close"])
    df["rsi"] = ta.momentum.RSIIndicator(df["close"], window=14).rsi()
    return round(df["rsi"].iloc[-1], 2)


# --------------------------------------------------
# CALCULATE RSI
# Fix:
# Your old code used only 6 prices with RSI window=14.
# That returns NaN. Need at least 14+ candles.
# --------------------------------------------------
def calculate_rsi(close_prices):
    if len(close_prices) < 14:
        # fallback simple value
        return 50.0

    df = pd.DataFrame(close_prices, columns=["close"])
    rsi_series = ta.momentum.RSIIndicator(
        close=df["close"],
        window=14
    ).rsi()

    latest_rsi = rsi_series.iloc[-1]

    if pd.isna(latest_rsi):
        return 50.0

    return round(float(latest_rsi), 2)


# --------------------------------------------------
# SIGNAL API
# --------------------------------------------------
@app.get("/options/signals")
def openSignals():

    raw = load_json("option_chain.json")
    records = raw["records"]["data"]
    spot = raw["records"]["underlyingValue"]

    total_ce_oi = 0
    total_pe_oi = 0

    strikes = []
    ce_oi_map = {}
    pe_oi_map = {}

    # --------------------------------------------------
    # READ OPTION CHAIN
    # --------------------------------------------------
    for row in records:
        strike = row["strikePrice"]
        strikes.append(strike)

        ce_oi = row.get("CE", {}).get("openInterest", 0)
        pe_oi = row.get("PE", {}).get("openInterest", 0)

        ce_oi_map[strike] = ce_oi
        pe_oi_map[strike] = pe_oi

        total_ce_oi += ce_oi
        total_pe_oi += pe_oi

    # --------------------------------------------------
    # SAFETY CHECK
    # --------------------------------------------------
    if not strikes:
        return {
            "signal": "NO DATA"
        }

    # --------------------------------------------------
    # PCR
    # --------------------------------------------------
    pcr = round(total_pe_oi / total_ce_oi, 2) if total_ce_oi > 0 else 0

    # --------------------------------------------------
    # MAX OI LEVELS
    # --------------------------------------------------
    max_ce_strike = max(ce_oi_map, key=ce_oi_map.get)
    max_pe_strike = max(pe_oi_map, key=pe_oi_map.get)

    # --------------------------------------------------
    # BETTER MAX PAIN (closest heavy zone)
    # --------------------------------------------------
    max_pain = round((max_ce_strike + max_pe_strike) / 2)

    # --------------------------------------------------
    # RSI + VWAP SAMPLE DATA
    # Need 15 candles minimum
    # --------------------------------------------------
    prices = [
        spot - 90,
        spot - 80,
        spot - 70,
        spot - 60,
        spot - 50,
        spot - 40,
        spot - 30,
        spot - 20,
        spot - 10,
        spot - 5,
        spot,
        spot + 5,
        spot + 10,
        spot + 15,
        spot + 20
    ]

    rsi = calculate_rsi(prices)
    vwap = round(sum(prices) / len(prices), 2)

    # --------------------------------------------------
    # DEFAULT RESPONSE
    # --------------------------------------------------
    signal = "NO TRADE"
    reasons = []
    confidence = 0
    target = 0
    sl = 0
    strike = round(spot / 50) * 50

    score_ce = 0
    score_pe = 0

    # ==================================================
    # BUY CE LOGIC
    # ==================================================
    if pcr > 1.1:
        score_ce += 20
        reasons.append("PCR Bullish")

    if spot > vwap:
        score_ce += 20
        reasons.append("Above VWAP")

    if rsi > 50:
        score_ce += 20
        reasons.append("RSI Strong")

    if spot > max_ce_strike:
        score_ce += 25
        reasons.append("Breakout Above Max CE OI")

    if spot > max_pain:
        score_ce += 15
        reasons.append("Above Max Pain")

    # ==================================================
    # BUY PE LOGIC
    # ==================================================
    if pcr < 0.9:
        score_pe += 20

    if spot < vwap:
        score_pe += 20

    if rsi < 50:
        score_pe += 20

    if spot < max_pe_strike:
        score_pe += 25

    if spot < max_pain:
        score_pe += 15

    # ==================================================
    # FINAL DECISION
    # ==================================================
    if score_ce >= 60 and score_ce > score_pe:
        signal = "BUY CE"
        confidence = score_ce
        target = 30
        sl = 15
        strike = round(spot / 50) * 50

    elif score_pe >= 60 and score_pe > score_ce:
        signal = "BUY PE"
        confidence = score_pe
        target = 30
        sl = 15
        strike = round(spot / 50) * 50

    # ==================================================
    # RESPONSE
    # ==================================================
    return {
        "index": "NIFTY",
        "spot": spot,
        "signal": signal,
        "strike": strike,
        "confidence": confidence,
        "target": target,
        "sl": sl,
        "pcr": pcr,
        "rsi": rsi,
        "vwap": vwap,
        "max_ce_oi_strike": max_ce_strike,
        "max_pe_oi_strike": max_pe_strike,
        "max_pain": max_pain,
        "score_ce": score_ce,
        "score_pe": score_pe,
        "reason": reasons
    }

