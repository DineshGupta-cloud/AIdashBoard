import { useEffect, useState } from "react";
import { createAlert, evaluateAlerts, getAlerts, removeAlert, setAlertEnabled } from "../API/api";

const options = [
  ["spot_above", "Spot rises above"], ["spot_below", "Spot falls below"],
  ["pcr_above", "PCR rises above"], ["pcr_below", "PCR falls below"],
  ["signal_is", "Market bias is"], ["breakout_resistance", "Spot breaks OI resistance"],
  ["breakdown_support", "Spot breaks OI support"],
];
const needsValue = new Set(["spot_above", "spot_below", "pcr_above", "pcr_below"]);

export default function AlertsDashboard() {
  const [alerts, setAlerts] = useState([]), [snapshot, setSnapshot] = useState(null), [events, setEvents] = useState([]), [error, setError] = useState("");
  const [form, setForm] = useState({ name: "", condition: "spot_above", threshold: "", signal: "BULLISH" });
  const refresh = async () => {
    try { const result = await evaluateAlerts(); setAlerts(result.alerts); setSnapshot(result.snapshot); if (result.triggered.length) setEvents(x => [...result.triggered, ...x].slice(0, 10)); setError(""); }
    catch { setError("Unable to reach the alert service. Start the FastAPI backend."); }
  };
  useEffect(() => { getAlerts().then(setAlerts).catch(() => setError("Unable to load alerts.")); refresh(); const timer = setInterval(refresh, 15000); return () => clearInterval(timer); }, []);
  const submit = async (event) => {
    event.preventDefault();
    try {
      const alert = await createAlert({ name: form.name || options.find(x => x[0] === form.condition)[1], condition: form.condition, threshold: needsValue.has(form.condition) ? Number(form.threshold) : null, signal: form.condition === "signal_is" ? form.signal : null });
      setAlerts(x => [...x, alert]); setForm(x => ({ ...x, name: "", threshold: "" }));
    } catch (e) { setError(e.response?.data?.detail || "Enter a valid alert value."); }
  };
  return <div className="space-y-6">
    
    <section className="rounded-2xl border border-slate-800 bg-slate-900 p-6"><div className="flex items-center justify-between"><div><h2 className="text-2xl font-bold">Alerts</h2><p className="text-sm text-slate-400">Rules evaluate every 15 seconds while this page is open.</p></div><button onClick={refresh} className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold">Check now</button></div>
      {snapshot && <div className="mt-5 grid grid-cols-2 gap-3 md:grid-cols-5">{[["Spot",snapshot.spot],["PCR",snapshot.pcr],["Bias",snapshot.signal],["OI support",snapshot.support ?? "-"],["OI resistance",snapshot.resistance ?? "-"]].map(([key,value]) => <div key={key} className="rounded-lg bg-slate-800 p-3 text-sm"><p className="text-slate-400">{key}</p><p className="mt-1 font-semibold">{value}</p></div>)}</div>}</section>
    {error && <div className="rounded-xl border border-red-800 bg-red-950 p-4 text-red-200">{error}</div>}
    <section className="rounded-2xl border border-slate-800 bg-slate-900 p-6"><h3 className="text-lg font-semibold">Create rule</h3><form onSubmit={submit} className="mt-4 grid gap-3 md:grid-cols-4"><input value={form.name} onChange={e=>setForm({...form,name:e.target.value})} placeholder="Name (optional)" className="rounded-lg bg-slate-800 p-3 text-sm"/><select value={form.condition} onChange={e=>setForm({...form,condition:e.target.value})} className="rounded-lg bg-slate-800 p-3 text-sm">{options.map(([v,l])=><option key={v} value={v}>{l}</option>)}</select>{needsValue.has(form.condition) ? <input required type="number" step="any" value={form.threshold} onChange={e=>setForm({...form,threshold:e.target.value})} placeholder="Threshold" className="rounded-lg bg-slate-800 p-3 text-sm"/> : form.condition === "signal_is" ? <select value={form.signal} onChange={e=>setForm({...form,signal:e.target.value})} className="rounded-lg bg-slate-800 p-3 text-sm"><option>BULLISH</option><option>BEARISH</option><option>NEUTRAL</option></select> : <div className="rounded-lg bg-slate-800 p-3 text-sm text-slate-400">Uses current OI level</div>}<button className="rounded-lg bg-emerald-600 p-3 text-sm font-semibold">Add alert</button></form></section>
    <section className="rounded-2xl border border-slate-800 bg-slate-900 p-6"><h3 className="text-lg font-semibold">Your rules</h3><div className="mt-4 space-y-3">{alerts.length ? alerts.map(a=><div key={a.id} className="flex flex-col justify-between gap-3 rounded-xl bg-slate-800 p-4 md:flex-row md:items-center"><div><p className="font-medium">{a.name}</p><p className="text-sm text-slate-400">{describe(a)}{a.lastTriggeredAt && ` · Last triggered ${new Date(a.lastTriggeredAt).toLocaleString()}`}</p></div><div className="flex gap-2"><button onClick={async()=>{const x=await setAlertEnabled(a.id,!a.enabled);setAlerts(z=>z.map(i=>i.id===x.id?x:i))}} className="rounded-lg border border-slate-600 px-3 py-2 text-sm">{a.enabled?"Disable":"Enable"}</button><button onClick={async()=>{await removeAlert(a.id);setAlerts(z=>z.filter(i=>i.id!==a.id))}} className="rounded-lg border border-red-800 px-3 py-2 text-sm text-red-300">Delete</button></div></div>) : <p className="text-sm text-slate-400">No alert rules yet.</p>}</div></section>
    <section className="rounded-2xl border border-slate-800 bg-slate-900 p-6"><h3 className="text-lg font-semibold">Triggered this session</h3><div className="mt-4 space-y-2 text-sm">{events.length ? events.map((e,i)=><div key={`${e.alert.id}-${i}`} className="rounded-lg border border-emerald-800 bg-emerald-950/40 p-3"><span className="font-semibold text-emerald-300">{e.alert.name}</span> triggered at spot {e.snapshot.spot}, PCR {e.snapshot.pcr}.</div>) : <p className="text-slate-400">No new triggers in this browser session.</p>}</div></section>
  </div>;
}
function describe(a) { 
  if (a.condition === "signal_is") 
    return `Market bias is ${a.signal}`; 
  if (a.condition === "breakout_resistance") 
    return "Spot breaks OI resistance"; 
  if (a.condition === "breakdown_support") 
    return "Spot breaks OI support"; 
  return `${
    a.condition.replace("_", " ")} 
    ${a.threshold}`; 
  }
