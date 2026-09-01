import { useEffect, useState } from "react";
import { getMarketStatus } from "../API/api";

export default function Header({ onRefresh }) {
  const [status, setStatus] = useState(null);
  const loadStatus = () => getMarketStatus().then(setStatus).catch(() => setStatus(null));
  useEffect(() => { loadStatus(); const timer = setInterval(loadStatus, 60000); return () => clearInterval(timer); }, []);
  const nifty = status?.instruments?.NIFTY;
  return (
    <div className="flex justify-between items-center">
      <h1 className="text-3xl font-bold"> AI Dashboard</h1>
      <div className="flex items-center gap-3">
        {nifty && <span className={`rounded-full px-3 py-1 text-xs font-semibold ${nifty.isStale ? "bg-amber-950 text-amber-300" : "bg-emerald-950 text-emerald-300"}`} title={nifty.fetchedAt || "No live snapshot yet"}>{nifty.isStale ? "NIFTY data stale" : `NIFTY live · ${nifty.ageSeconds}s`}</span>}
        <button onClick={() => { onRefresh(); loadStatus(); }} className="bg-blue-600 px-4 py-2 rounded-xl">Refresh</button>
      </div>
    </div>
  );
}
