import { useEffect, useState } from "react";
import Header from "./Component/Header";
import Search from "./Component/Search";
import StrategyCard from "./Component/StrategyCard";
import Chart from "./Component/Chart";
import Sidebar from "./Component/Sidebar";
import OpenInterestChart from "./Component/OpenInterestChart";
import SignalDashboard from "./Component/SignalDashboard";

import { getAnalysis, getChartData, searchRag } from "./API/api";
import OptionChainTable from "./Component/OptionChainTable";
import AdvanceSignals from "./Component/AdvanceSignals";

import BankNiftyDashboard from "./Component/BankNiftyDashboard";
import AlertsDashboard from "./Component/AlertsDashboard";

export default function App() {
  const [analysis, setAnalysis] = useState(null);
  const [chartData, setChartData] = useState(null);

  const [query, setQuery] = useState("");
  const [results, setResults] = useState([]);

  const [selected, setSelected] = useState("Dashboard");

  const load = async () => {
    const a = await getAnalysis();
    const c = await getChartData();

    setAnalysis(a);
    setChartData(c);
  };

  const search = async () => {
    const res = await searchRag(query);
    setResults(res);
  };

  useEffect(() => {
    load();
  }, []);

  if (!analysis) {
    return (
      <div className="min-h-screen bg-slate-950 text-white p-6">
        Loading...
      </div>
    );
  }

  return (
    <div className="flex min-h-screen bg-slate-950 text-white">

      {/* SIDEBAR */}
      <Sidebar selected={selected} setSelected={setSelected} />

      {/* MAIN */}
      <div className="flex-1 p-6 space-y-6">

        <Header onRefresh={load} />

        {/* DASHBOARD */}
        {selected === "Dashboard" && (
          <>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <Card title="Spot" value={analysis.spot} />
              <Card title="PCR" value={analysis.pcr} />
              <Card title="Max Pain" value={analysis.maxPain} />
              <Card title="View" value={analysis.view} />
            </div>

            <Chart analysis={analysis} chartData={chartData} />
              {/* Inner Component */}
    <div className="overflow-auto">
      <BankNiftyDashboard />
    </div>
            
          </>
        )}

        {/* CHART */}
        {selected === "Chart" && (
          <Chart analysis={analysis} chartData={chartData} />
        )}

        {/* STRATEGY */}
        {selected === "Strategy" && (
          <StrategyCard analysis={analysis} />
        )}

        {/* OPEN INTEREST */}
        {selected === "Open Interest" && (
          <OpenInterestChart />
        )}

          {/* OPEN INTEREST */}
        {selected === "Open table" && (
          <OptionChainTable/>
        )}

          {/* OPEN Signals */}
        {selected === "Signals" && (
          <SignalDashboard/>
        )}

          {/* OPEN Advanced Advisor */}
        {selected === "Advanced Advisor" && (
          <AdvanceSignals/>
        )}

        {selected === "Alerts" && <AlertsDashboard />}

        

        {/* SEARCH */}
        {selected === "Search" && (
          <Search
            query={query}
            setQuery={setQuery}
            search={search}
            results={results}
          />
        )}

      </div>
    </div>
  );
}

function Card({ title, value }) {
  return (
    <div className="rounded-2xl bg-slate-900 border border-slate-800 p-4 shadow">
      <div className="text-sm text-slate-400">{title}</div>
      <div className="text-2xl font-semibold mt-1">{value}</div>
    </div>
  );
}
