import { useEffect, useState } from "react";
import { advancedGetSignals } from "../API/api";

export default function Test() {
  const [data, setData] = useState(null);

 const load = async () => {
  try {
    const res = await advancedGetSignals();
    console.log("Signals Data:", res);
    setData(res);   // FIXED
  } catch (error) {
    console.error(error);
  }
};

  useEffect(() => {
    load();

    const timer = setInterval(load, 5000);
    return () => clearInterval(timer);
  }, []);

  if (!data) {
    return <div className="text-white">Loading Advisor...</div>;
  }

  const color =
    data.signal === "BUY CE"
      ? "text-green-400 border-green-500"
      : data.signal === "BUY PE"
      ? "text-red-400 border-red-500"
      : "text-gray-400 border-slate-700";

  return (
    <div className="space-y-6 p-4 bg-slate-950 min-h-screen text-white">
      {/* Top Signal Card */}
      <div className={`rounded-2xl border p-6 bg-slate-900 ${color}`}>
        <div className="text-3xl font-bold">{data.signal}</div>
        <div className="mt-2 text-slate-300">Index: {data.index}</div>
        <div className="text-slate-300">Spot: {data.spot}</div>
        <div className="text-slate-300">Strike: {data.strike}</div>
        <div className="text-slate-300">Confidence: {data.confidence}%</div>
        <div className="text-slate-300">Target: {data.target}</div>
        <div className="text-slate-300">SL: {data.sl}</div>
      </div>

      {/* Grid */}
      <div className="grid md:grid-cols-2 gap-4">
        <Panel title="Indicators">
          <Row label="PCR" value={data.pcr} />
          <Row label="RSI" value={data.rsi} />
          <Row label="VWAP" value={data.vwap} />
          <Row label="EMA9" value={data.ema9} />
          <Row label="EMA20" value={data.ema20} />
          <Row label="MACD" value={data.macd} />
          <Row label="Signal" value={data.macd_signal} />
          <Row label="Histogram" value={data.histogram} />
        </Panel>

        <Panel title="OI Levels">
          <Row label="Max CE OI" value={data.max_ce_oi_strike} />
          <Row label="Max PE OI" value={data.max_pe_oi_strike} />
          <Row label="Max Pain" value={data.max_pain} />
          <Row label="CE Score" value={data.score_ce} />
          <Row label="PE Score" value={data.score_pe} />
        </Panel>

        <Panel title="Strategy">
          <Row label="Name" value={data.strategy} />
          <Row label="View" value={data.marketView} />

          <div className="mt-3">
            <div className="text-slate-400 text-sm mb-2">Legs</div>
            {(data.legs || []).map((leg, i) => (
              <div key={i} className="text-white py-1">
                • {leg}
              </div>
            ))}
          </div>
        </Panel>

        <Panel title="Reasons">
          <ul className="space-y-2 text-slate-300">
            {data.reason?.length ? (
              data.reason.map((r, i) => <li key={i}>• {r}</li>)
            ) : (
              <li>No Trade</li>
            )}
          </ul>
        </Panel>
      </div>
    </div>
  );
}

function Panel({ title, children }) {
  return (
    <div className="rounded-2xl bg-slate-900 border border-slate-800 p-4">
      <div className="text-lg font-semibold mb-3">{title}</div>
      {children}
    </div>
  );
}

function Row({ label, value }) {
  return (
    <div className="flex justify-between py-1 border-b border-slate-800 text-sm">
      <span className="text-slate-400">{label}</span>
      <span className="text-white font-medium">{value}</span>
    </div>
  );
}