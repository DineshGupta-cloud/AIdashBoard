from fastapi import APIRouter

router = APIRouter()

# @router.get("/options/test")
# def options_advisor():
#     return {
#         "message": "Put your full advisor logic here"
#     }

# ============================================================
# COMBINED AI ADVISOR API
# Uses:
# 1. options/signals logic
# 2. options/analyze logic
# 3. options_playbook.json
# New Endpoint: /options/advisor
# ============================================================

import json
import math
from fastapi import FastAPI

app = FastAPI()

# ============================================================
# LOAD JSON
# ============================================================
def load_json(file):
    with open(file, "r", encoding="utf-8") as f:
        return json.load(f)

# ============================================================
# INDICATORS (ZERO DEPENDENCY)
# ============================================================
def calculate_rsi(prices, period=14):
    if len(prices) <= period:
        return 50

    gains, losses = [], []

    for i in range(1, len(prices)):
        diff = prices[i] - prices[i - 1]
        gains.append(max(diff, 0))
        losses.append(abs(min(diff, 0)))

    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period

    for i in range(period, len(gains)):
        avg_gain = ((avg_gain * (period - 1)) + gains[i]) / period
        avg_loss = ((avg_loss * (period - 1)) + losses[i]) / period

    if avg_loss == 0:
        return 100

    rs = avg_gain / avg_loss
    return round(100 - (100 / (1 + rs)), 2)


def calculate_ema(prices, period):
    if len(prices) < period:
        return prices[-1]

    multiplier = 2 / (period + 1)
    ema = sum(prices[:period]) / period

    for price in prices[period:]:
        ema = ((price - ema) * multiplier) + ema

    return round(ema, 2)


def calculate_macd(prices):
    ema12 = calculate_ema(prices, 12)
    ema26 = calculate_ema(prices, 26)

    macd = ema12 - ema26
    signal = macd * 0.8
    hist = macd - signal

    return round(macd, 2), round(signal, 2), round(hist, 2)


def calculate_vwap(prices, volumes):
    pv = sum(p * v for p, v in zip(prices, volumes))
    tv = sum(volumes)
    return round(pv / tv, 2) if tv else 0


# ============================================================
# SAMPLE PRICE SERIES
# ============================================================
def generate_prices(spot):
    return [spot - 80 + (i * 5) for i in range(30)]


def generate_volumes():
    return [1000 + (i * 200) for i in range(30)]


# ============================================================
# STRIKE HELPERS
# ============================================================
def atm(spot):
    return round(spot / 50) * 50

def otm_ce(spot):
    return math.ceil(spot / 50) * 50 + 50

def itm_ce(spot):
    return math.floor(spot / 50) * 50

def otm_pe(spot):
    return math.floor(spot / 50) * 50 - 50

def itm_pe(spot):
    return math.ceil(spot / 50) * 50


# ============================================================
# MAIN COMBINED API
# ============================================================
# @app.get("/options/advisor")
@router.get("/options/advanced-advisor")
def options_advisor():

    raw = load_json("data\option_chain.json") #E:\OptionsRagProject\python\data
    playbook = load_json("data\options_playbook.json")

    records = raw["records"]["data"]
    spot = raw["records"]["underlyingValue"]

    rows = []
    total_ce_oi = 0
    total_pe_oi = 0
    ce_map = {}
    pe_map = {}

    # --------------------------------------------------------
    # READ CHAIN
    # --------------------------------------------------------
    for row in records:
        strike = row["strikePrice"]

        ce = row["CE"]["openInterest"] if "CE" in row else 0
        pe = row["PE"]["openInterest"] if "PE" in row else 0

        rows.append({
            "strike": strike,
            "ceOi": ce,
            "peOi": pe
        })

        ce_map[strike] = ce
        pe_map[strike] = pe

        total_ce_oi += ce
        total_pe_oi += pe

    # --------------------------------------------------------
    # CORE LEVELS
    # --------------------------------------------------------
    pcr = round(total_pe_oi / total_ce_oi, 2) if total_ce_oi else 0

    nearby = [r for r in rows if abs(r["strike"] - spot) <= 500]

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

    max_ce_oi_strike = max(ce_map, key=ce_map.get)
    max_pe_oi_strike = max(pe_map, key=pe_map.get)
    max_pain = round((max_ce_oi_strike + max_pe_oi_strike) / 2)

    # --------------------------------------------------------
    # INDICATORS
    # --------------------------------------------------------
    prices = generate_prices(spot)
    volumes = generate_volumes()

    rsi = calculate_rsi(prices)
    ema9 = calculate_ema(prices, 9)
    ema20 = calculate_ema(prices, 20)
    macd, macd_signal, hist = calculate_macd(prices)
    vwap = calculate_vwap(prices, volumes)

    # --------------------------------------------------------
    # SIGNAL ENGINE
    # --------------------------------------------------------
    score_ce = 0
    score_pe = 0
    reasons = []

    if pcr > 1.1:
        score_ce += 15
        reasons.append("PCR Bullish")

    if spot > vwap:
        score_ce += 15
        reasons.append("Above VWAP")

    if rsi > 55:
        score_ce += 15
        reasons.append("RSI Strong")

    if ema9 > ema20:
        score_ce += 10
        reasons.append("EMA Bullish")

    if macd > macd_signal:
        score_ce += 10
        reasons.append("MACD Bullish")

    if spot >= max_ce_oi_strike:
        score_ce += 15
        reasons.append("Above Max CE OI")

    if spot > max_pain:
        score_ce += 10
        reasons.append("Above Max Pain")

    # ----------------------------------
    if pcr < 0.9:
        score_pe += 15

    if spot < vwap:
        score_pe += 15

    if rsi < 45:
        score_pe += 15

    if ema9 < ema20:
        score_pe += 10

    if macd < macd_signal:
        score_pe += 10

    if spot <= max_pe_oi_strike:
        score_pe += 15

    if spot < max_pain:
        score_pe += 10

    # --------------------------------------------------------
    # FINAL SIGNAL + STRATEGY
    # --------------------------------------------------------
    signal = "NO TRADE"
    confidence = 0
    strike = atm(spot)
    strategy_name = "Wait & Watch"
    legs = []
    view = "Neutral"

    if score_ce >= 60 and score_ce > score_pe:
        signal = "BUY CE"
        confidence = score_ce
        strike = atm(spot)

        if confidence >= 80:
            strategy_name = "Long Call"
            legs = [f"Buy {strike} CE"]
            view = "Strong Bullish"

        else:
            strategy_name = "Bull Call Spread"
            legs = [
                f"Buy {strike} CE",
                f"Sell {strike + 100} CE"
            ]
            view = "Moderate Bullish"

    elif score_pe >= 60 and score_pe > score_ce:
        signal = "BUY PE"
        confidence = score_pe
        strike = atm(spot)

        if confidence >= 80:
            strategy_name = "Long Put"
            legs = [f"Buy {strike} PE"]
            view = "Strong Bearish"

        else:
            strategy_name = "Bear Put Spread"
            legs = [
                f"Buy {strike} PE",
                f"Sell {strike - 100} PE"
            ]
            view = "Moderate Bearish"

    else:
        if best_support and best_resistance and best_support < spot < best_resistance:
            strategy_name = "Iron Condor"
            view = "Range Bound"
            legs = [
                f"Sell {best_support} PE",
                f"Buy {best_support - 100} PE",
                f"Sell {best_resistance} CE",
                f"Buy {best_resistance + 100} CE"
            ]

    # --------------------------------------------------------
    # FETCH PLAYBOOK DETAIL
    # --------------------------------------------------------
    detail = next(
        (x for x in playbook if x["name"].lower() == strategy_name.lower()),
        None
    )

    # --------------------------------------------------------
    # RESPONSE
    # --------------------------------------------------------
    return {
        "index": "NIFTY",
        "spot": spot,

        "signal": signal,
        "confidence": confidence,
        "strike": strike,

        "strategy": strategy_name,
        "legs": legs,
        "marketView": view,
        "strategyDetail": detail,

        "target": 30,
        "sl": 15,

        "pcr": pcr,
        "rsi": rsi,
        "vwap": vwap,
        "ema9": ema9,
        "ema20": ema20,
        "macd": macd,
        "macd_signal": macd_signal,
        "histogram": hist,

        "support": support,
        "resistance": resistance,

        "max_ce_oi_strike": max_ce_oi_strike,
        "max_pe_oi_strike": max_pe_oi_strike,
        "max_pain": max_pain,

        "score_ce": score_ce,
        "score_pe": score_pe,

        "reason": reasons
    }