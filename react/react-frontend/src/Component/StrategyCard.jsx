export default function StrategyCard({ analysis }) {
  const s = analysis.strategyDetail;
  if (!s) return null;

  return (
    <div className="rounded-2xl bg-slate-900 p-5 space-y-2">
      <h2 className="text-2xl font-bold">{analysis.bestStrategy}</h2>
      <p><span className="text-slate-400">Category:</span> {s.category}</p>
      <p><span className="text-slate-400">View:</span> {s.marketView}</p>
      <p><span className="text-slate-400">Setup:</span> {s.setup?.join(", ")}</p>
      <p><span className="text-slate-400">Max Profit:</span> {s.maxProfit}</p>
      <p><span className="text-slate-400">Max Loss:</span> {s.maxLoss}</p>
    </div>
  );
}