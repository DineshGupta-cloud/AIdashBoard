import React, { useEffect, useState } from "react";
import { getBankNiftyData } from "../API/api";

export default function BankNiftyDashboard() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const loadData = async () => {
    try {
      setLoading(true);
      const res = await getBankNiftyData();
      setData(res);
      setError("");
    } catch (err) {
      setError("Failed to load API");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 100000);
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <div className="bg-[#0f0f0f] text-white rounded-2xl p-6 shadow-lg">
        Loading...
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-900 text-red-200 rounded-2xl p-6 shadow-lg">
        {error}
      </div>
    );
  }

  const bn = data.banknifty;

  return (
    <div className="space-y-6 text-white">
      {/* Main Wrapper */}
      <div className="bg-[#121212] border border-gray-700 rounded-2xl shadow-2xl p-6">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center md:justify-between border-b border-gray-800 pb-4 mb-6">
          <div>
            <h2 className="text-2xl font-bold text-white">
              BankNifty AI Dashboard
            </h2>
            <p className="text-sm text-gray-300 mt-1">
              Live weighted options analysis
            </p>
          </div>

          <span
            className={`mt-3 md:mt-0 px-4 py-2 rounded-full text-sm font-bold ${
              bn.signal === "BULLISH"
                ? "bg-green-900 text-green-300"
                : bn.signal === "BEARISH"
                ? "bg-red-900 text-red-300"
                : "bg-yellow-900 text-yellow-300"
            }`}
          >
            {bn.signal}
          </span>
        </div>

        {/* Summary Cards */}
        <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-6 gap-4">
          <InfoCard title="Spot" value={bn.spot} />
          <InfoCard title="Confidence" value={`${bn.confidence}%`} />
          <InfoCard title="PCR" value={bn.pcr} />
          <InfoCard title="Support" value={bn.support} />
          <InfoCard title="Resistance" value={bn.resistance} />
          <InfoCard title="Score" value={bn.totalScore} />
        </div>
      </div>

      {/* Stock Analysis */}
      <div className="bg-[#121212] border border-gray-700 rounded-2xl shadow-2xl p-6">
        <div className="flex items-center justify-between mb-5">
          <h3 className="text-xl font-bold text-white">Stock Analysis</h3>
          <span className="text-sm text-gray-300">
            {data.stocks.length} Stocks
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {data.stocks.map((item, index) => (
            <div
              key={index}
              className="bg-[#1a1a1a] border border-gray-800 rounded-2xl p-4 shadow-md hover:shadow-xl transition-all"
            >
              {/* Top */}
              <div className="flex items-center justify-between mb-4">
                <h4 className="text-lg font-bold">{item.symbol}</h4>

                <span
                  className={`px-3 py-1 rounded-full text-xs font-bold ${
                    item.signal === "BULLISH"
                      ? "bg-green-900 text-green-300"
                      : item.signal === "BEARISH"
                      ? "bg-red-900 text-red-300"
                      : "bg-yellow-900 text-yellow-300"
                  }`}
                >
                  {item.signal}
                </span>
              </div>

              {/* Data Grid */}
              <div className="grid grid-cols-2 gap-3">
                <MiniInfo label="Weight" value={item.weight} />
                <MiniInfo label="Spot" value={item.spot} />
                <MiniInfo label="Strike" value={item.nearestStrike} />
                <MiniInfo label="Score" value={item.score} />
                <MiniInfo label="Weighted" value={item.weightedScore} />
              </div>

              {/* Reasons */}
              <div className="mt-4">
                <p className="text-xs text-gray-400 mb-2">Reasons</p>
                <div className="flex flex-wrap gap-2">
                  {item.reasons.map((reason, i) => (
                    <span
                      key={i}
                      className="px-2 py-1 bg-gray-800 text-blue-300 text-xs rounded-lg"
                    >
                      {reason}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

/* Summary Card */
function InfoCard({ title, value }) {
  return (
    <div className="bg-[#1b1b1b] border border-gray-800 rounded-2xl p-4 shadow-md">
      <p className="text-sm text-gray-250">{title}</p>
      <h3 className="text-xl font-bold text-white mt-1">{value}</h3>
    </div>
  );
}

/* Mini Card */
function MiniInfo({ label, value }) {
  return (
    <div className="bg-[#222222] border border-gray-800 rounded-xl p-2">
      <p className="text-xs text-gray-350">{label}</p>
      <p className="font-semibold text-white">{value}</p>
    </div>
  );
}