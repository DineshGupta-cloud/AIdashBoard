import asyncio, json, os, sqlite3, threading
from contextlib import suppress
from datetime import datetime, time, timezone
from http.cookiejar import CookieJar
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import HTTPCookieProcessor, Request, build_opener
from zoneinfo import ZoneInfo

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DB_FILE = DATA_DIR / "market_history.sqlite3"
IST = ZoneInfo("Asia/Kolkata")
INDEXES = {"NIFTY", "BANKNIFTY", "FINNIFTY", "MIDCPNIFTY"}

class NSEProvider:
    """NSE public-web provider. Use a licensed broker/data adapter for production scale."""
    headers = {"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124 Safari/537.36", "Accept":"application/json, text/plain, */*", "Accept-Language":"en-IN,en;q=0.9", "Referer":"https://www.nseindia.com/option-chain"}
    def __init__(self): self.opener = build_opener(HTTPCookieProcessor(CookieJar()))
    def request(self, url):
        try:
            with self.opener.open(Request(url, headers=self.headers), timeout=15) as response: return response.read()
        except (HTTPError, URLError, TimeoutError) as error: raise RuntimeError(f"NSE request failed: {error}") from error
    def fetch_option_chain(self, symbol):
        self.request("https://www.nseindia.com/")
        kind = "option-chain-indices" if symbol.upper() in INDEXES else "option-chain-equities"
        payload = json.loads(self.request(f"https://www.nseindia.com/api/{kind}?symbol={quote(symbol.upper())}").decode())
        if not payload.get("records", {}).get("data"): raise ValueError(f"NSE returned no option-chain rows for {symbol}")
        return payload

class SnapshotStore:
    def __init__(self):
        self.lock = threading.Lock()
        with sqlite3.connect(DB_FILE) as connection:
            connection.execute("CREATE TABLE IF NOT EXISTS option_chain_snapshots (id INTEGER PRIMARY KEY, symbol TEXT NOT NULL, fetched_at TEXT NOT NULL, provider TEXT NOT NULL, payload TEXT NOT NULL)")
            connection.execute("CREATE INDEX IF NOT EXISTS idx_snapshot_symbol ON option_chain_snapshots(symbol, id DESC)")
    def save(self, symbol, payload, provider):
        fetched_at = datetime.now(timezone.utc).isoformat()
        with self.lock, sqlite3.connect(DB_FILE) as connection: connection.execute("INSERT INTO option_chain_snapshots(symbol,fetched_at,provider,payload) VALUES (?,?,?,?)", (symbol.upper(), fetched_at, provider, json.dumps(payload)))
        return fetched_at
    def latest(self, symbol):
        with sqlite3.connect(DB_FILE) as connection: row = connection.execute("SELECT fetched_at,provider,payload FROM option_chain_snapshots WHERE symbol=? ORDER BY id DESC LIMIT 1", (symbol.upper(),)).fetchone()
        return None if not row else {"fetchedAt":row[0], "provider":row[1], "payload":json.loads(row[2])}
    def history(self, symbol, limit):
        with sqlite3.connect(DB_FILE) as connection: rows = connection.execute("SELECT fetched_at,provider FROM option_chain_snapshots WHERE symbol=? ORDER BY id DESC LIMIT ?", (symbol.upper(), limit)).fetchall()
        return [{"fetchedAt":x[0], "provider":x[1]} for x in rows]

class MarketDataService:
    def __init__(self):
        self.provider_name=os.getenv("MARKET_DATA_PROVIDER","nse").lower(); self.provider=NSEProvider() if self.provider_name=="nse" else None
        self.symbols=[x.strip().upper() for x in os.getenv("MARKET_DATA_SYMBOLS","NIFTY,BANKNIFTY").split(",") if x.strip()]
        self.refresh_seconds=int(os.getenv("MARKET_REFRESH_SECONDS","180")); self.stale_after_seconds=int(os.getenv("MARKET_STALE_AFTER_SECONDS","600"))
        self.market_hours_only=os.getenv("MARKET_HOURS_ONLY","true").lower()=="true"; self.scheduler_enabled=os.getenv("MARKET_SCHEDULER_ENABLED","true").lower()=="true"
        self.store=SnapshotStore(); self.task=None; self.last_error=None
    def is_market_open(self):
        now=datetime.now(IST); return now.weekday()<5 and time(9,15)<=now.time()<=time(15,30)
    def refresh_symbol(self, symbol):
        if not self.provider: raise RuntimeError("Live provider disabled. Configure NSE or a broker adapter.")
        payload=self.provider.fetch_option_chain(symbol); fetched=self.store.save(symbol,payload,self.provider_name); self.last_error=None
        return {"symbol":symbol,"fetchedAt":fetched,"records":len(payload["records"]["data"])}
    def refresh_all(self, force=False):
        if self.market_hours_only and not force and not self.is_market_open(): return {"skipped":True,"reason":"outside_market_hours","results":[]}
        results=[]
        for symbol in self.symbols:
            try: results.append(self.refresh_symbol(symbol))
            except Exception as error: self.last_error=str(error); results.append({"symbol":symbol,"error":str(error)})
        return {"skipped":False,"results":results}
    def payload(self, symbol, fallback=None):
        cached=self.store.latest(symbol)
        if not cached: return fallback,{"source":"bundled_snapshot" if fallback else "unavailable","fetchedAt":None,"isStale":True}
        age=max(0,(datetime.now(timezone.utc)-datetime.fromisoformat(cached["fetchedAt"])).total_seconds())
        return cached["payload"],{"source":cached["provider"],"fetchedAt":cached["fetchedAt"],"ageSeconds":round(age),"isStale":age>self.stale_after_seconds}
    def status(self):
        return {"provider":self.provider_name,"marketOpen":self.is_market_open(),"schedulerEnabled":self.scheduler_enabled,"marketHoursOnly":self.market_hours_only,"refreshSeconds":self.refresh_seconds,"lastError":self.last_error,"instruments":{x:self.payload(x)[1] for x in self.symbols}}
    async def start(self):
        if self.scheduler_enabled and not self.task: self.task=asyncio.create_task(self.run())
    async def stop(self):
        if self.task: self.task.cancel();
        if self.task:
            with suppress(asyncio.CancelledError): await self.task
            self.task=None
    async def run(self):
        while True: await asyncio.to_thread(self.refresh_all); await asyncio.sleep(self.refresh_seconds)

market_data=MarketDataService()
